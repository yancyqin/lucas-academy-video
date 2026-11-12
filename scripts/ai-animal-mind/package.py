"""Upload package for 「动物想什么？AI 知道吗？」 on the Desktop (only what gets uploaded; working copies stay in out/).

    python3 scripts/ai-animal-mind/package.py            the film
    python3 scripts/ai-animal-mind/package.py --shorts   the two vertical shorts, in their own folder

One picture with two voice tracks (Yancy 2026-11-10): the 1080p film with the English track (Yancy 11-11: 「应该是英文
视频，配中文m4a」, the other way round from 你爱听 AI 说「是的」吗？), the Chinese track as an M4A to add in YouTube Studio
(Languages → audio track), captions in both
languages (every line starts at the same moment in both tracks, so either set fits either track), the upload text in
both languages, and the covers: B, the thinking macaque (Yancy 11-11: 「用B」), plus D, the surprised swimmer with the
dolphin, as the alternative for YouTube's thumbnail test. Run build_timeline.py, render.py (both languages),
youtube.py and cover_images.py first.
"""
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = next(p / "lucas-academy-video-data" for p in ROOT.parents if (p / "lucas-academy-video-data").is_dir())
OUT = ROOT / "out/ai-animal-mind/delivery"
COVERS = DATA / "ai-animal-mind/covers"
NAME = "动物想什么AI知道吗"
DEST = Path.home() / "Desktop" / f"{NAME}-上传"

FILES = {
    f"{NAME}-英文.mp4": OUT / "ai-animal-mind.en.mp4",
    f"{NAME}.zh-Hans.srt": OUT / "ai-animal-mind.zh.zh-Hans.srt",
    f"{NAME}.en.srt": OUT / "ai-animal-mind.en.en.srt",
    "youtube-description.zh.txt": OUT / "youtube-description.zh.txt",
    "youtube-description.en.txt": OUT / "youtube-description.en.txt",
    "youtube-cover.zh.jpg": COVERS / "cover-b-monkey-face.zh.jpg",
    "youtube-cover.en.jpg": COVERS / "cover-b-monkey-face.en.jpg",
    "youtube-cover-备选.zh.jpg": COVERS / "cover-d-surprised-swimmer.zh.jpg",
    "youtube-cover-备选.en.jpg": COVERS / "cover-d-surprised-swimmer.en.jpg",
}


SHORT_NAMES = {"ocean": "海洋篇", "animals": "陆地篇"}
SHORTS_DEST = Path.home() / "Desktop" / f"{NAME}-竖屏短视频-上传"


def shorts() -> None:
    """The two vertical shorts (build_short.py, render_short.py, youtube.py) in their own Desktop folder
    (python3 scripts/ai-animal-mind/package.py --shorts): like the film, each is the English video plus the Chinese
    track as an M4A (Yancy 11-11: 「给英文视频配单独的中文音轨就好了」), captions in both languages, upload text in both."""
    src = ROOT / "out/ai-animal-mind/shorts"
    files = {}
    for key, zh in SHORT_NAMES.items():
        files[f"{NAME}-{zh}-英文.mp4"] = src / f"{key}.mp4"
        files[f"{NAME}-{zh}-中文音轨.m4a"] = src / f"{key}.zh.m4a"
        files[f"{NAME}-{zh}.en.srt"] = src / f"{key}.en.srt"
        files[f"{NAME}-{zh}.zh-Hans.srt"] = src / f"{key}.zh-Hans.srt"
        for lang in ("en", "zh"):
            files[f"youtube-{zh}.{lang}.txt"] = src / f"youtube-{key}.{lang}.txt"
    missing = [str(p) for p in files.values() if not p.is_file()]
    if missing:
        raise SystemExit("missing:\n  " + "\n  ".join(missing))
    SHORTS_DEST.mkdir(parents=True, exist_ok=True)
    for name, p in files.items():
        shutil.copy2(p, SHORTS_DEST / name)
    for p in sorted(SHORTS_DEST.iterdir()):
        print(f"{p.stat().st_size / 1e6:9.1f} MB  {p.name}")
    print(SHORTS_DEST)


def main() -> None:
    missing = [str(src) for src in FILES.values() if not src.is_file()]
    if missing:
        raise SystemExit("missing:\n  " + "\n  ".join(missing))
    DEST.mkdir(parents=True, exist_ok=True)
    for old in (f"{NAME}.mp4", f"{NAME}-英文音轨.m4a"):  # the first package (11-11) had the Chinese film + English M4A
        (DEST / old).unlink(missing_ok=True)
    for name, src in FILES.items():
        shutil.copy2(src, DEST / name)
    m4a = DEST / f"{NAME}-中文音轨.m4a"  # the Chinese mix as rendered (AAC 256k), stream-copied, no re-encode
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(OUT / "ai-animal-mind.zh.mp4"), "-vn", "-c:a", "copy",
                    "-metadata:s:a:0", "language=zho", "-movflags", "+faststart", str(m4a)], check=True)
    for p in sorted(DEST.iterdir()):
        print(f"{p.stat().st_size / 1e6:9.1f} MB  {p.name}")
    print(DEST)


if __name__ == "__main__":
    import sys
    shorts() if "--shorts" in sys.argv else main()
