"""lazy_painter.py — a lazy painter paints a picture in a few big strokes, one stroke per musical gesture.

Advisor plan (Fable 5.1, 2026-10-17): no timelapse of thousands of dabs. A handful of large strokes, each starting
on a note and lasting the note (merged runs = one wiggling stroke, held notes = one lingering stroke):
  A "block-in" strokes lay the flat mean colour of the painting under their footprint;
  B strokes lay the real painting down through the bristles; small fast "dab" strokes fill gaps on a flurry;
  "touch" strokes after completion only brighten for a moment (the picture stays exactly the painting).
Strokes are planned for coverage (seed at the least covered point of the stroke's zone, travel along the painting's
own orientation, steer toward bare canvas and in the melody's direction), so coverage reaches 100 % on the last
stroke; a short settle during that stroke's ring removes the last bristle gaps.

    python lazy_painter.py plan   TARGET.png SCORE.json STROKES.json [--seed 3]
    python lazy_painter.py render TARGET.png STROKES.json OUTDIR --to SECONDS [--fps 30]

SCORE.json: {"zones": {name: area}, "strokes": [{"t": s, "end": s, "kind": "A|B|dab|touch", "zone": name,
             "dir": "up|down|flat|wiggle", "loud": 0..1}], "settle": [t0, t1]}
Areas use the living page's format (fractions of the picture): ["rect",x,y,w,h], ["circle",cx,cy,r], ["poly",[...]],
["multi",[...]]. Output frames are the picture only (the compositor puts them on the primed-canvas ground).
"""
import argparse, json, math, os
import numpy as np, cv2
from scipy.spatial import cKDTree

GROUND = np.array([236, 228, 212], np.float32) / 255          # primed linen (#ece4d4)
SPEED = {"A": (350, 500), "B": (600, 950), "dab": (1300, 1700), "touch": (500, 700)}     # px/s at 1536 wide
WIDTH = {"A": (320, 380), "B": (250, 290), "dab": (150, 185), "touch": (40, 60)}         # a broad, loaded brush
MINLEN = {"A": 820, "B": 700, "dab": 320, "touch": 250}      # a quick note is a quick sweep, not a short mark
OPACITY = {"A": 0.82, "B": 0.97, "dab": 0.96, "touch": 1.0}     # the block-in is a thin scumble


def area_mask(area, W, H):
    m = np.zeros((H, W), np.uint8)
    def draw(a):
        if a[0] == "multi": [draw(b) for b in a[1]]
        elif a[0] == "rect": cv2.rectangle(m, (int(a[1] * W), int(a[2] * H)), (int((a[1] + a[3]) * W), int((a[2] + a[4]) * H)), 1, -1)
        elif a[0] == "circle": cv2.circle(m, (int(a[1] * W), int(a[2] * H)), int(a[3] * W), 1, -1)
        elif a[0] == "poly": cv2.fillPoly(m, [np.array([[p[0] * W, p[1] * H] for p in a[1]], np.int32)], 1)
    draw(area); return m.astype(bool)


def orientation(img):
    g = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    g = cv2.GaussianBlur(g, (0, 0), 3)
    gx = cv2.Sobel(g, cv2.CV_32F, 1, 0, ksize=3); gy = cv2.Sobel(g, cv2.CV_32F, 0, 1, ksize=3)
    jxx = cv2.GaussianBlur(gx * gx, (0, 0), 12); jyy = cv2.GaussianBlur(gy * gy, (0, 0), 12); jxy = cv2.GaussianBlur(gx * gy, (0, 0), 12)
    return 0.5 * np.arctan2(2 * jxy, jxx - jyy) + np.pi / 2       # along the edges


def trace(seed_xy, length, step, theta, deficit, zone, want, rng, W, H):
    """Walk from the seed along the painting's orientation, steering toward bare canvas and the wanted direction."""
    x, y = seed_xy; pts = [(x, y)]; d = None; travelled = 0; k = 0
    while travelled < length and k < 2000:
        k += 1
        th = theta[int(y), int(x)]
        e = np.array([math.cos(th), math.sin(th)])
        if d is None:
            d = e if (want is None or np.dot(e, want) >= 0) else -e
        elif np.dot(e, d) < 0: e = -e
        # look ahead: which side has more bare canvas?
        r = int(step * 3)
        best = np.zeros(2)
        for ang in (-0.6, 0, 0.6):
            c, s = math.cos(ang), math.sin(ang); v = np.array([c * d[0] - s * d[1], s * d[0] + c * d[1]])
            px, py = int(np.clip(x + v[0] * r, 0, W - 1)), int(np.clip(y + v[1] * r, 0, H - 1))
            best += v * (deficit[py, px] + 0.25 * zone[py, px])
        nd = 0.45 * d + 0.25 * e + 0.6 * best
        if want is not None: nd += 0.25 * want
        if k % 9 == 0: nd += rng.normal(0, 0.15, 2)
        nd /= np.linalg.norm(nd) + 1e-9
        nx, ny = x + nd[0] * step, y + nd[1] * step
        if not (2 <= nx < W - 2): nd[0] = -nd[0]; nx = x + nd[0] * step
        if not (2 <= ny < H - 2): nd[1] = -nd[1]; ny = y + nd[1] * step
        x, y, d = float(np.clip(nx, 2, W - 3)), float(np.clip(ny, 2, H - 3)), nd
        pts.append((x, y)); travelled += step
    return np.array(pts, np.float32)


def smooth_path(pts, width):
    """Resample to ~width/5 spacing and smooth, so a stroke bends like a wrist, never in facets."""
    seg = np.linalg.norm(np.diff(pts, axis=0), axis=1); cum = np.concatenate([[0], np.cumsum(seg)])
    if cum[-1] < 1: return pts
    s = np.linspace(0, cum[-1], max(3, int(cum[-1] / max(2.0, width / 5))))
    P = np.stack([np.interp(s, cum, pts[:, 0]), np.interp(s, cum, pts[:, 1])], 1)
    k = max(1, int(len(P) * 0.06)) | 1
    for _ in range(3):
        Q = P.copy()
        for d in range(2): Q[:, d] = np.convolve(np.pad(P[:, d], k, mode="edge"), np.ones(2 * k + 1) / (2 * k + 1), mode="valid")
        P = Q
    return P.astype(np.float32)


def stroke_fields(pts, width, W, H, rng, wiggle=False):
    """Per-pixel alpha, arc length u and nearest path sample for a stroke: ragged soft body, round caps,
    irregular bristle streaks that break up where the brush runs dry and lifts off."""
    pts = smooth_path(pts, width)
    if wiggle:                                                    # a trill: the brush shakes sideways along its path
        seg = np.diff(pts, axis=0); n = np.stack([-seg[:, 1], seg[:, 0]], 1); n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-9
        cum = np.concatenate([[0], np.cumsum(np.linalg.norm(seg, axis=1))])[1:]
        pts = pts.copy(); pts[1:] += n * (np.sin(cum / (width * 0.9) * 2 * math.pi) * width * 0.16)[:, None]
    seg = np.linalg.norm(np.diff(pts, axis=0), axis=1); cum = np.concatenate([[0], np.cumsum(seg)]); L = float(cum[-1])
    s = np.linspace(0, L, max(2, int(L / 1.5)))
    P = np.stack([np.interp(s, cum, pts[:, 0]), np.interp(s, cum, pts[:, 1])], 1)
    T = np.gradient(P, axis=0); T /= np.linalg.norm(T, axis=1, keepdims=True) + 1e-9; N = np.stack([-T[:, 1], T[:, 0]], 1)
    half = width / 2
    x0, y0 = int(max(0, P[:, 0].min() - half - 6)), int(max(0, P[:, 1].min() - half - 6))
    x1, y1 = int(min(W, P[:, 0].max() + half + 6)), int(min(H, P[:, 1].max() + half + 6))
    yy, xx = np.mgrid[y0:y1, x0:x1]; Q = np.stack([xx.ravel(), yy.ravel()], 1).astype(np.float32)
    dist, idx = cKDTree(P).query(Q, distance_upper_bound=half * 1.4)
    ok = np.isfinite(dist); idx = np.where(ok, idx, 0)
    D = Q - P[idx]
    v = (D * N[idx]).sum(1); along = (D * T[idx]).sum(1)
    u = s[idx]
    # ragged edge (±12 %), slimmer at the ends; round caps beyond either end
    knots = np.convolve(rng.uniform(-1, 1, 40), np.hanning(7) / np.hanning(7).sum(), mode="same")
    rag = 1 + 0.22 * np.interp(u, np.linspace(0, L, 40), knots)          # smooth, irregular edge (about ±8 %)
    slim = 0.72 + 0.28 * np.clip(u / (half * 1.2), 0, 1) ** 0.6 * np.clip((L - u) / (half * 2.0), 0, 1) ** 0.5
    R = half * rag * slim
    cap = np.where((idx == 0) & (along < 0), along, np.where((idx == len(P) - 1) & (along > 0), along, 0))
    r = np.sqrt(v * v + cap * cap) / (R + 1e-6)
    edge = np.clip((1 - r) / 0.16, 0, 1); edge = edge * edge * (3 - 2 * edge)
    # bristles: an irregular profile across the brush, each bristle carrying paint a different distance
    nb = 64
    prof = np.convolve(rng.uniform(0.84, 1.0, nb + 4), [0.25, 0.5, 0.25], mode="same")[2:-2]
    reach = rng.uniform(0.86, 1.0, nb)                            # where along the stroke each bristle runs dry
    b = np.clip(((v / (R + 1e-6)) * 0.5 + 0.5) * (nb - 1), 0, nb - 1)
    bi = b.astype(int); bf = b - bi; bj = np.minimum(bi + 1, nb - 1)
    bristle = prof[bi] * (1 - bf) + prof[bj] * bf
    runout = reach[bi] * (1 - bf) + reach[bj] * bf
    dry = np.clip((runout - u / L) / 0.05 + 1, 0, 1)              # bristles drop out one by one near the end
    grain = np.interp(u, np.linspace(0, L, 90), rng.uniform(0.93, 1.0, 90))
    streak = grain * (0.96 + 0.04 * np.sin(u / (width * 0.11) + bi * 2.3))
    a = np.where(ok, edge * bristle * dry * streak, 0).astype(np.float32)
    h, w = y1 - y0, x1 - x0
    return dict(x0=x0, y0=y0, alpha=a.reshape(h, w), u=np.where(ok, u, 1e9).astype(np.float32).reshape(h, w),
                idx=idx.astype(np.int32).reshape(h, w), P=P, L=L,
                v=np.where(ok, v, 0).astype(np.float32).reshape(h, w), R=np.where(ok, R, 1).astype(np.float32).reshape(h, w))


def plan(target_path, score_path, out_path, seed=3, wscale=1.0, lscale=1.0):
    rng = np.random.default_rng(seed)
    img = cv2.cvtColor(cv2.imread(target_path), cv2.COLOR_BGR2RGB).astype(np.float32) / 255
    H, W = img.shape[:2]; scale = W / 1536
    theta = orientation(img)
    edges = cv2.GaussianBlur(np.abs(cv2.Laplacian(cv2.cvtColor(img, cv2.COLOR_RGB2GRAY), cv2.CV_32F)), (0, 0), 6)
    edges = edges / (edges.max() + 1e-9)
    score = json.load(open(score_path))
    zones = {k: area_mask(v, W, H) for k, v in score["zones"].items()}
    covA = np.zeros((H, W), np.float32); covB = np.zeros((H, W), np.float32)
    out = []; prev_end = None
    for i, s in enumerate(score["strokes"]):
        kind = s["kind"]; dur = s["end"] - s["t"]
        if kind == "touch":
            sp = rng.uniform(*SPEED[kind]) * scale
        else:
            sp = rng.uniform(*SPEED[kind]) * scale
        width = rng.uniform(*WIDTH[kind]) * scale * (0.85 + 0.3 * s.get("loud", 0.5)) * wscale   # an abbreviated painting = a bigger brush
        length = max(MINLEN[kind] * scale, sp * dur) * lscale
        cov = covA if kind == "A" else covB
        zone = zones.get(s.get("zone"), np.ones((H, W), bool)).astype(np.float32)
        deficit = cv2.GaussianBlur(np.clip(1 - cov, 0, 1), (0, 0), width * 0.5)
        weight = deficit * (0.25 + 0.75 * zone) * (0.7 + 0.6 * edges if kind != "A" else 1)
        if kind == "touch":
            weight = edges * zone + 1e-3
        want = {"up": np.array([0.15, -1.0]), "down": np.array([0.15, 1.0]), "flat": None, "wiggle": None}.get(s.get("dir"), None)
        if want is not None: want = want / np.linalg.norm(want)
        # try ~40 seeds among the neediest points, keep the path that covers the most bare canvas (scored at 1/4 size)
        q = 4; small = cv2.resize(weight, (W // q, H // q), interpolation=cv2.INTER_AREA)
        flat = small.ravel(); cand = list(rng.choice(np.argsort(flat)[::-1][:400], size=min(30, flat.size), replace=False))
        if prev_end is not None:                                  # the hand continues from where it lifted
            for _ in range(20):
                r = rng.uniform(0, (0.12 if kind == "dab" else 0.28) * W); a_ = rng.uniform(0, 2 * math.pi)
                px, py = np.clip(prev_end + r * np.array([math.cos(a_), math.sin(a_)]), [0, 0], [W - 1, H - 1])
                cand.append(int(py // q) * (W // q) + int(px // q))
        best, best_score = None, -1
        for c in cand:
            sy, sx = divmod(int(c), W // q)
            if sy >= H // q or sx >= W // q: continue
            p_try = trace((sx * q + q / 2, sy * q + q / 2), length, max(3, width * 0.22), theta, deficit, zone, want, rng, W, H)
            m = np.zeros((H // q, W // q), np.uint8)
            cv2.polylines(m, [(p_try / q * 8).astype(np.int32)], False, 1, thickness=max(1, int(width * 0.8 / q)), shift=3)
            gain = float((small * m).sum())
            d = np.linalg.norm(p_try[0] - prev_end) if prev_end is not None else 0
            cs = gain * math.exp(-d / ((0.12 if kind == "dab" else 0.5) * W))   # a flurry stays in one place
            if cs > best_score: best, best_score = p_try, cs
        pts = best; prev_end = pts[-1].copy()
        f = stroke_fields(pts, width, W, H, rng, wiggle=s.get("dir") == "wiggle")
        a = f["alpha"]; x0, y0 = f["x0"], f["y0"]; h, w = a.shape
        cov[y0:y0 + h, x0:x0 + w] = 1 - (1 - cov[y0:y0 + h, x0:x0 + w]) * (1 - a * OPACITY[kind])
        colour = None
        if kind == "A":
            wsum = a.sum() + 1e-6
            colour = (img[y0:y0 + h, x0:x0 + w] * a[..., None]).reshape(-1, 3).sum(0) / wsum
            colour = colour.tolist()
        out.append(dict(i=i, kind=kind, t=s["t"], end=s["end"], ring=s.get("ring", 0.35), pts=pts.round(1).tolist(),
                        width=round(float(width), 1), seed=int(rng.integers(1 << 30)), colour=colour,
                        wiggle=s.get("dir") == "wiggle"))
        print(f"{i:2d} {kind:5s} {s['t']:6.2f}-{s['end']:6.2f}  w {width:5.0f}  L {f['L']:6.0f}  covA {covA.mean()*100:5.1f}%  covB {covB.mean()*100:5.1f}%  bare {(covB<0.5).mean()*100:5.1f}%")
    for k, st in enumerate(out):                                  # the brush must lift and travel before the next note
        nxt = out[k + 1] if k + 1 < len(out) else None
        stop = st["end"] + st["ring"]
        if nxt is not None:
            d = float(np.linalg.norm(np.array(nxt["pts"][0]) - np.array(st["pts"][-1])))
            quick = st["kind"] == "dab" and nxt["kind"] == "dab"     # the harp flurry: quick flicks
            travel = float(np.clip(d / (2600 if quick else 1800), 0.07 if quick else 0.15, 0.7))
            shortest = 0.16 if st["kind"] == "dab" else 0.3
            stop = max(st["t"] + shortest, min(stop, nxt["t"] - travel))
            late = stop + travel - nxt["t"]
            if late > 0:                                          # no time to get there: that stroke starts a moment late
                nxt["t"] = round(nxt["t"] + late, 3); nxt["end"] = round(nxt["end"] + late, 3)
        st["stop"] = round(max(st["t"] + (0.16 if st["kind"] == "dab" else 0.3), stop), 3)
    json.dump(dict(size=[W, H], settle=score.get("settle"), strokes=out), open(out_path, "w"))


def ease(s):                                                     # starts at speed, lifts off slowly
    s = min(max(s, 0), 1); return 1 - (1 - s) ** 2.2


def render(target_path, strokes_path, outdir, t_to, fps=30, t_from=0.0):
    img = cv2.cvtColor(cv2.imread(target_path), cv2.COLOR_BGR2RGB).astype(np.float32) / 255
    H, W = img.shape[:2]
    data = json.load(open(strokes_path)); S = data["strokes"]
    rng = np.random.default_rng(11)
    canvas = np.ones_like(img) * GROUND                            # flat: the compositor lays one canvas weave over everything
    tones = cv2.GaussianBlur(img, (0, 0), 0.016 * W)              # what a loaded brush picks up: the local tone
    grey = tones.mean(2, keepdims=True); tones = np.clip(grey + (tones - grey) * 1.25, 0, 1)
    fields = {}
    def field(st):
        if st["i"] not in fields:
            fields[st["i"]] = stroke_fields(np.array(st["pts"], np.float32), st["width"], W, H, np.random.default_rng(st["seed"]), st["wiggle"])
        return fields[st["i"]]
    def lay(dst, st, U, wet):
        f = field(st); a = f["alpha"] * OPACITY[st["kind"]]; x0, y0 = f["x0"], f["y0"]; h, w = a.shape
        if st["kind"] == "touch":
            return
        if U >= f["L"]: drawn = (f["u"] <= U).astype(np.float32)
        else:                                                     # the moving front is the round tip of the brush
            d = np.clip(f["u"] - (U - f["R"]), 0, None)
            tip = np.sqrt(np.clip(f["R"] ** 2 - d * d, 0, None))
            drawn = np.clip((tip - np.abs(f["v"])) / (0.18 * f["R"] + 1e-6), 0, 1) * (f["u"] <= U)
        if wet:                                                   # the freshly passed paint is 6 % darker for ~0.4 s of travel
            behind = np.clip((U - f["u"]) / max(1.0, wet), 0, 1)
            shade = (0.94 + 0.06 * behind)[..., None]
        else: shade = 1.0
        a3 = (a * drawn)[..., None]
        reg = dst[y0:y0 + h, x0:x0 + w]
        if st["kind"] != "A": src = img[y0:y0 + h, x0:x0 + w]
        else:
            if "tone" not in f:                                   # local tone along the stroke (loaded brush), flat across it
                Pi = np.clip(f["P"].round().astype(int), 0, [W - 1, H - 1])
                tone = tones[Pi[:, 1], Pi[:, 0]]
                k = max(1, len(tone) // 12)
                tone = np.stack([np.convolve(np.pad(tone[:, c], k, mode="edge"), np.ones(2 * k + 1) / (2 * k + 1), mode="valid") for c in range(3)], 1)
                f["tone"] = tone.astype(np.float32)
            src = f["tone"][f["idx"]] * (0.97 + 0.06 * f["alpha"][..., None])
        reg[:] = reg * (1 - a3) + src * shade * a3
    order = sorted(S, key=lambda s: s["end"] + s["ring"])
    done = set(); os.makedirs(outdir, exist_ok=True)
    settle = data.get("settle")
    n0, n1 = int(t_from * fps), int(math.ceil(t_to * fps))
    for n in range(n1):
        t = n / fps
        for st in order:
            if st["i"] not in done and st["end"] + st["ring"] <= t:
                lay(canvas, st, 1e9, 0); done.add(st["i"])
        if n < n0: continue
        frame = canvas.copy()
        for st in S:
            if st["i"] in done or st["t"] > t: continue
            f = field(st)
            prog = ease((t - st["t"]) / (st["end"] + st["ring"] - st["t"]))
            U = prog * f["L"]
            if st["kind"] == "touch":                             # a passing glint: brighten along the path, then let go
                age = np.clip((U - f["u"]) / (0.6 * f["L"] / max(0.1, st["end"] - st["t"])), 0, 1)
                glow = (f["alpha"] * (f["u"] <= U) * (1 - age))[..., None] * 0.08
                x0, y0 = f["x0"], f["y0"]; h, w = f["alpha"].shape
                frame[y0:y0 + h, x0:x0 + w] = np.minimum(1, frame[y0:y0 + h, x0:x0 + w] * (1 + glow))
                continue
            lay(frame, st, U, wet=0.4 * f["L"] / max(0.1, st["end"] - st["t"]))
        if settle and t > settle[0]:
            k = min(1, (t - settle[0]) / (settle[1] - settle[0])); k = k * k * (3 - 2 * k)
            frame = frame * (1 - k) + img * k
            if k >= 1: canvas = img.copy()
        cv2.imwrite(os.path.join(outdir, f"{n:05d}.jpg"), cv2.cvtColor((frame * 255 + .5).clip(0, 255).astype(np.uint8), cv2.COLOR_RGB2BGR),
                    [cv2.IMWRITE_JPEG_QUALITY, 96])
    return n1 - n0


def render_oil(target_path, strokes_path, outdir, t_to, fps=30, relief=(33.6, 39.4)):
    """Paint with the simulated oil brush (oil_brush.py, Codex 2026-10-17): paint is laid as the brush passes, wet
    paint is picked up and dragged, thickness is lit. The block-in mixes more and runs dry sooner; the strokes that
    lay the real painting mix less so they stay true to it. After the settle the colours are exactly the painting;
    the relief of the paint stays through the wide shot and flattens during the camera push-in (`relief`)."""
    import oil_brush as ob
    img = cv2.cvtColor(cv2.imread(target_path), cv2.COLOR_BGR2RGB).astype(np.float32) / 255
    H, W = img.shape[:2]
    data = json.load(open(strokes_path)); S = data["strokes"]; settle = data.get("settle")
    tones = cv2.GaussianBlur(img, (0, 0), 0.016 * W); grey = tones.mean(2, keepdims=True); tones = np.clip(grey + (tones - grey) * 1.25, 0, 1)
    def sampler(src):
        def f(xs, ys):
            xi = np.clip(np.asarray(xs).astype(int), 0, W - 1); yi = np.clip(np.asarray(ys).astype(int), 0, H - 1)
            return src[yi, xi]
        return f
    from_tone, from_paint = sampler(tones), sampler(img)
    canvas = ob.OilCanvas(W, H, ground=tuple(GROUND.tolist()), seed=7)
    geoms, last = {}, {}
    for st in S:
        pts = smooth_path(np.array(st["pts"], np.float32), st["width"])
        if st["wiggle"]:
            seg = np.diff(pts, axis=0); n = np.stack([-seg[:, 1], seg[:, 0]], 1); n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-9
            cum = np.concatenate([[0], np.cumsum(np.linalg.norm(seg, axis=1))])[1:]
            pts = pts.copy(); pts[1:] += n * (np.sin(cum / (st["width"] * 0.9) * 2 * math.pi) * st["width"] * 0.16)[:, None]
        k = st["kind"]
        width = st["width"] if k != "touch" else st["width"] * 1.5
        geoms[st["i"]] = ob.stroke_geometry([tuple(p) for p in pts], width, st["seed"],
                                            depletion={"A": 0.85, "B": 0.55, "dab": 0.5, "touch": 0.6}[k],
                                            mixing={"A": 0.3, "B": 0.1, "dab": 0.12, "touch": 0.08}[k])
        last[st["i"]] = 0.0
    os.makedirs(outdir, exist_ok=True)
    N = int(math.ceil(t_to * fps))
    for n in range(N):
        t = n / fps
        canvas.dry(1 / fps)
        for st in S:
            if st["t"] > t or last[st["i"]] >= 1: continue
            prog = ease((t - st["t"]) / (st.get("stop", st["end"] + st["ring"]) - st["t"]))
            if prog > last[st["i"]]:
                ob.paint(canvas, geoms[st["i"]], last[st["i"]], prog, from_tone if st["kind"] == "A" else from_paint)
                last[st["i"]] = prog
        shaded = ob.shade(canvas)
        light = np.clip(shaded / (canvas.rgb + 1e-3), 0.55, 1.5)
        base = canvas.rgb
        if settle and t > settle[0]:
            k = min(1, (t - settle[0]) / (settle[1] - settle[0])); k = k * k * (3 - 2 * k)
            base = base * (1 - k) + img * k
        r = 1 - min(1, max(0, (t - relief[0]) / (relief[1] - relief[0]))); r = r * r * (3 - 2 * r)
        frame = np.clip(base * (1 + (light - 1) * r), 0, 1)
        cv2.imwrite(os.path.join(outdir, f"{n:05d}.jpg"), cv2.cvtColor((frame * 255 + .5).clip(0, 255).astype(np.uint8), cv2.COLOR_RGB2BGR),
                    [cv2.IMWRITE_JPEG_QUALITY, 96])
    return N


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("plan"); p.add_argument("target"); p.add_argument("score"); p.add_argument("out"); p.add_argument("--seed", type=int, default=3)
    p.add_argument("--wscale", type=float, default=1.0); p.add_argument("--lscale", type=float, default=1.0)
    r = sub.add_parser("render"); r.add_argument("target"); r.add_argument("strokes"); r.add_argument("outdir")
    r.add_argument("--to", type=float, required=True); r.add_argument("--from", dest="t_from", type=float, default=0); r.add_argument("--fps", type=int, default=30)
    o = sub.add_parser("oil"); o.add_argument("target"); o.add_argument("strokes"); o.add_argument("outdir")
    o.add_argument("--to", type=float, required=True); o.add_argument("--fps", type=int, default=30)
    o.add_argument("--relief", type=float, nargs=2, default=(33.6, 39.4), help="when the paint's relief flattens (the camera push-in)")
    a = ap.parse_args()
    if a.cmd == "plan": plan(a.target, a.score, a.out, a.seed, a.wscale, a.lscale)
    elif a.cmd == "oil": print(render_oil(a.target, a.strokes, a.outdir, a.to, a.fps, tuple(a.relief)), "frames")
    else: print(render(a.target, a.strokes, a.outdir, a.to, a.fps, a.t_from), "frames")
