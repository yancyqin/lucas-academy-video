"""Whisper check of every take and the page's step anchors for 「你会算 7×8 吗？」 (Fun Economics 1's check.py).
The page plays its finger scene (s3) with the 10 × 10 grid scene (s6) between the formula and the x, y proof.
  ../lucas-academy-media/.conda/bin/python scripts/fun-economics-01-7x8/check.py [--lang en]
"""
from common import LANG, OUT, PUB, VOICES, base

ANCHORS = {
    "zh": {
        "s3.0": ("hx02-01", None), "s3.1": ("hx02-01", "七是"), "s3.2": ("hx02-01", "右手"), "s3.3": ("hx02-02", None),
        "s3.4": ("hx02-02", "拆开"), "s3.5": ("hx02-03", None), "s3.6": ("hx02-03", "减三十"), "s3.7": ("hx02-03", "剩下"),
        "s3.8": ("hx02-03", "最后"),
        "s6.0": ("hx02-04", None), "s6.1": ("hx02-04", "减三十"), "s6.2": ("hx02-04", "减二十"), "s6.3": ("hx02-04", "右下角"),
        "s6.4": ("hx02-04", "所以"), "s6.5": ("hx02-04", "剩下的"),
        "s3.9": ("hx02-05", None), "s3.10": ("hx02-05", "拆开"), "s3.11": ("hx02-05", "根手指"),
        "s3.12": ("hx03-01", None), "s3.13": ("hx03-01", "这就是"),
    },
    "en": {
        "s3.0": ("hx02-01", None), "s3.1": ("hx02-01", "seven is five"), "s3.2": ("hx02-01", "right hand"), "s3.3": ("hx02-02", None),
        "s3.4": ("hx02-02", "split it"), "s3.5": ("hx02-03", None), "s3.6": ("hx02-03", "minus thirty"), "s3.7": ("hx02-03", "which leaves"),
        "s3.8": ("hx02-03", "we add"),
        "s6.0": ("hx02-04", None), "s6.1": ("hx02-04", "minus thirty"), "s6.2": ("hx02-04", "minus twenty"), "s6.3": ("hx02-04", "the corner"),
        "s6.4": ("hx02-04", "so we add"), "s6.5": ("hx02-04", "what's left"),
        "s3.9": ("hx02-05", None), "s3.10": ("hx02-05", "split up"), "s3.11": ("hx02-05", "fingers without"),
        "s3.12": ("hx03-01", None), "s3.13": ("hx03-01", "this is what thinking"),
    },
}

if __name__ == "__main__":
    c = base("check")
    c.PUB, c.OUT, c.VOICES, c.ANCHORS = PUB, OUT / f"narration-check.{LANG}.json", VOICES, ANCHORS[LANG]
    c.main()
