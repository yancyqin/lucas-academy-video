"""Download the film's stock footage and illustrations listed in docs/fun-informatics-04/footage-sources.json.

    python3 scripts/fun-informatics-04/fetch_sources.py

Pexels clips (1080p) -> public/fun-informatics-04/footage/pexels/<id>.mp4; Wikimedia Commons clips (the original
files, resolved through the Commons API) -> footage/commons/<key>.<ext>; Nobel Prize illustrations ->
footage/nobel/<key>.jpg. Files already there are kept. Credits stay in the JSON; the end card and the YouTube text
read them from there.
"""
import json
import subprocess
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = json.loads((ROOT / "docs/fun-informatics-04/footage-sources.json").read_text())
OUT = ROOT / "public/fun-informatics-04/footage"
UA = {"User-Agent": "LucasAcademyVideo/1.0 (yqin; educational film credits kept)"}


def fetch(url: str, path: Path) -> None:
    if path.is_file() and path.stat().st_size > 0:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["curl", "-sSfL", "-A", UA["User-Agent"], "-o", str(path), url], check=True)
    print(f"{path.relative_to(ROOT)}  {path.stat().st_size / 1e6:.1f} MB", flush=True)


def commons_url(name: str) -> str:
    q = urllib.parse.urlencode({"action": "query", "titles": f"File:{name}", "prop": "imageinfo", "iiprop": "url",
                                "format": "json"})
    with urllib.request.urlopen(urllib.request.Request(f"https://commons.wikimedia.org/w/api.php?{q}", headers=UA)) as r:
        page = next(iter(json.load(r)["query"]["pages"].values()))
    return page["imageinfo"][0]["url"]


for pid, item in SRC["pexels"].items():
    fetch(item["link"], OUT / f"pexels/{pid}.mp4")
for key, item in SRC["commons"].items():
    fetch(commons_url(item["file"]), OUT / f"commons/{key}{Path(item['file']).suffix}")
    time.sleep(1)
for key, name in SRC["nobel"]["files"].items():
    fetch(SRC["nobel"]["base"] + name, OUT / f"nobel/{key}.jpg")
