"""Whisper-check the tightened Language Bridge narration (what the films actually play).

Uses the same rules as reciprocal-doors-retake.py (whole-line match, homophones,
must / must-not words, word-for-word lines) on the `reciprocal-doors-tight`
copies, so a clipped first or last sound from tightening would show up here.

    cd ../lucas-academy-media && PYTHONPATH=src .conda/bin/python ../lucas-academy-video/scripts/reciprocal-doors-check.py en [--played] [line ids...]
"""
from __future__ import annotations

import difflib
import importlib.util
import json
import sys
from pathlib import Path

import whisper

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("retake", HERE / "reciprocal-doors-retake.py")
retake = importlib.util.module_from_spec(spec)
spec.loader.exec_module(retake)


def main() -> None:
    args = sys.argv[1:]
    # --played: check the copies the film plays (public/audio, after the film's tempo).
    played = "--played" in args
    track, *rest = [a for a in args if a != "--played"]
    wanted = set(rest)
    voice, scripts = retake.TRACKS[track]
    folder = (HERE.parent / "public/audio/reciprocal-doors" / track) if played else retake.MEDIA / "outputs" / voice / "reciprocal-doors-tight"
    asr = whisper.load_model("medium", device="cpu")
    bad = 0
    for name, lang in scripts:
        for line in json.loads((retake.MEDIA / "data/scripts" / f"{name}.json").read_text(encoding="utf-8"))["lines"]:
            if wanted and line["id"] not in wanted:
                continue
            wav = folder / f"{line['id']}.wav"
            if not wav.exists():
                print(f"MISSING {wav}")
                bad += 1
                continue
            prompt = "以下是普通话的句子，使用简体中文。" if lang == "zh" else None
            heard = asr.transcribe(str(wav), language=lang, fp16=False, initial_prompt=prompt)["text"].strip()
            ratio = difflib.SequenceMatcher(None, retake.norm(line.get("check", line["text"]), lang), retake.norm(heard, lang)).ratio()
            must, must_not = retake.RULES.get((track, line["id"]), ([], []))
            flat = heard.lower()
            ok = (
                (ratio == 1.0 if (track, line["id"]) in retake.EXACT else ratio >= (0.94 if lang == "zh" else 0.9))
                and all(any(a in flat for a in m.split("|")) for m in must)
                and not any(n in flat for n in must_not)
            )
            bad += not ok
            print(f"{'OK ' if ok else 'BAD'} {ratio:.2f} {line['id']}: {heard}", flush=True)
    print(f"{bad} problem(s)")


if __name__ == "__main__":
    main()
