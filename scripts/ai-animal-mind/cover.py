"""YouTube covers for 「动物想什么？AI 知道吗？」: the G10 first frame (Yancy 2026-11-11: 「封面用G10来做」) with the title
alone, zh and en (cover standard: 1280×720, one language per cover, no ribbon or byline: a standalone film).

    python3 scripts/ai-animal-mind/cover.py [variant ...]
        -> lucas-academy-video-data/ai-animal-mind/covers/youtube-cover-<variant>.{zh,en}.jpg and options.jpg

Yancy on the first try (lower right, Noto Serif, coral + gold keywords): 「标题字太丑了！！配色丑字体丑！位置也不好，放中间
红色纱巾那里」. So the title sits in the middle on the red scarf: over its lower half, clear of the dolphin's snout
(the scarf in its mouth is the picture's point) and of both hands; heavy type, white, a soft shadow, no shade box. The
frame keeps its composition. Variants differ only in typeface (and one keeps a single soft keyword colour).
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = next(p / "lucas-academy-video-data" for p in ROOT.parents if (p / "lucas-academy-video-data").is_dir())
BG = DATA / "ai-animal-mind/hd/G10-dolphin-scarf.png"  # the Codex frame Yancy's G10 Muse clip starts from, 3840 wide
OUT = DATA / "ai-animal-mind/covers"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

TITLES = {"zh": '<span class="key">动物</span>想什么？<br>AI 知道吗？',  # the 11-11 title (cover_images.py now makes the covers)
          "en": 'What Are <span class="key">Animals</span><br>Thinking?<br>Does AI Know?'}
POS = {"zh": (648, 492), "en": (648, 500)}  # centre, cover pixels: the scarf's lower half, below the snout, right of the low hand
VARIANTS = {  # name: font family per language, weight, size per language, letter spacing per language, keyword colour
    "pingfang": dict(family={"zh": '"PingFang SC"', "en": '"SF Pro Display", -apple-system, "Helvetica Neue"'}, weight=600,
                     size={"zh": 100, "en": 72}, spacing={"zh": "4px", "en": "0px"}, key="#ffffff"),
    "songti": dict(family={"zh": '"Songti SC"', "en": 'Georgia, "Times New Roman"'}, weight=900,
                   size={"zh": 100, "en": 72}, spacing={"zh": "4px", "en": "0px"}, key="#ffffff"),
    "hiragino-key": dict(family={"zh": '"Hiragino Sans GB"', "en": '"Helvetica Neue"'}, weight=700,
                         size={"zh": 98, "en": 72}, spacing={"zh": "4px", "en": "0px"}, key="#ffe9a8"),
}


def render(name: str, lang: str) -> Path:
    v = VARIANTS[name]
    x, y = POS[lang]
    html = (ROOT / "scripts/ai-animal-mind/cover.html").read_text()
    for k, s in (("LANG", lang), ("BG", BG.as_uri()), ("FAMILY", v["family"][lang]), ("WEIGHT", str(v["weight"])),
                 ("POS", f"left: {x}px; top: {y}px; transform: translate(-50%, -50%); text-align: center"),
                 ("SIZE", str(v["size"][lang])), ("SPACING", v["spacing"][lang]), ("KEY", v["key"]),
                 ("TITLE", TITLES[lang])):
        html = html.replace(k, s)
    stem = f"youtube-cover-{name}.{lang}"
    page, png, jpg = OUT / f"{stem}.html", OUT / f"{stem}.png", OUT / f"{stem}.jpg"
    page.write_text(html)
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--allow-file-access-from-files",
                    "--force-device-scale-factor=1", "--window-size=1280,720", "--virtual-time-budget=3000",
                    f"--screenshot={png}", page.as_uri()], check=True, capture_output=True)
    subprocess.run(["sips", "-s", "format", "jpeg", "-s", "formatOptions", "92", str(png), "--out", str(jpg)],
                   check=True, capture_output=True)
    png.unlink()
    page.unlink()
    return jpg


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for name in sys.argv[1:] or VARIANTS:
        for lang in ("zh", "en"):
            print(render(name, lang))
