#!/usr/bin/env python3
"""Render the YouTube cover from cover.html (or the English one, cover.en.html) with headless Chrome (1280×720 PNG → JPG).

  python3 scripts/ai-sycophancy/cover.py <background image> [object-position, default "70% 50%"] [--en]
Writes out/ai-sycophancy/cover/youtube-cover.{zh,en}.{png,jpg}.
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = next(p / "lucas-academy-video-data" for p in ROOT.parents if (p / "lucas-academy-video-data").is_dir())
FONT = DATA / "jesu/fonts/NotoSerifSC-Regular.otf"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
OUT = ROOT / "out/ai-sycophancy/cover"

args = [a for a in sys.argv[1:] if a != "--en"]
lang = "en" if "--en" in sys.argv else "zh"
bg = Path(args[0]).resolve()
pos = args[1] if len(args) > 1 else "70% 50%"
OUT.mkdir(parents=True, exist_ok=True)
html = (ROOT / f"scripts/ai-sycophancy/cover{'.en' if lang == 'en' else ''}.html").read_text()
page = OUT / f"cover.{lang}.html"
page.write_text(html.replace("FONT", FONT.as_uri()).replace("BGPOS", pos).replace("BG", bg.as_uri()))
png = OUT / f"youtube-cover.{lang}.png"
subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--allow-file-access-from-files",
                "--force-device-scale-factor=1", "--window-size=1280,720", "--virtual-time-budget=3000",
                f"--screenshot={png}", page.as_uri()], check=True, capture_output=True)
subprocess.run(["sips", "-s", "format", "jpeg", "-s", "formatOptions", "92", str(png), "--out", str(OUT / f"youtube-cover.{lang}.jpg")],
               check=True, capture_output=True)
print(OUT / f"youtube-cover.{lang}.jpg")
