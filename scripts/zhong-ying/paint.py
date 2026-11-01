"""The painting under the text: each work painted onto blank paper stroke by stroke, then alive.

    .venv-reframe/bin/python scripts/zhong-ying/paint.py climb-higher [--only <work id>] [--still <seconds> ...]

For every work of the film (timeline.json, build_timeline.py) this writes public/zhong-ying/<film>/paint-<work>.mp4,
the painting from the work's first frame to its last, 1230 × 820 at 30 fps:

* The Chinese reading paints the picture in. Its regions (paintings.py) start on their words; inside a region,
  strokes follow the picture's own forms (along its edges, stopping where the colour changes), coarse to fine,
  and start when the voice does: the stroke clock runs on the narration's loudness, so the brush moves with the
  syllables and rests in the pauses. A stroke uncovers the real picture through a brush-shaped, bristled,
  tapered mask; when a region's strokes are done, the last gaps settle in, so the finished picture is exactly
  the art lab's.
* The English reading adds living brushes: from the work's first English verse on, the picture under the mask
  is the art lab's own living page (living-<work>.mp4, captured by living.mjs).

--still writes PNG stills at those film seconds instead (for checking), and needs no living capture.
"""
from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys

import cv2
import numpy as np

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
from films import DATA, FPS, PUBLIC  # noqa: E402

PW, PH = 1230, 820
SETTLE = 0.6                     # a region's last gaps fill in over this long once its strokes are done


def art_lab():
    found = sorted(DATA.glob("art-lab-*/living.html"))
    if not found:
        raise SystemExit(f"export the art lab first: git -C lucas-visual-art-lab archive origin/main | tar -x -C {DATA}/art-lab-<sha>")
    return found[-1].parent


# ---------------------------------------------------------------------------------------------------- pictures

def picture(work_id: str) -> np.ndarray:
    """The picture at film size, float32 RGB 0..1: the living capture's own first frame when there is one."""
    base = PUBLIC_FILM / f"living-{work_id}.jpg"
    src = base if base.exists() else art_lab() / "assets/living" / f"{work_id}.jpg"
    img = cv2.cvtColor(cv2.imread(str(src)), cv2.COLOR_BGR2RGB)
    return cv2.resize(img, (PW, PH), interpolation=cv2.INTER_AREA).astype(np.float32) / 255


def blank_paper(pic: np.ndarray, style: str, rng) -> tuple[np.ndarray, np.ndarray]:
    """(blank, need): the empty paper or canvas, and where the picture differs from it (what strokes must uncover)."""
    if style == "oil":
        y, x = np.mgrid[0:PH, 0:PW].astype(np.float32)
        weave = 0.5 * (np.sin(x * math.tau / 3.4) * np.sin(y * math.tau / 3.4)) + cv2.GaussianBlur(rng.standard_normal((PH, PW)).astype(np.float32), (0, 0), 0.7)
        blank = np.array([0.935, 0.912, 0.862], np.float32) + weave[..., None] * 0.012
        return np.clip(blank, 0, 1), np.ones((PH, PW), np.float32)
    small = cv2.resize(pic, (PW // 4, PH // 4), interpolation=cv2.INTER_AREA)
    lab = cv2.cvtColor(small, cv2.COLOR_RGB2LAB)
    paper_l = np.percentile(lab[..., 0], 70)
    ink = (np.abs(lab[..., 0] - paper_l) > 3) | (np.hypot(lab[..., 1] - np.median(lab[..., 1]), lab[..., 2] - np.median(lab[..., 2])) > 3)
    ink = cv2.dilate(ink.astype(np.uint8), np.ones((5, 5), np.uint8))
    paper = cv2.inpaint((small * 255).astype(np.uint8), ink, 9, cv2.INPAINT_TELEA).astype(np.float32) / 255
    paper = cv2.GaussianBlur(cv2.resize(paper, (PW, PH), interpolation=cv2.INTER_CUBIC), (0, 0), 6)
    grain = cv2.GaussianBlur(rng.standard_normal((PH, PW)).astype(np.float32), (0, 0), 0.8)[..., None] * 0.006
    blank = np.clip(paper + grain, 0, 1)
    d = np.linalg.norm(cv2.cvtColor(pic, cv2.COLOR_RGB2LAB) - cv2.cvtColor(blank, cv2.COLOR_RGB2LAB), axis=2)
    need = np.clip((d - 2.5) / 6, 0, 1)
    return blank, cv2.GaussianBlur(need, (0, 0), 1.5)


def disc(radius: int) -> np.ndarray:
    return cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * radius + 1, 2 * radius + 1))


def rasterize(shape) -> np.ndarray:
    kind = shape[0]
    m = np.zeros((PH, PW), np.uint8)
    if kind == "rect":
        _, x, y, w, h = shape
        m[int(y * PH):int(math.ceil((y + h) * PH)), int(x * PW):int(math.ceil((x + w) * PW))] = 1
    elif kind == "circle":
        _, cx, cy, r = shape
        cv2.circle(m, (int(cx * PW), int(cy * PH)), int(r * PW), 1, -1)
    elif kind == "poly":
        cv2.fillPoly(m, [np.array([[x * PW, y * PH] for x, y in shape[1]], np.int32)], 1)
    elif kind == "or":
        for s in shape[1:]:
            m |= rasterize(s)
    elif kind == "and":
        m = np.ones((PH, PW), np.uint8)
        for s in shape[1:]:
            m &= rasterize(s)
    return m


def region_labels(regions, pic) -> np.ndarray:
    """Each pixel's region (index into regions, −1 = paper no region claims); earlier regions win."""
    labels = np.full((PH, PW), -1, np.int16)
    blur = cv2.GaussianBlur(pic, (0, 0), 2)
    for i, r in enumerate(regions):
        m = rasterize(r["shape"]).astype(bool)
        for ref in r.get("not_near", []):
            m &= np.linalg.norm(blur - np.array(ref, np.float32) / 255, axis=2) > 0.13
        labels[m & (labels < 0)] = i
    return labels


# ---------------------------------------------------------------------------------------------------- strokes

def flow_field(pic):
    """Unit vectors along the picture's forms (perpendicular to the luminance gradient) and how sure we are."""
    g = cv2.GaussianBlur(cv2.cvtColor(pic, cv2.COLOR_RGB2GRAY), (0, 0), 1.5)
    gx, gy = cv2.Sobel(g, cv2.CV_32F, 1, 0, ksize=5), cv2.Sobel(g, cv2.CV_32F, 0, 1, ksize=5)
    jxx, jyy, jxy = (cv2.GaussianBlur(a, (0, 0), 7) for a in (gx * gx, gy * gy, gx * gy))
    theta = 0.5 * np.arctan2(2 * jxy, jxx - jyy) + math.pi / 2
    tr = jxx + jyy + 1e-9
    coherence = np.sqrt((jxx - jyy) ** 2 + 4 * jxy ** 2) / tr
    strength = np.clip(tr / (np.percentile(tr, 90) + 1e-9), 0, 1)
    return np.cos(theta), np.sin(theta), np.clip(coherence * strength * 1.6, 0, 1)


def make_strokes(index, region, labels, need, lab, flow, rng) -> list[dict]:
    """Cover the region's pixels that need paint: big strokes first, then half-size ones for what is left."""
    fx, fy, conf = flow
    inside = labels == index
    todo = inside & (need > 0.12)
    if not todo.any():
        return []
    covered = np.zeros((PH, PW), np.uint8)
    strokes = []
    base_angle = rng.uniform(-0.12, 0.12)
    for scale in (1.0, 0.55) if region["r"] < 6 else (1.0, 0.55, 0.3):
        r = max(2.0, region["r"] * scale)
        step = r * 1.15
        ys, xs = np.nonzero(todo & (covered == 0))
        if len(ys) < 0.06 * todo.sum() and scale < 1:      # the settle fills the last few gaps
            break
        if not len(ys):
            break
        grid = {}
        for y, x in zip(ys, xs):
            key = (int(y // step), int(x // step))
            if key not in grid:
                grid[key] = (y, x)
        seeds = list(grid.values())
        # A painter works the region in rows, back and forth.
        seeds.sort(key=lambda p: (int(p[0] // (step * 3)), p[1] * (1 if int(p[0] // (step * 3)) % 2 == 0 else -1)))
        for y0, x0 in seeds:
            y0 = float(np.clip(y0 + rng.uniform(-0.3, 0.3) * step, 0, PH - 1))
            x0 = float(np.clip(x0 + rng.uniform(-0.3, 0.3) * step, 0, PW - 1))
            yi, xi = int(y0), int(x0)
            if covered[yi, xi] or not todo[yi, xi]:
                continue
            pts = trace(x0, y0, r, index, labels, lab, fx, fy, conf, base_angle, rng)
            cv2.polylines(covered, [np.array(pts, np.int32)], False, 1, max(1, int(r * 1.5)))
            strokes.append({"pts": np.array(pts, np.float32), "r": r, "seed": int(rng.integers(1 << 30))})
    return strokes


def trace(x, y, r, index, labels, lab, fx, fy, conf, base_angle, rng):
    start_color = lab[int(y), int(x)]
    max_len = r * rng.uniform(4, 8) if r > 6 else r * rng.uniform(3, 6)
    max_len = min(max_len, 260)
    tol = 22 if r > 6 else 14
    sign = 1 if rng.random() < 0.5 else -1
    dx, dy = None, None
    pts, length = [(x, y)], 0.0
    while length < max_len:
        xi, yi = int(np.clip(x, 0, PW - 1)), int(np.clip(y, 0, PH - 1))
        c = conf[yi, xi]
        vx = c * fx[yi, xi] + (1 - c) * math.cos(base_angle)
        vy = c * fy[yi, xi] + (1 - c) * math.sin(base_angle)
        n = math.hypot(vx, vy) or 1
        vx, vy = vx / n, vy / n
        if dx is None:
            vx, vy = vx * sign, vy * sign
        elif vx * dx + vy * dy < 0:
            vx, vy = -vx, -vy
        if dx is not None and vx * dx + vy * dy < 0.5:      # don't fold back on itself
            break
        dx, dy = vx, vy
        s = max(1.5, r * 0.6)
        x, y = x + dx * s, y + dy * s
        xi, yi = int(x), int(y)
        if not (0 <= xi < PW and 0 <= yi < PH) or labels[yi, xi] != index:
            break
        if np.linalg.norm(lab[yi, xi] - start_color) > tol:
            break
        pts.append((x, y))
        length += s
    if len(pts) == 1:
        pts.append((x + math.cos(base_angle) * r * 0.8, y + math.sin(base_angle) * r * 0.8))
    return pts


def smooth_noise(n, rng, scale):
    """A 1-D smooth random curve sampled at n points (values about 0..1)."""
    k = max(2, int(n / scale) + 2)
    knots = rng.random(k)
    return np.interp(np.linspace(0, k - 1, n), np.arange(k), knots)


def stroke_mask(stroke, style):
    """The stroke's full alpha in its bounding box, and each pixel's distance along it (for drawing it on)."""
    pts, r = stroke["pts"], stroke["r"]
    rng = np.random.default_rng(stroke["seed"])
    pad = r * 1.4 + 2
    x0, y0 = int(max(0, pts[:, 0].min() - pad)), int(max(0, pts[:, 1].min() - pad))
    x1, y1 = int(min(PW, pts[:, 0].max() + pad + 1)), int(min(PH, pts[:, 1].max() + pad + 1))
    if x1 <= x0 or y1 <= y0:
        return None
    yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    best_d = np.full(xx.shape, 1e9, np.float32)
    best_s = np.zeros(xx.shape, np.float32)
    best_u = np.zeros(xx.shape, np.float32)
    seg_len = np.hypot(*(pts[1:] - pts[:-1]).T)
    cum = np.concatenate([[0], np.cumsum(seg_len)])
    total = max(cum[-1], 1e-3)
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]
        ab = b - a
        l2 = float(ab @ ab) or 1e-6
        t = np.clip(((xx - a[0]) * ab[0] + (yy - a[1]) * ab[1]) / l2, 0, 1)
        px, py = a[0] + t * ab[0], a[1] + t * ab[1]
        d = np.hypot(xx - px, yy - py)
        closer = d < best_d
        best_d[closer] = d[closer]
        best_s[closer] = (cum[i] + t * seg_len[i])[closer]
        cross = ab[0] * (yy - a[1]) - ab[1] * (xx - a[0])
        best_u[closer] = np.sign(cross)[closer] * d[closer]
    s = best_s / total
    # Width: pressed on, lifted off, a little uneven.
    taper = np.clip(np.minimum(s / 0.14, (1 - s) / 0.22), 0, 1) ** 0.6 * 0.75 + 0.25
    width = r * taper * (0.9 + 0.2 * np.interp(s, np.linspace(0, 1, 9), rng.random(9)))
    u = best_u / np.maximum(width, 0.5)
    edge_noise = np.interp(s * 6 + (u > 0) * 3, np.arange(10), rng.random(10)) * 0.25
    soft_from = 0.55 if style != "oil" else 0.8
    edge = 1 - np.clip((np.abs(u) - soft_from + edge_noise * 0.4) / (1.05 - soft_from), 0, 1)
    # Bristles: streaks along the stroke, fainter as the brush runs dry at the end.
    bristle_n = smooth_noise(64, rng, 2.2)
    bristle = np.interp((u + 1.2) / 2.4 * 63, np.arange(64), bristle_n)
    if style == "oil":
        bristle = 0.55 + 0.45 * bristle
    else:
        bristle = 0.7 + 0.3 * bristle
    dry = 1 - np.clip((s - 0.72) / 0.28, 0, 1) * (bristle < 0.8) * 0.7
    alpha = np.clip(edge * bristle * dry * (1.0 if style == "oil" else 0.9), 0, 1).astype(np.float32)
    alpha[best_d > r * 1.3] = 0
    return {"box": (x0, y0, x1, y1), "alpha": alpha, "s": (best_s).astype(np.float32), "len": total}


# ---------------------------------------------------------------------------------------------------- timing

def loudness_clock(narration_wav, duration):
    """Cumulative 'ink' at every film frame: it grows while someone speaks and barely while no one does."""
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(narration_wav), "-ac", "1", "-ar", "12000", "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    x = np.abs(np.frombuffer(raw, np.float32))
    per = 12000 // FPS
    n = int(duration * FPS) + 2
    env = np.array([x[i * per:(i + 1) * per].mean() if i * per < len(x) else 0 for i in range(n)], np.float32)
    env = np.convolve(env, np.ones(3) / 3, "same")
    env = env / (env.max() or 1) + 0.12
    return np.concatenate([[0], np.cumsum(env)])


def schedule(strokes, start, end, clock, rng):
    """Spread the strokes over [start, end] on the loudness clock; each takes time in proportion to its length."""
    if not strokes:
        return
    lens = np.array([s["mask"]["len"] for s in strokes])
    durs = np.clip(lens / np.where(np.array([s["r"] for s in strokes]) > 6, 900, 320), 0.12, 0.55)
    last = max(start + 0.05, end - durs[-1])
    ca, cb = np.interp([start * FPS, last * FPS], np.arange(len(clock)), clock)
    marks = np.linspace(ca, cb, len(strokes) + 1)[:-1] + (cb - ca) / max(1, len(strokes)) * rng.uniform(0, 0.6, len(strokes))
    times = np.interp(marks, clock, np.arange(len(clock))) / FPS
    for s, t0, d in zip(strokes, np.sort(times), durs):
        s["t0"], s["t1"] = float(t0), float(t0 + d)


# ---------------------------------------------------------------------------------------------------- the work

class Work:
    """One work's painting. Two layers, so nothing shows its shape before its word: regions marked `over` (an
    object on top of something: a boat, a child, a river through a field) are first covered by the paint around
    them (the picture with the object inpainted away), and painted themselves, on top, when their word comes."""

    FILL_SIGMA = 4.0             # one blur for every region's settling, so together they add up to exactly 1
    HOLE = 15                    # px around an object that its underpainting replaces (and its settle restores)

    def __init__(self, film_tl, work, seed=7):
        from scipy import ndimage

        self.work = work
        rng = np.random.default_rng(seed)
        self.pic = picture(work["id"])
        self.blank, need = blank_paper(self.pic, work["style"], rng)
        regions = work["regions"]
        labels = region_labels(regions, self.pic)
        over = np.array([bool(r.get("over")) for r in regions] + [False])        # [-1] = paper
        is_over = over[labels]
        under_labels = labels
        self.under = self.pic
        hole = is_over.astype(np.uint8)
        if is_over.any():
            nearest = ndimage.distance_transform_edt(is_over, return_distances=False, return_indices=True)
            under_labels = labels[nearest[0], nearest[1]]
            hole = cv2.dilate(is_over.astype(np.uint8), disc(self.HOLE))   # objects' soft edges too
            self.under = cv2.inpaint((self.pic * 255).astype(np.uint8), hole, 9, cv2.INPAINT_TELEA).astype(np.float32) / 255
            if work["style"] != "oil":   # on paper, what lies under an object's bare-paper side is just paper
                bare = cv2.GaussianBlur(((hole > 0) & (under_labels < 0)).astype(np.float32), (0, 0), 3)[..., None]
                self.under = self.under * (1 - bare) + self.blank * bare
            if work["style"] == "oil":   # an inpainted patch is smooth; give it the canvas's own brushwork from beside it
                detail = self.pic - cv2.GaussianBlur(self.pic, (0, 0), 5)
                texture, todo = np.zeros_like(detail), hole.astype(bool)
                for shift in (140, -140, 280, -280, 420, -420):       # from beside the hole, never from another hole
                    ok = todo & ~np.roll(hole.astype(bool), shift, axis=1)
                    texture[ok] = np.roll(detail, shift, axis=1)[ok]
                    todo &= ~ok
                h = cv2.GaussianBlur(hole.astype(np.float32), (0, 0), 3)[..., None]
                self.under = np.clip(self.under + texture * h, 0, 1)
        self.over_soft = cv2.GaussianBlur((hole if is_over.any() else is_over).astype(np.float32), (0, 0), 2)[..., None]
        need_under = need if work["style"] == "oil" else blank_paper(self.under, work["style"], rng)[1]
        lab, lab_under = cv2.cvtColor(self.pic, cv2.COLOR_RGB2LAB), cv2.cvtColor(self.under, cv2.COLOR_RGB2LAB)
        flow, flow_under = flow_field(self.pic), flow_field(self.under)
        clock = loudness_clock(PUBLIC_FILM / "narration.wav", film_tl["durationSeconds"])
        self.strokes = {"under": [], "over": []}
        self.fills = {"under": [], "over": []}
        soft = lambda m: cv2.GaussianBlur(m.astype(np.float32), (0, 0), self.FILL_SIGMA)  # noqa: E731
        self.fills["under"].append((soft(under_labels < 0), work["paint_from"] - 0.4, None))   # bare paper first
        for i, region in enumerate(regions):
            layer = "over" if over[i] else "under"
            lab_i, need_i, flow_i = (lab, need, flow) if over[i] else (lab_under, need_under, flow_under)
            own = labels if over[i] else under_labels
            strokes = make_strokes(i, region, own, need_i, lab_i, flow_i, rng)
            # A stroke may run a little past its region's edge, never over a region still to come.
            grow = 1 if region.get("not_near") else max(1, int(region["r"] * 0.35))   # a colour-masked region keeps to its colours
            reach = cv2.dilate((own == i).astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * grow + 1, 2 * grow + 1)))
            reach = np.clip(cv2.GaussianBlur(reach.astype(np.float32), (0, 0), max(1.0, grow * 0.6)) * 1.6, 0, 1)
            for st in strokes:
                st["mask"] = stroke_mask(st, work["style"])
                if st["mask"] is not None:
                    x0, y0, x1, y1 = st["mask"]["box"]
                    st["mask"]["alpha"] *= reach[y0:y1, x0:x1]
            strokes = [st for st in strokes if st["mask"] is not None]
            schedule(strokes, region["start"], region["end"], clock, rng)
            self.strokes[layer] += strokes
            done = max([st["t1"] for st in strokes], default=region["start"])
            if over[i]:   # the object itself, and its margin: settled back to the picture only where the paint around is
                margin = cv2.GaussianBlur(cv2.dilate((own == i).astype(np.uint8), disc(self.HOLE + 8)).astype(np.float32), (0, 0), 3)
                self.fills[layer].append((soft(own == i), done, margin))
            else:
                self.fills[layer].append((soft(own == i), done, None))
            print(f"  {work['id']}/{region['name']}{' (over)' if over[i] else ''}: {len(strokes)} strokes, "
                  f"{region['start']:.2f}–{region['end']:.2f}s")
        self.layers = {}
        for layer in ("under", "over"):
            self.strokes[layer].sort(key=lambda st: st["t0"])
            self.layers[layer] = {"done": np.zeros((PH, PW), np.float32), "next": 0, "active": []}
        self.t = -1e9

    def _mask(self, layer, t):
        state, strokes = self.layers[layer], self.strokes[layer]
        while state["next"] < len(strokes) and strokes[state["next"]]["t0"] <= t:
            state["active"].append(strokes[state["next"]])
            state["next"] += 1
        done = state["done"]
        m = done.copy()
        still = []
        for st in state["active"]:
            mk = st["mask"]
            x0, y0, x1, y1 = mk["box"]
            p = (t - st["t0"]) / (st["t1"] - st["t0"])
            if p >= 1:
                a = mk["alpha"]
                done[y0:y1, x0:x1] = 1 - (1 - done[y0:y1, x0:x1]) * (1 - a)
                m[y0:y1, x0:x1] = 1 - (1 - m[y0:y1, x0:x1]) * (1 - a)
                continue
            head = mk["len"] * (1 - (1 - p) ** 2)
            a = mk["alpha"] * np.clip((head - mk["s"]) / (st["r"] * 0.6) + 0.5, 0, 1)
            m[y0:y1, x0:x1] = 1 - (1 - m[y0:y1, x0:x1]) * (1 - a)
            still.append(st)
        state["active"] = still
        fill = np.zeros((PH, PW), np.float32)
        margin = np.zeros((PH, PW), np.float32)
        for soft, at, edge in self.fills[layer]:
            k = (t - at) / SETTLE
            if k > 0:
                k = min(1.0, k)
                fill += soft * (k * k * (3 - 2 * k))
                if edge is not None:
                    np.maximum(margin, edge * (k * k * (3 - 2 * k)), out=margin)
        return 1 - (1 - m) * (1 - np.clip(fill, 0, 1)), margin

    def frame(self, t, living=None):
        """The painting at film time t (call with increasing t). `living` is the art lab's living frame."""
        assert t >= self.t
        self.t = t
        top = self.pic if living is None else living
        under = top * (1 - self.over_soft) + self.under * self.over_soft
        mu = self._mask("under", t)[0][..., None]
        mo, margin = self._mask("over", t)
        mo = np.maximum(mo, margin * mu[..., 0])[..., None]   # an object's margin shows only where the paint around it is
        img = self.blank * (1 - mu) + under * mu
        return img * (1 - mo) + top * mo


CLIP_FADE = 1.0                  # seconds the living painting takes to dissolve into the MiniMax clip


def clip_frames(path, skip=0.0):
    """A prepared MiniMax clip (minimax_prep.py) or a rendered panel, frame by frame at the film's size and rate,
    from `skip` seconds in."""
    proc = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", f"{skip:.3f}", "-i", str(path), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                            stdout=subprocess.PIPE)
    while True:
        buf = proc.stdout.read(PW * PH * 3)
        if len(buf) < PW * PH * 3:
            return
        yield np.frombuffer(buf, np.uint8).reshape(PH, PW, 3).astype(np.float32) / 255


def living_frames(work_id):
    """The art lab's living page for this work, frame by frame (living.mjs)."""
    path = PUBLIC_FILM / f"living-{work_id}.mp4"
    meta = json.loads((PUBLIC_FILM / f"living-{work_id}.json").read_text())
    proc = subprocess.Popen(["ffmpeg", "-v", "error", "-i", str(path), "-vf", f"scale={PW}:{PH}:flags=area", "-f", "rawvideo",
                             "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    return meta, proc


def render(film_tl, work):
    w = Work(film_tl, work)
    meta, proc = living_frames(work["id"])
    out = PUBLIC_FILM / f"paint-{work['id']}.mp4"
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{PW}x{PH}", "-r", str(FPS),
                            "-i", "-", "-c:v", "libx264", "-crf", "14", "-preset", "medium", "-pix_fmt", "yuv420p", str(out)],
                           stdin=subprocess.PIPE)
    f0, f1 = round(work["start"] * FPS), round(work["end"] * FPS)
    lf0 = meta["firstFrame"]
    living = None
    mm = work.get("minimax")
    clip, moving = (clip_frames(PUBLIC_FILM / mm["file"]), None) if mm else (None, None)
    for f in range(f0, f1):
        t = f / FPS
        if f >= lf0:
            buf = proc.stdout.read(PW * PH * 3)
            if len(buf) == PW * PH * 3:
                living = np.frombuffer(buf, np.uint8).reshape(PH, PW, 3).astype(np.float32) / 255
        img = w.frame(t, living)
        if mm and t >= mm["from"]:          # the third step: the living painting dissolves into the MiniMax clip
            moving = next(clip, moving)
            k = min(1.0, (t - mm["from"]) / CLIP_FADE)
            img = img * (1 - k * k * (3 - 2 * k)) + moving * (k * k * (3 - 2 * k))
        enc.stdin.write((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8).tobytes())
    enc.stdin.close()
    enc.wait()
    proc.kill()
    print(f"{out.name}: {f1 - f0} frames")


def render_recap(film_tl):
    """The look back under the closing lines (build_timeline.py): each work's MiniMax clip plays again from its own
    start (a work without one: the end of its own panel, paint-<work>.mp4, so the works render first), holds its
    last frame, and dissolves into the next over recap["fade"] seconds."""
    recap = film_tl["recap"]
    out = PUBLIC_FILM / "paint-recap.mp4"
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{PW}x{PH}", "-r", str(FPS),
                            "-i", "-", "-c:v", "libx264", "-crf", "14", "-preset", "medium", "-pix_fmt", "yuv420p", str(out)],
                           stdin=subprocess.PIPE)
    clips = recap["clips"]
    frames = [clip_frames(PUBLIC_FILM / c["file"], c.get("skip", 0.0)) for c in clips]
    shown = [None] * len(clips)
    f0, f1 = round(recap["start"] * FPS), round(recap["end"] * FPS)
    for f in range(f0, f1):
        t = f / FPS
        img = None
        for i, c in enumerate(clips):
            if i and t < c["from"]:              # the first clip opens the look back (its frame 0 may round early)
                break
            shown[i] = next(frames[i], shown[i])          # a finished clip holds its last frame
            k = min(1.0, (t - c["from"]) / recap["fade"]) if i else 1.0
            k = k * k * (3 - 2 * k)
            img = shown[i] if img is None else img * (1 - k) + shown[i] * k
        enc.stdin.write((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8).tobytes())
    enc.stdin.close()
    enc.wait()
    print(f"{out.name}: {f1 - f0} frames")


def check(film_tl, work):
    """Does the work end on exactly the art lab's picture? (The last painted frame against the picture itself.)"""
    w = Work(film_tl, work)
    diff = np.abs(w.frame(work["end"]) - w.pic).max(axis=2) * 255
    bad = int((diff > 3).sum())
    print(f"{work['id']}: largest difference {diff.max():.1f}/255 → {'OK' if not bad else f'{bad} pixels differ by more than 3'}")
    return not bad


def stills(film_tl, work, times):
    w = Work(film_tl, work)
    for t in sorted(times):
        if work["start"] <= t < work["end"]:
            img = w.frame(t)
            path = PUBLIC_FILM / f"still-{work['id']}-{t:06.2f}.png"
            cv2.imwrite(str(path), cv2.cvtColor((np.clip(img, 0, 1) * 255).astype(np.uint8), cv2.COLOR_RGB2BGR))
            print(path)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("film")
    ap.add_argument("--only")
    ap.add_argument("--still", type=float, nargs="*")
    ap.add_argument("--check", action="store_true", help="only check that every work ends fully painted")
    args = ap.parse_args()
    PUBLIC_FILM = PUBLIC / args.film
    tl = json.loads((PUBLIC_FILM / "timeline.json").read_text())
    for work in tl["works"]:
        if args.only and work["id"] != args.only:
            continue
        if args.check:
            check(tl, work)
        elif args.still:
            stills(tl, work, args.still)
        else:
            render(tl, work)
    if tl.get("recap") and not (args.check or args.still) and args.only in (None, "recap"):
        render_recap(tl)
