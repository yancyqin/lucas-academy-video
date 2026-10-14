"""Contact sheets of Pexels candidates: one row per clip, five frames across its length.

  sheet.py CANDIDATES.json OUT_DIR [--rows 10]

CANDIDATES.json maps a slot to a list of Pexels video ids. Pexels serves 15 evenly spaced
preview frames per video at images.pexels.com/videos/<id>/pictures/preview-<k>.jpg, so a
clip can be judged start to end (a time-lapse from dark to light, a cut inside the clip,
a person walking into frame) without downloading it.
"""
import io
import json
import pathlib
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

from PIL import Image, ImageDraw, ImageFont

FRAMES = (0, 4, 7, 10, 14)
TW, TH = 256, 144
LABEL = 150
FONT = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 17)
SEARCH = pathlib.Path("/Users/yqin/repo/playground/lucas-academy-video-data/bach-suite/footage/search")
CACHE = SEARCH / "preview-cache"
# older uploads have no preview-<k> frames (404): fall back to the search thumbnail,
# id -> "<id>/<name>.jpeg" under images.pexels.com/videos/, copied from the search results
THUMBS = json.loads((SEARCH / "thumbs.json").read_text()) if (SEARCH / "thumbs.json").exists() else {}


def frame(vid, k):
    p = CACHE / f"{vid}-{k}.jpg"
    if not p.exists() and str(vid) in THUMBS:
        if k:
            return Image.new("RGB", (TW, TH), (35, 35, 35))
        p = CACHE / f"{vid}-thumb.jpg"
        url = f"https://images.pexels.com/videos/{THUMBS[str(vid)]}?auto=compress&cs=tinysrgb&w=750"
    else:
        url = f"https://images.pexels.com/videos/{vid}/pictures/preview-{k}.jpg"
    if not p.exists():
        # curl, not urllib: the conda Python has no CA bundle
        if subprocess.run(["curl", "-sfL", "--max-time", "30", "-o", str(p), url]).returncode:
            return Image.new("RGB", (TW, TH), (60, 0, 0))
    im = Image.open(io.BytesIO(p.read_bytes())).convert("RGB")
    im.thumbnail((TW, TH))
    canvas = Image.new("RGB", (TW, TH))
    canvas.paste(im, ((TW - im.width) // 2, (TH - im.height) // 2))
    return canvas


def main():
    cands = json.loads(pathlib.Path(sys.argv[1]).read_text())
    out = pathlib.Path(sys.argv[2])
    rows_per = int(sys.argv[sys.argv.index("--rows") + 1]) if "--rows" in sys.argv else 10
    out.mkdir(parents=True, exist_ok=True)
    CACHE.mkdir(exist_ok=True)
    rows = [(slot, i, vid) for slot, ids in cands.items() for i, vid in enumerate(ids)]
    with ThreadPoolExecutor(16) as ex:
        ims = list(ex.map(lambda r: [frame(r[2], k) for k in FRAMES], rows))
    for s in range(0, len(rows), rows_per):
        chunk = list(zip(rows, ims))[s:s + rows_per]
        sheet = Image.new("RGB", (LABEL + len(FRAMES) * (TW + 4), len(chunk) * (TH + 6)), (20, 20, 20))
        d = ImageDraw.Draw(sheet)
        for r, ((slot, i, vid), frames) in enumerate(chunk):
            y = r * (TH + 6)
            d.text((6, y + 40), f"{slot}.{i}", font=FONT, fill=(255, 220, 0))
            d.text((6, y + 66), str(vid), font=FONT, fill=(200, 200, 200))
            for c, im in enumerate(frames):
                sheet.paste(im, (LABEL + c * (TW + 4), y))
        path = out / f"sheet-{s // rows_per + 1:02d}.jpg"
        sheet.save(path, quality=85)
        print(path)


if __name__ == "__main__":
    main()
