"""Render 「跨越中等收入陷阱」 and lay in the Chinese mix.

  python3 scripts/middle-income-trap/render.py [--concurrency 4]

The picture renders silent (MiddleIncomeTrap) in four parts, so a crash costs one part; then one MP4 with the zh mix
(narration, Li Lu's clips, music) from build_timeline.py. Run assets.py and build_timeline.py first. Delete the parts
in out/middle-income-trap/ to render them again.
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FILM = "middle-income-trap"
OUT = ROOT / "out" / FILM
PARTS = 4
args = sys.argv[1:]
conc = args[args.index("--concurrency") + 1] if "--concurrency" in args else "4"

tl = json.loads((ROOT / "public" / FILM / "timeline.json").read_text())
frames = round(tl["durationSeconds"] * tl["fps"])
parts = []
for k in range(PARTS):
    a, b = k * frames // PARTS, (k + 1) * frames // PARTS - 1
    part = OUT / f"picture.part{k + 1}.mp4"
    parts.append(part)
    if part.exists():
        print(f"keep {part.name}")
        continue
    subprocess.run(["npx", "remotion", "render", "src/index.ts", "MiddleIncomeTrap", str(part), f"--frames={a}-{b}",
                    f"--concurrency={conc}", "--timeout=240000", "--offthreadvideo-cache-size-in-bytes=1000000000",
                    "--crf=17", "--log=error"], cwd=ROOT, check=True)
(OUT / "parts.txt").write_text("".join(f"file '{p.name}'\n" for p in parts))
picture = OUT / "picture.mp4"
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(OUT / "parts.txt"), "-c", "copy", "-an",
                str(picture)], check=True)
film = OUT / "delivery" / f"{FILM}.mp4"
film.parent.mkdir(parents=True, exist_ok=True)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(picture), "-i", str(OUT / "mix.zh.wav"),
                "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "256k", "-ar", "48000",
                "-metadata:s:a:0", "language=zho", "-movflags", "+faststart", "-shortest", str(film)], check=True)
print(film)
