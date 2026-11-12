"""Render 「动物想什么？AI 知道吗？」 and lay in a voice track (from scripts/fun-informatics-04/render.py).

  python3 scripts/ai-animal-mind/render.py [--lang en|zh] [--concurrency 4] [--draft]

The picture (composition AiAnimalMind) has no text and is the same for both tracks, so it renders once, silent, in four
parts (a crash costs one part) into out/ai-animal-mind/picture/ (draft/ at half size); then one MP4 per language with
that language's mix from build_timeline.py. After a change, only the parts whose shots (or the clips they play)
changed are rendered again; delete the parts to force a full render.
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FILM = "ai-animal-mind"
DRAFT = "--draft" in sys.argv
LANG = sys.argv[sys.argv.index("--lang") + 1] if "--lang" in sys.argv else "en"
OUT = ROOT / "out" / FILM / ("draft" if DRAFT else "picture")
OUT.mkdir(parents=True, exist_ok=True)
PARTS = 4
args = sys.argv[1:]
conc = args[args.index("--concurrency") + 1] if "--concurrency" in args else "4"

tl = json.loads((ROOT / "public" / FILM / "timeline.json").read_text())
clips = json.loads((ROOT / "public" / FILM / "clips.json").read_text())
frames = round(tl["durationSeconds"] * tl["fps"])
stamp = OUT / "timeline.json"


def part_range(k: int, n_frames: int) -> tuple:
    return k * n_frames // PARTS, (k + 1) * n_frames // PARTS - 1


def part_key(t: dict, clip_info: dict, k: int) -> list:
    """What part k's picture depends on: the shots that touch its frames (with a second either side for the
    crossfades) and the staged clip each one plays (its source and length)."""
    n = round(t["durationSeconds"] * t["fps"])
    a, b = (f / t["fps"] for f in part_range(k, n))
    near = [x for x in t["shots"] if x["start"] < b + 1.0 and x["end"] > a - 1.0]
    return [[x, clip_info.get(x.get("clip"), {}).get("source"), clip_info.get(x.get("clip"), {}).get("probe")] for x in near]


# keep the parts whose shots did not change (a new Muse clip or a moved cut re-renders only the parts it touches)
if stamp.exists():
    old = json.loads(stamp.read_text())
    old_tl, old_clips = (old["timeline"], old["clips"]) if "timeline" in old else (old, clips)
    same_length = old_tl["durationSeconds"] == tl["durationSeconds"] and old_tl["fps"] == tl["fps"]
    for k in range(PARTS):
        part = OUT / f"picture.part{k + 1}.mp4"
        if part.exists() and not (same_length and part_key(old_tl, old_clips, k) == part_key(tl, clips, k)):
            part.unlink()
            print(f"part {k + 1} changed, rendering it again")
stamp.write_text(json.dumps({"timeline": tl, "clips": clips}))
parts = []
for k in range(PARTS):
    a, b = part_range(k, frames)
    part = OUT / f"picture.part{k + 1}.mp4"
    parts.append(part)
    if part.exists():
        print(f"keep {part.name}")
        continue
    subprocess.run(["npx", "remotion", "render", "src/index.ts", "AiAnimalMind", str(part), f"--frames={a}-{b}",
                    f"--concurrency={conc}", "--timeout=240000", "--offthreadvideo-cache-size-in-bytes=1000000000",
                    "--crf=17", "--log=error", *(["--scale=0.5"] if DRAFT else [])], cwd=ROOT, check=True)
(OUT / "parts.txt").write_text("".join(f"file '{p.name}'\n" for p in parts))
picture = OUT / "picture.mp4"
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(OUT / "parts.txt"), "-c", "copy", "-an",
                str(picture)], check=True)
film = (ROOT / "out" / FILM / f"{FILM}.{LANG}.draft.mp4") if DRAFT else (ROOT / "out" / FILM / "delivery" / f"{FILM}.{LANG}.mp4")
film.parent.mkdir(parents=True, exist_ok=True)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(picture), "-i", str(ROOT / "out" / FILM / f"mix.{LANG}.wav"),
                "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "256k", "-ar", "48000",
                "-metadata:s:a:0", f"language={'zho' if LANG == 'zh' else 'eng'}", "-movflags", "+faststart", "-shortest",
                str(film)], check=True)
print(film)
