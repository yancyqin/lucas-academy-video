"""Covers A and B made from real photographs (Yancy 2026-11-12: 「用A B的蝴蝶，但使用真实的照片合成」).

    /Users/yqin/repo/playground/lucas-academy-video/.venv-align/bin/python scripts/butterfly-challenge/cover_real.py

The Codex covers (cover_images.py) were whole AI pictures. These keep their ideas and titles but every butterfly is a
real photograph, never passed through an image model (an edit would redraw it). The photos are only cropped, scaled
and set on a blurred, darkened copy of themselves; the title is lettered here in the Codex covers' style (heavy white
sans with a soft shadow, the same accent colours: Real / 真的 green, AI amber).
  A — two European Peacocks side by side as photo cards, like the film's pair screen: Dimitǎr Boevski (iNaturalist
      359063525, CC BY) and Cheongweei Gan (the film's pair 5 photo, iNaturalist 566316447, CC BY). Both are real.
  B — the glasswing on a red zinnia: Jason Eckberg (the film's pair 1 photo, iNaturalist, CC BY), title on the right.
Writes lucas-academy-video-data/butterfly-challenge/covers/real/cover-{a,b}-real.{en,zh}.jpg (1280x720).
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

DATA = Path("/Users/yqin/repo/playground/lucas-academy-video-data/butterfly-challenge")
OUT = DATA / "covers/real"
W, H = 1280, 720
GREEN, AMBER, WHITE = (92, 224, 40), (255, 163, 26), (255, 255, 255)
EN = "/Library/Fonts/Montserrat-Bold.ttf"
ZH = ("/System/Library/Fonts/Hiragino Sans GB.ttc", 1)  # W6


def font(lang: str, size: int):
    return ImageFont.truetype(EN, size) if lang == "en" else ImageFont.truetype(ZH[0], size, index=ZH[1])


def cover_bg(img: Image.Image, blur: float = 28, dark: float = 0.55) -> Image.Image:
    """The photo scaled to fill the frame, blurred and darkened: a backdrop that is still that photo."""
    s = max(W / img.width, H / img.height)
    b = img.resize((round(img.width * s), round(img.height * s)), Image.LANCZOS)
    b = b.crop(((b.width - W) // 2, (b.height - H) // 2, (b.width - W) // 2 + W, (b.height - H) // 2 + H))
    b = b.filter(ImageFilter.GaussianBlur(blur))
    return Image.blend(b, Image.new("RGB", (W, H), (8, 12, 10)), dark)


def title(canvas: Image.Image, lines, lang: str, size: int, anchor_x: float, top: int, align: str = "center",
          gap: float = 1.08) -> None:
    """lines: [[(text, colour), ...], ...]; drawn with a soft drop shadow; Chinese thickened with a same-colour stroke."""
    f = font(lang, size)
    stroke = max(1, size // 40) if lang == "zh" else 0
    shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    text = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ds, dt = ImageDraw.Draw(shadow), ImageDraw.Draw(text)
    y = top
    for line in lines:
        width = sum(dt.textlength(t, font=f) for t, _ in line) + stroke * 2
        x = anchor_x - width / 2 if align == "center" else anchor_x - width
        for t, colour in line:
            ds.text((x, y + size * 0.05), t, font=f, fill=(0, 0, 0, 170), stroke_width=stroke, stroke_fill=(0, 0, 0, 170))
            dt.text((x, y), t, font=f, fill=colour, stroke_width=stroke, stroke_fill=colour)
            x += dt.textlength(t, font=f)
        y += size * gap
    shadow = shadow.filter(ImageFilter.GaussianBlur(size * 0.07))
    canvas.alpha_composite(shadow)
    canvas.alpha_composite(text)


def card(canvas: Image.Image, img: Image.Image, box, at, w: int) -> None:
    """A rounded photo card: img cropped to box (3:2), scaled to width w, with a soft shadow."""
    c = img.crop(box)
    h = round(w * c.height / c.width)
    c = c.resize((w, h), Image.LANCZOS).convert("RGBA")
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, w - 1, h - 1], radius=18, fill=255)
    sh = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([at[0] + 4, at[1] + 10, at[0] + w + 4, at[1] + h + 10], radius=18, fill=(0, 0, 0, 150))
    canvas.alpha_composite(sh.filter(ImageFilter.GaussianBlur(14)))
    canvas.paste(c, at, mask)


TITLES = {
    "a": {"en": [[("Which One", WHITE)], [("Is ", WHITE), ("Real", GREEN), ("?", WHITE)]],
          "zh": [[("哪一只", WHITE)], [("是", WHITE), ("真的", GREEN), ("？", WHITE)]]},
    "b": {"en": [[("Real", WHITE)], [("or ", WHITE), ("AI", AMBER), ("?", WHITE)]],
          "zh": [[("真的", WHITE)], [("还是", WHITE), ("AI", AMBER), ("？", WHITE)]]},
}


def cover_a(lang: str) -> Image.Image:
    left = Image.open(OUT / "peacock-boevski-359063525.jpg").convert("RGB")
    right = Image.open(DATA / "photos/p17.jpg").convert("RGB")
    canvas = cover_bg(right).convert("RGBA")
    size = 124 if lang == "en" else 126
    title(canvas, TITLES["a"][lang], lang, size, W / 2, 12, gap=1.0)
    # crops (3:2) around each butterfly, found by eye on the originals (2048x1536 both)
    card(canvas, left, (110, 180, 1970, 1420), (74, 330), 548)
    card(canvas, right, (317, 325, 1817, 1325), (658, 330), 548)
    return canvas.convert("RGB")


def cover_b(lang: str) -> Image.Image:
    photo = Image.open(DATA / "photos/g1.jpg").convert("RGB")
    canvas = cover_bg(photo, blur=34, dark=0.6).convert("RGBA")
    s = H / photo.height
    p = photo.resize((round(photo.width * s), H), Image.LANCZOS).convert("RGBA")
    fade = 220  # the photo's right edge melts into its own blurred copy
    mask = Image.new("L", p.size, 255)
    md = ImageDraw.Draw(mask)
    for i in range(fade):
        md.line([(p.width - fade + i, 0), (p.width - fade + i, H)], fill=round(255 * (1 - i / fade) ** 1.4))
    canvas.paste(p, (0, 0), mask)
    size = 168 if lang == "en" else 150
    title(canvas, TITLES["b"][lang], lang, size, W - 48, (H - size * 2.1) / 2, align="right", gap=1.12)
    return canvas.convert("RGB")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for key, make in (("a", cover_a), ("b", cover_b)):
        for lang in ("en", "zh"):
            path = OUT / f"cover-{key}-real.{lang}.jpg"
            make(lang).save(path, quality=92)
            print(path)


if __name__ == "__main__":
    main()
