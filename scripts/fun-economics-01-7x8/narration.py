"""Narration inputs for 「你会算 7×8 吗？」 from docs/fun-economics-01-7x8/{zh,en}-edit.md, with Fun Economics 1's rules
(numbers spelled out for the voice, captions keep them; the other language from each line's `>` translation).

Six lines are word for word the finger lines of Fun Economics 1 v0.7, whose takes are reused: reuse_takes() copies
them in under this film's ids, so narrate.py only voices the new ones.
  python3 scripts/fun-economics-01-7x8/narration.py
"""
import shutil

from common import FILM, PUB, DOCS, ROOT, VOICES, base

REUSE = {"hx01-02": "oc04-09", "hx02-01": "oc04-10", "hx02-02": "oc04-11", "hx02-03": "oc04-12", "hx02-05": "oc04-13", "hx03-01": "oc04-14"}
TAKES = next(p / "lucas-academy-video-data/fun-economics-01/finger-takes-v0.7" for p in ROOT.parents
             if (p / "lucas-academy-video-data").is_dir())


def reuse_takes() -> None:
    for lang in ("zh", "en"):
        out = VOICES[lang]["narrator"]
        out.mkdir(parents=True, exist_ok=True)
        for new, old in REUSE.items():
            if not (out / f"{new}.wav").exists():
                shutil.copy2(TAKES / lang / f"{old}.wav", out / f"{new}.wav")


if __name__ == "__main__":
    n = base("narration")
    n.SRC, n.OUT, n.CUES = DOCS, PUB / "narration", 10
    n.ROWS = ("hx02",)  # the grid line: 10 行, 2 行, 8 行 are rows (háng)
    n.QUESTIONS = {"hx00-01", "hx03-02"}
    # the reused zh take of oc04-10 was voiced with this reading (a stray word came out with the period)
    n.RETAKE = {"zh": {"hx02-01": ("看弯着的手指。七是", "看弯着的手指：七是")}, "en": {}}
    n.main()
    reuse_takes()
    print(f"{FILM}: reused {len(REUSE)} takes per language")
