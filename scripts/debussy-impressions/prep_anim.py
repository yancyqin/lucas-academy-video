#!/usr/bin/env python3
"""Turn a MiniMax clip into a layer the renderer can use: slowed, registered to the painting, painting-sized.

1. slow to `speed` (0.5 = half speed) with motion-compensated interpolation to 30 fps (ffmpeg minterpolate)
2. register the clip's first frame onto the painting (SIFT + RANSAC similarity, ECC fallback on blurred structure)
3. warp every frame into the painting frame at the same size as real/aligned/<id>.png and write anim.mp4
usage: .venv-reframe/bin/python prep_anim.py RUNDIR --speed 0.5 [--until SECONDS] [--motion-region "x,y;x,y;..."]
"""
import argparse, json, os, subprocess, sys
import cv2, numpy as np
DATA = "/Users/yqin/repo/playground/lucas-academy-video-data/debussy-impressions"

def register(frame0, painting):
    sift = cv2.SIFT_create(nfeatures=6000)
    g1 = cv2.cvtColor(frame0, cv2.COLOR_BGR2GRAY); g2 = cv2.cvtColor(painting, cv2.COLOR_BGR2GRAY)
    k1, d1 = sift.detectAndCompute(g1, None); k2, d2 = sift.detectAndCompute(g2, None)
    m = cv2.BFMatcher().knnMatch(d1, d2, k=2); good = [a for a, b in (x for x in m if len(x) == 2) if a.distance < 0.75 * b.distance]
    src = np.float32([k1[g.queryIdx].pt for g in good]); dst = np.float32([k2[g.trainIdx].pt for g in good])
    M, inl = cv2.estimateAffinePartial2D(src, dst, method=cv2.RANSAC, ransacReprojThreshold=3.0, maxIters=10000)
    return M, int(inl.sum()) if inl is not None else 0, len(good)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("run"); ap.add_argument("--speed", type=float, default=0.5)
    ap.add_argument("--until", type=float, default=None, help="use only the first N seconds of the source (cut before a drift)")
    ap.add_argument("--motion-region", default=None, help="'x,y;x,y;...' normalized polygon: only this area moves, the rest stays the painting")
    a = ap.parse_args()
    meta = json.load(open(os.path.join(a.run, "request-metadata.json"))); pid = meta["id"]
    src = os.path.join(a.run, "original.mp4"); slow = os.path.join(a.run, f"slow-{a.speed:g}x.mp4")
    cut = ["-t", str(a.until)] if a.until else []
    subprocess.run(["ffmpeg", "-v", "error", "-y", *cut, "-i", src, "-vf", f"setpts=PTS/{a.speed},minterpolate=fps=30:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1",
                    "-an", "-c:v", "libx264", "-crf", "12", "-preset", "medium", "-pix_fmt", "yuv420p", slow], check=True)
    ref = cv2.imread(f"{DATA}/real/aligned/{pid}.png") if os.path.exists(f"{DATA}/real/aligned/{pid}.png") else None
    P = cv2.imread(f"{DATA}/art/{pid}.jpg"); H0, W0 = (ref.shape[:2] if ref is not None else (int(P.shape[0] * 2160 / max(P.shape[:2])), int(P.shape[1] * 2160 / max(P.shape[:2]))))
    Pw = cv2.resize(P, (W0, H0), interpolation=cv2.INTER_AREA)
    cap = cv2.VideoCapture(slow); ok, f0 = cap.read()
    M, inl, ng = register(f0, Pw)
    sx = float(np.hypot(M[0, 0], M[1, 0]))
    print(f"{pid}: registration inliers {inl}/{ng}, scale {sx:.3f}, rot {np.degrees(np.arctan2(M[1, 0], M[0, 0])):.2f} deg, shift {M[0, 2]:.1f},{M[1, 2]:.1f}")
    out = os.path.join(a.run, "anim.mp4")
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W0}x{H0}", "-r", "30", "-i", "-",
                            "-c:v", "libx264", "-crf", "14", "-preset", "medium", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    mask = None
    if a.motion_region:                                              # feathered matte: motion inside, painting outside
        pts = np.array([[float(v) for v in xy.split(",")] for xy in a.motion_region.split(";")]) * [W0, H0]
        m = np.zeros((H0, W0), np.float32); cv2.fillPoly(m, [pts.astype(np.int32)], 1.0)
        mask = cv2.GaussianBlur(m, (0, 0), 0.025 * W0)[..., None]
        Pf = Pw.astype(np.float32)
    n = 0; f = f0
    while ok:
        w = cv2.warpAffine(f, M, (W0, H0), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        if mask is not None: w = (w.astype(np.float32) * mask + Pf * (1 - mask)).astype(np.uint8)
        enc.stdin.write(w.tobytes()); n += 1; ok, f = cap.read()
    enc.stdin.close(); enc.wait()
    # how close is frame 0 to the painting after registration (mean abs diff on 256-px grey)
    w0 = cv2.warpAffine(f0, M, (W0, H0), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    sm = lambda x: cv2.resize(cv2.cvtColor(x, cv2.COLOR_BGR2GRAY), (256, int(256 * H0 / W0))).astype(np.float32)
    info = {"speed": a.speed, "until_s": a.until, "motion_region": a.motion_region, "frames": n, "duration_s": round(n / 30, 3), "size": [W0, H0], "inliers": inl, "matches": ng, "affine": M.round(4).tolist(),
            "frame0_vs_painting_mad": round(float(np.abs(sm(w0) - sm(Pw)).mean()), 2)}
    json.dump(info, open(os.path.join(a.run, "anim.json"), "w"), indent=1); print(info)

if __name__ == "__main__":
    main()
