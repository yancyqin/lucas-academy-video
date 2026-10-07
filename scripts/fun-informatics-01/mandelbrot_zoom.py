"""The fractal zoom for 「计算机怎么算 1+1=？」 (FUN-INFORMATICS-01.md): a Mandelbrot
zoom the film can honestly call "computed from this one line": z -> z*z + c.

Deterministic, like the Remotion compositions: the same arguments give the same
frames. Every frame is a fresh escape-time render of the view at that zoom
(nothing is stored and scaled), which is the film's point in IT06 / IT09.

Two clips:
  main       24 s, x2 a second from the whole set down to ~1.7e7x: the opening (IT00),
             the callbacks (IT06, IT09). Comfortably inside double precision.
  overdrive  keeps zooming x8 a second until adjacent pixels get the same c (the
             double mantissa runs out near 1e13-1e14x) and the picture breaks into
             blocks that grow until two or three fill the frame: the picture for
             "规则也有尽头" (it09-10). Not a bug; the point.

Run with the lucas-academy-media conda env (numba + numpy); numba makes a 1080p
frame a fraction of a second, the numpy fallback is tens of seconds a frame.

  P=../lucas-academy-media/.conda/bin/python
  $P scripts/fun-informatics-01/mandelbrot_zoom.py main      public/fun-informatics-01/footage/fractal-main.mp4
  $P scripts/fun-informatics-01/mandelbrot_zoom.py overdrive public/fun-informatics-01/footage/fractal-overdrive.mp4
  # a quick look: --preview renders at 640x360, 1/4 of the frames

Writes <out>.json next to the video: per-frame centre, view width, zoom and max
iterations, so the Remotion overlay (the formula and the numbers in IT09) can
read the exact values the frame was computed from.
"""
import argparse
import json
import math
import subprocess
import sys
import time

import numpy as np

try:
    from numba import njit, prange
    HAVE_NUMBA = True
except ImportError:  # pragma: no cover - the numpy path is a fallback only
    HAVE_NUMBA = False

# Seahorse Valley, a classic deep-zoom target with structure at every scale.
CENTER = (-0.743643887037151, 0.131825904205330)
START_WIDTH = 3.6  # the whole set fits a 16:9 frame at this view width

CLIPS = {
    "main": {"seconds": 24.0, "zoom_per_second": 2.0},
    # x8/s for 18 s = 2^54 ≈ 1.8e16. At 1920 px wide, adjacent pixels share one c from ~5e13 (t ≈ 15 s):
    # 2 px blocks, then 100 px blocks near t = 17 s, two or three blocks across the frame at the end.
    "overdrive": {"seconds": 18.0, "zoom_per_second": 8.0},
}

# The room's palette (mr-yancy-black.svg / the Live Paintings): navy -> teal -> cyan -> mint -> white.
PALETTE = np.array([
    [6, 19, 30], [12, 41, 64], [38, 127, 143], [89, 215, 255], [167, 245, 155], [240, 252, 255],
], dtype=np.float64)
PALETTE_PERIOD = 48.0  # smooth-iteration units per colour cycle; keeps detail at every depth


def max_iterations(zoom):
    """More iterations the deeper we go, so the boundary stays sharp."""
    return int(200 + 90 * math.log2(max(zoom, 1.0)))


if HAVE_NUMBA:
    @njit(parallel=True, fastmath=False, cache=True)
    def escape_times(cx, cy, view_w, width, height, max_iter):
        out = np.empty((height, width), dtype=np.float64)
        px = view_w / width
        x0 = cx - view_w / 2.0
        y0 = cy + (height * px) / 2.0
        for j in prange(height):
            ci = y0 - (j + 0.5) * px
            for i in range(width):
                cr = x0 + (i + 0.5) * px
                zr = 0.0
                zi = 0.0
                n = 0
                while n < max_iter:
                    zr2 = zr * zr
                    zi2 = zi * zi
                    if zr2 + zi2 > 4096.0:  # a large bailout makes the smooth colouring smoother
                        break
                    zi = 2.0 * zr * zi + ci
                    zr = zr2 - zi2 + cr
                    n += 1
                if n >= max_iter:
                    out[j, i] = -1.0
                else:
                    mag = math.sqrt(zr * zr + zi * zi)
                    out[j, i] = n + 1.0 - math.log(math.log(mag)) / math.log(2.0)
        return out
else:
    def escape_times(cx, cy, view_w, width, height, max_iter):
        px = view_w / width
        xs = cx - view_w / 2.0 + (np.arange(width) + 0.5) * px
        ys = cy + (height * px) / 2.0 - (np.arange(height) + 0.5) * px
        c = xs[None, :] + 1j * ys[:, None]
        z = np.zeros_like(c)
        n = np.zeros(c.shape, dtype=np.int32)
        alive = np.ones(c.shape, dtype=bool)
        out = np.full(c.shape, -1.0)
        for k in range(max_iter):
            z[alive] = z[alive] * z[alive] + c[alive]
            escaped = alive & (np.abs(z) > 64.0)
            if escaped.any():
                mag = np.abs(z[escaped])
                out[escaped] = k + 1.0 - np.log(np.log(mag)) / np.log(2.0)
                alive &= ~escaped
            n[alive] = k + 1
            if not alive.any():
                break
        return out


def colour(times):
    """Smooth escape time -> RGB bytes; inside the set stays black."""
    inside = times < 0
    t = np.where(inside, 0.0, times) / PALETTE_PERIOD
    t = t - np.floor(t)  # cyclic
    pos = t * (len(PALETTE) - 1)
    lo = np.floor(pos).astype(np.int64)
    hi = np.minimum(lo + 1, len(PALETTE) - 1)
    frac = (pos - lo)[..., None]
    rgb = PALETTE[lo] * (1.0 - frac) + PALETTE[hi] * frac
    rgb[inside] = 0.0
    return np.clip(rgb + 0.5, 0, 255).astype(np.uint8)


def frames_of(clip, fps, preview):
    spec = CLIPS[clip]
    total = int(round(spec["seconds"] * fps))
    step = 4 if preview else 1
    for index in range(0, total, step):
        seconds = index / fps
        zoom = spec["zoom_per_second"] ** seconds
        yield index, seconds, zoom, START_WIDTH / zoom


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("clip", choices=sorted(CLIPS))
    ap.add_argument("out", help="output .mp4 (H.264, yuv420p, keyframe every 15 frames for Remotion)")
    ap.add_argument("--width", type=int, default=1920)
    ap.add_argument("--height", type=int, default=1080)
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--preview", action="store_true", help="640x360 and every 4th frame, for a quick look")
    args = ap.parse_args()
    width, height = (640, 360) if args.preview else (args.width, args.height)
    fps = args.fps if not args.preview else max(1, args.fps // 4)

    ffmpeg = subprocess.Popen([
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{width}x{height}", "-r", str(fps), "-i", "-",
        "-an", "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", "-r", str(fps),
        "-g", "15", "-keyint_min", "15", "-sc_threshold", "0", "-movflags", "+faststart", args.out,
    ], stdin=subprocess.PIPE)
    manifest = {"clip": args.clip, "fps": fps, "width": width, "height": height,
                "center": CENTER, "start_width": START_WIDTH, "formula": "z -> z*z + c",
                "numba": HAVE_NUMBA, "frames": []}
    started = time.time()
    count = 0
    for index, seconds, zoom, view_w in frames_of(args.clip, args.fps, args.preview):
        max_iter = max_iterations(zoom)
        times = escape_times(CENTER[0], CENTER[1], view_w, width, height, max_iter)
        ffmpeg.stdin.write(colour(times).tobytes())
        manifest["frames"].append({"frame": index, "seconds": round(seconds, 4), "zoom": zoom,
                                   "view_width": view_w, "pixel": view_w / width, "max_iter": max_iter})
        count += 1
        if count == 1 or count % 30 == 0:
            print(f"{args.clip}: frame {index} t={seconds:5.2f}s zoom={zoom:.3g} iter={max_iter} "
                  f"({time.time() - started:.0f}s)", file=sys.stderr)
    ffmpeg.stdin.close()
    if ffmpeg.wait() != 0:
        sys.exit("ffmpeg failed")
    with open(args.out + ".json", "w") as f:
        json.dump(manifest, f)
    print(f"{args.out}: {count} frames, {width}x{height}@{fps}, {time.time() - started:.0f}s "
          f"({'numba' if HAVE_NUMBA else 'numpy'})")


if __name__ == "__main__":
    main()
