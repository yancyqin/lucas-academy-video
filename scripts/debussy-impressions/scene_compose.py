"""scene_compose.py — the plein-air scene for the faune film: a painter's easel in front of the real river, a vintage
brush painting the picture stroke by stroke, a camera push-in to the canvas, then a vintage magic wand that wakes the
living painting up (owner, 2026-10-17).

Layers (back to front): the restored real scene (Codex), the easel with its canvas (Codex, green-keyed), the painted
canvas (lazy_painter frames, mapped onto the canvas in perspective), the brush (Codex, green-keyed) with its soft
shadow, then in the living phase the browser frames on the canvas and the wand (Codex, green-keyed) with golden dust.
The camera is 2.5D: the canvas quad is interpolated to a full-screen rectangle; the easel follows that homography,
the background only a third of the zoom and goes out of focus, so the easel seems to come off the river.

    python scene_compose.py CONFIG.json OUT.mp4
"""
import json, math, subprocess, sys, os, glob
import numpy as np, cv2
sys.path.insert(0, os.path.dirname(__file__))
from lazy_painter import smooth_path, ease

FW, FH, FPS = 1920, 1080, 30


def load_rgb(p): return cv2.cvtColor(cv2.imread(p), cv2.COLOR_BGR2RGB).astype(np.float32) / 255


def key_green(path):
    """RGBA from a flat #00FF00 backdrop: alpha from how much green beats red/blue, then despill the edges."""
    im = cv2.imread(path).astype(np.float32)
    b, g, r = im[..., 0], im[..., 1], im[..., 2]
    spill = g - np.maximum(r, b)
    a = 1 - np.clip((spill - 18) / 70, 0, 1)
    a = cv2.GaussianBlur(a, (0, 0), 0.7)
    g2 = np.where(spill > 0, np.maximum(r, b) + np.clip(spill, 0, None) * 0.15, g)
    rgb = np.stack([r, g2, b], -1) / 255
    return np.dstack([rgb, a]).astype(np.float32)


def key_magenta(path):
    """RGBA from a flat #FF00FF backdrop (Impressionist palettes are full of greens, so no green screen)."""
    im = cv2.imread(path).astype(np.float32)
    b, g, r = im[..., 0], im[..., 1], im[..., 2]
    spill = np.minimum(r, b) - g
    a = 1 - np.clip((spill - 40) / 90, 0, 1)
    a = cv2.GaussianBlur(a, (0, 0), 0.8)
    m = np.minimum(r, b); excess = np.clip(m - g - 20, 0, None) * (1 - a)       # pull the magenta out of the edges
    rgb = np.stack([r - excess, g, b - excess], -1) / 255
    return np.dstack([rgb.clip(0, 1), a]).astype(np.float32)


def key_any(path):
    im = cv2.imread(path); corner = im[:8, :8].reshape(-1, 3).mean(0)        # BGR of the backdrop
    return key_magenta(path) if corner[2] > 180 and corner[0] > 180 and corner[1] < 90 else key_green(path)


def dreamy(rgba, fade=0.82, glow=0.35, soften=1.4, desat=0.15):
    """The tools as a memory of a painting: softer edges, a little transparent, a soft glow, a little less colour."""
    out = rgba.copy(); a = cv2.GaussianBlur(rgba[..., 3], (0, 0), soften) * fade
    rgb = rgba[..., :3]; grey = rgb.mean(2, keepdims=True); rgb = grey + (rgb - grey) * (1 - desat)
    halo = cv2.GaussianBlur(rgb * rgba[..., 3:4], (0, 0), 9) * glow
    out[..., :3] = np.clip(rgb + halo * (1 - rgb), 0, 1)
    out[..., 3] = np.clip(np.maximum(a, cv2.GaussianBlur(rgba[..., 3], (0, 0), 9) * glow * 0.5), 0, 1)
    return out


def canvas_quad(easel_rgba):
    """The blank canvas: the biggest bright, low-saturation region; its 4 corners TL, TR, BR, BL."""
    rgb = (easel_rgba[..., :3] * 255).astype(np.uint8); a = easel_rgba[..., 3]
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    m = ((hsv[..., 2] > 170) & (hsv[..., 1] < 60) & (a > 0.6 * a.max())).astype(np.uint8)   # works on a faded easel too
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    n, lab, stats, _ = cv2.connectedComponentsWithStats(m)
    k = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    cnt, _ = cv2.findContours((lab == k).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    hull = cv2.convexHull(max(cnt, key=cv2.contourArea)).reshape(-1, 2).astype(np.float32)
    s = hull.sum(1); d = hull[:, 0] - hull[:, 1]
    return np.array([hull[np.argmin(s)], hull[np.argmax(d)], hull[np.argmax(s)], hull[np.argmin(d)]], np.float32)


def tip_of(rgba, toward):
    """The working end of a sprite: the opaque pixel farthest in the direction `toward` (e.g. (-1, 1) = lower left)."""
    ys, xs = np.nonzero(rgba[..., 3] > 0.5)
    i = np.argmax(xs * toward[0] + ys * toward[1])
    return np.array([xs[i], ys[i]], np.float32)


def over(dst, rgba, x, y):
    """Alpha-composite an RGBA sprite at integer position (x, y) onto dst (clipped)."""
    h, w = rgba.shape[:2]
    x0, y0 = max(0, x), max(0, y); x1, y1 = min(dst.shape[1], x + w), min(dst.shape[0], y + h)
    if x1 <= x0 or y1 <= y0: return
    s = rgba[y0 - y:y1 - y, x0 - x:x1 - x]; a = s[..., 3:4]
    dst[y0:y1, x0:x1] = dst[y0:y1, x0:x1] * (1 - a) + s[..., :3] * a


def sprite_at(rgba, tip, pos, scale, angle_deg):
    """Scale and rotate a sprite about its tip, so the tip lands on `pos`; returns (rgba, x, y)."""
    h, w = rgba.shape[:2]
    M = cv2.getRotationMatrix2D((float(tip[0]), float(tip[1])), angle_deg, scale)
    M[:, 2] += np.array(pos) - tip
    corners = np.array([[0, 0, 1], [w, 0, 1], [w, h, 1], [0, h, 1]], np.float32) @ M.T
    x0, y0 = np.floor(corners.min(0)).astype(int); x1, y1 = np.ceil(corners.max(0)).astype(int)
    M[:, 2] -= [x0, y0]
    out = cv2.warpAffine(rgba, M, (x1 - x0, y1 - y0), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
    return out, x0, y0


def smoothstep(x): x = min(max(x, 0.0), 1.0); return x * x * (3 - 2 * x)


class Brush:
    """The painter's hand, continuous: on a stroke the brush head follows the stroke (eased like the paint); between
    strokes it lifts and glides on a smooth curve (leaving along the old stroke, arriving along the new one), so it
    never jumps. Returns (x, y, lift 0..1, direction) in picture pixels."""
    def __init__(self, strokes, pic_size):
        self.S = strokes; self.W, self.H = pic_size; self.paths = []
        for s in strokes:
            P = smooth_path(np.array(s["pts"], np.float32), s["width"])
            seg = np.linalg.norm(np.diff(P, axis=0), axis=1); cum = np.concatenate([[0], np.cumsum(seg)])
            self.paths.append((P, cum))

    def stop(self, k): s = self.S[k]; return s.get("stop", s["end"] + s.get("ring", 0.35))

    def on(self, k, u):
        P, cum = self.paths[k]; u = float(np.clip(u, 0, cum[-1]))
        i = int(np.clip(np.searchsorted(cum, u), 1, len(P) - 1))
        f = (u - cum[i - 1]) / max(1e-6, cum[i] - cum[i - 1]); p = P[i - 1] + (P[i] - P[i - 1]) * f
        d = P[min(i + 4, len(P) - 1)] - P[max(i - 4, 0)]; d = d / (np.linalg.norm(d) + 1e-9)
        return p, d

    def at(self, t):
        S = self.S; n = len(S)
        for k in range(n):
            if S[k]["t"] <= t <= self.stop(k):
                L = self.paths[k][1][-1]
                p, d = self.on(k, ease((t - S[k]["t"]) / (self.stop(k) - S[k]["t"])) * L)
                return p[0], p[1], 0.0, math.atan2(d[1], d[0])
        prev = max([k for k in range(n) if self.stop(k) < t], default=None)
        nxt = min([k for k in range(n) if S[k]["t"] > t], default=None)
        if prev is None:                                          # arriving before the first stroke
            p1, d1 = self.on(nxt, 0); ta, tb = S[nxt]["t"] - 1.2, S[nxt]["t"]
            p0 = p1 + np.array([self.W * 0.5, -self.H * 0.35]); d0 = -(p0 - p1) / np.linalg.norm(p0 - p1)
        elif nxt is None:                                         # leaving after the last one
            p0, d0 = self.on(prev, 1e9); ta = self.stop(prev); tb = ta + 1.6
            p1 = p0 + np.array([self.W * 0.6, -self.H * 0.5]); d1 = (p1 - p0) / np.linalg.norm(p1 - p0)
            if t > tb: return None
        else:
            p0, d0 = self.on(prev, 1e9); p1, d1 = self.on(nxt, 0); ta, tb = self.stop(prev), S[nxt]["t"]
        f = min(1.0, max(0.0, (t - ta) / max(0.05, tb - ta))); g = f * f * (3 - 2 * f)
        dist = float(np.linalg.norm(p1 - p0)); m = max(40.0, 0.6 * dist)
        h00, h10, h01, h11 = 2 * g ** 3 - 3 * g ** 2 + 1, g ** 3 - 2 * g ** 2 + g, -2 * g ** 3 + 3 * g ** 2, g ** 3 - g ** 2
        p = h00 * p0 + h10 * m * d0 + h01 * p1 + h11 * m * d1      # cubic Hermite: smooth in and out
        lift = math.sin(math.pi * f) * min(1.0, 0.25 + dist / 500)
        if nxt is None: lift = min(1.0, f * 2)
        if prev is None: lift = min(1.0, (1 - f) * 2)
        vel = (p1 - p0) if dist > 1 else d0
        return float(p[0]), float(p[1]), lift, math.atan2(vel[1], vel[0])


def main(cfg_path, out, stills=None):
    C = json.load(open(cfg_path))
    bg = load_rgb(C["background"]); bg = cv2.resize(bg, (int(FW * 1.12), int(FW * 1.12 * bg.shape[0] / bg.shape[1])), interpolation=cv2.INTER_CUBIC)
    bg_loop = sorted(glob.glob(os.path.join(C["background_loop"], "*.jpg"))) if C.get("background_loop") else []   # MiniMax, looping
    easel = key_any(C["easel"]); brush = key_any(C["brush"]); wand = key_any(C["wand_img"])
    if C.get("dreamy"):                                           # owner 10-17: 稍微 fade 一些，给人梦幻的感觉
        dz = C["dreamy"] if isinstance(C["dreamy"], dict) else {}
        easel = dreamy(easel, **dz); brush = dreamy(brush, **dz); wand = dreamy(wand, **dz)
    if C.get("flip"): easel = np.ascontiguousarray(easel[:, ::-1])   # the easel turned the other way
    paint = sorted(glob.glob(os.path.join(C["paint_frames"], "*.jpg")))
    live = sorted(glob.glob(os.path.join(C["live_frames"], "*.jpg")))
    pic0 = load_rgb(paint[0]); ph, pw = pic0.shape[:2]
    Q = canvas_quad(easel)
    # squeeze the easel sideways so its canvas has the painting's proportions, then place it from the canvas
    qa = (np.linalg.norm(Q[1] - Q[0]) + np.linalg.norm(Q[2] - Q[3])) / (np.linalg.norm(Q[3] - Q[0]) + np.linalg.norm(Q[2] - Q[1]))
    sx = (pw / ph) / qa
    ch0 = (np.linalg.norm(Q[3] - Q[0]) + np.linalg.norm(Q[2] - Q[1])) / 2
    es = C.get("canvas_height", 0.46) * FH / ch0
    qc = Q.mean(0) * [es * sx, es]
    eo = np.array(C.get("canvas_center", [0.36, 0.30])) * [FW, FH] - qc
    A2 = np.float32([[es * sx, 0, eo[0]], [0, es, eo[1]]])
    easel_f = cv2.warpAffine(easel, A2, (FW, FH), flags=cv2.INTER_AREA, borderValue=(0, 0, 0, 0))
    Qf0 = (Q * [es * sx, es] + eo).astype(np.float32)             # canvas quad in the wide shot
    ch = min(FH * C.get("full_height", 0.94), FW * 0.96 * ph / pw); cw = ch * pw / ph   # wide paintings fit the width
    Qf1 = np.array([[(FW - cw) / 2, (FH - ch) / 2], [(FW + cw) / 2, (FH - ch) / 2], [(FW + cw) / 2, (FH + ch) / 2], [(FW - cw) / 2, (FH + ch) / 2]], np.float32)
    rect = np.array([[0, 0], [pw, 0], [pw, ph], [0, ph]], np.float32)
    # the canvas's own light and weave, taken from the blank canvas in the easel image
    lightmap = cv2.warpPerspective(cv2.cvtColor((easel[..., :3] * 255).astype(np.uint8), cv2.COLOR_RGB2GRAY).astype(np.float32) / 255,
                                   cv2.getPerspectiveTransform(Q.astype(np.float32), rect), (pw, ph))
    lightmap = (lightmap / (np.median(lightmap) + 1e-6)).clip(0.75, 1.15)[..., None]
    # the easel stands in the scene at a painter's distance (owner 10-21: 画板小很多，真的在画的那种距离), so its feet
    # are on the ground: soft contact shadows under each leg, grass in front of the lowest part of the legs, and the
    # wood takes a little of the light around it
    ea = easel_f[..., 3]; rows = np.where(ea.max(1) > 0.5)[0]
    e_bot = int(rows[-1]); E_h = float(rows[-1] - rows[0])
    band = ((ea > 0.5) & (np.arange(FH)[:, None] >= e_bot - 0.06 * E_h)).astype(np.uint8)
    nl, lab, stats, _ = cv2.connectedComponentsWithStats(band)
    feet = []
    for k in range(1, nl):
        if stats[k, cv2.CC_STAT_AREA] < 4: continue
        yy, xx = np.where(lab == k); feet.append((float(xx[yy == yy.max()].mean()), float(yy.max())))
    S0 = np.zeros((FH, FW), np.float32); gy, gx = np.mgrid[0:FH, 0:FW].astype(np.float32)
    for fx, fy in feet:
        S0 += 0.35 * np.exp(-((gx - fx) / (0.035 * E_h)) ** 2 / 2 - ((gy - fy) / (0.012 * E_h)) ** 2 / 2)
    if feet:
        mx = np.mean([f[0] for f in feet]); my = max(f[1] for f in feet)
        S0 += 0.16 * np.exp(-((gx - mx) / (0.16 * E_h)) ** 2 / 2 - ((gy - my + 0.01 * E_h) / (0.025 * E_h)) ** 2 / 2)
    S0 = np.clip(S0, 0, 0.6)
    colbot = np.where(ea.max(0) > 0.5, FH - 1 - np.argmax(ea[::-1] > 0.5, axis=0), -10 ** 6).astype(np.float32)
    grass = C.get("grass", 0.0)                                   # how far up the legs the grass reaches (× easel height)
    W0 = np.clip(1 - (colbot[None, :] - gy) / max(1.0, grass * E_h), 0, 1) ** 2 * (gy <= colbot[None, :]) if grass else None
    bg0 = cv2.warpAffine(bg, np.float32([[1, 0, -(bg.shape[1] - FW) / 2], [0, 1, -(bg.shape[0] - FH) / 2]]), (FW, FH))
    if C.get("light_match", True) and feet:
        fx0, fy0 = int(np.mean([f[0] for f in feet])), int(min(FH - 1, max(f[1] for f in feet)))
        r0 = int(0.12 * E_h); patch = bg0[max(0, fy0 - r0):fy0 + 1, max(0, fx0 - r0):fx0 + r0]
        if patch.size:
            cg = patch.reshape(-1, 3).mean(0); al = ea > 0.5
            m = easel_f[..., :3][al].mean(0)
            easel_f[..., :3] = np.clip((m + 0.9 * (easel_f[..., :3] - m)) * (0.85 + 0.15 * cg), 0, 1)
    # camera with "zoom_lock" s: the wide shot holds while the easel is painted, then one push in (cam), slow at both
    # ends and smooth in log-scale (the small canvas grows ×4–7); up to ×s the ground zooms with the easel so its feet
    # stay put on the grass, after that the background falls behind (a third of the zoom) and goes out of focus
    r_zoom = float((np.linalg.norm(Qf1[3] - Qf1[0]) + np.linalg.norm(Qf1[2] - Qf1[1])) / (np.linalg.norm(Qf0[3] - Qf0[0]) + np.linalg.norm(Qf0[2] - Qf0[1])))
    c0 = Qf0.mean(0); c1 = Qf1.mean(0); lock = C.get("zoom_lock")
    if lock: Lw, Lr = math.log(lock), math.log(r_zoom); lin_w = (lock - 1) / (r_zoom - 1)
    bt = tip_of(brush, (-1, 1)); wt = tip_of(wand, (-1, -1))
    # the paint on the brush tip takes the colour it is laying down (the generated brush is loaded with blue)
    bhsv = cv2.cvtColor((brush[..., :3] * 255).astype(np.uint8), cv2.COLOR_RGB2HSV).astype(np.float32)
    paintmask = ((bhsv[..., 0] > 95) & (bhsv[..., 0] < 140) & (bhsv[..., 1] > 90)).astype(np.float32)
    paintmask = cv2.GaussianBlur(paintmask, (0, 0), 2)[..., None]
    blum = (brush[..., :3] @ np.float32([0.299, 0.587, 0.114]))[..., None]
    target_col = cv2.GaussianBlur(load_rgb(C["target"]), (0, 0), 25) if C.get("target") else None
    def brush_in(col):
        if not C.get("tint_brush", True): return brush            # the painted brushes carry their own colours
        out = brush.copy()
        tinted = np.clip(np.asarray(col, np.float32) * (0.55 + 1.6 * blum), 0, 1)
        out[..., :3] = brush[..., :3] * (1 - paintmask) + tinted * paintmask
        return out
    strokes = json.load(open(C["strokes"]))["strokes"]
    B = Brush(strokes, (pw, ph))
    cam = C["camera"]                                             # [t0, t1] of the push-in
    live_t0 = C["live_start"]; wand_path = C.get("wand_path", [])
    T0, T1 = C["range"] if "range" in C else C["music"]; N = int(round((T1 - T0) * FPS))
    paint_t0 = C.get("paint_t0", T0)
    if "music" in C and "wav" in C:
        cmd = ["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{FW}x{FH}", "-r", str(FPS), "-i", "-",
               "-ss", str(T0), "-t", str(T1 - T0), "-i", C["wav"], "-filter:a", f"afade=t=out:st={T1 - T0 - 3}:d=3",
               "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart", "-shortest", out]
    else:                                                         # a film section: picture only, the music goes on once at the end
        cmd = ["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{FW}x{FH}", "-r", str(FPS), "-i", "-",
               "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p", out]
    enc = None if stills else subprocess.Popen(cmd, stdin=subprocess.PIPE)
    want = None if not stills else {int(round((x - T0) * FPS)) for x in stills}
    if stills: os.makedirs(out, exist_ok=True)
    rng = np.random.default_rng(9); dust = []; magic_level = 0.0                      # wand dust particles: [x, y, vx, vy, born, size]
    for n in range(N):
        t = T0 + n / FPS
        if want is not None and n not in want and not (wand_path and live_t0 - 1.5 <= t): continue
        if lock:
            g = smoothstep((t - cam[0]) / (cam[1] - cam[0])); g = g * g * (3 - 2 * g)   # extra-slow start and arrival
            Lt = Lr * g; sc = math.exp(Lt); c = g; lin = (sc - 1) / (r_zoom - 1)
            zc = c0 + (c1 - c0) * lin                                 # zoom about one fixed point: the canvas comes to the centre
            fix = np.clip((lin - lin_w) / (1 - lin_w), 0, 1) ** 2         # the canvas squares up to the screen only in the push
            Qt = (zc + sc * (Qf0 - c0) + (Qf1 - (c1 + r_zoom * (Qf0 - c0))) * fix).astype(np.float32)
            z = min(2.6, math.exp(min(Lt, Lw) + 0.35 * max(0.0, Lt - Lw)))   # the ground keeps with the easel at first
            blur = 0.6 * min(1.0, Lt / Lw) + 7 * max(0.0, (Lt - Lw) / (Lr - Lw))
        else:
            c = smoothstep((t - cam[0]) / (cam[1] - cam[0]))
            c = c * c * (3 - 2 * c)                                   # extra-slow start and arrival
            Qt = (Qf0 + (Qf1 - Qf0) * c).astype(np.float32)
            zc = Qt.mean(0); z = 1 + 0.35 * c * (cw / (Qf0[1, 0] - Qf0[0, 0]) - 1)   # background: a third of the zoom
            blur = 0.5 + 7 * c if c > 0.01 else 0
        Hc = cv2.getPerspectiveTransform(Qf0, Qt)
        M = np.float32([[z, 0, zc[0] - z * (c0[0] + (bg.shape[1] - FW) / 2)], [0, z, zc[1] - z * (c0[1] + (bg.shape[0] - FH) / 2)]])
        if bg_loop:
            bgf = load_rgb(bg_loop[n % len(bg_loop)]); bgf = cv2.resize(bgf, (bg.shape[1], bg.shape[0]), interpolation=cv2.INTER_CUBIC)
        else: bgf = bg
        frame = cv2.warpAffine(bgf, M, (FW, FH), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        if blur > 0.05: frame = cv2.GaussianBlur(frame, (0, 0), blur)
        ground = frame.copy()
        if feet: frame = frame * (1 - cv2.warpPerspective(S0, Hc, (FW, FH))[..., None])
        e = cv2.warpPerspective(easel_f, Hc, (FW, FH), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0))
        frame = frame * (1 - e[..., 3:4]) + e[..., :3] * e[..., 3:4]
        if W0 is not None:                                        # grass blades in front of the feet
            gg = cv2.cvtColor(ground, cv2.COLOR_RGB2GRAY)
            tex = cv2.GaussianBlur(np.clip(np.abs(gg - cv2.GaussianBlur(gg, (0, 0), 2.5)) * 14, 0, 1), (0, 0), 0.8)
            k = (cv2.warpPerspective(W0.astype(np.float32), Hc, (FW, FH)) * e[..., 3] * tex)[..., None]
            frame = frame * (1 - k) + ground * k
        # the canvas
        src = paint[int(np.clip(round((t - paint_t0) * FPS), 0, len(paint) - 1))] if t < live_t0 else live[min(int(round((t - live_t0) * FPS)), len(live) - 1)]
        pic = load_rgb(src) * (lightmap if t < live_t0 else (1 + (lightmap - 1) * (1 - c)))
        Hp = cv2.getPerspectiveTransform(rect, Qt)
        warped = cv2.warpPerspective(pic, Hp, (FW, FH), flags=cv2.INTER_AREA if c < 0.5 else cv2.INTER_LINEAR)
        m = cv2.warpPerspective(np.ones((ph, pw), np.float32), Hp, (FW, FH), flags=cv2.INTER_LINEAR)[..., None]
        frame = frame * (1 - m) + warped * m
        scale_pic = np.linalg.norm(Qt[1] - Qt[0]) / pw            # screen px per picture px (roughly)
        # the brush
        st = B.at(t) if t < (cam[1] - 0.8 if lock else cam[0] + 1.0) else None
        if st is not None:
            x, y, lift, ang = st
            p = cv2.perspectiveTransform(np.array([[[x, y]]], np.float32), Hp)[0, 0]
            bs = C.get("brush_scale", 0.55) * (1 + 0.1 * lift) * scale_pic * pw / brush.shape[1]
            rot = -6 * math.sin(ang) * (1 - lift) + 4 * lift
            col = target_col[int(np.clip(y, 0, ph - 1)), int(np.clip(x, 0, pw - 1))] if target_col is not None else (0.35, 0.4, 0.6)
            brush_now = brush_in(col)
            up = 70 * lift * scale_pic * 2.2                       # lifted toward the viewer
            tip = (p[0], p[1] - up)
            # shadow: same brush pivoted about the point under the tip (the light is upper left), so it meets the
            # bristles when they touch the canvas and slides away, softer, as the brush lifts
            ks = max(0.2, np.linalg.norm(Qt[3] - Qt[0]) / 500)        # tuned on a ~500 px canvas
            sh, sx, sy = sprite_at(brush_now, bt, (p[0] + 34 * lift * ks, p[1] + 26 * lift * ks), bs * 1.02, rot - 9)
            shadow = np.zeros_like(sh); shadow[..., :3] = 0.06
            shadow[..., 3] = cv2.GaussianBlur(sh[..., 3], (0, 0), (2.5 + 9 * lift) * ks) * (0.42 - 0.22 * lift)
            over(frame, shadow, sx, sy)
            spr, sx, sy = sprite_at(brush_now, bt, tip, bs, rot)
            over(frame, spr, sx, sy)
        # the wand and its dust
        if t >= live_t0 - 1.2 and wand_path:
            pts = [w for w in wand_path if w[0] <= t]
            if pts:
                k = len(pts) - 1
                if k + 1 < len(wand_path):
                    a, b = wand_path[k], wand_path[k + 1]; f = smoothstep((t - a[0]) / (b[0] - a[0]))
                    u, v = a[1] + (b[1] - a[1]) * f, a[2] + (b[2] - a[2]) * f
                    on = a[3] if len(a) > 3 else 1
                else: u, v, on = wand_path[-1][1], wand_path[-1][2], 0
                magic = magic_level = min(1.0, max(0.0, magic_level + (1 if on else -1) / (0.35 * FPS)))   # fades in/out ~0.35 s
                p = cv2.perspectiveTransform(np.array([[[u * pw, v * ph]]], np.float32), Hp)[0, 0]
                for _ in range(int(round(5 * magic))):                    # dust only while the painting is waking up
                    dust.append([p[0], p[1], rng.normal(0, 22), rng.normal(16, 12), t, rng.uniform(1.2, 3.4)])
                ws = C.get("wand_scale", 0.42) * FH / wand.shape[0]
                spr, sx, sy = sprite_at(wand, wt, (p[0], p[1]), ws, 4 * math.sin(t * 1.7))
                over(frame, spr, sx, sy)
                tw = (0.18 + 0.82 * magic) * (0.75 + 0.25 * math.sin(t * 9.0))   # the crystal lights up while it works
                R = 26; yy, xx = np.mgrid[-R:R + 1, -R:R + 1]
                g = (np.exp(-(xx * xx + yy * yy) / (2 * 7.0 ** 2)) + 0.5 * np.exp(-(yy * yy) / 2.0 - np.abs(xx) / 9.0)
                     + 0.5 * np.exp(-(xx * xx) / 2.0 - np.abs(yy) / 9.0))[..., None] * tw * 0.8
                x0, y0 = int(p[0]) - R, int(p[1]) - R
                if 0 <= x0 and x0 + 2 * R + 1 <= FW and 0 <= y0 and y0 + 2 * R + 1 <= FH:
                    reg = frame[y0:y0 + 2 * R + 1, x0:x0 + 2 * R + 1]; reg[:] = reg + (np.array([1.0, 0.95, 0.8]) - reg) * np.clip(g, 0, 1)
        alive = []
        for d in dust:                                            # golden dust: drifts down, twinkles, fades in ~1.4 s
            age = t - d[4]
            if age > 1.4: continue
            x, y = d[0] + d[2] * age, d[1] + d[3] * age + 6 * age * age
            k = (1 - age / 1.4) * (0.6 + 0.4 * math.sin(age * 23 + d[5] * 7))
            r = d[5]
            x0, y0 = int(x - 6), int(y - 6)
            if 0 <= x0 < FW - 13 and 0 <= y0 < FH - 13:
                yy, xx = np.mgrid[-6:7, -6:7]
                g = np.exp(-(xx * xx + yy * yy) / (2 * r * r))[..., None] * k
                reg = frame[y0:y0 + 13, x0:x0 + 13]
                reg[:] = reg + (np.array([1.0, 0.88, 0.55]) - reg) * g
            alive.append(d)
        dust = alive
        img8 = (np.clip(frame, 0, 1) * 255 + .5).astype(np.uint8)
        if enc: enc.stdin.write(img8.tobytes())
        elif n in want: cv2.imwrite(os.path.join(out, f"t{t:06.2f}.jpg"), cv2.cvtColor(img8, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 90])
    if enc: enc.stdin.close(); enc.wait()
    print(out, N, "frames")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], [float(x) for x in sys.argv[3].split(",")] if len(sys.argv) > 3 else None)
