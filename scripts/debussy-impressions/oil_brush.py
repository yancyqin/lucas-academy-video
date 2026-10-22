"""Deterministic, incremental flat oil brush. Coordinates and width are in pixels.

    python oil_brush.py demo OUT_DIR [--target TARGET.png]
    python oil_brush.py benchmark
    python oil_brush.py check

RGB is float32 sRGB in [0, 1]; height is an optical relief in pixel units,
not millimetres; wet is [0, 1]. This is a painterly deposition approximation,
not a fluid solver. Requires numpy, scipy, opencv and numba.

Prepare geometry once, then paint successive non-overlapping intervals [p0,p1].
Fixed spatial stamps make results independent of frame boundaries (for an
unchanged colour/load and stroke order). A stamp extends a little ahead of the
brush centre, as a real contact patch does. Replaying an interval adds paint.
A zero-length path makes one dab. Call canvas.dry(dt) explicitly to age paint;
paint() itself has no clock. shade() never changes the painting.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import time
import weakref

import cv2
import numpy as np
from numba import njit
from scipy.ndimage import gaussian_filter, gaussian_filter1d
from scipy.interpolate import PchipInterpolator

DEFAULT_TARGET = Path('/Users/yqin/repo/playground/lucas-academy-video-data/debussy-impressions/faune/sample-seine/target.png')


def _noise(rng, shape, sigma):
    z = gaussian_filter(rng.standard_normal(shape).astype(np.float32), sigma)
    return z / max(float(z.std()), 1e-6)


class OilCanvas:
    def __init__(self, W, H, ground=(0.925, 0.894, 0.831), seed=0):
        if int(W) != W or int(H) != H or W < 1 or H < 1:
            raise ValueError('W and H must be positive integers')
        self.W, self.H = int(W), int(H)
        W, H = self.W, self.H
        g = _rgb(ground)
        rng = np.random.default_rng(seed)
        # Woven linen with irregular yarns; not a regular stripe mask on paint.
        yy, xx = np.mgrid[:H, :W].astype(np.float32)
        warp = _noise(rng, (H, W), 5.0)
        yarn = (np.sin(xx * 2.1 + warp * .8) + np.sin(yy * 2.28 + warp * .7)) * .045
        self.tooth = np.clip(.5 + yarn + _noise(rng, (H, W), .65) * .17
                             + _noise(rng, (H, W), 2.8) * .045, 0, 1).astype(np.float32)
        self.rgb = np.clip(g + (self.tooth[..., None] - .5) * .012, 0, 1).astype(np.float32)
        self.height = np.zeros((H, W), np.float32)
        self.wet = np.zeros((H, W), np.float32)
        self._pickup = weakref.WeakKeyDictionary()

    def dry(self, dt, half_life=20.0):
        """Age wetness, in caller-chosen seconds; no effect on RGB or relief."""
        if not np.isfinite(dt) or dt < 0 or not np.isfinite(half_life) or half_life <= 0:
            raise ValueError('dt >= 0 and half_life > 0 are required')
        self.wet *= np.float32(2 ** (-dt / half_life))

    def clear_pickup(self, geom=None):
        """Clean the brush before reusing a geometry (normally use a new one)."""
        if geom is None:
            self._pickup.clear()
        else:
            self._pickup.pop(geom, None)


def _rgb(value):
    a = np.asarray(value, np.float32)
    if a.shape != (3,) or not np.isfinite(a).all() or np.any((a < 0) | (a > 1)):
        raise ValueError('colour/ground must be an RGB triple in [0, 1]')
    return a


@dataclass(eq=False)
class StrokeGeometry:
    """Reusable geometry. Arrays are read-only by convention; no canvas state."""
    points: np.ndarray
    progress: np.ndarray
    tangents: np.ndarray
    pressure: np.ndarray
    widths: np.ndarray
    profiles: np.ndarray
    bristles: np.ndarray  # offset, radius, load, reach, warm/cool bias, tip extension
    width: float
    length: float
    step: float
    seed: int
    depletion: float
    mixing: float


def stroke_geometry(points, width, seed, pressure=None, *, bristles=None,
                    depletion=0.85, mixing=0.22, step=1.5):
    """Resample a centre path; pressure is a scalar, samples, or callable(p).

    Width is the nominal fully spread width. Default pressure lands heavily,
    relaxes, fluctuates, then lifts. Explicit pressure replaces that envelope.
    depletion=0 disables travel-related exhaustion, mixing=0 disables pickup.
    Bristles represent visible hairs/small hair bundles (default 48..160).
    Fixed spacing step (default 1.5 px) is also the progress quantisation.
    """
    pts = np.asarray(points, np.float64)
    if pts.ndim != 2 or pts.shape[1] != 2 or not len(pts) or not np.isfinite(pts).all():
        raise ValueError('points must be a finite non-empty Nx2 array')
    if not np.isfinite(width) or width <= 0 or not np.isfinite(step) or step <= 0:
        raise ValueError('width and step must be positive')
    if not np.isfinite(depletion) or depletion < 0 or not 0 <= mixing <= 1:
        raise ValueError('depletion >= 0 and mixing in [0,1] are required')
    rng = np.random.default_rng(seed)
    keep = np.r_[True, np.linalg.norm(np.diff(pts, axis=0), axis=1) > 1e-8]
    pts = pts[keep]
    if len(pts) == 1:
        P = pts.copy(); length = 0.; u = np.array([0.]); T = np.array([[1., 0.]])
    else:
        arc = np.r_[0., np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))]
        # PCHIP avoids the large overshoot of an unconstrained cubic spline.
        dense_s = np.linspace(0, arc[-1], max(8, int(arc[-1] / .65) + 1))
        dense = PchipInterpolator(arc, pts, axis=0)(dense_s)
        arc2 = np.r_[0., np.cumsum(np.linalg.norm(np.diff(dense, axis=0), axis=1))]
        length = float(arc2[-1])
        ss = np.linspace(0., length, max(2, int(np.ceil(length / step)) + 1))
        P = np.column_stack([np.interp(ss, arc2, dense[:, k]) for k in range(2)])
        u = ss / length
        T = np.gradient(P, axis=0)
        T = gaussian_filter1d(T, max(.5, min(width * .018 / step, 3.)), axis=0, mode='nearest')
        T /= np.maximum(np.linalg.norm(T, axis=1, keepdims=True), 1e-9)
    n = len(P)
    if pressure is None:
        pr = np.interp(u, [0, .045, .16, .40, .68, .80, .91, 1],
                       [.72, 1., .78, .64, .70, .58, .30, .015])
        variation = np.interp(u, np.linspace(0, 1, 17), rng.normal(0, .065, 17))
        pr = np.clip(pr + variation * np.sin(np.pi * u), .005, 1.)
    else:
        pr = np.asarray(pressure(u) if callable(pressure) else pressure, np.float64)
        if pr.ndim > 1 or pr.size == 0 or not np.isfinite(pr).all() or np.any((pr < 0) | (pr > 1)):
            raise ValueError('pressure must contain values in [0,1]')
        pr = np.full(n, float(pr)) if pr.ndim == 0 else np.interp(u, np.linspace(0, 1, len(pr)), pr)
    # Asymmetric splay and nonperiodic breathing of the brush.
    breath = np.interp(u, np.linspace(0, 1, 23), rng.normal(0, .038, 23))
    widths = width * (.30 + .70 * np.sqrt(pr)) * (1 + breath)
    nb = int(np.clip(width * .65, 48, 160)) if bristles is None else int(bristles)
    if nb < 2:
        raise ValueError('at least two bristles are required')
    b = np.empty((nb, 6), np.float32)
    # Jittered hairs avoid both a regular comb and implausibly empty clumps.
    b[:, 0] = (np.arange(nb) + rng.uniform(.05, .95, nb)) / nb * 1.96 - .98
    b[:, 1] = rng.uniform(.65, 2.25, nb) * max(.65, width / nb / 1.8)
    b[:, 2] = rng.lognormal(-.08, .40, nb)
    b[:, 3] = rng.uniform(.62, 1.30, nb)
    b[:, 4] = rng.normal(0, .75, nb)
    b[:, 5] = rng.normal(0, .30, nb)
    bins = max(96, int(np.ceil(width * 1.5)))
    q = np.linspace(-1.15, 1.15, bins)
    profile = np.zeros((n, bins, 4), np.float32)
    # Hair trajectories wander independently; a shared slow clump motion gives
    # short broken grooves, rather than identical comb lines down the stroke.
    knots = np.linspace(0, 1, max(5, int(length / max(12., width * .16)) + 2))
    clump = _noise(rng, (len(knots), 11), (.8, .7))
    drift = np.stack([np.interp(u, knots, clump[:, j]) for j in range(11)], axis=1)
    for j in range(nb):
        cluster = min(10, int((b[j, 0] + 1) * 5.5))
        wander = np.interp(u, knots, rng.normal(0, 1, len(knots)))
        centre = b[j, 0] + (.022 * drift[:, cluster] + .010 * wander)
        delta = (q[None, :] - centre[:, None]) * widths[:, None] * .5
        radius = b[j, 1] * (.65 + .35 * pr[:, None])
        hair = np.exp(-.5 * (delta / radius) ** 2)
        exhausted = np.clip((b[j, 3] - u * depletion) / .24, 0, 1)
        amount = hair * (b[j, 2] * exhausted)[:, None]
        profile[:, :, 0] += amount
        profile[:, :, 1] += amount * b[j, 4]
        profile[:, :, 2] += amount * b[j, 5]
        # Side ridges of individual hair grooves.
        profile[:, :, 3] += np.exp(-.5 * ((np.abs(delta) - radius * 1.1) / (radius * .32 + .25)) ** 2) * exhausted[:, None]
    total = profile[:, :, 0].copy()
    profile[:, :, 1:3] /= np.maximum(total[:, :, None], .001)
    # Aperiodic, broad patches of incompletely mixed pigment.
    mottled = _noise(rng, (max(8, int(length / 9) + 1), max(12, bins // 8)), (1.3, 1.0))
    mottled = cv2.resize(mottled, (bins, n), interpolation=cv2.INTER_LINEAR)
    profile[:, :, 1] = profile[:, :, 1] * .55 + mottled * .90
    edge_left = .94 + .045 * drift[:, 0]
    edge_right = .94 + .045 * drift[:, -1]
    core = np.clip((q[None, :] + edge_left[:, None]) / .14, 0, 1)
    core *= np.clip((edge_right[:, None] - q[None, :]) / .14, 0, 1)
    # Loaded pigment bridges the gaps between hairs. This film thins with use;
    # individual hairs still control ridges, colour, contact length and runout.
    film = core * (.78 * np.maximum(0, 1 - u * depletion) ** .65)[:, None]
    profile[:, :, 0] = (np.clip(total * .42, 0, 1.7) + film) * np.clip(1 + mottled * .22, .30, 1.65)
    # Interrupted ridges: hairs skip, clump and catch again, at a finer scale
    # than the broad pigment marbling. No periodic phase/noise reset per frame.
    chatter = _noise(rng, (max(8, int(length / 4) + 1), max(16, bins // 3)), (.8, .7))
    chatter = cv2.resize(chatter, (bins, n), interpolation=cv2.INTER_LINEAR)
    profile[:, :, 3] = np.minimum(profile[:, :, 3] * .20, .8) * np.clip(.85 + chatter * .6, .08, 1.8)
    profile[:, :, 2] += mottled * .16
    return StrokeGeometry(P.astype(np.float32), u, T.astype(np.float32), pr.astype(np.float32),
                          widths.astype(np.float32), profile, b, float(width), length,
                          length / max(1, n - 1), int(seed), float(depletion), float(mixing))


def brush_tip(geom, p):
    """Return centre x,y, tangent angle in radians, and pressure at progress p."""
    p = _progress(p)
    x = np.interp(p, geom.progress, geom.points[:, 0])
    y = np.interp(p, geom.progress, geom.points[:, 1])
    angles = np.unwrap(np.arctan2(geom.tangents[:, 1], geom.tangents[:, 0]))
    return float(x), float(y), float(np.interp(p, geom.progress, angles)), float(np.interp(p, geom.progress, geom.pressure))


def _progress(p):
    if not np.isfinite(p) or not 0 <= p <= 1:
        raise ValueError('progress must be finite and in [0,1]')
    return float(p)


@njit(cache=True)
def _stamp(rgb, height, wet, tooth, profile, pickup, pigment, cx, cy, tx, ty,
           width, pressure, progress, step, load, mixing, depletion, is_first, x0, y0):
    H, W = height.shape
    bins = profile.shape[0]
    half = width * .5
    depth = max(1.4, width * (.065 + .065 * pressure))
    # Fixed integrated dose, independent of how many animation frames are used.
    dose = step / depth
    if is_first:
        dose += .55
    reserve = load * np.exp(-depletion * progress * 1.35)
    ph, pw = pigment.shape[:2]
    sums = np.zeros((bins, 4), np.float32)
    for iy in range(ph):
        y = y0 + iy
        if y < 0 or y >= H:
            continue
        for ix in range(pw):
            x = x0 + ix
            if x < 0 or x >= W:
                continue
            dx, dy = x - cx, y - cy
            a = dx * tx + dy * ty
            q = (-dx * ty + dy * tx) / half
            bf = (q + 1.15) / 2.3 * (bins - 1)
            if bf < 0 or bf >= bins - 1:
                continue
            bi = int(bf); f = bf - bi
            density = profile[bi, 0] * (1-f) + profile[bi+1, 0] * f
            warmth = profile[bi, 1] * (1-f) + profile[bi+1, 1] * f
            extension = profile[bi, 2] * (1-f) + profile[bi+1, 2] * f
            ridge = profile[bi, 3] * (1-f) + profile[bi+1, 3] * f
            # Each hair ends at a different depth; the tip is not a reveal cut.
            front = depth * (max(.12, 1 - (q * .89) ** 2) ** .4)
            r = abs(a - extension * depth * .65) / front
            if r >= 1:
                continue
            contact = max(0., 1 - r*r) ** .65
            local = density * reserve * pressure
            # As the brush dries/lifts, it only touches raised linen/old paint.
            surface = tooth[y, x] + min(.28, height[y, x] * .08)
            dry_gate = min(1., max(0., (surface + local * .85 - .63) * 5.5))
            # A loaded brush spreads a continuous oil film over low yarns too.
            dry_gate = max(dry_gate, min(1., max(0., (local - .28) * 1.8)))
            coverage = contact * dry_gate * min(1.5, density)
            amount = coverage * dose * reserve * (.28 + pressure * .85)
            if amount < .0001:
                continue
            alpha = 1 - np.exp(-amount * 3.8)
            oldwet = wet[y, x]
            mix = mixing * oldwet * min(.8, pickup[bi, 3])
            # Pigment pickup is advected by the next spatial stamp of this hair.
            for c in range(3):
                old = rgb[y, x, c]
                base = pigment[iy, ix, c]
                tint = (0.022 if c == 0 else (0.005 if c == 1 else -.018)) * warmth
                tint += .025 * warmth * (base - .4)
                fresh = min(1., max(0., base + tint))
                carried = pickup[bi, c] / max(.001, pickup[bi, 3])
                fresh = fresh * (1 - mix) + carried * mix
                rgb[y, x, c] = min(1., max(0., old + alpha * (fresh - old)))
                sums[bi, c] += old * oldwet * coverage
            sums[bi, 3] += oldwet * coverage
            # Bristles comb existing wet ridges, while loaded edges leave relief.
            target_h = reserve * (.5 + pressure * 1.45) * (.72 + ridge) * contact
            target_h += reserve * contact * (.36 * abs(warmth) + .38 * (tooth[y,x]-.5))
            # Small unloading ridge just before the final lift, not a round cap.
            target_h += reserve * .6 * np.exp(-((progress-.87)/.055)**2) * contact
            h = height[y, x]
            height[y, x] = max(0., h + amount * .6 + min(.55, amount * 1.8) * (target_h - h) * (.4 + oldwet * .6))
            wet[y, x] = min(1., oldwet + alpha * (1 - oldwet))
    for b in range(bins):
        if sums[b, 3] > .001:
            weight = min(.8, sums[b, 3] * .07)
            for c in range(3):
                pickup[b, c] = pickup[b, c] * .84 + sums[b, c] / sums[b, 3] * weight * .16
            pickup[b, 3] = pickup[b, 3] * .84 + weight * .16
        else:
            for c in range(4):
                pickup[b, c] *= .985


def paint(canvas, geom, p0, p1, colour, load=1.0):
    """Deposit only spatial stamps in (p0,p1], plus the landing at p0=0.

    colour is RGB or callable(xs,ys)->(...,3). xs/ys are clipped float32
    pixel-coordinate grids for each stamp's bounding rectangle. Callable output
    may broadcast to that grid; it must be finite RGB in [0,1]. Sampling occurs
    at destination pixels, useful for revealing an image. load >= 0 controls
    opacity, exhaustion and relief. The callable should itself be deterministic.
    """
    p0, p1 = _progress(p0), _progress(p1)
    if p1 < p0:
        raise ValueError('p1 must be >= p0')
    if not np.isfinite(load) or load < 0:
        raise ValueError('load must be finite and nonnegative')
    if p1 == p0 or load == 0:
        return
    constant = None if callable(colour) else _rgb(colour)
    start = 0 if p0 == 0 else int(np.searchsorted(geom.progress, p0, side='right'))
    end = int(np.searchsorted(geom.progress, p1, side='right'))
    if start >= end:
        return
    pickup = canvas._pickup.setdefault(geom, np.zeros((geom.profiles.shape[1], 4), np.float32))
    for i in range(start, end):
        cx, cy = geom.points[i]; tx, ty = geom.tangents[i]
        width, pr = float(geom.widths[i]), float(geom.pressure[i])
        if pr <= 0:
            continue
        depth = max(1.4, width * (.065 + .065 * pr)) * 2.1
        rx, ry = abs(ty) * width * .58 + abs(tx) * depth + 2, abs(tx) * width * .58 + abs(ty) * depth + 2
        x0, x1 = max(0, int(np.floor(cx-rx))), min(canvas.W, int(np.ceil(cx+rx))+1)
        y0, y1 = max(0, int(np.floor(cy-ry))), min(canvas.H, int(np.ceil(cy+ry))+1)
        if x1 <= x0 or y1 <= y0:
            continue
        shape = (y1-y0, x1-x0, 3)
        if constant is not None:
            pigment = np.broadcast_to(constant, shape)
        else:
            ys, xs = np.mgrid[y0:y1, x0:x1].astype(np.float32)
            raw = np.asarray(colour(xs, ys), np.float32)
            if not np.isfinite(raw).all() or np.any((raw < 0) | (raw > 1)):
                raise ValueError('colour callable must return finite RGB in [0,1]')
            pigment = np.broadcast_to(raw, shape)
        _stamp(canvas.rgb, canvas.height, canvas.wet, canvas.tooth, geom.profiles[i], pickup,
               pigment, float(cx), float(cy), float(tx), float(ty), width, pr,
               float(geom.progress[i]), geom.step, float(load), geom.mixing, geom.depletion,
               i == 0, x0, y0)


@njit(cache=True)
def _shade(rgb, height, tooth, lx, ly, strength):
    H, W = height.shape
    out = np.empty_like(rgb)
    for y in range(H):
        ym, yp = max(0, y-1), min(H-1, y+1)
        for x in range(W):
            xm, xp = max(0, x-1), min(W-1, x+1)
            gx = (height[y, xp] - height[y, xm]) * .5
            gy = (height[yp, x] - height[ym, x]) * .5
            # Soft, matte raking light; no wet-plastic white highlight.
            diffuse = min(.20, max(-.24, (-gx * lx - gy * ly) * .26))
            relief = min(1., height[y, x] * 1.8)
            grain = (tooth[y, x] - .5) * .012 * relief
            glint = max(0., diffuse - .06) ** 2 * .32 * relief
            for c in range(3):
                base = rgb[y, x, c]
                out[y, x, c] = min(1., max(0., base * (1 + strength * (diffuse + grain)) + glint * strength))
    return out


def shade(canvas, light=(-0.5, -0.7), strength=1.0):
    """New RGB display array with matte relief. light is screen-space direction."""
    light = np.asarray(light, np.float64)
    if light.shape != (2,) or not np.isfinite(light).all() or not np.isfinite(strength) or strength < 0:
        raise ValueError('light must be a finite 2-vector; strength must be >= 0')
    norm = max(float(np.linalg.norm(light)), 1e-9)
    return _shade(canvas.rgb, canvas.height, canvas.tooth, light[0]/norm, light[1]/norm, float(strength))


def _save(path, rgb):
    if not cv2.imwrite(str(path), cv2.cvtColor(np.uint8(np.clip(rgb, 0, 1)*255 + .5), cv2.COLOR_RGB2BGR)):
        raise OSError(f'Could not write {path}')


def _label(img, title, x, y):
    # OpenCV 5's text renderer accepts uint8 only. Restrict conversion to label ROI.
    y0, y1 = max(0, y-22), min(img.shape[0], y+6)
    x0, x1 = max(0, x), min(img.shape[1], x+len(title)*12)
    roi = np.uint8(np.clip(img[y0:y1, x0:x1], 0, 1)*255+.5)
    cv2.putText(roi, title, (x-x0, y-y0), cv2.FONT_HERSHEY_SIMPLEX, .55, (61,59,54), 1, cv2.LINE_AA)
    img[y0:y1, x0:x1] = roi.astype(np.float32)/255


def _sampler(target):
    def sample(xs, ys):
        return cv2.remap(target, xs, ys, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    return sample


def demo(out_dir, target_path=DEFAULT_TARGET):
    """Write inspection sheets, an incremental sequence, reveal and dense study."""
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    c = OilCanvas(1440, 1120, seed=42)
    cases = [
        ('Loaded straight / cool green', [(90,145),(590,170)], 130, (.22,.36,.32), 1.2),
        ('Curved / warm ochre', [(800,130),(900,225),(1100,140),(1320,180)], 135, (.66,.46,.20), 1.05),
        ('Trill / violet grey', [(80+i*44,420+24*np.sin(i*1.8)) for i in range(13)], 110, (.43,.39,.52), 1.1),
        ('Short dabs / heavy landing', [(850,400),(925,430)], 140, (.75,.69,.47), 1.4),
        ('Long sweep / paint runs out', [(110,700),(350,625),(630,710),(950,650),(1310,740)], 150, (.23,.39,.48), .85),
        ('Wet overlap / pigment dragged', [(160,930),(630,970)], 130, (.66,.49,.32), 1.1),
        ('Dry scumble / broken canvas', [(870,930),(1300,970)], 125, (.39,.48,.36), .40),
    ]
    for k, (title, pts, w, col, load) in enumerate(cases):
        g = stroke_geometry(pts,w,100+k)
        paint(c,g,0,1,col,load)
    paint(c,stroke_geometry([(380,860),(410,1035)],110,608),0,1,(.33,.42,.47),1.2)
    paint(c,stroke_geometry([(1070,398)],95,220),0,1,(.51,.56,.39),1.3)
    paint(c,stroke_geometry([(1210,390),(1250,405)],80,221),0,1,(.72,.53,.29),1.1)
    sheet = shade(c)
    for title, x, y in [(cases[0][0],45,45),(cases[1][0],765,45),(cases[2][0],45,315),
                         (cases[3][0],765,315),(cases[4][0],45,570),(cases[5][0],45,855),(cases[6][0],765,855)]:
        _label(sheet,title,x,y)
    _save(out/'01-stroke-sheet.png',sheet)
    _save(out/'01-detail.png',shade(c)[80:250,100:630])
    _save(out/'01-height.png',np.repeat(np.clip(c.height[...,None]/3,0,1),3,axis=2))
    print('wrote stroke sheet', flush=True)

    # Progress: exactly the same canvas, no prepainted part of a future stroke.
    c = OilCanvas(900,330,seed=12)
    g = stroke_geometry([(100,170),(300,140),(530,190),(790,150)],165,24)
    frames=[]; p0=0.
    for p in [.25,.5,.75,1.]:
        paint(c,g,p0,p,(.24,.39,.43),1.1); p0=p
        frame=shade(c); _save(out/f'03-progress-{int(p*100):03d}.png',frame)
        _label(frame,f'{int(p*100)}% | tip x={brush_tip(g,p)[0]:.1f}',20,28); frames.append(frame)
    _save(out/'03-progress-sheet.png',np.concatenate(frames,axis=0))

    raw=cv2.imread(str(target_path))
    if raw is None:
        raise FileNotFoundError(f'Reveal target is required: {target_path}')
    target=cv2.cvtColor(raw,cv2.COLOR_BGR2RGB).astype(np.float32)/255
    H,W=target.shape[:2]; sample=_sampler(target)
    c=OilCanvas(W,H,seed=8)
    paths=[[(.10,.18),(.42,.21),(.84,.14)],[(.12,.34),(.46,.28),(.84,.40)],
           [(.09,.51),(.38,.56),(.87,.50)],[(.15,.71),(.54,.66),(.85,.76)],
           [(.13,.88),(.46,.82),(.88,.91)]]
    for k,pts in enumerate(paths):
        g=stroke_geometry([(x*W,y*H) for x,y in pts],W*.17,300+k)
        for p in range(45):
            paint(c,g,p/45,(p+1)/45,sample,1.15)
    _save(out/'02-reveal-shaded.png',shade(c))
    _save(out/'02-reveal-flat.png',c.rgb)
    print('wrote reveal and progress sheets',flush=True)

    # Short, interlocked strokes from a crop of the reference. Each dab uses a
    # locally averaged pigment, so the result demonstrates marks, not a mask.
    study=cv2.resize(target,(800,707),interpolation=cv2.INTER_AREA)
    c=OilCanvas(800,707,seed=14); rng=np.random.default_rng(77)
    blurred=cv2.GaussianBlur(study,(0,0),3)
    for layer in range(3):
        spacing=[52,31,21][layer]
        coords=[(x,y) for y in range(0,707+spacing,spacing) for x in range(0,800+spacing,spacing)]
        rng.shuffle(coords)
        for x,y in coords:
            x=float(np.clip(x+rng.normal(0,spacing*.25),0,799)); y=float(np.clip(y+rng.normal(0,spacing*.25),0,706))
            angle=rng.normal(-.12 if y>300 else -.45,.40)
            length=rng.uniform(.65,1.6)*spacing
            dx,dy=np.cos(angle)*length,np.sin(angle)*length
            w=spacing*rng.uniform(1.05,1.65) if layer==0 else spacing*rng.uniform(.60,1.15)
            g=stroke_geometry([(x-dx*.4,y-dy*.4),(x+dx*.6,y+dy*.6)],w,int(rng.integers(1,2**30)),depletion=.45,mixing=.16)
            col=np.clip(blurred[int(y),int(x)]+rng.normal(0,.014,3),0,1)
            paint(c,g,0,1,col,rng.uniform(.9,1.5))
        c.dry(8)
    _save(out/'04-short-stroke-study.png',shade(c))
    _save(out/'04-study-detail.png',shade(c)[220:520,250:650])
    _save(out/'04-study-reference.png',study)
    print(f'Demo PNGs: {out.resolve()}',flush=True)


def benchmark(frames=90):
    """1440x1272, width 250, length 800; defaults to three seconds at 30 fps."""
    if frames < 1:
        raise ValueError('frames must be positive')
    c=OilCanvas(1440,1272,seed=1)
    t=time.perf_counter(); g=stroke_geometry([(270,600),(1070,600)],250,2)
    geometry_ms=(time.perf_counter()-t)*1000
    # Warm both Numba specialisations, including callable-contiguous RGB input.
    paint(c,g,0,.01,(.3,.4,.5)); shade(c)
    sample=lambda x,y: np.stack((x/1440,y/1272,np.full_like(x,.45)),axis=-1)
    paint(c,g,.01,.02,sample)
    reports=[]
    for name,col in [('constant',(.3,.4,.5)),('callable',sample)]:
        c=OilCanvas(1440,1272,seed=1); pt=[]; st=[]
        for i in range(frames):
            t=time.perf_counter(); paint(c,g,i/frames,(i+1)/frames,col); pt.append((time.perf_counter()-t)*1000)
            t=time.perf_counter(); shade(c); st.append((time.perf_counter()-t)*1000)
        reports.append(f'{name}: paint median={np.median(pt):.2f} ms p95={np.percentile(pt,95):.2f} max={max(pt):.2f}; shade median={np.median(st):.2f} ms p95={np.percentile(st,95):.2f}; combined p95={np.percentile(np.array(pt)+st,95):.2f} ms')
    print(f'Geometry: {geometry_ms:.1f} ms; {len(g.bristles)} bristles; {len(g.points)} spatial stamps; {frames} frames ({800/frames:.2f} px/frame)\n'+'\n'.join(reports))
    print('JIT warm-up excluded; geometry/canvas creation are not per-frame work. Timing depends on pixels travelled per frame.')


def check():
    """Small behavioural checks (chunking, boundaries, pickup, no future paint)."""
    g=stroke_geometry([(35,75),(130,105),(225,70)],64,78)
    g2=stroke_geometry([(35,75),(130,105),(225,70)],64,78)
    assert np.array_equal(g.profiles,g2.profiles),'geometry seed determinism'
    a=OilCanvas(280,180,seed=2); b=OilCanvas(280,180,seed=2)
    col=(.35,.45,.55)
    paint(a,g,0,1,col)
    for i in range(41): paint(b,g2,i/41,(i+1)/41,col)
    for attr in ['rgb','height','wet']:
        assert np.array_equal(getattr(a,attr),getattr(b,attr)),attr+' partition dependence'
    assert np.allclose(shade(a,strength=0),a.rgb)
    before=a.rgb.copy(); shade(a); assert np.array_equal(before,a.rgb)
    c=OilCanvas(280,180,seed=2); before=c.rgb.copy()
    paint(c,g,.2,.2,col); assert np.array_equal(before,c.rgb)
    paint(c,g,0,.25,col); assert np.array_equal(before[:,150:],c.rgb[:,150:]),'future paint'
    before=c.rgb.copy()
    paint(c,stroke_geometry([(40,40),(240,130)],90,4,pressure=0),0,1,col)
    assert np.array_equal(before,c.rgb),'zero pressure leaves paint'
    wet_before=c.wet.copy(); c.dry(20)
    assert np.allclose(c.wet,wet_before*.5),'drying half life'
    for path in [[(-90,-90),(-30,-30)],[(0,0)],[(279,179),(279,179)],[(50,30),(200,100)]]:
        z=stroke_geometry(path,80,5,pressure=0 if len(path)>1 and path[0]==(50,30) else None)
        paint(c,z,0,1,lambda x,y: np.broadcast_to(np.array(col,np.float32),x.shape+(3,)))
    assert np.isfinite(c.rgb).all() and np.isfinite(c.height).all()
    assert c.height.min()>=0 and c.wet.min()>=0 and c.wet.max()<=1
    wet=OilCanvas(280,180,seed=2); dry=OilCanvas(280,180,seed=2)
    under=stroke_geometry([(30,90),(240,90)],85,11)
    over=stroke_geometry([(130,30),(140,150)],60,12,mixing=.8)
    for c in [wet,dry]: paint(c,under,0,1,(.8,.25,.1))
    dry.dry(1000)
    for c in [wet,dry]: paint(c,over,0,1,(.15,.35,.7))
    assert np.max(np.abs(wet.rgb-dry.rgb))>.005,'wet pickup inactive'
    # Callable reveal on wet underpainting, including pickup across frame cuts.
    a=OilCanvas(280,180,seed=3); b=OilCanvas(280,180,seed=3)
    sample=lambda xs,ys: np.stack((xs/280,ys/180,np.full_like(xs,.4)),axis=-1)
    for c in [a,b]: paint(c,under,0,1,(.8,.25,.1))
    paint(a,over,0,1,sample)
    for i in range(23): paint(b,over,i/23,(i+1)/23,sample)
    for attr in ['rgb','height','wet']:
        assert np.array_equal(getattr(a,attr),getattr(b,attr)),'wet callable partition: '+attr
    print('PASS: seed determinism; exact frame partition invariance (fixed RGB and wet callable); nonmutating shade; empty intervals; zero pressure; drying; no future paint; clipped/dab paths; numeric bounds; wet pickup.')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    sub=parser.add_subparsers(dest='command',required=True)
    d=sub.add_parser('demo'); d.add_argument('out_dir'); d.add_argument('--target',type=Path,default=DEFAULT_TARGET)
    bm=sub.add_parser('benchmark'); bm.add_argument('--frames',type=int,default=90)
    sub.add_parser('check')
    args=parser.parse_args()
    if args.command=='demo': demo(args.out_dir,args.target)
    elif args.command=='benchmark': benchmark(args.frames)
    else: check()
