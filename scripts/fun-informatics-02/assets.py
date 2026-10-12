"""Fetch museum/Commons still assets with their own recorded licensing metadata."""
import concurrent.futures
import hashlib
import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PUB = ROOT / "public/fun-informatics-02"
MANIFEST = ROOT / "docs/fun-informatics-02/assets.json"
AGENT = "LucasAcademyVideo/1.0 (lucasacademy.org; educational film)"
COMMONS = {
    "monet-bridge-1899": "File:Bridge Over a Pond of Water Lilies, Claude Monet 1899.jpg",
    "impression-sunrise": "File:Claude Monet, Impression, soleil levant.jpg",
    "monet-nadar-1899": "File:Claude Monet 1899 Nadar crop.jpg",
    "debussy-nadar-1908": "File:Claude Debussy ca 1908, foto av Félix Nadar.jpg",
    "daguerre-boulevard": "File:Boulevard du Temple by Daguerre.jpg",
}
AIC = {"water-lilies-1906": 16568, "stacks-summer": 64818, "stacks-autumn": 14624, "stacks-snow": 81545}


def request(url):
    for attempt in range(4):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": AGENT}), timeout=45)
        except urllib.error.HTTPError as error:
            if error.code not in (429, 502, 503) or attempt == 3:
                raise
            time.sleep(4 * (attempt + 1))


def json_at(url):
    with request(url) as response:
        return json.load(response)


def metadata():
    records = []
    url = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode({"action": "query", "format": "json", "prop": "imageinfo", "iiprop": "url|extmetadata", "titles": "|".join(COMMONS.values())})
    pages = {p["title"]: p for p in json_at(url)["query"]["pages"].values()}
    for name, title in COMMONS.items():
        page = pages[title]
        if not page.get("imageinfo"):
            raise RuntimeError(f"Missing Commons original: {title}")
        info = page["imageinfo"][0]
        meta = info["extmetadata"]
        license_name = meta.get("LicenseShortName", {}).get("value", "")
        if license_name not in ("Public domain", "CC0") and not re.fullmatch(r"CC BY \d\.\d", license_name):
            raise RuntimeError(f"Unapproved asset license: {title}: {license_name}")
        records.append({"name": name, "path": f"art/{name}.jpg", "title": title.removeprefix("File:"), "source": info["descriptionurl"], "download": info["url"].split("?")[0], "license": license_name, "metadata": meta})
    for name, object_id in AIC.items():
        data = json_at(f"https://api.artic.edu/api/v1/artworks/{object_id}")["data"]
        assert data["is_public_domain"] is True and data["image_id"]
        records.append({"name": name, "path": f"art/{name}.jpg", "title": data["title"], "date": data["date_display"], "author": data["artist_display"], "source": f"https://www.artic.edu/artworks/{object_id}", "download": f"https://www.artic.edu/iiif/2/{data['image_id']}/full/3000,/0/default.jpg", "license": "CC0", "licenseSource": "https://www.artic.edu/open-access/open-access-images", "isPublicDomain": data["is_public_domain"]})
    return records


def fetch(record):
    path = PUB / record["path"]
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        with request(record["download"]) as response:
            blob = response.read()
        assert len(blob) > 5000, record["name"]
        temporary = path.with_suffix(".download")
        temporary.write_bytes(blob)
        temporary.replace(path)
    record["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    record["bytes"] = path.stat().st_size
    print(f"{record['name']}: {record['bytes']} bytes; {record['license']}", flush=True)
    return record


def main():
    records = metadata()
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        records = list(pool.map(fetch, records))
    MANIFEST.write_text(json.dumps({"checked": "2026-10-07", "assets": records}, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
