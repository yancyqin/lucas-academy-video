#!/usr/bin/env python3
"""Compose one section of the 焰火 film from its plan.json and the captured living-painting frames.

Per frame: the realistic photo dims (the light falls) and dissolves into the living painting; the camera frames the
painting on a dark surround lit by a blurred glow of the painting itself; a painted tool glides in, its flame (or sparks,
or ember) is drawn here so it can flicker, its light already falls on the painting (lamps in the plan), it touches the
fuse — a sputter — and the first rocket rises. Writes feux/film/<id>/section.mp4 (1920x1080, 30 fps, no audio).

    python film_compose.py <id> [--from K --to K --preview]
"""
import argparse, json, math, os, subprocess
import numpy as np, cv2

DATA = "/Users/yqin/repo/playground/lucas-academy-video-data/debussy-impressions"
FILM = f"{DATA}/feux/film"; REAL = f"{DATA}/feux/real/aligned"; TOOLS = f"{DATA}/feux/tools/keyed"
W, H = 1920, 1080

def smooth(x): x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)
def ramp(t, a, b): return smooth((t - a) / (b - a)) if b > a else float(t >= b)

def screen(dst, add):
    """dst, add: float32 0..1 — light added the way light adds (never a hard clip)."""
    return 1 - (1 - dst) * (1 - np.clip(add, 0, 1))

# ---------------------------------------------------------------- flames (all point up; drawn into a local patch)
def teardrop(h, t, seed, width=0.30, sway=0.16, white=0.85):
    """A soft painterly flame of height h px: returns (rgb patch float32, base x, base y in the patch)."""
    h = max(6.0, h); pw, ph = int(h * 3.0) | 1, int(h * 3.2) | 1           # roomy: every falloff reaches zero inside
    bx, by = pw / 2, ph * 0.66
    ys, xs = np.mgrid[0:ph, 0:pw].astype(np.float32)
    he = h * (1 + 0.08 * math.sin(t * 17.3 + seed) + 0.05 * math.sin(t * 29.1 + 2 * seed))
    v = (by - ys) / he
    sw = (0.6 * math.sin(t * 8.7 + seed) + 0.4 * math.sin(t * 13.9 + 1.7 * seed)) * sway * he * np.clip(v, 0, None) ** 2
    u = (xs - bx - sw) / (width * he)
    prof = np.where(v >= 0, np.sin(np.pi * np.clip(v, 0, 1) ** 0.55) * (1 - 0.3 * np.clip(v, 0, 1)), np.exp(-(v / 0.1) ** 2) * 0.55) + 1e-3
    fall = np.clip((v + 0.12) / 0.17, 0, 1) * (1 - np.clip((v - 0.55) / 0.55, 0, 1))
    D = np.exp(-2.4 * (u / prof) ** 2) * fall
    D2 = np.exp(-2.6 * (u / (0.45 * prof)) ** 2) * np.clip((v + 0.08) / 0.12, 0, 1) * (1 - np.clip((v - 0.1) / 0.4, 0, 1))
    G = np.exp(-(((xs - bx) / (0.7 * he)) ** 2 + ((ys - (by - 0.35 * he)) / (0.7 * he)) ** 2))
    rgb = (D[..., None] * np.float32([1.0, 0.48, 0.12]) + white * D2[..., None] * np.float32([1.0, 0.92, 0.7])
           + 0.22 * G[..., None] * np.float32([1.0, 0.55, 0.2]))
    rgb = cv2.GaussianBlur(rgb, (0, 0), max(0.6, 0.035 * h))
    return rgb, bx, by

def stamp(dst, patch, x, y, gain=1.0):
    """screen-add patch (rgb) so that its anchor (ax, ay) lands at (x, y). patch = (rgb, ax, ay)."""
    rgb, ax, ay = patch
    x0, y0 = int(round(x - ax)), int(round(y - ay)); ph, pw = rgb.shape[:2]
    X0, Y0, X1, Y1 = max(0, x0), max(0, y0), min(W, x0 + pw), min(H, y0 + ph)
    if X1 <= X0 or Y1 <= Y0: return
    dst[Y0:Y1, X0:X1] = screen(dst[Y0:Y1, X0:X1], rgb[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0] * gain)

def glow(dst, x, y, r, col, amp):
    r = max(2, r); n = int(r * 2.2)
    ys, xs = np.mgrid[-n:n + 1, -n:n + 1].astype(np.float32)
    g = np.exp(-(xs * xs + ys * ys) / (2 * (r / 1.6) ** 2))[..., None] * np.float32(col) * amp
    stamp(dst, (g, n, n), x, y)

def sparks(dst, x, y, rng, n, lmin, lmax, up=0.0, col=(1.0, 0.85, 0.5), amp=1.0, width=1.4):
    """Short bright streaks flung out from (x, y); `up` biases them upward (a fountain)."""
    n = int(n)
    if n <= 0: return
    R = int(lmax * 1.3) + 4; layer = np.zeros((2 * R + 1, 2 * R + 1, 3), np.float32)
    for _ in range(n):
        a = rng.uniform(0, 2 * math.pi)
        if up: a = -math.pi / 2 + rng.normal(0, 1.0 - 0.6 * up)
        L = rng.uniform(lmin, lmax); r0 = L * rng.uniform(0.2, 0.5)
        p0 = (R + math.cos(a) * r0, R + math.sin(a) * r0); p1 = (R + math.cos(a) * L, R + math.sin(a) * L + 0.15 * L * L / max(lmax, 1))
        b = rng.uniform(0.5, 1.0) * amp
        cv2.line(layer, (int(p0[0] * 4), int(p0[1] * 4)), (int(p1[0] * 4), int(p1[1] * 4)), tuple(float(c * b) for c in col), max(1, int(round(width))), cv2.LINE_AA, 2)
    layer = cv2.GaussianBlur(layer, (0, 0), 0.9)
    stamp(dst, (layer, R, R), x, y)

def smoke(over, x, y, Hd, t, seed, amp, col=(0.62, 0.64, 0.72)):
    """A thin wandering thread of smoke rising from (x, y), alpha-blended (not light)."""
    L = 0.22 * Hd; n = 28
    pts = []
    for i in range(n):
        s = i / (n - 1)
        px = x + math.sin(s * 5.5 + t * 1.3 + seed) * 0.014 * Hd * s + 0.03 * Hd * s * s * math.sin(seed)
        py = y - s * L
        pts.append((int(px * 4), int(py * 4)))
    layer = np.zeros(over.shape[:2], np.float32)
    cv2.polylines(layer, [np.array(pts, np.int32)], False, 1.0, max(1, int(0.004 * Hd)), cv2.LINE_AA, 2)
    layer = cv2.GaussianBlur(layer, (0, 0), 0.004 * Hd + 1)
    a = np.clip(layer * amp, 0, 1)[..., None]
    over[:] = over * (1 - a) + np.float32(col) * a

def draw_flame(frame, kind, x, y, Hd, t, I, I0, axis, rng, since):
    """kind = match | wick | taper | sparkler | incense | portfire | torch; (x, y) = the lighting end on screen."""
    k = I / max(I0, 1e-3)
    if k <= 0.01: return
    if kind in ("match", "wick", "taper"):
        h = {"match": 0.05, "wick": 0.036, "taper": 0.042}[kind] * Hd
        if kind == "match" and since < 0.3:                       # the strike: a flare and a spray of sulphur sparks
            h *= 1 + 1.2 * (1 - since / 0.3)
            sparks(frame, x, y, rng, 22 * (1 - since / 0.3), 0.01 * Hd, 0.05 * Hd, col=(1.0, 0.8, 0.45), amp=1.2)
        stamp(frame, teardrop(h, t, 3.1), x, y, min(1.4, k))
        glow(frame, x, y - 0.4 * h, 2.6 * h, (1.0, 0.6, 0.25), 0.22 * min(1.3, k))
    elif kind == "torch":
        h = 0.07 * Hd
        stamp(frame, teardrop(h, t, 5.3, width=0.36, sway=0.2), x, y, min(1.3, k))
        stamp(frame, teardrop(0.6 * h, t * 1.13, 9.7, width=0.3, sway=0.25), x - 0.12 * h, y + 0.05 * h, 0.7 * min(1.3, k))
        stamp(frame, teardrop(0.55 * h, t * 0.91, 1.9, width=0.3, sway=0.25), x + 0.13 * h, y + 0.05 * h, 0.7 * min(1.3, k))
        glow(frame, x, y - 0.4 * h, 2.4 * h, (1.0, 0.55, 0.2), 0.26 * min(1.3, k))
        if rng.random() < 0.5: sparks(frame, x, y - 0.6 * h, rng, 2, 0.01 * Hd, 0.03 * Hd, up=0.8, col=(1.0, 0.7, 0.35))
    elif kind == "portfire":
        h = 0.06 * Hd
        stamp(frame, teardrop(h, t, 7.7, width=0.26, sway=0.1, white=1.2), x, y, min(1.4, k))
        glow(frame, x, y - 0.3 * h, 2.8 * h, (1.0, 0.75, 0.4), 0.3 * min(1.3, k))
        sparks(frame, x, y, rng, 6 * k, 0.01 * Hd, 0.045 * Hd, col=(1.0, 0.9, 0.65), amp=1.1)
    elif kind == "sparkler":
        glow(frame, x, y, 0.012 * Hd, (1.0, 0.97, 0.9), 1.4 * k)
        glow(frame, x, y, 0.06 * Hd, (1.0, 0.8, 0.5), 0.35 * k)
        sparks(frame, x, y, rng, 46 * min(1.2, k), 0.012 * Hd, 0.075 * Hd, col=(1.0, 0.9, 0.62), amp=1.15, width=1.2)
    elif kind == "incense":
        pulse = 0.85 + 0.15 * math.sin(t * 3.1)
        glow(frame, x, y, 0.009 * Hd, (1.0, 0.6, 0.3), 2.2 * k * pulse)
        glow(frame, x, y, 0.05 * Hd, (1.0, 0.42, 0.15), 0.42 * k * pulse)
        if rng.random() < 0.35: sparks(frame, x, y, rng, 1, 0.004 * Hd, 0.012 * Hd, col=(1.0, 0.6, 0.3))

# ---------------------------------------------------------------- the section
def main():
    ap = argparse.ArgumentParser(); ap.add_argument("sid"); ap.add_argument("--from", dest="k0", type=int, default=0)
    ap.add_argument("--to", dest="k1", type=int, default=None); ap.add_argument("--preview", action="store_true")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    P = json.load(open(f"{FILM}/{a.sid}/plan.json")); T = P["tool"]; frames = P["frames"]
    k1 = a.k1 if a.k1 is not None else len(frames)
    rd = lambda p: cv2.imread(p)[..., ::-1]                         # everything here is RGB
    live0 = rd(f"{FILM}/{a.sid}/frames-live/{a.k0:05d}.jpg")
    lh, lw = live0.shape[:2]; aspect = lw / lh
    photo = cv2.resize(rd(f"{REAL}/{a.sid}.png"), (lw, lh), interpolation=cv2.INTER_AREA).astype(np.float32) / 255
    sprite = cv2.imread(f"{TOOLS}/{a.sid}.png", cv2.IMREAD_UNCHANGED).astype(np.float32) / 255
    sprite = np.dstack([sprite[..., 2::-1], sprite[..., 3]])
    meta = json.load(open(f"{TOOLS}/tools.json"))[a.sid]
    tip = np.float32(meta["tip"]); end = np.float32(meta["end"])
    if T["side"] == "left":                                         # mirrored: the lighting end at lower RIGHT
        sprite = sprite[:, ::-1].copy(); tip[0] = sprite.shape[1] - 1 - tip[0]; end[0] = sprite.shape[1] - 1 - end[0]
    sprite_rgb = sprite[..., :3]
    grey = sprite_rgb.mean(-1, keepdims=True); sprite_rgb = sprite_rgb * 0.85 + grey * 0.15      # a little faded, dreamy
    sprite_a = cv2.GaussianBlur(sprite[..., 3], (0, 0), 0.7)
    yy, xx = np.mgrid[0:sprite.shape[0], 0:sprite.shape[1]].astype(np.float32)
    warm_fall = np.exp(-np.hypot(xx - tip[0], yy - tip[1]) / meta["length"] / 0.3)[..., None] * np.float32([1.15, 0.8, 0.45])
    from film_plan import FLAME
    I0 = FLAME[T["flame"]][0]
    out = a.out or (f"{FILM}/{a.sid}/preview.mp4" if a.preview else f"{FILM}/{a.sid}/section.mp4")
    ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(P["fps"]), "-i", "-",
                           "-c:v", "libx264", "-crf", "16" if not a.preview else "21", "-preset", "medium", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    rng = np.random.default_rng(7)
    touch, fuse = T["touch"], T["fuse"]; cxu, cyv = T["contact"]
    for k in range(a.k0, k1):
        f = frames[k]; t = f["t"]
        live = rd(f"{FILM}/{a.sid}/frames-live/{k:05d}.jpg").astype(np.float32) / 255
        # 1) the light falls on the real scene, which melts into the painting
        g = ramp(t, *P["dim"])
        ph = photo * (1 - g * (1 - np.float32([0.36, 0.42, 0.62])))                        # dusk: darker, bluer
        ph = ph * (1 - 0.25 * g) + ph.mean(-1, keepdims=True) * 0.25 * g
        al = ramp(t, *P["dissolve"])
        pic = ph * (1 - al) + live * al
        # 2) camera
        z, cx, cy = f["cam"]; Hd = H * z; Wd = Hd * aspect
        X0, Y0 = W / 2 - cx * Wd, H / 2 - cy * Hd
        M = np.float32([[Wd / lw, 0, X0], [0, Hd / lh, Y0]])
        body = cv2.warpAffine(pic, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
        mask = cv2.warpAffine(np.ones((lh, lw), np.float32), M, (W, H), flags=cv2.INTER_LINEAR)
        mask = cv2.GaussianBlur(mask, (0, 0), 1.2)
        # surround: the painting's own light, blurred far out and dimmed — the dark room it glows in
        small = cv2.resize(pic, (96, int(96 / aspect)), interpolation=cv2.INTER_AREA)
        small = cv2.GaussianBlur(small, (0, 0), 6)
        bg = cv2.resize(small, (W, H), interpolation=cv2.INTER_LINEAR) * 0.26
        shadow = cv2.GaussianBlur(mask, (0, 0), 22)
        bg = bg * (1 - 0.55 * shadow[..., None])
        frame = bg * (1 - mask[..., None]) + body * mask[..., None]
        # 3) the tool
        ta = f["tool"]["a"]
        if ta > 0.01:
            u, v = f["tool"]["u"], f["tool"]["v"]
            tx, ty = X0 + u * Wd, Y0 + v * Hd
            L = T["length"] * Hd; s = L / meta["length"]
            ang = math.radians(f["tool"]["rot"]) * (-1 if T["side"] == "left" else 1)
            c, sn = math.cos(ang) * s, math.sin(ang) * s
            A = np.float32([[c, -sn, 0], [sn, c, 0]]); A[:, 2] = np.float32([tx, ty]) - A[:, :2] @ tip
            night_amb = 1 - 0.5 * ramp(t, *P["dim"])
            I = f["tool"]["I"]
            spr = sprite_rgb.copy()
            if I > 0.01:                                                                # lit warm near its flame
                spr = spr * (night_amb + (I / max(I0, 1e-3)) * warm_fall)
            else:
                spr = spr * night_amb
            rgbw = cv2.warpAffine(spr, A, (W, H), flags=cv2.INTER_LINEAR)
            aw = cv2.warpAffine(sprite_a, A, (W, H), flags=cv2.INTER_LINEAR)[..., None] * 0.96 * ta
            frame = frame * (1 - aw) + rgbw * aw
            # 4) its flame
            ax_ = (tip - end); ax_ = ax_ / (np.linalg.norm(ax_) + 1e-6)
            fx, fy = tx, ty
            if T["flame"] == "sparkler":                                              # the burning point creeps up the wire
                q = tip - ax_ * min(0.5, max(0.0, t - T["ignite"]) * 0.028) * meta["length"]
                fx, fy = A[:, :2] @ q + A[:, 2]
            draw_flame(frame, T["flame"], fx, fy, Hd, t, I, I0, ax_, rng, t - T["ignite"])
            if T["flame"] == "incense" and I > 0.01:
                smoke(frame, fx, fy, Hd, t, 1.3, 0.6 * min(1, I / I0) * ta)
        # 5) the fuse sputters where it was touched, then the rocket (drawn in the painting) rises
        if touch - 0.05 <= t < touch + fuse + 0.1:
            sx, sy = X0 + cxu * Wd, Y0 + cyv * Hd
            e = ramp(t, touch - 0.05, touch + 0.1) * (1 - ramp(t, touch + fuse - 0.05, touch + fuse + 0.1))
            sparks(frame, sx, sy, rng, 16 * e, 0.008 * Hd, 0.035 * Hd, up=0.7, col=(1.0, 0.82, 0.45), amp=1.2)
            glow(frame, sx, sy, 0.03 * Hd, (1.0, 0.7, 0.35), 0.5 * e)
        # 6) fades
        fade = 1.0
        if P.get("fade_in"): fade *= ramp(t, *P["fade_in"])
        if P.get("fade_out"): fade *= 1 - ramp(t, *P["fade_out"])
        frame = frame * fade
        ff.stdin.write((np.clip(frame, 0, 1) * 255 + 0.5).astype(np.uint8).tobytes())
        if k % 150 == 0: print(a.sid, k, f"t={t:.2f}", flush=True)
    ff.stdin.close(); ff.wait()
    print("->", out)

if __name__ == "__main__":
    main()
