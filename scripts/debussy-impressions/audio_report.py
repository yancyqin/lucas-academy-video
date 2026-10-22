#!/usr/bin/env python3
"""Measure each candidate recording: loudness, peaks, bandwidth, noise floor, clipping, silence, live-applause hints.

usage: /usr/bin/python3 audio_report.py <file> [<file> ...]   (needs numpy + ffmpeg on PATH)
"""
import json, subprocess, sys, re
import numpy as np

SR = 44100

def decode(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vn", "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).reshape(-1, 2)

def ebur128(path):
    err = subprocess.run(["ffmpeg", "-nostats", "-hide_banner", "-i", path, "-vn", "-af", "ebur128=peak=true", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    tail = err[err.rfind("Summary:"):]
    g = lambda pat: float(re.search(pat, tail).group(1))
    return {"I": g(r"I:\s+(-?[\d.]+) LUFS"), "LRA": g(r"LRA:\s+([\d.]+) LU"), "TP": g(r"Peak:\s+(-?[\d.]+) dBFS")}

def db(x): return 20 * np.log10(max(float(x), 1e-12))

def analyse(path):
    x = decode(path); mono = x.mean(axis=1); n = len(mono); dur = n / SR
    # 50 ms RMS envelope
    hop = int(0.05 * SR); frames = n // hop
    env = np.sqrt((mono[:frames * hop].reshape(frames, hop) ** 2).mean(axis=1) + 1e-20)
    env_db = 20 * np.log10(env)
    peak_db = float(env_db.max())
    # leading / trailing silence: below peak-50 dB
    thr = peak_db - 50
    loud = np.where(env_db > thr)[0]
    lead = float(loud[0] * 0.05) if len(loud) else 0.0
    trail = float((frames - 1 - loud[-1]) * 0.05) if len(loud) else 0.0
    # noise floor: 10th percentile of 50 ms RMS over the musical span
    span = env_db[loud[0]:loud[-1] + 1] if len(loud) else env_db
    floor = float(np.percentile(span, 2))
    # bandwidth: long-term spectrum, highest frequency within 60 dB of the 200 Hz–4 kHz average level
    nfft = 8192
    segs = mono[: (n // nfft) * nfft].reshape(-1, nfft)
    loud_segs = segs[np.argsort((segs ** 2).mean(axis=1))[-min(400, len(segs)):]]
    spec = (np.abs(np.fft.rfft(loud_segs * np.hanning(nfft), axis=1)) ** 2).mean(axis=0)
    f = np.fft.rfftfreq(nfft, 1 / SR); sdb = 10 * np.log10(spec + 1e-20)
    ref = sdb[(f > 200) & (f < 4000)].mean()
    above = np.where(sdb > ref - 60)[0]
    bw = float(f[above[-1]]) if len(above) else 0.0
    # hiss: level 10–16 kHz relative to ref during the quietest 10 % of segments
    q_segs = segs[np.argsort((segs ** 2).mean(axis=1))[: max(1, len(segs) // 10)]]
    qspec = 10 * np.log10((np.abs(np.fft.rfft(q_segs * np.hanning(nfft), axis=1)) ** 2).mean(axis=0) + 1e-20)
    hiss = float(qspec[(f > 10000) & (f < 16000)].mean() - ref)
    # clipping: runs of >=3 consecutive samples at |x| >= 0.999
    a = np.abs(x).max(axis=1) >= 0.999
    clips = int(np.sum(a[2:] & a[1:-1] & a[:-2]))
    # applause hint: spectral flatness of the last 8 s vs the median of the piece (applause ~ white noise)
    def flatness(sig):
        s = np.abs(np.fft.rfft(sig[: (len(sig) // 4096) * 4096].reshape(-1, 4096) * np.hanning(4096), axis=1)) ** 2 + 1e-20
        return float(np.median(np.exp(np.log(s).mean(axis=1)) / s.mean(axis=1)))
    end_flat = flatness(mono[max(0, int((dur - trail - 8) * SR)): int((dur - trail) * SR)])
    mid_flat = flatness(mono[int(dur * 0.4 * SR): int(dur * 0.6 * SR)])
    r = {"file": path.split("/")[-1], "dur": round(dur, 1), "lead_s": round(lead, 2), "trail_s": round(trail, 2),
         "floor_dB_rel_peak": round(floor - peak_db, 1), "bandwidth_kHz": round(bw / 1000, 1), "hiss_dB": round(hiss, 1),
         "clip_runs": clips, "end_flatness": round(end_flat, 3), "mid_flatness": round(mid_flat, 3)}
    r.update(ebur128(path))
    return r

if __name__ == "__main__":
    out = [analyse(p) for p in sys.argv[1:]]
    for r in out:
        print(json.dumps(r, ensure_ascii=False, default=float))
