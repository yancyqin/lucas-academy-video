"""Render the silent picture of 你知道印象派的秘密吗？ in resumable chunks, then join them.

    python3 scripts/impressionism-secret/render.py [--concurrency 2] [--chunk 1800]

Each chunk is rendered with `remotion render --frames=a-b --muted` into
out/impressionism-secret/chunks/; a chunk with the right frame count is kept on
the next run, so an interrupted render resumes. Chunks are joined by stream copy
into out/impressionism-secret/picture.mp4, which deliver.py mixes and muxes.
"""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "out/impressionism-secret"
CHUNKS = OUT / "chunks"
TIMELINE = ROOT / "src/data/impressionism-secret.json"


def frames_in(path: Path) -> int | None:
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_packets",
                        "-show_entries", "stream=nb_read_packets", "-of", "json", str(path)], capture_output=True, text=True)
    try:
        return int(json.loads(r.stdout)["streams"][0]["nb_read_packets"])
    except (ValueError, KeyError, IndexError, TypeError):
        return None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--concurrency", type=int, default=2)
    ap.add_argument("--chunk", type=int, default=1800)
    args = ap.parse_args()
    tl = json.loads(TIMELINE.read_text())
    total = int(-(-tl["durationSeconds"] * tl["fps"] // 1))
    CHUNKS.mkdir(parents=True, exist_ok=True)
    gl = os.environ.get("REMOTION_GL", "angle" if sys.platform == "darwin" else "swangle")
    parts = []
    for i, a in enumerate(range(0, total, args.chunk)):
        b = min(total, a + args.chunk) - 1
        part = CHUNKS / f"part-{i:03d}.mp4"
        parts.append(part)
        if part.exists() and frames_in(part) == b - a + 1:
            continue
        print(f"rendering {part.name}: frames {a}-{b} of {total}", flush=True)
        code = subprocess.run(["npx", "remotion", "render", "src/index.ts", "ImpressionismPicture", str(part), f"--frames={a}-{b}",
                               "--muted", f"--concurrency={args.concurrency}", f"--gl={gl}", "--timeout=300000", "--log=error",
                               "--offthreadvideo-cache-size-in-bytes=536870912", "--media-cache-size-in-bytes=268435456",
                               "--offthreadvideo-video-threads=2"],
                              cwd=ROOT).returncode
        if code != 0 or frames_in(part) != b - a + 1:
            raise SystemExit(f"{part.name}: renderer exited {code}, frames {frames_in(part)} (expected {b - a + 1})")
    listing = CHUNKS / "parts.txt"
    listing.write_text("".join(f"file '{p.name}'\n" for p in parts))
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(listing),
                    "-c", "copy", "-movflags", "+faststart", str(OUT / "picture.mp4")], check=True)
    print(f"picture.mp4: {frames_in(OUT / 'picture.mp4')} frames (expected {total})")


if __name__ == "__main__":
    main()
