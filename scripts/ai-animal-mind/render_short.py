"""Render the vertical shorts (AiAnimalShort, timelines from build_short.py): the English video and the Chinese track.

    python3 scripts/ai-animal-mind/render_short.py [ocean animals ...]   (default: every built short)

Yancy 2026-11-11: 「给英文视频配单独的中文音轨就好了」. Writes out/ai-animal-mind/shorts/<short>.mp4 (1080×1920, 30 fps,
H.264 CRF 18, the English mix as AAC 256k) and <short>.zh.m4a (the Chinese mix, AAC 256k, same length) to add in
YouTube Studio as a second audio track.
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PUB, OUT = ROOT / "public/ai-animal-mind/shorts", ROOT / "out/ai-animal-mind/shorts"
names = sys.argv[1:] or sorted(p.stem for p in PUB.glob("*.json"))
for name in names:
    silent = OUT / f"{name}.picture.mp4"
    subprocess.run(["npx", "remotion", "render", "src/index.ts", "AiAnimalShort", str(silent), "--props",
                    json.dumps({"short": name}), "--concurrency=4", "--crf=18", "--log=error",
                    "--offthreadvideo-cache-size-in-bytes=1000000000"], cwd=ROOT, check=True)
    film = OUT / f"{name}.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(silent), "-i", str(OUT / f"{name}.en.wav"), "-map", "0:v",
                    "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-shortest",
                    "-metadata:s:a:0", "language=eng", "-movflags", "+faststart", str(film)], check=True)
    silent.unlink()
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(OUT / f"{name}.zh.wav"), "-c:a", "aac", "-b:a", "256k",
                    "-ar", "48000", "-metadata:s:a:0", "language=zho", "-movflags", "+faststart",
                    str(OUT / f"{name}.zh.m4a")], check=True)
    print(film, flush=True)
