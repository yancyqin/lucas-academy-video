"""Delivery checks for 「你会算 7×8 吗？」 (Fun Economics 1's quality.py): codec, both caption files, black frames, loudness.
  python3 scripts/fun-economics-01-7x8/quality.py [--lang en]
"""
from common import FILM, OUT, PUB, base

if __name__ == "__main__":
    q = base("quality")
    q.PUB, q.OUT, q.DELIVERY, q.FILM_NAME = PUB, OUT, OUT / "delivery", FILM
    q.FOOTAGE = ["hands.{lang}.mp4", "page.{lang}.mp4"]
    q.LAST_CUE = "hx03-02"
    q.main()
