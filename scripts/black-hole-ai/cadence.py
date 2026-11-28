"""Decoded-frame cadence and black frames of the delivered film (docs/PRODUCTION-CHECKLIST.md: "运镜检查必须测量实际
解码帧" — measure the decoded frames, not the frame rate or the timecodes).

Decodes out/black-hole-ai/delivery/black-hole-ai.mp4 frame by frame at 1920×1080 (luma) and, for the picture above
the chapter bar (the bar's ▼ moves a fraction of a pixel per frame), records:
  - repeated frames: a frame whose largest pixel difference from the one before is <= 2 (codec noise), inside each
    moving footage shot (dissolves excluded) — a repeated frame there is a stall the eye sees;
  - black frames: mean luma <= 24 and std <= 4 (scripts/qa/picture.py's rule, at 960 px), as runs, each marked
    planned (the spec's planned_black: the fall's fade, the film's last second) or not.
Writes out/black-hole-ai/qa/cadence.json and prints a summary.

  python3 scripts/black-hole-ai/cadence.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
try:
    import numpy as np
except ImportError:
    for parent in [ROOT, *ROOT.parents]:
        py = parent / ".venv-align/bin/python"
        if py.is_file():
            os.execv(str(py), [str(py), "-B", *sys.argv])
    raise

PUB = ROOT / "public/black-hole-ai"
FILM = ROOT / "out/black-hole-ai/delivery/black-hole-ai.mp4"
SPEC = ROOT / "out/black-hole-ai/qa/film.qa-spec.json"
W, H, BAR = 1920, 1080, 90          # the chapter bar's band at the bottom is left out


def runs(mask):
    out, i = [], 0
    while i < len(mask):
        if mask[i]:
            j = i
            while j < len(mask) and mask[j]:
                j += 1
            out.append((i, j))
            i = j
        else:
            i += 1
    return out


def main() -> None:
    film = Path(sys.argv[1]) if len(sys.argv) > 1 else FILM
    tl = json.loads((PUB / "timeline.json").read_text())
    spec = json.loads(SPEC.read_text())
    fps = tl["fps"]
    proc = subprocess.Popen(["ffmpeg", "-v", "error", "-i", str(film), "-map", "0:v:0", "-f", "rawvideo", "-pix_fmt", "gray", "-"],
                            stdout=subprocess.PIPE)
    size = W * H
    maxdiff, luma, std = [], [], []
    prev = None
    while True:
        buf = proc.stdout.read(size)
        if len(buf) < size:
            break
        f = np.frombuffer(buf, np.uint8).reshape(H, W)[: H - BAR]
        small = f.reshape((H - BAR) // 2, 2, W // 2, 2).mean(axis=(1, 3))
        luma.append(float(small.mean()))
        std.append(float(small.std()))
        cur = f.astype(np.int16)
        maxdiff.append(int(np.abs(cur - prev).max()) if prev is not None else 255)
        prev = cur
    proc.wait()
    n = len(luma)
    maxdiff, luma, std = np.array(maxdiff), np.array(luma), np.array(std)
    fades = np.zeros(n, bool)
    for a, b in spec.get("transitions", []):
        fades[max(0, int(a * fps) - 1): min(n, int(b * fps) + 2)] = True
    repeated = []
    for s in tl["shots"]:
        if s["kind"] != "footage":
            continue
        a, b = s["startFrame"], min(n, s["endFrame"])
        rep = [k for k in range(a + 1, b) if maxdiff[k] <= 2 and not fades[k]]
        spans = []                                   # runs of repeated frames, film seconds (+ the clip's own seconds)
        for k in rep:
            if spans and k == spans[-1][1]:
                spans[-1][1] = k + 1
            else:
                spans.append([k, k + 1])
        repeated.append({"shot": s["id"], "frames": [a, b], "source_from": s["fromFrame"], "repeated": len(rep),
                         "runs": [{"film": [round(x / fps, 3), round(y / fps, 3)], "frames": y - x,
                                   "clip": [round((s["fromFrame"] + x - a) / fps, 3), round((s["fromFrame"] + y - a) / fps, 3)]}
                                  for x, y in spans]})
    planned = np.zeros(n, bool)
    for a, b in spec.get("planned_black", []):
        planned[max(0, int(a * fps) - 1): min(n, int(b * fps) + 2)] = True
    black = (luma <= 24) & (std <= 4)
    black_runs = [{"seconds": [round(a / fps, 3), round(b / fps, 3)], "frames": b - a,
                   "planned": bool(planned[a:b].all()),
                   "clip_seconds": [round(a / fps - tl["marks"]["fall"] + tl["fall"]["from"], 3)] if tl["marks"]["fall"] <= a / fps < tl["marks"]["bh04"] else None}
                  for a, b in runs(black)]
    report = {"film": str(film), "frames": n, "fps": fps, "repeated_in_footage": repeated, "black_runs": black_runs,
              "rule": "repeated = largest pixel difference <= 2 from the previous frame (above the chapter bar), dissolves excluded; "
                      "black = mean luma <= 24 and std <= 4 at 960 px (scripts/qa/picture.py)"}
    out = ROOT / "out/black-hole-ai/qa/cadence.json"
    out.write_text(json.dumps(report, indent=1) + "\n")
    print(f"{n} frames decoded")
    for r in repeated:
        print(f"  {r['shot']}: {r['repeated']} repeated frames"
              + "".join(f"\n    clip {x['clip'][0]}-{x['clip'][1]} s ({x['frames']} frames)" for x in r["runs"]))
    for r in black_runs:
        print(f"  black {r['seconds']} ({r['frames']} frames) {'planned' if r['planned'] else 'NOT PLANNED'}"
              + (f", clip {r['clip_seconds']}" if r["clip_seconds"] else ""))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
