"""Upload package for 「Challenge: Which Butterflies Are Real?」 on the Desktop: only what gets uploaded.

    python3 scripts/butterfly-challenge/package.py [--tag film]

Like 「动物想什么？AI 知道吗？」 (scripts/ai-animal-mind/package.py): one picture with two voice tracks, so the English film
(the default track, Yancy 2026-11-12: 「默认语言英文，配中文音轨」), the Chinese track as an M4A to add in YouTube Studio
(Languages → audio track), captions in both languages (timed to the English track; every line starts at the same moment
in the Chinese track), the upload text in both languages, and every cover in both languages (Yancy 11-12:
「封面都放包里我看看」: A, B, C, not yet chosen). The film, the M4A and the captions are moved, not copied, so only one
copy exists (README / upload-folder rule); the mp4's md5 is checked against the render before and after the move.
Run build_timeline.py, render.py, youtube.py and cover_images.py first.
"""
import hashlib
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = next(p / "lucas-academy-video-data" for p in ROOT.parents if (p / "lucas-academy-video-data").is_dir())
args = sys.argv[1:]
OUT = ROOT / "out/butterfly-challenge" / (args[args.index("--tag") + 1] if "--tag" in args else "film")
COVERS = DATA / "butterfly-challenge/covers"
NAME = "猜一猜哪些蝴蝶是真的"
DEST = Path.home() / "Desktop" / f"{NAME}-上传"

MOVE = {  # renders: moved into the folder
    f"{NAME}-英文.mp4": OUT / "butterfly-challenge.mp4",
    f"{NAME}-中文音轨.m4a": OUT / "butterfly-challenge.zh.m4a",
    f"{NAME}.en.srt": OUT / "butterfly-challenge.en-track.en.srt",
    f"{NAME}.zh-Hans.srt": OUT / "butterfly-challenge.en-track.zh-Hans.srt",
}
COPY = {  # text and covers: copied (their sources are the generators' outputs and the data folder)
    "youtube-description.en.txt": OUT / "youtube-description.en.txt",
    "youtube-description.zh.txt": OUT / "youtube-description.zh.txt",
    # A and B from real photographs (cover_real.py; Yancy 11-12: 「用A B的蝴蝶，但使用真实的照片合成」), C still Codex
    **{f"youtube-cover-{k}.{lang}.jpg": COVERS / f"{v}.{lang}.jpg"
       for k, v in (("A", "real/cover-a-real"), ("B", "real/cover-b-real"), ("C", "cover-c-magnifier")) for lang in ("en", "zh")},
}


def md5(p: Path) -> str:
    h = hashlib.md5()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    missing = [str(p) for p in {**MOVE, **COPY}.values() if not p.is_file()]
    if missing:
        raise SystemExit("missing:\n  " + "\n  ".join(missing))
    before = md5(MOVE[f"{NAME}-英文.mp4"])
    DEST.mkdir(parents=True, exist_ok=True)
    for name, src in MOVE.items():
        shutil.move(str(src), DEST / name)
    for name, src in COPY.items():
        shutil.copy2(src, DEST / name)
    after = md5(DEST / f"{NAME}-英文.mp4")
    assert before == after, "mp4 changed in the move"
    (OUT / "PACKAGED.txt").write_text(f"moved to {DEST}\nmp4 md5 {after}\n")
    for p in sorted(DEST.iterdir()):
        print(f"{p.stat().st_size / 1e6:9.1f} MB  {p.name}")
    print(DEST, "mp4 md5", after)


if __name__ == "__main__" and "--shorts" not in sys.argv:
    main()


SHORT_NAMES = {"blue-mormon": "蓝摩门凤蝶", "leopard": "豹纹蛱蝶"}
SHORTS_DEST = Path.home() / "Desktop" / f"{NAME}-竖屏短视频-上传"


def shorts() -> None:
    """The two vertical shorts (build_short.py, render_short.py, youtube.py --shorts) in their own Desktop folder: per
    short the English video, the Chinese track as an M4A, captions in both languages, upload text in both. Renders and
    captions are moved, upload text copied."""
    src = ROOT / "out/butterfly-challenge/shorts"
    move, copy = {}, {}
    for key, zh in SHORT_NAMES.items():
        move[f"{NAME}-{zh}-英文.mp4"] = src / key / f"{key}.mp4"
        move[f"{NAME}-{zh}-中文音轨.m4a"] = src / key / f"{key}.zh.m4a"
        move[f"{NAME}-{zh}.en.srt"] = src / key / f"{key}.en.srt"
        move[f"{NAME}-{zh}.zh-Hans.srt"] = src / key / f"{key}.zh-Hans.srt"
        for lang in ("en", "zh"):
            copy[f"youtube-{zh}.{lang}.txt"] = src / key / f"youtube-{key}.{lang}.txt"
    missing = [str(p) for p in {**move, **copy}.values() if not p.is_file()]
    if missing:
        raise SystemExit("missing:\n  " + "\n  ".join(missing))
    SHORTS_DEST.mkdir(parents=True, exist_ok=True)
    for name, p in move.items():
        before = md5(p)
        shutil.move(str(p), SHORTS_DEST / name)
        assert md5(SHORTS_DEST / name) == before, name
    for name, p in copy.items():
        shutil.copy2(p, SHORTS_DEST / name)
    for p in sorted(SHORTS_DEST.iterdir()):
        print(f"{p.stat().st_size / 1e6:9.1f} MB  {p.name}")
    print(SHORTS_DEST)


if __name__ == "__main__" and "--shorts" in sys.argv:
    shorts()
