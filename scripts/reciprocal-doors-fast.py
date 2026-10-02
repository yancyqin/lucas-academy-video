"""Native fast takes for the Chinese lines the 1.3x tempo stretch does not survive.

The Chinese film plays at 1.3x (TEMPO in reciprocal-doors-prep.mjs): its takes are
time-stretched. A few stretched lines read wrong to Whisper (图画 → 读话, 练 →
恋爱, a breath turned into 呵呵). For those, voice the line again AT the faster pace
instead -- aiming at 1.3x the film's median speaking rate, checked like every take
on the tightened audio -- and keep it in reciprocal-doors-fast/ (already tightened).
The prep step plays a fast take as it is, without stretching it again.

    cd ../lucas-academy-media && PYTHONPATH=src .conda/bin/python ../lucas-academy-video/scripts/reciprocal-doors-fast.py rd07-03 rd07-06
"""
from __future__ import annotations

import difflib
import importlib.util
import json
import sys
import tempfile
from pathlib import Path

import soundfile as sf
import whisper
from lucas_media.cosyvoice_engine import CosyVoiceEngine
from lucas_media.joke import add_peak_headroom, save_wav

HERE = Path(__file__).resolve().parent
MEDIA = HERE.parent.parent / "lucas-academy-media"
SCRIPT = MEDIA / "data/scripts/reciprocal-doors-zh.json"
FAST = MEDIA / "outputs/fangfang/zh/reciprocal-doors-fast"
PACE = HERE.parent / "src/scripts/reciprocal-doors.pace.zh.json"
TEMPO = 1.3
# Readings forced with CosyVoice pinyin tokens for the fast take only (the
# subtitle and the Whisper check keep the character): 练 kept coming out 连 / 脸.
PRONOUNCE = {"rd07-06": {"练": "[l][iàn]"}}
TOL = 0.10
SPEED = (1.0, 1.7)
TRIES = 5


def load(name: str):
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), HERE / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


retake = load("reciprocal-doors-retake")
pace = load("reciprocal-doors-pace")
tighten = load("reciprocal-doors-tighten").tighten


def main() -> None:
    wanted = sys.argv[1:]
    if not wanted:
        raise SystemExit("name the line ids to re-voice fast")
    lines = {l["id"]: l for l in json.loads(SCRIPT.read_text(encoding="utf-8"))["lines"]}
    target = json.loads(PACE.read_text(encoding="utf-8"))["target"] * TEMPO
    FAST.mkdir(parents=True, exist_ok=True)
    engine = CosyVoiceEngine("fangfang/zh")
    asr = whisper.load_model("medium", device="cpu")
    for line_id in wanted:
        line = lines[line_id]
        expected = line.get("check", line["text"])
        must, must_not = retake.RULES.get(("zh", line_id), ([], []))
        speed = min(SPEED[1], max(SPEED[0], line.get("speed", 1.0) * TEMPO))
        best = None
        for attempt in range(1, TRIES + 1):
            spoken = line["text"]
            for char, tokens in PRONOUNCE.get(line_id, {}).items():
                spoken = spoken.replace(char, tokens)
            speech, sr, _ = engine.synthesize(spoken, target_language="zh", mode=line["mode"], speed=speed, instruction=line.get("instruct", ""))
            y = tighten(add_peak_headroom(speech, peak_dbfs=-2.0).squeeze(0).numpy(), sr)
            with tempfile.NamedTemporaryFile(suffix=".wav") as played:
                sf.write(played.name, y, sr, subtype="PCM_16")
                heard = asr.transcribe(played.name, language="zh", fp16=False, initial_prompt="以下是普通话的句子，使用简体中文。")["text"].strip()
                r = pace.rate(Path(played.name), expected)  # tightening again is a no-op
            ratio = difflib.SequenceMatcher(None, retake.norm(expected, "zh"), retake.norm(heard, "zh")).ratio()
            reads = ratio >= 0.94 and all(any(a in heard for a in m.split("|")) for m in must) and not any(n in heard for n in must_not)
            err = r / target - 1
            print(f"{line_id} try {attempt} @ {speed:.2f}: {r / target:.2f}x the 1.3x target, ratio {ratio:.2f} {'OK' if reads else 'MISREAD'} | {heard}", flush=True)
            if reads and (best is None or abs(err) < abs(best[1])):
                best = (y, err, speed, sr)
            if reads and abs(err) <= TOL:
                break
            if reads:
                speed = min(SPEED[1], max(SPEED[0], speed / (1 + err)))
        if best is None:
            print(f"   {line_id}: no fast take read correctly; the stretched take stays", flush=True)
            continue
        y, err, used, sr = best
        sf.write(FAST / f"{line_id}.wav", y, sr, subtype="PCM_16")
        print(f"   {line_id}: kept a fast take at speed {used:.2f} ({1 + err:.2f}x the target)", flush=True)


if __name__ == "__main__":
    main()
