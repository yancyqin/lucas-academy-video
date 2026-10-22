#!/usr/bin/env python3
"""Plan picture changes for the breathing style (owner 2026-10-16: "按照旋律来好像在呼吸一样，不用定格").

Picture changes happen in the music's breaths: the deep minima of the breath curve (breath_curve.py), where the
picture is already dark and soft; the next image dissolves in through the breath and brightens with the next phrase.
Candidates = local minima of b (+-0.6 s) with prominence >= 0.15 (how far b rises on both sides within 3 s).
DP picks one cut per shot change, maximising prominence + depth - DRIFT*|t - target| with shot lengths in
[MIN_SHOT, MAX_SHOT]; target = the shot's previous start (`at` of the reveal plan), so images keep their musical place.
Writes "at" = dissolve end (cut + XF_AFTER), "xf_in" = XF_BEFORE + XF_AFTER, "breath_cut" = the minimum's time.
usage: python3 plan_breaths.py edits/03-clair.json DATA/music/breath-clair.json
"""
import json, sys

MIN_SHOT, MAX_SHOT, DRIFT = 7.0, 20.0, 0.04
XF_BEFORE, XF_AFTER = 1.6, 0.8            # the dissolve runs through the breath and is complete as the phrase returns

def main(edit, curve):
    ed = json.load(open(edit)); C = json.load(open(curve)); b = C["b"]; fps = C["fps"]; n = len(b)
    w, w3 = int(0.6 * fps), int(3.0 * fps)
    cand = []
    for i in range(w3, n - w3):
        if b[i] == min(b[i - w:i + w + 1]):
            prom = min(max(b[i - w3:i]), max(b[i + 1:i + w3 + 1])) - b[i]
            if prom >= 0.15 and (not cand or i - cand[-1][0] > fps): cand.append((i, prom, b[i]))
    T = [i / fps for i, _, _ in cand]; V = [p + (0.5 - d) for _, p, d in cand]
    shots = [s for s in ed["shots"] if not s.get("drop")]; K = len(shots)
    for s in shots: s.setdefault("at_reveal_plan", s["at"])
    tgt = [s["at_reveal_plan"] - 1.2 for s in shots]          # the old dissolve's middle
    end = ed["end"]; INF = 1e18; m = len(T)
    cost = [[INF] * m for _ in range(K)]; back = [[-1] * m for _ in range(K)]
    for j in range(m):
        if MIN_SHOT <= T[j] <= MAX_SHOT: cost[1][j] = -V[j] + DRIFT * abs(T[j] - tgt[1])
    for k in range(2, K):
        for j in range(m):
            if cost[k - 1][j] >= INF: continue
            for jj in range(j + 1, m):
                L = T[jj] - T[j]
                if L < MIN_SHOT: continue
                if L > MAX_SHOT: break
                c = cost[k - 1][j] - V[jj] + DRIFT * abs(T[jj] - tgt[k])
                if c < cost[k][jj]: cost[k][jj] = c; back[k][jj] = j
    last = [j for j in range(m) if cost[K - 1][j] < INF and MIN_SHOT <= end - 4 - T[j] <= MAX_SHOT + 6]
    j = min(last, key=lambda j: cost[K - 1][j])
    cuts = [0.0] * K
    for k in range(K - 1, 0, -1): cuts[k] = T[j]; j = back[k][j]
    for k, s in enumerate(shots):
        if k == 0: s.update({"at": 0.0, "xf_in": XF_BEFORE + XF_AFTER, "breath_cut": 0.0})
        else: s.update({"at": round(cuts[k] + XF_AFTER, 3), "xf_in": XF_BEFORE + XF_AFTER, "breath_cut": round(cuts[k], 3)})
        for key in ("reveal_at", "reveal_type", "accent", "accent_db", "intensity"): s.pop(key, None)
    ed["style"] = "breath"; ed["xfade_mode"] = "end"; ed["breath"] = {"curve": curve.split("debussy-impressions/")[-1]}
    ed.pop("music_light", None)
    json.dump(ed, open(edit, "w"), ensure_ascii=False, indent=1)
    for k, s in enumerate(shots):
        nxt = shots[k + 1]["breath_cut"] if k + 1 < K else end
        print(f"{k + 1:2d} {s['id'][:14]:14s} cut {s['breath_cut']:6.1f} ({int(s['breath_cut'] // 60)}:{s['breath_cut'] % 60:04.1f})  length {nxt - s['breath_cut']:5.1f}")

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
