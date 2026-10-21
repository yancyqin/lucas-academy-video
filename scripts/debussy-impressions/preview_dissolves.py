#!/usr/bin/env python3
"""Render a review video: for each id, aligned photo (hold) -> cross-dissolve -> painting (hold).

Each image is fitted into a 1920x1080 frame on a near-black ground with a small id label; one clip per
pair (ffmpeg xfade), then concat (chained xfade breaks timestamps, so never chain them).
usage: .venv-reframe/bin/python preview_dissolves.py [--hold-photo 1.5 --fade 5 --hold-painting 3] out.mp4 id [id ...]
"""
import os, subprocess, sys, tempfile
import cv2, numpy as np
DATA = "/Users/yqin/repo/playground/lucas-academy-video-data/debussy-impressions"
W, H, BG = 1920, 1080, (17, 17, 20)
HOLD_A, FADE, HOLD_B = 1.5, 5.0, 3.0   # owner 2026-10-14: photo 1.5 s, dissolve 5 s, painting 3 s

def frame(img, label):
    k = min(W / img.shape[1], H / img.shape[0]); im = cv2.resize(img, (int(img.shape[1] * k), int(img.shape[0] * k)), interpolation=cv2.INTER_AREA)
    f = np.full((H, W, 3), BG, np.uint8); y = (H - im.shape[0]) // 2; x = (W - im.shape[1]) // 2; f[y:y + im.shape[0], x:x + im.shape[1]] = im
    cv2.putText(f, label, (24, 44), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (200, 200, 200), 2, cv2.LINE_AA)
    return f

def main(out, ids):
    tmp = tempfile.mkdtemp(prefix="dissolve-"); clips = []
    for pid in ids:
        a = cv2.imread(f"{DATA}/real/aligned/{pid}.png"); b = cv2.imread(f"{DATA}/art/{pid}.jpg")
        b = cv2.resize(b, (a.shape[1], a.shape[0]), interpolation=cv2.INTER_AREA)
        fa, fb = f"{tmp}/{pid}-a.png", f"{tmp}/{pid}-b.png"
        cv2.imwrite(fa, frame(a, pid)); cv2.imwrite(fb, frame(b, pid))
        clip = f"{tmp}/{pid}.mp4"; T = HOLD_A + FADE + HOLD_B
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-t", str(T), "-i", fa, "-loop", "1", "-t", str(T), "-i", fb,
                        "-filter_complex", f"[0][1]xfade=transition=fade:duration={FADE}:offset={HOLD_A},format=yuv420p,fps=30",
                        "-t", str(T), "-c:v", "libx264", "-crf", "18", "-preset", "medium", clip], check=True)
        clips.append(clip)
    lst = f"{tmp}/list.txt"; open(lst, "w").write("".join(f"file '{c}'\n" for c in clips))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", "-movflags", "+faststart", out], check=True)
    print("wrote", out)

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(); ap.add_argument("--hold-photo", type=float, default=HOLD_A); ap.add_argument("--fade", type=float, default=FADE)
    ap.add_argument("--hold-painting", type=float, default=HOLD_B); ap.add_argument("out"); ap.add_argument("ids", nargs="+")
    a = ap.parse_args(); HOLD_A, FADE, HOLD_B = a.hold_photo, a.fade, a.hold_painting
    main(a.out, a.ids)
