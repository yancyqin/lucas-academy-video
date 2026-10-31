"""Join the film's takes into one listening preview, with the pauses from voice-direction.md.

  ../lucas-academy-media/.conda/bin/python scripts/ai-sycophancy/preview.py sc00 sc01 [...]   (section prefixes)
Each take is trimmed to its speech the way 「跨越中等收入陷阱」's timeline does it: the span above −40 dBFS, minus the
stray vocoder blips CosyVoice sometimes leaves at either end (Yancy heard them as 哔哔), with short fades. Lines are
0.45 s apart unless the direction gives a 停顿; after a question there is at least QUESTION_GAP, a breath to think.
Writes out/ai-sycophancy/narration/<first>-<last>.{wav,mp3}; no music, no picture.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parents[2]
MEDIA = next(p / "lucas-academy-media" for p in ROOT.parents if (p / "lucas-academy-media").is_dir())
TAKES = MEDIA / "outputs/yancy/zh/ai-sycophancy-v1"
PUNCT = re.compile(r"[，。、；：？！…“”‘’「」『』《》（）—\-·+,.;:?!\"'()\s%]")
GAP, QUESTION_GAP = 0.45, 1.2


def speech_bounds(y: np.ndarray, rate: int) -> tuple:
    """The span above -40 dBFS, minus a burst of at most 30 ms that is 80 ms or more away from the speech."""
    hop = int(0.005 * rate)
    env = np.sqrt(np.add.reduceat(y ** 2, np.arange(0, len(y), hop)) / hop)
    on = np.flatnonzero(20 * np.log10(env + 1e-9) > -40)
    if not len(on):
        return 0, len(y)
    runs = np.split(on, np.flatnonzero(np.diff(on) > 1) + 1)
    while len(runs) > 1 and len(runs[0]) <= 6 and runs[1][0] - runs[0][-1] >= 16:
        runs.pop(0)
    while len(runs) > 1 and len(runs[-1]) <= 6 and runs[-1][0] - runs[-2][-1] >= 16:
        runs.pop()
    return runs[0][0] * hop, (runs[-1][-1] + 1) * hop


def trim(y: np.ndarray, rate: int) -> np.ndarray:
    a, b = speech_bounds(y, rate)
    y = y[max(a - int(0.02 * rate), 0):b + int(0.05 * rate)].copy()
    n_in, n_out = int(0.01 * rate), int(0.03 * rate)
    y[:n_in] *= np.linspace(0, 1, n_in)
    y[-n_out:] *= np.linspace(1, 0, n_out)
    return y


sections = sys.argv[1:]
lines = [l for l in json.loads((TAKES / "lines.json").read_text()) if any(l["id"].startswith(s) for s in sections)]
parts, rate, speech, chars, after_question = [], None, 0.0, 0, False
for n, l in enumerate(lines):
    y, rate = sf.read(TAKES / f"s{l['speed']:.2f}/{l['id']}.wav", dtype="float32")
    y = trim(y, rate)
    gap = l["pause"] if l["pause"] is not None else GAP
    if after_question:
        gap = max(gap, QUESTION_GAP)
    if n:
        parts.append(np.zeros(int(rate * gap), np.float32))
    parts.append(y)
    after_question = l["question"]
    speech += len(y) / rate
    chars += len(PUNCT.sub("", re.sub(r"</?strong>", "", l["spoken"])))
audio = np.concatenate(parts)
dest = ROOT / f"out/ai-sycophancy/narration/{sections[0]}-{sections[-1]}"
dest.parent.mkdir(parents=True, exist_ok=True)
sf.write(f"{dest}.wav", audio, rate)
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", f"{dest}.wav", "-b:a", "160k", f"{dest}.mp3"], check=True)
print(f"{dest}.mp3  {len(lines)} lines, {len(audio) / rate / 60:.1f} min, speech {chars / speech:.2f} 字/s")
