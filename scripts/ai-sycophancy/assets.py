"""Copy what the picture needs into public/ai-sycophancy/ (a local working copy, see .gitignore).

  python3 scripts/ai-sycophancy/assets.py

Run after build_timeline.py: each footage shot's clip (lucas-academy-video-data/ai-sycophancy/footage/clips, picked in
selection.json) is cut to the stretch the shot plays (from `in`, its length at its rate, plus a little), cropped to
16:9, scaled to 1920×1080 and stored silent as clips/<shot clip>.mp4, so the bundle stays small and seeking is quick.
The series font goes to fonts/. A clip already staged at the right length is kept.

The green-screen clips are staged plain; key_screens.py then darkens their screens in place.
"""
import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = next(p / "lucas-academy-video-data" for p in ROOT.parents if (p / "lucas-academy-video-data").is_dir())
FOOT = DATA / "ai-sycophancy/footage"
PUB = ROOT / "public/ai-sycophancy"

picks = {s["shot"]: s for s in json.loads((FOOT / "selection.json").read_text())}
tl = json.loads((PUB / "timeline.json").read_text())
(PUB / "clips").mkdir(parents=True, exist_ok=True)
(PUB / "fonts").mkdir(exist_ok=True)
for name in ("NotoSerifSC-Regular.otf", "NotoSerifSC-Light.otf"):
    if not (PUB / "fonts" / name).exists():
        shutil.copy2(DATA / "jesu/fonts" / name, PUB / "fonts" / name)

for s in tl["shots"]:
    if s["k"] != "footage":
        continue
    out = PUB / "clips" / f"{s['clip']}.mp4"
    if (PUB / "clips" / f"{s['clip']}.plain.mp4").exists():  # keyed by key_screens.py: check, and restage, the plain one
        out = PUB / "clips" / f"{s['clip']}.plain.mp4"
    length = min((s["end"] - s["start"] + 1.0) * s["rate"] + 0.5, float(picks[s["clip"]]["probe"]["duration"]) - s.get("in", 0.0))
    if out.exists():
        have = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(out)],
                                    capture_output=True, text=True).stdout or 0)
        if have >= length - 0.3:
            continue
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{s.get('in', 0.0):.2f}", "-i", str(FOOT / picks[s["clip"]]["file"]),
                    "-t", f"{length:.2f}", "-vf", "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,setsar=1", "-an", "-c:v", "libx264", "-crf", "19", "-preset", "medium", "-pix_fmt", "yuv420p", "-g", "15",
                    "-movflags", "+faststart", str(out)], check=True)
    print(s["clip"], f"{length:.1f}s" + ("  (run key_screens.py again)" if out.stem.endswith(".plain") else ""), flush=True)
total = sum(p.stat().st_size for p in (PUB / "clips").glob("*.mp4"))
print(f"{len(list((PUB / 'clips').glob('*.mp4')))} clips, {total / 1e6:.0f} MB in {PUB / 'clips'}")
