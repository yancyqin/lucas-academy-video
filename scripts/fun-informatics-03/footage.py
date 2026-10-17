"""Steady, cropped, cleaned-up Pictionary clips for NS02 (FUN-INFORMATICS-03.md §5.8).

    ../.venv-reframe/bin/python scripts/fun-informatics-03/footage.py [name ...]   (needs OpenCV)

The owner filmed the game handheld from above (lucas-academy-video-data/fun-informatics-03/drawings/
original/). For every clip the film uses, this:

  1. locks the shot: optical flow on what does not move (paper, pencil strokes, the table) estimates each
     frame's motion, and every frame is warped onto the clip's last frame, as if shot from a tripod.
     Hands and coloured pencils are masked out of the tracking, since they move on their own;
  2. crops to the drawing (the box is given in last-frame pixels), which leaves the clutter on the table
     outside the picture;
  3. cleans it up: the paper is white-balanced to the film's warm paper and the pencil lines are darkened;
  4. softens the crop's edges with a feathered blur, so nothing sharp sits at the border. The film puts a
     blurred, enlarged copy of the clip behind it (the owner asked for a blurred background).

Writes public/fun-informatics-03/footage/<name>.mp4 (H.264, 30 fps, with the original sound) and a
<name>.jpg poster of the last frame.
"""
import json
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SRC = Path("/Users/yqin/repo/playground/lucas-academy-video-data/fun-informatics-03/drawings/original")
OUT = ROOT / "public/fun-informatics-03/footage"
PAPER = np.array([230, 238, 242], np.float32)  # BGR of the film's warm white paper (#F2EEE6)
SMALL = 1 / 3  # tracking resolution

# name: source, trim [start, end) s, crop (x, y, w, h) in the trimmed clip's last frame, size of the crop
# once scaled, and "ccw" where the drawer sat at the camera's left: those drawings are turned upright, so
# a landscape crop comes out portrait. Every clip ends up 900 x 1200.
CLIPS = {
    "r1-lucas": {"src": "IMG_8516.MOV", "trim": (0.0, 36.0), "crop": (185, 678, 800, 600), "size": (1200, 900), "ccw": True},
    "r1-cachew": {"src": "IMG_8517.MOV", "trim": (0.0, 24.3), "crop": (190, 590, 840, 630), "size": (1200, 900), "ccw": True, "white": 0.985},
    "r2-umbrella": {"src": "IMG_8527.MOV", "trim": (0.0, 10.2), "crop": (89, 622, 800, 600), "size": (1200, 900), "ccw": True},
    "r2-moon": {"src": "IMG_8529.MOV", "trim": (0.0, 14.5), "crop": (330, 660, 540, 720), "size": (900, 1200), "white": 0.97},
    "r2-star": {"src": "IMG_8530.MOV", "trim": (0.0, 22.9), "crop": (458, 110, 720, 960), "size": (900, 1200)},
}


def frames(path, start, end):
    cap = cv2.VideoCapture(str(path))
    fps = cap.get(cv2.CAP_PROP_FPS)
    cap.set(cv2.CAP_PROP_POS_MSEC, start * 1000)
    i = 0
    while True:
        ok, f = cap.read()
        if not ok or (start + i / fps) >= end:
            break
        yield f
        i += 1
    cap.release()


def still_mask(small_bgr):
    """Where tracking may look: grey or white, not skin, not a coloured pencil."""
    hsv = cv2.cvtColor(small_bgr, cv2.COLOR_BGR2HSV)
    mask = (hsv[..., 1] < 45).astype(np.uint8) * 255
    return cv2.erode(mask, np.ones((9, 9), np.uint8))


def motions(path, start, end):
    """3x3 transforms M[i] mapping frame i onto frame i+1 (full resolution)."""
    S = np.diag([SMALL, SMALL, 1.0])
    Sinv = np.linalg.inv(S)
    prev = prev_mask = None
    out, kept = [], []
    for f in frames(path, start, end):
        small = cv2.resize(f, None, fx=SMALL, fy=SMALL, interpolation=cv2.INTER_AREA)
        gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
        if prev is not None:
            M = np.eye(3)
            pts = cv2.goodFeaturesToTrack(prev, maxCorners=500, qualityLevel=0.005, minDistance=6, mask=prev_mask)
            if pts is not None and len(pts) >= 12:
                nxt, st, _ = cv2.calcOpticalFlowPyrLK(prev, gray, pts, None, winSize=(21, 21), maxLevel=3)
                good = st.ravel() == 1
                if good.sum() >= 12:
                    A, inliers = cv2.estimateAffinePartial2D(pts[good], nxt[good], method=cv2.RANSAC, ransacReprojThreshold=1.5)
                    if A is not None and inliers.sum() >= 10:
                        M = Sinv @ np.vstack([A, [0, 0, 1]]) @ S
                        kept.append(int(inliers.sum()))
            out.append(M)
        prev, prev_mask = gray, still_mask(small)
    return out, kept


def grade_lut(last_crop, white=0.92):
    """Per-channel LUTs: the paper (bright, grey) goes to PAPER, light shadows with it; pencil lines darken."""
    bright = last_crop.reshape(-1, 3)
    lum = bright.mean(axis=1)
    paper = np.median(bright[lum > np.percentile(lum, 70)], axis=0).astype(np.float32)
    x = np.arange(256, dtype=np.float32)
    luts = []
    for c in range(3):
        # As a fraction of the paper: grey shadows near it (above `white`) become paper, pencil darkens, anything
        # at a quarter of the paper or below is ink. A lightly drawn clip gets a higher `white`, or its lines fade.
        v = np.clip((x / paper[c] - 0.25) / (white - 0.25), 0, 1)
        luts.append(np.clip(PAPER[c] * np.power(v, 1.3), 0, 255).astype(np.uint8))
    return luts, paper


def feather(w, h, edge):
    m = np.zeros((h, w), np.float32)
    m[edge:h - edge, edge:w - edge] = 1
    return cv2.GaussianBlur(m, (0, 0), edge / 2)[..., None]


def build(name, cfg):
    src = SRC / cfg["src"]
    start, end = cfg["trim"]
    M, kept = motions(src, start, end)
    # A[i] maps frame i onto the last frame.
    A = [np.eye(3)]
    for m in reversed(M):
        A.append(A[-1] @ m)
    A = A[::-1]
    x, y, w, h = cfg["crop"]
    W, H = cfg["size"]
    to_out = np.array([[W / w, 0, -x * W / w], [0, H / h, -y * H / h], [0, 0, 1]])
    last = list(frames(src, end - 0.2, end))[-1]
    last_crop = cv2.warpAffine(last, to_out[:2], (W, H))
    luts, paper = grade_lut(last_crop, cfg.get("white", 0.92))
    soft = feather(W, H, 60)
    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / f"{name}.mp4"
    enc = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{H}x{W}" if cfg.get("ccw") else f"{W}x{H}", "-r", "30", "-i", "-",
         "-ss", f"{start}", "-t", f"{end - start}", "-i", str(src), "-map", "0:v", "-map", "1:a", "-c:v", "libx264",
         "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-shortest", str(out)],
        stdin=subprocess.PIPE)
    n = 0
    for i, f in enumerate(frames(src, start, end)):
        T = to_out @ A[min(i, len(A) - 1)]
        img = cv2.warpAffine(f, T[:2], (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        img = cv2.merge([cv2.LUT(img[..., c], luts[c]) for c in range(3)])
        blurred = cv2.GaussianBlur(img, (0, 0), 18)
        img = (img * soft + blurred * (1 - soft)).astype(np.uint8)
        if cfg.get("ccw"):
            img = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
        enc.stdin.write(np.ascontiguousarray(img).tobytes())
        n += 1
    enc.stdin.close()
    enc.wait()
    cv2.imwrite(str(OUT / f"{name}.jpg"), img)
    report = {"frames": n, "tracked": f"{len(kept)}/{len(M)}", "median_inliers": int(np.median(kept)) if kept else 0,
              "paper_bgr": paper.round().tolist()}
    print(name, json.dumps(report), flush=True)
    return report


def main():
    names = sys.argv[1:] or list(CLIPS)
    for name in names:
        build(name, CLIPS[name])


if __name__ == "__main__":
    main()
