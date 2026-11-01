"""crayon.py — a child draws one crayon picture in time with one variation of K. 265.

The picture (Codex, one style for all: thick black crayon outlines, flat crayon fills) is split into
  lines   dark, unsaturated pixels → skeleton → ordered paths (the main star's outline first);
  regions the rest, clustered by colour → connected pieces; the sky (largest blue piece) and the small stars kept apart.
The section's form drives the stages (every variation is A A B A' B A'):
  A    outline of the main star, one stroke per beat     A2  every other outline
  BA   colour the star and the objects, one scribble per beat
  BA2  the sky, then the small stars; drawn stars twinkle on the beats; the last beat finishes the picture.
A stroke starts on its beat and lasts most of it; between strokes the crayon lifts and glides (cubic Hermite, never
jumps), its shadow meeting the tip on contact. Held notes (no attack) lengthen the stroke before them.

    python crayon.py analyze PICTURE.png OUT.npz [--preview PREVIEW.png]
    python crayon.py plan    OUT.npz BEATS.json PLAN.json --start S --end E [--seed 1]
    python crayon.py render  PLAN.json PICTURE.png OUT.npz FRAMES_OUT.npy-or-dir ...   (used by film.py)
"""
import argparse, json, math
import numpy as np, cv2
from skimage.morphology import skeletonize

PAPER = np.array([243, 236, 220], np.float32)                   # cream drawing paper (RGB)
LINE_RGB = (38, 36, 40)


# ---------------------------------------------------------------- analysis
def line_mask(rgb):
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    v = hsv[..., 2].astype(np.int32); s = hsv[..., 1].astype(np.int32)
    m = ((v < 78) & (s < 110)) | (v < 45)
    m = m.astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(m, 8)
    keep = np.zeros(n, bool); keep[1:] = st[1:, cv2.CC_STAT_AREA] >= 60
    return keep[lab]


NB = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]


def skeleton_paths(mask, minlen=4):
    """Skeleton → list of polylines (x, y), split at junctions."""
    sk = skeletonize(mask).astype(np.uint8)
    H, W = sk.shape
    pad = np.pad(sk, 1)
    deg = sum(np.roll(np.roll(pad, dy, 0), dx, 1) for dy, dx in NB)[1:-1, 1:-1] * sk
    ys, xs = np.nonzero(sk)
    on = set(zip(ys.tolist(), xs.tolist()))
    visited_edges = set(); paths = []
    def nbrs(p):
        y, x = p
        return [(y + dy, x + dx) for dy, dx in NB if (y + dy, x + dx) in on]
    nodes = [p for p in on if deg[p] != 2]
    def walk(a, b):
        path = [a, b]; prev, cur = a, b
        while deg[cur] == 2:
            nx = [q for q in nbrs(cur) if q != prev]
            if not nx: break
            prev, cur = cur, nx[0]; path.append(cur)
            if cur == a: break
        return path
    for a in nodes:
        for b in nbrs(a):
            e = (a, b)
            if e in visited_edges: continue
            path = walk(a, b)
            visited_edges.add((path[0], path[1])); visited_edges.add((path[-1], path[-2]))
            for i in range(len(path) - 1): visited_edges.add((path[i], path[i + 1])); visited_edges.add((path[i + 1], path[i]))
            if len(path) >= minlen: paths.append(path)
    seen = set(p for path in paths for p in path)                       # closed loops with no junction (circles)
    for p in list(on):
        if p in seen or deg[p] != 2: continue
        nx = nbrs(p)
        if not nx: continue
        path = walk(p, nx[0]); seen.update(path)
        if len(path) >= minlen: paths.append(path)
    out = []
    for path in paths:
        pts = np.array([(x, y) for y, x in path], np.float32)
        keep = [0]
        for i in range(1, len(pts)):
            if np.hypot(*(pts[i] - pts[keep[-1]])) >= 3 or i == len(pts) - 1: keep.append(i)
        out.append(pts[keep])
    return out


def regions(rgb, lines, min_area=120):
    """A colouring book's areas: every piece of paper enclosed by the black outlines is one region.
    Pixels between a region and its outline (and specks too small to be a region) go to the nearest region."""
    wall = cv2.dilate(lines.astype(np.uint8), np.ones((3, 3), np.uint8))
    n, cc, st, cen = cv2.connectedComponentsWithStats((1 - wall).astype(np.uint8), 4)
    rid = np.full(lines.shape, -1, np.int32); meta = []
    for j in range(1, n):
        area = int(st[j, cv2.CC_STAT_AREA])
        if area < min_area: continue
        m = cc == j
        rid[m] = len(meta)
        col = np.median(rgb[m].reshape(-1, 3), 0)
        meta.append({"id": len(meta), "area": area, "color": [int(v) for v in col],
                     "bbox": [int(v) for v in st[j, :4]], "center": [float(v) for v in cen[j]]})
    # the leftovers (rims under the dilation, specks) join their nearest region, so filling a region covers them
    missing = (rid < 0) & ~lines
    if missing.any():
        _, idx = cv2.distanceTransformWithLabels((rid < 0).astype(np.uint8), cv2.DIST_L2, 3, labelType=cv2.DIST_LABEL_PIXEL)
        ys, xs = np.nonzero(rid >= 0)
        lut = np.zeros(idx.max() + 1, np.int32); lut[idx[ys, xs]] = rid[ys, xs]
        rid[missing] = lut[idx[missing]]
    return rid, meta


def classify(rgb, rid, meta):
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    for r in meta:
        m = rid == r["id"]
        h, s, v = [float(np.median(hsv[..., i][m])) for i in range(3)]
        r["hsv"] = [h, s, v]
        r["yellow"] = 18 <= h <= 36 and s > 90 and v > 150
        r["blue"] = 95 <= h <= 130 and s > 60 and v < 170
    blues = [r for r in meta if r["blue"]]
    sky = max(blues, key=lambda r: r["area"]) if blues else max(meta, key=lambda r: r["area"])
    def solidity(r):                                      # a five-pointed star is clearly concave (≈0.55–0.8)
        m = (rid == r["id"]).astype(np.uint8)
        cs, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not cs: return 1.0
        c = max(cs, key=cv2.contourArea); return r["area"] / max(cv2.contourArea(cv2.convexHull(c)), 1.0)
    yel = sorted([r for r in meta if r["yellow"]], key=lambda r: -r["area"])
    starry = [r for r in yel if r["area"] > 0.005 * rid.size and 20 <= r["hsv"][0] <= 33 and r["hsv"][1] > 150 and 0.45 <= solidity(r) <= 0.9]
    main = starry[0] if starry else (yel[0] if yel else None)
    total = rid.size
    skies = {r["id"] for r in meta if r is sky or (r["blue"] and r["area"] > 0.01 * total)}
    def in_sky(r):                                        # a little star sits in the sky (a lit window does not)
        x, y, w, h = r["bbox"]; pad = 24
        y0, y1, x0, x1 = max(0, y - pad), min(rid.shape[0], y + h + pad), max(0, x - pad), min(rid.shape[1], x + w + pad)
        m = (rid[y0:y1, x0:x1] == r["id"]).astype(np.uint8)
        ring = cv2.dilate(m, np.ones((31, 31), np.uint8)).astype(bool) & ~cv2.dilate(m, np.ones((13, 13), np.uint8)).astype(bool)
        around = rid[y0:y1, x0:x1][ring]; around = around[around >= 0]
        return len(around) > 0 and np.isin(around, list(skies)).mean() > 0.6
    for r in meta:
        r["role"] = "object"
        if r["id"] in skies: r["role"] = "sky"
        elif r is main: r["role"] = "star"
        elif r["yellow"] and r["area"] < 0.02 * total and in_sky(r): r["role"] = "smallstar"
    return main, sky


def analyze(pic_path, out_path, preview=None):
    bgr = cv2.imread(pic_path); rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    lines = line_mask(rgb)
    paths = skeleton_paths(lines)
    rid, meta = regions(rgb, lines)
    main, sky = classify(rgb, rid, meta)
    dist = cv2.distanceTransform(lines.astype(np.uint8), cv2.DIST_L2, 3)
    sk = skeletonize(lines)
    thick = float(np.median(dist[sk]) * 2) if sk.any() else 8.0
    star_zone = np.zeros(lines.shape, np.uint8)
    if main is not None:
        star_zone = cv2.dilate((rid == main["id"]).astype(np.uint8), np.ones((31, 31), np.uint8))
        filled = star_zone.copy(); cv2.floodFill(filled, None, (0, 0), 1)                # include the face inside
        star_zone = star_zone | (1 - filled)
    on_star = [bool(star_zone[np.clip(p[:, 1].astype(int), 0, rid.shape[0] - 1), np.clip(p[:, 0].astype(int), 0, rid.shape[1] - 1)].mean() > 0.6) for p in paths]
    np.savez_compressed(out_path, lines=lines, rid=rid, thick=thick,
                        paths=np.array([p for p in paths], dtype=object), on_star=np.array(on_star),
                        meta=json.dumps(meta))
    print(f"{pic_path}: {len(paths)} line paths ({sum(on_star)} on the star), line width {thick:.1f}px, "
          f"{len(meta)} regions: star={main and main['id']} sky={sky['id']} ({sky['area'] / rid.size:.0%}), "
          f"small stars {sum(r['role'] == 'smallstar' for r in meta)}, line px {lines.mean():.1%}")
    if preview:
        vis = rgb.copy() // 3 + 120
        rng = np.random.default_rng(0)
        for r in meta:
            col = {"sky": (40, 60, 200), "star": (250, 220, 0), "smallstar": (250, 150, 0)}.get(r["role"])
            vis[rid == r["id"]] = col if col else rng.integers(60, 230, 3)
        vis[lines] = (0, 0, 0)
        for p, s in zip(paths, on_star):
            cv2.polylines(vis, [p.astype(np.int32)], False, (255, 0, 0) if s else (0, 200, 0), 2)
        cv2.imwrite(preview, cv2.cvtColor(np.hstack([rgb, vis]), cv2.COLOR_RGB2BGR))


# ---------------------------------------------------------------- planning
def order_paths(paths, start=None):
    """Nearest-neighbour chain; each path may be drawn either way round."""
    left = list(range(len(paths))); out = []
    cur = np.array(start if start is not None else paths[left[0]][0], np.float32)
    while left:
        best = None
        for i in left:
            p = paths[i]
            for rev in (False, True):
                a = p[-1] if rev else p[0]
                d = float(np.hypot(*(a - cur)))
                if best is None or d < best[0]: best = (d, i, rev)
        _, i, rev = best; left.remove(i)
        p = paths[i][::-1] if rev else paths[i]
        out.append(p); cur = p[-1]
    return out


def split_by_length(paths, n):
    """Cut the ordered paths into n pieces of equal drawn length; a piece may hop between paths (a quick lift)."""
    segs = []                                             # (path index, cumulative lengths)
    total = 0.0
    for p in paths:
        d = np.r_[0, np.cumsum(np.hypot(*np.diff(p, axis=0).T))]
        segs.append(d); total += d[-1]
    target = np.linspace(0, total, n + 1)
    pieces = [[] for _ in range(n)]
    acc = 0.0
    for p, d in zip(paths, segs):
        for j in range(n):
            a, b = max(target[j] - acc, 0.0), min(target[j + 1] - acc, d[-1])
            if b <= a: continue
            inner = p[(d > a) & (d < b)]
            ia = (np.interp(a, d, p[:, 0]), np.interp(a, d, p[:, 1]))
            ib = (np.interp(b, d, p[:, 0]), np.interp(b, d, p[:, 1]))
            pieces[j].append(np.vstack([[ia], inner, [ib]]).astype(np.float32))
        acc += d[-1]
    return pieces, total


def scribble(mask, width, angle_deg, rng, gap=0.62):
    """A zig-zag over a region: parallel passes at the angle, joined end to end; clipped to the region's extent per pass."""
    ys, xs = np.nonzero(mask)
    if len(xs) == 0: return np.empty((0, 2), np.float32)
    th = math.radians(angle_deg)
    u = np.array([math.cos(th), math.sin(th)]); v = np.array([-u[1], u[0]])
    P = np.stack([xs, ys], 1).astype(np.float32)
    pu, pv = P @ u, P @ v
    step = width * gap
    rows = np.arange(pv.min() + step * 0.4, pv.max(), step)
    pts = []; flip = False
    for r in rows:
        sel = np.abs(pv - r) < step * 0.5
        if sel.sum() < 3: continue
        a, b = np.percentile(pu[sel], 1), np.percentile(pu[sel], 99)
        a -= width * 0.15; b += width * 0.15
        ends = [a, b] if not flip else [b, a]
        jit = rng.normal(0, width * 0.06, 2)
        for e, j in zip(ends, jit): pts.append(u * e + v * (r + j))
        flip = not flip
    return np.array(pts, np.float32)


def resample(pts, step):
    if len(pts) < 2: return pts
    d = np.r_[0, np.cumsum(np.hypot(*np.diff(pts, axis=0).T))]
    if d[-1] < 1e-3: return pts[:1]
    s = np.arange(0, d[-1], step); s = np.r_[s, d[-1]]
    return np.stack([np.interp(s, d, pts[:, 0]), np.interp(s, d, pts[:, 1])], 1).astype(np.float32)


VL, VF, VG = 1100.0, 2000.0, 2000.0       # px/s at picture scale: outlining, scribbling, gliding between strokes
DUTY = 0.86                                # a stroke lasts this share of its beat; the rest is the lift to the next


def split_by_weights(paths, weights, with_index=False):
    """Cut the ordered paths into pieces whose length (trips between paths included) follows the weights.
    with_index: pieces are (path index, points, air) where air = None for drawing, or (u0, u1, trip length) for the
    part of a trip in the air between path k and k+1 — so a trip cut by a beat keeps its time in both strokes."""
    segs, total = [], 0.0                                 # (kind, k, points, cumulative lengths, offset)
    for k, p in enumerate(paths):
        d = np.r_[0, np.cumsum(np.hypot(*np.diff(p, axis=0).T))]
        segs.append(("draw", k, p, d, total)); total += d[-1]
        if k + 1 < len(paths):
            q = np.array([p[-1], paths[k + 1][0]], np.float32); h = float(np.hypot(*(q[1] - q[0])))
            if h > 1.0: segs.append(("air", k, q, np.array([0.0, h]), total)); total += h
    w = np.asarray(weights, float); target = np.r_[0, np.cumsum(w / w.sum())] * total
    pieces = [[] for _ in w]
    for kind, k, p, d, off in segs:
        for j in range(len(w)):
            a, b = max(target[j] - off, 0.0), min(target[j + 1] - off, d[-1])
            if b <= a: continue
            inner = p[(d > a) & (d < b)]
            ia = (np.interp(a, d, p[:, 0]), np.interp(a, d, p[:, 1])); ib = (np.interp(b, d, p[:, 0]), np.interp(b, d, p[:, 1]))
            piece = np.vstack([[ia], inner, [ib]]).astype(np.float32)
            if kind == "draw": pieces[j].append((k, piece, None) if with_index else piece)
            elif with_index: pieces[j].append((k, piece, (a / d[-1], b / d[-1], float(d[-1]))))
    return pieces, total


def path_len(parts):
    L = sum(float(np.hypot(*np.diff(p, axis=0).T).sum()) for p in parts if len(p) > 1)
    return L + sum(float(np.hypot(*(parts[i + 1][0] - parts[i][-1]))) for i in range(len(parts) - 1))


def star_points(rid, meta):
    """Where the stars can twinkle: the little stars (and star-shaped yellow bits like a trail), plus the main star's tips."""
    pts, tips = [], []
    for r in meta:
        if not r.get("yellow") or r["role"] in ("sky",): continue
        m = (rid == r["id"]).astype(np.uint8)
        cs, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        if not cs: continue
        c = max(cs, key=cv2.contourArea); hull = cv2.contourArea(cv2.convexHull(c))
        solidity = r["area"] / max(hull, 1.0)
        if r["role"] == "star":
            P = c[:, 0, :].astype(np.float32); cen = np.array(r["center"], np.float32)
            ang = np.arctan2(P[:, 1] - cen[1], P[:, 0] - cen[0]); rad = np.hypot(*(P - cen).T)
            for k in range(5):                            # the farthest point in each fifth of the turn ≈ a tip
                a0 = -math.pi + k * 2 * math.pi / 5 + 0.3
                sel = ((ang - a0) % (2 * math.pi)) < 2 * math.pi / 5
                if sel.any(): j = np.argmax(np.where(sel, rad, -1)); tips.append([float(P[j, 0]), float(P[j, 1])])
        elif r["area"] < 0.02 * rid.size and (r["role"] == "smallstar" or (solidity < 0.75 and r["hsv"][1] > 180 and 23 <= r["hsv"][0] <= 30)):
            pts.append({"xy": r["center"], "size": float(math.sqrt(r["area"]) * 1.9)})
    tips.sort(key=lambda q: q[1])
    return pts, tips


def plan(npz_path, beats_path, out_path, start, end, seed=1, hold=3.6, wmul=1.0, split_at=None):
    A = np.load(npz_path, allow_pickle=True)
    rid = A["rid"]; meta = json.loads(str(A["meta"])); paths = list(A["paths"]); on_star = A["on_star"]
    thick = float(A["thick"]); H, W = rid.shape
    sketch = "mode" in A.files and str(A["mode"]) == "sketch"
    if sketch: thick = 2.4                                  # a pencil / thin-brush underdrawing (film.py draws it itself)
    rng = np.random.default_rng(seed)
    BJ = json.load(open(beats_path)); B = BJ["beats"]
    beats = [b for b in B if start - 0.05 <= b["t"] <= end]
    cadence = BJ.get("cadence", beats[-1]["t"])
    n = len(beats); span = beats[-1]["t"] - beats[0]["t"]
    attacks = [i for i, b in enumerate(beats) if b["attack"]]
    def phrase(k):                                        # start of the k-th 8-bar phrase, on a real note
        tt = beats[0]["t"] + span * k / 6
        return min(attacks, key=lambda i: abs(beats[i]["t"] - tt))
    # the drawing is done `hold` seconds before the last note (on a real note); the stars twinkle for the rest
    iend = min([i for i in attacks if i > n // 2], key=lambda i: abs(beats[i]["t"] - (cadence - hold)))
    hold_beats = beats[iend:]
    marks = []                                            # held beats lengthen the stroke before them
    for i, b in enumerate(beats[:iend]):
        if marks and not b["attack"]: marks[-1]["end_i"] = i; continue
        marks.append({"t": b["t"], "i": i, "loud": b["loud"], "end_i": i})
    tnext = lambda m: beats[m["end_i"] + 1]["t"] if m["end_i"] + 1 < n else m["t"] + 0.4
    dur = lambda m: DUTY * (tnext(m) - m["t"])

    # ---- the work: every outline (the main star's first), every area to colour
    plen = lambda p: float(np.hypot(*np.diff(p, axis=0).T).sum())
    small_zone = np.zeros(rid.shape, np.uint8)                # little stars are drawn whole (outline too) at the end
    for r in meta:
        if r["role"] == "smallstar": small_zone |= (rid == r["id"]).astype(np.uint8)
    small_zone = cv2.dilate(small_zone, np.ones((45, 45), np.uint8)).astype(bool)
    def in_small(p):
        q = p.astype(int); q[:, 0] = np.clip(q[:, 0], 0, W - 1); q[:, 1] = np.clip(q[:, 1], 0, H - 1)
        return small_zone[q[:, 1], q[:, 0]].mean() > 0.3
    star_paths = [p for p, s in zip(paths, on_star) if s]                     # the star's face is drawn, however small
    other_paths = [p for p, s in zip(paths, on_star) if not s and plen(p) >= 24 and not in_small(p)]   # specks appear when outlining ends
    top = None
    if star_paths:
        hi = min(star_paths, key=lambda p: p[:, 1].min()); top = hi[np.argmin(hi[:, 1])]
    ordered = order_paths(star_paths, top) if star_paths else []
    ordered += order_paths(other_paths, ordered[-1][-1] if ordered else None) if other_paths else []
    L_line = path_len(ordered)
    objects = sorted([r for r in meta if r["role"] in ("star", "object")], key=lambda r: (r["role"] != "star", -r["area"]))
    paperlike = lambda r: float(np.linalg.norm(np.array(r["color"], float) - PAPER)) < 28 and r["role"] != "star"
    tiny = [r["id"] for r in objects if r["area"] < 600 or paperlike(r)]   # specks and white clouds: no scribble needed
    objects = [r for r in objects if r["area"] >= 600 and not paperlike(r)]
    def chain(regs, start_xy):                            # nearest-neighbour order, so the crayon doesn't criss-cross
        left = list(regs); out = []; cur = np.array(start_xy, float)
        while left:
            r = min(left, key=lambda r: np.hypot(*(np.array(r["center"]) - cur))); left.remove(r); out.append(r); cur = np.array(r["center"])
        return out
    if objects: objects = objects[:1] + chain(objects[1:], objects[0]["center"])
    sky = sorted([r for r in meta if r["role"] == "sky"], key=lambda r: -r["area"])
    small = [r for r in meta if r["role"] == "smallstar"]
    wdef = lambda r: float(np.clip(math.sqrt(r["area"]) * 0.11, 16, 46)) * wmul    # a brush is wider than a pencil
    gapf = lambda r: 0.95 if r["area"] > 0.02 * rid.size else 0.62        # big areas: visible scribble, closed at the end
    _len = {}
    def need(r, k=1.0):                                   # the real scribble length at the default width (holes included)
        key = (r["id"], k)
        if key not in _len:
            zz = scribble(rid == r["id"], wdef(r) * k, 40.0, np.random.default_rng(0), gapf(r))
            _len[key] = path_len([zz]) if len(zz) >= 2 else 0.0
        return _len[key]
    T_line = L_line / VL; T_fill = sum(need(r) for r in objects) / VF + sum(need(r, 1.5) for r in sky) / VF + sum(need(r, 0.8) for r in small) / VF
    # outlines until the start of phrase 2 or 3 (beat 32 or 48), whichever matches the workload better
    def rush(i):                                          # how much faster than comfortable the busier stage must go
        tl = sum(dur(m) for m in marks if m["i"] < i); tf = sum(dur(m) for m in marks if m["i"] >= i)
        return max(T_line / max(tl, 1e-3), T_fill / max(tf, 1e-3))
    split = phrase(split_at) if split_at else min((phrase(1), phrase(2), phrase(3), phrase(4)), key=rush)   # up to 2/3
    line_ms = [m for m in marks if m["i"] < split]; fill_ms = [m for m in marks if m["i"] >= split]

    strokes = []
    pieces, _ = split_by_weights(ordered, [dur(m) for m in line_ms], with_index=True)
    for m, piece in zip(line_ms, pieces):
        if piece:
            strokes.append({"kind": "line", "t0": m["t"], "t1": m["t"] + dur(m), "loud": m["loud"], "color": LINE_RGB,
                            "parts": [(resample(pp, 2.0) if air is None else pp).tolist() for _, pp, air in piece],
                            "part_air": [air for _, _, air in piece], "width": thick / 2 + 3})
    pos = [np.array(strokes[-1]["parts"][-1][-1]) if strokes else np.array([W / 2, H / 2])]

    def zig(mask, w, gap=0.62):
        zz = scribble(mask, w, float(rng.uniform(15, 65) * rng.choice([-1, 1])), rng, gap)
        if len(zz) < 2: return None
        zz = resample(zz, 3.0)
        if np.hypot(*(zz[-1] - pos[0])) < np.hypot(*(zz[0] - pos[0])): zz = zz[::-1]   # start where the crayon is
        return zz

    # ---- colour: every area as one continuous scribble (objects → sky → little stars), cut into beats by length,
    # so small areas share a beat, big areas span several, and the crayon keeps an even pace
    small = chain(small, (objects[-1]["center"] if objects else (W / 2, H / 2)))
    seq = [(r, 1.0, 1) for r in objects] + [(r, 1.5, 7) for r in sky] + [(r, 0.8, 1) for r in small]
    T_avail = sum(dur(m) for m in fill_ms)
    big = {r["id"] for r, _, _ in seq if r["area"] > 0.02 * rid.size}
    L_small = sum(need(r, k) for r, k, _ in seq if r["id"] not in big); L_big = sum(need(r, k) for r, k, _ in seq if r["id"] in big)
    trips = sum(float(np.hypot(*(np.array(a["center"]) - np.array(b["center"])))) for (a, _, _), (b, _, _) in zip(seq[:-1], seq[1:]))
    budget = VF * T_avail - L_small - trips                # what is left for the big areas at a comfortable speed
    widen = float(np.clip(L_big / max(budget, 0.3 * L_big), 1.0, 3.5)) if L_big else 1.0
    parts, part_reg, part_w = [], [], []
    start_xy = np.array(pos[0], np.float32)                 # where the outlines ended: the trip to the first colour is timed
    parts.append(np.array([start_xy, start_xy + 0.01], np.float32)); part_reg.append(-1); part_w.append(0.0)
    for r, k, patches in seq:
        w = min(wdef(r) * k * (widen if r["id"] in big else 1.0), 260 if r["role"] == "sky" else 160)
        mask = rid == r["id"]; zs = []
        if patches > 1 and r["area"] > 0.08 * rid.size:      # a big sky goes in patch by patch
            ys, xs = np.nonzero(mask); pts = np.stack([xs, ys], 1).astype(np.float32)
            crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0); cv2.setRNGSeed(seed)
            _, _, cen = cv2.kmeans(pts[::7], patches, None, crit, 2, cv2.KMEANS_PP_CENTERS)
            lab = np.argmin(((pts[:, None, :] - cen[None]) ** 2).sum(-1), 1)
            order = [int(np.argmin(np.hypot(*(cen - pos[0]).T)))]
            while len(order) < patches:
                rest = [j for j in range(patches) if j not in order]
                order.append(min(rest, key=lambda j: np.hypot(*(cen[j] - cen[order[-1]]))))
            for j in order:
                pm = np.zeros_like(mask); pm[ys[lab == j], xs[lab == j]] = True
                zz = zig(pm, w, gapf(r))
                if zz is not None: zs.append(zz); pos[0] = zz[-1]
        else:
            zz = zig(mask, w, gapf(r))
            if zz is not None: zs.append(zz); pos[0] = zz[-1]
        for zz in zs: parts.append(zz); part_reg.append(r["id"]); part_w.append(w)
    settle_at, first_at = {}, {}
    if parts and fill_ms:
        pieces, _ = split_by_weights(parts, [dur(m) for m in fill_ms], with_index=True)
        regcol = {r["id"]: r["color"] for r, _, _ in seq}
        regcol[-1] = seq[0][0]["color"] if seq else list(LINE_RGB)   # the opening trip carries the first colour
        for m, piece in zip(fill_ms, pieces):
            if not piece: continue
            t0, t1 = m["t"], m["t"] + dur(m)
            regs = [part_reg[k] if air is None else -1 for k, _, air in piece]
            lens = {}
            for (k, pp, air) in piece:
                if air is None: lens[part_reg[k]] = lens.get(part_reg[k], 0) + float(np.hypot(*np.diff(pp, axis=0).T).sum())
            for r in regs:
                if r >= 0: settle_at[r] = t1; first_at.setdefault(r, (t0, t1))
            col = regcol[max(lens, key=lens.get)] if lens else regcol[part_reg[piece[0][0]]]
            strokes.append({"kind": "fill", "t0": t0, "t1": t1, "loud": m["loud"], "region": sorted({r for r in regs if r >= 0}),
                            "part_regions": regs, "part_widths": [part_w[k] if air is None else 0 for k, _, air in piece],
                            "part_air": [air for _, _, air in piece],
                            "color": col, "parts": [pp.tolist() for _, pp, _ in piece],
                            "width": float(np.mean([part_w[k] for k, _, _ in piece])), "settle": False})
    sky_ids = [r["id"] for r in sky]; small_ids = [r["id"] for r in small]
    sky_ms = [m for m in fill_ms if any(first_at.get(r, (1e9,))[0] <= m["t"] for r in sky_ids)]
    sm_t = min([first_at[r][0] for r in small_ids if r in first_at] or [end])
    sm_ms = [m for m in fill_ms if m["t"] >= sm_t]
    n_sm = len(sm_ms)

    # whatever trip is still short (outline pieces, the first colour) borrows from the stroke before
    strokes.sort(key=lambda s: s["t0"])
    for a, b in zip(strokes[:-1], strokes[1:]):
        d = float(np.hypot(*(np.array(b["parts"][0][0]) - np.array(a["parts"][-1][-1]))))
        needt = d / (VG * 1.5) + 0.05                      # a lifted swoop may go a little faster than drawing
        if b["t0"] - a["t1"] < needt:
            a["t1"] = max(a["t0"] + 0.75 * (a["t1"] - a["t0"]), b["t0"] - needt)

    twinkles = []
    for r in small:
        if r["id"] not in settle_at: continue
        after = [m for m in fill_ms if m["t"] > settle_at[r["id"]] + 0.05]
        if after: twinkles.append({"t": after[0]["t"], "xy": r["center"], "size": float(math.sqrt(r["area"]) * 1.9), "loud": after[0]["loud"]})
    # the finished picture: two stars twinkle on every beat, the big star sparkles on each bar, everyone on the last note
    pts, tips = star_points(rid, meta)
    order = list(rng.permutation(len(pts))) if pts else []
    k = 0
    for j, b in enumerate(hold_beats):
        if b["t"] >= cadence - 0.05: break
        if not b["attack"]: continue                      # only where a note really sounds
        for _ in range(min(2, len(order))):
            q = pts[order[k % len(order)]]; k += 1
            twinkles.append({"t": b["t"], "xy": q["xy"], "size": q["size"] * (0.9 + 0.3 * b["loud"]), "loud": b["loud"]})
        if j % 2 == 0 and tips:
            tip = tips[(j // 2) % len(tips)]
            twinkles.append({"t": b["t"], "xy": tip, "size": 60.0, "loud": 1.0})
    for q in pts:
        twinkles.append({"t": cadence, "xy": q["xy"], "size": q["size"] * 1.25, "loud": 1.0, "dur": 1.1})
    for tip in tips:
        twinkles.append({"t": cadence, "xy": tip, "size": 70.0, "loud": 1.0, "dur": 1.1})
    t_sky0 = min([first_at[r][0] for r in sky_ids if r in first_at] or [fill_ms[-1]["t"] if fill_ms else end])
    out = {"size": [W, H], "start": start, "end": end, "finish": beats[iend]["t"] - 0.35, "cadence": cadence,
           "hold": beats[iend]["t"], "strokes": strokes, "twinkles": twinkles,
           "settle_objects": {"t": t_sky0 - 0.3, "regions": [r["id"] for r in objects] + tiny},
           "deferred_lines": [r["id"] for r in meta if r["role"] == "smallstar"], "settle_at": {str(k): v for k, v in settle_at.items()},
           "stages": {"A": beats[0]["t"], "BA": fill_ms[0]["t"] if fill_ms else end, "BA2": t_sky0,
                      "stars": sm_t}}
    json.dump(out, open(out_path, "w"))
    sp = [path_len([np.array(p) for p in s["parts"]]) / max(s["t1"] - s["t0"], 1e-3) for s in strokes]
    gl = [float(np.hypot(*(np.array(b["parts"][0][0]) - np.array(a["parts"][-1][-1])))) / max(b["t0"] - a["t1"], 1e-3)
          for a, b in zip(strokes[:-1], strokes[1:])]
    lv = [path_len([np.array(p) for p in s_["parts"]]) / max(s_["t1"] - s_["t0"], 1e-3) for s_ in strokes if s_["kind"] == "line"]
    fv = [path_len([np.array(p) for p in s_["parts"]]) / max(s_["t1"] - s_["t0"], 1e-3) for s_ in strokes if s_["kind"] == "fill"]
    print(f"speeds: line p95 {np.percentile(lv, 95) if lv else 0:.0f} fill p95 {np.percentile(fv, 95) if fv else 0:.0f}")
    print(f"hold {beats[iend]['t']:.2f}→{cadence:.2f}s ({cadence - beats[iend]['t']:.1f}s, {len(hold_beats)} beats); ", end="")
    print(f"plan: {len(marks)} marks, outlines to beat {split} ({beats[split]['t']:.2f}s; need {T_line:.1f}s, colour {T_fill:.1f}s, rush {rush(split):.2f}) → "
          f"{sum(s['kind'] == 'line' for s in strokes)} line / {sum(s['kind'] == 'fill' for s in strokes)} fill strokes; "
          f"draw speed med {np.median(sp):.0f} p95 {np.percentile(sp, 95):.0f} max {max(sp):.0f}; glide p95 {np.percentile(gl, 95):.0f} max {max(gl):.0f} px/s")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("analyze"); a.add_argument("picture"); a.add_argument("out"); a.add_argument("--preview")
    p = sub.add_parser("plan"); p.add_argument("npz"); p.add_argument("beats"); p.add_argument("out")
    p.add_argument("--start", type=float, required=True); p.add_argument("--end", type=float, required=True)
    p.add_argument("--seed", type=int, default=1); p.add_argument("--hold", type=float, default=3.6); p.add_argument("--wmul", type=float, default=1.0); p.add_argument("--split", type=int, default=0)
    g = ap.parse_args()
    if g.cmd == "analyze": analyze(g.picture, g.out, g.preview)
    if g.cmd == "plan": plan(g.npz, g.beats, g.out, g.start, g.end, g.seed, g.hold, g.wmul, g.split or None)
