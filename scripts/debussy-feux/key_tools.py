#!/usr/bin/env python3
"""Key the painted lighting tools off #FF00FF and find where the flame goes.

Reads feux/tools/<id>-tool.png (tool diagonal, lighting end at lower left). Writes feux/tools/keyed/<id>.png (RGBA, cropped
to the object + margin) and feux/tools/keyed/tools.json: for each tool the tip (lighting end) and the handle end in the
cropped sprite's pixels, and the object's length.

usage: .venv-reframe/bin/python key_tools.py
"""
import glob, json, os
import numpy as np, cv2

TOOLS = "/Users/yqin/repo/playground/lucas-academy-video-data/debussy-impressions/feux/tools"
OUT = f"{TOOLS}/keyed"

def key(img):
    b, g, r = [img[..., i].astype(np.float32) for i in range(3)]
    m = np.minimum(r, b) - g                                          # how magenta a pixel is (255 on the backdrop)
    alpha = 1 - np.clip((m - 60) / (190 - 60), 0, 1)
    alpha = cv2.GaussianBlur(alpha, (0, 0), 0.8)
    spill = np.clip(np.minimum(r, b) - np.maximum(g, 0.5 * (r + b) - 40), 0, None) * (1 - alpha)   # magenta fringe
    rgb = np.stack([b - spill, g, r - spill], -1)
    lab = cv2.connectedComponentsWithStats((alpha > 0.5).astype(np.uint8))   # keep the biggest piece (drop stray specks)
    n, labels, stats = lab[0], lab[1], lab[2]
    if n > 1:
        big = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
        keep = cv2.dilate((labels == big).astype(np.uint8), np.ones((9, 9), np.uint8)) > 0
        alpha = alpha * keep
    return np.dstack([np.clip(rgb, 0, 255), alpha * 255]).astype(np.uint8)

def main():
    os.makedirs(OUT, exist_ok=True); meta = {}
    for f in sorted(glob.glob(f"{TOOLS}/*-tool.png")):
        tid = os.path.basename(f)[:-9]
        rgba = key(cv2.imread(f))
        ys, xs = np.nonzero(rgba[..., 3] > 128)
        pad = 24
        x0, x1, y0, y1 = max(0, xs.min() - pad), min(rgba.shape[1], xs.max() + pad), max(0, ys.min() - pad), min(rgba.shape[0], ys.max() + pad)
        crop = rgba[y0:y1, x0:x1]
        xs, ys = xs - x0, ys - y0
        tip_i = np.argmax(-xs + ys); end_i = np.argmax(xs - ys)
        tip, end = (int(xs[tip_i]), int(ys[tip_i])), (int(xs[end_i]), int(ys[end_i]))
        cv2.imwrite(f"{OUT}/{tid}.png", crop)
        meta[tid] = {"size": [crop.shape[1], crop.shape[0]], "tip": tip, "end": end,
                     "length": round(float(np.hypot(end[0] - tip[0], end[1] - tip[1])), 1),
                     "angle_deg": round(float(np.degrees(np.arctan2(end[1] - tip[1], end[0] - tip[0]))), 1)}
        print(tid, meta[tid])
    json.dump(meta, open(f"{OUT}/tools.json", "w"), indent=1)

if __name__ == "__main__":
    main()
