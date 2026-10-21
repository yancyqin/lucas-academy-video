#!/usr/bin/env python3
"""Move each cut of an edit list onto an accented note (owner 2026-10-16: "重音的时候换照片").

For every shot but the first, look at the onsets in [at-BACK, at+FWD] (accents.json from accents.py) and take the
best by score - DRIFT*|offset|, keeping every shot >= MIN_SHOT long. The phrase-based cut is kept as "at_phrase".
Also picks "reveal_at": the strongest accent 1.2-3.0 s after the cut, where the photo starts dissolving into the
painting. Sets xfade/xfade_mid so the cross-fade is short and centred on the accent.
usage: python3 snap_cuts.py edits/03-clair.json DATA/music/accents-clair.json [--xfade 0.8]
"""
import argparse, json

BACK, FWD, DRIFT, MIN_SHOT = 2.0, 3.0, 0.03, 5.0

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("edit"); ap.add_argument("accents"); ap.add_argument("--xfade", type=float, default=0.8)
    a = ap.parse_args()
    ed = json.load(open(a.edit)); A = json.load(open(a.accents))["onsets"]
    shots = ed["shots"]; end = ed["end"]
    for s in shots: s.setdefault("at_phrase", s["at"])
    prev = 0.0
    for i, s in enumerate(shots):
        if i == 0: continue
        t = s["at_phrase"]
        nxt = shots[i + 1]["at_phrase"] if i + 1 < len(shots) else end
        cands = [o for o in A if t - BACK <= o["t"] <= t + FWD and o["t"] - prev >= MIN_SHOT and nxt - o["t"] >= MIN_SHOT - 1.0]
        if cands:
            best = max(cands, key=lambda o: o["score"] - DRIFT * abs(o["t"] - t))
            s["at"] = round(best["t"], 3); s["accent"] = best["score"]
        prev = s["at"]
    for i, s in enumerate(shots):
        nxt = shots[i + 1]["at"] if i + 1 < len(shots) else end
        lo, hi = s["at"] + 1.2, min(s["at"] + 3.0, nxt - 3.0)
        c = [o for o in A if lo <= o["t"] <= hi]
        if c: s["reveal_at"] = round(max(c, key=lambda o: o["score"])["t"], 3)
        else: s.pop("reveal_at", None)
    ed["xfade"] = a.xfade; ed["xfade_mid"] = 0.5
    json.dump(ed, open(a.edit, "w"), ensure_ascii=False, indent=1)
    sc = {o["t"]: o["score"] for o in A}
    for i, s in enumerate(shots):
        nxt = shots[i + 1]["at"] if i + 1 < len(shots) else end
        old = max([o["score"] for o in A if abs(o["t"] - s["at_phrase"]) < 0.12] or [0])
        print(f"{i + 1:2d} {s['id'][:14]:14s} {s['at_phrase']:7.2f} ({old:.2f}) -> {s['at']:7.2f} ({s.get('accent', 0):.2f})  shot {nxt - s['at']:5.2f} s  reveal at +{s.get('reveal_at', s['at']) - s['at']:.2f}")

if __name__ == "__main__":
    main()
