"""Render the vertical shorts built by build_short.py: per short an English MP4 and the Chinese track as M4A.

  python3 scripts/butterfly-challenge/render_short.py [name ...] [--draft]

Like the film (render.py): the picture renders silent (ButterflyShort, props {name}), then the English mix is muxed
into <name>.mp4 and the Chinese mix becomes <name>.zh.m4a, the same length. --draft renders at half size.
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "out/butterfly-challenge/shorts"
args = sys.argv[1:]
DRAFT = "--draft" in args
names = [a for a in args if not a.startswith("--")] or ["blue-mormon", "leopard"]

for name in names:
    d = OUT / name
    picture = d / ("picture.draft.mp4" if DRAFT else "picture.mp4")
    subprocess.run(["npx", "remotion", "render", "src/index.ts", "ButterflyShort", str(picture),
                    f"--props={json.dumps({'name': name})}", "--concurrency=6", "--crf=17", "--log=error",
                    "--offthreadvideo-cache-size-in-bytes=1000000000", *(["--scale=0.5"] if DRAFT else [])], cwd=ROOT, check=True)
    suffix = ".draft" if DRAFT else ""
    mp4 = d / f"{name}{suffix}.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(picture), "-i", str(d / "mix.en.wav"), "-map", "0:v", "-map", "1:a",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-metadata:s:a:0", "language=eng",
                    "-movflags", "+faststart", "-shortest", str(mp4)], check=True)
    dur = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(mp4)],
                         capture_output=True, text=True, check=True).stdout.strip()
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(d / "mix.zh.wav"), "-t", dur, "-c:a", "aac", "-b:a", "256k",
                    "-ar", "48000", "-metadata:s:a:0", "language=zho", "-movflags", "+faststart", str(d / f"{name}{suffix}.zh.m4a")],
                   check=True)
    print(mp4, dur)
