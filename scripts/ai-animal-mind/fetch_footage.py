"""Download the Pexels clips listed in docs/ai-animal-mind/footage-sources.json (1080p files).

    python3 scripts/ai-animal-mind/fetch_footage.py

Writes lucas-academy-video-data/ai-animal-mind/footage/pexels/<id>.mp4; files already there are kept. The clips were
picked from Pexels search pages read in the browser (scripts get a Cloudflare check there); the video CDN itself
serves plain downloads. Credits stay in the JSON for the YouTube description. Six downloads run at once.
"""
import json
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = next(p / "lucas-academy-video-data" for p in ROOT.parents if (p / "lucas-academy-video-data").is_dir())
OUT = DATA / "ai-animal-mind/footage/pexels"
SRC = json.loads((ROOT / "docs/ai-animal-mind/footage-sources.json").read_text())["pexels"]
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36"


def fetch(item):
    pid, info = item
    path = OUT / f"{pid}.mp4"
    if path.is_file() and path.stat().st_size > 0:
        return f"keep {pid}"
    r = subprocess.run(["curl", "-sSfL", "-A", UA, "-o", str(path), info["link"]], capture_output=True, text=True)
    if r.returncode:
        path.unlink(missing_ok=True)
        return f"FAIL {pid} {r.stderr.strip()[:120]}"
    return f"ok {pid} {path.stat().st_size / 1e6:.1f} MB"


OUT.mkdir(parents=True, exist_ok=True)
with ThreadPoolExecutor(6) as pool:
    for line in pool.map(fetch, SRC.items()):
        print(line, flush=True)
