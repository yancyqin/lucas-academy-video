"""Contact sheet of images (or one frame of each video) with a small caption under each, for picking pictures.

    .venv-align/bin/python scripts/ai-animal-mind/sheet.py OUT.jpg [--cols 3] [--w 480] FILE[=caption] ...
A video gets its frame at 40 %; a missing file is skipped.
"""
import subprocess
import sys
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

args = sys.argv[1:]
out = Path(args.pop(0))
cols = int(args[args.index("--cols") + 1]) if "--cols" in args else 3
W = int(args[args.index("--w") + 1]) if "--w" in args else 480
args = [a for i, a in enumerate(args) if a not in ("--cols", "--w") and (i == 0 or args[i - 1] not in ("--cols", "--w"))]
H, CAP = round(W * 9 / 16), 24
FONT = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Unicode.ttf", 16)


def load(path: Path) -> Image.Image:
    if path.suffix.lower() in (".mp4", ".mov", ".webm", ".m4v", ".ogv"):
        dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                    str(path)], capture_output=True, text=True).stdout or 1)
        png = subprocess.run(["ffmpeg", "-loglevel", "error", "-ss", f"{dur * 0.4:.2f}", "-i", str(path), "-frames:v", "1",
                              "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True).stdout
        return Image.open(BytesIO(png)).convert("RGB")
    return Image.open(path).convert("RGB")


items = []
for a in args:
    f, _, cap = a.partition("=")
    if Path(f).is_file():
        items.append((Path(f), cap or Path(f).stem))
rows = (len(items) + cols - 1) // cols
sheet = Image.new("RGB", (cols * W, rows * (H + CAP)), "white")
draw = ImageDraw.Draw(sheet)
for i, (f, cap) in enumerate(items):
    im = load(f)
    im.thumbnail((W, H))
    x, y = (i % cols) * W, (i // cols) * (H + CAP)
    sheet.paste(im, (x + (W - im.width) // 2, y + (H - im.height) // 2))
    draw.text((x + 4, y + H + 3), cap[:60], fill="black", font=FONT)
sheet.save(out, quality=88)
print(out, len(items))
