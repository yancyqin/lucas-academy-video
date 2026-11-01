"""Sunny's recordings (her voice samples, iPhone memos Windchime 18 and 19 — owner, 2026-10-28: both are Sunny),
cut into verse clips that replace the AI voice for those verses.

    .venv-align/bin/python scripts/zhong-ying/sunny_voice.py

Each recording (iPhone voice memo, 2026-10-27) reads several verses in Chinese, in the order listed in RECORDINGS.
The known text is force-aligned to the recording (stable-ts), and each verse is cut from just before its first
syllable to just after its last, splitting the pauses between verses. The memos are already clean (the phone gates
the silences to digital zero), so there is no denoising: a 70 Hz high-pass and 15 ms fades, then the STUDIO chain
(the owner's pick, A, among voice_versions.py's auditions); loudness is matched to the other lines when the film is mixed
(build_timeline.py levels every line to the same LUFS).

Writes the plain cuts to DATA/narration/sunny/zh-raw/ and, with the STUDIO chain the owner chose, the clips the
film uses to DATA/narration/sunny/zh/<film>-vNN.wav (48 kHz mono; films.clip() prefers them over the AI takes), and
DATA/narration/sunny/cuts.json (where each verse was cut, for checking).
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from films import DATA, texts  # noqa: E402

SUNNY_DIR = DATA / "narration" / "sunny"
SR = 48000
# recording on the Desktop → the verses it reads, in order
RECORDINGS = {
    "Windchime 18.m4a": [("little-boats", 1), ("little-boats", 2)],
    "Windchime 19.m4a": [("little-boats", 7), ("climb-higher", 1), ("climb-higher", 2), ("climb-higher", 7), ("climb-higher", 8)],
}
PRE, POST = 0.22, 0.35
# The owner's choice (2026-10-27, version A of voice_versions.py): the recorded voice, studio-processed — rumble cut, less
# mud, more presence and air, gentle compression, de-essing, a touch of room.
STUDIO = ("highpass=f=80,equalizer=f=250:t=q:w=1.0:g=-2.5,equalizer=f=3500:t=q:w=1.2:g=2.5,highshelf=f=10000:g=2,"
          "deesser=i=0.4,acompressor=threshold=-24dB:ratio=3:attack=8:release=140:makeup=3,"
          "aecho=0.85:0.5:23|41:0.07|0.05")


def han(text: str) -> str:
    return "".join(re.findall(r"[一-鿿]", text))


def main():
    import numpy as np
    import soundfile as sf
    import stable_whisper

    model = stable_whisper.load_model("medium", device="cpu")
    spoken = {}
    for film in {f for verses in RECORDINGS.values() for f, _ in verses}:
        spoken.update({(film, u["n"]): u["spoken_zh"] for u in texts(film)})
    (SUNNY_DIR / "raw").mkdir(parents=True, exist_ok=True)
    (SUNNY_DIR / "zh").mkdir(parents=True, exist_ok=True)
    (SUNNY_DIR / "zh-raw").mkdir(parents=True, exist_ok=True)
    cuts = {}
    for name, verses in RECORDINGS.items():
        src = Path.home() / "Desktop" / name
        keep = SUNNY_DIR / "raw" / name
        if not keep.exists():
            shutil.copy2(src, keep)                      # the original memo, kept beside the cuts
        wav = SUNNY_DIR / "raw" / (keep.stem.replace(" ", "-").lower() + ".wav")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(keep), "-ac", "1", "-ar", str(SR), str(wav)], check=True)
        audio, _ = sf.read(wav)
        result = model.align(str(wav), "".join(spoken[v] for v in verses), language="zh")
        chars = []
        for w in result.all_words():
            letters = han(w.word)
            step = (w.end - w.start) / max(1, len(letters))
            chars += [(w.start + k * step, w.start + (k + 1) * step) for k in range(len(letters))]
        spans, at = [], 0
        for v in verses:
            n = len(han(spoken[v]))
            spans.append((chars[at][0], chars[at + n - 1][1]))
            at += n
        assert at == len(chars), f"{name}: aligned {len(chars)} syllables, expected {at}"
        # The aligner can start a verse's first word late (it squeezed 「我要向山」 into half a second), so the cuts
        # come from the sound itself: a verse runs from the end of the pause before it to the start of the pause
        # after it (the memo's pauses are digital silence), with PRE / POST kept.
        hop = SR // 100
        env = np.sqrt(np.convolve(audio ** 2, np.ones(hop) / hop, "same")[::hop])
        loud = env > env.max() * 10 ** (-45 / 20)
        edges = []
        for a, b in spans:
            i, j = int(a * 100), min(len(loud) - 1, int(b * 100))
            while i > 0 and loud[max(0, i - 25):i].any():   # back to the last 250 ms pause
                i -= 1
            while j < len(loud) - 1 and loud[j:j + 25].any():
                j += 1
            edges.append((i / 100, j / 100))
        for i, (v, (a, b)) in enumerate(zip(verses, edges)):
            lo = max(0.0, a - PRE) if i == 0 else max(a - PRE, (edges[i - 1][1] + a) / 2)
            hi = min(len(audio) / SR, b + POST) if i == len(edges) - 1 else min(b + POST, (b + edges[i + 1][0]) / 2)
            raw = SUNNY_DIR / "zh-raw" / f"{v[0]}-v{v[1]:02d}.wav"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{lo:.3f}", "-to", f"{hi:.3f}", "-i", str(wav),
                            "-af", f"highpass=f=70,afade=t=in:d=0.015,areverse,afade=t=in:d=0.015,areverse", str(raw)], check=True)
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(raw), "-af", STUDIO, str(SUNNY_DIR / "zh" / raw.name)], check=True)
            cuts[f"{v[0]}-v{v[1]:02d}"] = {"recording": name, "from": round(lo, 3), "to": round(hi, 3),
                                          "sound": [round(a, 3), round(b, 3)], "text": spoken[v]}
            print(f"{name}: {v[0]} v{v[1]:02d} {lo:6.2f}–{hi:6.2f}s (sound {a:.2f}–{b:.2f})  {spoken[v]}")
    (SUNNY_DIR / "cuts.json").write_text(json.dumps(cuts, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
