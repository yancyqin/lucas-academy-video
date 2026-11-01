"""beats.py — the beat grid of one variation of K. 265 in the Renzi recording, for drawing that follows the music.

Every section is 2/4 with both halves repeated (A A B A' B A'), so it is 96 beats long; the variation is played
steadily, so a dynamic-programming beat tracker (onset strength + a penalty for leaving the local period) finds the
grid. Each beat says whether a note starts on it (melody marks) and how strong it is (accents → bigger marks).

    python beats.py ONSETS.json START END OUT.json [--beats 96]
ONSETS.json comes from ../debussy-impressions/faune_onsets.py over a window a little wider than [START, END].
"""
import argparse, json
import numpy as np

FS = 200                                    # envelope samples per second


def envelope(onsets, a, b):
    env = np.zeros(int((b - a + 1) * FS))
    for o in onsets:
        i = int(round((o["t"] - a) * FS))
        if 0 <= i < len(env): env[i] += o["flux"]
    return np.convolve(env, np.hanning(7), "same")


def period(env):
    ac = np.correlate(env, env, "full")[len(env) - 1:]
    lags = np.arange(len(ac)) / FS
    sel = np.nonzero((lags > 0.28) & (lags < 0.75))[0]
    return lags[sel[np.argmax(ac[sel])]]


def track(env, p, tight=120.0):
    """Ellis-style DP: best chain of beats through the envelope with spacing close to p."""
    n = len(env); P = p * FS
    score = env.copy(); back = -np.ones(n, int)
    lo, hi = int(P * 0.75), int(P * 1.33)
    for i in range(n):
        j0, j1 = max(0, i - hi), i - lo
        if j1 <= j0: continue
        js = np.arange(j0, j1)
        pen = -tight * np.log((i - js) / P) ** 2
        k = np.argmax(score[js] + pen)
        score[i] = env[i] + score[js[k]] + pen[k]; back[i] = js[k]
    i = int(np.argmax(score[int(n - P * 1.5):])) + int(n - P * 1.5)
    path = []
    while i >= 0: path.append(i); i = back[i]
    return np.array(path[::-1]) / FS


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("onsets"); ap.add_argument("start", type=float)
    ap.add_argument("end", type=float); ap.add_argument("out"); ap.add_argument("--beats", type=int, default=96)
    a = ap.parse_args()
    on = [o for o in json.load(open(a.onsets))["onsets"] if a.start - 0.05 <= o["t"] <= a.end + 0.05]
    env = envelope(on, a.start, a.end)
    p = period(env)
    bt = a.start + track(env, p)
    bt = bt[bt >= on[0]["t"] - 0.08]                       # the grid starts on the first note
    ts = np.array([o["t"] for o in on]); fl = np.array([o["flux"] for o in on]); hz = np.array([o["hz"] for o in on])
    strong = [o["t"] for o in on if o["flux"] >= 0.6 and o["t"] <= a.end]
    cadence = strong[-1] if strong else on[-1]["t"]               # the section's last strong note: the picture is done
    bt = bt[bt <= cadence + 0.05]
    beats = []
    for i, t in enumerate(bt):
        near = np.nonzero(np.abs(ts - t) < 0.07)[0]
        k = near[np.argmax(fl[near])] if len(near) else None
        nxt = bt[i + 1] if i + 1 < len(bt) else t + p
        inside = np.nonzero((ts > t + 0.03) & (ts < nxt - 0.03))[0]          # notes between this beat and the next
        beats.append({"i": i, "t": round(float(ts[k] if k is not None else t), 3), "attack": k is not None,
                      "strength": round(float(fl[k]) if k is not None else 0.0, 3),
                      "hz": round(float(hz[k]), 1) if k is not None else None, "subnotes": int(len(inside))})
    s = np.array([b["strength"] for b in beats]); top = np.percentile(s[s > 0], 90) if (s > 0).any() else 1
    for b in beats: b["loud"] = round(min(1.0, b["strength"] / top), 3)
    out = {"range": [a.start, a.end], "period": round(float(p), 4), "n": len(beats), "cadence": round(float(cadence), 3),
           "form": {"A": [0, 16], "A2": [16, 32], "BA": [32, 64], "BA2": [64, 96]}, "beats": beats}
    json.dump(out, open(a.out, "w"), indent=1)
    gaps = np.diff([b["t"] for b in beats])
    print(f"period {p:.3f}s  beats {len(bt)} -> kept {len(beats)}  first {beats[0]['t']}  last {beats[-1]['t']}  "
          f"gap min/med/max {gaps.min():.3f}/{np.median(gaps):.3f}/{gaps.max():.3f}  no-attack {sum(not b['attack'] for b in beats)}")


if __name__ == "__main__":
    main()
