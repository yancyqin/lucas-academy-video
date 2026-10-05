"""Even out the pace of the Chinese film: every line near the film's median speaking rate.

One reading style for the whole film is not enough on its own: CosyVoice decides
each line's tempo, so plain long lines ran fast and short emphasised lines ran
slow (19 of 53 lines more than 12% off; owner: "忽快忽慢"). This measures each
line's speaking rate on the tightened take -- syllables per second of *sound*,
pauses excluded, an English name counted as two syllables -- and re-voices a
line that is more than TOL off the median at a speed that brings it in,
checked by Whisper like every other take (reciprocal-doors-retake.py rules).
A missing line is voiced first at the film speed, then measured.

The chosen speeds go to src/scripts/reciprocal-doors.pace.zh.json and into the
media script, so `reciprocal-doors-voice.py narration` keeps them.

    cd ../lucas-academy-media && PYTHONPATH=src .conda/bin/python ../lucas-academy-video/scripts/reciprocal-doors-pace.py
"""
from __future__ import annotations

import difflib
import importlib.util
import json
import re
import statistics
import sys
import tempfile
from pathlib import Path

import librosa
import soundfile as sf
import whisper
from lucas_media.cosyvoice_engine import CosyVoiceEngine
from lucas_media.joke import add_peak_headroom, save_wav

HERE = Path(__file__).resolve().parent
VIDEO = HERE.parent
MEDIA = VIDEO.parent / "lucas-academy-media"
SCRIPT = MEDIA / "data/scripts/reciprocal-doors-zh.json"
RAW = MEDIA / "outputs/fangfang/zh/reciprocal-doors"
PACE = VIDEO / "src/scripts/reciprocal-doors.pace.zh.json"
TOL = 0.10  # a line within 10% of the film's median rate is left alone
SPEED = (0.8, 1.25)
TRIES = 4


def load(name: str):
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), HERE / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


retake = load("reciprocal-doors-retake")
tighten = load("reciprocal-doors-tighten").tighten


def syllables(text: str) -> int:
    text = re.sub(r"</?strong>|\[[^\]]+\]", "", text)
    return len(re.sub(r"[^一-鿿]", "", text)) + 2 * len(re.findall(r"\b(?:Mary|Jacob)\b", text))


def rate(path: Path, text: str) -> float:
    y, sr = sf.read(path, dtype="float32")
    y = tighten(y, sr)
    intervals = librosa.effects.split(y, top_db=35, frame_length=1024, hop_length=240)
    voiced = sum(b - a for a, b in intervals) / sr
    return syllables(text) / max(voiced, 0.1)


def main() -> None:
    script = json.loads(SCRIPT.read_text(encoding="utf-8"))
    pace = json.loads(PACE.read_text(encoding="utf-8")) if PACE.exists() else {}
    speeds = pace.setdefault("speeds", {})
    # Narration lines only: the taught phrase keeps its slow, plain reading.
    lines = [l for l in script["lines"] if l.get("mode")]
    engine = CosyVoiceEngine("fangfang/zh")
    asr = whisper.load_model("medium", device="cpu")

    def take(line: dict, speed: float, attempt: int):
        speech, sr, _ = engine.synthesize(line["text"], target_language="zh", mode=line["mode"], speed=speed, instruction=line.get("instruct", ""))
        trial = RAW / f"{line['id']}.pace{attempt}.wav"
        save_wav(trial, add_peak_headroom(speech, peak_dbfs=-2.0), sr)
        y, sr_read = sf.read(trial, dtype="float32")
        with tempfile.NamedTemporaryFile(suffix=".wav") as played:
            sf.write(played.name, tighten(y, sr_read), sr_read, subtype="PCM_16")
            heard = asr.transcribe(played.name, language="zh", fp16=False, initial_prompt="以下是普通话的句子，使用简体中文。")["text"].strip()
        expected = line.get("check", line["text"])
        ratio = difflib.SequenceMatcher(None, retake.norm(expected, "zh"), retake.norm(heard, "zh")).ratio()
        must, must_not = retake.RULES.get(("zh", line["id"]), ([], []))
        reads = ratio >= 0.94 and all(any(a in heard for a in m.split("|")) for m in must) and not any(n in heard for n in must_not)
        return trial, reads, rate(trial, expected), heard

    # Lines without a take (their text changed) are voiced first at the film speed.
    for line in lines:
        if not (RAW / f"{line['id']}.wav").exists():
            for attempt in range(1, TRIES + 1):
                trial, reads, r, heard = take(line, line.get("speed", 1.0), attempt)
                print(f"{line['id']} new take {attempt}: {r:.2f} syll/s {'OK' if reads else 'MISREAD'} | {heard}", flush=True)
                if reads:
                    trial.replace(RAW / f"{line['id']}.wav")
                    break
                trial.unlink()
    rates = {l["id"]: rate(RAW / f"{l['id']}.wav", l.get("check", l["text"])) for l in lines if (RAW / f"{l['id']}.wav").exists()}
    target = statistics.median(rates.values())
    pace["target"] = round(target, 3)
    print(f"film median: {target:.2f} syllables/s over {len(rates)} lines", flush=True)

    only = set(sys.argv[1:])
    for line in lines:
        if line["id"] not in rates or (only and line["id"] not in only):
            continue
        current = line.get("speed", 1.0)
        off = rates[line["id"]] / target
        if abs(off - 1) <= TOL:
            continue
        speed = min(SPEED[1], max(SPEED[0], current / off))
        print(f"{line['id']}: {off:.2f}x the median at speed {current:g} -> try {speed:.2f}", flush=True)
        best = None
        for attempt in range(1, TRIES + 1):
            trial, reads, r, heard = take(line, speed, attempt)
            err = r / target - 1
            print(f"   try {attempt} @ {speed:.2f}: {r / target:.2f}x {'OK' if reads else 'MISREAD'} | {heard}", flush=True)
            if reads and (best is None or abs(err) < abs(best[2])):
                best = (trial, speed, err)
            else:
                trial.unlink()
            if reads and abs(err) <= TOL:
                break
            if reads:
                speed = min(SPEED[1], max(SPEED[0], speed / (1 + err)))
        if best is None:
            print(f"   {line['id']}: no take read correctly; kept the current one", flush=True)
            continue
        trial, used, err = best
        if abs(err) < abs(off - 1):
            trial.replace(RAW / f"{line['id']}.wav")
            speeds[line["id"]] = round(used, 3)
            line["speed"] = round(used, 3)
            print(f"   {line['id']}: kept speed {used:.2f} ({1 + err:.2f}x the median)", flush=True)
            PACE.write_text(json.dumps(pace, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            SCRIPT.write_text(json.dumps(script, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        for leftover in RAW.glob(f"{line['id']}.pace*.wav"):
            leftover.unlink()
    PACE.write_text(json.dumps(pace, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
