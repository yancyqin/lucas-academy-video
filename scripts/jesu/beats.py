"""Beat grid of a recording of the piece.

  beats.py MUSIC [--bpm 69]     print tempo, beat and bar (3/4) times

Jesu, Joy of Man's Desiring is in 3/4 with flowing triplets. On the Gli Armonici
recording the beat is ~0.88 s (≈69 bpm) and the bar ~2.6 s; an onset autocorrelation
shows the triplet (0.30 s), beat (0.87 s) and bar (2.61 s) clearly. The tracker is
seeded near the beat so it doesn't lock onto the triplets.
"""
import argparse

import librosa
import numpy as np

SR = 22050
HOP = 512


def analyze(path, bpm=69.0):
    """-> dict(tempo, beats [s]) for the recording at `path`."""
    y, _ = librosa.load(str(path), sr=SR, mono=True)
    oenv = librosa.onset.onset_strength(y=y, sr=SR, hop_length=HOP)
    tempo, frames = librosa.beat.beat_track(onset_envelope=oenv, sr=SR, hop_length=HOP,
                                            start_bpm=bpm, tightness=300)
    beats = librosa.frames_to_time(frames, sr=SR, hop_length=HOP)
    return {"tempo": float(np.atleast_1d(tempo)[0]), "beats": beats.round(3).tolist(),
            "duration": round(len(y) / SR, 3)}


def snap(t, beats):
    beats = np.asarray(beats)
    return float(beats[np.argmin(np.abs(beats - t))])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("music")
    ap.add_argument("--bpm", type=float, default=69.0)
    a = ap.parse_args()
    r = analyze(a.music, a.bpm)
    b = np.asarray(r["beats"])
    print(f"tempo {r['tempo']:.1f} bpm, {len(b)} beats, median beat {np.median(np.diff(b)):.3f} s, "
          f"bar ≈ {3 * np.median(np.diff(b)):.2f} s, length {r['duration']:.1f} s")
    print(" ".join(f"{t:.2f}" for t in b))


if __name__ == "__main__":
    main()
