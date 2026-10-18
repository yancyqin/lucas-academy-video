#!/usr/bin/env python3
"""Find the accented notes in a recording, so picture changes can land on them (owner 2026-10-16:
"重音的时候换照片").

An onset = a peak of spectral flux (log-magnitude increase). Its accent strength is LOCAL salience,
i.e. how much the note stands out from the notes within +-2 s (a soft piece still has accents):
  * loudness peak after the onset (dB above the local median)      weight 0.40
  * low-band flux 30-260 Hz (a new bass note = new harmony = downbeat) weight 0.35
  * broadband flux (how hard / how many notes are struck)            weight 0.25
z-scored, weighted, then ranked 0..1 across the piece; accents.json lists every onset with its score.
usage: .venv-reframe/bin/python accents.py music/normalized/<file>.wav OUT.json
"""
import json, subprocess, sys
import numpy as np

DATA = "/Users/yqin/repo/playground/lucas-academy-video-data/debussy-impressions"
SR, N, HOP = 22050, 2048, 256

def rank(v):
    o = np.argsort(np.argsort(v)); return o / max(len(v) - 1, 1)

def main(wav, out):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", f"{DATA}/{wav}", "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True).stdout
    x = np.frombuffer(raw, np.float32)
    nfr = (len(x) - N) // HOP
    fr = np.lib.stride_tricks.as_strided(x, shape=(nfr, N), strides=(x.strides[0] * HOP, x.strides[0]))
    mag = np.abs(np.fft.rfft(fr * np.hanning(N).astype(np.float32), axis=1)).astype(np.float32)
    f = np.fft.rfftfreq(N, 1 / SR); t = (np.arange(nfr) * HOP + N / 2) / SR
    lm = np.log1p(1000 * mag); d = np.maximum(lm[1:] - lm[:-1], 0)
    broad = np.concatenate([[0], d[:, f > 60].sum(1)]); low = np.concatenate([[0], d[:, (f > 30) & (f < 260)].sum(1)])
    db = 20 * np.log10(np.sqrt((fr ** 2).mean(1)) + 1e-9)
    sm = lambda v, k: np.convolve(v, np.ones(k) / k, "same")
    B, Lw = sm(broad, 3), sm(low, 3)
    k = int(1.0 * SR / HOP)
    med = np.array([np.median(B[max(0, i - k):i + k]) for i in range(len(B))])
    peaks = [i for i in range(2, len(B) - 2) if B[i] >= B[i - 1] and B[i] > B[i + 1] and B[i] > 1.5 * med[i] + 3]
    keep = []                                          # merge peaks closer than 60 ms (a rolled chord = one event)
    for i in peaks:
        if keep and t[i] - t[keep[-1]] < 0.06:
            if B[i] > B[keep[-1]]: keep[-1] = i
        else: keep.append(i)
    P = np.array(keep)
    bro = B[P]; lo = np.array([Lw[max(0, i - 2):i + 4].max() for i in P])
    w25 = int(0.25 * SR / HOP)
    rise = np.array([db[i:i + 6].max() - db[max(0, i - w25):i - 1].mean() if i > 2 else 0 for i in P])
    ts = t[P]
    prom = np.array([bro[j] / (np.median(bro[(np.abs(ts - ts[j]) < 1.0)]) + 1e-6) for j in range(len(P))])
    loud = np.array([db[i:i + 10].max() for i in P])
    # local salience: how much this note stands out from the notes within +-2 s (what the ear hears as an accent)
    def local(v, j, win=2.0):
        m = np.abs(ts - ts[j]) < win
        return v[j] - np.median(v[m])
    s_loud = np.array([local(loud, j) for j in range(len(P))])                     # dB above the local median
    s_bass = np.array([local(np.log1p(lo), j) for j in range(len(P))])             # new bass note vs neighbours
    s_hit = np.array([local(np.log1p(bro), j) for j in range(len(P))])             # attack vs neighbours
    z = lambda v: (v - v.mean()) / (v.std() + 1e-9)
    score = 0.40 * z(s_loud) + 0.35 * z(s_bass) + 0.25 * z(s_hit)
    score = rank(score)
    res = [{"t": round(float(a), 3), "score": round(float(s), 3), "broad": round(float(b), 1), "bass": round(float(l), 1),
            "rise_db": round(float(r), 1), "prom": round(float(p), 2), "db": round(float(L), 1),
            "s_loud": round(float(sl), 2), "s_bass": round(float(sb), 2), "s_hit": round(float(sh), 2)}
           for a, s, b, l, r, p, L, sl, sb, sh in zip(ts, score, bro, lo, rise, prom, loud, s_loud, s_bass, s_hit)]
    json.dump({"wav": wav, "onsets": res}, open(out, "w"), indent=0)
    print(len(res), "onsets ->", out)

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
