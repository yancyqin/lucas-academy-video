"""Render 「法国人走上街头，出路在哪里？」 and lay in both audio tracks.

  python3 scripts/news-education-01/render.py [--concurrency 2]

The picture renders once (NewsEducation01, silent), in four parts so a crash costs one part; then one MP4 with the zh
mix as the default track and the en mix as a second track (language-tagged), plus the en mix on its own for YouTube
Studio's "add audio track". Run build_timeline.py first (not --draft).
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FILM = "news-education-01"
OUT = ROOT / "out" / FILM
PARTS = 4
args = sys.argv[1:]
conc = args[args.index("--concurrency") + 1] if "--concurrency" in args else "2"

tl = json.loads((ROOT / "public" / FILM / "timeline.json").read_text())
assert not tl["draft"], "the timeline still has estimated lines: build it without --draft"
frames = round(tl["durationSeconds"] * tl["fps"])
parts = []
for k in range(PARTS):
    a, b = k * frames // PARTS, (k + 1) * frames // PARTS - 1
    part = OUT / f"picture.part{k + 1}.mp4"
    parts.append(part)
    if part.exists():
        print(f"keep {part.name}")
        continue
    subprocess.run(["npx", "remotion", "render", "src/index.ts", "NewsEducation01", str(part), f"--frames={a}-{b}",
                    f"--concurrency={conc}", "--timeout=240000", "--offthreadvideo-cache-size-in-bytes=2000000000",
                    "--crf=17", "--log=error"], cwd=ROOT, check=True)
(OUT / "parts.txt").write_text("".join(f"file '{p.name}'\n" for p in parts))
picture = OUT / "picture.mp4"
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(OUT / "parts.txt"), "-c", "copy", "-an", str(picture)], check=True)
film = OUT / "delivery" / f"{FILM}.mp4"
film.parent.mkdir(parents=True, exist_ok=True)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(picture), "-i", str(OUT / "mix.zh.wav"), "-i", str(OUT / "mix.en.wav"),
                "-map", "0:v", "-map", "1:a", "-map", "2:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "256k", "-ar", "48000",
                "-metadata:s:a:0", "language=zho", "-metadata:s:a:0", "title=中文", "-disposition:a:0", "default",
                "-metadata:s:a:1", "language=eng", "-metadata:s:a:1", "title=English", "-disposition:a:1", "0",
                "-movflags", "+faststart", "-shortest", str(film)], check=True)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(OUT / "mix.en.wav"), "-c:a", "pcm_s24le", "-ar", "48000",
                str(OUT / "delivery" / f"{FILM}.en-audio.wav")], check=True)
print(film)
