"""Write the YouTube description's picture credits from shots.ts and SOURCES.txt."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
shots = (ROOT / "src/videos/vg-why/shots.ts").read_text(encoding="utf-8")
sources = {}
for line in (ROOT / "public/vg-why-paint-them/art/SOURCES.txt").read_text(encoding="utf-8").splitlines():
    if line.startswith("#") or not line.strip():
        continue
    parts = line.split(" | ")
    sources[parts[0]] = parts[1]

rows = []
for m in re.finditer(r"^\s*'?([a-z-]+)'?: \{w: \d+, h: \d+, title: \{zh: '([^']+)', en: (['\"])(.+?)\3\}, meta: (['\"])(.+?)\5\}", shots, re.M):
    art, zh, en, meta = m.group(1), m.group(2), m.group(4), m.group(6)
    artist = "Giotto" if art == "giotto" else "Vincent van Gogh"
    rows.append(f"- {zh} / {en.replace('Giotto, ', '')} — {artist}, {meta}\n  {sources[art]}")

text = ("Pictures (public-domain photographs via Wikimedia Commons)\n画作（公有领域图片，来自 Wikimedia Commons）\n\n"
        + "\n".join(rows)
        + "\n\nLetters quoted: vangoghletters.org — Van Gogh Museum / Huygens ING (letters 652, 663, 673, 705, 729).\n"
        "Lesson links and faith reading are Lucas Academy's own. 课程联系与信仰理解为 Lucas Academy 的解释。\n")
out = ROOT / "out/vg-why-paint-them/description-credits.txt"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(text, encoding="utf-8")
print(f"{len(rows)} works → {out.relative_to(ROOT)}")
