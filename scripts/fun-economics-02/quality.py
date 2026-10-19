"""Delivery checks for one language's film of 「都学了三年，放弃就白学了吗？」, with episode 1's checker: every take
checked, codec and frame count, both caption files, no black frames, loudness, and no placeholder footage (every clip
the shot list names is in the footage folder). Writes out/fun-economics-02/delivery-check.<lang>.json.
Run after render.py.
  python3 scripts/fun-economics-02/quality.py [--lang en]
"""
import re

from common import FILM, OUT, PUB, ROOT, base

q = base("quality")
q.PUB, q.OUT, q.DELIVERY, q.FILM_NAME, q.LAST_CUE = PUB, OUT, OUT / "delivery", FILM, "sc09-01"
q.FOOTAGE = sorted(set(re.findall(r'clip\("([^"]+\.mp4)"', (ROOT / "src/videos/fun-economics-02/FunEconomics02Video.tsx").read_text())))

if __name__ == "__main__":
    q.main()
