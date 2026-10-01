"""Restore the media this repository does not commit for "Why Did Van Gogh Paint Them?".

    python3 scripts/vg-why/fetch_assets.py      # needs Pillow

Downloads every work in public/vg-why-paint-them/art/SOURCES.txt from
Wikimedia Commons at its recorded size, re-applies the photo-border trims
recorded below, writes the ≤800 px tiles, and fetches the Van Gogh House music
(music/SOURCE.md). Each file is checked against its recorded SHA-256; a
mismatch is reported, not fatal (Commons can re-render a thumbnail, and a
re-encoded trim depends on the Pillow version). Existing files are kept.
The narration audio is not here: it is generated in lucas-academy-media.
"""
import hashlib
import json
import ssl
import time
import urllib.parse
import urllib.request
from io import BytesIO
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
ART = ROOT / "public/vg-why-paint-them/art"
MUSIC = ROOT / "public/vg-why-paint-them/music/van-gogh-human-horizon-a-v1.mp3"
MUSIC_URL = ("https://objects.lucasacademy.org/runtime/v1/audio/"
             "3396d5fa16b4be4e305e4a7b691ea8ad2eb987d146041b9a490876a0d3eeda23-van-gogh-human-horizon-a-v1.mp3")
MUSIC_SHA256 = "3396d5fa16b4be4e305e4a7b691ea8ad2eb987d146041b9a490876a0d3eeda23"
UA = {"User-Agent": "LucasAcademyMedia/0.1 (https://github.com/yancyqin/lucas-academy-video)"}
# Photographic borders cut from the full Commons original: pixels off (left, top, right, bottom).
TRIMS = {
    "berceuse-met": (44, 0, 20, 12),
    "first-steps": (12, 12, 12, 12),
    "mother-baby": (12, 20, 20, 12),
    "roulin": (36, 20, 44, 20),
    "wheat-cypresses": (28, 44, 36, 28),
}
Image.MAX_IMAGE_PIXELS = None
try:  # conda Pythons often lack the system CA store; certifi carries its own
    import certifi
    TLS = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    TLS = ssl.create_default_context()


def get(url: str) -> bytes:
    for attempt in range(8):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120, context=TLS).read()
        except Exception as error:  # Commons rate-limits bursts; back off and retry
            print(f"  retry {attempt + 1}: {error}")
            time.sleep(15 * (attempt + 1))
    raise SystemExit(f"could not download {url}")


def original_width(title: str) -> int:
    query = urllib.parse.urlencode({"action": "query", "format": "json", "titles": f"File:{title}",
                                    "prop": "imageinfo", "iiprop": "size"})
    page = next(iter(json.loads(get(f"https://commons.wikimedia.org/w/api.php?{query}"))["query"]["pages"].values()))
    return page["imageinfo"][0]["width"]


def main() -> None:
    (ART / "tiles").mkdir(parents=True, exist_ok=True)
    for line in (ART / "SOURCES.txt").read_text(encoding="utf-8").splitlines():
        if line.startswith("#") or not line.strip():
            continue
        work, page, sha256, size = (part.strip() for part in line.split(" | ")[:4])
        path = ART / f"{work}.jpg"
        if not path.exists():
            title = urllib.parse.unquote(page.split("File:", 1)[1]).replace("_", " ")
            width = int(size.split("x")[0])
            file_url = "https://commons.wikimedia.org/wiki/Special:FilePath/" + urllib.parse.quote(title)
            if work in TRIMS or width >= original_width(title):
                body = get(file_url)
            else:
                body = get(f"{file_url}?width={width}")
            if work in TRIMS:
                image = Image.open(BytesIO(body)).convert("RGB")
                left, top, right, bottom = TRIMS[work]
                image.crop((left, top, image.width - right, image.height - bottom)).save(path, quality=92)
            else:
                path.write_bytes(body)
            time.sleep(3)
        status = "ok" if hashlib.sha256(path.read_bytes()).hexdigest() == sha256 else "differs from the record"
        tile = ART / "tiles" / path.name
        if not tile.exists():
            image = Image.open(path).convert("RGB")
            image.thumbnail((800, 800))
            image.save(tile, quality=86)
        print(f"{work}: {status}")
    if not MUSIC.exists():
        MUSIC.write_bytes(get(MUSIC_URL))
    music_ok = hashlib.sha256(MUSIC.read_bytes()).hexdigest() == MUSIC_SHA256
    print(f"music: {'ok' if music_ok else 'differs from the record'}")


if __name__ == "__main__":
    main()
