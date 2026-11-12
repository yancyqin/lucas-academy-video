"""Stage the pictures of 「动物想什么？AI 知道吗？」 in public/ai-animal-mind/ (gitignored) for Remotion.

    python3 scripts/ai-animal-mind/assets.py [--force]

Reads scripts/ai-animal-mind/edit.json and shorts.json and stages only what they use:
  clips/px<id>.mp4     Pexels footage (fetch_footage.py), 1920x1080, 30 fps, no sound, at most MAX_LEN s
  clips/muse-<G>.mp4   Yancy's Muse clip for G.. when one is in lucas-academy-video-data/ai-animal-mind/muse/ (1248x704, scaled up)
  clips/jesu.mp4       the picture of 《耶稣，世人仰望的喜悦》 (lucas-academy-video-data/jesu/build/jesu-clean.mp4) from 148.1 s
  stills/<name>        Codex first frames and the Commons pictures (Clever Hans 1904, Monet), the HD copy from hd/ first
clips.json records each clip's source, length and frame rate for build_timeline.py.
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PUB = ROOT / "public/ai-animal-mind"
DATA = next(p / "lucas-academy-video-data" for p in ROOT.parents if (p / "lucas-academy-video-data").is_dir())
FILM = DATA / "ai-animal-mind"
EDIT = json.loads((ROOT / "scripts/ai-animal-mind/edit.json").read_text())
SHORTS = json.loads((ROOT / "scripts/ai-animal-mind/shorts.json").read_text())["shorts"]
JESU = DATA / "jesu/build/jesu-clean.mp4"
MAX_LEN, JESU_LEN = 45.0, 50.0
STILL_DIRS = [FILM / "hd", FILM / "references", FILM / "stills"]  # hd/ = Real-ESRGAN copies (upscale.py)


def probe(path: Path) -> dict:
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                        "stream=width,height,r_frame_rate:format=duration", "-of", "json", str(path)],
                       capture_output=True, text=True, check=True)
    j = json.loads(r.stdout)
    s = j["streams"][0]
    return {"width": s["width"], "height": s["height"], "fps": s["r_frame_rate"], "duration": float(j["format"]["duration"])}


def muse_file(g: str):
    """Yancy's clip for G..: named G01.mp4, G01-2.mp4, G01_x.mov, G01 something.mp4 (not G01b for G01); the first by name."""
    hits = sorted(p for p in (FILM / "muse").glob("*") if p.suffix.lower() in (".mp4", ".mov")
                  and (p.stem == g or p.stem[len(g):len(g) + 1] in ("-", "_", " ", ".")) and p.stem.startswith(g))
    return hits[0] if hits else None


def reference(g: str):
    hits = sorted((FILM / "references").glob(f"{g}-*.png"))
    return hits[0] if hits else None


def encode(src: Path, out: Path, start: float, length: float) -> None:
    """1080p, no sound; 50/60 fps sources stay 60 fps so a shot can slow them smoothly, the rest become 30 fps.
    A source under 1080p (Muse gives 1248x704) is scaled with lanczos and a light unsharp mask: steady from frame to
    frame, unlike Real-ESRGAN on video, which also would take about 13 s a frame here (11-11 test on G08)."""
    p = probe(src)
    a, _, b = p["fps"].partition("/")
    fps = 60 if float(a) / float(b or 1) >= 49 else 30
    up = ":flags=lanczos" if p["height"] < 1080 else ""
    sharpen = ",unsharp=5:5:0.6:5:5:0.0" if p["height"] < 1080 else ""
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(start), "-i", str(src), "-t", str(length), "-an",
                    "-vf", f"scale=1920:1080:force_original_aspect_ratio=increase{up},crop=1920:1080{sharpen},fps={fps},"
                           "format=yuv420p",
                    "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-threads", "4", str(out)], check=True)


def main() -> None:
    force = "--force" in sys.argv
    for sub in ("clips", "stills"):
        (PUB / sub).mkdir(parents=True, exist_ok=True)
    info = json.loads((PUB / "clips.json").read_text()) if (PUB / "clips.json").exists() and not force else {}
    todo, stills = {}, set()
    for s in EDIT["shots"]:
        if s["k"] == "clip":
            pid = s["clip"][2:]
            todo[s["clip"]] = (FILM / f"footage/pexels/{pid}.mp4", 0.0, MAX_LEN, f"pexels:{pid}")
        elif s["k"] == "jesu":
            todo["jesu"] = (JESU, EDIT["jesu"]["in"], JESU_LEN, "jesu")
        elif s["k"] == "muse":
            m = muse_file(s["g"])
            if m:
                todo[f"muse-{s['g']}"] = (m, 0.0, MAX_LEN, f"muse:{m.name}")
            ref = reference(s["g"])
            if ref:
                stills.add(ref.name)
        elif s["k"] == "still":
            stills.add(s["img"])
    for short in SHORTS.values():  # the vertical shorts (shorts.json) play clips the film may not use
        for beat in short["beats"]:
            for s in beat.get("shots", []) + [{"clip": c} for c in beat.get("tail_shots", [])]:
                c = s["clip"]
                if c.startswith("px"):
                    todo[c] = (FILM / f"footage/pexels/{c[2:]}.mp4", 0.0, MAX_LEN, f"pexels:{c[2:]}")
                elif c.startswith("muse-") and (m := muse_file(c[5:])):
                    todo[c] = (m, 0.0, MAX_LEN, f"muse:{m.name}")
    missing = []
    for name, (src, start, length, source) in todo.items():
        out = PUB / f"clips/{name}.mp4"
        if not src.is_file():
            missing.append(f"{name} ({src.name})")
            continue
        stale = name in info and info[name].get("source") != source
        if force or stale or not out.is_file():
            encode(src, out, start, length)
            print("clip", name, flush=True)
        info[name] = {"source": source, "probe": probe(out)}
    for gone in set(info) - set(todo):
        info.pop(gone)
    (PUB / "clips.json").write_text(json.dumps(info, indent=1) + "\n")
    for name in sorted(stills):
        src = next((d / name for d in STILL_DIRS if (d / name).is_file()), None)
        if src is None:
            missing.append(name)
        elif force or not (PUB / f"stills/{name}").is_file():
            shutil.copy2(src, PUB / f"stills/{name}")
    print(f"{len(info)} clips, {len(stills)} stills staged in {PUB.relative_to(ROOT)}")
    if missing:
        print("missing:", ", ".join(missing))


if __name__ == "__main__":
    main()
