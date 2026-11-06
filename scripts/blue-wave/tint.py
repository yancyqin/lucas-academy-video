#!/usr/bin/env python3
"""A light blue filter (owner 11-05 on the Wanderer ending: 「加上一层比较淡的蓝色的滤镜」).

The picture is mixed with a blue-toned copy of itself: the copy maps luminance onto a deep-blue → pale-blue ramp, so
shadows go navy and highlights go a cool white; `strength` is how much of that copy shows (0 = untouched).

  tint.py IN OUT STRENGTH [MAX_SIDE]      one still
  tint.py --strip IN OUT_DIR S1 S2 …      the original plus one file per strength (tint-<s>.jpg), for picking
"""
import os, sys
import numpy as np
from PIL import Image

# luminance 0 → 1 mapped onto these colours (piecewise linear)
RAMP = [(0.0, (10, 20, 44)), (0.45, (78, 112, 166)), (1.0, (232, 241, 255))]

def blue_tone(rgb: np.ndarray) -> np.ndarray:
    lum = (rgb @ np.array([0.299, 0.587, 0.114])) / 255.0
    xs = [p for p, _ in RAMP]
    return np.stack([np.interp(lum, xs, [c[k] for _, c in RAMP]) for k in range(3)], axis=-1)

def tint(im: Image.Image, strength: float) -> Image.Image:
    rgb = np.asarray(im.convert("RGB"), dtype=np.float64)
    out = (1 - strength) * rgb + strength * blue_tone(rgb)
    return Image.fromarray(np.clip(out + 0.5, 0, 255).astype(np.uint8))

def load(path, max_side):
    im = Image.open(path).convert("RGB")
    if max_side: im.thumbnail((max_side, max_side), Image.LANCZOS)
    return im

if __name__ == "__main__":
    if sys.argv[1] == "--strip":
        src, out_dir, strengths = sys.argv[2], sys.argv[3], [float(s) for s in sys.argv[4:]]
        os.makedirs(out_dir, exist_ok=True)
        im = load(src, 1600); im.save(f"{out_dir}/tint-0.jpg", quality=90)
        for s in strengths: tint(im, s).save(f"{out_dir}/tint-{s:g}.jpg", quality=90)
    else:
        src, dst, s = sys.argv[1], sys.argv[2], float(sys.argv[3])
        tint(load(src, int(sys.argv[4]) if len(sys.argv) > 4 else 0), s).save(dst, quality=95)
