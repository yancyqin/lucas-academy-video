"""Fit the Chinese narration to the English: each Chinese line about as long as its English line.

English is the reference and is not touched. A Chinese line that runs longer
than its English line is regenerated faster -- never slower than its directed
speed, never faster than CEIL -- and measured after the same tightening both
languages get (reciprocal-doors-tighten.py). Each attempt is checked with
Whisper; the closest attempt that reads correctly wins. A Chinese line that is
already shorter keeps its reading: the shared timeline gives it a longer pause.

Results go to src/scripts/reciprocal-doors.fit.json and into the media script,
so `reciprocal-doors-voice.py narration` sees them as current.

Run with the lucas-academy-media environment:
    cd ../lucas-academy-media && PYTHONPATH=src .conda/bin/python ../lucas-academy-video/scripts/reciprocal-doors-fit.py
"""
from __future__ import annotations

import difflib
import importlib.util
import json
import re
import sys
from pathlib import Path

import soundfile as sf
import whisper
from lucas_media.cosyvoice_engine import CosyVoiceEngine
from lucas_media.joke import add_peak_headroom, save_wav

VIDEO = Path(__file__).resolve().parent.parent
MEDIA = VIDEO.parent / "lucas-academy-media"
SOURCE = VIDEO / "src/scripts/reciprocal-doors.json"
FIT = VIDEO / "src/scripts/reciprocal-doors.fit.json"
ZH_SCRIPT = MEDIA / "data/scripts/reciprocal-doors-zh.json"
ZH_RAW = MEDIA / "outputs/fangfang/zh/reciprocal-doors"
ZH_TIGHT = MEDIA / "outputs/fangfang/zh/reciprocal-doors-tight"
EN_TIGHT = MEDIA / "outputs/louise/en/reciprocal-doors-tight"

CEIL = 1.15  # fastest Chinese reading we accept for children
TOL = 0.06  # close enough: within 6% of the English length
TRIES = 3
REGEN_IF = 1.04  # regenerate when the fitted speed is at least 4% faster
# Words Whisper must hear (| = alternatives) / must not hear: lessons from earlier takes.
MUST = {
    "rd01-02": (["把故事"], []),
    "rd02-03": (["练认字|練認字"], ["恋人"]),
    "rd03-05": (["难|難"], []),
    "rd05-04": (["事"], ["事儿"]),
    "rd06-04": (["交换|交換"], ["的"]),
    "rd06-06": (["听一听|聽一聽"], []),
    "rd09-01": (["这样试|這樣試"], []),
}
HOMOPHONES = str.maketrans({"它": "他", "她": "他", "的": "得", "地": "得", "话": "画", "話": "画"})

spec = importlib.util.spec_from_file_location("tighten", VIDEO / "scripts/reciprocal-doors-tighten.py")
tighten_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tighten_module)
tighten = tighten_module.tighten


def tight_seconds(path: Path) -> float:
    y, sr = sf.read(path, dtype="float32")
    return len(tighten(y, sr)) / sr


def han(text: str) -> str:
    return re.sub(r"[^一-鿿]", "", re.sub(r"</?strong>", "", text).translate(HOMOPHONES))


def main() -> None:
    only = set(sys.argv[1:])
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    zh_script = json.loads(ZH_SCRIPT.read_text(encoding="utf-8"))
    zh_lines = {l["id"]: l for l in zh_script["lines"]}
    fit = json.loads(FIT.read_text(encoding="utf-8")) if FIT.exists() else {}
    fit.setdefault("zh", {})

    # (zh line id, target seconds, floor speed)
    jobs = []
    for segment in source["segments"]:
        for chunk in segment["chunks"]:
            if "parts" in chunk:
                # Match the whole chunk: narration part + taught phrase in each language.
                zh_parts, en_parts = chunk["parts"]["zh"], chunk["parts"]["en"]
                lead = f"{chunk['id']}-p1"
                zh_demo = tight_seconds(ZH_TIGHT / f"{chunk['id']}-p2.wav")
                en_total = sum(tight_seconds(EN_TIGHT / f"{chunk['id']}-p{i + 1}.wav") for i in range(len(en_parts)))
                jobs.append((lead, en_total - zh_demo, zh_parts[0].get("speed", 0.95)))
            else:
                jobs.append((chunk["id"], tight_seconds(EN_TIGHT / f"{chunk['id']}.wav"), chunk.get("speed", 0.9)))

    engine = asr = None
    for line_id, target, floor in jobs:
        if only and line_id not in only:
            continue
        line = zh_lines[line_id]
        current = line.get("speed", floor)
        existing = ZH_RAW / f"{line_id}.wav"
        if existing.exists():
            seconds = tight_seconds(existing)
            need = current * seconds / target
            if need < current * REGEN_IF:
                continue
            speed = min(need, CEIL)
            print(f"{line_id}: zh {seconds:.2f}s vs en {target:.2f}s -> speed {current:g} -> {speed:.2f}", flush=True)
        else:
            speed = floor
            print(f"{line_id}: new line, en {target:.2f}s, start at {speed:g}", flush=True)
        if engine is None:
            engine = CosyVoiceEngine("fangfang/zh")
            asr = whisper.load_model("medium", device="cpu")

        must, must_not = MUST.get(line_id, ([], []))
        best = None
        for attempt in range(1, TRIES + 1):
            speech, sr, mode = engine.synthesize(
                line["text"],
                target_language="zh",
                mode=(line.get("mode") or "instruct") if line.get("instruct") else "auto",
                speed=speed,
                instruction=line.get("instruct", ""),
            )
            trial = ZH_RAW / f"{line_id}.fit{attempt}.wav"
            save_wav(trial, add_peak_headroom(speech, peak_dbfs=-2.0), sr)
            seconds = tight_seconds(trial)
            heard = asr.transcribe(str(trial), language="zh", fp16=False, initial_prompt="以下是普通话的句子，使用简体中文。")["text"].strip()
            ratio = difflib.SequenceMatcher(None, han(line["text"]), han(heard)).ratio()
            reads = ratio >= 0.85 and all(any(a in heard for a in m.split("|")) for m in must) and not any(n in heard for n in must_not)
            error = seconds / target - 1
            print(f"   try {attempt} @ {speed:.2f}: {seconds:.2f}s ({error:+.0%}) ratio {ratio:.2f} {'OK' if reads else 'MISREAD'} | {heard}", flush=True)
            if reads and (best is None or abs(error) < abs(best[2])):
                best = (trial, speed, error)
            if reads and (abs(error) <= TOL or (speed >= CEIL and error > 0) or (speed <= floor and error < 0)):
                break
            speed = min(CEIL, max(floor, speed * seconds / target))

        if best is None:
            print(f"   {line_id}: no attempt read correctly; kept the previous file", flush=True)
        else:
            trial, used, error = best
            trial.replace(ZH_RAW / f"{line_id}.wav")
            fit["zh"][line_id] = round(used, 3)
            line["speed"] = round(used, 3)
            print(f"   {line_id}: kept speed {used:.2f} ({error:+.0%} vs English)", flush=True)
            FIT.write_text(json.dumps(fit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            ZH_SCRIPT.write_text(json.dumps(zh_script, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        for leftover in ZH_RAW.glob(f"{line_id}.fit*.wav"):
            leftover.unlink()


if __name__ == "__main__":
    main()
