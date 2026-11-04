#!/usr/bin/env python3
"""YouTube covers for 听得见的舞: the owner's two Muse stills (11-03) — L'Étoile frame 12 and The Dance Class frame 22 —
each with the title alone, zh and en (cover standard: 1280×720, one language per cover, no ribbon or byline), the title in
the upper left on the thirds grid.

  .venv-reframe/bin/python scripts/gymnopedies/cover.py   -> covers/youtube-cover[-<variant>].{zh,en}.jpg in the data folder
The étoile cover is the main one (the film opens on that painting); the dance-class one is for YouTube's thumbnail test.
"""
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = Path("/Users/yqin/repo/playground/lucas-academy-video-data")
FONT = DATA / "jesu/fonts/NotoSerifSC-Regular.otf"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
OUT = DATA / "satie-gymnopedies/covers"

TITLES = {"zh": '听得见的<span class="key">舞</span>', "en": 'The <span class="key">Dance</span><br>You Can Hear'}
# Owner 11-03: 「明星的封面不要改变原始构图」, then he drew where each title goes (「文字放到我画的地方，明星可以背景稍微虚化
# 一点」): L'Étoile — over the man's legs and the floor beside him, with everything behind the star softened a little
# (dof()); The Dance Class — on the floor in front of the teacher. (covers/thirds-*.png: an unused upper-right attempt.)
CENTRE = "left: {x}px; top: {y}px; transform: translate(-50%, -50%); text-align: center"
def shade(x, y, a=.5): return (f"radial-gradient(ellipse 24% 20% at {x / 12.8:.1f}% {y / 7.2:.1f}%, rgba(12,10,8,{a}) 0%, "
                               f"rgba(12,10,8,{a * .45:.2f}) 60%, rgba(12,10,8,0) 100%)")
VARIANTS = {   # name: background, object-position, text box, shade, font size per language
    "": dict(bg="bg-etoile-dof.png", pos="50% 50%", side=CENTRE.format(x=345, y=318), shade=shade(345, 318), size={"zh": 84, "en": 60}),
    "dance-class": dict(bg="bg-dance-class.png", pos="50% 50%", side={"zh": CENTRE.format(x=1000, y=600), "en": CENTRE.format(x=1000, y=612)},
                        shade=shade(1000, 605, .42), size={"zh": 84, "en": 56}),
}

def dof():
    """bg-etoile.png with everything but the star dancer slightly blurred: GrabCut, seeded with boxes in 1280×720 cover
    pixels (her, the white-tutu dancer and the legs behind her), on the owner's frame — his composition is untouched."""
    import cv2, numpy as np
    im = cv2.imread(str(OUT / "bg-etoile.png")); H, W = im.shape[:2]
    small = cv2.resize(im, (1280, 720), interpolation=cv2.INTER_AREA)
    m = np.full((720, 1280), cv2.GC_BGD, np.uint8)
    m[40:720, 570:1280] = cv2.GC_PR_FGD; m[200:720, 780:1280] = cv2.GC_PR_FGD
    m[60:335, 600:805] = cv2.GC_BGD; m[90:215, 860:935] = cv2.GC_BGD; m[0:200, 570:780] = cv2.GC_BGD
    m[260:330, 850:930] = cv2.GC_FGD; m[450:620, 800:1100] = cv2.GC_FGD
    cv2.grabCut(small, m, None, np.zeros((1, 65)), np.zeros((1, 65)), 6, cv2.GC_INIT_WITH_MASK)
    a = np.where((m == cv2.GC_FGD) | (m == cv2.GC_PR_FGD), 1.0, 0.0).astype(np.float32)
    a = cv2.morphologyEx(a, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    a = cv2.GaussianBlur(cv2.resize(a, (W, H), interpolation=cv2.INTER_LINEAR), (0, 0), 2.5 * W / 1280)[..., None]
    soft = cv2.GaussianBlur(im, (0, 0), 3.2 * W / 1280)                    # 「稍微」: a slight softening, not a bokeh
    cv2.imwrite(str(OUT / "bg-etoile-dof.png"), (im * a + soft * (1 - a)).astype(np.uint8))

def render(variant, lang):
    v = VARIANTS[variant]; bg = OUT / v["bg"]
    if not bg.exists(): print("skip, no", bg); return
    html = (ROOT / "scripts/gymnopedies/cover.html").read_text()
    for k, s in (("LANG", lang), ("FONT", FONT.as_uri()), ("BGPOS", v["pos"]), ("BG", bg.as_uri()), ("SHADE", v["shade"]),
                 ("SIDE", v["side"][lang] if isinstance(v["side"], dict) else v["side"]), ("SIZE", str(v["size"][lang])),
                 ("SPACING", "6px" if lang == "zh" else "1px"), ("TITLE", v.get("titles", {}).get(lang, TITLES[lang]))):
        html = html.replace(k, s)
    name = f"youtube-cover{'-' + variant if variant else ''}.{lang}"
    page = OUT / f"{name}.html"; page.write_text(html)
    png = OUT / f"{name}.png"
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--allow-file-access-from-files",
                    "--force-device-scale-factor=1", "--window-size=1280,720", "--virtual-time-budget=3000",
                    f"--screenshot={png}", page.as_uri()], check=True, capture_output=True)
    subprocess.run(["sips", "-s", "format", "jpeg", "-s", "formatOptions", "92", str(png), "--out", str(OUT / f"{name}.jpg")],
                   check=True, capture_output=True)
    png.unlink(); page.unlink()
    print(OUT / f"{name}.jpg")

if __name__ == "__main__":
    if not (OUT / "bg-etoile-dof.png").exists(): dof()
    for variant in VARIANTS:
        for lang in ("zh", "en"): render(variant, lang)
