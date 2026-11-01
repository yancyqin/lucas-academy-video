"""The YouTube covers of a 中英阅读 film (ZhongYingCover, ZHONG-YING.md §Cover): 双语朗读 big, the title small.

    python3 scripts/zhong-ying/cover.py climb-higher <upload dir> [--layout a|b ...] [--lang zh|en ...]

Copies the art lab's full-size painting to public/zhong-ying/<film>/cover-<work>.jpg, renders each cover at
1920 × 1080 to out/zhong-ying/<film>/cover.<layout>.<lang>.png, and writes the YouTube thumbnail beside the film:
<upload dir>/cover.<layout>.<lang>.jpg at 1280 × 720 (YouTube takes up to 2 MB).
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/zhong-ying"))
from films import DATA  # noqa: E402

ART = {"climb-higher": "foreign-lands", "little-boats": "where-go-the-boats", "can-beauty-last": "sonnet-18"}   # as COVERS in ZhongYingVideo.tsx


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("film", choices=ART)
    ap.add_argument("dest", type=Path)
    ap.add_argument("--layout", nargs="+", default=["a"], choices=["a", "b"])   # the owner chose a (2026-10-27)
    ap.add_argument("--lang", nargs="+", default=["zh", "en"], choices=["zh", "en"])
    args = ap.parse_args()
    work = ART[args.film]
    src = sorted(DATA.glob(f"art-lab-*/assets/living/{work}.jpg"))[0]       # whichever art lab export has the painting
    shutil.copy2(src, ROOT / "public/zhong-ying" / args.film / f"cover-{work}.jpg")
    out = ROOT / "out/zhong-ying" / args.film
    out.mkdir(parents=True, exist_ok=True)
    args.dest.mkdir(parents=True, exist_ok=True)
    for layout in args.layout:
        for lang in args.lang:
            png = out / f"cover.{layout}.{lang}.png"
            props = json.dumps({"film": args.film, "lang": lang, "layout": layout})
            subprocess.run(["npx", "remotion", "still", "src/index.ts", "ZhongYingCover", str(png), f"--props={props}", "--log=error"],
                           cwd=ROOT, check=True)
            jpg = args.dest / f"cover.{layout}.{lang}.jpg"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(png), "-vf", "scale=1280:720:flags=lanczos", "-q:v", "2", str(jpg)],
                           check=True)
            size = jpg.stat().st_size
            print(f"{jpg}  {size / 1e6:.2f} MB" + ("  !! over YouTube's 2 MB" if size > 2e6 else ""))


if __name__ == "__main__":
    main()
