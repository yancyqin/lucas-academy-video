"""Where the letters lines say each letter, for the letters take's timing (build_timeline.py LETTER_WORDS).

    ../lucas-academy-media/.conda/bin/python scripts/cube-5x5/letter_words.py [--write]

Whisper (small, word timestamps) on the raw English takes of cf02-01 ("R … U … F … a little mark … a 2 after it")
and cf02-02 ("2R … M"). Prints every word with its start, then the moves' times: R, U and F at their letters, R′
at "mark", U2 at the "two" of "a two after it", 2R at the "two" before "R", M at "M". --write saves them to
scripts/cube-5x5/letter_words.json. Check the printed words before trusting a time.
"""
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MEDIA = next(p / "lucas-academy-media" for p in ROOT.parents if (p / "lucas-academy-media").is_dir())
TAKES = MEDIA / "outputs/louise/en/cube-5x5-v1"
OUT = ROOT / "scripts/cube-5x5/letter_words.json"


def words(model, cid):
    result = model.transcribe(str(TAKES / f"{cid}.wav"), language="en", word_timestamps=True,
                              initial_prompt="Cube notation: R, U, F, R prime, U two, two R, M.")
    out = [(re.sub(r"[^\w]", "", w["word"]).lower(), round(w["start"], 2)) for s in result["segments"] for w in s["words"]]
    print(cid, " ".join(f"{w}@{t}" for w, t in out))
    return out


def first(seq, test, after=0.0):
    return next(t for i, (w, t) in enumerate(seq) if t >= after and test(i, w))


def main():
    import whisper
    model = whisper.load_model("small", device="cpu")
    a = words(model, "cf02-01")
    b = words(model, "cf02-02")
    times = {
        "cf02-01": {
            "R": first(a, lambda i, w: w in ("r", "are")),
            "U": first(a, lambda i, w: w in ("u", "you")),
            "F": first(a, lambda i, w: w == "f"),
            "R'": first(a, lambda i, w: w.startswith("mark")),
            "U2": first(a, lambda i, w: w in ("two", "2") and a[i - 1][0] == "a"),
        },
        "cf02-02": {
            "2R": first(b, lambda i, w: w in ("two", "2", "2r", "tor") and (w == "2r" or b[i + 1][0] in ("r", "are"))),
            "M": first(b, lambda i, w: w in ("m", "em")),
        },
    }
    print(json.dumps(times))
    if "--write" in sys.argv:
        OUT.write_text(json.dumps(times, indent=2) + "\n")
        print(f"-> {OUT}")


if __name__ == "__main__":
    os.chdir(MEDIA)
    main()
