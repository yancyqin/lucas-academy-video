"""Trim and level each raw voice take into the episode (run with lucas-academy-media's Python: numpy, soundfile).

Fangfang's takes open on about a second of room tone and CosyVoice leaves faint tails; both are cut to the speech,
with a short margin and a 10 ms fade. Every line is then set to one loudness (LINE_LUFS) with a fixed gain, so the
mix never rides levels (a one-pass loudnorm is dynamic).

  ../lucas-academy-media/.conda/bin/python scripts/weekly/takes.py 001 [zh|en]
writes public/weekly/<ep>/narration/<lang>/<id>.wav; build_timeline.py then uses the real lengths.
"""
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parents[2]
MEDIA = next(p / "lucas-academy-media" for p in ROOT.parents if (p / "lucas-academy-media").is_dir())
VOICE = {"zh": "fangfang/zh", "en": "louise/en"}
LINE_LUFS = -20.0
PEAK = 10 ** (-1.5 / 20)
HEAD, TAIL = 0.06, 0.14  # seconds kept before the first and after the last voiced frame


def loudness(signal: np.ndarray, sr: int) -> float:
    with tempfile.NamedTemporaryFile(suffix=".wav") as tmp:
        sf.write(tmp.name, signal, sr)
        out = subprocess.run(["ffmpeg", "-nostats", "-i", tmp.name, "-af", "ebur128=framelog=quiet", "-f", "null", "-"],
                             capture_output=True, text=True).stderr
    return float(re.findall(r"I:\s+(-?[\d.]+) LUFS", out)[-1])


def trim(signal: np.ndarray, sr: int) -> np.ndarray:
    hop = int(sr * 0.01)
    frames = len(signal) // hop
    rms = np.sqrt(np.mean(signal[: frames * hop].reshape(frames, hop) ** 2, axis=1) + 1e-12)
    db = 20 * np.log10(rms)
    # Speech is anything within 35 dB of the take's loudest 10 ms, and above -50 dBFS (room tone sits near -48).
    voiced = np.where(db > max(-50.0, db.max() - 35.0))[0]
    a = max(0, voiced[0] * hop - int(HEAD * sr))
    b = min(len(signal), (voiced[-1] + 1) * hop + int(TAIL * sr))
    out = signal[a:b].copy()
    fade = int(0.01 * sr)
    out[:fade] *= np.linspace(0, 1, fade)
    out[-fade:] *= np.linspace(1, 0, fade)
    return out


def main(ep: str, langs: list[str]) -> None:
    for lang in langs:
        src = MEDIA / f"outputs/{VOICE[lang]}/weekly-{ep}-v1"
        dst = ROOT / "public/weekly" / ep / "narration" / lang
        dst.mkdir(parents=True, exist_ok=True)
        done = 0
        for raw in sorted(src.glob("*.wav")):
            target = dst / raw.name
            if target.exists() and target.stat().st_mtime >= raw.stat().st_mtime:
                continue
            signal, sr = sf.read(raw, dtype="float32", always_2d=False)
            if signal.ndim > 1:
                signal = signal.mean(axis=1)
            cut = trim(signal, sr)
            gain = 10 ** ((LINE_LUFS - loudness(cut, sr)) / 20)
            cut = cut * gain
            if np.abs(cut).max() > PEAK:
                cut *= PEAK / np.abs(cut).max()
            sf.write(target, cut, sr, subtype="PCM_16")
            done += 1
        print(f"{lang}: {done} takes trimmed and levelled -> {dst.relative_to(ROOT)}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2:] or ["zh", "en"])
