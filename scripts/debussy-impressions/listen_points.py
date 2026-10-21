#!/usr/bin/env python3
"""Find the moments in each recording worth a careful listen.

  clipping   runs of >= 3 samples at full scale in the ORIGINAL file (grouped within 0.5 s)
  noise      short noise-like bursts (cough, chair, page turn, mic bump) in quiet passages:
             3-10 kHz energy >= 12 dB over its local median, spectrally flat, passage quiet
  clicks     single-sample jumps far larger than the local signal (digital clicks, edit points)
  dropouts   near-digital-silence (< -75 dBFS) for >= 80 ms inside the music
  hum        50/60 Hz mains peaks standing out in quiet passages
usage: .venv-reframe/bin/python listen_points.py key [key ...]   (keys from music/sources.json)
"""
import json, subprocess, sys
import numpy as np

DATA = "/Users/yqin/repo/playground/lucas-academy-video-data/debussy-impressions"
SR = 44100

def dec(path, ch=2):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vn", "-ac", str(ch), "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).reshape(-1, ch)

def mmss(t): return f"{int(t // 60)}:{t % 60:04.1f}"

def group(times, gap=0.5):
    out = []
    for t in times:
        if out and t - out[-1][1] <= gap: out[-1][1] = t; out[-1][2] += 1
        else: out.append([t, t, 1])
    return out

def analyse(key, src):
    orig = dec(f"{DATA}/music/{src['file']}")
    base = src["file"].rsplit("/", 1)[1].rsplit(".", 1)[0]
    x = dec(f"{DATA}/music/normalized/{base}.wav").mean(axis=1)
    res = {"key": key}
    a = np.abs(orig).max(axis=1) >= 0.999
    runs = np.where(a[2:] & a[1:-1] & a[:-2])[0] / SR
    res["clipping"] = [(round(s, 2), round(e, 2), n) for s, e, n in group(runs)]
    # frames
    hop = int(0.02 * SR); n = len(x) // hop; fr = x[: n * hop].reshape(n, hop)
    rms = 20 * np.log10(np.sqrt((fr ** 2).mean(axis=1)) + 1e-9)
    win = np.hanning(2048); nfft = 2048
    idx = np.arange(0, len(x) - nfft, hop)
    S = np.abs(np.fft.rfft(np.stack([x[i:i + nfft] * win for i in idx[: n]]), axis=1)) ** 2 + 1e-12
    f = np.fft.rfftfreq(nfft, 1 / SR)
    hb = 10 * np.log10(S[:, (f >= 3000) & (f <= 10000)].sum(axis=1))
    flat = np.exp(np.log(S[:, (f >= 1000) & (f <= 10000)]).mean(axis=1)) / S[:, (f >= 1000) & (f <= 10000)].mean(axis=1)
    m = len(hb); rmsm = rms[:m]
    k = int(3 / 0.02)
    from numpy.lib.stride_tricks import sliding_window_view
    pad = np.pad(hb, (k, k), mode="edge"); med_hb = np.median(sliding_window_view(pad, 2 * k + 1), axis=1)[:m]
    padr = np.pad(rmsm, (k, k), mode="edge"); med_r = np.median(sliding_window_view(padr, 2 * k + 1), axis=1)[:m]
    cand = np.where((hb - med_hb >= 12) & (flat > 0.25) & (med_r < -34))[0] * 0.02
    res["noise"] = [(round(s, 2), round(e, 2), c) for s, e, c in group(cand, 0.3) if e - s < 0.8]
    # clicks: sample jumps
    d = np.abs(np.diff(x)); loc = np.sqrt(np.convolve(x ** 2, np.ones(441) / 441, mode="same"))[1:] + 1e-4
    cl = np.where((d > 0.25) & (d > 12 * loc))[0] / SR
    res["clicks"] = [round(s, 2) for s, e, c in group(cl, 0.2)]
    # dropouts inside the music
    music = np.where(rms > rms.max() - 45)[0]
    inside = rms[music[0]: music[-1]] if len(music) else rms
    low = np.where(inside < -75)[0]
    dro = [(round((s + music[0]) * 0.02, 2), round((e + music[0]) * 0.02, 2)) for s, e, c in group(low * 1.0, 1.0) if (e - s) >= 4]
    res["dropouts"] = [(round(s * 1, 2), round(e, 2)) for s, e in dro]
    # hum: quiet frames, compare 50/60 Hz (+harmonics) bins against neighbours
    q = np.argsort(rmsm)[: max(20, m // 20)]
    Sq = S[q].mean(axis=0)
    def peak(fq):
        i = np.argmin(np.abs(f - fq)); nb = np.r_[Sq[max(1, i - 8): i - 2], Sq[i + 3: i + 9]]
        return 10 * np.log10(Sq[i - 1: i + 2].max() / np.median(nb))
    res["hum_db"] = {hz: round(max(peak(hz), peak(2 * hz)), 1) for hz in (50, 60)}
    res["duration"] = mmss(len(x) / SR)
    return res

def main(keys):
    src = {s["key"]: s for s in json.load(open(f"{DATA}/music/sources.json"))}
    out = {}
    for k in keys:
        r = analyse(k, src[k]); out[k] = r
        print(f"\n## {k} ({src[k]['piece'][:50]}, {r['duration']})")
        print("  clipping :", "; ".join(f"{mmss(s)}{'–' + mmss(e) if e > s else ''} ×{n}" for s, e, n in r["clipping"][:15]) or "none", f"({len(r['clipping'])} events)")
        print("  noise    :", "; ".join(f"{mmss(s)}" for s, e, c in r["noise"][:20]) or "none", f"({len(r['noise'])} events)")
        print("  clicks   :", "; ".join(mmss(t) for t in r["clicks"][:20]) or "none", f"({len(r['clicks'])})")
        print("  dropouts :", "; ".join(f"{mmss(s)}–{mmss(e)}" for s, e in r["dropouts"]) or "none")
        print("  hum dB   :", r["hum_db"])
    json.dump(out, open(f"{DATA}/music/listen-points.json", "w"), indent=1, default=float)

if __name__ == "__main__":
    main(sys.argv[1:])
