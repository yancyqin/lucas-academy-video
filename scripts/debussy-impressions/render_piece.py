#!/usr/bin/env python3
"""Render one piece of the Debussy film from its edit list (edits/NN-*.json) with the music.

Every shot starts at its `at` (the musical cut). The previous shot cross-fades into it over `xfade`
seconds ending at `at`, so the new image is fully there when the phrase starts. Inside a shot:
the aligned photo (real/aligned/<id>.png) holds `photo_hold` s after the cut, then dissolves into the
painting over `reveal` s; the painting holds until the next cut. A slow push-in (`push_per_min`,
toward the optional `focus` point) runs through the whole shot and is shared by photo and painting,
so they stay registered while dissolving. Shots without a photo show the painting at once.
A shot's optional "anim" (a painting-framed clip from prep_anim.py) plays near the end of the shot and then
holds its last frame for `anim_freeze` s (default 4) up to the next cut; a 1 s cross-fade brings it in from
the still painting (its first frame is the painting). The still before it is never shorter than anim_min_still.
A shot may name its own "photo" and "painting" (paths under DATA); when the painting file does not exist
yet, the photo holds for the whole shot. With "photo_hold_frac"/"reveal_frac" in the edit list, hold and reveal scale with the shot's length
(clamped by photo_hold_range / reveal_range); a shot's own photo_hold / reveal still overrides.

Style "breath" (v8): no reveal, no freeze - the whole picture breathes with the melody (breath_curve.py: darker,
softer and faded in the breaths, bright and clear as the melody rises) and each photo becomes its painting a little
more on every in-breath. Edit-list options for music sync: "xfade_mid" 0.5 centres each cross-fade on its cut; a shot's "reveal_at"
(absolute seconds) starts the photo -> painting dissolve on that note.

  --review   draw small grey labels (number + title, "照片待生成", "动画待做") for preview copies
usage: .venv-reframe/bin/python render_piece.py edits/01-mer.json OUT.mp4 [--review] [--from S --to S]
"""
import argparse, json, os, subprocess
import cv2, numpy as np
from PIL import Image, ImageDraw, ImageFont

DATA = "/Users/yqin/repo/playground/lucas-academy-video-data/debussy-impressions"
W, H, FPS = 1920, 1080, 30
BG = (16, 15, 14)   # BGR, near black with a warm tint
FONT = "/System/Library/Fonts/STHeiti Light.ttc"

def smooth(u):
    u = min(max(u, 0.0), 1.0); return u * u * (3 - 2 * u)

class Shot:
    def __init__(self, s, ed, end_t, idx, n):
        self.s, self.i, self.n = s, idx, n
        self.at = s["at"]; self.end = end_t
        L = end_t - s["at"]                                            # this shot's own time, cut to next cut
        if "photo_hold_frac" in ed:                                    # proportional rhythm (owner 2026-10-14):
            lo, hi = ed.get("photo_hold_range", [2, 4])                # longer transformation, shorter final still
            self.hold = s.get("photo_hold", min(max(ed["photo_hold_frac"] * L, lo), hi))
            lo, hi = ed.get("reveal_range", [8, 36])
            self.reveal = s.get("reveal", min(max(ed["reveal_frac"] * L, lo), hi))
        else:
            self.hold = s.get("photo_hold", ed["photo_hold"]); self.reveal = s.get("reveal", ed["reveal"])
        if "reveal_at" in s: self.hold = max(0.5, s["reveal_at"] - s["at"])  # dissolve starts on a chosen accent
        sid = s["id"]                                                  # explicit paths (月光: photo first,
        pp = f"{DATA}/" + s.get("painting", f"art/{sid}.jpg")          # AI painting made from it)
        ph = f"{DATA}/" + s.get("photo", f"real/aligned/{sid}.png")
        if s.get("photo_final") and os.path.exists(f"{DATA}/{s['photo_final']}"): ph = f"{DATA}/{s['photo_final']}"   # Codex-widened 16:9 photo
        P = cv2.imread(pp, cv2.IMREAD_COLOR) if os.path.exists(pp) else None
        R = cv2.imread(ph, cv2.IMREAD_COLOR) if os.path.exists(ph) and not s.get("no_photo") else None
        self.no_paint = P is None                                      # painting not made yet: the photo holds
        if self.no_paint: P, R = R, None                               # the whole shot ("油画待生成" in --review)
        self.key, self.glow_thr = 0.3, 0.7
        self.mix = None
        if ed.get("style") == "breath" and BREATH:                      # v8 (owner: 按照旋律来好像在呼吸一样，不用定格)
            bb, bf = BREATH["b"], BREATH["fps"]
            seg_all = bb[int(self.at * bf):max(int(self.end * bf), int(self.at * bf) + 2)]
            mb = float(np.mean(seg_all)) if len(seg_all) else 0.5
            mL = float(cv2.cvtColor(P, cv2.COLOR_BGR2GRAY).mean()) / 255
            g = min(max((0.30 + 0.10 * (mb - 0.5)) / max(mL, 0.02), 0.75), 1.35)   # equal footing; the breath does the rest
            P = expose(P, g)
            if R is not None:                                           # match the photo to its painting, so turning into the
                lP = float(cv2.cvtColor(P, cv2.COLOR_BGR2GRAY).mean())  # painting never drifts the brightness against the breath
                lR = float(cv2.cvtColor(R, cv2.COLOR_BGR2GRAY).mean())
                R = expose(R, min(max(lP / max(lR, 1.0), 0.6), 2.3))
            if R is not None:                                           # the photo becomes the painting a little more
                i0 = int((self.at + 1.0) * bf)                          # on every in-breath, fully by 65 % of the shot
                i1 = max(int((self.at + 0.65 * (self.end - self.at)) * bf), i0 + bf)
                seg = np.array(bb[max(i0 - 1, 0):i1 + 1], np.float64)
                inc = np.maximum(np.diff(seg), 0) + 0.0015
                cum = np.cumsum(inc); cum /= cum[-1]
                self.mix = (i0, cum * cum * (3 - 2 * cum))
        if ed.get("style") == "reveal":                                 # v7: pre-expose so brightness follows the music,
            mL = float(cv2.cvtColor(P, cv2.COLOR_BGR2GRAY).mean()) / 255   # not each image's own key
            rr = reg_at(s["reveal_at"]) if "reveal_at" in s else 0.5          # music sitting high at the reveal -> brighter
            g = min(max((0.28 + 0.14 * s.get("intensity", 0.6) + 0.10 * (rr - 0.5)) / max(mL, 0.02), 0.75), 1.35)
            P = expose(P, g); R = expose(R, g) if R is not None else None
            gr = cv2.cvtColor(P, cv2.COLOR_BGR2GRAY)
            self.key = float(gr.mean()) / 255; self.glow_thr = max(0.35, float(np.percentile(gr, 85)) / 255)
        k = min(W / P.shape[1], H / P.shape[0])                       # contain in frame
        self.bw, self.bh = P.shape[1] * k, P.shape[0] * k
        self.x0, self.y0 = (W - self.bw) / 2, (H - self.bh) / 2
        self.xf = s.get("_xf", ed["xfade"])                            # this shot's incoming dissolve
        length = self.end - (self.at - self.xf)
        self.zmax = 1 + ed["push_per_min"] * length / 60
        self.pre = 1.1 * self.zmax * (1.05 if ed.get("style") == "reveal" else 1.0)   # pre-scale with headroom (+ punch)
        sz = (int(round(self.bw * self.pre)), int(round(self.bh * self.pre)))
        self.P = cv2.resize(P, sz, interpolation=cv2.INTER_AREA)
        self.R = cv2.resize(R, sz, interpolation=cv2.INTER_AREA) if R is not None else None
        fx, fy = s.get("focus") or (bright_focus(P) if ed.get("style") == "reveal" else (0.5, 0.5))
        self.F = (self.x0 + fx * self.bw, self.y0 + fy * self.bh)
        self.t_start = self.at - self.xf; self.length = length
        self.anim = None
        if s.get("anim"):                                              # MiniMax layer, painting-framed (prep_anim.py)
            self.anim = cv2.VideoCapture(f"{DATA}/{s['anim']}"); self.anim_n = int(self.anim.get(cv2.CAP_PROP_FRAME_COUNT))
            alen = self.anim_n / FPS; rev_end = self.at + self.hold + self.reveal
            freeze = s.get("anim_freeze", ed.get("anim_freeze", 4.0))   # owner 2026-10-14: hold the clip's last frame
            still = ed.get("anim_min_still", 2.0)                       # a few seconds, take that time from the still
            self.anim_t0 = max(rev_end + still + 1.0, end_t - alen - freeze)   # painting before it; total unchanged
            self.anim_idx, self.anim_img = -1, None
        self.rv = None
        if ed.get("style") == "reveal" and "reveal_at" in s:          # 月光 (owner 2026-10-16): veiled transformation,
            self.rv = dict(REVEAL_DEFAULTS, **ed.get("reveal", {}))     # painting revealed ON the accent, then held
            rv = self.rv; self.R_t = s["reveal_at"]; self.kind = s.get("reveal_type", "firm")
            I = min(1.0, max(0.0, (s.get("intensity", 0.6) - 0.3) / 0.7))   # 0 = soft (I 0.3) .. 1 = climax (I 1.0)
            lerp = lambda ab: ab[0] + (ab[1] - ab[0]) * I
            self.p = {"blur": lerp(rv["blur"]), "gain": min(max(lerp(rv["gain"]) - 0.5 * (self.key - 0.30), 0.55), 0.80),
                      "desat": lerp(rv["desat"]), "vig": lerp(rv["vignette"]), "pop": 0.03 + 0.02 * I,
                      "over": lerp(rv["overshoot"]), "glow": lerp(rv["glow"]), "punch": lerp(rv["punch"]) if self.kind == "snap" else 0.0,
                      "attack": rv["attack_frames"][self.kind] / FPS}
            build = self.R_t - self.at
            self.B = min(rv["veil_max"], max(rv["veil_min"], build - rv["clear"]))   # surplus length goes to the clear photo
            self.B = min(self.B, max(build - 0.6, 0.5))
            self.b0 = self.R_t - FRAME - self.B                         # veil start
    def punch(self, t):
        if self.rv is None or not self.p["punch"]: return 1.0
        u = min(max((t - (self.R_t - FRAME)) / self.rv["punch_time"], 0.0), 1.0)
        return 1 + self.p["punch"] * (1 - (1 - u) ** 3)                # ease-out, then stays (the slow push continues)
    def M(self, t):
        if self.rv is not None:                                         # v7: still under the veil, motion released by the reveal
            z = 1 + self.rv["push_after"] * min(max((t - self.R_t) / max(self.end - self.R_t, 1.0), 0), 1)
        else:
            z = 1 + (self.zmax - 1) * min(max((t - self.t_start) / self.length, 0), 1)
        z *= self.punch(t)
        s = z / self.pre
        # image pixel (u,v) -> box position (x0 + u/pre, y0 + v/pre), then scale by z about F
        a = s; tx = self.F[0] + z * (self.x0 - self.F[0]); ty = self.F[1] + z * (self.y0 - self.F[1])
        return np.float32([[a, 0, tx], [0, a, ty]])
    def anim_frame(self, t):
        want = min(max(int((t - self.anim_t0) * FPS), 0), self.anim_n - 1)
        while self.anim_idx < want:
            ok, f = self.anim.read()
            if not ok: break
            self.anim_idx += 1; self.anim_img = f
        return cv2.resize(self.anim_img, (self.P.shape[1], self.P.shape[0]), interpolation=cv2.INTER_AREA)
    def frame(self, t):
        M = self.M(t)
        paint = cv2.warpAffine(self.P, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=BG)
        if self.anim is not None and t >= self.anim_t0 - 1.0:
            mov = cv2.warpAffine(self.anim_frame(t), M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=BG)
            w = smooth((t - (self.anim_t0 - 1.0)) / 1.0)
            return mov if w >= 1 else cv2.addWeighted(paint, 1 - w, mov, w, 0)
        if self.rv is not None: return self.reveal_frame(t, M, paint)
        if self.mix is not None:
            i0, cum = self.mix; k = int(round(t * BREATH["fps"])) - i0
            m = 0.0 if k < 0 else (1.0 if k >= len(cum) else float(cum[k]))
            if m >= 1: return paint
            photo = cv2.warpAffine(self.R, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=BG)
            return photo if m <= 0 else cv2.addWeighted(photo, 1 - m, paint, m, 0)
        if self.R is None: return paint
        a = smooth((t - self.at - self.hold) / self.reveal)
        if a >= 1: return paint
        photo = cv2.warpAffine(self.R, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=BG)
        return photo if a <= 0 else cv2.addWeighted(photo, 1 - a, paint, a, 0)

FRAME = 1 / FPS
REVEAL_DEFAULTS = {        # [soft, climax] pairs are interpolated by the shot's intensity (spec reviewed with Fable 5.1)
    "clear": 2.2, "veil_min": 2.5, "veil_max": 6.0, "form_frac": 0.75,   # photo clear / veil (painting forms in 75 %)
    "blur": [3.0, 7.0],            # Gaussian sigma px at the full veil (1080p)
    "gain": [0.78, 0.60], "lift": 0.02,   # brightness at the full veil + black lift (a milky veil, not a black hole)
    "desat": [0.10, 0.25], "vignette": [0.15, 0.30],   # vignette darkening at r = 0.75 of the half-diagonal
    "attack_frames": {"snap": 2, "firm": 5, "bloom": 24},
    "overshoot": [0.06, 0.18], "over_tau": 0.25,       # brightness overshoot at full reveal, exp decay
    "glow": [0.15, 0.40], "glow_sigma": 20, "glow_thresh": 0.70,   # threshold per image = its 85th luma percentile
    "push_after": 0.015,           # push-in only after the reveal, through the rest and fade
    "punch": [0.015, 0.025], "punch_time": 16 / 30,    # snap only, centred on the brightest point (moon)
    "out_blur": 2.0,               # outgoing painting softens while the next photo surfaces
}
KS = 43                            # fixed blur kernel (sigma up to 7): no kernel-size jumps -> no flicker
_VIG = {}

def bright_focus(img):
    g = cv2.GaussianBlur(cv2.cvtColor(cv2.resize(img, (192, int(192 * img.shape[0] / img.shape[1]))), cv2.COLOR_BGR2GRAY), (0, 0), 6)
    y, x = np.unravel_index(int(np.argmax(g)), g.shape)
    return min(max(x / g.shape[1], 0.3), 0.7), min(max(y / g.shape[0], 0.3), 0.7)

def vignette_mask():
    if "m" not in _VIG:
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        r = np.hypot(xx - W / 2, yy - H / 2) / np.hypot(W / 2, H / 2)
        _VIG["m"] = np.minimum((r / 0.75) ** 2, 1.6)[..., None]
    return _VIG["m"]

def soft_clip(f, knee=225.0):
    over = f > knee
    if over.any(): f[over] = knee + (255 - knee) * np.tanh((f[over] - knee) / (255 - knee))
    return f

LIGHT = {}                         # per-frame music curves (music_light): "E" gain, "r" register 0..1

def reg_at(t):
    r = LIGHT.get("r"); return 0.5 if r is None else float(r[min(max(int(round(t * FPS)), 0), len(r) - 1)])

BREATH = {}                        # breath curve (breath_curve.py), loaded in main for style "breath"
BREATH_LOOK = {"hi": 1.04, "depth": 0.30, "blur": 5.0, "desat": 0.18, "vig": 0.22}

def breath_look(img, b, lk):
    """Out-breath (low b): darker, softer, a little faded at the edges; in-breath (high b): bright and clear."""
    v = 1.0 - b
    sig = lk["blur"] * max(0.0, (v - 0.25) / 0.75)
    out = cv2.GaussianBlur(img, (KS, KS), sig) if sig > 0.25 else img
    f = out.astype(np.float32)
    if lk["desat"] > 0 and v > 0.02:
        g = cv2.cvtColor(out, cv2.COLOR_BGR2GRAY).astype(np.float32)[..., None]; d = lk["desat"] * v; f = f * (1 - d) + g * d
    f = f * (lk["hi"] - lk["depth"] * v ** 1.2) * (1 - lk["vig"] * v * vignette_mask())
    return np.clip(soft_clip(f), 0, 255).astype(np.uint8)

def expose(img, g):
    f = img.astype(np.float32) * g
    hi = f > 217.0                                                     # soft shoulder from 0.85
    if hi.any(): f[hi] = 217.0 + 38.0 * np.tanh((f[hi] - 217.0) / 38.0)
    return np.clip(f, 0, 255).astype(np.uint8)

def veil(img, v, p, rv, r=0.5):
    if v <= 0.002: return img
    sig = p["blur"] * v * (0.75 + 0.5 * (1 - r))                       # bass = murkier, treble = clearer
    out = cv2.GaussianBlur(img, (KS, KS), sig) if sig > 0.25 else img
    f = out.astype(np.float32)
    if p["desat"] > 0:
        g = cv2.cvtColor(out, cv2.COLOR_BGR2GRAY).astype(np.float32)[..., None]
        d = p["desat"] * v; f = f * (1 - d) + g * d
    gain = 1 - (1 - p["gain"]) * v
    f = f * gain * (1 - p["vig"] * v * vignette_mask()) + 255 * (rv["lift"] - 0.04 * (1 - r)) * v   # bass deepens the blacks
    return np.clip(f, 0, 255).astype(np.uint8)

def reveal_frame_impl(sh, t, M, paint):
    rv, p, R = sh.rv, sh.p, sh.R_t
    t0 = R - FRAME                                                     # first changed frame: one frame before the note
    if t < t0:
        q = min(max((t - sh.b0) / max(t0 - sh.b0, 0.1), 0.0), 1.0)
        v = smooth(q) ** 2                                             # deepest, softest frame = the one before the snap
        if sh.R is None: img = paint
        else:
            m = smooth(min(max((t - sh.b0) / (rv["form_frac"] * sh.B), 0.0), 1.0))
            if m >= 1: img = paint
            else:
                photo = cv2.warpAffine(sh.R, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=BG)
                img = photo if m <= 0 else cv2.addWeighted(photo, 1 - m, paint, m, 0)
        return veil(img, v, p, rv, reg_at(t))
    u = min((t - t0) / p["attack"], 1.0); e = 1 - (1 - u) ** 3        # ease-out: most of the change in the first frame
    img = veil(paint, 1 - e, p, rv, reg_at(t))
    t_full = t0 + p["attack"]
    amp = e if t < t_full else np.exp(-(t - t_full) / rv["over_tau"])
    over, glow = p["over"] * amp, p["glow"] * amp
    if over < 0.003 and glow < 0.003: return img
    f = img.astype(np.float32)
    if glow >= 0.003:
        small = cv2.resize(img, (W // 4, H // 4), interpolation=cv2.INTER_AREA).astype(np.float32)
        th = sh.glow_thr
        hi = np.clip((small - 255 * th) / (255 * (1 - th)), 0, 1) * small
        gl = cv2.resize(cv2.GaussianBlur(hi, (0, 0), rv["glow_sigma"] / 4), (W, H), interpolation=cv2.INTER_LINEAR)
        f = 255 - (255 - f) * (1 - glow * gl / 255)                    # screen blend, highlights only
    bp = p["pop"] * amp                                                # contrast returns: black point drops a few %
    f = (f - 255 * bp) / (1 - bp)
    f = soft_clip(f * (1 + over))                                      # overshoot with a soft knee (the moon never clips)
    return np.clip(f, 0, 255).astype(np.uint8)

Shot.reveal_frame = reveal_frame_impl

def music_light(ed, end, reveals=()):
    """Continuous light from the music (v7, spec from the Fable 5.1 review). Edit-list block "music_light":
    short-term loudness l and register r (band ratio, register_curve.py) mapped once, globally, by their 5-95 %
    range to 0..1; envelopes l: attack 0.25 / release 1.4 s, r: 0.6 / 2.0 s; two 0.8 Hz low-passes; slew <= 6 %/s;
    E = (1 + 0.18 (l - 0.5)) (1 + 0.12 (r - 0.5) w), w = clip(l / 0.15) so silence never brightens; clamp 0.84-1.14;
    frozen for 0.8 s from each reveal frame (never fights the overshoot), then eased back. Fills LIGHT["r"] for the veil."""
    ml = ed.get("music_light")
    if not ml: return None
    C = json.load(open(f"{DATA}/{ml['curve']}")); rt = np.array(C["t"])
    def norm(v):
        v = np.array(v, np.float64); lo, hi = np.percentile(v, 5), np.percentile(v, 95); return np.clip((v - lo) / (hi - lo + 1e-9), 0, 1)
    n = int(end * FPS) + 2; tt = np.arange(n) / FPS
    def env(x, att, rel):
        up = 1 - np.exp(-1 / (FPS * att)); dn = 1 - np.exp(-1 / (FPS * rel)); out = np.empty_like(x); g = x[0]
        for i, v in enumerate(x): g += (v - g) * (up if v > g else dn); out[i] = g
        return out
    def lp(x, fc=0.8):
        a = 1 - np.exp(-2 * np.pi * fc / FPS); y = np.empty_like(x); g = x[0]
        for i, v in enumerate(x): g += (v - g) * a; y[i] = g
        return y
    l = lp(lp(env(np.interp(tt, rt, norm(C["lst"])), 0.25, 1.4)))
    r = lp(lp(env(np.interp(tt, rt, norm(C["treb"])), 0.6, 2.0)))
    w = np.clip(l / 0.15, 0, 1)
    E = (1 + ml.get("l_gain", 0.18) * (l - 0.5)) * (1 + ml.get("r_gain", 0.12) * (r - 0.5) * w)
    slew = ml.get("slew", 0.06) / FPS
    for i in range(1, n): E[i] = E[i - 1] + np.clip(E[i] - E[i - 1], -slew, slew)
    for R in reveals:                                                   # freeze 0.8 s from the reveal, ease back over 0.8 s
        i0 = int(round(R * FPS)); f = int(0.8 * FPS)
        if i0 >= n: continue
        E[i0:i0 + f] = E[i0]
        for k in range(f):
            if i0 + f + k < n: E[i0 + f + k] = E[i0] + (E[i0 + f + k] - E[i0]) * (k + 1) / f
    lo, hi = ml.get("range", [0.84, 1.14])
    LIGHT["r"] = r
    return np.clip(E, lo, hi)

def label_img(text, size=24, alpha=170):
    f = ImageFont.truetype(FONT, size); w = int(f.getlength(text)) + 20
    im = Image.new("RGBA", (w, size + 16), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, size + 15], 6, fill=(0, 0, 0, 110)); d.text((10, 6), text, font=f, fill=(225, 225, 225, alpha))
    a = np.asarray(im).astype(np.float32); return a[..., [2, 1, 0]], a[..., 3:4] / 255.0

def overlay(frame, lab, x, y):
    rgb, al = lab; h, w = rgb.shape[:2]
    roi = frame[y:y + h, x:x + w].astype(np.float32); frame[y:y + h, x:x + w] = (roi * (1 - al) + rgb * al).astype(np.uint8)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("edit"); ap.add_argument("out"); ap.add_argument("--review", action="store_true")
    ap.add_argument("--from", dest="t0", type=float, default=0.0); ap.add_argument("--to", dest="t1", type=float, default=None)
    a = ap.parse_args()
    ed = json.load(open(a.edit)); end = ed["end"]; X = ed["xfade"]
    ed["shots"] = [s for s in ed["shots"] if not s.get("drop")]         # owner-approved drops stay in the list, flagged
    # xfade_mid (default 1 = old behaviour, fade ENDS at the cut): 0.5 centres the cross-fade on `at`, so a picture
    # change snapped to an accent arrives with the note instead of before it (owner 2026-10-16: 重音的时候换照片)
    shift = X * (1 - ed.get("xfade_mid", 1.0))
    if ed.get("style") in ("reveal", "breath"):                        # per-shot dissolves (reveal: centred before the note)
        end_mode = ed.get("xfade_mode") == "end"                       # v5: `at` = fade END (slow fade after the rest)
        ed["shots"] = [dict(s, _xf=s.get("xf_in", X), at=s["at"] if (i == 0 or end_mode) else s["at"] - FRAME + s.get("xf_in", X) / 2)
                       for i, s in enumerate(ed["shots"])]
    elif shift:
        ed["shots"] = [s if i == 0 else dict(s, at=s["at"] + shift) for i, s in enumerate(ed["shots"])]
    G = music_light(ed, end, [s["reveal_at"] - FRAME for s in ed["shots"] if "reveal_at" in s])   # light from the music (optional)
    if ed.get("style") == "breath":
        Bc = json.load(open(f"{DATA}/{ed['breath']['curve']}")); BREATH.update(b=Bc["b"], fps=Bc["fps"])
        BREATH_LOOK.update(ed["breath"].get("look", {}))
    shots = []
    for i, s in enumerate(ed["shots"]):
        nxt = ed["shots"][i + 1]["at"] if i + 1 < len(ed["shots"]) else end
        shots.append(Shot(s, ed, nxt, i, len(ed["shots"])))
    labels = {}
    if a.review:
        for sh in shots:
            labels[sh.i] = {"name": label_img(f"{sh.i + 1}/{sh.n}  {sh.s['zh']}"), "nophoto": label_img("照片待生成"), "nopaint": label_img("油画待生成"), "mm": label_img(sh.s["mm"] if isinstance(sh.s.get("mm"), str) else "动画待做（MiniMax）")}
        head = label_img(f"预览 · {ed['title']}", 26)
    t1 = a.t1 if a.t1 is not None else end
    tmp = a.out + ".video.mp4"
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                            "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
    nf = int(round((t1 - a.t0) * FPS))
    for fi in range(nf):
        t = a.t0 + fi / FPS
        cur = max((sh for sh in shots if sh.at - sh.xf <= t), key=lambda sh: sh.at, default=shots[0])
        fr = cur.frame(t)
        prev = shots[cur.i - 1] if cur.i > 0 else None
        if prev is not None and t < cur.at:                            # cross-fade into `cur`
            w = smooth((t - (cur.at - cur.xf)) / cur.xf); pf = prev.frame(t)
            if prev.rv is not None and w > 0.02: pf = cv2.GaussianBlur(pf, (KS, KS), prev.rv["out_blur"] * w)
            fr = cv2.addWeighted(pf, 1 - w, fr, w, 0)
        if BREATH:                                                      # the whole picture breathes with the melody
            bi = BREATH["b"][min(int(round(t * BREATH["fps"])), len(BREATH["b"]) - 1)]
            fr = breath_look(fr, bi, BREATH_LOOK)
        if G is not None:                                               # bass darker, treble brighter, louder brighter
            gi = G[min(int(round(t * FPS)), len(G) - 1)]
            if abs(gi - 1) > 0.002: fr = np.clip(soft_clip(fr.astype(np.float32) * gi), 0, 255).astype(np.uint8)
        g = 1.0
        if t < ed["fade_in"]: g = smooth(t / ed["fade_in"])
        if t > end - ed["fade_out"]: g = min(g, smooth((end - t) / ed["fade_out"]))
        if g < 1: fr = (fr.astype(np.float32) * g + np.float32(BG) * (1 - g)).astype(np.uint8)
        if a.review:
            sh = cur if (prev is None or t >= cur.at - X / 2) else prev
            L = labels[sh.i]; overlay(fr, L["name"], 24, H - 64)
            if sh.no_paint: overlay(fr, L["nopaint"], 24 + L["name"][0].shape[1] + 12, H - 64)
            elif sh.R is None and t < sh.at + sh.hold + sh.reveal: overlay(fr, L["nophoto"], 24 + L["name"][0].shape[1] + 12, H - 64)
            nxt_at = shots[sh.i + 1].at if sh.i + 1 < len(shots) else end
            if sh.s.get("mm") and nxt_at - 22 < t < nxt_at - X: overlay(fr, L["mm"], 24 + L["name"][0].shape[1] + 12, H - 64)
            if t < 8: overlay(fr, head, 24, 24)
        enc.stdin.write(fr.tobytes())
        if fi % (FPS * 30) == 0: print(f"  {t:6.1f}s / {t1:.0f}s", flush=True)
    enc.stdin.close(); enc.wait()
    dur = t1 - a.t0
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp, "-ss", str(a.t0), "-t", str(dur), "-i", f"{DATA}/{ed['music']}",
                    "-filter_complex", f"[1:a]apad,afade=t=in:st=0:d={0.5 if a.t0 > 0 else 0.01},afade=t=out:st={max(0, dur - ed['fade_out'])}:d={ed['fade_out']}[a]",
                    "-map", "0:v", "-map", "[a]", "-t", str(dur), "-c:v", "copy", "-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart", a.out], check=True)
    os.remove(tmp); print("wrote", a.out)

if __name__ == "__main__":
    main()
