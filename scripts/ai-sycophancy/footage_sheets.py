#!/usr/bin/env python3
"""One frame sheet per shot for the footage review: every candidate is a row of four frames (15/40/65/90 %).

  ../lucas-academy-media/.conda/bin/python scripts/ai-sycophancy/footage_sheets.py [<search file> <sheet suffix>]
Reads footage/search/pexels.json (or the given round, e.g. pexels2.json -2) and the previews in
footage/preview/<shot>-<id>.mp4 (lucas-academy-video-data/ai-sycophancy); writes footage/sheets/<shot><suffix>.jpg
with each row labelled #n, Pexels id, size, fps and length.
"""
import json
import subprocess
import sys
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
DATA = next(p / "lucas-academy-video-data" for p in ROOT.parents if (p / "lucas-academy-video-data").is_dir())
FOOT = DATA / "ai-sycophancy/footage"
W, H, LABEL = 320, 180, 26
FONT = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Unicode.ttf", 18)


def frame(path: Path, t: float) -> Image.Image:
    png = subprocess.run(["ffmpeg", "-loglevel", "error", "-ss", f"{t:.2f}", "-i", str(path), "-frames:v", "1",
                          "-vf", f"scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2",
                          "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True).stdout
    return Image.open(BytesIO(png)) if png else Image.new("RGB", (W, H), "gray")


def length(path: Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                         capture_output=True, text=True).stdout
    return float(out or 0)


name, suffix = (sys.argv[1], sys.argv[2]) if len(sys.argv) > 2 else ("pexels.json", "")
search = json.loads((FOOT / "search" / name).read_text())
(FOOT / "sheets").mkdir(exist_ok=True)
for shot, items in search.items():
    rows = [(n, x) for n, x in enumerate(items[:10], 1) if (FOOT / f"preview/{shot}-{x['id']}.mp4").exists()]
    sheet = Image.new("RGB", (4 * W, len(rows) * (H + LABEL)), "white")
    draw = ImageDraw.Draw(sheet)
    for r, (n, x) in enumerate(rows):
        path = FOOT / f"preview/{shot}-{x['id']}.mp4"
        dur = length(path)
        y = r * (H + LABEL)
        draw.text((6, y + 3), f"#{n}  pexels {x['id']}  {x['w']}x{x['h']}  {x['fps']} fps  {x['dur']} s  ·  {x['u']}",
                  fill="black", font=FONT)
        for c, f in enumerate((0.15, 0.4, 0.65, 0.9)):
            sheet.paste(frame(path, dur * f), (c * W, y + LABEL))
    sheet.save(FOOT / f"sheets/{shot}{suffix}.jpg", quality=85)
    print(shot, len(rows), flush=True)
