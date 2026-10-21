#!/usr/bin/env python3
"""The "breath" of a piano recording, 30 values per second, for picture that breathes with the melody.

Owner 2026-10-16 (月光): "不要突然亮定格。按照旋律来好像在呼吸一样，不用定格。低音变暗变fade 高音变亮变清晰，
主要旋律的速率强度，音乐的感觉来显示".

  mel   melody-band (500 Hz - 4 kHz) energy in dB, enveloped with attack 0.12 s / release 0.9 s: rises with each
        melody note and phrase swell, sinks in the breaths; fast melody keeps it up, slow melody makes it pulse
  reg   register: band ratio (E > 1 kHz - E 40-250 Hz) / E, smoothed 0.8 s: high music sits high, bass-heavy sits low
  b     breath 0..1 = 0.75 * melody + 0.25 * register, each mapped half globally (5-95 % of the piece: loud passages are
        brighter overall) and half locally (5-95 % within +-6 s: a soft passage still breathes visibly), then a 1.5 Hz
        low-pass so it never flickers
usage: .venv-reframe/bin/python breath_curve.py music/normalized/<file>.wav OUT.json
"""
import json, subprocess, sys
import numpy as np

DATA = "/Users/yqin/repo/playground/lucas-academy-video-data/debussy-impressions"
SR, FPS = 22050, 30
N, HOP = 2048, SR // 100                     # 100 Hz analysis

def env(x, att, rel, rate):
    up = 1 - np.exp(-1 / (rate * att)); dn = 1 - np.exp(-1 / (rate * rel)); out = np.empty_like(x); g = x[0]
    for i, v in enumerate(x): g += (v - g) * (up if v > g else dn); out[i] = g
    return out

def lp(x, fc, rate):
    a = 1 - np.exp(-2 * np.pi * fc / rate); y = np.empty_like(x); g = x[0]
    for i, v in enumerate(x): g += (v - g) * a; y[i] = g
    return y

def gl_norm(v, rate, win=6.0):
    lo, hi = np.percentile(v, 5), np.percentile(v, 95); g = np.clip((v - lo) / (hi - lo + 1e-9), 0, 1)
    k = int(win * rate); loc = np.empty_like(v)
    for i in range(len(v)):
        w = v[max(0, i - k):i + k]; a, b = np.percentile(w, 5), np.percentile(w, 95)
        loc[i] = np.clip((v[i] - a) / max(b - a, 3.0), 0, 1)              # >= 3 dB span so near-silence stays dark
    return 0.5 * g + 0.5 * loc

def main(wav, out):
    x = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", f"{DATA}/{wav}", "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True).stdout, np.float32)
    nfr = (len(x) - N) // HOP; rate = SR / HOP
    fr = np.lib.stride_tricks.as_strided(x, shape=(nfr, N), strides=(x.strides[0] * HOP, x.strides[0]))
    P = np.abs(np.fft.rfft(fr * np.hanning(N).astype(np.float32), axis=1)) ** 2
    f = np.fft.rfftfreq(N, 1 / SR)
    mel_db = 10 * np.log10(P[:, (f >= 500) & (f <= 4000)].sum(1) + 1e-10)
    mel = env(mel_db, 0.12, 0.9, rate)
    tot = P[:, f > 40].sum(1) + 1e-12
    reg = lp((P[:, f > 1000].sum(1) - P[:, (f > 40) & (f < 250)].sum(1)) / tot, 1 / (2 * np.pi * 0.8), rate)
    b = 0.75 * gl_norm(mel, rate) + 0.25 * gl_norm(reg * 20, rate)
    b = lp(b, 1.5, rate)
    t = (np.arange(nfr) * HOP + N / 2) / SR
    tt = np.arange(0, t[-1], 1 / FPS)
    res = {"fps": FPS, "b": [round(float(v), 4) for v in np.interp(tt, t, b)],
           "mel": [round(float(v), 2) for v in np.interp(tt, t, mel)], "reg": [round(float(v), 4) for v in np.interp(tt, t, reg)]}
    json.dump(res, open(out, "w"))
    print(len(tt), "frames; b percentiles", np.percentile(b, [5, 25, 50, 75, 95]).round(2))

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
