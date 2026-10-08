"""Render one film in chunks (muted), join them, and put the narration mix under the picture.

  python3 scripts/fun-informatics-01/render.py zh|en [--chunks 4] [--concurrency 6]

A chunk that fails is tried again once with lower concurrency, so a stuck frame costs one chunk,
not the whole film. Writes out/fun-informatics-01/delivery/fun-informatics-01.LANG.mp4.
"""
import argparse
import json
import math
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PUB = ROOT / "public/fun-informatics-01"
WORK = ROOT / "out/fun-informatics-01/chunks"
OUT = ROOT / "out/fun-informatics-01/delivery"
FILM_NAME = "fun-informatics-01"
COMP_PREFIX = "FunInformatics01"
LANGS = ("zh", "en")


def render(comp: str, out: Path, frames: str, concurrency: int) -> bool:
    cmd = ["npx", "remotion", "render", "src/index.ts", comp, str(out), f"--frames={frames}", "--muted",
           f"--concurrency={concurrency}", "--timeout=300000", "--offthreadvideo-cache-size-in-bytes=1500000000", "--log=error"]
    return subprocess.run(cmd, cwd=ROOT).returncode == 0


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("lang", choices=LANGS)
    ap.add_argument("--chunks", type=int, default=4)
    ap.add_argument("--concurrency", type=int, default=6)
    args = ap.parse_args()
    tl = json.loads((PUB / f"timeline.{args.lang}.json").read_text())
    total = math.ceil(tl["durationSeconds"] * tl["fps"])
    comp = f"{COMP_PREFIX}{args.lang.capitalize()}"
    WORK.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    size = math.ceil(total / args.chunks)
    parts = []
    for k in range(args.chunks):
        a, b = k * size, min(total, (k + 1) * size) - 1
        part = WORK / f"{args.lang}.{k:02d}.mp4"
        parts.append(part)
        if part.exists() and part.with_suffix(".ok").exists():
            print(f"{args.lang} chunk {k}: done earlier", flush=True)
            continue
        print(f"{args.lang} chunk {k}: frames {a}-{b}", flush=True)
        if not render(comp, part, f"{a}-{b}", args.concurrency) and not render(comp, part, f"{a}-{b}", max(2, args.concurrency // 2)):
            sys.exit(f"{args.lang} chunk {k} failed twice")
        part.with_suffix(".ok").touch()
    listing = WORK / f"{args.lang}.txt"
    listing.write_text("".join(f"file '{p}'\n" for p in parts))
    film = OUT / f"{FILM_NAME}.{args.lang}.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(listing),
                    "-i", str(PUB / f"audio/{args.lang}.mix.wav"), "-map", "0:v:0", "-map", "1:a:0",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "320k", "-shortest", "-movflags", "+faststart", str(film)], check=True)
    got = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(film)],
                               capture_output=True, text=True, check=True).stdout)
    print(f"{film.name}: {got:.1f}s (timeline {tl['durationSeconds']:.1f}s)", flush=True)


if __name__ == "__main__":
    main()
