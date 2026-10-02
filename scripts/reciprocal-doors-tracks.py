"""Mix the narration of each Language Bridge film into one full-length track.

Two films (owner, 2026-10-01): the Chinese video and the English video, each on
its own timeline (scripts/reciprocal-doors-prep.mjs). For each film this writes
out/reciprocal-doors/<lang>/:
  language-bridge.<lang>.wav   48 kHz 16-bit mono, -16 LUFS (linear gain only)
  language-bridge.<lang>.mp3   for listening
  language-bridge.<lang>.timing.csv   line id, start, end, texts
(the film's captions in both languages are written there by the prep step).

    ../lucas-academy-media/.conda/bin/python scripts/reciprocal-doors-tracks.py [zh|en]
"""
from __future__ import annotations

import csv
import json
import re
import sys
import subprocess
import tempfile
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "public"
OUT = ROOT / "out/reciprocal-doors"
RATE = 48000
LOUDNESS = -16.0  # integrated LUFS for both languages (YouTube plays speech at about -14)


def read_mono(path: Path) -> np.ndarray:
    with tempfile.NamedTemporaryFile(suffix=".wav") as tmp:
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(path), "-ac", "1", "-ar", str(RATE), tmp.name], check=True)
        audio, _ = sf.read(tmp.name, dtype="float32")
    return audio


def loudness_match(source: Path, target: Path) -> None:
    """Two-pass loudnorm with linear gain only: the performance's dynamics stay as they are."""
    probe = subprocess.run(
        ["ffmpeg", "-hide_banner", "-i", str(source), "-af", f"loudnorm=I={LOUDNESS}:TP=-1.5:LRA=20:print_format=json", "-f", "null", "-"],
        capture_output=True, text=True, check=True,
    ).stderr
    # ffmpeg prints the measurement as the last {...} block, followed by its summary line.
    measured = json.loads(re.findall(r"\{[^{}]*\}", probe)[-1])
    chain = (
        f"loudnorm=I={LOUDNESS}:TP=-1.5:LRA=20:linear=true:"
        f"measured_I={measured['input_i']}:measured_TP={measured['input_tp']}:"
        f"measured_LRA={measured['input_lra']}:measured_thresh={measured['input_thresh']}:offset={measured['target_offset']}"
    )
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(source), "-af", chain, "-ar", str(RATE), "-c:a", "pcm_s16le", str(target)], check=True)


def film(lang: str) -> None:
    timeline = json.loads((ROOT / f"src/scripts/reciprocal-doors.timeline.{lang}.json").read_text(encoding="utf-8"))
    if timeline.get("missing"):
        raise SystemExit(f"{lang}: narration missing for {len(timeline['missing'])} parts; run the narration first")
    out = OUT / lang
    out.mkdir(parents=True, exist_ok=True)
    total = int(round(timeline["durationSeconds"] * RATE))
    mix = np.zeros(total, dtype="float32")
    for segment in timeline["segments"]:
        for chunk in segment["chunks"]:
            for part in chunk["tracks"][lang]:
                audio = read_mono(PUBLIC / part["file"])
                at = int(round((chunk["start"] + part["offset"]) * RATE))
                mix[at:at + len(audio)] += audio[: total - at]
    with tempfile.NamedTemporaryFile(suffix=".wav") as raw:
        sf.write(raw.name, mix, RATE, subtype="FLOAT")
        wav = out / f"language-bridge.{lang}.wav"
        loudness_match(Path(raw.name), wav)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(wav), "-c:a", "libmp3lame", "-b:a", "160k", str(wav.with_suffix(".mp3"))], check=True)
    with (out / f"language-bridge.{lang}.timing.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.writer(handle)
        writer.writerow(["segment", "line", "start_s", "end_s", "zh", "en"])
        for segment in timeline["segments"]:
            for chunk in segment["chunks"]:
                writer.writerow([segment["id"], chunk["id"], f"{chunk['start']:.3f}", f"{chunk['start'] + chunk['slot']:.3f}", chunk["zh"], chunk["en"]])
    print(f"{lang}: {wav.name} {sf.info(wav).duration:.2f}s, timing + captions in {out}")


def main() -> None:
    for lang in sys.argv[1:] or ["zh", "en"]:
        film(lang)


if __name__ == "__main__":
    main()
