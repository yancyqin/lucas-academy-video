"""YouTube covers, zh and en -> DATA/cover/youtube-cover.<zh|en>.jpg (1280x720)

The channel's big-title cover (owner 2026-10-06 / 10-21): a question in two huge lines, one language per cover, the
same accent colour on the same keyword in both, one strong visual, no card, no byline. The visual reads as real: the
finished theme drawing (at the moment every star flashes on the last note) lying on the desk, with its crayon.
Rendered as HTML by headless Chrome, then converted with sips.
"""
import pathlib
import subprocess
import sys
import tempfile

import cv2
import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import film  # noqa: E402

DATA = pathlib.Path("/Users/yqin/repo/playground/lucas-academy-video-data/twinkle-stars")
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
GOLD, CYAN, INK = "#ffd23f", "#7fe0f0", "#fbf5e8"
ZH = '"PingFang SC", "Hiragino Sans GB", sans-serif'
EN = '"Avenir Next", "Helvetica Neue", Arial, sans-serif'

TITLES = {
    "zh": (f'<div class="big zh"><span style="color:{GOLD}">小星星</span>，</div>'
           f'<div class="big zh">能<span style="color:{CYAN}">画</span>出来吗？</div>'),
    "en": (f'<div class="big en">Can You <span style="color:{CYAN}">Draw</span></div>'
           f'<div class="big en">a <span style="color:{GOLD}">Little Star</span>?</div>'),
}

PAGE = """<!doctype html><html><head><meta charset="utf-8"><style>
html,body{{margin:0;width:1280px;height:720px;overflow:hidden;background:#3a2414}}
.desk{{position:absolute;inset:0;background:url('{desk}') center/cover}}
.shade{{position:absolute;inset:0;background:linear-gradient(90deg,rgba(22,12,5,.88) 0%,rgba(22,12,5,.74) 40%,rgba(22,12,5,.10) 66%,rgba(22,12,5,0) 100%)}}
.sheet{{position:absolute;right:46px;top:118px;width:590px;transform:rotate(-3.5deg);
        box-shadow:14px 22px 34px rgba(0,0,0,.45),2px 3px 6px rgba(0,0,0,.35)}}
.crayon{{position:absolute;left:{cx}px;top:{cy}px;width:{cw}px;transform:rotate(8deg);filter:drop-shadow(10px 14px 10px rgba(0,0,0,.45))}}
.title{{position:absolute;left:66px;top:0;bottom:0;width:640px;display:flex;flex-direction:column;justify-content:center;color:{ink};
        text-shadow:0 4px 18px rgba(0,0,0,.55)}}
.big{{font-weight:800;line-height:1.16;letter-spacing:.01em;white-space:nowrap}}
.zh{{font-family:{zh};font-size:100px}}
.en{{font-family:{en};font-size:78px;line-height:1.14}}
</style></head><body><div class="desk"></div><div class="shade"></div>
<img class="sheet" src="{sheet}"><img class="crayon" src="{crayon}"><div class="title">{title}</div></body></html>"""


def crayon_png(path_out):
    """The film's crayon, tinted the yellow it last coloured with, cut out with alpha."""
    cr = film.load_crayon(str(DATA / "pictures/crayon.png"))
    col = np.array([238, 206, 70], np.float32) / 255
    body = cr["rgb"] / 255 * 0.25 + cr["lum"] * col[None, None] * 0.75
    rgba = np.dstack([np.clip(body * 255, 0, 255), cr["a"][..., None] * 255]).astype(np.uint8)
    cv2.imwrite(str(path_out), cv2.cvtColor(rgba, cv2.COLOR_RGBA2BGRA))
    return rgba.shape[1]


def shoot(page, jpg):
    """One 1280×720 cover: the page's HTML -> headless Chrome screenshot -> JPEG."""
    with tempfile.TemporaryDirectory() as tmp:
        html, png = pathlib.Path(tmp) / "cover.html", pathlib.Path(tmp) / "cover.png"
        html.write_text(page)
        subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=1",
                        "--window-size=1280,720", "--allow-file-access-from-files", f"--screenshot={png}", html.as_uri()],
                       check=True, capture_output=True)
        subprocess.run(["sips", "-s", "format", "jpeg", "-s", "formatOptions", "92", str(png), "--out", str(jpg)],
                       check=True, capture_output=True)
    print(jpg)


def main():
    out = DATA / "cover"; out.mkdir(exist_ok=True)
    w = crayon_png(out / "crayon-yellow.png")
    for lang, title in TITLES.items():
        shoot(PAGE.format(desk=(out / "desk.jpg").as_uri(), sheet=(out / "sheet-theme-flash.png").as_uri(),
                          crayon=(out / "crayon-yellow.png").as_uri(), cx=700, cy=520, cw=int(w * 0.62),
                          ink=INK, zh=ZH, en=EN, title=title), out / f"youtube-cover.{lang}.jpg")


if __name__ == "__main__":
    main()
