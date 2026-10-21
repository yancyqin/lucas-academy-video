#!/usr/bin/env python3
"""月光 (Clair de lune): cut the 16:9 photo frames for the web photos.

Each frame is both the photo the shot starts on and the picture Codex paints from, so the AI painting
is born in the same 16:9 frame. ANCHOR is where the crop sits vertically (0 = keep the top, 1 = keep the
bottom); None means the photo is too square to crop and Codex widens it instead (see codex_prompts.py).
Sources: Pexels at 2560 px wide in clair/full/<pexels id>.jpg (downloaded if missing).
usage: .venv-reframe/bin/python clair_frames.py
"""
import json, os, subprocess
from PIL import Image

DATA = "/Users/yqin/repo/playground/lucas-academy-video-data/debussy-impressions/clair"
FRAMES = {  # key: (pexels id, anchor)
    "moonpath": (15406028, 0.8), "moonrise-sea": (14686005, 0.5), "stilt-hut": (31361084, 0.6),
    "pink-moon-boat": (7669917, 0.0), "alicante-sail": (32046825, 0.7), "reeds-lake": (14316861, 0.55),
    "river-bridge": (18281187, 0.3), "frozen-lake": (29801134, 0.5), "fjord-clouds": (30069979, 0.0),
    "lilac-branches": (35507692, 0.5), "birds-branches": (34195216, 0.6), "lone-tree": (12453183, None),
    "roof-moon": (6017481, 0.5), "mackerel-moon": (11336937, 0.5), "honfleur": (5839301, 0.5),
    "fishing-pier": (30084110, 0.5), "marina": (18762006, 0.35), "dubrovnik": (16907852, 0.0),
    "river-village": (13734062, 0.45), "cypresses": (9039685, 0.8), "cypress-sea": (5353962, 0.6),
    "cobble-street": (7367686, 0.5), "swiss-village": (16347761, 0.6), "milkyway-lake": (27408592, 0.5),
    "alpenglow": (6531876, 0.6), "lavender": (13604873, 0.5),
}

def main():
    os.makedirs(f"{DATA}/full", exist_ok=True); os.makedirs(f"{DATA}/frames", exist_ok=True)
    out = {}
    for key, (pid, anc) in FRAMES.items():
        src = f"{DATA}/full/{pid}.jpg"
        if not os.path.exists(src):
            subprocess.run(["curl", "-s", "-f", "-o", src, f"https://images.pexels.com/photos/{pid}/pexels-photo-{pid}.jpeg?auto=compress&cs=tinysrgb&w=2560"], check=True)
        im = Image.open(src).convert("RGB"); w, h = im.size
        if anc is None:
            out[key] = {"pexels": pid, "source": f"full/{pid}.jpg", "frame": None, "note": "too square: Codex widens it to 16:9 first"}
            continue
        ch = round(w * 9 / 16)
        if ch <= h:
            y0 = round((h - ch) * anc); box = (0, y0, w, y0 + ch)
        else:                                   # wider than 16:9: crop the sides, centred
            cw = round(h * 16 / 9); x0 = (w - cw) // 2; box = (x0, 0, x0 + cw, h)
        im.crop(box).save(f"{DATA}/frames/{key}.jpg", quality=93)
        out[key] = {"pexels": pid, "source": f"full/{pid}.jpg", "frame": f"frames/{key}.jpg", "crop": box, "size": [box[2] - box[0], box[3] - box[1]]}
    json.dump(out, open(f"{DATA}/frames/frames.json", "w"), indent=1)
    for k, v in out.items(): print(f"{k:15s} {v.get('size') or v['note']}")

if __name__ == "__main__":
    main()
