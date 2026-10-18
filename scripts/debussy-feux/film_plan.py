#!/usr/bin/env python3
"""Plan the 焰火 film (Debussy, Feux d'artifice; Ligoratti, CC BY 3.0): seven paintings, each entered as the light dims
over a realistic photo, lit by a flame carried in (match, lamplighter's pole, taper, sparkler, incense, portfire, torch),
then fireworks that BURST ON THE MUSIC'S ACCENTS (owner 2026-10-18: "焰火绽开要卡节奏点上").

Writes feux/film/<id>/plan.json: per output frame the film time, the night level, the lamp lights (for the living
painting), the tool tip / alpha / angle / flame intensity and the camera; plus the shell list (`at` = the beat it bursts on).

    python film_plan.py [ids...]
"""
import hashlib, json, math, os, random, sys

DATA = "/Users/yqin/repo/playground/lucas-academy-video-data/debussy-impressions"
FILM = f"{DATA}/feux/film"
ASSETS = "/Users/yqin/repo/playground/lucas-visual-art-lab-feux/assets/living"
FPS = 30
W_OUT, H_OUT = 1920, 1080
XF = 0.75                       # half of the 1.5 s crossfade between sections

# palettes: kind -> colour (the kinds each painting's own brushes use, plus one or two that suit it)
GOLDP, ROSE, WHITEB, GREEN, RED, BLUE = [255, 176, 90], [255, 138, 208], [214, 226, 255], [156, 255, 176], [255, 72, 58], [90, 140, 255]
WILLOW, CRACK = [255, 204, 102], [255, 210, 122]

SECTIONS = [
  dict(id="venice", span=(0.0, 61.5 + XF), fade_in=(0.0, 2.5), dim=(6.0, 13.0), dissolve=(8.5, 12.5), night=(0.15, 0.8),
       tool=dict(side="right", enter=11.2, ignite=14.56, hover=(0.80, 0.80), contact=(0.62, 0.57), length=0.27, flame="match"),
       first=dict(at=21.13, kind="peony", y=0.24, size=66, rise=1.0, fuse=0.5), fw_end=59.6, horizon=0.57,
       sky=((0.30, 0.95), (0.09, 0.32)), big=["peony", "willow", "chrysanthemum"], mid=["ring", "peony", "crackle"], soft=["crackle", "ring"],
       colors=dict(peony=GOLDP, willow=WILLOW, ring=ROSE, chrysanthemum=WHITEB, crackle=CRACK), zoom=[(0, 1.0), (61, 1.05)]),
  dict(id="parliament", span=(61.5 - XF, 105.0 + XF), dim=(62.6, 65.8), dissolve=(63.2, 65.6), night=(0.2, 0.78),
       tool=dict(side="left", enter=63.4, ignite=65.34, hover=(0.30, 0.84), contact=(0.56, 0.62), length=0.40, flame="wick"),
       first=dict(at=68.34, kind="chrysanthemum", y=0.2, size=70, rise=0.95, fuse=0.45), fw_end=104.6, horizon=0.62,
       sky=((0.10, 0.94), (0.07, 0.32)), big=["chrysanthemum", "palm", "peony"], mid=["crossette", "peony", "ring"], soft=["crossette", "crackle"],
       colors=dict(chrysanthemum=WHITEB, palm=WILLOW, crossette=GREEN, peony=[255, 150, 90], ring=ROSE, crackle=CRACK), zoom=[(61, 1.0), (105, 1.04)]),
  dict(id="montmartre", span=(105.0 - XF, 137.5 + XF), dim=(107.5, 115.0), dissolve=(109.5, 114.0), night=(0.1, 0.35),
       tool=dict(side="right", enter=113.0, ignite=116.66, hover=(0.70, 0.64), contact=(0.50, 0.30), length=0.40, flame="taper"),
       first=dict(at=121.53, kind="peony", y=0.11, size=60, rise=1.25, fuse=0.5), fw_end=137.45, horizon=0.30,
       sky=((0.20, 0.80), (0.04, 0.15)), big=["peony", "ring", "crackle"], mid=["crackle", "peony", "ring"], soft=["crackle", "ring"],
       colors=dict(peony=GOLDP, ring=ROSE, crackle=CRACK), zoom=[(105, 1.0), (137.5, 1.05)]),
  dict(id="rhone", span=(137.5 - XF, 160.5 + XF), dim=(138.2, 141.0), dissolve=(138.4, 140.8), night=(0.05, 0.22),
       tool=dict(side="left", enter=139.2, ignite=140.54, hover=(0.32, 0.70), contact=(0.60, 0.44), length=0.42, flame="sparkler"),
       first=dict(at=143.31, kind="chrysanthemum", y=0.17, size=68, rise=0.95, fuse=0.45), fw_end=159.6, horizon=0.44,
       sky=((0.26, 0.92), (0.08, 0.27)), big=["chrysanthemum", "willow", "peony"], mid=["crackle", "peony", "chrysanthemum"], soft=["crackle", "willow"],
       colors=dict(chrysanthemum=WHITEB, willow=WILLOW, crackle=CRACK, peony=GOLDP), zoom=[(137.5, 1.0), (160.5, 1.05)]),
  dict(id="beijing", span=(160.5 - XF, 186.0 + XF), dim=(161.0, 163.8), dissolve=(161.4, 163.6), night=(0.1, 0.4),
       tool=dict(side="right", enter=162.1, ignite=163.41, hover=(0.82, 0.84), contact=(0.72, 0.56), length=0.36, flame="incense"),
       first=dict(at=169.03, kind="peony", y=0.2, size=72, rise=1.4, fuse=0.8), fw_end=185.9, horizon=0.56,
       sky=((0.38, 0.96), (0.08, 0.34)), big=["peony", "palm", "chrysanthemum"], mid=["crossette", "peony", "chrysanthemum"], soft=["crossette", "crackle"],
       colors=dict(peony=RED, palm=WILLOW, chrysanthemum=WHITEB, crossette=GREEN, crackle=CRACK), zoom=[(160.5, 1.0), (186, 1.05)]),
  dict(id="rocket", span=(186.0 - XF, 228.0), fade_out=(225.6, 227.8), dim=(186.6, 189.4), dissolve=(187.0, 189.2), night=(0.02, 0.15),
       tool=dict(side="left", enter=187.3, ignite=188.69, hover=(0.24, 0.90), contact=(0.42, 0.78), length=0.34, flame="portfire"),
       first=dict(at=192.25, kind="willow", y=0.22, size=72, rise=1.2, fuse=0.4), fw_end=217.0, horizon=0.78,
       sky=((0.16, 0.84), (0.07, 0.34)), big=["willow", "palm", "peony"], mid=["crackle", "willow", "peony"], soft=["crackle", "willow"],
       colors=dict(willow=WILLOW, palm=WILLOW, peony=[255, 190, 110], crackle=CRACK),
       extra=[dict(at=217.6, kind="willow", size=84, x=0.5, y=0.16)],
       zoom=[(185.25, 1.0), (191.2, 1.0), (194.0, 1.24, 0.5, 0.36), (221.5, 1.24, 0.5, 0.36), (226.5, 1.06, 0.5, 0.45)]),
  dict(id="montorgueil", span=(227.5, 276.5), fade_in=(228.6, 230.6), fade_out=(273.4, 276.4), dim=(231.5, 240.0), dissolve=(233.5, 238.5),
       night=(0.1, 0.66),
       tool=dict(side="right", enter=236.4, ignite=237.99, hover=(0.74, 0.64), contact=(0.50, 0.32), length=0.27, flame="torch"),
       first=dict(at=246.11, kind="tricolor", y=0.12, size=66, rise=1.1, fuse=0.6), fw_end=270.0, horizon=0.32,
       sky=((0.36, 0.64), (0.05, 0.19)), big=["tricolor"], mid=["tricolor", "ring"], soft=["ring", "tricolor"],
       colors=dict(tricolor=BLUE, ring=[250, 246, 238]), only=[249.16, 252.05, 255.01, 261.49, 264.58, 267.76],
       zoom=[(227.5, 1.0), (244.2, 1.0), (247.6, 1.3, 0.5, 0.3), (267.5, 1.3, 0.5, 0.3), (273.5, 1.0, 0.5, 0.5)]),
]

FLAME = {   # lamp light the flame throws on the painting: steady intensity, radius (fraction of the long side), colour
  "match": (0.55, 0.30, [255, 172, 96]), "wick": (0.5, 0.28, [255, 178, 104]), "taper": (0.5, 0.28, [255, 184, 110]),
  "sparkler": (0.62, 0.34, [255, 226, 180]), "incense": (0.26, 0.16, [255, 140, 70]), "portfire": (0.75, 0.34, [255, 200, 130]),
  "torch": (0.8, 0.38, [255, 160, 80]),
}

def smooth(x): x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)
def ramp(t, a, b): return smooth((t - a) / (b - a)) if b > a else float(t >= b)
def lerp(a, b, f): return a + (b - a) * f
def seed_of(*parts): return int(hashlib.md5("|".join(map(str, parts)).encode()).hexdigest()[:8], 16) / 2 ** 32 * 1000

def asset_size(sid):
    from PIL import Image
    return Image.open(f"{ASSETS}/feux-{sid}.jpg").size

def camera(sec, t, aspect):
    """zoom (1 = painting height fills the frame), view centre (cx, cy) in painting fractions, clamped to the painting."""
    ks = sec["zoom"]
    def at(i): k = ks[i]; return (k[1], k[2] if len(k) > 2 else 0.5, k[3] if len(k) > 3 else 0.5)
    if t <= ks[0][0]: z, cx, cy = at(0)
    elif t >= ks[-1][0]: z, cx, cy = at(len(ks) - 1)
    else:
        i = max(j for j in range(len(ks)) if ks[j][0] <= t); f = smooth((t - ks[i][0]) / (ks[i + 1][0] - ks[i][0]))
        a, b = at(i), at(i + 1); z, cx, cy = [lerp(a[j], b[j], f) for j in range(3)]
    Hd = H_OUT * z; Wd = Hd * aspect
    cy = 0.5 if Hd <= H_OUT else min(max(cy, H_OUT / 2 / Hd), 1 - H_OUT / 2 / Hd)
    cx = 0.5 if Wd <= W_OUT else min(max(cx, W_OUT / 2 / Wd), 1 - W_OUT / 2 / Wd)
    return z, cx, cy

def screen_to_frac(sec, t, aspect, X, Y):
    z, cx, cy = camera(sec, t, aspect); Hd = H_OUT * z; Wd = Hd * aspect
    return cx + (X - W_OUT / 2) / Wd, cy + (Y - H_OUT / 2) / Hd

def tool_track(sec, aspect):
    """Keyframes of the tool tip (painting fractions): in from off-screen, strike / catch at the hover point, glide to the
    fuse, hold while it sputters, then out. Off-screen points are placed in SCREEN space so portrait paintings work too."""
    T, F = sec["tool"], sec["first"]
    touch = F["at"] - F["rise"] - F["fuse"]
    right = T["side"] == "right"
    off_in = screen_to_frac(sec, T["enter"], aspect, W_OUT + 260 if right else -260, H_OUT + 120)
    off_out = screen_to_frac(sec, touch + F["fuse"] + 3.2, aspect, W_OUT + 300 if right else -300, H_OUT + 160)
    hx, hy = T["hover"]; cx, cy = T["contact"]
    keys = [(T["enter"], off_in), (T["ignite"] - 0.12, (hx, hy)), (T["ignite"] + 0.45, (hx + (0.01 if right else -0.01), hy - 0.02)),
            (touch, (cx, cy)), (touch + F["fuse"] + 0.25, (cx + (0.012 if right else -0.012), cy + 0.01)), (touch + F["fuse"] + 3.2, off_out)]
    return keys, touch

def track_at(keys, t):
    if t <= keys[0][0]: return keys[0][1]
    if t >= keys[-1][0]: return keys[-1][1]
    i = max(j for j in range(len(keys)) if keys[j][0] <= t)
    (t0, p0), (t1, p1) = keys[i], keys[i + 1]
    f = smooth((t - t0) / (t1 - t0))
    # a gentle arc between keyframes (never a straight robotic line)
    mx, my = lerp(p0[0], p1[0], f), lerp(p0[1], p1[1], f)
    bow = math.sin(math.pi * f) * 0.04 * math.hypot(p1[0] - p0[0], p1[1] - p0[1])
    return (mx, my - bow)

def accents():
    return json.load(open(f"{FILM}/accents.json"))["onsets"]

def loud01(db): return min(1.0, max(0.0, (db + 30) / 20))

def schedule(sec):
    """Shells on accents: strongest first, at least 0.42 s apart, a loudness-dependent cap per 3 s window."""
    F = sec["first"]; rnd = random.Random(sec["id"])
    A = [a for a in accents() if F["at"] + 0.3 < a["t"] <= sec["fw_end"]]
    if "only" in sec: A = [a for a in accents() if any(abs(a["t"] - o) < 0.02 for o in sec["only"])]
    for a in A: a["loud"] = loud01(a["db"]); a["pri"] = 0.7 * a["score"] + 0.3 * a["loud"]
    picked = [dict(t=F["at"], pri=1.0, loud=0.8, first=True)]
    for a in sorted(A, key=lambda a: -a["pri"]):
        if "only" not in sec and a["pri"] < 0.5: continue
        if any(abs(a["t"] - p["t"]) < 0.42 for p in picked): continue
        cap = 1 + round(2 * a["loud"])
        if sum(1 for p in picked if abs(a["t"] - p["t"]) < 1.5) >= cap: continue
        picked.append(dict(t=a["t"], pri=a["pri"], loud=a["loud"]))
    picked.sort(key=lambda p: p["t"])
    (x0, x1), (y0, y1) = sec["sky"]; H = sec["horizon"]
    shells, last_kind, last_x = [], None, []
    for i, p in enumerate(picked):
        if p.get("first"):
            kind, size, y = F["kind"], F["size"], F["y"]; x = sec["tool"]["contact"][0]
        else:
            tier = "big" if p["pri"] >= 0.82 and p["loud"] >= 0.5 else ("soft" if p["loud"] < 0.3 else "mid")
            choices = [k for k in sec[tier] if k != last_kind] or sec[tier]
            kind = rnd.choice(choices)
            size = {"big": 70, "mid": 60, "soft": 50}[tier] + 14 * p["loud"] + rnd.uniform(-5, 5)
            cand = [rnd.uniform(x0, x1) for _ in range(10)]
            x = max(cand, key=lambda c: min([abs(c - lx) for lx in last_x[-2:]] or [1]))
            y = rnd.uniform(y0, y0 + (y1 - y0) * (0.65 if tier == "big" else 1.0))
        rise = min(1.8, max(0.8, 0.75 + 1.5 * (H - y))) if not p.get("first") else F["rise"]
        sh = dict(kind=kind, at=round(p["t"], 3), x=round(x, 4), y=round(y, 4), size=round(size, 1), color=sec["colors"][kind],
                  seed=round(seed_of(sec["id"], i, p["t"]), 4), rise=round(rise, 3))
        if p.get("first"): sh["lx"] = sec["tool"]["contact"][0]
        shells.append(sh); last_kind = kind; last_x.append(x)
    for e in sec.get("extra", []):
        y = e["y"]; shells.append(dict(kind=e["kind"], at=e["at"], x=e["x"], y=y, size=e["size"], color=sec["colors"][e["kind"]],
                                       seed=round(seed_of(sec["id"], "extra", e["at"]), 4), rise=round(min(1.8, 0.75 + 1.5 * (H - y)), 3)))
    return sorted(shells, key=lambda s: s["at"])

def flame_level(sec, t, touch):
    T, F = sec["tool"], sec["first"]
    I0 = FLAME[T["flame"]][0]
    if t < T["ignite"]: return 0.0
    a = t - T["ignite"]
    base = I0 * smooth(a / 0.35)
    if T["flame"] == "match": base += 0.9 * math.exp(-a / 0.18) * (a > 0)          # the strike flares, then settles
    flick = 1 + 0.08 * math.sin(2 * math.pi * 7.3 * t) + 0.06 * math.sin(2 * math.pi * 11.7 * t + 1.3)
    return base * flick

def plan(sec):
    sid = sec["id"]; w, h = asset_size(sid); aspect = w / h
    keys, touch = tool_track(sec, aspect)
    T, F = sec["tool"], sec["first"]
    I0, R, col = FLAME[T["flame"]]
    t_exit = keys[-1][0]
    frames = []
    n = int(round((sec["span"][1] - sec["span"][0]) * FPS))
    for k in range(n):
        t = sec["span"][0] + k / FPS
        nf, nt = sec["night"]
        night = lerp(nf, nt, ramp(t, sec["dissolve"][0], sec["dim"][1] + 0.5)) if t >= sec["dissolve"][0] else nf
        tip = track_at(keys, t)
        alpha = ramp(t, T["enter"], T["enter"] + 0.7) * (1 - ramp(t, t_exit - 0.8, t_exit))
        I = flame_level(sec, t, touch) * alpha
        lamps = [dict(x=round(tip[0], 4), y=round(tip[1] - 0.02, 4), I=round(I, 3), R=R, c=col)] if I > 0.01 else []
        z, cx, cy = camera(sec, t, aspect)
        dip = -7 * ramp(t, touch - 0.4, touch) * (1 - ramp(t, touch + F["fuse"], touch + F["fuse"] + 0.6))
        sway = 3 * math.sin(t * 1.3 + 0.7) + 1.5 * math.sin(t * 2.9)
        frames.append(dict(t=round(t, 4), night=round(night, 4), lamps=lamps,
                           tool=dict(u=round(tip[0], 4), v=round(tip[1], 4), a=round(alpha, 3), rot=round(dip + sway, 2), I=round(I, 3)),
                           cam=[round(z, 4), round(cx, 4), round(cy, 4)]))
    out = dict(id=sid, work=f"feux-{sid}", fps=FPS, span=sec["span"], size=[w, h], fade_in=sec.get("fade_in"), fade_out=sec.get("fade_out"),
               dim=sec["dim"], dissolve=sec["dissolve"], tool=dict(T, touch=round(touch, 3), fuse=F["fuse"], keys=keys),
               show=schedule(sec), frames=frames)
    os.makedirs(f"{FILM}/{sid}", exist_ok=True)
    json.dump(out, open(f"{FILM}/{sid}/plan.json", "w"))
    print(f"{sid:12s} {n} frames, {len(out['show'])} shells, touch {touch:.2f}, shells at", " ".join(f"{s['at']:.1f}" for s in out["show"]))

if __name__ == "__main__":
    ids = sys.argv[1:] or [s["id"] for s in SECTIONS]
    for s in SECTIONS:
        if s["id"] in ids: plan(s)
