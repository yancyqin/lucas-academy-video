import json, sys, numpy as np, cv2
sys.path.insert(0, ".")
import film
C = json.load(open(sys.argv[1])); rng = np.random.default_rng(2)
for s_ in C["sections"]: s_.setdefault("lead_in", C.get("lead_in", 0.0))
secs = [film.Section(s, rng) for s in C["sections"]]
poses = C.get("poses", [[-1.2, [0, 6]], [0.9, [-8, 4]]])
REST = np.array([1765.0, 690.0])
for i, s in enumerate(secs):
    s.land = 0.2 if i == 0 else max(secs[i - 1].P.get("cadence", secs[i - 1].finish) + 0.25, s.start - 1.6); s.ready = s.land + (0.8 if i == 0 else C.get("slide", 1.25))
for i, s in enumerate(secs):
    s.leave = secs[i + 1].land if i + 1 < len(secs) else s.end
    M, _ = film.sheet_matrix(s.pw, s.ph, *poses[i % len(poses)]); s.M = M
    Mi = cv2.invertAffineTransform(M); s.rest = Mi[:, :2] @ REST + Mi[:, 2] - film.SHEET_MARGIN
for i, s in enumerate(secs):
    t_end = secs[i + 1].land if i + 1 < len(secs) else s.end
    ts = np.arange(s.ready, t_end, 1 / 30)
    out = [s.tool(t, s.rest) for t in ts]
    P = np.array([film.to_frame(s.M, o[0]) for o in out]); L = np.array([o[1] for o in out])
    d = np.hypot(*np.diff(P, axis=0).T)
    print(f"section {i}: frames {len(ts)}, max {d.max():.0f}px/frame, p99 {np.percentile(d, 99):.0f}, >40px: {(d > 40).sum()}, >80px: {(d > 80).sum()}")
    print("   worst at", [(round(float(ts[k]), 2), int(d[k])) for k in np.argsort(d)[::-1][:10]])
    flips = int(np.sum(np.abs(np.diff(L)) > 0.08))
    print(f"   lift steps >0.08/frame {flips} ({flips / (ts[-1] - ts[0]):.1f}/s)")
