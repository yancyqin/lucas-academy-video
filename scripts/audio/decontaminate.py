"""Subtract another stem's leakage out of a stem.

Demucs stems stay sample-aligned with each other, so leakage is a scaled copy
of a stem we already have. Per short window we solve for that scale by least
squares and subtract it. The voice is uncorrelated with a guitar or a pad, so
the fit lands on the leak and leaves the voice alone -- and because we subtract
a real signal rather than gating a spectrum, it adds no musical artifacts.

  decontaminate.py <in.wav> <out.wav> <contaminant.wav> [more.wav ...]
                   [--strength=1.0] [--window=8192]

A shorter window tracks the leak more closely and cancels more of it, at the
cost of following the voice too -- watch the correlation against the input.
"""
import sys
import numpy as np
import soundfile as sf

args = [a for a in sys.argv[1:] if not a.startswith('--')]
strength, window = 1.0, 8192
for a in sys.argv[1:]:
    if a.startswith('--strength'):
        strength = float(a.split('=')[1])
    elif a.startswith('--window'):
        window = int(a.split('=')[1])

src, out, contams = args[0], args[1], args[2:]
x, sr = sf.read(src, dtype='float32', always_2d=True)

N = window                    # 8192 = ~0.17 s at 48 kHz: a stable fit
hop = N // 2
win = np.hanning(N + 1)[:N].astype('float32')   # periodic Hann, sums to 1 at N/2 hop

for cpath in contams:
    c, _ = sf.read(cpath, dtype='float32', always_2d=True)
    n = min(len(x), len(c))
    x, c = x[:n], c[:n]
    acc = np.zeros_like(x)
    removed = 0.0
    for start in range(0, n - N, hop):
        sl = slice(start, start + N)
        xw, cw = x[sl] * win[:, None], c[sl] * win[:, None]
        for ch in range(x.shape[1]):
            num = float(np.dot(xw[:, ch], cw[:, ch]))
            den = float(np.dot(cw[:, ch], cw[:, ch]))
            # Only ever subtract, and never more than the contaminant itself:
            # a fit outside [0, 1] is noise in the estimate, not leakage.
            g = 0.0 if den < 1e-9 else min(max(num / den, 0.0), 1.0) * strength
            acc[sl, ch] += xw[:, ch] - g * cw[:, ch]
            removed += g * den
    x = acc
    print(f'  - {cpath.split("/")[-1]:<12} subtracted (energy {removed:.3g})', flush=True)

peak = float(np.max(np.abs(x))) or 1.0
if peak > 0.999:
    x = x * (0.999 / peak)
sf.write(out, x, sr)
print('wrote', out)
