"""Render a 中英阅读 film and put its narration under the picture.

    python3 scripts/zhong-ying/render.py climb-higher [--concurrency 2] [--frames 0-299]

The picture (composition ZhongYing<Film>) is rendered muted, then joined with public/zhong-ying/<film>/narration.wav
(already at −16 LUFS: build_timeline.py) into out/zhong-ying/<film>/<film>.mp4. Prints the measured loudness and
duration. --frames renders just those frames to out/zhong-ying/<film>/part.mp4, with sound, for checking.
"""
import argparse
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COMPS = {"climb-higher": "ZhongYingClimbHigher", "little-boats": "ZhongYingLittleBoats", "can-beauty-last": "ZhongYingCanBeautyLast"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("film", choices=COMPS)
    ap.add_argument("--concurrency", type=int, default=2)
    ap.add_argument("--frames")
    args = ap.parse_args()
    pub = ROOT / "public/zhong-ying" / args.film
    out = ROOT / "out/zhong-ying" / args.film
    out.mkdir(parents=True, exist_ok=True)
    tl = json.loads((pub / "timeline.json").read_text())
    picture = out / ("part.picture.mp4" if args.frames else "picture.mp4")
    cmd = ["npx", "remotion", "render", "src/index.ts", COMPS[args.film], str(picture), "--muted",
           f"--concurrency={args.concurrency}", "--timeout=300000", "--offthreadvideo-cache-size-in-bytes=1500000000",
           "--crf=16", "--log=error"]
    if args.frames:
        cmd.append(f"--frames={args.frames}")
    subprocess.run(cmd, cwd=ROOT, check=True)
    film = out / ("part.mp4" if args.frames else f"{args.film}.mp4")
    start = int(args.frames.split("-")[0]) / tl["fps"] if args.frames else 0
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(picture), "-ss", f"{start:.3f}", "-i", str(pub / "narration.wav"),
                    "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac", "-b:a", "320k", "-shortest",
                    "-movflags", "+faststart", str(film)], check=True)
    got = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(film)],
                               capture_output=True, text=True, check=True).stdout)
    meter = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(film), "-af", "ebur128=peak=true", "-f", "null", "-"],
                           capture_output=True, text=True).stderr
    lufs = re.findall(r"I:\s+(-?[\d.]+) LUFS", meter)[-1]
    peak = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", meter)[-1]
    print(f"{film.relative_to(ROOT)}: {got:.2f}s (timeline {tl['durationSeconds']:.2f}s), {lufs} LUFS, true peak {peak} dBTP")


if __name__ == "__main__":
    main()
