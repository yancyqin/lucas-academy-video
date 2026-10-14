"""YouTube covers, zh and en -> DATA/build/youtube-cover.<zh|en>.jpg (1280x720)

The channel's big-title cover (README / owner 2026-10-06): one strong visual, a huge two-line title
with 1-2 keywords in accent colours, the other language small underneath, no card behind the text.
Here the title is the owner's "best of Bach, with illustration" (2026-10-14) and the visual is
Haussmann's 1746 portrait of Bach (public domain). Rendered as HTML by headless Chrome, then
converted with sips.
"""
import json
import pathlib
import subprocess
import tempfile

HERE = pathlib.Path(__file__).parent
DATA = pathlib.Path(json.loads((HERE / "edit.json").read_text())["data"])
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
PORTRAIT = DATA / "art/cover-bach-haussmann.jpg"
GOLD, TEAL, INK, BG = "#e9b93a", "#6fd0c6", "#f6efe0", "#14110d"
ZH = '"PingFang SC", "Hiragino Sans GB", sans-serif'
EN = '"Avenir Next", "Helvetica Neue", Arial, sans-serif'
SERIF = 'Georgia, "Songti SC", serif'

TITLES = {
    "zh": (f'<div class="big zh"><span style="color:{GOLD}">巴赫</span>精选</div>'
           f'<div class="big zh"><span style="color:{TEAL}">看得见</span>的音乐</div>'
           f'<div class="small" style="font-family:{SERIF};font-style:italic">The Best of Bach, Illustrated</div>'),
    "en": (f'<div class="big en">The Best of <span style="color:{GOLD}">Bach</span>,</div>'
           f'<div class="big en" style="color:{TEAL}">Illustrated</div>'
           f'<div class="small" style="font-family:{SERIF}">巴赫精选 · 看得见的音乐</div>'),
}

PAGE = """<!doctype html><html><head><meta charset="utf-8"><style>
html,body{{margin:0;width:1280px;height:720px;overflow:hidden;background:{bg}}}
.bgimg{{position:absolute;inset:-40px;background:url('{img}') center/cover;filter:blur(26px) brightness(.38)}}
.shade{{position:absolute;inset:0;background:linear-gradient(90deg,rgba(20,17,13,.96) 0%,rgba(20,17,13,.82) 46%,rgba(20,17,13,.15) 80%)}}
.portrait{{position:absolute;right:70px;top:44px;height:632px;box-shadow:0 26px 70px rgba(0,0,0,.65)}}
.title{{position:absolute;left:78px;top:0;bottom:0;width:700px;display:flex;flex-direction:column;justify-content:center;color:{ink}}}
.big{{font-weight:800;line-height:1.12;letter-spacing:.01em;white-space:nowrap}}
.zh{{font-family:{zh};font-size:104px}}
.en{{font-family:{en};font-size:68px;line-height:1.12}}
.small{{font-size:36px;margin-top:34px;opacity:.92}}
</style></head><body><div class="bgimg"></div><div class="shade"></div>
<img class="portrait" src="{img}"><div class="title">{title}</div></body></html>"""


def main():
    out = DATA / "build"
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        for lang, title in TITLES.items():
            html = tmp / f"cover-{lang}.html"
            html.write_text(PAGE.format(bg=BG, img=PORTRAIT.as_uri(), ink=INK, zh=ZH, en=EN, title=title))
            png = tmp / f"cover-{lang}.png"
            subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                            "--force-device-scale-factor=1", "--window-size=1280,720",
                            "--allow-file-access-from-files", f"--screenshot={png}", html.as_uri()],
                           check=True, capture_output=True)
            jpg = out / f"youtube-cover.{lang}.jpg"
            subprocess.run(["sips", "-s", "format", "jpeg", "-s", "formatOptions", "92", str(png),
                            "--out", str(jpg)], check=True, capture_output=True)
            print(jpg)


if __name__ == "__main__":
    main()
