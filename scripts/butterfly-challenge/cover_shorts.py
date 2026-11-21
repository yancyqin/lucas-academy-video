"""Covers for the two vertical shorts (Yancy 2026-11-16: 「都需要封面」「四个蝴蝶封面吧」), 1080x1920, zh and en.

    /Users/yqin/repo/playground/lucas-academy-video/.venv-align/bin/python scripts/butterfly-challenge/cover_shorts.py

Each cover shows that short's four butterflies, the two test pairs as the AIs saw them (one row a pair, A left, B
right), under the question 「哪两只是真的？」 / "Which Two Are Real?". The
backdrop is the same four pictures blurred and darkened. Lettering as the film's real-photo covers (cover_real.py):
heavy white sans with a soft shadow, 真的 / Real in green. One language per cover, no other text (cover standard).
Tiles are 4:3, cut from the 16:9 pictures around each butterfly (CENTRE, read off a 10% grid, every wing inside); the
glasswing spans 85% of its frame, wider than any 4:3 cut, so it keeps its whole picture over a blurred copy of itself.
Writes lucas-academy-video-data/butterfly-challenge/covers/shorts/cover-<name>.{en,zh}.jpg.
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_short import SHORTS  # noqa: E402
from cover_real import DATA, GREEN, WHITE, font, title  # noqa: E402

OUT = DATA / "covers/shorts"
W, H = 1080, 1920
TW, GAP = 522, 12  # tile width, gap between tiles
TH = round(TW * 3 / 4)
# where each butterfly's middle is, as a fraction of the picture's width; None = too wide for 4:3, show it whole
CENTRE = {"02-A": 0.485, "02-B": 0.64, "04-A": 0.51, "04-B": 0.49, "01-A": None, "01-B": 0.48, "07-A": 0.53, "07-B": 0.545}
TITLES = {"en": [[("Which Two", WHITE)], [("Are ", WHITE), ("Real", GREEN), ("?", WHITE)]],
          "zh": [[("哪两只", WHITE)], [("是", WHITE), ("真的", GREEN), ("？", WHITE)]]}


def fit(lines, lang: str, start: int, width: int = 1000) -> int:
    """The largest size (≤ start) at which every title line fits in width."""
    d = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    size = start
    while max(sum(d.textlength(t, font=font(lang, size)) for t, _ in line) for line in lines) > width:
        size -= 4
    return size


def tile_image(key: str, pic: Image.Image) -> Image.Image:
    """The picture as a TW x TH tile: a 4:3 window around the butterfly, or the whole picture over its blurred copy."""
    c = CENTRE[key]
    if c is None:
        bg = pic.resize((round(pic.width * TH / pic.height), TH), Image.LANCZOS)
        bg = bg.crop(((bg.width - TW) // 2, 0, (bg.width - TW) // 2 + TW, TH)).filter(ImageFilter.GaussianBlur(18))
        bg = Image.blend(bg, Image.new("RGB", (TW, TH), (8, 12, 10)), 0.35)
        fg = pic.resize((TW, round(TW * pic.height / pic.width)), Image.LANCZOS)
        bg.paste(fg, (0, (TH - fg.height) // 2))
        return bg
    w = round(pic.height * 4 / 3)
    left = min(max(round(c * pic.width - w / 2), 0), pic.width - w)
    return pic.crop((left, 0, left + w, pic.height)).resize((TW, TH), Image.LANCZOS)


def grid(pictures) -> Image.Image:
    """Four pictures as a 2x2 grid (rows = pairs) on a transparent layer, rounded, ringed and shadowed."""
    g = Image.new("RGBA", (2 * TW + GAP + 40, 2 * TH + GAP + 40), (0, 0, 0, 0))
    shadow = Image.new("RGBA", g.size, (0, 0, 0, 0))
    for k, pic in enumerate(pictures):
        x, y = 20 + (k % 2) * (TW + GAP), 20 + (k // 2) * (TH + GAP)
        tile = pic.convert("RGBA")
        mask = Image.new("L", (TW, TH), 0)
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, TW - 1, TH - 1], radius=16, fill=255)
        ImageDraw.Draw(shadow).rounded_rectangle([x, y + 8, x + TW, y + TH + 8], radius=16, fill=(0, 0, 0, 160))
        g.paste(tile, (x, y), mask)
        ImageDraw.Draw(g).rounded_rectangle([x, y, x + TW - 1, y + TH - 1], radius=16, outline=(255, 255, 255, 120), width=3)
    shadow = shadow.filter(ImageFilter.GaussianBlur(14))
    shadow.alpha_composite(g)
    return shadow


def cover(name: str, lang: str) -> Image.Image:
    keys = [f"{n:02d}-{side}" for n, _ in SHORTS[name] for side in "AB"]
    pictures = [tile_image(k, Image.open(DATA / f"pairs/{k}.jpg").convert("RGB")) for k in keys]
    # backdrop: the 2x2 grid itself, scaled to fill the frame, blurred and darkened
    flat = Image.new("RGB", (2 * TW, 2 * TH))
    for k, pic in enumerate(pictures):
        flat.paste(pic.resize((TW, TH)), ((k % 2) * TW, (k // 2) * TH))
    s = H / flat.height
    bg = flat.resize((round(flat.width * s), H), Image.LANCZOS)
    bg = bg.crop(((bg.width - W) // 2, 0, (bg.width - W) // 2 + W, H)).filter(ImageFilter.GaussianBlur(48))
    canvas = Image.blend(bg, Image.new("RGB", (W, H), (8, 12, 10)), 0.62).convert("RGBA")

    lines = TITLES[lang]
    size = fit(lines, lang, 230 if lang == "zh" else 190)
    title_h = size * 2.1
    g = grid(pictures)
    total = title_h + 60 + g.height - 40
    top = round((H - total) / 2 - 30)  # a little above centre: the Shorts title text covers the bottom
    title(canvas, lines, lang, size, W / 2, top, gap=1.08)
    canvas.alpha_composite(g, ((W - g.width) // 2, round(top + title_h + 60 - 20)))
    return canvas.convert("RGB")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for name in SHORTS:
        for lang in ("en", "zh"):
            path = OUT / f"cover-{name}.{lang}.jpg"
            cover(name, lang).save(path, quality=92)
            print(path)


if __name__ == "__main__":
    main()
