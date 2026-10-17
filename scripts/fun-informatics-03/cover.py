"""YouTube covers for both films, to the owner's cover standard (1280x720, a big two-line question,
the keyword in an accent colour, a small line in the other language, one picture, no card behind the title;
README "YouTube covers": no Lucas Academy name or series tag, so the question stands alone).

    python3 scripts/fun-informatics-03/cover.py [walkie|star|desk]

The owner (2026-10-16): the audience is parents and educators first, so the cover should look real and
educational, not cartoon-like. "star" is a real frame of the family's game (IMG_8530 at 22.6 s: the star with the
extra little stars, real pencils on the table); "desk" is a photographic Codex picture; "walkie" is the first,
illustrated cover. Writes out/fun-informatics-03/delivery/cover.{zh,en}.<variant>.jpg via headless Chrome and sips.
"""
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "out/fun-informatics-03/delivery"
IMAGES = ROOT / "public/fun-informatics-03/images"
ORIGINAL = Path("/Users/yqin/repo/playground/lucas-academy-video-data/fun-informatics-03/drawings/original")


def star_photo() -> Path:
    """The real frame, cropped so the star sits right of centre, warmed and brightened; the paper stays paper."""
    out = IMAGES / "cover-photo-star.jpg"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "22.6", "-i", str(ORIGINAL / "IMG_8530.MOV"), "-frames:v", "1",
                    "-vf", "crop=1300:1080:300:0,scale=1040:864:flags=lanczos,eq=contrast=1.08:brightness=0.03:saturation=0.9,"
                           "colortemperature=temperature=5800,curves=all='0/0 0.5/0.46 0.85/0.9 1/1'",
                    "-q:v", "2", str(out)], check=True)
    return out
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

TEXT = {
    "zh": {"title": '报数为什么<br>说「<span class="k">幺</span>」？', "sub": "Why Do Pilots Say “Bravo”?",
           "font": '"PingFang SC", sans-serif', "size": 132, "series": "趣味信息学 3 · Lucas Academy", "right": -160},
    "en": {"title": 'Why Do Pilots<br>Say “<span class="k">Bravo</span>”?', "sub": "报数为什么说「幺」？",
           "font": '"Avenir Next", sans-serif', "size": 100, "series": "Fun Informatics 3 · Lucas Academy", "right": -290},
}


def page(lang, variant):
    t = TEXT[lang]
    if variant == "walkie":
        image, right, fade = (IMAGES / "walkie-talkie.png").as_uri(), t["right"], "#f3eee5 0%, #f3eee5 42%, rgba(243,238,229,0) 62%"
        pic = f".pic {{{{ position: absolute; right: {right}px; top: -20px; width: 1000px; height: 760px; background: url('{image}') center/cover; }}}}"
    elif variant == "star":
        # The real photo, whole, lying on the page like a print: the star, the pencils, the table all stay in.
        image, fade = star_photo().as_uri(), "rgba(0,0,0,0) 0%, rgba(0,0,0,0) 100%"
        pic = (f".pic {{{{ position: absolute; right: 54px; top: 74px; width: 560px; height: 572px; border-radius: 10px; transform: rotate(2.5deg);"
               f" background: url('{image}') center/cover; box-shadow: 0 22px 50px rgba(60,45,20,.28), 0 2px 6px rgba(60,45,20,.18); }}}}")
    else:
        image = (IMAGES / "cover-photo-desk.png").as_uri()
        fade = "rgba(250,248,244,.94) 0%, rgba(250,248,244,.86) 38%, rgba(250,248,244,0) 64%"
        pic = f".pic {{{{ position: absolute; inset: 0; background: url('{image}') center/cover; }}}}"
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ width: 1280px; height: 720px; overflow: hidden; background: #f3eee5; font-family: {t['font']}; }}
{pic.replace('{{', '{').replace('}}', '}')}
.fade {{ position: absolute; inset: 0; background: linear-gradient(90deg, {fade}); }}
.text {{ position: absolute; left: 70px; top: 0; bottom: 0; width: 900px; display: flex; flex-direction: column; justify-content: center; }}
.series {{ font-family: "Avenir Next", "PingFang SC", sans-serif; font-size: 26px; font-weight: 700; color: #0f766e; letter-spacing: 1px; margin-bottom: 26px; }}
h1 {{ font-size: {t['size']}px; line-height: 1.12; font-weight: 900; color: #2b2926; white-space: nowrap; }}
.k {{ color: #c2410c; }}
.sub {{ margin-top: 30px; font-size: 38px; font-weight: 700; color: #6b645b; font-family: "Avenir Next", "PingFang SC", sans-serif; }}
</style></head><body><div class="pic"></div><div class="fade"></div>
<div class="text"><h1>{t['title']}</h1><div class="sub">{t['sub']}</div></div></body></html>"""


def main():
    variant = next((a for a in sys.argv[1:] if a in ("walkie", "star", "desk")), "desk")  # the owner picked desk
    OUT.mkdir(parents=True, exist_ok=True)
    for lang in ("zh", "en"):
        with tempfile.TemporaryDirectory() as tmp:
            html, png = Path(tmp, "cover.html"), Path(tmp, "cover.png")
            html.write_text(page(lang, variant), encoding="utf-8")
            subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", f"--user-data-dir={tmp}/profile",
                            "--window-size=1280,720", "--force-device-scale-factor=1", f"--screenshot={png}", html.as_uri()],
                           check=True, capture_output=True)
            jpg = OUT / f"cover.{lang}.{variant}.jpg"
            subprocess.run(["sips", "-s", "format", "jpeg", "-s", "formatOptions", "92", str(png), "--out", str(jpg)],
                           check=True, capture_output=True)
            print(jpg)


if __name__ == "__main__":
    main()
