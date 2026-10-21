"""faune_onsets.py — every note entry in a stretch of the faune recording, for strokes that follow the music.

Spectral flux (log magnitude, 150 Hz–6 kHz) with an adaptive threshold; for each onset: loudness (RMS dB in the
first 0.3 s), length (to the next onset, or until the level falls 12 dB), and the dominant pitch (Hz) so a stroke
can follow the melody's direction. No tempo or beat tracking: the piece is rubato.

    python faune_onsets.py WAV OUT.json [--from 0 --to 60]
"""
import argparse, json
import numpy as np
from scipy.io import wavfile
from scipy.signal import stft, medfilt, find_peaks

ap = argparse.ArgumentParser(); ap.add_argument("wav"); ap.add_argument("out")
ap.add_argument("--from", dest="t0", type=float, default=0); ap.add_argument("--to", dest="t1", type=float, default=60)
ap.add_argument("--thr", type=float, default=0.06, help="how far above the running median a peak must rise")
ap.add_argument("--gap", type=float, default=0.12, help="minimum seconds between onsets"); ap.add_argument("--quiet", action="store_true")
a = ap.parse_args()
sr, x = wavfile.read(a.wav)
x = x.astype(np.float32); x = x.mean(1) if x.ndim > 1 else x; x /= (np.abs(x).max() + 1e-9)
x = x[int(a.t0 * sr):int(a.t1 * sr)]
hop = 256
f, t, Z = stft(x, sr, nperseg=2048, noverlap=2048 - hop)
M = np.abs(Z); band = (f > 150) & (f < 6000)
L = np.log1p(1000 * M[band])
flux = np.maximum(0, np.diff(L, axis=1)).sum(0); flux = np.concatenate([[0], flux])
flux /= np.percentile(flux, 99) + 1e-9
thr = medfilt(flux, 41) + a.thr
peaks, _ = find_peaks(flux, height=thr, distance=int(a.gap * sr / hop))
rms = np.sqrt(np.convolve(x * x, np.ones(int(0.05 * sr)) / int(0.05 * sr), mode="same") + 1e-12)
db = 20 * np.log10(rms + 1e-9)
fp = (f > 250) & (f < 2500)
out = []
for k, p in enumerate(peaks):
    ts = t[p]; s0 = int(ts * sr)
    loud = float(db[s0:s0 + int(0.3 * sr)].max()) if s0 < len(db) else -90
    nxt = t[peaks[k + 1]] if k + 1 < len(peaks) else (len(x) / sr)
    seg = db[s0:int(nxt * sr)]
    below = np.nonzero(seg < loud - 12)[0]
    length = min(nxt - ts, (below[0] / sr) if len(below) else nxt - ts)
    p1 = min(M.shape[1], p + max(2, int(min(length, 0.4) * sr / hop)))
    spec = M[fp, p:p1].mean(1) if p1 > p else M[fp, p]
    pitch = float(f[fp][int(np.argmax(spec))])
    out.append(dict(t=round(float(ts + a.t0), 3), db=round(loud, 1), len=round(float(length), 3),
                    gap=round(float(nxt - ts), 3), hz=round(pitch, 1), flux=round(float(flux[p]), 3)))
json.dump(dict(range=[a.t0, a.t1], onsets=out), open(a.out, "w"), indent=0)
print(len(out), "onsets")
for o in ([] if a.quiet else out): print(f"{o['t']:7.2f}  {o['db']:6.1f} dB  len {o['len']:5.2f}  gap {o['gap']:5.2f}  {o['hz']:7.1f} Hz  flux {o['flux']:.2f}")
