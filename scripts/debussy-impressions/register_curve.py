#!/usr/bin/env python3
"""Loudness and register curves of a recording, 10 per second (for music-driven light).

  db      RMS loudness, dBFS, 0.4 s smoothing
  reg     register = log2 spectral centroid of 80 Hz - 5 kHz (octaves above 55 Hz), 0.6 s smoothing:
          higher = the music sits higher (treble), lower = bass-heavy
  bass    share of energy below 250 Hz (dB relative to total)
  treb    band ratio (E > 1 kHz - E 40-250 Hz) / E: steadier "how high the music sits" on piano
  lst     short-term loudness (3 s window), dB
usage: .venv-reframe/bin/python register_curve.py music/normalized/<file>.wav OUT.json
"""
import json, subprocess, sys
import numpy as np

DATA = "/Users/yqin/repo/playground/lucas-academy-video-data/debussy-impressions"
SR, N, HOP = 22050, 4096, 2205      # 0.1 s hop

def smooth(v, k):
    k = max(1, int(k)); return np.convolve(np.pad(v, (k, k), mode="edge"), np.ones(2 * k + 1) / (2 * k + 1), "same")[k:-k]

def main(wav, out):
    x = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", f"{DATA}/{wav}", "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True).stdout, np.float32)
    nfr = (len(x) - N) // HOP
    fr = np.lib.stride_tricks.as_strided(x, shape=(nfr, N), strides=(x.strides[0] * HOP, x.strides[0]))
    P = np.abs(np.fft.rfft(fr * np.hanning(N).astype(np.float32), axis=1)) ** 2
    f = np.fft.rfftfreq(N, 1 / SR); band = (f > 80) & (f < 5000)
    cen = (P[:, band] * f[band]).sum(1) / (P[:, band].sum(1) + 1e-12)
    reg = smooth(np.log2(np.maximum(cen, 60) / 55), 3)
    db = smooth(10 * np.log10(P.sum(1) / N + 1e-12), 2)
    bass = smooth(10 * np.log10((P[:, f < 250].sum(1) + 1e-12) / (P.sum(1) + 1e-12)), 3)
    tot = P[:, f > 40].sum(1) + 1e-12
    treb = smooth((P[:, f > 1000].sum(1) - P[:, (f > 40) & (f < 250)].sum(1)) / tot, 3)   # band ratio: + treble, - bass
    lst = 10 * np.log10(smooth(10 ** (db / 10), 15) + 1e-12)                              # short-term loudness (3 s window)
    t = (np.arange(nfr) * HOP + N / 2) / SR
    json.dump({"t": [round(float(v), 2) for v in t], "db": [round(float(v), 2) for v in db], "reg": [round(float(v), 3) for v in reg],
               "bass": [round(float(v), 2) for v in bass], "treb": [round(float(v), 4) for v in treb],
               "lst": [round(float(v), 2) for v in lst]}, open(out, "w"))
    print(nfr, "frames; reg range", round(float(np.percentile(reg, 5)), 2), round(float(np.percentile(reg, 95)), 2))

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
