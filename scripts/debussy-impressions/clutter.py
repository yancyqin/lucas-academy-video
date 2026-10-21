#!/usr/bin/env python3
"""Rank paintings by visual clutter (owner 2026-10-16: if there are too many paintings, drop the messy ones first).

Per aligned painting at 960 px: edge density (Canny on a lightly blurred grey image), fine-detail energy
(mean |Laplacian| after a 1.5 px blur), and fragmentation (number of separate edge components per megapixel).
Each is ranked 0..1 across the set; clutter = mean of the three ranks.
usage: .venv-reframe/bin/python clutter.py
"""
import json, os
import cv2, numpy as np

DATA = "/Users/yqin/repo/playground/lucas-academy-video-data/debussy-impressions"
HERE = os.path.dirname(os.path.abspath(__file__))

def metrics(path):
    im = cv2.imread(path); im = cv2.resize(im, (960, int(960 * im.shape[0] / im.shape[1])), interpolation=cv2.INTER_AREA)
    g = cv2.GaussianBlur(cv2.cvtColor(im, cv2.COLOR_BGR2GRAY), (0, 0), 1.5)
    e = cv2.Canny(g, 40, 110)
    n, _ = cv2.connectedComponents((e > 0).astype(np.uint8))
    return float((e > 0).mean()), float(np.abs(cv2.Laplacian(g, cv2.CV_32F)).mean()), n / (im.shape[0] * im.shape[1] / 1e6)

def main():
    ed = json.load(open(f"{HERE}/edits/03-clair.json"))
    rows = []
    for i, s in enumerate(ed["shots"]):
        p = f"{DATA}/clair/paint/aligned/{s['id']}.png" if "painting" in s else f"{DATA}/art/{s['id']}.jpg"
        rows.append([i + 1, s["id"], *metrics(p)])
    for c in (2, 3, 4):
        order = np.argsort(np.argsort([r[c] for r in rows]))
        for r, o in zip(rows, order): r.append(o / (len(rows) - 1))
    for r in rows: r.append(sum(r[5:8]) / 3)
    rows.sort(key=lambda r: -r[8])
    print(" #  shot            edges  detail  pieces/MP  clutter")
    for r in rows: print(f"{r[0]:2d}  {r[1]:14s}  {r[2]:.3f}  {r[3]:6.2f}  {r[4]:8.0f}   {r[8]:.2f}")
    json.dump([{"shot": r[0], "id": r[1], "clutter": round(r[8], 3)} for r in rows], open(f"{DATA}/clair/paint/clutter.json", "w"), indent=1)

if __name__ == "__main__":
    main()
