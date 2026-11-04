#!/usr/bin/env python3
"""YouTube covers for 「诺贝尔奖：光遗传学是什么？从信息学的角度看」 (README "YouTube covers"), 1280×720.

    python3 scripts/fun-informatics-04/cover.py

Laid out like 「你爱听 AI 说「是的」吗？」's cover (scripts/ai-sycophancy/cover.html): the question in two lines on the
left, one line under it, one picture, rendered with headless Chrome. No series ribbon: Yancy 11-01, 「趣味信息学封面不要那个斜条」.
Versions:
  switch  「大脑里，也有开关吗？」 over the Nobel committee's illustration of the switch and the brain (the film's opening)
  dish    「光遗传学是什么？」 over the last frame of the Muse clip G2 (the algae gathered on the lit side)
  en      the English film's cover: the switch version in English only (README: one language per cover)
Writes out/fun-informatics-04/cover/youtube-cover.<lang>.<version>.jpg.
"""
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = next(p / "lucas-academy-video-data" for p in ROOT.parents if (p / "lucas-academy-video-data").is_dir())
FONT = DATA / "jesu/fonts/NotoSerifSC-Regular.otf"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
OUT = ROOT / "out/fun-informatics-04/cover"
PUB = ROOT / "public/fun-informatics-04"

VERSIONS = {  # name: (picture, its position, title, line under it)
    "switch": (PUB / "stills/nobel-main.jpg", "80% 40%", '大脑里，<br>也有<span class="k">开关</span>吗？',
               "2026年 诺贝尔奖<br>光遗传学，从信息学的角度看"),  # Yancy 11-01: drop 生理学或医学奖
    "dish": (OUT / "g2-last.png", "60% 50%", '<span class="k">光</span>遗传学<br>是什么？',
             "2026 诺贝尔生理学或医学奖<br>从信息学的角度看"),
    "en": (PUB / "stills/nobel-main.jpg", "80% 40%", 'Does the Brain<br>Have <span class="k">Switches</span>?',
           "The 2026 Nobel Prize<br>Optogenetics, seen through informatics"),
}

PAGE = """<!doctype html>
<html lang="zh"><head><meta charset="utf-8"><style>
  @font-face { font-family: "NotoSerifSC"; src: url("FONT"); }
  html, body { margin: 0; width: 1280px; height: 720px; overflow: hidden; background: #0d1216; }
  .bg { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; object-position: BGPOS; }
  .shade { position: absolute; inset: 0;
    background: linear-gradient(90deg, rgba(10,12,15,.92) 0%, rgba(10,12,15,.78) 40%, rgba(10,12,15,.15) 68%, rgba(10,12,15,0) 100%); }
  .text { position: absolute; left: 64px; top: 0; bottom: 0; display: flex; flex-direction: column; justify-content: center; }
  .title { font-family: "NotoSerifSC", "Songti SC", serif; font-size: 112px; line-height: 1.2; letter-spacing: 4px;
    color: #fff; text-shadow: 0 4px 24px rgba(0,0,0,.6); white-space: nowrap; }
  .k { color: #ffb13d; }
  .rule { width: 72px; height: 5px; background: #d2ad62; margin: 34px 0 22px; }
  .sub { font-family: "PingFang SC", sans-serif; font-weight: 500; font-size: 40px; line-height: 1.35; letter-spacing: 2px;
    color: #eee6d6; text-shadow: 0 3px 16px rgba(0,0,0,.7); white-space: nowrap; }
</style></head><body>
  <img class="bg" src="BG"><div class="shade"></div>
  <div class="text"><div class="title">TITLE</div><div class="rule"></div><div class="sub">SUB</div></div>
</body></html>"""


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    g2 = OUT / "g2-last.png"
    if not g2.exists():
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "9.5", "-i", str(PUB / "muse/G2-1.mp4"), "-frames:v", "1", str(g2)],
                       check=True)
    for name, (bg, pos, title, sub) in VERSIONS.items():
        lang = "en" if name == "en" else "zh"
        page = OUT / f"cover.{lang}.{name}.html"
        page.write_text(PAGE.replace("FONT", FONT.as_uri()).replace("BGPOS", pos).replace("BG", bg.as_uri())
                        .replace("TITLE", title).replace("SUB", sub)
                        .replace('<html lang="zh">', f'<html lang="{lang}">'))
        png = OUT / f"youtube-cover.{lang}.{name}.png"
        subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--allow-file-access-from-files",
                        "--force-device-scale-factor=1", "--window-size=1280,720", "--virtual-time-budget=3000",
                        f"--screenshot={png}", page.as_uri()], check=True, capture_output=True)
        jpg = OUT / f"youtube-cover.{lang}.{name}.jpg"
        subprocess.run(["sips", "-s", "format", "jpeg", "-s", "formatOptions", "92", str(png), "--out", str(jpg)],
                       check=True, capture_output=True)
        print(jpg)


if __name__ == "__main__":
    main()
