"""Render a cube film, "How Do You Solve a 2×2 Cube?" (CUBE-2X2.md) or the 5×5 one (CUBE-5X5.md): one picture,
two soundtracks.

The picture (composition Cube2x2) is rendered muted in chunks with episode 1's chunk renderer, then joined with
BOTH mixes as two audio streams, English first (the default) and Chinese second, each tagged with its language:
  out/cube-2x2/delivery/cube-2x2.mp4          the film; YouTube plays its first (English) stream
  out/cube-2x2/delivery/cube-2x2.zh-track.wav the Chinese track alone, for YouTube Studio's "Add audio track"
Both tracks are exactly the picture's length. Concurrency 2 (the owner's memory budget). Refuses a draft
timeline, or a take that changed after check.py looked at it; chunks are rendered again only when something
the picture is made of changed.

  python3 scripts/cube-2x2/render.py [--chunks 4] [--draft] [--film cube-5x5]

(The 5×5 film's names are the same with cube-5x5 for cube-2x2, composition Cube5x5.)
"""
import hashlib
import importlib.util
import json
import math
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
# Each film: its composition and its takes folder (narrate.py TAKES).
FILMS = {"cube-2x2": ("Cube2x2", "cube-2x2-v3"), "cube-5x5": ("Cube5x5", "cube-5x5-v1")}
FILM = sys.argv[sys.argv.index("--film") + 1] if "--film" in sys.argv else "cube-2x2"
COMPOSITION, TAKES = FILMS[FILM]
PUB = ROOT / f"public/{FILM}"
OUT = ROOT / f"out/{FILM}"
WORK, DELIVERY = OUT / "chunks", OUT / "delivery"
spec = importlib.util.spec_from_file_location("fi01_render", ROOT / "scripts/fun-informatics-01/render.py")
shared = importlib.util.module_from_spec(spec)
spec.loader.exec_module(shared)
MEDIA = next(p / "lucas-academy-media" for p in ROOT.parents if (p / "lucas-academy-media").is_dir())
LANGS = ("en", "zh")
NAMES = {"en": ("eng", "English"), "zh": ("chi", "中文")}


def checked():
    """Every take the timeline uses is the one check.py heard."""
    for lang in LANGS:
        report = OUT / f"narration-check{'.en' if lang == 'en' else ''}.json"
        if not report.exists():
            raise SystemExit(f"run check.py --lang {lang} first")
        check = json.loads(report.read_text())
        lines = {l["id"]: l for l in json.loads((PUB / f"narration/{lang}.json").read_text())["lines"]}
        for cid, line in lines.items():
            record = check["cues"].get(cid)
            if not record or record["spoken"] != line["text"]:
                raise SystemExit(f"{lang} {cid}: not checked since its script changed; re-voice and re-check it")
            take = MEDIA / f"outputs/louise/{lang}/{TAKES}/{cid}.wav"
            if hashlib.sha256(take.read_bytes()).hexdigest() != record["sha256"]:
                raise SystemExit(f"{lang} {cid}: the take changed after check.py; run it again")


def main():
    draft = "--draft" in sys.argv
    chunks = int(sys.argv[sys.argv.index("--chunks") + 1]) if "--chunks" in sys.argv else 4
    tl = json.loads((PUB / "timeline.json").read_text())
    if tl.get("draft") and not draft:
        raise SystemExit("The timeline is a draft (missing takes); voice every line and rebuild it first (or pass --draft)")
    if not draft:
        checked()
    # The 5×5 film's composition builds on the 2×2 one's.
    sources = {ROOT / "src/videos/cube-2x2", ROOT / f"src/videos/{FILM}"}
    files = sorted(p for folder in sources for p in folder.glob("*.ts*")) + [PUB / "timeline.json"]
    files += sorted(p for p in (PUB / "footage").glob("*") if p.suffix in (".jpg", ".mp4"))
    digest = hashlib.sha256(b"".join(p.read_bytes() for p in files)).hexdigest()
    WORK.mkdir(parents=True, exist_ok=True)
    DELIVERY.mkdir(parents=True, exist_ok=True)
    stamp = WORK / "fingerprint.txt"
    if not stamp.exists() or stamp.read_text() != digest:
        for ok in WORK.glob("film.*.ok"):
            ok.unlink()
    stamp.write_text(digest)
    total = math.ceil(tl["durationSeconds"] * tl["fps"])
    size = math.ceil(total / chunks)
    parts = []
    for k in range(chunks):
        a, b = k * size, min(total, (k + 1) * size) - 1
        part = WORK / f"film.{k:02d}.mp4"
        parts.append(part)
        if part.exists() and part.with_suffix(".ok").exists():
            print(f"chunk {k}: done earlier", flush=True)
            continue
        print(f"chunk {k}: frames {a}-{b}", flush=True)
        if not shared.render(COMPOSITION, part, f"{a}-{b}", 2) and not shared.render(COMPOSITION, part, f"{a}-{b}", 1):
            sys.exit(f"chunk {k} failed twice")
        part.with_suffix(".ok").touch()
    listing = WORK / "film.txt"
    listing.write_text("".join(f"file '{p}'\n" for p in parts))
    film = DELIVERY / f"{FILM}.mp4"
    mixes = [PUB / f"audio/{lang}.mix.wav" for lang in LANGS]
    meta = []
    for i, lang in enumerate(LANGS):
        code, title = NAMES[lang]
        meta += [f"-metadata:s:a:{i}", f"language={code}", f"-metadata:s:a:{i}", f"title={title}"]
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(listing),
                    *sum((["-i", str(m)] for m in mixes), []),
                    "-map", "0:v:0", *sum((["-map", f"{i + 1}:a:0"] for i in range(len(mixes))), []),
                    # Apple's AAC keeps the true peak where the mix put it; ffmpeg's own added ~1 dB (-1.2 -> -0.2 dBTP).
                    "-c:v", "copy", "-c:a", "aac_at", "-b:a", "320k", *meta,
                    "-disposition:a:0", "default", "-disposition:a:1", "0", "-shortest", "-movflags", "+faststart", str(film)], check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(PUB / "audio/zh.mix.wav"), "-c:a", "pcm_s16le", str(DELIVERY / f"{FILM}.zh-track.wav")], check=True)
    got = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(film)],
                               capture_output=True, text=True, check=True).stdout)
    print(f"{film.name}: {got:.1f}s (timeline {tl['durationSeconds']:.1f}s), audio: English (default) + 中文", flush=True)


if __name__ == "__main__":
    main()
