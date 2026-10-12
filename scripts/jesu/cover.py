"""YouTube covers: one frame of the film + the title, one per language
-> DATA/build/youtube-cover-<name>.<zh|en>.jpg (1280x720)

  cover.py                       the default candidates
  cover.py star=199.5            a named frame at a time (s) in jesu-clean.mp4
  cover.py earthrise=72.5@top    title in the upper third (dark sky above a horizon)
"""
import json
import pathlib
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = pathlib.Path(__file__).parent
EDIT = json.loads((HERE / "edit.json").read_text())
DATA = pathlib.Path(EDIT["data"])
W, H = 1280, 720
TITLES = {"zh": ("耶稣，世人仰望的喜悦", "从创世到再来", 92, 44),
          "en": ("Jesu, Joy of Man's Desiring", "From Creation to His Return", 70, 40)}
DEFAULT = {"star": 199.5, "earthrise": 72.0, "sistine": 150.0}


def frame(t):
    p = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t}", "-i", str(DATA / "build/jesu-clean.mp4"),
                        "-frames:v", "1", "-f", "image2pipe", "-vcodec", "png", "-"],
                       capture_output=True, check=True)
    import io
    return Image.open(io.BytesIO(p.stdout)).convert("RGB").resize((W, H), Image.LANCZOS)


def cover(img, lang, top=False):
    # darken behind the title so it reads on any frame
    shade = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(shade)
    for y in range(H):
        u = (H * 0.58 - y) / (H * 0.58) if top else (y - H * 0.42) / (H * 0.58)
        d.line([(0, y), (W, y)], fill=int(170 * max(0.0, u) ** 1.3))
    base = H * 0.30 if top else H * 0.70
    img = Image.composite(Image.new("RGB", (W, H), (0, 0, 0)), img, shade)
    title, sub, size, sub_size = TITLES[lang]
    fz = ImageFont.truetype(str(DATA / "fonts/NotoSerifSC-Regular.otf"), size)
    fe = ImageFont.truetype(str(DATA / "fonts/NotoSerifSC-Light.otf"), sub_size)
    text = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    t = ImageDraw.Draw(text)
    t.text((W / 2, base), title, font=fz, fill=(255, 255, 255, 255), anchor="ms")
    if sub:
        t.text((W / 2, base + 72), sub, font=fe, fill=(235, 228, 210, 255), anchor="ms")
    glow = text.getchannel("A").filter(ImageFilter.GaussianBlur(10))
    halo = Image.merge("RGBA", (*Image.new("RGB", (W, H), (0, 0, 0)).split(), glow.point(lambda v: int(v * 0.8))))
    out = Image.alpha_composite(img.convert("RGBA"), halo)
    return Image.alpha_composite(out, text).convert("RGB")


def main():
    picks = dict(a.split("=") for a in sys.argv[1:]) or DEFAULT
    for name, t in picks.items():
        t, _, where = str(t).partition("@")
        img = frame(float(t))
        for lang in TITLES:
            path = DATA / f"build/youtube-cover-{name}.{lang}.jpg"
            cover(img, lang, top=where == "top").save(path, quality=92)
            print(path)


if __name__ == "__main__":
    main()
