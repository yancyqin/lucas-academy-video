"""Even out the pitch of one film: no line far above or below the rest.

CosyVoice picks each take's pitch afresh, so one line can come out several
semitones above its neighbours. In the zh film 「第三个理念」 sat about 6 semitones
above the other four section openers, and a listener heard the voice go up and
down (「忽高忽低」). This measures each line's median pitch (pyin over voiced
frames) against the film median and re-voices a line more than TOL semitones off,
at its paced speed, keeping the take nearest the median among those Whisper still
hears correctly and that keeps the film's pace (pace.py's measure, within pace.TOL).

The picture is rendered from public/whole-person-01/timeline.LANG.json, so a new
take must also fit its line's slot there; then `build_timeline.py --keep-timeline
LANG` rebuilds only the audio.

Run from lucas-academy-media with its env:
  .conda/bin/python ../lucas-academy-video/scripts/whole-person-01/pitch.py zh|en [--measure]
"""
import difflib
import json
import shutil
import statistics
import sys
from pathlib import Path

import librosa
import numpy as np
import soundfile as sf

sys.path.insert(0, "src")
sys.path.insert(0, str(Path(__file__).parent))
import narrate  # noqa: E402  (OUT, SCRIPT, SPOKEN, ZH_SUBSTITUTIONS)
import pace  # noqa: E402  (HOMOPHONES, PACE, PROMPT, SPEED, TOL, norm, rate)

VIDEO = Path(__file__).resolve().parents[2]
TOL = 2.0              # semitones off the film median that make a line stand out
GOAL = 1.0             # stop re-voicing a line once a take is this close
TRIES = 8
EXEMPT = {"wp00-01"}   # the opening question is asked higher on purpose
F0_RANGE = {"yancy/zh": (65, 330), "louise/zh": (110, 420), "louise/en": (110, 420)}  # by voice: pyin search range, Hz
SILENCE, KEEP = 300, 0.05  # build_timeline.py's trim: |int16| above SILENCE, KEEP s kept each side


def trimmed(path: Path) -> tuple[np.ndarray, int]:
    """The take as the film plays it: build_timeline.py trims the room tone."""
    y, sr = sf.read(path, dtype="int16")
    loud = np.nonzero(np.abs(y[::120].astype(np.int32)) > SILENCE)[0] * 120
    keep = round(KEEP * sr)
    return y[max(0, loud[0] - keep):min(len(y), loud[-1] + keep)].astype(np.float32) / 32768, sr


def pitch(path: Path, voice: str) -> float:
    # Measured on the trimmed take: the faint tails CosyVoice leaves read as low "voiced" frames.
    y, sr = trimmed(path)
    f0, voiced, _ = librosa.pyin(y, fmin=F0_RANGE[voice][0], fmax=F0_RANGE[voice][1], sr=sr, frame_length=1024, hop_length=240)
    return float(np.median(f0[voiced & ~np.isnan(f0)]))


def speech_length(path: Path) -> float:
    y, sr = trimmed(path)
    return len(y) / sr


def main(lang: str, measure_only: bool) -> None:
    script = json.load(open(narrate.SCRIPT.format(lang=lang)))
    out = Path(narrate.OUT[lang])
    text = {l["id"]: l["text"] for l in script["lines"]}
    f0 = {i: pitch(out / f"{i}.wav", script["voice"]) for i in text}
    median = statistics.median(f0.values())
    st = lambda hz: 12 * np.log2(hz / median)  # noqa: E731
    off = {i: st(hz) for i, hz in f0.items() if abs(st(hz)) > TOL and i not in EXEMPT}
    spread = max(st(hz) for hz in f0.values()) - min(st(hz) for hz in f0.values())
    pace_median = statistics.median(pace.rate(out / f"{i}.wav", text[i], lang) for i in text)
    print(f"[{lang}] median {median:.0f} Hz, lines span {spread:.1f} st, {len(off)} lines beyond ±{TOL} st", flush=True)
    for i, s in sorted(off.items(), key=lambda kv: -abs(kv[1])):
        print(f"   {i} {s:+.1f} st  {text[i][:24]}", flush=True)
    if measure_only or not off:
        return

    import whisper
    from lucas_media.cosyvoice_engine import CosyVoiceEngine
    from lucas_media.joke import DEFAULT_PEAK_DBFS, add_peak_headroom, save_wav

    timeline = json.loads((VIDEO / f"public/whole-person-01/timeline.{lang}.json").read_text())
    cues = {c["id"]: c for c in timeline["cues"]}
    speeds = json.loads(pace.PACE.read_text()).get(lang, {}) if pace.PACE.exists() else {}
    engine = CosyVoiceEngine(script["voice"])
    model = whisper.load_model("small", device="cpu")
    kwargs = {"mode": script["mode"], "instruction": script["instruction"]} if "mode" in script else {}

    for i, before in off.items():
        spoken = narrate.SPOKEN[lang].get(i, text[i])
        if lang == "zh":
            for a, b in narrate.ZH_SUBSTITUTIONS.items():
                spoken = spoken.replace(a, b)
        speed = speeds.get(i, script.get("speed", 1.0))
        room = cues[i]["end"] - cues[i]["speech"]["start"] - 0.1  # end before the next line's slot
        best = None  # (semitones off, path)
        for k in range(TRIES):
            speech, sr, _ = engine.synthesize(spoken, target_language=lang, speed=speed, **kwargs)
            tmp = out / f"{i}.pitch{k}.wav"
            save_wav(tmp, add_peak_headroom(speech, peak_dbfs=DEFAULT_PEAK_DBFS), sr)
            heard = model.transcribe(str(tmp), language=lang, initial_prompt=pace.PROMPT[lang], fp16=False)["text"]
            for a, b in pace.HOMOPHONES[lang].items():
                heard = heard.replace(a, b)
            match = difflib.SequenceMatcher(None, pace.norm(spoken.lower(), lang), pace.norm(heard.lower(), lang)).ratio()
            length, now = speech_length(tmp), st(pitch(tmp, script["voice"]))
            paced = pace.rate(tmp, text[i], lang) / pace_median
            fits = length <= room and abs(paced - 1) <= pace.TOL
            print(f"   try {k} {i}: {now:+.1f} st, pace {paced:.2f}x, {length:.2f}s (room {room:.2f}s), whisper {match:.2f}", flush=True)
            if match >= 0.9 and fits and (best is None or abs(now) < abs(best[0])):
                if best:
                    best[1].unlink()
                best = (now, tmp)
            else:
                tmp.unlink()
            if best and abs(best[0]) <= GOAL:
                break
            # As in pace.py: steer the next take's speed by what this one measured.
            speed = min(max(speed / paced, pace.SPEED[0]), pace.SPEED[1])
        if best and abs(best[0]) < abs(before):
            shutil.move(best[1], out / f"{i}.wav")
            print(f"kept {i}: {before:+.1f} -> {best[0]:+.1f} st", flush=True)
        else:
            if best:
                best[1].unlink()
            print(f"KEEP-ORIGINAL {i} ({before:+.1f} st)", flush=True)
    print(f"[{lang}] pitch evened", flush=True)


if __name__ == "__main__":
    main(sys.argv[1], "--measure" in sys.argv)
