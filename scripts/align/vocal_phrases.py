"""Measure where an isolated vocal is actually singing.

Forced alignment gives a start per line but its end timestamps run on through
instrumental gaps: the last word of a phrase absorbs the silence behind it, so a
line claims 22 seconds when it was sung in three. Display length then comes from a
timestamp nothing measured.

This reads the envelope instead and reports the voiced runs, which is a
measurement the alignment can be clamped against.
"""
import argparse, json, pathlib
import numpy as np, soundfile as sf

ap = argparse.ArgumentParser()
ap.add_argument('--vocal', required=True)
ap.add_argument('--hop', type=float, default=0.02, help='seconds per envelope frame')
ap.add_argument('--floor-percentile', type=float, default=45.0)
ap.add_argument('--open', type=float, default=6.0, help='dB over floor to count as voiced')
ap.add_argument('--min-gap', type=float, default=0.35, help='shorter silences do not split a phrase')
ap.add_argument('--min-phrase', type=float, default=0.18)
ap.add_argument('--out', default=None)
a = ap.parse_args()

x, sr = sf.read(a.vocal, dtype='float32', always_2d=True)
x = x.mean(axis=1)
hop = int(sr * a.hop)
n = len(x) // hop
rms = np.sqrt(np.maximum((x[:n * hop] ** 2).reshape(n, hop).mean(axis=1), 1e-12))
db = 20 * np.log10(rms)

floor = np.percentile(db, a.floor_percentile)
thresh = floor + a.open
voiced = db > thresh
print(f'{a.vocal}')
print(f'  {n} frames @ {a.hop * 1000:.0f}ms   floor {floor:.1f} dB   threshold {thresh:.1f} dB')
print(f'  voiced {voiced.mean() * 100:.1f}% of the track')

# Close short gaps first, then drop specks, so a phrase is not split by a breath.
gap_frames = int(a.min_gap / a.hop)
idx = np.flatnonzero(voiced)
runs = []
if len(idx):
    start = idx[0]; prev = idx[0]
    for i in idx[1:]:
        if i - prev > gap_frames:
            runs.append((start, prev)); start = i
        prev = i
    runs.append((start, prev))
phrases = [(s * a.hop, (e + 1) * a.hop) for s, e in runs
           if (e + 1 - s) * a.hop >= a.min_phrase]
print(f'  {len(phrases)} voiced runs\n')
for i, (s, e) in enumerate(phrases):
    print(f'{i:3} {int(s)//60}:{s%60:06.3f} -> {int(e)//60}:{e%60:06.3f}   {e-s:5.2f}s')
if a.out:
    pathlib.Path(a.out).write_text(json.dumps(
        [{'start': round(s, 3), 'end': round(e, 3)} for s, e in phrases], indent=2) + '\n')
    print(f'\nwrote {a.out}')
