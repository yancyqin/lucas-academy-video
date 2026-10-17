"""Timeline, narration mix and both caption files for 「你会算 7×8 吗？」, built by Fun Economics 1's build_timeline.py.
One piece of music (the Minuet in G, as Fun Economics 1 opens). Writes public/fun-economics-01-7x8/timeline.<lang>.json,
audio/<lang>.mix.wav and out/fun-economics-01-7x8/delivery/fun-economics-01-7x8.<lang>.{zh-Hans,en}.srt
  python3 scripts/fun-economics-01-7x8/build_timeline.py [--lang en] [--srt-only]
"""
import json
import sys

from common import FILM, LANG, OUT, PUB, ROOT, VOICES, base

b = base("build_timeline")
b.PUB, b.DELIVERY, b.FILM_NAME, b.VOICES = PUB, OUT / "delivery", FILM, VOICES
b.TITLE = {"zh": "你会算 7×8 吗？", "en": "Can You Work Out 7 × 8?"}
# Seconds after a line for the picture: the title card, a gesture to copy, an animation to finish, the last question.
b.HOLD = {"hx00-01": 3.5, "hx01-01": 2.0, "hx01-02": 1.5, "hx02-02": 3.0, "hx02-03": 1.0, "hx02-04": 2.0,
          "hx02-05": 1.5, "hx03-01": 1.5, "hx03-02": 3.5}
b.BED = [("hx00", ROOT / "public/fun-economics-01/music/minuet-in-g-musopen.ogg")]

if __name__ == "__main__":
    if "--srt-only" in sys.argv:
        b.write_srt(json.loads((PUB / f"timeline.{LANG}.json").read_text())["cues"], LANG)
    else:
        b.build(LANG)
