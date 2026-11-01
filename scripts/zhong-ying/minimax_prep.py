"""A work's MiniMax clip, made ready to follow its living painting (the third step: painted → alive → moving).

    .venv-reframe/bin/python scripts/zhong-ying/minimax_prep.py <film> <work id> <run dir> [--tone]

The clip (MiniMax-Hailuo-02, first frame = the art-lab picture; made with scripts/debussy-impressions/minimax_job.py,
MINIMAX_DATA=lucas-academy-video-data/zhong-ying) is scaled to the film's picture size (1230 × 820) and brought
from 24 to 30 fps by motion interpolation. --tone pulls every frame's colour back to the picture: MiniMax tends to
re-tone a pale painting within the first second (the paper greys, washes saturate), so each frame's Lab mean and
spread are matched to the clip's first frame, which is the picture itself.

Writes public/zhong-ying/<film>/minimax-<work>.mp4 and .json ({seconds, run, tone, firstFrameDiff}); build_timeline.py
gives a work with a clip the time to play it after its last verse, and paint.py dissolves into it.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from films import PUBLIC  # noqa: E402

PW, PH = 1230, 820


def frames(path):
    proc = subprocess.Popen(["ffmpeg", "-v", "error", "-i", str(path), "-vf", f"scale={PW}:{PH}:flags=area",
                             "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    while True:
        buf = proc.stdout.read(PW * PH * 3)
        if len(buf) < PW * PH * 3:
            break
        yield np.frombuffer(buf, np.uint8).reshape(PH, PW, 3)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("film")
    ap.add_argument("work")
    ap.add_argument("run")
    ap.add_argument("--tone", action="store_true")
    a = ap.parse_args()
    run = Path(a.run)
    out = PUBLIC / a.film / f"minimax-{a.work}.mp4"
    picture = cv2.cvtColor(cv2.imread(str(PUBLIC / a.film / f"living-{a.work}.jpg")), cv2.COLOR_BGR2RGB)
    picture = cv2.resize(picture, (PW, PH), interpolation=cv2.INTER_AREA)
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{PW}x{PH}",
                            "-r", "24", "-i", "-", "-vf", "minterpolate=fps=30:mi_mode=mci:mc_mode=aobmc:me_mode=bidir",
                            "-c:v", "libx264", "-crf", "14", "-pix_fmt", "yuv420p", str(out)], stdin=subprocess.PIPE)
    ref = None
    n = 0
    first_diff = None
    for frame in frames(run / "original.mp4"):
        if first_diff is None:
            first_diff = float(np.abs(frame.astype(float) - picture).mean())
        if a.tone:
            lab = cv2.cvtColor(frame, cv2.COLOR_RGB2LAB).astype(np.float32)
            if ref is None:
                ref = (lab.reshape(-1, 3).mean(0), lab.reshape(-1, 3).std(0) + 1e-6)
            mean, std = lab.reshape(-1, 3).mean(0), lab.reshape(-1, 3).std(0) + 1e-6
            lab = (lab - mean) / std * ref[1] + ref[0]
            frame = cv2.cvtColor(np.clip(lab, 0, 255).astype(np.uint8), cv2.COLOR_LAB2RGB)
        enc.stdin.write(frame.tobytes())
        n += 1
    enc.stdin.close()
    enc.wait()
    seconds = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(out)],
                                   capture_output=True, text=True, check=True).stdout)
    meta = {"seconds": round(seconds, 3), "run": str(run), "tone": a.tone, "sourceFrames": n,
            "firstFrameDiff": round(first_diff, 2)}
    out.with_suffix(".json").write_text(json.dumps(meta, indent=1))
    print(f"{out.name}: {seconds:.2f}s, first frame differs from the picture by {first_diff:.1f}/255 on average")


if __name__ == "__main__":
    main()
