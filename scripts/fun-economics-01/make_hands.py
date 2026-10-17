"""Turn Yancy's hand footage into public/fun-economics-01/footage/hands.<lang>.mp4, on each film's clock for oc04-08.

The phone clip is HDR (HLG). macOS's avconvert makes the SDR copy (its tone mapping keeps skin natural; ffmpeg here
has no zscale), then the frame is cropped to the hands (the doorway on the right is cut away) and lifted so the wall
reads white. One take on one speed curve (owner's rule: 曲线变速, no jump cuts). Since v0.8 the finger path is a single
line, so the gestures land at shares of its speech (LEFT_AT, RIGHT_AT) and the held gesture plays to the end of the cue. Slow stretches blend the two nearest
source frames so the picture doesn't stutter. Run with lucas-academy-media's Python (numpy), after build_timeline.py
(it reads the timeline):
  ../lucas-academy-media/.conda/bin/python scripts/fun-economics-01/make_hands.py [--lang en]
"""
import json
import math
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
PUB = ROOT / "public/fun-economics-01"
# The original clip lives with the film data, beside the repository (from a worktree, further up).
DATA = next(p / "lucas-academy-video-data" for p in ROOT.parents if (p / "lucas-academy-video-data").is_dir())
SOURCE = DATA / "fun-economics-01/footage/IMG_8514.MOV"
SDR = ROOT / "out/fun-economics-01/hands-sdr.mov"
LANG = sys.argv[sys.argv.index("--lang") + 1] if "--lang" in sys.argv else "zh"
OUT = PUB / f"footage/hands.{LANG}.mp4"
LEFT_AT, RIGHT_AT = 0.18, 0.42  # where each hand moves, as shares of oc04-08's speech
FPS, SRC_FPS, W, H = 30, 30000 / 1001, 1920, 1080
LOOK = "crop=1000:563:350:280,scale=1920:1080:flags=lanczos,colorlevels=rimax=0.86:gimax=0.84:bimax=0.82,eq=saturation=0.9"
FADE = 0.3  # the composition fades each background in this long before its first cue
# Source seconds, read off 10 fps contact sheets: hands open from the start; the left hand folds to 2 over
# 5.3–5.7 s; the right hand curls and comes up as 3 over 13.9–14.95 s; both hold steady until about 20.3 s.
OPEN, LEFT, RIGHT, HELD_TO = 3.8, (5.3, 5.7), (13.9, 14.95), 20.0  # open hands from 0.3 s; start late, the cue is short


def monotone(points):
    """Cubic Hermite keys [t, s, speed] with no backwards motion (src/lib/timeRamps.ts monotoneRamp)."""
    keys = []
    for i, (t, s) in enumerate(points):
        if i in (0, len(points) - 1):
            keys.append((t, s, 0.0))
            continue
        a = (s - points[i - 1][1]) / (t - points[i - 1][0])
        b = (points[i + 1][1] - s) / (points[i + 1][0] - t)
        keys.append((t, s, 0.0 if a <= 0 or b <= 0 else min(a, b)))
    return keys


def ramp_at(keys, t):
    if t <= keys[0][0]:
        return keys[0][1]
    for (t0, s0, v0), (t1, s1, v1) in zip(keys, keys[1:]):
        if t > t1:
            continue
        h = t1 - t0
        u = (t - t0) / h
        return ((2 * u**3 - 3 * u**2 + 1) * s0 + (u**3 - 2 * u**2 + u) * h * v0
                + (3 * u**2 - 2 * u**3) * s1 + (u**3 - u**2) * h * v1)
    return keys[-1][1]



def gestures(left: float, right: float, length: float, open_from: float = OPEN) -> list:
    """The speed curve: open hands, the left hand's 2 at `left`, the right hand's 3 at `right` (film seconds from the
    footage's start), then the held gesture to `length`."""
    return monotone([(0, open_from), (left, LEFT[0]), (left + 0.4, LEFT[1]), (right, RIGHT[0]),
                     (right + 1.05, RIGHT[1]), (length, HELD_TO)])


def write(keys: list, a: float, b: float, out: Path) -> None:
    """Encode the footage on that curve from film second a to b (blending frames on slow stretches); out.json keeps the keys."""
    if not SDR.exists():
        SDR.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["avconvert", "--source", str(SOURCE), "--preset", "Preset1920x1080", "--output", str(SDR), "--replace"],
                       check=True, capture_output=True)
    reader = subprocess.Popen(["ffmpeg", "-v", "error", "-i", str(SDR), "-vf", LOOK, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                              stdout=subprocess.PIPE)
    writer = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                               "-i", "-", "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", "-color_primaries", "bt709",
                               "-color_trc", "bt709", "-colorspace", "bt709", "-movflags", "+faststart", str(out)], stdin=subprocess.PIPE)
    size = W * H * 3
    frames = {}  # source index -> frame; only the two around the current time are kept
    next_index = 0

    def frame(i):
        nonlocal next_index
        while next_index <= i:
            raw = reader.stdout.read(size)
            if len(raw) < size:
                raise SystemExit(f"source ended at frame {next_index}")
            frames[next_index] = np.frombuffer(raw, np.uint8).reshape(H, W, 3)
            next_index += 1
        for k in [k for k in frames if k < i - 1]:
            del frames[k]
        return frames[i]

    total = math.ceil((b - a) * FPS)
    for n in range(total):
        pos = ramp_at(keys, n / FPS) * SRC_FPS
        i, w = int(pos), pos - int(pos)
        picture = frame(i) if w < 0.02 else (frame(i) * (1 - w) + frame(i + 1) * w + 0.5).astype(np.uint8)
        writer.stdin.write(picture.tobytes())
    writer.stdin.close()
    reader.kill()
    if writer.wait() != 0:
        raise SystemExit("encoding failed")
    out.with_suffix(".json").write_text(json.dumps({"source": SOURCE.name, "start": round(a, 3), "end": b, "fps": FPS, "frames": total,
                                                    "look": LOOK, "keys": [[round(x, 3) for x in k] for k in keys]}, indent=1) + "\n")
    print(f"{out.name}: {total} frames, {b - a:.2f} s from {a:.2f} s")


def main() -> None:
    tl = json.loads((PUB / f"timeline.{LANG}.json").read_text())
    cue = {c["id"]: c for c in tl["cues"]}["oc04-08"]
    a, b = cue["start"] - FADE, cue["end"]
    s0, s1 = cue["speech"]["start"], cue["speech"]["end"]
    left, right = (s0 + f * (s1 - s0) - a for f in (LEFT_AT, RIGHT_AT))
    write(gestures(left, right, b - a), a, b, OUT)


if __name__ == "__main__":
    main()
