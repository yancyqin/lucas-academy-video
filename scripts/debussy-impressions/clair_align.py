#!/usr/bin/env python3
"""月光: register each AI painting (clair/paint/<key>.png) onto the photo it was painted from.

The reverse of align.py: here the PHOTO is the master frame (clair/frames/<key>.jpg|png, as named in
edits/03-clair.json) and the painting is warped into it, so the dissolve photo -> painting stays put.
Same matching as align.py (structure images, stretch / ECC / SIFT / template candidates, best NCC).
Writes clair/paint/aligned/<key>.png (photo frame, long side <= 2560), report.json, review/<key>.jpg
(photo | aligned painting | 50 % blend | painting edges over the photo).
usage: .venv-reframe/bin/python clair_align.py [keys...]   (default: every painting that exists)
"""
import json, os, sys
import numpy as np, cv2
from align import structure, ecc, sift_init, template_init, score, decompose, residual_flow, fill_edges, edges_overlay, warp, WORK

DATA = "/Users/yqin/repo/playground/lucas-academy-video-data/debussy-impressions"
PAINT = f"{DATA}/clair/paint"; OUT = f"{PAINT}/aligned"; REV = f"{OUT}/review"
HERE = os.path.dirname(os.path.abspath(__file__))

def photo_for(shot):
    """The final 16:9 photo: photo_final when Codex has made it, else the frame."""
    p = shot.get("photo_final")
    return f"{DATA}/{p}" if p and os.path.exists(f"{DATA}/{p}") else f"{DATA}/{shot['photo']}"

def main(keys):
    ed = json.load(open(f"{HERE}/edits/03-clair.json"))
    shots = {s["id"]: s for s in ed["shots"] if "painting" in s}
    keys = keys or [k for k in shots if os.path.exists(f"{PAINT}/{k}.png")]
    os.makedirs(REV, exist_ok=True)
    rep_path = f"{OUT}/report.json"
    report = json.load(open(rep_path)) if os.path.exists(rep_path) else {}
    for key in keys:
        P0 = cv2.imread(photo_for(shots[key])); R0 = cv2.imread(f"{PAINT}/{key}.png")
        h, w = P0.shape[:2]; k = WORK / max(h, w); size = (int(round(w * k)), int(round(h * k)))
        P = cv2.resize(P0, size, interpolation=cv2.INTER_AREA)
        kr = WORK / max(R0.shape[:2]); R = cv2.resize(R0, (int(R0.shape[1] * kr), int(R0.shape[0] * kr)), interpolation=cv2.INTER_AREA)
        Ps = structure(P); Rs = structure(R)
        stretch = np.float32([[size[0] / R.shape[1], 0, 0], [0, size[1] / R.shape[0], 0]])
        cands = {"stretch": stretch, "ecc": ecc(Ps, Rs, stretch, size)}
        Ms, n_in = sift_init(P, R)
        if Ms is not None:
            cands["sift"] = Ms.astype(np.float32); cands["sift+ecc"] = ecc(Ps, Rs, Ms, size, levels=(0.5, 1.0))
        Mt = template_init(Ps, Rs, size, scales=np.arange(1.0, 1.31, 0.02))
        if Mt is not None:
            cands["tmpl"] = Mt; cands["tmpl+ecc"] = ecc(Ps, Rs, Mt, size, levels=(0.5, 1.0))
        scored = {n: score(Ps, R, M, size) for n, M in cands.items()}
        base = size[0] / R.shape[1]
        valid = {n: v for n, v in scored.items() if v[1] > 0.95 and 0.8 < decompose(cands[n], size)["scale_x"] / base < 1.35}
        best = max(valid or scored, key=lambda n: scored[n][0]); M = cands[best]
        K = min(1.0, 2560 / max(h, w)); out_size = (int(round(w * K)), int(round(h * K)))
        A = (np.diag([out_size[0] / size[0], out_size[1] / size[1], 1.0]) @ np.vstack([M, [0, 0, 1]]) @ np.diag([kr, kr, 1.0]))[:2].astype(np.float32)
        Wfull = warp(R0, A, out_size); cover = warp(np.full(R0.shape[:2], 255, np.uint8), A, out_size)
        Wfull, filled = fill_edges(Wfull, cover)
        cv2.imwrite(f"{OUT}/{key}.png", Wfull)
        W = warp(R, M, size); mask = warp(np.ones(R.shape[:2], np.uint8), M, size) > 0
        med, p95 = residual_flow(Ps, structure(W), mask)
        report[key] = {"photo": os.path.relpath(photo_for(shots[key]), DATA), "method": best, "score": round(scored[best][0], 3),
                       "score_stretch": round(scored["stretch"][0], 3), "sift_inliers": n_in, "transform": decompose(M, size),
                       "uncovered_pct": round(100 * (1 - float((cover > 128).mean())), 2), "flow_median_pct": med, "flow_p95_pct": p95,
                       "painting_size": [R0.shape[1], R0.shape[0]], "edge_fill_px": filled, "out_size": list(out_size)}
        Pv = cv2.resize(P0, out_size, interpolation=cv2.INTER_AREA)
        tiles = [Pv, Wfull, cv2.addWeighted(Pv, 0.5, Wfull, 0.5, 0), edges_overlay(Pv, Wfull)]
        th = 540; tiles = [cv2.resize(t, (int(t.shape[1] * th / t.shape[0]), th)) for t in tiles]
        gap = np.full((th, 12, 3), 255, np.uint8); strip = tiles[0]
        for t in tiles[1:]: strip = np.hstack([strip, gap, t])
        cv2.imwrite(f"{REV}/{key}.jpg", strip, [cv2.IMWRITE_JPEG_QUALITY, 85])
        r = report[key]
        print(f"{key:15s} {best:9s} score {r['score_stretch']:.3f}->{r['score']:.3f} | sift {n_in:4d} | {r['transform']} | uncovered {r['uncovered_pct']:.1f}% | flow med {med}% p95 {p95}% | painting {r['painting_size']}")
    json.dump(report, open(rep_path, "w"), ensure_ascii=False, indent=1)

if __name__ == "__main__":
    main(sys.argv[1:])
