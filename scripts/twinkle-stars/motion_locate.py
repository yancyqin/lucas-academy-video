"""motion_locate.py — where a piece's tool moves fastest, and what it is doing there (stroke, glide, approach).

    python motion_locate.py CONFIG.json [--top 4]
"""
import argparse, json
import numpy as np, cv2
import film

ap = argparse.ArgumentParser(); ap.add_argument("config"); ap.add_argument("--top", type=int, default=4)
a = ap.parse_args()
C = json.load(open(a.config)); rng = np.random.default_rng(2)
for s_ in C["sections"]: s_.setdefault("lead_in", C.get("lead_in", 0.0))
secs = [film.Section(s, rng) for s in C["sections"]]
poses = C.get("poses", [[-1.2, [0, 6]], [0.9, [-8, 4]]]); REST = np.array(C.get("rest", [1765.0, 690.0]), float)
for i, s in enumerate(secs):
    s.land = 0.2 if i == 0 else min(max(secs[i - 1].P.get("cadence", secs[i - 1].finish) + 0.25, s.start - C.get("approach", 1.6)), s.start - 1.6)
    s.ready = s.land + (0.8 if i == 0 else C.get("slide", 1.25))
for i, s in enumerate(secs):
    s.leave = secs[i + 1].land if i + 1 < len(secs) else s.end
    M, _ = film.sheet_matrix(s.pw, s.ph, *poses[i % len(poses)]); s.M = M
    Mi = cv2.invertAffineTransform(M); s.rest = Mi[:, :2] @ REST + Mi[:, 2] - film.SHEET_MARGIN
rows = []
for i, s in enumerate(secs):
    ts = np.arange(s.ready, secs[i + 1].land if i + 1 < len(secs) else s.end, 1 / 30)
    P = np.array([film.to_frame(s.M, s.tool(t, s.rest)[0]) for t in ts]); d = np.hypot(*np.diff(P, axis=0).T)
    for k in np.argsort(d)[::-1][:a.top]:
        t = ts[k]; S = s.strokes; state = f"after the last stroke ({S[-1]['t1']:.2f})"
        for j, st in enumerate(S):
            if st["t0"] <= t <= st["t1"]: state = f"in {st['kind']} #{j} ({st['t0']:.2f}–{st['t1']:.2f})"; break
            if t < st["t0"]: state = f"glide to #{j} {st['kind']} ({S[j - 1]['t1'] if j else s.ready:.2f} → {st['t0']:.2f})"; break
        rows.append((int(d[k]), i + 1, round(float(t), 2), state, round(s.ready, 2)))
for r in sorted(rows, reverse=True)[:12]:
    print(f"{r[0]:4d} px/frame  picture {r[1]}  t={r[2]}  {r[3]}  (ready {r[4]})")
