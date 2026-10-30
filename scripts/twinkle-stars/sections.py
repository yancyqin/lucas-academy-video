"""sections.py — where one picture ends and the next begins in a piece: the natural breaths of the recording.

For n pictures, each boundary is searched within ±25 % of a section around its even split (duration·k/n): the deepest dip
in the smoothed loudness there (a breath, a held cadence, a rest), then the first strong note after it (the next phrase
starts there). Also writes every piece's beat file for crayon.py (one mark per note, thinned to a minimum spacing that
follows the piece's own pace; the cadence = the last strong note before the section ends).

    python sections.py WAV N OUT.json [--onsets ONSETS.json] [--gap 0.3] [--fixed T1,T2,... --per N1,N2,...]
--fixed: boundaries that must be kept (movement breaks); --per: how many pictures between consecutive fixed points.
"""
import argparse, json, subprocess, sys, pathlib
import numpy as np
from scipy.io import wavfile

HERE = pathlib.Path(__file__).parent


def loudness(wav):
    sr, x = wavfile.read(wav)
    x = x.astype(np.float32); x = x.mean(1) if x.ndim > 1 else x; x /= (np.abs(x).max() + 1e-9)
    hop = int(sr * 0.05)
    rms = np.sqrt(np.convolve(x * x, np.ones(hop * 4) / (hop * 4), mode="same")[::hop] + 1e-12)
    db = 20 * np.log10(rms + 1e-9)
    k = 9; db_s = np.convolve(db, np.ones(k) / k, mode="same")
    return db_s, 0.05, len(x) / sr


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("wav"); ap.add_argument("n", type=int); ap.add_argument("out")
    ap.add_argument("--onsets"); ap.add_argument("--gap", type=float, default=0.3, help="minimum seconds between marks")
    ap.add_argument("--fixed", default=""); ap.add_argument("--per", default="")
    ap.add_argument("--win", type=float, default=0.25, help="search ± this share of a section around the even split")
    a = ap.parse_args()
    db, dt, dur = loudness(a.wav)
    if not a.onsets:
        a.onsets = a.out.replace(".json", "-onsets.json")
        subprocess.run([sys.executable, str(HERE.parent / "debussy-impressions/faune_onsets.py"), a.wav, a.onsets,
                        "--from", "0", "--to", str(dur), "--quiet"], check=True)
    on = json.load(open(a.onsets))["onsets"]
    ts = np.array([o["t"] for o in on]); fl = np.array([o["flux"] for o in on])
    strong = ts[fl >= np.percentile(fl, 60)]
    first = float(ts[0]); last = float(strong[strong < dur - 0.3][-1]) if len(strong) else float(ts[-1])
    def split(lo, hi, n):                                         # n pictures between lo and hi, at the breaths
        out = []
        for k in range(1, n):
            c = lo + (hi - lo) * k / n; w = (hi - lo) / n * a.win
            i0, i1 = int((c - w) / dt), int((c + w) / dt)
            j = i0 + int(np.argmin(db[i0:i1]))                        # the deepest breath near the even split
            after = strong[strong > j * dt + 0.05]
            out.append(float(after[0]) if len(after) else j * dt)
        return out
    if a.fixed:                                                   # movement breaks stay where they are
        fx = [float(v) for v in a.fixed.split(",")]; per = [int(v) for v in a.per.split(",")]
        assert len(per) == len(fx) + 1 and sum(per) == a.n
        edges = [first] + [float(ts[ts > f][0]) for f in fx] + [last]       # a movement may begin softly
        bounds = [first]
        for (lo, hi), n in zip(zip(edges[:-1], edges[1:]), per):
            bounds += split(lo, hi, n) + ([hi] if hi != last else [])
    else:
        bounds = [first] + split(first, last, a.n)
    bounds.append(dur)
    sections = []
    for k in range(a.n):
        s0, s1 = bounds[k], bounds[k + 1]
        inside = [o for o in on if s0 - 0.02 <= o["t"] < s1 - 0.05]
        marks = []                                                  # one mark per note, at least `gap` apart (keep the stronger)
        for o in inside:
            if marks and o["t"] - marks[-1]["t"] < a.gap:
                if o["flux"] > marks[-1]["flux"]: marks[-1] = o
                continue
            marks.append(o)
        fx = np.array([m["flux"] for m in marks]); top = np.percentile(fx, 90) if len(fx) else 1
        cad = [m["t"] for m in marks if m["t"] < s1 - 0.6]                # the last note (not the next phrase's pickup)
        beats = [{"i": i, "t": round(m["t"], 3), "attack": True, "strength": round(m["flux"], 3), "hz": m["hz"],
                  "loud": round(min(1.0, m["flux"] / top), 3), "subnotes": 0} for i, m in enumerate(marks)]
        sections.append({"start": round(s0, 3), "end": round(s1, 3), "cadence": round(cad[-1] if cad else s1 - 0.5, 3),
                         "n": len(beats), "beats": beats})
    json.dump({"wav": a.wav, "duration": dur, "bounds": bounds, "sections": sections}, open(a.out, "w"), indent=1)
    for k, s in enumerate(sections):
        print(f"  picture {k + 1}: {s['start']:7.2f} → {s['end']:7.2f} ({s['end'] - s['start']:5.1f} s), {s['n']} marks, last strong note {s['cadence']}")


if __name__ == "__main__":
    main()
