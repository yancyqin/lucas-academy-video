"""Render 「怎么骗过 AI：面包还是狗？」 with the mixes build_timeline.py made for the same timeline (copied from the butterfly film).

  python3 scripts/bread-or-dog/render.py --tag <tag> [--draft] [--concurrency 4] [--name NAME]

public/bread-or-dog/timeline.json is whatever build_timeline.py wrote last, so build and render one tag at a
time. The picture renders silent (BreadOrDog) in parts, so a crash costs one part. Then, as in
the butterfly film (Yancy, 2026-11-16: 「英文视频配中文音轨」): <NAME>.mp4 with the English mix
(out/bread-or-dog/<tag>/mix.en.wav) and <NAME>.zh.m4a, the Chinese mix on its own, for YouTube's added audio
track. A tag with only one mix (the voice test) gets just the MP4 with that mix. --draft renders at half size.
Parts are kept until the timeline changes. The mixes are mono; both files are exported as stereo (-ac 2), the
format every film is checked against (README "Automatic checks": aac, 48 kHz, stereo).
"""
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
args = sys.argv[1:]
TAG = args[args.index("--tag") + 1]
DRAFT = "--draft" in args
CONC = args[args.index("--concurrency") + 1] if "--concurrency" in args else "4"
NAME = args[args.index("--name") + 1] if "--name" in args else "bread-or-dog"
OUT = ROOT / "out/bread-or-dog" / TAG
PARTS_DIR = OUT / ("parts-draft" if DRAFT else "parts")

tl_path = ROOT / "public/bread-or-dog/timeline.json"
tl = json.loads(tl_path.read_text())
stamp = hashlib.md5(tl_path.read_bytes()).hexdigest()
if (PARTS_DIR / "timeline.md5").exists() and (PARTS_DIR / "timeline.md5").read_text() != stamp:
    shutil.rmtree(PARTS_DIR)
PARTS_DIR.mkdir(parents=True, exist_ok=True)
(PARTS_DIR / "timeline.md5").write_text(stamp)
frames = round(tl["durationSeconds"] * tl["fps"])
n_parts = max(1, min(4, frames // 1800 + 1))
parts = []
for k in range(n_parts):
    a, b = k * frames // n_parts, (k + 1) * frames // n_parts - 1
    part = PARTS_DIR / f"picture.part{k + 1}.mp4"
    parts.append(part)
    if part.exists():
        print(f"keep {part.name}")
        continue
    subprocess.run(["npx", "remotion", "render", "src/index.ts", "BreadOrDog", str(part), f"--frames={a}-{b}",
                    f"--concurrency={CONC}", "--timeout=240000", "--offthreadvideo-cache-size-in-bytes=1000000000",
                    "--crf=17", "--log=error", *(["--scale=0.5"] if DRAFT else [])], cwd=ROOT, check=True)
(PARTS_DIR / "parts.txt").write_text("".join(f"file '{p.name}'\n" for p in parts))
picture = PARTS_DIR / "picture.mp4"
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(PARTS_DIR / "parts.txt"), "-c", "copy",
                "-an", str(picture)], check=True)
suffix = ".draft" if DRAFT else ""
main_lang = "en" if (OUT / "mix.en.wav").exists() else "zh"
film = OUT / f"{NAME}{suffix}.mp4"
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(picture), "-i", str(OUT / f"mix.{main_lang}.wav"),
                "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-ac", "2",
                "-metadata:s:a:0", f"language={'eng' if main_lang == 'en' else 'zho'}", "-movflags", "+faststart", "-shortest",
                str(film)], check=True)
print(film)
if main_lang == "en" and (OUT / "mix.zh.wav").exists():
    dur = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(film)],
                         capture_output=True, text=True, check=True).stdout.strip()
    m4a = OUT / f"{NAME}{suffix}.zh.m4a"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(OUT / "mix.zh.wav"), "-t", dur, "-c:a", "aac", "-b:a", "256k",
                    "-ar", "48000", "-ac", "2", "-metadata:s:a:0", "language=zho", "-movflags", "+faststart", str(m4a)],
                   check=True)
    print(m4a)
