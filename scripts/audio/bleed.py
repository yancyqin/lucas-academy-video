"""Measure how much of one stem leaked into another.

Demucs stems are sample-aligned copies of the same mix, so a zero-lag
normalized correlation between a vocal stem and the "other" stem is a direct
read on bleed: 0 means the pad is gone, higher means a copy of it is still
riding under the voice.

  bleed.py <candidate.wav> <contaminant.wav> [start_s] [end_s]
"""
import sys
import numpy as np
import soundfile as sf


def mono(path, start, end):
    info = sf.info(path)
    a, sr = sf.read(path, start=int(start * info.samplerate),
                    stop=int(end * info.samplerate), dtype='float32')
    return (a.mean(axis=1) if a.ndim > 1 else a), sr


cand, cont = sys.argv[1], sys.argv[2]
start = float(sys.argv[3]) if len(sys.argv) > 3 else 0.0
end = float(sys.argv[4]) if len(sys.argv) > 4 else 30.0

x, sr = mono(cand, start, end)
y, _ = mono(cont, start, end)
n = min(len(x), len(y))
x, y = x[:n], y[:n]

corr = float(np.dot(x, y) / (np.linalg.norm(x) * np.linalg.norm(y) + 1e-12))
# Least-squares gain: how much of y is sitting in x, in dB.
g = float(np.dot(x, y) / (np.dot(y, y) + 1e-12))
db = 20 * np.log10(abs(g) + 1e-12)
rms = 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-12)

print(f'{cand.split("/")[-2][:14]:<14} {cand.split("/")[-1]:<16} '
      f'corr={corr:+.4f}  leak_gain={db:+6.1f} dB  rms={rms:6.1f} dBFS')
