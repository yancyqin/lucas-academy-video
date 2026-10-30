"""YouTube covers for 小星星的莫扎特画本, zh and en -> mozart-sketchbook/package/youtube-cover.<zh|en>.jpg (1280x720)

    python sketchbook_cover.py

The channel's big-title cover (a question in two huge lines, one language per cover, the same accent colour on the same
keyword, one strong visual, no card or byline), same look as the Twinkle cover: on the evening desk, three finished
sheets in three of the film's media (oil, crayon, gouache) lie fanned out, with a round brush beside them.
"""
import pathlib
import sys

import cv2
import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import film  # noqa: E402
from cover import EN, INK, ZH, shoot  # noqa: E402

DATA = pathlib.Path("/Users/yqin/repo/playground/lucas-academy-video-data/mozart-sketchbook")
TW = pathlib.Path("/Users/yqin/repo/playground/lucas-academy-video-data/twinkle-stars")
GOLD, CYAN = "#ffd23f", "#7fe0f0"
# back to front: (picture, left, top, width, rotation)
SHEETS = [(DATA / "pictures/m01-01.png", 664, 40, 440, -8), (TW / "pictures/p00-theme.png", 860, 86, 440, 7),
          (DATA / "pictures/m06-03.png", 694, 300, 560, -2.5)]

TITLES = {
    "zh": (f'<div class="big zh"><span style="color:{GOLD}">莫扎特</span>的音乐</div>'
           f'<div class="big zh">能<span style="color:{CYAN}">画</span>出来吗？</div>'),
    "en": (f'<div class="big en">Can You <span style="color:{CYAN}">Draw</span></div>'
           f'<div class="big en"><span style="color:{GOLD}">Mozart</span>\'s Music?</div>'),
}

PAGE = """<!doctype html><html><head><meta charset="utf-8"><style>
html,body{{margin:0;width:1280px;height:720px;overflow:hidden;background:#3a2414}}
.desk{{position:absolute;inset:0;background:url('{desk}') center/cover}}
.shade{{position:absolute;inset:0;background:linear-gradient(90deg,rgba(22,12,5,.88) 0%,rgba(22,12,5,.72) 38%,rgba(22,12,5,.10) 58%,rgba(22,12,5,0) 100%)}}
.sheet{{position:absolute;padding:12px;background:#f6f0e2;box-shadow:14px 22px 34px rgba(0,0,0,.45),2px 3px 6px rgba(0,0,0,.35)}}
.sheet img{{display:block;width:100%}}
.tool{{position:absolute;left:{bx}px;top:{by}px;width:{bw}px;transform:rotate(-14deg);filter:drop-shadow(10px 14px 10px rgba(0,0,0,.45))}}
.title{{position:absolute;left:62px;top:0;bottom:0;width:600px;display:flex;flex-direction:column;justify-content:center;color:{ink};
        text-shadow:0 4px 18px rgba(0,0,0,.55)}}
.big{{font-weight:800;line-height:1.16;letter-spacing:.01em;white-space:nowrap}}
.zh{{font-family:{zh};font-size:96px}}
.en{{font-family:{en};font-size:70px;line-height:1.14}}
</style></head><body><div class="desk"></div><div class="shade"></div>{sheets}
<img class="tool" src="{brush}"><div class="title">{title}</div></body></html>"""


def brush_png(path_out):
    """The film's round brush, cut out of its magenta background, its tip wet with blue."""
    b = film.load_crayon(str(DATA / "tools/brush-round.png"), 430)
    col = np.array([52, 92, 170], np.float32)
    rgb = b["rgb"] * (1 - b["tipw"]) + (b["lum"] * col) * b["tipw"]
    rgba = np.dstack([np.clip(rgb, 0, 255), b["a"][..., None] * 255]).astype(np.uint8)
    cv2.imwrite(str(path_out), cv2.cvtColor(rgba, cv2.COLOR_RGBA2BGRA))
    return rgba.shape[1]


def main():
    out = DATA / "package"; out.mkdir(exist_ok=True)
    work = DATA / "cover"; work.mkdir(exist_ok=True)
    w = brush_png(work / "brush-blue.png")
    sheets = "".join(f'<div class="sheet" style="left:{x}px;top:{y}px;width:{sw}px;transform:rotate({r}deg)">'
                     f'<img src="{p.as_uri()}"></div>' for p, x, y, sw, r in SHEETS)
    for lang, title in TITLES.items():
        shoot(PAGE.format(desk=(DATA / "tools/desk-evening.png").as_uri(), sheets=sheets, brush=(work / "brush-blue.png").as_uri(),
                          bx=566, by=500, bw=int(w * 0.7), ink=INK, zh=ZH, en=EN, title=title), out / f"youtube-cover.{lang}.jpg")


if __name__ == "__main__":
    main()
