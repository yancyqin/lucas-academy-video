#!/usr/bin/env python3
"""Find and fetch public-domain paintings on Wikimedia Commons.

  commons_art.py search "Monet Morning on the Seine"        top File: hits with size and licence
  commons_art.py fetch ID "File:Exact name.jpg" [ID "File:…" …]
        -> art/<ID>.jpg (3840 px wide thumbnail, or the original if smaller) + an entry in art/art-sources.json
Uses the Commons API with a descriptive User-Agent; thumbnails only at the allowed widths (3840 here).
"""
import json, os, sys, time, urllib.parse, urllib.request

ART = "/Users/yqin/repo/playground/lucas-academy-video-data/debussy-impressions/art"
API = "https://commons.wikimedia.org/w/api.php"
UA = "LucasAcademyVideoResearch/1.0 (yqin@paciolan.com)"

def api(**params):
    params.update(format="json")
    req = urllib.request.Request(API + "?" + urllib.parse.urlencode(params), headers={"User-Agent": UA})
    return json.load(urllib.request.urlopen(req, timeout=40))

def info(titles):
    d = api(action="query", titles="|".join(titles), prop="imageinfo", iiprop="url|size|extmetadata", iiurlwidth=3840)
    out = {}
    for p in d["query"]["pages"].values():
        if "imageinfo" not in p: out[p["title"]] = None; continue
        ii = p["imageinfo"][0]; m = ii.get("extmetadata", {})
        out[p["title"]] = {"w": ii["width"], "h": ii["height"], "url": ii["url"], "thumb": ii.get("thumburl"),
                           "page": ii["descriptionurl"], "license": m.get("LicenseShortName", {}).get("value", ""),
                           "artist": m.get("Artist", {}).get("value", "")[:120]}
    return out

def search(q):
    d = api(action="query", list="search", srsearch=q, srnamespace=6, srlimit=12)
    titles = [h["title"] for h in d["query"]["search"]]
    if not titles: print("no hits"); return
    for t, v in info(titles).items():
        if v: print(f"{v['w']:5d}x{v['h']:<5d} {v['license'][:16]:16s} {t}")

def fetch(pairs):
    path = os.path.join(ART, "art-sources.json")
    src = json.load(open(path)); have = {a["id"]: a for a in src}
    meta = info([t for _, t in pairs])
    for pid, title in pairs:
        v = meta.get(title)
        if not v: print("MISSING", pid, title); continue
        url = v["thumb"] if v["w"] > 3840 and v["thumb"] else v["url"]
        dst = os.path.join(ART, f"{pid}.jpg")
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        for attempt in range(4):
            try:
                data = urllib.request.urlopen(req, timeout=120).read(); break
            except Exception as e:
                print("retry", pid, e); time.sleep(20 * (attempt + 1))
        else:
            print("FAILED", pid); continue
        open(dst, "wb").write(data)
        w = min(v["w"], 3840); h = round(v["h"] * w / v["w"])
        have[pid] = {"id": pid, "file": title.replace("File:", ""), "orig_w": v["w"], "orig_h": v["h"], "saved": f"{pid}.jpg",
                     "w": w, "h": h, "bytes": len(data), "url": url, "page": v["page"], "license": v["license"]}
        print(f"{pid}: {w}x{h} {len(data)//1024} KB  {v['license']}")
        time.sleep(2)
    json.dump(list(have.values()), open(path, "w"), ensure_ascii=False, indent=1)

if __name__ == "__main__":
    if sys.argv[1] == "search": search(" ".join(sys.argv[2:]))
    elif sys.argv[1] == "fetch": fetch(list(zip(sys.argv[2::2], sys.argv[3::2])))
