"""Render "We Build A BlackHole with AI" (BLACK-HOLE-AI.md): one picture, two soundtracks.

The picture (composition BlackHoleAi) is rendered muted in chunks (concurrency 2, the owner's memory budget), joined,
and muxed with BOTH mixes as two AAC streams (Apple's encoder, aac_at, 320k): English first and default, Chinese
second, each language-tagged. The Chinese track is also written alone as an M4A for YouTube Studio's "Add audio
track" (an M4A, not a WAV: a WAV got stuck processing in Studio before; ffmpeg's own `aac` raised the true peak by
about 1 dB, aac_at keeps it where the mix put it).

  out/black-hole-ai/delivery/black-hole-ai.mp4        the film (English default + Chinese second audio stream)
  out/black-hole-ai/delivery/black-hole-ai.zh.m4a     the Chinese track alone, the film's exact length

A chunk is rendered again only when something it shows changed: the composition's source, or the timeline's shots,
overlays and chapters that touch its frames. Refuses a draft timeline (placeholder takes) unless --draft, and a
take that changed on disk after the timeline was built.

  python3 scripts/black-hole-ai/render.py [--chunks 6] [--draft]
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PUB = ROOT / "public/black-hole-ai"
OUT = ROOT / "out/black-hole-ai"
WORK, DELIVERY = OUT / "chunks", OUT / "delivery"
COMPOSITION = "BlackHoleAi"
FILM = "black-hole-ai"
LANGS = ("en", "zh")
NAMES = {"en": ("eng", "English"), "zh": ("chi", "中文")}
DATA = PUB.resolve().parent                     # the media folder (v01), where the takes live


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while block := f.read(1 << 20):
            h.update(block)
    return h.hexdigest()


def takes_unchanged(tl: dict) -> None:
    for lang, lines in tl["takes"].items():
        for cid, t in lines.items():
            src = t["source"]
            if src.get("placeholder"):
                continue
            if sha(DATA / src["file"]) != src["sha256"]:
                raise SystemExit(f"{lang} {cid}: {src['file']} changed after the timeline was built; rebuild it")


def chunk_key(tl: dict, a: int, b: int, sources: bytes) -> str:
    """What frames a..b are made of: the composition's code, the chapters and length (the bar is on every frame),
    and every shot, overlay and cue that overlaps them."""
    fps = tl["fps"]
    t0, t1 = a / fps - 1, (b + 1) / fps + 1
    near = lambda s, e: e >= t0 and s <= t1  # noqa: E731
    part = {
        "sections": tl["sections"], "duration": tl["durationInFrames"], "draft": tl["draft"], "fadeOut": tl["fadeOut"],
        "shots": [s for s in tl["shots"] if s["endFrame"] >= a - 2 and s["startFrame"] <= b + 2],
        "overlays": [o for o in tl["overlays"] if near(o["start"], o["end"])],
        "title": tl["title"], "byline": tl["byline"],
    }
    footage = sorted({s["clip"] for s in part["shots"] if s.get("clip")})
    files = [PUB / f"footage/{c}.mp4" for c in footage] + [PUB / f"stills/{s['image']}.png" for s in part["shots"] if s.get("image")]
    stamp = [(str(f.name), f.stat().st_size, int(f.stat().st_mtime)) for f in files]
    return hashlib.sha256(sources + json.dumps([part, stamp], sort_keys=True).encode()).hexdigest()


def render(out: Path, frames: str, concurrency: int) -> bool:
    cmd = ["npx", "remotion", "render", "src/index.ts", COMPOSITION, str(out), f"--frames={frames}", "--muted",
           f"--concurrency={concurrency}", "--timeout=300000", "--offthreadvideo-cache-size-in-bytes=1500000000",
           "--crf=16", "--color-space=bt709", "--log=error"]
    return subprocess.run(cmd, cwd=ROOT).returncode == 0


def loudness(path: Path, stream: str = "a:0") -> tuple[float, float]:
    err = subprocess.run(["ffmpeg", "-nostats", "-hide_banner", "-i", str(path), "-map", f"0:{stream}", "-af", "ebur128=peak=true",
                          "-f", "null", "-"], capture_output=True, text=True).stderr
    summary = err[err.rfind("Summary:"):]
    return float(re.search(r"I:\s+(-?[\d.]+) LUFS", summary)[1]), float(re.search(r"Peak:\s+(-?[\d.]+|-inf) dBFS", summary)[1])


def seconds(path: Path) -> float:
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                                capture_output=True, text=True, check=True).stdout)


def main() -> None:
    draft_ok = "--draft" in sys.argv
    chunks = int(sys.argv[sys.argv.index("--chunks") + 1]) if "--chunks" in sys.argv else 6
    tl = json.loads((PUB / "timeline.json").read_text())
    if tl["draft"] and not draft_ok:
        raise SystemExit("The timeline is a draft (placeholder takes): build it from the real takes, or pass --draft")
    takes_unchanged(tl)
    sources = b"".join(p.read_bytes() for p in sorted((ROOT / "src/videos/black-hole-ai").glob("*.ts*")))
    WORK.mkdir(parents=True, exist_ok=True)
    DELIVERY.mkdir(parents=True, exist_ok=True)
    total = tl["durationInFrames"]
    size = math.ceil(total / chunks)
    parts = []
    for k in range(chunks):
        a, b = k * size, min(total, (k + 1) * size) - 1
        part = WORK / f"film.{k:02d}.mp4"
        ok = part.with_suffix(".ok")
        key = chunk_key(tl, a, b, sources) + f":{a}-{b}"
        parts.append(part)
        if part.exists() and ok.exists() and ok.read_text() == key:
            print(f"chunk {k}: frames {a}-{b} unchanged", flush=True)
            continue
        ok.unlink(missing_ok=True)
        print(f"chunk {k}: frames {a}-{b}", flush=True)
        if not render(part, f"{a}-{b}", 2) and not render(part, f"{a}-{b}", 1):
            sys.exit(f"chunk {k} failed twice")
        ok.write_text(key)
    listing = WORK / "film.txt"
    listing.write_text("".join(f"file '{p}'\n" for p in parts))
    picture = WORK / "picture.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(listing), "-c", "copy", str(picture)], check=True)
    mixes = [PUB / f"audio/{lang}.mix.wav" for lang in LANGS]
    meta = []
    for i, lang in enumerate(LANGS):
        code, title = NAMES[lang]
        meta += [f"-metadata:s:a:{i}", f"language={code}", f"-metadata:s:a:{i}", f"title={title}"]
    film = DELIVERY / f"{FILM}.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(picture), *sum((["-i", str(m)] for m in mixes), []),
                    "-map", "0:v:0", *sum((["-map", f"{i + 1}:a:0"] for i in range(len(mixes))), []),
                    "-c:v", "copy", "-c:a", "aac_at", "-b:a", "320k", "-ar", "48000", "-ac", "2", *meta,
                    "-metadata:s:v:0", "language=und", "-disposition:a:0", "default", "-disposition:a:1", "0",
                    "-shortest", "-movflags", "+faststart", str(film)], check=True)
    m4a = DELIVERY / f"{FILM}.zh.m4a"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(PUB / "audio/zh.mix.wav"), "-c:a", "aac_at", "-b:a", "320k",
                    "-ar", "48000", "-ac", "2", "-metadata:s:a:0", "language=chi", "-metadata:s:a:0", "title=中文",
                    "-movflags", "+faststart", str(m4a)], check=True)
    report = {"film": film.name, "seconds": round(seconds(film), 3), "timelineSeconds": tl["durationSeconds"],
              "zhTrack": {"file": m4a.name, "seconds": round(seconds(m4a), 3)}}
    for i, lang in enumerate(LANGS):
        report[f"film.a:{i}.{lang}"] = dict(zip(("lufs", "true_peak_dbtp"), loudness(film, f"a:{i}")))
    report["zh.m4a"] = dict(zip(("lufs", "true_peak_dbtp"), loudness(m4a)))
    (OUT / "render-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps(report, ensure_ascii=False, indent=1), flush=True)


if __name__ == "__main__":
    main()
