"""Even out the speaking pace of one film: every line near the film's median rate.

One reading style is not enough: CosyVoice picks each line's tempo, so some lines
run fast and others slow ("忽快忽慢"). This measures each line's rate as
syllables per second of *sound* (pauses and the trimmed edges excluded; an
English word counts its vowel groups) and re-voices a line more than TOL off
the median at speed = current / ratio (within SPEED), keeping the take closest
to the median among those Whisper hears correctly. Chosen speeds are stored in
outputs/whole-person-five-ideas.pace.json (lucas-academy-media, ignored) so the
next run starts from them.

Run from lucas-academy-media with its env:
  .conda/bin/python ../lucas-academy-video/scripts/whole-person-01/pace.py zh|en [--measure]
"""
import difflib
import json
import re
import shutil
import statistics
import sys
from pathlib import Path

import librosa
import soundfile as sf

sys.path.insert(0, "src")
sys.path.insert(0, str(Path(__file__).parent))
import narrate  # noqa: E402  (OUT, SCRIPT, SPOKEN, ZH_SUBSTITUTIONS)

PACE = Path("outputs/whole-person-five-ideas.pace.json")  # beside the takes in lucas-academy-media (ignored)
TOL = 0.10
SPEED = (0.8, 1.25)
TRIES = 3
# Lines read deliberately on purpose: the opening question is asked slowly and then held.
EXEMPT = {"wp00-01"}
PROMPT = {"zh": "以下是普通话的句子，使用简体中文。", "en": None}


def english_syllables(word: str) -> int:
    groups = re.findall(r"[aeiouy]+", word.lower())
    n = len(groups) - (1 if word.lower().endswith("e") and len(groups) > 1 else 0)
    return max(1, n)


def syllables(text: str, lang: str) -> int:
    words = re.findall(r"[A-Za-z]+(?:'[a-z]+)?", text)
    latin = sum(english_syllables(w) for w in words)
    return latin + (len(re.findall(r"[一-鿿]", text)) if lang == "zh" else 0)


def rate(path: Path, text: str, lang: str) -> float:
    y, sr = sf.read(path, dtype="float32")
    if y.ndim > 1:
        y = y.mean(axis=1)
    intervals = librosa.effects.split(y, top_db=35, frame_length=1024, hop_length=240)
    voiced = sum(b - a for a, b in intervals) / sr
    return syllables(text, lang) / max(voiced, 0.1)


def norm(s: str, lang: str):
    if lang == "zh":
        return list(re.sub(r"[^一-鿿A-Za-z]", "", s))
    return re.sub(r"[^a-z ]", "", s.lower().replace("'", "").replace("’", "")).split()


def main(lang: str, measure_only: bool) -> None:
    script = json.load(open(narrate.SCRIPT.format(lang=lang)))
    out = Path(narrate.OUT[lang])
    lines = script["lines"]
    rates = {l["id"]: rate(out / f"{l['id']}.wav", l["text"], lang) for l in lines}
    median = statistics.median(rates.values())
    off = {i: r / median for i, r in rates.items() if abs(r / median - 1) > TOL and i not in EXEMPT}
    spread = max(abs(r / median - 1) for r in rates.values())
    print(f"[{lang}] median {median:.2f} syl/s, max off {spread:.0%}, {len(off)} lines beyond ±{TOL:.0%}", flush=True)
    for i, ratio in sorted(off.items(), key=lambda kv: kv[1]):
        print(f"   {i} {ratio:.2f}x", flush=True)
    if measure_only or not off:
        return

    import whisper
    from lucas_media.cosyvoice_engine import CosyVoiceEngine
    from lucas_media.joke import DEFAULT_PEAK_DBFS, add_peak_headroom, save_wav

    pace = json.loads(PACE.read_text()) if PACE.exists() else {}
    speeds = pace.setdefault(lang, {})
    base = script.get("speed", 1.0)
    engine = CosyVoiceEngine(script["voice"])
    model = whisper.load_model("small", device="cpu")
    kwargs = {"mode": script["mode"], "instruction": script["instruction"]} if "mode" in script else {}
    text = {l["id"]: l["text"] for l in lines}

    for i, ratio in off.items():
        spoken = narrate.SPOKEN[lang].get(i, text[i])
        if lang == "zh":
            for a, b in narrate.ZH_SUBSTITUTIONS.items():
                spoken = spoken.replace(a, b)
        speed = min(max(speeds.get(i, base) / ratio, SPEED[0]), SPEED[1])
        best = None  # (distance from median, path, speed)
        for k in range(TRIES):
            speech, sr, _ = engine.synthesize(spoken, target_language=lang, speed=speed, **kwargs)
            tmp = out / f"{i}.pace{k}.wav"
            save_wav(tmp, add_peak_headroom(speech, peak_dbfs=DEFAULT_PEAK_DBFS), sr)
            heard = model.transcribe(str(tmp), language=lang, initial_prompt=PROMPT[lang], fp16=False)["text"]
            match = difflib.SequenceMatcher(None, norm(text[i], lang), norm(heard, lang)).ratio()
            new_ratio = rate(tmp, text[i], lang) / median
            print(f"   try {k} {i} speed {speed:.2f}: {new_ratio:.2f}x, whisper {match:.2f}", flush=True)
            if match >= 0.9 and (best is None or abs(new_ratio - 1) < best[0]):
                if best:
                    best[1].unlink()
                best = (abs(new_ratio - 1), tmp, speed)
            else:
                tmp.unlink()
            if best and best[0] <= TOL / 2:
                break
            # CosyVoice's tempo is not linear in `speed`: correct from what this take measured.
            speed = min(max(speed / new_ratio, SPEED[0]), SPEED[1])
        if best and best[0] < abs(ratio - 1):
            shutil.move(best[1], out / f"{i}.wav")
            speeds[i] = round(best[2], 3)
            print(f"kept {i} at speed {best[2]:.2f} ({1 + best[0]:.2f}x off)", flush=True)
        else:
            if best:
                best[1].unlink()
            print(f"KEEP-ORIGINAL {i}", flush=True)
        PACE.write_text(json.dumps(pace, ensure_ascii=False, indent=1) + "\n")
    print(f"[{lang}] paced", flush=True)


if __name__ == "__main__":
    main(sys.argv[1], "--measure" in sys.argv)
