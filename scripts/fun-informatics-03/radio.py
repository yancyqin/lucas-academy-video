"""The two walkie-talkie listening tests of NS01 (FUN-INFORMATICS-03.md §5.4).

    ../lucas-academy-media/.conda/bin/python scripts/fun-informatics-03/radio.py [zh|en]

Test 1 must leave the viewer unsure (一 or 七? / B or D?); test 2 must come through at once (拐 / Bravo).
Both words are cut from Louise's own takes, so the radio voice is the narrator's:

  zh  test 1: 七 from ns01-04 「你慢慢念：一，七。」   test 2: 拐 from ns01-07 「拐！一下就听出来了。」
  en  test 1: B from ns01-04 "Say them slowly: B, D, …"   test 2: Bravo from ns01-07 "Bravo! Easy."

Whisper's word times (out/fun-informatics-03/narration-check*.json, from check.py) find the word; the
take's own pauses set the exact edges. Then both go through the same radio: a 300–3000 Hz band, a little
overdrive, steady static, a squelch click at each end. Test 1 also has its first sound buried in a burst
of static, which leaves only the shared vowel (ī / ee) to hear. The burial is BURY_MS: the owner listened to
60, 90, 120 and 150 ms and kept 120 ms, where 一 and 七 (B, E and D) come out nearly equally likely.

  public/fun-informatics-03/audio/radio-{lang}-test1-{ms}ms.wav, radio-{lang}-test2.wav, and the clean cuts
"""
import json
import sys
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfilt

ROOT = Path(__file__).resolve().parents[2]
for parent in ROOT.parents:
    if (parent / "lucas-academy-media").is_dir():
        MEDIA = parent / "lucas-academy-media"
        break
else:
    raise SystemExit("Cannot find lucas-academy-media")
OUT = ROOT / "public/fun-informatics-03/audio"
RATE = 24000

SOURCES = {
    "zh": {"test1": ("ns01-04", "七"), "test2": ("ns01-07", "拐")},
    "en": {"test1": ("ns01-04", "B"), "test2": ("ns01-07", "Bravo")},
}
BURY_MS = (120,)  # the owner approved 120 ms (2026-10-15); 60, 90 and 150 ms were tried


def word_span(lang, cid, target, nth=0):
    """Whisper's start and end of the nth word that contains `target` (whole word for English)."""
    report = ROOT / f"out/fun-informatics-03/narration-check{'.en' if lang == 'en' else ''}.json"
    cue = json.loads(report.read_text())["cues"][cid]
    analysis = cue["analyses"].get("medium") or cue["analyses"]["small"]
    hits = 0
    for w in analysis["_cut"]["words"]:
        token = w["word"].strip().strip(",.!?:;\"'，。！？：；「」")
        if (lang == "zh" and target in token) or (lang == "en" and token.lower() == target.lower()):
            hits += 1
            if hits <= nth:
                continue
            if lang == "zh" and len(token) > 1:
                # Whisper can time several characters as one token: take this character's share.
                i, n = token.index(target), len(token)
                d = (w["end"] - w["start"]) / n
                return w["start"] + i * d, w["start"] + (i + 1) * d
            return w["start"], w["end"]
    raise SystemExit(f"{lang} {cid}: no word {target!r} in {analysis['heard']!r}")


def voiced(x, rate, floor_db=-35, bridge=0.08):
    """Stretches of speech: 10 ms frames within floor_db of the take's loudest frame, gaps under `bridge` s joined."""
    hop = int(0.01 * rate)
    frames = x[: len(x) // hop * hop].reshape(-1, hop)
    db = 20 * np.log10(np.sqrt((frames ** 2).mean(axis=1)) + 1e-9)
    loud = db > db.max() + floor_db
    spans, s0 = [], None
    for i, on in enumerate(np.append(loud, False)):
        if on and s0 is None:
            s0 = i
        elif not on and s0 is not None:
            if spans and (s0 - spans[-1][1]) * 0.01 < bridge:
                spans[-1][1] = i
            else:
                spans.append([s0, i])
            s0 = None
    return [(a * 0.01, b * 0.01) for a, b in spans]


def cut(lang, cid, target, nth=0):
    """The word as the take's own pauses bound it: the stretch of speech that Whisper's word time falls in.

    Whisper's word times are rough (it gave B a zero-length span), so they only pick which stretch; the
    stretch itself comes from the audio.
    """
    x, rate = sf.read(MEDIA / f"outputs/louise/{lang}/fun-informatics-03-v1/{cid}.wav", dtype="float64")
    assert rate == RATE, rate
    start, end = word_span(lang, cid, target, nth)
    spans = voiced(x, rate)
    overlap = [(min(b, end + 0.1) - max(a, start - 0.1), (a, b)) for a, b in spans]
    best = max(overlap)
    a, b = best[1] if best[0] > 0 else min(spans, key=lambda s: abs((s[0] + s[1]) / 2 - (start + end) / 2))
    a, b = int(max(0, a - 0.02) * rate), int(min(len(x) / rate, b + 0.03) * rate)
    word = x[a:b].copy()
    fade = int(0.006 * rate)
    word[:fade] *= np.linspace(0, 1, fade)
    word[-fade:] *= np.linspace(1, 0, fade)
    print(f"{lang} {cid} {target}: {a / rate:.2f}–{b / rate:.2f} s ({(b - a) / rate:.2f} s); stretches near it:",
          [(round(p, 2), round(q, 2)) for p, q in spans if p < end + 1 and q > start - 1])
    return word / (np.sqrt(np.mean(word ** 2)) + 1e-9) * 10 ** (-20 / 20)


def band(x, lo, hi, order=4):
    return sosfilt(butter(order, [lo, hi], btype="band", fs=RATE, output="sos"), x)


def static(n, rng):
    """Radio hiss: band-limited noise with a slow wobble and a few crackles."""
    hiss = band(rng.standard_normal(n), 400, 5000)
    wobble = 1 + 0.35 * np.sin(2 * np.pi * rng.uniform(3, 6) * np.arange(n) / RATE)
    crackle = np.zeros(n)
    for i in rng.integers(0, n, size=max(1, n // 1200)):
        crackle[i] = rng.uniform(-1, 1) * 6
    return (hiss * wobble + band(crackle, 800, 6000)) / 3


def radio(word, bury_ms, rng):
    lead, tail = int(0.45 * RATE), int(0.35 * RATE)
    voice = np.concatenate([np.zeros(lead), word, np.zeros(tail)])
    voice = np.tanh(2.2 * band(voice, 300, 3000)) / np.tanh(2.2)
    noise = static(len(voice), rng) * 10 ** (-27 / 20)
    if bury_ms:
        # Bury the word's first sound under a loud burst, so only the vowel that follows is clear.
        n = int(bury_ms / 1000 * RATE)
        ramp = np.ones(n)
        ramp[-int(0.015 * RATE):] = np.linspace(1, 0, int(0.015 * RATE))
        voice[lead:lead + n] *= 1 - ramp * 0.97
        noise[lead - int(0.02 * RATE):lead + n] += static(n + int(0.02 * RATE), rng) * 10 ** (-12 / 20)
    out = voice * 10 ** (-3 / 20) + noise
    for at in (int(0.12 * RATE), len(out) - int(0.12 * RATE)):  # squelch clicks: push-to-talk on and off
        k = int(0.03 * RATE)
        out[at:at + k] += static(k, rng) * 10 ** (-8 / 20) * np.linspace(1, 0, k)
    return out / np.max(np.abs(out)) * 10 ** (-3 / 20)


def main():
    langs = [a for a in sys.argv[1:] if a in SOURCES] or list(SOURCES)
    OUT.mkdir(parents=True, exist_ok=True)
    for lang in langs:
        for test, (cid, target) in SOURCES[lang].items():
            word = cut(lang, cid, target)
            sf.write(OUT / f"word-{lang}-{test}.wav", word, RATE)
            for ms in (BURY_MS if test == "test1" else (0,)):
                rng = np.random.default_rng(3)  # the same static in every file, so the tests differ only in the word
                name = f"radio-{lang}-{test}" + (f"-{ms}ms" if ms else "") + ".wav"
                sf.write(OUT / name, radio(word, ms, rng), RATE)
                print(OUT / name)


if __name__ == "__main__":
    main()
