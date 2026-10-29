"""film.py — the drawing film: sheets of paper on a desk, a crayon that draws each picture in time with K. 265.

    python film.py CONFIG.json OUT.mp4 [--from 0 --to 90.6] [--fps 30] [--preview 2]

CONFIG.json: {"desk": png, "crayon": png (white crayon on #FF00FF), "music": wav,
              "sections": [{"id", "picture", "npz", "plan", "start", "end"}], "fade_out": 1.0}
Film time = recording time. Each section's sheet slides in during the pause before its first beat; the crayon glides
on a cubic-Hermite path between strokes (never jumps), its shadow meeting the tip on contact and drifting away when it
lifts. Frames are piped straight into ffmpeg (no frame dumps).
"""
import argparse, json, math, subprocess
import numpy as np, cv2

W, H = 1920, 1080
SHEET_MARGIN = 34                          # cream paper around the drawing, in picture pixels
SHEET_SCALE = 0.835                        # sheet → frame
TOOL_LEN = 330                             # crayon length on screen (px)
PAPER = np.array([243, 236, 220], np.float32)


def smooth(u): u = np.clip(u, 0, 1); return u * u * (3 - 2 * u)


# ---------------------------------------------------------------- crayon sprite
def load_crayon(path, tool_len=None):
    bgr = cv2.imread(path); rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB).astype(np.float32)
    mag = np.array([255, 0, 255], np.float32)
    d = np.sqrt(((rgb - mag) ** 2).sum(-1))
    a = np.clip((d - 60) / 80, 0, 1)
    a = cv2.GaussianBlur(a, (0, 0), 1.0)
    rgb = np.where(a[..., None] > 0.01, rgb, 255)
    rgb[..., 1] = np.maximum(rgb[..., 1], (rgb[..., 0] + rgb[..., 2]) / 2 - 40)   # kill magenta fringe
    ys, xs = np.nonzero(a > 0.5)
    P = np.stack([xs, ys], 1).astype(np.float32); c = P.mean(0)
    u, s, vt = np.linalg.svd(P - c, full_matrices=False); axis = vt[0]
    if axis[0] > 0: axis = -axis                          # point toward the lower-left tip
    proj = (P - c) @ axis
    tip = P[np.argmax(proj)]; tail = P[np.argmin(proj)]
    length = float(np.hypot(*(tip - tail)))
    x0, y0, x1, y1 = xs.min() - 20, ys.min() - 20, xs.max() + 20, ys.max() + 20
    rgb = rgb[y0:y1, x0:x1]; a = a[y0:y1, x0:x1]; tip = tip - [x0, y0]
    k = (tool_len or TOOL_LEN) / length
    rgb = cv2.resize(rgb, None, fx=k, fy=k, interpolation=cv2.INTER_AREA); a = cv2.resize(a, None, fx=k, fy=k, interpolation=cv2.INTER_AREA)
    lum = rgb.mean(-1, keepdims=True) / 255.0
    yy, xx = np.mgrid[0:a.shape[0], 0:a.shape[1]].astype(np.float32)
    along = (xx - tip[0] * k) * -axis[0] + (yy - tip[1] * k) * -axis[1]          # distance from the tip toward the tail
    tipw = np.clip(1 - along / (0.2 * length * k), 0, 1)[..., None]              # where a brush carries its paint
    return {"rgb": rgb, "a": a, "lum": lum, "tip": tip * k, "tipw": tipw, "angle": math.degrees(math.atan2(axis[1], axis[0]))}


def draw_crayon(frame, cr, tip_xy, color, lift, sway_deg, scale_k, tint="body"):
    """Shadow first (pivoted about the tip, sliding away as it lifts), then the tool: a crayon or pencil takes its colour
    all over, a brush only on the tip it paints with."""
    col = np.array(color, np.float32) / 255.0
    if tint == "none":                                          # a black pen keeps its own colour
        body = cr["rgb"].copy()
    elif tint == "tip":
        wet = cr["rgb"] / 255.0 * 0.2 + col[None, None] * (0.45 + 0.4 * cr["lum"])
        body = np.clip((cr["rgb"] / 255.0 * (1 - cr["tipw"]) + wet * cr["tipw"]) * 255, 0, 255)
    else:
        body = cr["rgb"] / 255.0 * 0.25 + cr["lum"] * col[None, None] * 0.75
        wrapper_mix = np.clip((cr["lum"] - 0.55) * 2.2, 0, 1)                      # bright paper keeps some white
        body = body * (1 - 0.35 * wrapper_mix) + 0.35 * wrapper_mix * (0.55 + 0.45 * col)
        body = np.clip(body * 255, 0, 255)
    h, w = cr["a"].shape
    s = scale_k * (1 + 0.10 * lift)
    tx, ty = cr["tip"]
    def place(img, a, angle, off, blur):
        M = cv2.getRotationMatrix2D((float(tx), float(ty)), angle, s)
        M[0, 2] += tip_xy[0] - tx + off[0]; M[1, 2] += tip_xy[1] - ty + off[1]
        aw = cv2.warpAffine(a, M, (W, H), flags=cv2.INTER_LINEAR, borderValue=0)
        if blur > 0.3: aw = cv2.GaussianBlur(aw, (0, 0), blur)
        iw = cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderValue=0) if img is not None else None
        return aw, iw
    sh_a, _ = place(None, cr["a"], sway_deg - 7 - 10 * lift, (18 + 70 * lift, 14 + 55 * lift), 2.5 + 9 * lift)
    sh = sh_a * (0.42 - 0.18 * lift)
    frame *= (1 - sh[..., None])
    a, img = place(body, cr["a"], sway_deg, (0, -26 * lift), 0)
    frame[:] = frame * (1 - a[..., None]) + img * a[..., None]


# ---------------------------------------------------------------- one section
class Section:
    def __init__(self, cfg, rng):
        self.cfg = cfg
        bgr = cv2.imread(cfg["picture"]); self.pic = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB).astype(np.float32)
        A = np.load(cfg["npz"], allow_pickle=True)
        self.rid = A["rid"]; self.lines = A["lines"]
        self.bbox = self.region_boxes()
        self.ph, self.pw = self.rid.shape
        self.line_soft = cv2.GaussianBlur(cv2.dilate(self.lines.astype(np.uint8), np.ones((5, 5), np.uint8)).astype(np.float32), (0, 0), 1.0)
        P = json.load(open(cfg["plan"])); self.P = P
        self.medium = cfg.get("medium", "crayon")                 # crayon | pencil | watercolour | ink | oil
        self.mode = str(A["mode"]) if "mode" in A.files else "picture"   # sketch: the lines are our own underdrawing
        self.sketch_rgb = np.array(cfg.get("sketch_color", [96, 96, 104]), np.float32)
        L = cfg.get("lead_in", 0.0)                                 # silence before the music: shift every time
        if L:
            for k in ("start", "end", "finish", "cadence", "hold"):
                if k in P: P[k] += L
            for st in P["strokes"]: st["t0"] += L; st["t1"] += L
            for tw in P.get("twinkles", []): tw["t"] += L
            P["settle_at"] = {r: t + L for r, t in P.get("settle_at", {}).items()}
            if P.get("settle_objects"): P["settle_objects"]["t"] += L
            P["stages"] = {k: v + L for k, v in P["stages"].items()}
        self.wet = []                                               # (window, region, until): watercolour still spreading
        self.start, self.end, self.finish = P["start"], P["end"], P["finish"]
        self.strokes = sorted(P["strokes"], key=lambda s: s["t0"])
        for s in self.strokes:
            s["parts"] = [np.array(p, np.float32) for p in s["parts"] if len(p) >= 2]
            lens = [float(np.hypot(*np.diff(p, axis=0).T).sum()) for p in s["parts"]]
            hops = [float(np.hypot(*(s["parts"][i + 1][0] - s["parts"][i][-1]))) for i in range(len(s["parts"]) - 1)]
            s["lens"], s["hops"] = lens, hops
            s["total"] = sum(lens) + sum(hops)
            s["drawn"] = 0.0
            if s["kind"] == "fill":                       # the crayon takes the colour it lays down
                pts = np.vstack(s["parts"]).astype(int)
                pts[:, 0] = np.clip(pts[:, 0], 0, self.pw - 1); pts[:, 1] = np.clip(pts[:, 1], 0, self.ph - 1)
                s["regions"] = s["region"] if isinstance(s["region"], list) else [s["region"]]
                inreg = np.isin(self.rid[pts[:, 1], pts[:, 0]], s["regions"])
                samp = self.pic[pts[inreg, 1], pts[inreg, 0]] if inreg.any() else self.pic[pts[:, 1], pts[:, 0]]
                s["color"] = [float(v) for v in np.median(samp, 0)]
        noise = rng.random((self.ph // 3 + 1, self.pw // 3 + 1)).astype(np.float32)
        self.grain = cv2.resize(cv2.GaussianBlur(noise, (0, 0), 0.8), (self.pw, self.ph))[:self.ph, :self.pw]
        self.grain = 0.74 + 0.26 * (self.grain - self.grain.min()) / (np.ptp(self.grain) + 1e-6)
        self.pen = np.zeros((self.ph, self.pw), np.uint8)          # line strokes drawn so far
        self.acc = np.zeros((self.ph, self.pw), np.float32)       # crayon coverage of the fills
        self.settles = {}                                           # region id → time its last stroke ends
        for s in self.strokes:
            if s["kind"] == "fill" and s.get("settle"):
                for r in s["regions"]: self.settles[r] = max(self.settles.get(r, 0), s["t1"])
        for r, te in P.get("settle_at", {}).items(): self.settles[int(r)] = te          # each area closes after its last piece
        so = P.get("settle_objects")
        if so:                                                   # every object (and speck) is coloured by the sky
            for r in so["regions"]: self.settles[r] = min(self.settles.get(r, so["t"]), so["t"])
        self.region_px = {}
        pn = np.random.default_rng(5).random((self.ph, self.pw)).astype(np.float32)
        self.paper = PAPER[None, None] * (0.97 + 0.03 * cv2.GaussianBlur(pn, (0, 0), 1.2)[..., None])
        self.sheet = None
        self.tw = P.get("twinkles", [])
        # little stars: their outlines wait for their colouring stroke (the crayon draws the whole star then)
        self.deferred = np.zeros((self.ph, self.pw), np.float32); self.star_lines = []
        for r in P.get("deferred_lines", []):
            zone = cv2.dilate((self.rid == r).astype(np.uint8), np.ones((45, 45), np.uint8)).astype(bool)
            self.deferred[zone] = 1.0
            st = [s for s in self.strokes if s["kind"] == "fill" and r in s["regions"]]
            if st: self.star_lines.append((st[0]["t0"], st[0]["t1"], zone))

    # --- the crayon's path -------------------------------------------------------------------------------
    def stroke_point(self, s, dist):
        """Point at arc length `dist` along a stroke's parts and hops; also whether the tip touches the paper."""
        acc = 0.0; air = s.get("part_air") or [None] * len(s["parts"])
        for i, p in enumerate(s["parts"]):
            L = s["lens"][i]
            if dist <= acc + L or (i == len(s["parts"]) - 1):
                d = np.r_[0, np.cumsum(np.hypot(*np.diff(p, axis=0).T))]
                q = np.clip(dist - acc, 0, d[-1])
                x = np.interp(q, d, p[:, 0]); y = np.interp(q, d, p[:, 1])
                k = min(int(np.searchsorted(d, q)), len(p) - 1); k0 = max(0, k - 1)
                return np.array([x, y]), air[i] is None, p[k] - p[k0]
            acc += L
            hop = s["hops"][i]
            if dist <= acc + hop:
                u = (dist - acc) / max(hop, 1e-6)
                a, b = p[-1], s["parts"][i + 1][0]
                return a + (b - a) * u, False, b - a          # constant speed; the lift rises and falls with u
            acc += hop
        return s["parts"][-1][-1], True, np.array([1.0, 0.0])

    def hop_lift(self, s, dist):
        """The crayon's height: an arc over every trip (its parts may be split across strokes), none under 30 px."""
        acc = 0.0; air = s.get("part_air") or [None] * len(s["parts"])
        for i, L in enumerate(s["lens"]):
            if acc <= dist <= acc + L and air[i] is not None:
                u0, u1, full = air[i]
                if full < 30: return 0.0
                u = u0 + (u1 - u0) * (dist - acc) / max(L, 1e-6)
                return 0.4 * math.sin(math.pi * u) * min(1.0, full / 200)
            acc += L
            if i < len(s["hops"]):
                h = s["hops"][i]
                if acc <= dist <= acc + h and h >= 30:
                    return 0.4 * math.sin(math.pi * (dist - acc) / h) * min(1.0, h / 200)
                acc += h
        return 0.0

    def progress(self, s, t):
        u = np.clip((t - s["t0"]) / max(s["t1"] - s["t0"], 1e-3), 0, 1)
        return s["total"] * (0.15 * smooth(u) + 0.85 * u)

    def tool(self, t, rest):
        """(tip, lift, colour, drawing) of the crayon at time t, in picture coordinates."""
        S = self.strokes
        if not S or t < self.ready: return rest, 1.0, S[0]["color"] if S else (200, 200, 200), False
        for i, s in enumerate(S):
            if s["t0"] <= t <= s["t1"]:
                d = self.progress(s, t)
                p, touch, _ = self.stroke_point(s, d)
                return p, self.hop_lift(s, d), s["color"], touch
            if t < s["t0"]:
                prev = S[i - 1] if i > 0 else None
                a_t = prev["t1"] if prev else self.ready
                a_p = self.stroke_point(prev, prev["total"])[0] if prev else np.array(rest, np.float32)
                b_p = s["parts"][0][0]
                la = self.hop_lift(prev, prev["total"]) if prev else 1.0
                return self.glide(t, a_t, a_p, s["t0"], b_p, prev, s, la, self.hop_lift(s, 0.0))
        last = S[-1]; a_p = self.stroke_point(last, last["total"])[0]
        return self.glide(t, last["t1"], a_p, last["t1"] + 1.2, np.array(rest, np.float32), last, None)   # step aside

    def glide(self, t, ta, pa, tb, pb, sa, sb, la=0.0, lb=0.0):
        u = np.clip((t - ta) / max(tb - ta, 1e-3), 0, 1)
        dist = float(np.hypot(*(pb - pa)))
        va = self.end_tangent(sa) * min(dist, 260) * 0.6 if sa else np.zeros(2)
        vb = self.start_tangent(sb) * min(dist, 260) * 0.6 if sb else np.zeros(2)
        h00 = 2 * u ** 3 - 3 * u ** 2 + 1; h10 = u ** 3 - 2 * u ** 2 + u; h01 = -2 * u ** 3 + 3 * u ** 2; h11 = u ** 3 - u ** 2
        p = h00 * pa + h10 * va + h01 * pb + h11 * vb
        lift = math.sin(math.pi * u) * float(np.clip(dist / 260, 0.25, 1.0))
        if sb is None: lift = max(lift, smooth(u))
        if sa is None: lift = max(lift, 1 - smooth(u))
        lift = max(lift, la * (1 - u) + lb * u)
        ca = np.array(sa["color"] if sa else sb["color"], np.float32); cb = np.array(sb["color"] if sb else sa["color"], np.float32)
        col = ca + (cb - ca) * smooth((u - 0.2) / 0.5)
        return p, lift, col, False

    def end_tangent(self, s):
        p = s["parts"][-1]; v = p[-1] - p[max(0, len(p) - 4)]; n = np.hypot(*v); return v / n if n > 1e-3 else np.zeros(2)

    def start_tangent(self, s):
        p = s["parts"][0]; v = p[min(len(p) - 1, 3)] - p[0]; n = np.hypot(*v); return v / n if n > 1e-3 else np.zeros(2)

    # --- the picture at time t ----------------------------------------------------------------------------
    def advance(self, t):
        for s in self.strokes:
            if s["t0"] > t: break
            target = self.progress(s, t)
            if target <= s["drawn"] + 0.5: continue
            segs = self.segment(s, s["drawn"], target)
            s["drawn"] = target
            air = s.get("part_air") or [None] * len(s["parts"])
            for i, seg in segs:
                if air[i] is not None: continue                 # in the air: nothing is drawn
                if s["kind"] == "line": w = int(round(s["width"] * 2.0))
                else: w = int(round(s["part_widths"][i] if "part_widths" in s else s["width"]))
                pad = w + 3                                    # work only in the window the new marks touch
                x0 = int(max(0, seg[:, 0].min() - pad)); x1 = int(min(self.pw, seg[:, 0].max() + pad + 1))
                y0 = int(max(0, seg[:, 1].min() - pad)); y1 = int(min(self.ph, seg[:, 1].max() + pad + 1))
                if x1 <= x0 or y1 <= y0: continue
                off = np.array([x0, y0], np.float32)
                if s["kind"] == "line":
                    cv2.polylines(self.pen[y0:y1, x0:x1], [(seg - off).astype(np.int32)], False, 1, max(2, w), cv2.LINE_AA)
                else:
                    reg = s["part_regions"][i] if "part_regions" in s else None
                    inreg = (self.rid[y0:y1, x0:x1] == reg) if reg is not None else np.isin(self.rid[y0:y1, x0:x1], s["regions"])
                    acc = self.acc[y0:y1, x0:x1]; g = self.grain[y0:y1, x0:x1]
                    dep = self.deposit(seg - off, w, (y1 - y0, x1 - x0)) * inreg
                    acc[:] = 1 - (1 - acc) * (1 - dep * g)
                    if self.medium in ("watercolour", "ink"): self.wet.append(((y0, y1, x0, x1), reg, t + 0.9))

    def deposit(self, seg, w, shape):
        """How much colour one pass lays down, by medium (0..1 per pixel of the window)."""
        tmp = np.zeros(shape, np.float32)
        if self.medium == "oil":                                    # a loaded brush: parallel bristle streaks
            d = np.diff(seg, axis=0); n = np.stack([-d[:, 1], d[:, 0]], 1); n /= (np.linalg.norm(n, axis=1, keepdims=True) + 1e-6)
            n = np.vstack([n, n[-1:]]); rng = np.random.default_rng(int(seg[0, 0] * 7 + seg[0, 1]) % 99991)
            for o in np.linspace(-0.5, 0.5, 9):
                cv2.polylines(tmp, [(seg + n * o * w).astype(np.int32)], False, float(rng.uniform(0.55, 1.0)),
                              max(2, int(w / 7)), cv2.LINE_AA)
            return np.clip(tmp * 1.1, 0, 0.97)
        cv2.polylines(tmp, [seg.astype(np.int32)], False, 1.0, max(3, w), cv2.LINE_AA)
        if self.medium in ("watercolour", "ink"):                   # a soft, wet brush
            return np.clip(cv2.GaussianBlur(tmp, (0, 0), max(1.5, w / 5)) * 1.25, 0, 0.9)
        if self.medium == "pencil":                                 # light hatching that builds up
            return tmp * 0.62
        if self.medium == "gouache":                                # opaque, smooth-edged paint
            return np.clip(cv2.GaussianBlur(tmp, (0, 0), 1.4) * 1.05, 0, 0.96)
        if self.medium == "pastel":                                 # soft, powdery, rubbed in
            return np.clip(cv2.GaussianBlur(tmp, (0, 0), max(2.0, w / 6)), 0, 0.72)
        return tmp * 0.97

    def spread(self, t):
        """Watercolour keeps creeping outward for a moment after the brush passes (inside its area)."""
        keep = []
        for (y0, y1, x0, x1), reg, until in self.wet:
            if t > until: continue
            keep.append(((y0, y1, x0, x1), reg, until))
            pad = 6; y0, x0 = max(0, y0 - pad), max(0, x0 - pad); y1, x1 = min(self.ph, y1 + pad), min(self.pw, x1 + pad)
            acc = self.acc[y0:y1, x0:x1]
            inreg = self.rid[y0:y1, x0:x1] == reg if reg is not None else np.ones(acc.shape, bool)
            grown = cv2.GaussianBlur(acc, (0, 0), 2.2) * 1.12
            acc[inreg] = np.maximum(acc[inreg], np.minimum(grown[inreg], 1.0))
        self.wet = keep[-60:]

    def segment(self, s, d0, d1):
        """Drawn polylines between arc lengths d0 and d1, as (part index, points); hops are not drawn."""
        out = []; acc = 0.0
        for i, p in enumerate(s["parts"]):
            L = s["lens"][i]
            a, b = max(d0 - acc, 0), min(d1 - acc, L)
            if b > a:
                d = np.r_[0, np.cumsum(np.hypot(*np.diff(p, axis=0).T))]
                sel = p[(d > a) & (d < b)]
                pa = [np.interp(a, d, p[:, 0]), np.interp(a, d, p[:, 1])]; pb = [np.interp(b, d, p[:, 0]), np.interp(b, d, p[:, 1])]
                out.append((i, np.vstack([[pa], sel, [pb]])))
            acc += L + (s["hops"][i] if i < len(s["hops"]) else 0)
            if acc > d1: break
        return out

    def region_boxes(self):
        boxes = {}
        for r in np.unique(self.rid):
            if r < 0: continue
            ys, xs = np.nonzero(self.rid == r)
            boxes[int(r)] = (int(xs.min()), int(ys.min()), int(xs.max() - xs.min() + 1), int(ys.max() - ys.min() + 1))
        return boxes

    def region_mask(self, r):
        m = self.region_px.get(r)
        if m is None: m = self.region_px[r] = self.rid == r
        return m

    def picture(self, t):
        self.advance(t)
        a_line = np.minimum(1.0, cv2.GaussianBlur(self.pen.astype(np.float32), (0, 0), 1.2))
        if self.mode != "sketch": a_line = a_line * self.line_soft         # a sketch is exactly what the tool drew
        a_line = a_line * (1 - self.deferred) + a_line * self.deferred * (t > self.P["stages"].get("stars", 1e9))
        for r, te in list(self.settles.items()):                 # a region's last stroke smooths out its gaps
            if t <= te: continue
            v = float(smooth((t - te) / 0.45)); x, y, w, h = self.bbox[r]
            m = self.rid[y:y + h, x:x + w] == r; acc = self.acc[y:y + h, x:x + w]
            acc[m] = np.maximum(acc[m], v)
            if v >= 1: del self.settles[r]
        cov = self.acc
        if t > self.finish: cov = np.maximum(cov, smooth((t - self.finish) / 0.6))
        tba = self.P["stages"]["BA"] - 0.4                         # every outline (eye dots too) is done before colouring
        if t > tba and self.mode != "sketch": a_line = np.maximum(a_line, smooth((t - tba) / 0.4) * self.line_soft * (1 - self.deferred))
        for t0, t1, zone in self.star_lines:
            if t > t0: a_line[zone] = np.maximum(a_line[zone], float(smooth((t - t0) / max(t1 - t0, 0.05))) * self.line_soft[zone])
        if self.medium in ("watercolour", "ink"): self.spread(t)
        if self.mode == "sketch":                                   # our underdrawing first, the paint over it
            sk = (a_line * 0.8)[..., None]
            base = self.paper * (1 - sk) + self.sketch_rgb * sk
            c = cov[..., None]
            img = base * (1 - c) + self.pic * c
            if self.medium == "watercolour": img = img * (1 - 0.22 * a_line[..., None] * c) + self.sketch_rgb * 0.22 * a_line[..., None] * c
        else:
            alpha = np.maximum(a_line, cov)[..., None]
            img = self.paper * (1 - alpha) + self.pic * alpha
        for tw in self.tw:                                        # the drawn little stars twinkle on the beat
            dt = t - tw["t"]
            D = tw.get("dur", 0.7)
            if 0 <= dt < D: self.glint(img, tw["xy"], tw["size"] * (0.9 + 0.5 * tw["loud"]), math.sin(math.pi * dt / D))
        return img

    def glint(self, img, xy, size, k):
        x, y = int(xy[0]), int(xy[1]); r = int(size * 1.4)
        if r < 4: return
        y0, y1, x0, x1 = max(0, y - r), min(self.ph, y + r), max(0, x - r), min(self.pw, x + r)
        yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32); dx, dy = (xx - x) / size, (yy - y) / size
        ray = np.exp(-(dx ** 2) * 60) * np.exp(-np.abs(dy) * 2.2) + np.exp(-(dy ** 2) * 60) * np.exp(-np.abs(dx) * 2.2)
        glow = np.exp(-(dx ** 2 + dy ** 2) * 3.0)
        a = np.clip((ray * 0.9 + glow * 0.5) * k, 0, 1)[..., None]
        img[y0:y1, x0:x1] = img[y0:y1, x0:x1] * (1 - a) + np.array([255, 251, 225], np.float32) * a


# ---------------------------------------------------------------- the desk and the sheets
def sheet_matrix(pw, ph, angle, offset):
    sw, sh = pw + 2 * SHEET_MARGIN, ph + 2 * SHEET_MARGIN
    M = cv2.getRotationMatrix2D((sw / 2, sh / 2), angle, SHEET_SCALE)
    M[0, 2] += W / 2 - sw / 2 + offset[0]; M[1, 2] += H / 2 - sh / 2 + offset[1]
    return M, (sw, sh)


def to_frame(M, p):
    return np.array([M[0, 0] * (p[0] + SHEET_MARGIN) + M[0, 1] * (p[1] + SHEET_MARGIN) + M[0, 2],
                     M[1, 0] * (p[0] + SHEET_MARGIN) + M[1, 1] * (p[1] + SHEET_MARGIN) + M[1, 2]])


def put_sheet(frame, img, M, size, paper):
    sw, sh = size
    sheet = np.empty((sh, sw, 3), np.float32); sheet[:] = paper
    sheet[SHEET_MARGIN:SHEET_MARGIN + img.shape[0], SHEET_MARGIN:SHEET_MARGIN + img.shape[1]] = img
    a = np.ones((sh, sw), np.float32)
    Ms = M.copy(); Ms[0, 2] += 10; Ms[1, 2] += 14
    sha = cv2.GaussianBlur(cv2.warpAffine(a, Ms, (W, H), borderValue=0), (0, 0), 9) * 0.45
    frame *= (1 - sha[..., None])
    aw = cv2.warpAffine(a, M, (W, H), flags=cv2.INTER_LINEAR, borderValue=0)
    iw = cv2.warpAffine(sheet, M, (W, H), flags=cv2.INTER_AREA, borderValue=0)
    frame[:] = frame * (1 - aw[..., None]) + iw * aw[..., None]


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("config"); ap.add_argument("out")
    ap.add_argument("--from", dest="t0", type=float, default=0.0); ap.add_argument("--to", dest="t1", type=float, default=None)
    ap.add_argument("--fps", type=int, default=30); ap.add_argument("--preview", type=float, default=0, help="write a still every N s")
    g = ap.parse_args()
    C = json.load(open(g.config)); rng = np.random.default_rng(2)
    global W, H, SHEET_SCALE, TOOL_LEN                    # a vertical short sets its own frame, sheet and crayon size
    W, H = C.get("size", [W, H]); SHEET_SCALE = C.get("sheet_scale", SHEET_SCALE); TOOL_LEN = C.get("tool_len", TOOL_LEN)
    dimg = cv2.imread(C["desk"]); dh, dw = dimg.shape[:2]
    k = max(W / dw, H / dh); dimg = cv2.resize(dimg, (int(round(dw * k)), int(round(dh * k))), interpolation=cv2.INTER_CUBIC)
    x0 = int(C.get("desk_x", 0.5) * (dimg.shape[1] - W)); y0 = (dimg.shape[0] - H) // 2      # cover the frame, then crop
    desk = cv2.cvtColor(dimg[y0:y0 + H, x0:x0 + W], cv2.COLOR_BGR2RGB).astype(np.float32)
    cr = load_crayon(C["crayon"])
    for s in C["sections"]: s.setdefault("lead_in", C.get("lead_in", 0.0))
    secs = [Section(s, rng) for s in C["sections"]]
    for s in secs:                                              # each section draws with its own tool(s)
        t = s.cfg.get("tool")
        s.tool_sprite = load_crayon(t["png"], t.get("len")) if t else cr
        s.tint = t.get("tint", "body") if t else "body"
        tl = s.cfg.get("tool_lines")                                # e.g. a pencil for the sketch, then the brush
        s.line_sprite = load_crayon(tl["png"], tl.get("len")) if tl else None
        s.line_tint = tl.get("tint", "body") if tl else "body"
    poses = C.get("poses", [[-1.2, [0, 6]], [0.9, [-8, 4]]])
    REST = np.array(C.get("rest", [1765.0, 690.0]), float)        # the crayon's waiting place, beside the sheet
    for i, s in enumerate(secs):
        s.land = 0.2 if i == 0 else min(max(secs[i - 1].P.get("cadence", secs[i - 1].finish) + 0.25, s.start - C.get("approach", 1.6)), s.start - 1.6)   # after the last note
        s.ready = s.land + (0.8 if i == 0 else C.get("slide", 1.25))               # ...and has landed
    for i, s in enumerate(secs):
        s.leave = secs[i + 1].land if i + 1 < len(secs) else s.end
        M, _ = sheet_matrix(s.pw, s.ph, *poses[i % len(poses)])
        Mi = cv2.invertAffineTransform(M)
        s.rest = Mi[:, :2] @ REST + Mi[:, 2] - SHEET_MARGIN
    t1 = g.t1 if g.t1 is not None else secs[-1].end + 2
    ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(g.fps), "-i", "-",
                           "-ss", str(g.t0), "-t", str(t1 - g.t0), "-i", C["music"],
                           "-af", (f"adelay={int(C.get('lead_in', 0) * 1000)}:all=1," if C.get("lead_in") else "") + (C["audio_filter"] + "," if C.get("audio_filter") else "") + f"afade=t=out:st={t1 - g.t0 - C.get('fade_out', 1.0)}:d={C.get('fade_out', 1.0)},apad",
                           "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "256k",
                           "-shortest", g.out], stdin=subprocess.PIPE)
    n = int(round((t1 - g.t0) * g.fps)); next_still = 0.0
    for f in range(n):
        t = g.t0 + f / g.fps
        frame = desk.copy()
        k = max([i for i, s in enumerate(secs) if t >= s.land] or [0])
        # the previous sheet stays under the new one until the new one has landed
        for i in ([k - 1] if k > 0 else []) + [k]:
            s = secs[i]; ang, off = poses[i % len(poses)]
            M0, size = sheet_matrix(s.pw, s.ph, ang, off)
            u = smooth((t - s.land) / (s.ready - s.land)) if i == k else 1.0
            if u <= 0: continue
            if i == k - 1 and t > secs[k].ready: continue
            M = M0.copy(); M[0, 2] += (1 - u) * 1500; M[1, 2] += (1 - u) * 260
            put_sheet(frame, s.picture(t) if i == k else s.picture(min(t, s.end)), M, size, s.paper[0, 0])
        s = secs[k]; ang, off = poses[k % len(poses)]
        M, _ = sheet_matrix(s.pw, s.ph, ang, off)
        if k > 0 and t < s.ready:                               # sheet change: the crayon waits at the side
            tip, lift, col = secs[k - 1].rest, 1.0, secs[k - 1].strokes[-1]["color"]; Mt, _ = sheet_matrix(secs[k - 1].pw, secs[k - 1].ph, *poses[(k - 1) % len(poses)])
        else:
            tip, lift, col, drawing = s.tool(t, s.rest); Mt = M
        ftip = to_frame(Mt, tip)
        speed_sway = 4 * math.sin(t * 2.1)
        ts_ = secs[k - 1] if (k > 0 and t < s.ready) else s
        sketching = ts_.line_sprite is not None and t < ts_.P["stages"]["BA"] - 0.25
        spr, tnt = (ts_.line_sprite, ts_.line_tint) if sketching else (ts_.tool_sprite, ts_.tint)
        draw_crayon(frame, spr, ftip, col, float(lift), ang + speed_sway, 1.0, tnt)
        if C.get("outro"):                                      # after the music: hold the last picture, then the empty desk
            u = smooth((t - secs[-1].end - C["outro"][0]) / C["outro"][1])
            if u > 0: frame = frame * (1 - u) + desk * u
        ff.stdin.write(np.clip(frame, 0, 255).astype(np.uint8).tobytes())
        if g.preview and t >= next_still:
            cv2.imwrite(g.out.replace(".mp4", f"-{t:05.1f}.jpg"), cv2.cvtColor(np.clip(frame, 0, 255).astype(np.uint8), cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 85])
            next_still += g.preview
        if f % (g.fps * 10) == 0: print(f"t={t:6.1f}s", flush=True)
    ff.stdin.close(); ff.wait()
    print("wrote", g.out)


if __name__ == "__main__":
    main()
