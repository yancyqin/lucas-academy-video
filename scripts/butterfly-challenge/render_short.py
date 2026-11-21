"""Render the vertical shorts built by build_short.py: one MP4 per short (music only, so it serves both languages).

  python3 scripts/butterfly-challenge/render_short.py [name ...] [--draft]

The picture renders silent (ButterflyShort, props {name}), then the music mix is muxed in. --draft renders at half size.
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "out/butterfly-challenge/shorts"
args = sys.argv[1:]
DRAFT = "--draft" in args
names = [a for a in args if not a.startswith("--")] or ["mormon-leopard", "glasswing-purple"]

for name in names:
    d = OUT / name
    picture = d / ("picture.draft.mp4" if DRAFT else "picture.mp4")
    subprocess.run(["npx", "remotion", "render", "src/index.ts", "ButterflyShort", str(picture),
                    f"--props={json.dumps({'name': name})}", "--concurrency=6", "--crf=17", "--log=error",
                    "--offthreadvideo-cache-size-in-bytes=1000000000", *(["--scale=0.5"] if DRAFT else [])], cwd=ROOT, check=True)
    mp4 = d / f"{name}{'.draft' if DRAFT else ''}.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(picture), "-i", str(d / "mix.wav"), "-map", "0:v", "-map", "1:a",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-movflags", "+faststart", "-shortest", str(mp4)],
                   check=True)
    dur = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(mp4)],
                         capture_output=True, text=True, check=True).stdout.strip()
    print(mp4, dur)
