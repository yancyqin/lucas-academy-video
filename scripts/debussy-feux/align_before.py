#!/usr/bin/env python3
"""Register each "before the light dims" photo onto its painting AS CROPPED FOR THE ART LAB (assets/living/feux-<id>.jpg),
so the film can dissolve photo -> living painting without a jump. Same method as debussy-impressions/align.py
(structure images, ECC / SIFT / template candidates, best score kept).

Writes feux/real/aligned/<id>.png (exactly the asset's size), feux/real/aligned/report.json and review/<id>.jpg
(painting | aligned photo | 50 % blend | edge overlay).

usage: .venv-reframe/bin/python align_before.py [ids...]
"""
import json, os, sys, glob
import numpy as np, cv2

DATA = "/Users/yqin/repo/playground/lucas-academy-video-data/debussy-impressions"
ASSETS = "/Users/yqin/repo/playground/lucas-visual-art-lab-feux/assets/living"
REAL = f"{DATA}/feux/real"
OUT = f"{REAL}/aligned"; REV = f"{OUT}/review"
WORK = 900       # analysis long side
PHOTOS = {"montorgueil": f"{DATA}/real/aligned/fire-2.png", "beijing": f"{DATA}/clair/frames/beijing-tower.png"}
# Composition-locked edits (round 2) already sit on the painting; day-vs-night structure fools the matcher into 2-3x
# zooms, so these are just resized to the painting (checked by eye on 50 % blends).
STRETCH = {"venice", "montmartre", "rhone"}

def photo_path(pid):
    if pid in PHOTOS: return PHOTOS[pid]
    vs = sorted(glob.glob(f"{REAL}/{pid}-before-v*.png"), key=lambda p: int(p.rsplit("-v", 1)[1].split(".")[0]))
    return vs[-1] if vs else f"{REAL}/{pid}-before.png"

def structure(img, sigma_frac=0.012):
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    g = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(g)
    s = max(1.0, sigma_frac * max(g.shape))
    g = cv2.GaussianBlur(g.astype(np.float32) / 255.0, (0, 0), s)
    return (g - g.mean()) / (g.std() + 1e-6)

def gradmag(s):
    gx = cv2.Sobel(s, cv2.CV_32F, 1, 0, ksize=3); gy = cv2.Sobel(s, cv2.CV_32F, 0, 1, ksize=3)
    m = np.sqrt(gx * gx + gy * gy); return (m - m.mean()) / (m.std() + 1e-6)

def ncc(a, b, mask=None):
    if mask is None: mask = np.ones_like(a, bool)
    a, b = a[mask], b[mask]; a = a - a.mean(); b = b - b.mean()
    return float((a * b).sum() / (np.sqrt((a * a).sum() * (b * b).sum()) + 1e-9))

def warp(img, M, size):
    return cv2.warpAffine(img, M, size, flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_CONSTANT, borderValue=0)

def score(Ps, R, M, size):
    W = warp(R, M, size); mask = warp(np.ones(R.shape[:2], np.uint8), M, size) > 0
    Ws = structure(W)
    return 0.5 * ncc(Ps, Ws, mask) + 0.5 * ncc(gradmag(Ps), gradmag(Ws), mask), float(mask.mean())

def ecc(Ps, Rs_full, M0, size, levels=(0.25, 0.5, 1.0)):
    M = M0.copy().astype(np.float32)
    for lv in levels:
        sz = (max(32, int(size[0] * lv)), max(32, int(size[1] * lv)))
        P = cv2.resize(Ps, sz, interpolation=cv2.INTER_AREA)
        S = np.diag([lv, lv, 1.0]).astype(np.float32)
        Ml = (S @ np.vstack([M, [0, 0, 1]]) @ np.linalg.inv(np.diag([lv, lv, 1.0])).astype(np.float32))[:2]
        Rl = cv2.resize(Rs_full, (max(32, int(Rs_full.shape[1] * lv)), max(32, int(Rs_full.shape[0] * lv))), interpolation=cv2.INTER_AREA)
        # transform maps photo(level) -> painting(level); ECC wants template=painting, input=photo warped with inverse map
        try:
            _, Mi = cv2.findTransformECC(P, Rl, cv2.invertAffineTransform(Ml).astype(np.float32), cv2.MOTION_AFFINE,
                                          (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 300, 1e-6), None, 5)
            Ml = cv2.invertAffineTransform(Mi)
        except cv2.error:
            pass
        M = (np.linalg.inv(S) @ np.vstack([Ml, [0, 0, 1]]) @ np.diag([lv, lv, 1.0]).astype(np.float32))[:2]
    return M.astype(np.float32)

def sift_init(P, R):
    sift = cv2.SIFT_create(nfeatures=4000)
    gp = cv2.GaussianBlur(cv2.cvtColor(P, cv2.COLOR_BGR2GRAY), (0, 0), 2); gr = cv2.GaussianBlur(cv2.cvtColor(R, cv2.COLOR_BGR2GRAY), (0, 0), 2)
    kp1, d1 = sift.detectAndCompute(gr, None); kp2, d2 = sift.detectAndCompute(gp, None)
    if d1 is None or d2 is None or len(kp1) < 8 or len(kp2) < 8: return None, 0
    m = cv2.BFMatcher().knnMatch(d1, d2, k=2)
    good = [a for a, b in (x for x in m if len(x) == 2) if a.distance < 0.8 * b.distance]
    if len(good) < 8: return None, len(good)
    src = np.float32([kp1[g.queryIdx].pt for g in good]); dst = np.float32([kp2[g.trainIdx].pt for g in good])
    M, inl = cv2.estimateAffinePartial2D(src, dst, method=cv2.RANSAC, ransacReprojThreshold=0.02 * max(P.shape[:2]), maxIters=5000)
    return M, int(inl.sum()) if inl is not None else 0

def template_init(Ps, Rs, size, scales=np.arange(1.0, 2.61, 0.04)):
    """Painting = a crop of a wider photo. Slide the painting's structure over the photo enlarged by s."""
    W, H = size; best = (-2, None)
    Pg = gradmag(Ps)
    for s in scales:
        k = W * s / Rs.shape[1]; rw, rh = int(Rs.shape[1] * k), int(Rs.shape[0] * k)
        if rw < W or rh < H: continue
        R2 = cv2.resize(Rs, (rw, rh), interpolation=cv2.INTER_AREA)
        sc = 0.5 * cv2.matchTemplate(R2, Ps, cv2.TM_CCOEFF_NORMED) + 0.5 * cv2.matchTemplate(gradmag(R2), Pg, cv2.TM_CCOEFF_NORMED)
        _, v, _, loc = cv2.minMaxLoc(sc)
        if v > best[0]: best = (v, np.float32([[k, 0, -loc[0]], [0, k, -loc[1]]]))
    return best[1]

def decompose(M, size):
    a, b, c, d = M[0, 0], M[0, 1], M[1, 0], M[1, 1]
    sx = np.hypot(a, c); sy = np.hypot(b, d); rot = np.degrees(np.arctan2(c, a))
    return {"scale_x": round(float(sx), 3), "scale_y": round(float(sy), 3), "rot_deg": round(float(rot), 2),
            "shift_x_pct": round(100 * float(M[0, 2]) / size[0], 1), "shift_y_pct": round(100 * float(M[1, 2]) / size[1], 1)}

def residual_flow(Ps, Ws, mask):
    a = cv2.normalize(Ps, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8); b = cv2.normalize(Ws, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    dis = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)
    f = dis.calc(a, b, None); mag = np.hypot(f[..., 0], f[..., 1])[mask]
    w = Ps.shape[1]
    return round(100 * float(np.median(mag)) / w, 2), round(100 * float(np.percentile(mag, 95)) / w, 2)

def fill_edges(img, cover):
    """Fill uncovered bands at the frame edges by stretching the nearest strip of real photo outward.
    Only the outermost band (at most ~4x its own width) is resampled; the aligned interior is untouched."""
    h, w = cover.shape; ok = cover > 128
    cols = ok.any(axis=0); rows = ok.any(axis=1)
    first_y = np.where(cols, ok.argmax(axis=0), h); last_y = np.where(cols, h - 1 - ok[::-1].argmax(axis=0), -1)
    xs = np.arange(int(w * 0.02), int(w * 0.98))
    t = int(first_y[xs].max()); b = int((h - 1 - last_y[xs]).max())
    ys = np.arange(t, h - b) if h - b > t else np.arange(0, h)
    first_x = ok[ys].argmax(axis=1); last_x = w - 1 - ok[ys][:, ::-1].argmax(axis=1)
    l = int(first_x.max()); r = int((w - 1 - last_x).max())
    t, b, l, r = [v + 1 if v else 0 for v in (t, b, l, r)]
    if t + b > 0.2 * h or l + r > 0.2 * w:
        return img, {"top": t, "bottom": b, "left": l, "right": r, "skipped": True}
    out = img.copy()
    if t:
        L = min(h // 4, 4 * t + 8); out[0:t + L] = cv2.resize(img[t:t + L], (w, t + L), interpolation=cv2.INTER_CUBIC)
    if b:
        L = min(h // 4, 4 * b + 8); out[h - b - L:h] = cv2.resize(img[h - b - L:h - b], (w, b + L), interpolation=cv2.INTER_CUBIC)
    if l:
        L = min(w // 4, 4 * l + 8); out[:, 0:l + L] = cv2.resize(out[:, l:l + L], (l + L, h), interpolation=cv2.INTER_CUBIC)
    if r:
        L = min(w // 4, 4 * r + 8); out[:, w - r - L:w] = cv2.resize(out[:, w - r - L:w - r], (r + L, h), interpolation=cv2.INTER_CUBIC)
    return out, {"top": t, "bottom": b, "left": l, "right": r}

def edges_overlay(P, W):
    e = cv2.Canny(cv2.GaussianBlur(cv2.cvtColor(W, cv2.COLOR_BGR2GRAY), (0, 0), 2.5), 40, 110)
    base = cv2.cvtColor(cv2.cvtColor(P, cv2.COLOR_BGR2GRAY), cv2.COLOR_GRAY2BGR) // 2 + 60
    base[e > 0] = (40, 40, 255)
    return base

def main(ids):
    os.makedirs(REV, exist_ok=True)
    rep_path = f"{OUT}/report.json"
    report = json.load(open(rep_path)) if os.path.exists(rep_path) else {}
    for pid in ids:
        P0 = cv2.imread(f"{ASSETS}/feux-{pid}.jpg"); R0 = cv2.imread(photo_path(pid))
        if pid in STRETCH:
            cv2.imwrite(f"{OUT}/{pid}.png", cv2.resize(R0, (P0.shape[1], P0.shape[0]), interpolation=cv2.INTER_AREA))
            report[pid] = {"photo": os.path.basename(photo_path(pid)), "method": "stretch (composition-locked edit)"}
            print(f"{pid:8s} stretch"); continue
        h, w = P0.shape[:2]; k = WORK / max(h, w); size = (int(round(w * k)), int(round(h * k)))
        P = cv2.resize(P0, size, interpolation=cv2.INTER_AREA)
        kr = WORK / max(R0.shape[:2]); R = cv2.resize(R0, (int(R0.shape[1] * kr), int(R0.shape[0] * kr)), interpolation=cv2.INTER_AREA)
        Ps = structure(P); Rs = structure(R)
        stretch = np.float32([[size[0] / R.shape[1], 0, 0], [0, size[1] / R.shape[0], 0]])
        cands = {"stretch": stretch}
        cands["ecc"] = ecc(Ps, Rs, stretch, size)
        Ms, n_in = sift_init(P, R)
        if Ms is not None:
            cands["sift"] = Ms.astype(np.float32); cands["sift+ecc"] = ecc(Ps, Rs, Ms, size, levels=(0.5, 1.0))
        Mt = template_init(Ps, Rs, size)
        if Mt is not None:
            cands["tmpl"] = Mt; cands["tmpl+ecc"] = ecc(Ps, Rs, Mt, size, levels=(0.5, 1.0))
        scored = {}
        for name, M in cands.items():
            s, cov = score(Ps, R, M, size); scored[name] = (s, cov)
        valid = {k2: v for k2, v in scored.items() if v[1] > 0.95 and 0.6 < decompose(cands[k2], size)["scale_x"] / (size[0] / R.shape[1]) < 2.7}
        best = max(valid or scored, key=lambda k2: scored[k2][0])
        M = cands[best]
        # full-resolution output in the painting frame
        out_size = (w, h)                                                    # the asset's own size
        A = np.diag([out_size[0] / size[0], out_size[1] / size[1], 1.0]) @ np.vstack([M, [0, 0, 1]]) @ np.diag([kr, kr, 1.0])
        A = A[:2].astype(np.float32)
        Wfull = warp(R0, A, out_size); cover = warp(np.full(R0.shape[:2], 255, np.uint8), A, out_size)
        Wfull, filled = fill_edges(Wfull, cover)
        cv2.imwrite(f"{OUT}/{pid}.png", Wfull)
        # residual
        W = warp(R, M, size); mask = warp(np.ones(R.shape[:2], np.uint8), M, size) > 0
        med, p95 = residual_flow(Ps, structure(W), mask)
        miss = 100 * (1 - float((cover > 128).mean()))
        report[pid] = {"photo": os.path.basename(photo_path(pid)), "method": best, "scores": {k2: round(v[0], 3) for k2, v in scored.items()},
                       "score": round(scored[best][0], 3), "score_stretch": round(scored["stretch"][0], 3), "sift_inliers": n_in,
                       "transform": decompose(M, size), "uncovered_pct": round(miss, 2), "flow_median_pct": med, "flow_p95_pct": p95,
                       "photo_ratio": round(R0.shape[1] / R0.shape[0], 3), "painting_ratio": round(w / h, 3), "edge_fill_px": filled, "out_size": list(out_size)}
        # review strip
        Pv = cv2.resize(P0, out_size, interpolation=cv2.INTER_AREA)
        blend = cv2.addWeighted(Pv, 0.5, Wfull, 0.5, 0)
        tiles = [Pv, Wfull, blend, edges_overlay(Pv, Wfull)]
        th = 700; tiles = [cv2.resize(t, (int(t.shape[1] * th / t.shape[0]), th)) for t in tiles]
        gap = np.full((th, 12, 3), 255, np.uint8); strip = tiles[0]
        for t in tiles[1:]: strip = np.hstack([strip, gap, t])
        cv2.imwrite(f"{REV}/{pid}.jpg", strip, [cv2.IMWRITE_JPEG_QUALITY, 85])
        r = report[pid]
        print(f"{pid:8s} {r['method']:9s} score {r['score_stretch']:.3f}->{r['score']:.3f} | sift inl {n_in:4d} | {r['transform']} | uncovered {r['uncovered_pct']:.1f}% fill {filled} | flow med {med}% p95 {p95}% | ratio photo {r['photo_ratio']} painting {r['painting_ratio']}")
    json.dump(report, open(rep_path, "w"), ensure_ascii=False, indent=1)

if __name__ == "__main__":
    ids = sys.argv[1:] or ["venice", "parliament", "montmartre", "rhone", "beijing", "rocket", "montorgueil"]
    main(ids)
