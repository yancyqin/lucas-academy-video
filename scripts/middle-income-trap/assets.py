"""Copy what the picture needs into public/middle-income-trap/ (a local working copy, see .gitignore).

  python3 scripts/middle-income-trap/assets.py

- art/<key>.jpg: the latest version (-vN) of each Codex illustration in lucas-academy-video-data/middle-income-trap/
  art/codex that edit.json uses, as JPEG; and the King photo from the series' first episode (public domain,
  news-education-01/art/sources.json); and the cover of 「一根冰棍，要花多少钱？」 for the card at sc02-07.
- clips/: the Li Lu clips, as cut (MIDDLE-INCOME-TRAP.md).
- stills/: frames from those clips for the lines that retell them, letterbox cropped like the clips on screen.
"""
import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for parent in ROOT.parents:
    if (parent / "lucas-academy-video-data").is_dir():
        DATA = parent / "lucas-academy-video-data"
        break
SRC = DATA / "middle-income-trap"
PUB = ROOT / "public/middle-income-trap"
STILLS = {"lilu-a1": ("lilu_A_trap.mp4", 1.0), "lilu-a2": ("lilu_A_trap.mp4", 24.0),
          "lilu-b1": ("lilu_B_zero_sum.mp4", 3.0), "lilu-b2": ("lilu_B_zero_sum.mp4", 30.0)}


def latest(key: str) -> Path:
    versions = sorted(SRC.glob(f"art/codex/{key}-v*.png"), key=lambda p: int(p.stem.rsplit("-v", 1)[1]))
    return versions[-1] if versions else SRC / f"art/codex/{key}.png"


edit = json.loads((ROOT / "scripts/middle-income-trap/edit.json").read_text())["shots"]
keys = sorted({s["src"] for s in edit if s["k"] in ("art", "title")})
(PUB / "art").mkdir(parents=True, exist_ok=True)
missing = []
for key in keys:
    src = latest(key)
    if not src.exists():
        missing.append(key)
        continue
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-q:v", "2", str(PUB / f"art/{key}.jpg")], check=True)
shutil.copy(DATA / "news-education-01/art/sc07-king.jpg", PUB / "art/king.jpg")
# The other episode sc02-07 points to (「可以点击右上角，看我们另一个视频」): its Chinese cover, small, as the card.
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(DATA / "fun-economics-01/out/fun-economics-01/delivery/cover.zh.png"),
                "-vf", "scale=640:-2", "-q:v", "2", str(PUB / "art/promo-icepop.jpg")], check=True)
(PUB / "clips").mkdir(exist_ok=True)
for clip in sorted({s["src"] for s in edit if s["k"] == "clip"}):
    shutil.copy(SRC / "clips" / clip, PUB / "clips" / clip)
(PUB / "stills").mkdir(exist_ok=True)
for name, (clip, at) in STILLS.items():
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(at), "-i", str(SRC / "clips" / clip), "-frames:v", "1",
                    "-vf", "crop=960:540:0:90,scale=1920:1080:flags=lanczos", "-q:v", "2", str(PUB / f"stills/{name}.jpg")],
                   check=True)
print(f"{len(keys) - len(missing)} illustrations, {len(STILLS)} stills")
if missing:
    print("not generated yet:", ", ".join(missing))
