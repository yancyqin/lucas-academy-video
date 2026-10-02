"""Tighten the Language Bridge narration: clean edges and cap the pauses inside a line.

CosyVoice pauses 0.5–0.85 s around <strong> words and on every "……", and some
lines end in a tiny blip that stops edge trimming. Both languages get the same
treatment so their lines can be matched in length:

  * edges: cut to 60 ms around the speech, ignoring blips shorter than 80 ms;
  * inside: every silence longer than CAP is shortened to CAP (half its start,
    half its end, joined with a 10 ms crossfade) -- speech is never touched.

Run with the lucas-academy-media environment (librosa, soundfile):
    ../lucas-academy-media/.conda/bin/python scripts/reciprocal-doors-tighten.py
"""
from __future__ import annotations

import re
from pathlib import Path

import librosa
import numpy as np
import soundfile as sf

MEDIA = Path(__file__).resolve().parent.parent.parent / "lucas-academy-media" / "outputs"
FOLDERS = {"zh": MEDIA / "fangfang/zh", "en": MEDIA / "louise/en"}
CAP = 0.55  # longest pause kept inside a line, seconds
EDGE = 0.06  # silence kept before the first and after the last sound
BLIP = 0.08  # sounds shorter than this at the edges are noise, not speech...
ISOLATED = 0.3  # ...when this far from the rest of the line
TOP_DB = 35  # silence = 35 dB below the line's loudest frame
XFADE = 0.01


def tighten(y: np.ndarray, sr: int) -> np.ndarray:
    intervals = librosa.effects.split(y, top_db=TOP_DB, frame_length=1024, hop_length=240)
    if len(intervals) == 0:
        return y
    keep = [iv for iv in intervals]
    # Drop tiny blips at either edge (a click after the last word, a breath
    # tick) -- but only isolated ones: a final consonant release sits close to
    # its word and must stay.
    isolated = lambda gap: gap / sr > ISOLATED
    while len(keep) > 1 and (keep[0][1] - keep[0][0]) / sr < BLIP and isolated(keep[1][0] - keep[0][1]):
        keep.pop(0)
    while len(keep) > 1 and (keep[-1][1] - keep[-1][0]) / sr < BLIP and isolated(keep[-1][0] - keep[-2][1]):
        keep.pop()
    edge = int(EDGE * sr)
    start = max(0, keep[0][0] - edge)
    end = min(len(y), keep[-1][1] + edge)
    cap, fade = int(CAP * sr), int(XFADE * sr)
    out = [y[start:keep[0][1]]]
    for (a0, a1), (b0, b1) in zip(keep, keep[1:]):
        gap = y[a1:b0]
        if len(gap) > cap:
            head, tail = gap[: cap // 2 + fade], gap[len(gap) - cap // 2 - fade:]
            ramp = np.linspace(1.0, 0.0, 2 * fade, dtype=y.dtype)
            joint = head[-2 * fade:] * ramp + tail[: 2 * fade] * ramp[::-1]
            gap = np.concatenate([head[:-2 * fade], joint, tail[2 * fade:]])
        out.append(gap)
        out.append(y[b0:b1])
    out.append(y[keep[-1][1]:end])
    return np.concatenate(out)


def main() -> None:
    for track, folder in FOLDERS.items():
        source, target = folder / "reciprocal-doors", folder / "reciprocal-doors-tight"
        target.mkdir(exist_ok=True)
        before = after = 0.0
        for wav in sorted(source.glob("rd*.wav")):
            if not re.fullmatch(r"rd\d\d-\d\d(-p\d)?\.wav", wav.name):
                continue  # trial takes (.try*, .fit*) are not narration
            y, sr = sf.read(wav, dtype="float32")
            t = tighten(y, sr)
            sf.write(target / wav.name, t, sr, subtype="PCM_16")
            before += len(y) / sr
            after += len(t) / sr
        # A tightened copy whose take was deleted (to be re-voiced) is stale: drop it,
        # so the timeline sees the line as missing instead of playing the old take.
        for stale in target.glob("rd*.wav"):
            if not (source / stale.name).exists():
                stale.unlink()
        print(f"{track}: {before:.1f}s -> {after:.1f}s in {target}")


if __name__ == "__main__":
    main()
