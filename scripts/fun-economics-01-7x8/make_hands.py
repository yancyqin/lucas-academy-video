"""The hand footage for 「你会算 7×8 吗？」 (Fun Economics 1's make_hands.py): one take on one speed curve over hx01-01
and hx01-02, the left hand making its 2 on 「左手」 / "left" and the right hand its 3 on 「右手」 / "right".
  ../lucas-academy-media/.conda/bin/python scripts/fun-economics-01-7x8/make_hands.py [--lang en]
"""
import json

from common import LANG, OUT, PUB, base

WORDS = {"zh": ("左", "右"), "en": ("left", "right")}


def word_time(words: list, cue: dict, start: str) -> float:
    """Film time of the first word of a cue's take that starts with `start`."""
    word = next(w for w in words if w["w"].lower().strip(" ,.;:").startswith(start))
    return cue["speech"]["start"] + word["start"] - cue.get("trim", 0.0)


if __name__ == "__main__":
    h = base("make_hands")
    cues = {c["id"]: c for c in json.loads((PUB / f"timeline.{LANG}.json").read_text())["cues"]}
    words = json.loads((OUT / f"narration-check.{LANG}.json").read_text())["cues"]["hx01-01"]["words"]
    a, b = cues["hx01-01"]["start"] - h.FADE, cues["hx01-02"]["end"]
    left, right = (word_time(words, cues["hx01-01"], w) - a for w in WORDS[LANG])
    (PUB / "footage").mkdir(parents=True, exist_ok=True)
    h.write(h.gestures(left, right, b - a, open_from=0.3), a, b, PUB / f"footage/hands.{LANG}.mp4")
    print(f"left hand at +{left:.2f} s, right at +{right:.2f} s")
