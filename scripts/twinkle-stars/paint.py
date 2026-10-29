"""paint.py — split a painterly picture (watercolour, oil, Chinese ink, coloured pencil) for crayon.py's planner.

Painted pictures have no closed black outlines, so the areas come from colour instead: mean-shift smoothing flattens
the brush texture, k-means groups the colours, connected pieces become regions and specks merge into their neighbour.
The lines to draw first depend on the medium:
  sketch   the region boundaries with real colour contrast, smoothed: a synthetic underdrawing (pencil for watercolour,
           a thin brown brush for oil) that film.py draws in its own colour before the paint goes on;
  picture  the picture's own dark, thin strokes (Chinese ink lines, coloured-pencil outlines), revealed from the picture.
Writes the same npz as crayon.analyze (lines, rid, paths, on_star, thick, meta) plus `mode`.

    python paint.py PICTURE.png OUT.npz --lines sketch|picture [--k 14] [--preview P.jpg]
"""
import argparse, json
import numpy as np, cv2
from skimage.morphology import skeletonize
import crayon


def colour_regions(rgb, k=14, min_frac=0.0035, seed=0):
    H, W = rgb.shape[:2]; s = 768 / W
    small = cv2.resize(rgb, (768, int(round(H * s))), interpolation=cv2.INTER_AREA)
    flat = cv2.pyrMeanShiftFiltering(cv2.cvtColor(small, cv2.COLOR_RGB2BGR), 14, 26)
    lab = cv2.cvtColor(flat, cv2.COLOR_BGR2LAB).astype(np.float32)
    cv2.setRNGSeed(seed)
    _, lbl, _ = cv2.kmeans(lab.reshape(-1, 3), k, None, (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.5), 3,
                           cv2.KMEANS_PP_CENTERS)
    lbl = cv2.medianBlur(lbl.reshape(lab.shape[:2]).astype(np.uint8), 5)
    comp = np.full(lbl.shape, -1, np.int32); n = 0
    for c in range(k):
        m, cc = cv2.connectedComponents((lbl == c).astype(np.uint8), connectivity=4)
        for j in range(1, m): comp[cc == j] = n; n += 1
    # merge specks into the neighbour they share the longest border with, smallest first, until none is left
    min_px = min_frac * comp.size
    while True:
        ids, cnt = np.unique(comp, return_counts=True)
        small_ids = [i for i, c in sorted(zip(ids, cnt), key=lambda x: x[1]) if c < min_px]
        if not small_ids: break
        i = small_ids[0]; m = (comp == i).astype(np.uint8)
        ring = cv2.dilate(m, np.ones((3, 3), np.uint8)).astype(bool) & (comp != i)
        nb, nc = np.unique(comp[ring], return_counts=True)
        comp[m.astype(bool)] = nb[np.argmax(nc)] if len(nb) else comp[m.astype(bool)][0]
    ids = np.unique(comp); remap = {v: j for j, v in enumerate(ids)}
    comp = np.vectorize(remap.get)(comp).astype(np.int32)
    rid = cv2.resize(comp.astype(np.float32), (W, H), interpolation=cv2.INTER_NEAREST).astype(np.int32)
    meta = []
    for r in range(len(ids)):
        m = rid == r; ys, xs = np.nonzero(m)
        meta.append({"id": r, "area": int(m.sum()), "color": [int(v) for v in np.median(rgb[m].reshape(-1, 3), 0)],
                     "bbox": [int(xs.min()), int(ys.min()), int(xs.max() - xs.min() + 1), int(ys.max() - ys.min() + 1)],
                     "center": [float(xs.mean()), float(ys.mean())]})
    return rid, meta


def sketch_lines(rgb, rid, min_contrast=34.0):
    """Region borders with real colour contrast, smoothed: the underdrawing."""
    lab = cv2.cvtColor(cv2.GaussianBlur(rgb, (0, 0), 2), cv2.COLOR_RGB2LAB).astype(np.float32)
    edge = np.zeros(rid.shape, bool)
    edge[:, 1:] |= rid[:, 1:] != rid[:, :-1]; edge[1:, :] |= rid[1:, :] != rid[:-1, :]
    d = np.zeros(rid.shape, np.float32)                     # colour difference a few pixels across the border
    for dy, dx in ((0, 4), (4, 0)):
        a = lab[dy:, dx:] if dy or dx else lab
        diff = np.linalg.norm(lab[:lab.shape[0] - dy, :lab.shape[1] - dx] - a, axis=-1)
        d[:lab.shape[0] - dy, :lab.shape[1] - dx] = np.maximum(d[:lab.shape[0] - dy, :lab.shape[1] - dx], diff)
    edge &= cv2.GaussianBlur(d, (0, 0), 2) > min_contrast
    edge = cv2.dilate(edge.astype(np.uint8), np.ones((5, 5), np.uint8))
    edge = cv2.morphologyEx(edge, cv2.MORPH_CLOSE, np.ones((13, 13), np.uint8))     # bridge the dips: one continuous line
    return edge.astype(bool)


def picture_lines(rgb):
    """The picture's own dark, thin strokes (ink lines, pencil outlines) — not its big dark washes."""
    L = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB)[..., 0].astype(np.float32)
    local = cv2.GaussianBlur(L, (0, 0), 9)
    dark = (L < local - 18) & (L < 120)
    dark = cv2.morphologyEx(dark.astype(np.uint8), cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
    blobs = cv2.morphologyEx(dark, cv2.MORPH_OPEN, np.ones((13, 13), np.uint8))     # thick washes are not lines
    thin = (dark > 0) & ~(blobs > 0)
    n, lab_, st, _ = cv2.connectedComponentsWithStats(thin.astype(np.uint8), 8)
    keep = np.zeros(n, bool); keep[1:] = st[1:, cv2.CC_STAT_AREA] >= 40
    return keep[lab_]


def analyze(pic, out, lines_mode, k=14, preview=None):
    rgb = cv2.cvtColor(cv2.imread(pic), cv2.COLOR_BGR2RGB)
    rid, meta = colour_regions(rgb, k)
    main, sky = crayon.classify(rgb, rid, meta)
    for r in meta:                                          # a big area along the top is the background painted last
        x, y, w, h = r["bbox"]
        if r["role"] == "object" and r["area"] > 0.08 * rid.size and y <= 4: r["role"] = "sky"
    lines = sketch_lines(rgb, rid) if lines_mode == "sketch" else picture_lines(rgb)
    paths = crayon.skeleton_paths(lines, minlen=6)
    paths = [crayon.resample(cv2.approxPolyDP(p.reshape(-1, 1, 2), 1.2, False).reshape(-1, 2).astype(np.float32), 3.0)
             for p in paths if len(p) >= 2]
    if lines_mode == "sketch":                              # an underdrawing has no crumbs: only lines worth drawing
        paths = [p for p in paths if float(np.hypot(*np.diff(p, axis=0).T).sum()) >= 45]
    sk = skeletonize(lines); dist = cv2.distanceTransform(lines.astype(np.uint8), cv2.DIST_L2, 3)
    thick = float(np.median(dist[sk]) * 2) if sk.any() else 6.0
    zone = np.zeros(rid.shape, np.uint8)
    if main is not None:
        zone = cv2.dilate((rid == main["id"]).astype(np.uint8), np.ones((31, 31), np.uint8))
        filled = zone.copy(); cv2.floodFill(filled, None, (0, 0), 1); zone = zone | (1 - filled)
    on_star = [bool(zone[np.clip(p[:, 1].astype(int), 0, rid.shape[0] - 1), np.clip(p[:, 0].astype(int), 0, rid.shape[1] - 1)].mean() > 0.6)
               for p in paths]
    np.savez_compressed(out, lines=lines, rid=rid, thick=thick, paths=np.array(paths, dtype=object), on_star=np.array(on_star),
                        meta=json.dumps(meta), mode=lines_mode)
    print(f"{pic}: {len(meta)} regions (star={main and main['id']}, sky/background {[r['id'] for r in meta if r['role'] == 'sky']}, "
          f"little stars {sum(r['role'] == 'smallstar' for r in meta)}), {len(paths)} line paths ({sum(on_star)} on the star), "
          f"lines {lines.mean():.1%} of the picture, width {thick:.1f}")
    if preview:
        rng = np.random.default_rng(0); vis = np.zeros_like(rgb)
        for r in meta: vis[rid == r["id"]] = rng.integers(40, 230, 3) if r["role"] == "object" else {"sky": (40, 60, 200), "star": (250, 220, 0), "smallstar": (250, 140, 0)}[r["role"]]
        vis[lines] = (0, 0, 0)
        cv2.imwrite(preview, cv2.cvtColor(np.hstack([rgb, vis]), cv2.COLOR_RGB2BGR))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("picture"); ap.add_argument("out")
    ap.add_argument("--lines", choices=["sketch", "picture"], required=True); ap.add_argument("--k", type=int, default=14)
    ap.add_argument("--preview")
    g = ap.parse_args(); analyze(g.picture, g.out, g.lines, g.k, g.preview)
