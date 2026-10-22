#!/usr/bin/env python3
"""Plan the 月光 reveals: each painting is revealed on the FIRST strong accent once it is ready, then rests.

Owner notes, 2026-10-16:
  v4  "照片到印象派画作带一点模糊 光暗一些，重音的时候把最后的作品亮出来 带视觉冲击 停一下 再进入下一个"
  v5  "有时候低音重音该亮没亮 等了下一个重音才亮" -> never skip a strong accent: the reveal is the first strong
      accent after the minimum build (photo clear + veil);
      "重音完了要多有一些时间慢慢开始fade 重音消弱的感觉，切换太快太不自然" -> rest >= HOLD_MIN after the reveal,
      then a slow FADE s dissolve into the next photo;
      "如果画作多了 你可以建议删除，优先选择画面凌乱的" -> shots marked "drop": true are skipped (clutter.py ranks them).
Strong accents (accents.py): a new bass note that stands out (s_bass >= 0.25, s_loud >= 1.0dB) or any accent scoring >= 0.95.
DP over the strong accents, one reveal per kept shot in order: shot k+1 can reveal on accent j' after accent j iff some
hold in [HOLD_MIN, HOLD_MAX] makes j' the first strong accent at or after (fade end + BUILD_MIN). Cost = DRIFT*|t - target|
- score; target = where the shot revealed in v4 ("reveal_v4"). Writes "at" = fade end (the next photo is fully there),
"xf_in" = fade length, "reveal_at", "reveal_type", "intensity". Edit-list "xfade_mode": "end".
usage: python3 plan_reveals.py edits/03-clair.json DATA/music/accents-clair.json
"""
import json, sys

HOLD_MIN, HOLD_MAX, HOLD_PREF, FADE, BUILD_MIN = 3.0, 6.5, 4.2, 2.2, 3.3
LATE = 2.0   # no strong accent may sound in the last LATE s before a reveal (it would make the reveal feel late)
# v6 review (Fable 5.1 advisor): in the loudest 20 % the notes are dense - relax there, or every climax is missed
LOUD_LATE, LOUD_HOLD_MIN, QUIET_FADE = 0.8, 2.5, 2.6
CURVE = None   # music/register-clair.json (register_curve.py), loaded in main
FIRST_MIN, LAST_MAX = 5.0, 297.0
DB_LO, DB_HI = -27.0, -11.0
SNAP_AT = [(76.0, 90.0), (155.0, 176.0)]                          # rubato peak, the two climax surges
BLOOM_AT = [(0.0, 58.0), (178.0, 205.0), (285.0, 400.0)]          # soft opening, calming + theme return, morendo
def kind(t, db):
    """v6 review: snap only on loud accents in the rising/climax passages; bloom for quiet accents, the opening
    (unless loud) and everything from the arpeggio echo on; firm otherwise."""
    if db >= -13.0 and any(a <= t < b for a, b in SNAP_AT): return "snap"
    if t >= 262.0 or db < -18.5 or (t < 58.0 and db < -12.0): return "bloom"
    return "firm"

def strong(o): return (o["s_bass"] >= 0.25 and o["s_loud"] >= 1.0) or o["score"] >= 0.95 or (o["db"] >= -13.5 and o["score"] >= 0.6)
def value(o): return o["score"] + 0.4 * min(max((o["db"] + 20.0) / 8.0, 0.0), 1.0)   # loud peaks win close calls

def at(arr, t):
    i = min(max(int(round((t - CURVE["t"][0]) / 0.1)), 0), len(arr) - 1); return arr[i]
def loud(t): return at(CURVE["lst"], t) >= CURVE["p80"]                    # top 20 % short-term loudness
def quiet(t): return at(CURVE["lst"], t) <= CURVE["p30"]
def late(t): return LOUD_LATE if loud(t) else LATE
def hold_min(t): return LOUD_HOLD_MIN if loud(t) else HOLD_MIN
def fade(t): return QUIET_FADE if quiet(t) else FADE
def decay(t):
    """Seconds until the sound falls 6 dB below its peak just after the accent at t (the fade starts when the chord has died)."""
    db = CURVE["db"]; i0 = int(round((t - CURVE["t"][0]) / 0.1)); pk = max(db[i0:i0 + 4])
    for i in range(i0 + 4, min(i0 + 70, len(db))):
        if db[i] <= pk - 6: return (i - i0) * 0.1
    return HOLD_MAX

def main(edit, acc):
    global CURVE
    ed = json.load(open(edit)); A = json.load(open(acc))["onsets"]
    CURVE = json.load(open(acc.replace("accents-", "register-")))
    ls = sorted(CURVE["lst"]); CURVE["p80"] = ls[int(0.8 * len(ls))]; CURVE["p30"] = ls[int(0.3 * len(ls))]
    S = [o for o in A if strong(o)]; T = [o["t"] for o in S]; n = len(S)
    allshots = ed["shots"]
    for s in allshots: s.setdefault("reveal_v4", s.get("reveal_at", s["at"]))
    shots = [s for s in allshots if not s.get("drop")]; K = len(shots)
    LANDMARK = {"beijing-tower": 81.7, "honfleur": 162.0, "night-1": 171.8, "dubrovnik": 197.5, "frozen-lake": 268.3, "eave-moon": 293.0}
    tgt = [s.get("target", LANDMARK.get(s["id"])) for s in shots]       # only musical landmarks pull a reveal in time
    def link(j, jj):
        """fade end c for a reveal on S[jj] after a reveal on S[j]; None if impossible. Returns (c, penalty)."""
        hm = hold_min(T[j]); pref = min(max(decay(T[j]), HOLD_PREF), HOLD_MAX); F = fade(T[j] + pref)
        lo = max(T[j] + hm + F, T[jj - 1] - BUILD_MIN + 0.05); hi = min(T[j] + HOLD_MAX + F, T[jj] - BUILD_MIN)
        if lo > hi: return None
        c = min(max(T[j] + pref + F, lo), hi)
        if any(max(c, T[jj] - late(T[jj])) < t < T[jj] - 0.05 for t in T[j + 1:jj]): return None
        build = T[jj] - c; pen = 0.12 * max(0.0, build - 7.0)          # long builds = a static photo
        for t in T[j + 1:jj]:                                           # a strong accent passing while the photo is up
            if t > c: pen += 0.5 if t > T[jj] - min(6.0, build - 1.2) else 0.2
        return c, pen
    INF = 1e18
    cost = [[INF] * n for _ in range(K)]; back = [[-1] * n for _ in range(K)]
    def drift(k, t): return 0.08 * abs(t - tgt[k]) if tgt[k] is not None else 0.0
    for j in range(n):
        if T[j] >= FIRST_MIN and (j == 0 or T[j - 1] < FIRST_MIN):
            cost[0][j] = drift(0, T[j]) - value(S[j])
    for k in range(1, K):
        for j in range(n):
            if cost[k - 1][j] >= INF: continue
            for jj in range(j + 1, n):
                if T[jj] < T[j] + LOUD_HOLD_MIN + FADE + BUILD_MIN: continue
                if T[jj - 1] >= T[j] + HOLD_MAX + QUIET_FADE + BUILD_MIN: break
                if k == K - 1 and T[jj] > LAST_MAX: break
                L = link(j, jj)
                if L is None: continue
                c = cost[k - 1][j] + drift(k, T[jj]) - value(S[jj]) + L[1]
                if c < cost[k][jj]: cost[k][jj] = c; back[k][jj] = j
    j = min(range(n), key=lambda j: cost[K - 1][j]); assert cost[K - 1][j] < INF / 2, "no feasible plan - drop more shots"
    pick = [0] * K
    for k in range(K - 1, -1, -1): pick[k] = j; j = back[k][j]
    R = [T[j] for j in pick]
    ends = [0.0] + [round(link(pick[k - 1], pick[k])[0], 3) for k in range(1, K)]
    for k, s in enumerate(shots):
        o = S[pick[k]]; loud = min(1.0, max(0.0, (o["db"] - DB_LO) / (DB_HI - DB_LO)))
        s.update({"at": ends[k], "xf_in": fade(R[k - 1] + min(max(decay(R[k - 1]), HOLD_PREF), HOLD_MAX)) if k else FADE, "reveal_at": round(o["t"], 3), "accent": o["score"], "accent_db": o["db"],
                  "intensity": round(0.5 * loud + 0.5 * o["score"], 3),
                  "reveal_type": kind(o["t"], o["db"])})
    ed["style"] = "reveal"; ed["xfade_mode"] = "end"
    ed["end"] = 306.5; ed["fade_out"] = 5.0; ed["fade_in"] = 4.0
    json.dump(ed, open(edit, "w"), ensure_ascii=False, indent=1)
    for k, s in enumerate(shots):
        nxt = shots[k + 1]["at"] - shots[k + 1]["xf_in"] if k + 1 < K else ed["end"] - ed["fade_out"]
        fd = shots[k + 1]["xf_in"] if k + 1 < K else ed["fade_out"]
        print(f"{k + 1:2d} {s['id'][:14]:14s} photo {s['at']:6.1f}  reveal {s['reveal_at']:6.1f} ({s['accent']:.2f}, {s['accent_db']:5.1f} dB) {s['reveal_type']:5s}  build {s['reveal_at'] - s['at']:4.1f}  rest {nxt - s['reveal_at']:4.1f}  fade {fd}")
    print(K, "shots; dropped:", [s["id"] for s in allshots if s.get("drop")])

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
