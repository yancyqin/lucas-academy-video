"""Move the finished film into its Desktop upload folder (only the upload files; one copy each).

  python3 scripts/bread-or-dog/package.py --tag film-v04

Yancy, 2026-11-17: 「做好以后放到桌面上传文件夹」. As the project's rule (one new top-level Desktop 「…-上传」 folder per
upload, nothing else in it; files are moved, not copied, and checked by md5):
  ~/Desktop/狗还是面包怎么骗过AI-上传/
      bread-or-dog.mp4 (English track) · bread-or-dog.zh.m4a (Chinese track) · bread-or-dog.en.srt · bread-or-dog.zh-Hans.srt
      youtube-description.{en,zh}.txt · youtube-cover.{zh,en}.jpg (A) · youtube-cover-B.{zh,en}.jpg (alternate)
The covers are Codex PNGs (data covers/cover_{A,B}_{zh,en}.png), saved as 1280×720 JPG.
"""
import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
args = sys.argv[1:]
TAG = args[args.index("--tag") + 1] if "--tag" in args else "film-v04"
FILM = ROOT / "out/bread-or-dog" / TAG
DATA = next(p / "lucas-academy-video-data" for p in ROOT.parents if (p / "lucas-academy-video-data").is_dir()) / "bread-or-dog"
DESK = Path.home() / "Desktop"
FILM_DIR = DESK / "狗还是面包怎么骗过AI-上传"


def md5(p: Path) -> str:
    return hashlib.md5(p.read_bytes()).hexdigest()


def move(src: Path, dst: Path) -> None:
    h = md5(src)
    shutil.move(str(src), str(dst))
    assert md5(dst) == h, dst
    print(f"{dst.name}  {h[:8]}")


def cover(src: Path, dst: Path) -> None:
    subprocess.run(["sips", "-s", "format", "jpeg", "-s", "formatOptions", "92", "-z", "720", "1280", str(src), "--out", str(dst)],
                   check=True, capture_output=True)
    print(dst.name)


def main():
    for d in (FILM_DIR,):
        if d.exists() and any(d.iterdir()):
            raise SystemExit(f"{d} is not empty; look at it first")
        d.mkdir(parents=True, exist_ok=True)
    move(FILM / "bread-or-dog.mp4", FILM_DIR / "bread-or-dog.mp4")
    move(FILM / "bread-or-dog.zh.m4a", FILM_DIR / "bread-or-dog.zh.m4a")
    # captions timed to the English (default) track; the Chinese track's lines start at the same moments
    move(FILM / "bread-or-dog.en-track.en.srt", FILM_DIR / "bread-or-dog.en.srt")
    move(FILM / "bread-or-dog.en-track.zh-Hans.srt", FILM_DIR / "bread-or-dog.zh-Hans.srt")
    for lang in ("en", "zh"):
        move(FILM / f"youtube-description.{lang}.txt", FILM_DIR / f"youtube-description.{lang}.txt")
        cover(DATA / f"covers/cover_A_{lang}.png", FILM_DIR / f"youtube-cover.{lang}.jpg")
        cover(DATA / f"covers/cover_B_{lang}.png", FILM_DIR / f"youtube-cover-B.{lang}.jpg")
    for d in (FILM_DIR,):
        print(d.name, sorted(p.name for p in d.iterdir()))


if __name__ == "__main__":
    main()
