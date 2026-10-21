#!/usr/bin/env python3
"""Pictures for the 牧神午后 living paintings (Impressionist only, owner 2026-10-16: no faun, no nudes) (art-lab living.html): crop scan borders, long side 1536, JPEG.

usage: python faune_living_pictures.py ART_LAB_REPO      -> ART_LAB_REPO/assets/living/faune-<name>.jpg
"""
import os, sys
from PIL import Image

ART = "/Users/yqin/repo/playground/lucas-academy-video-data/debussy-impressions/art"
PICS = {  # living id: (art id, crop fractions left, top, right, bottom)
    "faune-seine": ("fau-seine", (0, 0, 0, 0)),
    "faune-antibes": ("fau-antibes", (0, 0, 0, 0)),
    "faune-bridge": ("fau-bridge", (0, 0, 0, 0)),
    "faune-meadow": ("fau-meadow", (0, 0, 0, 0)),
    "faune-grenouillere": ("fau-grenouillere", (0.012, 0.014, 0.012, 0.014)),       # dark scan border
    "faune-bathers": ("isle-3", (0, 0, 0, 0)),
    "faune-jatte": ("isle-4", (0.01, 0.012, 0.01, 0.012)),                         # painted border band
    "faune-cliff": ("fau-cliff", (0, 0, 0, 0)),
    "faune-poppies": ("rev-2", (0, 0, 0, 0)),
    "faune-parasol": ("rev-1", (0, 0, 0, 0)),
    "faune-lilies": ("fau-lilies", (0.012, 0.022, 0.012, 0.016)),                  # black border in the scan
    "faune-summer": ("fau-summer", (0, 0, 0, 0)),
    "faune-path": ("fau-path", (0, 0, 0, 0)),
    "faune-springtime": ("rev-4", (0, 0, 0, 0)),
    "faune-cradle": ("rev-3", (0, 0, 0, 0)),
}

def main(repo):
    out = os.path.join(repo, "assets", "living"); os.makedirs(out, exist_ok=True)
    for lid, (aid, (l, t, r, b)) in PICS.items():
        im = Image.open(os.path.join(ART, f"{aid}.jpg")).convert("RGB"); w, h = im.size
        im = im.crop((round(l * w), round(t * h), round(w - r * w), round(h - b * h)))
        k = 1536 / max(im.size); im = im.resize((round(im.width * k / 2) * 2, round(im.height * k / 2) * 2), Image.LANCZOS)
        im.save(os.path.join(out, f"{lid}.jpg"), quality=90, optimize=True)
        print(f"{lid:22s} {im.width}x{im.height}")

if __name__ == "__main__":
    main(sys.argv[1])
