#!/usr/bin/env python3
"""Round 6 (Yancy 2026-11-12): the real side becomes real high-resolution photographs, wings as sharp as possible.

  inat_photos.py candidates            up to 12 candidates per slot -> photos/cand/<slot>/, sheets photos/cand/sheet-*.jpg
  inat_photos.py fetch <slot>=<id> …   download the chosen photo's original -> photos/<slot>.jpg, credits photos/credits.json

「真实的蝴蝶找真实的高清照 wing 尽量不blur」. Source: iNaturalist research-grade observations (species confirmed by
the community), photo licence CC0 or CC BY only (the channel is monetised; BY needs a credit line), original at least
1600 px wide and landscape, most-favourited first. Same species as the 10 video clips, so the reveal can still play
the clip; #4 (unidentified leopard-spotted butterfly in the clip) uses the Common Leopard, #9 the postman pair.
"""
import json, os, subprocess, sys, time, urllib.parse

DATA = "/Users/yqin/repo/playground/lucas-academy-video-data/butterfly-challenge"
UA = "butterfly-research/1.0"
SLOTS = {
    "g1": ["Greta oto"], "p08": ["Papilio polymnestor"], "p15": ["Siproeta stelenes"], "p16": ["Phalanta phalantha"],
    "p17": ["Aglais io"], "p18": ["Polyommatus icarus"], "p26": ["Limenitis arthemis astyanax"],
    "p44": ["Papilio polyxenes"], "p67": ["Heliconius erato", "Heliconius melpomene"], "p69": ["Ornithoptera euphorion"],
}


def get(url):
    out = subprocess.run(["curl", "-s", "-A", UA, url], capture_output=True, text=True, check=True).stdout
    time.sleep(1.1)  # iNaturalist asks for about one request a second
    return json.loads(out)


def candidates():
    from PIL import Image, ImageDraw, ImageFont
    os.makedirs(f"{DATA}/photos/cand", exist_ok=True)
    allc = {}
    for slot, taxa in SLOTS.items():
        found = []
        for taxon in taxa:
            q = urllib.parse.urlencode(dict(taxon_name=taxon, quality_grade="research", photo_license="cc0,cc-by",
                                            photos="true", per_page=60, order_by="votes"))
            for o in get(f"https://api.inaturalist.org/v1/observations?{q}")["results"]:
                for p in o["photos"]:
                    d = p.get("original_dimensions") or {}
                    if p.get("license_code") not in ("cc0", "cc-by") or d.get("width", 0) < 1600:
                        continue
                    if d["width"] < d["height"] * 1.2:
                        continue
                    found.append(dict(id=p["id"], obs=o["id"], taxon=o["taxon"]["name"], license=p["license_code"],
                                      attribution=p["attribution"], w=d["width"], h=d["height"],
                                      url=p["url"].replace("square.", "medium.")))
                    break  # one photo per observation
                if len(found) >= 12 * len(taxa) // len(taxa) and len(found) >= 12:
                    break
        found = found[:12]
        os.makedirs(f"{DATA}/photos/cand/{slot}", exist_ok=True)
        for c in found:
            subprocess.run(["curl", "-s", "-A", UA, "-o", f"{DATA}/photos/cand/{slot}/{c['id']}.jpg", c["url"]], check=True)
        allc[slot] = found
        print(slot, len(found), flush=True)
    json.dump(allc, open(f"{DATA}/photos/cand/candidates.json", "w"), indent=1)
    f = ImageFont.truetype("/System/Library/Fonts/Hiragino Sans GB.ttc", 20)
    slots = list(SLOTS)
    for s, chunk in enumerate([slots[i:i + 2] for i in range(0, len(slots), 2)]):
        W, H = 320, 180
        im = Image.new("RGB", (6 * W, 4 * H), "black"); dr = ImageDraw.Draw(im)
        for r, slot in enumerate(chunk):
            for i, c in enumerate(allc[slot]):
                t = Image.open(f"{DATA}/photos/cand/{slot}/{c['id']}.jpg").convert("RGB"); t.thumbnail((W, H))
                x, y = (i % 6) * W, (r * 2 + i // 6) * H
                im.paste(t, (x, y)); dr.rectangle([x, y, x + 150, y + 24], fill="black")
                dr.text((x + 3, y + 2), f"{slot} {c['id']}", fill="yellow", font=f)
        im.save(f"{DATA}/photos/cand/sheet-{s + 1}.jpg", quality=85)


def fetch(choices):
    allc = json.load(open(f"{DATA}/photos/cand/candidates.json"))
    credits = {}
    for ch in choices:
        slot, pid = ch.split("=")
        c = next(x for x in allc[slot] if str(x["id"]) == pid)
        url = c["url"].replace("medium.", "original.")
        subprocess.run(["curl", "-s", "-A", UA, "-o", f"{DATA}/photos/{slot}.jpg", url], check=True)
        credits[slot] = dict(c, original=url, page=f"https://www.inaturalist.org/observations/{c['obs']}")
        print(slot, pid, c["taxon"], c["license"], c["attribution"])
    path = f"{DATA}/photos/credits.json"
    old = json.load(open(path)) if os.path.exists(path) else {}
    old.update(credits)
    json.dump(old, open(path, "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "candidates":
        candidates()
    elif len(sys.argv) > 2 and sys.argv[1] == "fetch":
        fetch(sys.argv[2:])
    else:
        sys.exit(__doc__)
