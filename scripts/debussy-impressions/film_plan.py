"""film_plan.py — plan the whole faune film from the music.

Per painting (owner 2026-10-17): the lazy painter paints fast and abbreviated, still stroke by stroke on the beat
(「一开始作画的过程可以快一些，省略一些（还是按照节奏运笔）」); the camera pushes in; the wand adds the living
effects one by one on accents; then there is time to look at the living painting (「live painting 结束以后要有一些
时间欣赏」). The easel's place changes from painting to painting (「画板位置的构图，不要一成不变」).

    python film_plan.py sections            -> DATA/faune/film/plan.json
    python film_plan.py score ID            -> DATA/faune/film/ID/score.json   (strokes on the section's notes)
    python film_plan.py live ID             -> DATA/faune/film/ID/live.json, scene.json  (needs snap.json, strokes.json)
    python film_plan.py layout [ID...]      -> re-place the easels (LAYOUT, ground() camera) in existing scene.json
"""
import json, math, re, sys, os
import numpy as np

DATA = "/Users/yqin/repo/playground/lucas-academy-video-data/debussy-impressions"
FILM = f"{DATA}/faune/film"
ARTLAB = "/private/tmp/claude-502/-Users-yqin-repo-playground-lucas-academy-video--claude-worktrees-information-theory-video-plan-d0f6c2/f1455221-65f4-4f6e-bb02-5410f583d23b/scratchpad/artlab-film"
ASSETS = f"{DATA}/faune/sample-seine/assets"
END = 554.0
# order and section starts (advisor's loudness/structure map); Lilies and the Footbridge swapped so the
# Footbridge's creatures and flashes meet the global climax at 329 s
SECTIONS = [("seine", 0.0), ("antibes", 59.1), ("cliff", 112.6), ("poppies", 145.0), ("meadow", 184.0), ("parasol", 222.0),
            ("lilies", 262.0), ("bridge", 303.0), ("grenouillere", 345.0), ("summer", 373.0), ("path", 431.0), ("springtime", 493.0)]
PRE = 2.5          # the dissolve from the previous living painting into this scene ends on the section start
PUSH = 3.6         # camera push-in

WATER = {"stillwater", "pondwater", "brokenlight", "seawaves"}
SKY = {"clouds", "racingclouds", "driftclouds"}
WIND = {"foliage", "pine", "tallgrass", "gusts", "poppywind", "cloth", "parasolsway", "willows"}
LIGHT = {"mistlight", "heathaze", "dapple", "sunlight"}
SWEEP = {"stillwater": (1, .15), "pondwater": (1, .15), "brokenlight": (1, .15), "seawaves": (.15, 1), "clouds": (1, 0),
         "racingclouds": (1, 0), "driftclouds": (1, 0), "foliage": (.3, 1), "pine": (.3, 1), "willows": (1, 0), "tallgrass": (1, 0), "gusts": (1, 0),
         "poppywind": (1, 0), "cloth": (1, .3), "parasolsway": (0, 1), "mistlight": (1, 0), "heathaze": (1, 0),
         "dapple": (-.6, 1), "sunlight": (0, 1)}
# where the easel stands, painting by painting (canvas centre and height as fractions of the frame; flip = mirrored easel).
# Owner 10-21: 「一开始的构图应该画板小很多，而且是真的在画的那种距离…每一个作品可能不一样」. Sized by the horizon rule:
# on flat ground a thing standing at row y_feet is H·(y_feet − y_horizon)/h_cam tall on screen, whatever the lens;
# the easel sprites are 1.75 m with a 0.58 m canvas centred 1.2 m up, so canvas = 0.58/h_cam·Δ and its centre sits
# 1.2/h_cam·Δ above the feet (Δ = y_feet − y_horizon). h_cam comes from the people (the horizon cuts a standing
# adult at the camera's eye height) or water lines. Slopes (path, poppies) are scaled from the figures; lilies looks
# down, so its easel stands on the near bank with the legs cut off by the frame; antibes and bridge too (an easel whose
# feet end in view over water reads as standing in it); lilies and bridge show only the canvas and the top of the
# easel at the bottom of the frame, as if we stand on the bank behind the painter. Feet row / horizon / camera height / ground:
#   seine 1.02/0.59/1.6 left bank in the reeds · antibes 1.21/0.78/– on the shore below the frame (none in view)
#   cliff 0.93/0.40/1.35 cliff-top grass · poppies 1.02/0.50/2.3 grass, figure-scaled · meadow 1.05/0.65/1.6 behind
#   the flowers · parasol 0.92/≈0.50/1.6 the slope left of the boy · lilies ≈1.4/–/– over the painter's shoulder · bridge
#   ≈1.3/0.44/– over the shoulder from the left bank · grenouillere 0.90/0.34/1.76 in the near rowboat · summer 0.96/0.33/1.25
#   seated, the deck's right edge · path 1.00/≈0.22/figures, grass left of the trail · springtime 0.83/0.30/1.2 seated, lawn
LAYOUT = {"seine": ([0.19, 0.70], 0.16, False), "antibes": ([0.70, 0.80], 0.20, True), "cliff": ([0.26, 0.46], 0.23, False),
          "poppies": ([0.17, 0.75], 0.13, False), "meadow": ([0.68, 0.75], 0.15, False), "parasol": ([0.16, 0.36], 0.28, False),
          "lilies": ([0.24, 0.83], 0.26, False), "bridge": ([0.15, 0.83], 0.22, False), "grenouillere": ([0.17, 0.52], 0.19, False),
          "summer": ([0.80, 0.58], 0.18, True), "path": ([0.26, 0.76], 0.13, True), "springtime": ([0.82, 0.31], 0.25, True)}
# how far up the legs the grass in front of them reaches (× easel height); 0 = boat, deck, bare bank or off-frame
GRASS = {"seine": 0.13, "cliff": 0.13, "poppies": 0.13, "meadow": 0.15, "parasol": 0.13, "path": 0.13, "springtime": 0.08}
ZOOM_LOCK = 1.8    # in the push the ground keeps with the easel up to this zoom (its feet stay on the grass)


TOOLS = f"{DATA}/faune/design-tools"
# every painting has its own easel, brush and wand, painted in its own colours (owner 2026-10-17)
TOOLSET = {"seine": "monet", "meadow": "sisley", "summer": "morisot", "path": "renoir", "antibes": "antibes", "cliff": "cliff",
           "poppies": "poppies", "parasol": "parasol", "lilies": "lilies", "bridge": "bridge", "grenouillere": "grenouillere",
           "springtime": "springtime"}


def tools(sid):
    t = TOOLSET[sid]
    return dict(easel=f"{TOOLS}/{t}-easel.png", brush=f"{TOOLS}/{t}-brush.png", wand_img=f"{TOOLS}/{t}-wand.png",
                dreamy=True, tint_brush=False)


def sm(x): x = min(max(x, 0.0), 1.0); return x * x * (3 - 2 * x)


def ground(sec, sid):
    """The camera for a small easel standing in the scene (owner 10-21: 「不要上来就 zoom in，和以前一样的节奏，一开始
    全画面，大概一半才 zoom in」): the wide shot holds while it is painted, the push starts halfway to the living
    painting and arrives on it; the ground zooms with the easel up to ×ZOOM_LOCK. Stroke timing unchanged."""
    return dict(camera=[round(0.5 * sec["live_t0"], 2), sec["live_t0"]], zoom_lock=ZOOM_LOCK, grass=GRASS.get(sid, 0.0))


def section_times():
    out = []
    for k, (sid, s0) in enumerate(SECTIONS):
        s1 = SECTIONS[k + 1][1] if k + 1 < len(SECTIONS) else END
        L = s1 - s0
        P = float(np.clip(0.23 * L, 7.5, 13.0))                  # painting: fast, abbreviated
        A = float(np.clip(0.24 * L, 6.5, 13.0))                  # looking at the living painting
        W = L - P - PUSH - 0.6 - A                               # the wand adds the effects
        out.append(dict(id=sid, s0=s0, s1=s1, L=round(L, 2), paint=[0, round(P, 2)], push=[round(P + 0.3, 2), round(P + 0.3 + PUSH, 2)],
                        live_t0=round(P + 0.3 + PUSH, 2), wand=[round(P + 0.3 + PUSH + 0.3, 2), round(L - A, 2)], look=[round(L - A, 2), round(L, 2)],
                        pre=0.0 if k == 0 else PRE, W=round(W, 2)))
    return out


def onsets(sid):
    return json.load(open(f"{DATA}/music/faune-sections/{sid}.json"))["onsets"]


def score(sid):
    sec = {s["id"]: s for s in section_times()}[sid]; s0 = sec["s0"]; P = sec["paint"][1]
    on = [o for o in onsets(sid) if s0 <= o["t"] < s0 + P - 1.6]
    groups = []
    for o in on:                                                 # notes closer than 0.5 s are one gesture
        if groups and o["t"] - groups[-1]["t"] < 0.33:
            groups[-1]["flux"] += o["flux"]; continue
        groups.append(dict(t=o["t"], flux=o["flux"], hz=o["hz"]))
    nmax = int(np.clip(round(P * 1.7), 12, 22)); nmin = int(round(P * 1.5))   # fast: about 1.6 strokes a second
    if len(groups) > nmax:                                       # keep the strongest gestures, in time order
        keep = sorted(sorted(groups, key=lambda g: -g["flux"])[:nmax], key=lambda g: g["t"])
        if groups[0] not in keep: keep = [groups[0]] + keep[1:]
        groups = keep
    while len(groups) < nmin:                                    # sparse music: fill the longest gaps
        ts = [s0] + [g["t"] for g in groups] + [s0 + P - 1.6]
        gaps = [(ts[i + 1] - ts[i], i) for i in range(len(ts) - 1)]
        g, i = max(gaps); groups.insert(i, dict(t=ts[i] + g / 2, flux=0.2, hz=0)); groups.sort(key=lambda x: x["t"])
    n = len(groups); nA = max(2, int(round(n * 0.25)))         # a quick block-in, then the painting itself
    zones = ["top", "middle", "bottom"]
    strokes = []
    for i, g in enumerate(groups):
        t = round(g["t"] - s0, 3); nxt = groups[i + 1]["t"] - s0 if i + 1 < n else P - 0.5
        hz2 = groups[i + 1]["hz"] if i + 1 < n else g["hz"]
        d = "flat" if not g["hz"] or not hz2 or abs(hz2 - g["hz"]) < 15 else ("up" if hz2 > g["hz"] else "down")
        last = i == n - 1
        strokes.append(dict(t=t, end=round(max(t + 0.45, nxt), 3), kind="A" if i < nA else "B",
                            zone=zones[(i if i < nA else i - nA) % 3], dir=d, loud=0.9 if last else 0.6, ring=0.6 if last else 0.35))
    sc = dict(piece="faune", painting=f"faune-{sid}", section=[sec["s0"], sec["s1"]],
              zones={"top": ["rect", 0, 0, 1, 0.42], "middle": ["rect", 0, 0.3, 1, 0.4], "bottom": ["rect", 0, 0.58, 1, 0.42]},
              strokes=strokes, settle=[round(P - 1.3, 2), round(P + 0.3, 2)])
    os.makedirs(f"{FILM}/{sid}", exist_ok=True)
    json.dump(sc, open(f"{FILM}/{sid}/score.json", "w"), indent=1)
    print(sid, n, "strokes", f"{nA} block-in", "paint", sec["paint"])


def effects(sid):
    html = open(f"{ARTLAB}/living.html").read(); js = open(f"{ARTLAB}/assets/living-brushes.js").read()
    i = html.index(f'"faune-{sid}":'); blk = html[i:html.index("\n    ] },", i)]
    ids = re.findall(r'\{ id:"(\w+)"', blk)
    kinds = dict(re.findall(r'(\w+): \{ tint:"[^"]*", kind:"(\w+)"', js))
    warps = [b for b in ids if kinds.get(b) == "warp"]; marks = [b for b in ids if kinds.get(b) == "mark"]
    order = sorted(warps, key=lambda b: (0 if b in WATER else 1 if b in SKY else 2 if b in WIND else 3))
    return order, marks


def live(sid):
    sec = {s["id"]: s for s in section_times()}[sid]; s0 = sec["s0"]
    snap = json.load(open(f"{FILM}/{sid}/snap.json")); GW, GH, Wp, Hp = snap["GW"], snap["GH"], snap["W"], snap["H"]
    warps, marks = effects(sid)
    warps = [w for w in warps if snap["masks"].get(w)]
    items = [("warp", w) for w in warps] + [("mark", m) for m in marks if any(x["key"] == m for x in snap["marks"])]
    w0, w1 = sec["wand"]
    def weight(it):
        if it[0] == "warp": return 1.4 if it[1] in WATER else 1.2 if it[1] in SKY else 1.0 if it[1] in WIND else 0.8
        return 0.6 + 0.12 * sum(1 for x in snap["marks"] if x["key"] == it[1])
    ws = np.array([weight(it) for it in items]); edges = w0 + np.concatenate([[0], np.cumsum(ws / ws.sum() * (w1 - w0))])
    on = [o for o in onsets(sid) if s0 + w0 <= o["t"] < s0 + w1]
    sched = dict(warps=[], marks=[], gain=1.8, live_t0=sec["live_t0"], t_end=sec["L"])
    path = []                                                   # [t, u, v, adding]
    def add(t, u, v, a): path.append([round(t, 3), round(float(u), 4), round(float(v), 4), a])
    cur = np.array([1.15, 0.15])
    for k, (kind, key) in enumerate(items):
        a0, a1 = edges[k], edges[k + 1]
        cand = [o for o in on if a0 <= o["t"] - s0 <= a0 + 0.45 * (a1 - a0)]
        t0 = (max(cand, key=lambda o: o["flux"])["t"] - s0) if cand else a0 + 0.2
        if kind == "warp":
            base = 4.5 if key in WATER else 4.0 if key in SKY else 3.0 if key in WIND else 2.5
            dur = float(np.clip(min(base, a1 - t0 - 0.4), 1.5, base))
            dx, dy = SWEEP.get(key, (1, 0))
            cells = np.array(snap["masks"][key]); cx = ((cells % GW) + .5) / GW; cy = ((cells // GW) + .5) / GH
            u = cx * dx + cy * dy; lo, hi = float(u.min()), float(u.max())
            entry = dict(key=key, t0=round(t0, 3), dur=round(dur, 3), dir=[dx, dy])
            if key == "driftclouds": entry.update(drift=12, ramp=4)   # the wind rises as the wand brings the clouds
            sched["warps"].append(entry)
            tt = t0
            while tt <= t0 + dur + 1e-6:                          # the wand rides the front of the effect
                front = lo + (hi - lo) * sm((tt - t0) / dur)
                near = np.abs(u - front) < 0.035
                if not near.any(): near = np.abs(u - front) <= np.abs(u - front).min() + 1e-6
                p = np.array([cx[near].mean(), cy[near].mean()])
                add(tt, p[0], p[1], 1 if tt < t0 + dur - 0.1 else 0); cur = p; tt += 0.2
        else:
            pts = [(i, x["x"] / Wp, x["y"] / Hp) for i, x in enumerate([m for m in snap["marks"] if m["key"] == key])]
            order, here = [], cur.copy()
            while pts:                                           # visit them nearest first
                j = min(range(len(pts)), key=lambda q: (pts[q][1] - here[0]) ** 2 + (pts[q][2] - here[1]) ** 2)
                i, x, y = pts.pop(j); order.append(i); here = np.array([x, y])
            n = len(order); gap = float(np.clip((a1 - t0 - 0.4) / max(1, n), 0.18, 0.45))
            times = [round(t0 + q * gap, 3) for q in range(n)]
            sched["marks"].append(dict(key=key, order=order, times=times))
            allm = [m for m in snap["marks"] if m["key"] == key]
            for q, i in enumerate(order):
                add(times[q], allm[i]["x"] / Wp, allm[i]["y"] / Hp, 1)
            cur = np.array([allm[order[-1]]["x"] / Wp, allm[order[-1]]["y"] / Hp])
            add(times[-1] + 0.25, cur[0], cur[1], 0)
    if path:
        first = path[0][0]; path.insert(0, [round(first - 1.4, 3), 1.15, 0.15, 0])
        last = max(p[0] for p in path); path.append([round(min(sec["look"][0] + 1.4, last + 1.6), 3), 1.2, -0.25, 0])
    path.sort(key=lambda p: p[0])
    json.dump(sched, open(f"{FILM}/{sid}/live.json", "w"), indent=1)
    c, h, flip = LAYOUT[sid]
    scene = dict(background=f"{DATA}/faune/scenes/bg-{sid}-real.png", easel=f"{ASSETS}/easel-green.png", brush=f"{ASSETS}/brush-green.png",
                 wand_img=f"{ASSETS}/wand-green.png", target=f"{FILM}/{sid}/target.png", paint_frames=f"{FILM}/{sid}/frames-paint",
                 live_frames=f"{FILM}/{sid}/frames-live", strokes=f"{FILM}/{sid}/strokes.json", range=[-sec["pre"], sec["L"]],
                 camera=sec["push"], live_start=sec["live_t0"], wand_path=path, canvas_center=c, canvas_height=h, flip=flip,
                 **ground(sec, sid),
                 full_height=0.94, brush_scale=0.52, wand_scale=0.42, paint_t0=0.0, relief=sec["push"])
    scene.update(tools(sid))
    json.dump(scene, open(f"{FILM}/{sid}/scene.json", "w"), indent=1)
    print(sid, "items", [it[1] for it in items], "wand", sec["wand"], "look", sec["look"])


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "sections":
        os.makedirs(FILM, exist_ok=True); S = section_times(); json.dump(S, open(f"{FILM}/plan.json", "w"), indent=1)
        for s in S: print(f"{s['id']:13s} {s['s0']:6.1f}-{s['s1']:6.1f} L {s['L']:5.1f}  paint 0-{s['paint'][1]:4.1f}  push {s['push']}  wand {s['wand']}  look {s['look']}  (W {s['W']})")
    elif cmd == "score": score(sys.argv[2])
    elif cmd == "live": live(sys.argv[2])
    elif cmd == "layout":                                        # re-place the easels in existing scenes (keeps backgrounds)
        secs = {x["id"]: x for x in section_times()}
        for sid in (sys.argv[2:] or [x for x, _ in SECTIONS]):
            p = f"{FILM}/{sid}/scene.json"; c = json.load(open(p)); cc, h, flip = LAYOUT[sid]
            c.pop("walk", None); c.update(canvas_center=cc, canvas_height=h, flip=flip, **ground(secs[sid], sid)); json.dump(c, open(p, "w"), indent=1)
            print(sid, cc, h, "camera", c["camera"], "lock", c["zoom_lock"], "grass", c["grass"])
    elif cmd == "tools":                                         # point existing scenes at their own tool set
        for sid in (sys.argv[2:] or [x for x, _ in SECTIONS]):
            p = f"{FILM}/{sid}/scene.json"; c = json.load(open(p)); c.update(tools(sid)); json.dump(c, open(p, "w"), indent=1); print(sid, TOOLSET[sid])
