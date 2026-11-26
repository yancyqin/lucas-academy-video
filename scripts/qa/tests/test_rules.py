"""Rules that need no Whisper, so this never skips: which differences count as the same sound, and when one of
Yancy's approvals still holds.

    .venv-align/bin/python scripts/qa/tests/test_rules.py

A stand-in listener returns a fixed transcript, so every case states exactly what was "heard".
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import decisions as D  # noqa: E402
import narration as N  # noqa: E402
import qa  # noqa: E402
import spec as S  # noqa: E402
from common import FAIL, UNSURE, decode_audio, item  # noqa: E402

SR = N.SR
DATA = Path("/Users/yqin/repo/playground/lucas-academy-video-data")


class Heard:
    """Stands in for narration.Listener: both models "hear" this text, its words spread evenly over the clip."""

    def __init__(self, text: str, lang: str):
        self.text, self.lang = text, lang

    def hear(self, audio, lang, prompt="", which="primary"):
        parts = list(self.text.replace(" ", "")) if self.lang == "zh" else [" " + w for w in self.text.split()]
        a, b = 0.25, len(audio) / SR - 0.25
        step = (b - a) / max(1, len(parts))
        return {"text": self.text, "words": [{"w": w, "s": round(a + k * step, 3), "e": round(a + (k + 1) * step, 3)}
                                             for k, w in enumerate(parts)]}

    def save(self):
        pass


def problems(script: str, heard: str, lang: str) -> set[tuple[str, str]]:
    dur = max(2.0, 0.3 * len(script if lang == "zh" else script.split()))
    spec = S.normalise({"film": "rules", "music": False,
                        "lines": [{"id": "L1", "lang": lang, "start": 0.5, "end": 0.5 + dur, "text": script}]})
    t = np.arange(int((dur + 1.0) * SR)) / SR
    played = (0.1 * np.sin(2 * np.pi * 200 * t)).astype(np.float32)        # a steady hum: no pauses, no clicks
    _, items = N.check(spec, played, None, Heard(heard, lang), log=lambda *_: None)
    return {(p["code"], p["verdict"]) for i in items for p in i.get("problems", [i])}


NUMBER = ("narration.number", FAIL)
SOUND_CASES = [
    # (name, language, script, heard, the finding that must be there — None = no finding at all)
    ("eight heard as eighty", "en", "There are eight dogs.", "There are eighty dogs.", NUMBER),
    ("eighty heard as eight", "en", "She is eighty years old.", "She is eight years old.", NUMBER),
    ("sixty heard as sixth", "en", "It took sixty days.", "It took sixth days.", NUMBER),
    ("fifty heard as fifth", "en", "He counted fifty birds.", "He counted fifth birds.", NUMBER),
    ("million heard as billion", "en", "A million stars came out.", "A billion stars came out.", NUMBER),
    ("nineteen heard as ninety", "en", "She was nineteen then.", "She was ninety then.", NUMBER),
    ("fifteen heard as fifty", "en", "It costs fifteen dollars.", "It costs fifty dollars.", NUMBER),
    ("136 heard as 163", "en", "Psalm 136 is a song.", "Psalm 163 is a song.", NUMBER),
    ("十 heard as 四", "zh", "一共有十个人。", "一共有四个人。", NUMBER),
    ("两 heard as 二", "zh", "他买了两本书。", "他买了二本书。", NUMBER),
    # the same sound written another way is not an error
    ("the number said right", "en", "There are eight dogs.", "There are eight dogs.", None),
    ("quays written keys", "en", "The quays were empty.", "The keys were empty.", None),
    ("Christina written Cristina", "en", "Then Christina sang.", "Then Cristina sang.", None),
    ("十 written 时 (same tone)", "zh", "一共有十个人。", "一共有时个人。", None),
    ("136 written out", "en", "Psalm 136 is a song.", "Psalm one hundred and thirty six is a song.", None),
    ("角色 still needs listening", "zh", "记忆扮演了什么角色。", "记忆扮演了什么角色。", ("narration.articulation", UNSURE)),
    ("predict still needs listening", "en", "We predict what comes next.", "We predict what comes next.", ("narration.articulation", UNSURE)),
]


def sound_cases() -> bool:
    ok_all = True
    for name, lang, script, heard, want in SOUND_CASES:
        got = problems(script, heard, lang)
        ok = (want in got) if want else not got
        ok_all &= ok
        print(f"{'PASS' if ok else 'MISS'}  {name:<28} expected {want or 'nothing'} | got {sorted(got) or 'nothing'}")
    return ok_all


# ---------------------------------------------------------------------------------------------------------------
# An approval is about one recording.


def speechlike(seed: int, dur: float = 6.0) -> np.ndarray:
    """A made-up "take": syllables of a buzzing voice with its own rhythm and melody (another seed = another take)."""
    rng = np.random.default_rng(seed)
    x = np.zeros(int(dur * SR), np.float32)
    t = 0.15
    while t < dur - 0.4:
        length = rng.uniform(0.12, 0.3)
        n = int(length * SR)
        tt = np.arange(n) / SR
        f0 = rng.uniform(110, 240) * (1 + rng.uniform(-0.15, 0.15) * tt / length)
        formants = rng.uniform(300, 2600, 3)
        phase = 2 * np.pi * np.cumsum(f0) / SR
        syl = sum(np.sin(h * phase) * sum(np.exp(-((h * f0 - f) / 220) ** 2) for f in formants) for h in range(1, 16))
        a = int(t * SR)
        x[a:a + n] += (syl * np.hanning(n) * rng.uniform(0.4, 1.0)).astype(np.float32)[: len(x) - a]
        t += length + rng.uniform(0.02, 0.18)
    return 0.2 * x / np.abs(x).max()


def rerendered(x: np.ndarray, delay_ms: float, gain_db: float = 0.0) -> np.ndarray:
    """The same recording after another render: moved on the timeline, level changed, encoded to AAC again."""
    with tempfile.TemporaryDirectory() as td:
        wav, m4a = Path(td) / "a.wav", Path(td) / "b.m4a"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", str(wav)],
                       input=x.astype(np.float32).tobytes(), check=True)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(wav), "-af",
                        f"aresample=48000,adelay={delay_ms}:all=1,volume={gain_db}dB", "-c:a", "aac", "-b:a", "128k",
                        "-ac", "2", str(m4a)], check=True)
        return decode_audio(m4a)


def line_item(take: str) -> dict:
    return item("narration", UNSURE, "narration.line", "L1：名字听得不一样", key="k-line", line="L1", take=take)


def take_cases() -> bool:
    a, b = speechlike(1), speechlike(2)
    pa, pb = N.take_print(a), N.take_print(b)
    moved = N.take_print(rerendered(a, 1000 / 30 * 1.37, -2.0))
    rows = [("the recording against itself", D.similarity(pa, pa), True),
            ("moved 46 ms, 2 dB down, AAC again", D.similarity(pa, moved), True),
            ("another take of the same length", D.similarity(pa, pb), False),
            ("no print saved with the decision", D.similarity(pa, None), False)]
    # Real voices, when the data folder is on this machine.
    for orig in sorted((DATA / "journey/narration/takes/retakes").glob("*.orig.wav")):
        for cand in sorted(orig.parent.glob(orig.name.replace(".orig.wav", ".cand*.wav"))):
            x, y = decode_audio(orig), decode_audio(cand)
            rows.append((f"real retake {cand.name}", D.similarity(N.take_print(x), N.take_print(y)), False))
            rows.append((f"real take {orig.name} rendered again", D.similarity(N.take_print(x), N.take_print(rerendered(x, 21.0))), True))
    ok_all = True
    for name, s, same in rows:
        ok = (s >= D.SAME_TAKE) == same
        ok_all &= ok
        print(f"{'PASS' if ok else 'MISS'}  {name:<44} similarity {s:.3f} → {'same' if s >= D.SAME_TAKE else 'another'} recording")

    # The gate: an approval holds for the recording it was given on, and for nothing else.
    with tempfile.TemporaryDirectory() as td:
        folder = Path(td)

        def report(take):
            r = {"video": "film.mp4", "sha256": "x", "items": [line_item(take)], "skipped": [], "incomplete": []}
            (folder / "report.json").write_text(json.dumps(r), encoding="utf-8")
            return r

        r = report(pa)
        D.record(folder, "k-line", "pass", note="听过了")
        checks = [("approved line passes the gate", qa.status(r, D.load(folder))["ok"], True),
                  ("same recording after a re-render keeps it", qa.status(report(moved), D.load(folder))["ok"], True),
                  ("another take with the same key is asked again", qa.status(report(pb), D.load(folder))["ok"], False)]
        dropped = D.prune(folder, report(pb))
        checks.append(("a new check drops the outdated approval", bool(dropped) and not D.load(folder), True))
        # A page left open from the earlier check plays the old clips: it must not approve the new recording.
        old_page, r = D.report_id(dict(report(pa), created="yesterday")), report(pb)
        try:
            D.record(folder, "k-line", "pass", seen=old_page)
            refused = False
        except KeyError:
            refused = True
        checks.append(("a page from an earlier check cannot approve", refused and not qa.status(r, D.load(folder))["ok"], True))
        D.record(folder, "k-line", "pass", seen=D.report_id(r))
        checks.append(("the current page can", qa.status(r, D.load(folder))["ok"], True))
    for name, got, want in checks:
        ok = got == want
        ok_all &= ok
        print(f"{'PASS' if ok else 'MISS'}  {name}")
    return ok_all


def key_cases() -> bool:
    """The approval key: steady when Whisper writes the same recording another way or the line moves; new when the
    text or the kind of doubt changes; never shared by two lines with the same words."""
    def keys(lines, heard):
        spec = S.normalise({"film": "rules", "music": False, "names": ["Meng Haoran"], "lines": lines})
        end = max(l["end"] for l in spec["lines"]) + 1.0
        t = np.arange(int(end * SR)) / SR
        played = (0.1 * np.sin(2 * np.pi * 200 * t)).astype(np.float32)
        _, items = N.check(spec, played, None, Heard(heard, "en"), log=lambda *_: None)
        return [i["key"] for i in items if i["code"] == "narration.line" and i["verdict"] == UNSURE]

    script = "Then Meng Haoran wrote a short poem."
    one = lambda a, text=script: {"lang": "en", "start": a, "end": a + 3.0, "text": text}  # noqa: E731
    k1 = keys([one(0.5)], "Then Men Hallan wrote a short poem.")
    k2 = keys([one(0.5)], "Then Man Halloran wrote a short poem.")         # the same doubt, written another way
    k3 = keys([one(2.5)], "Then Men Hallan wrote a short poem.")           # the line moved
    k4 = keys([one(0.5, "Then Meng Haoran wrote one short poem.")], "Then Men Hallan wrote one short poem.")
    k5 = keys([one(0.5), one(5.0)], "Then Men Hallan wrote a short poem.")
    checks = [("an 拿不准 line gets one key", len(k1) == 1),
              ("Whisper spelling it another way keeps the key", k1 == k2),
              ("moving the line keeps the key", k1 == k3),
              ("changing the text changes the key", k1 != k4),
              ("two lines with the same words get two keys", len(k5) == 2 and len(set(k5)) == 2 and k5[0] == k1[0])]
    for name, ok in checks:
        print(f"{'PASS' if ok else 'MISS'}  {name}")
    return all(ok for _, ok in checks)


def main() -> int:
    ok = sound_cases()
    ok &= take_cases()
    ok &= key_cases()
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
