"""The upload text rules: a description made by scripts/youtube_text.py passes; each broken one is caught.

    python3 scripts/qa/tests/test_upload.py
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parents[1]))
import upload  # noqa: E402
from youtube_text import upload_text  # noqa: E402

CHAPTERS = [(0, "开场：大脑里也有开关吗？"), (45.2, "一碟绿水"), (103.0, "开关和比特"), (190.0, "编码和解码")]
GOOD = upload_text(title="诺贝尔奖：光遗传学是什么？｜趣味信息学4", chapters=CHAPTERS, duration=560.0,
                   body=["你有没有想过：要是大脑里也有开关，按一下，会发生什么？", "作者：Yancy Qin | Lucas Academy"],
                   own_tags=["趣味信息学", "光遗传学"], more_tags=["optogenetics"],
                   settings=["视频语言：中文（简体）", "类别：教育"])


def codes(text: str, duration=560.0, short=False) -> set[str]:
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "youtube-description.zh.txt"
        p.write_text(text, encoding="utf-8")
        return {f["code"] for f in upload.check_description(p, duration, short)}


def main() -> int:
    cases = [
        ("made by youtube_text", GOOD, set()),
        ("intro before the chapters", GOOD.replace("0:00 开场", "你好！\n\n0:00 开场", 1), {"upload.chapters_first"}),
        ("no chapters at all", "\n".join(r for r in GOOD.splitlines() if not upload.CHAPTER.match(r)),
         {"upload.chapters_first"}),
        ("a chapter under 10 s", GOOD.replace("0:45 一碟绿水", "0:05 一碟绿水"), {"upload.chapters_short"}),
        ("only two chapters", GOOD.replace("3:10 编码和解码\n", "").replace("1:43 开关和比特\n", ""),
         {"upload.chapters_count"}),
        ("no 【标签】", GOOD.split("【标签")[0] + "【上传设置 / Upload settings】\n· x\n", {"upload.section.标签"}),
        ("tags with commas", GOOD.replace("#趣味信息学 #光遗传学", "趣味信息学, 光遗传学"), {"upload.tags_format"}),
        ("a default tag missing", GOOD.replace(" #stem", "", 2), {"upload.tags_defaults"}),
        ("uppercase hashtag", GOOD.replace("#optogenetics", "#Optogenetics"), {"upload.tags_case"}),
        ("hashtag line not last", GOOD.replace("#education #parenting #art", "#趣味信息学 #education #parenting #art", 1),
         {"upload.hashtags_head"}),
        ("angle brackets", GOOD.replace("会发生什么？", "会发生什么？<br>"), {"upload.desc_brackets"}),
    ]
    ok_all = True
    for name, text, want in cases:
        got = codes(text)
        ok = (got == want) if not want else want <= got
        ok_all &= ok
        print(f"{'PASS' if ok else 'MISS'}  {name:<28} expected {sorted(want) or 'nothing'} | got {sorted(got) or 'nothing'}")
    for bad in ([(0, "a"), (5, "b"), (30, "c")], [(0, "a"), (20, "b")]):
        try:
            upload_text(title="t", chapters=bad, duration=100, body=[], own_tags=[])
            print(f"MISS  youtube_text accepted bad chapters {bad}")
            ok_all = False
        except ValueError as e:
            print(f"PASS  youtube_text refuses {bad}: {e}")
    ok_all &= folder_case()
    return 0 if ok_all else 1


def folder_case() -> bool:
    """A whole package that must pass: a 40-s film checked by qa.py (no 拿不准), a youtube_text description, a
    1280×720 cover. Needs ffmpeg and the QA environment (numpy); skipped without them."""
    import subprocess
    try:
        import numpy  # noqa: F401
    except ImportError:
        print("SKIP  folder case (run with .venv-align/bin/python)")
        return True
    sys.path.insert(0, str(HERE.parent))
    import qa
    from common import OUT
    work = OUT / "_upload_case"
    work.mkdir(parents=True, exist_ok=True)
    film = work / "film.mp4"
    if not film.exists():
        still = work / "still.png"   # a still picture (a painting holds still; animated test sources read as motion)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc2=s=1920x1080", "-frames:v", "1",
                        str(still)], check=True)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-framerate", "30", "-t", "40", "-i", str(still),
                        "-f", "lavfi", "-i", "sine=frequency=330:sample_rate=48000:duration=40",
                        "-af", "volume=-12dB,aformat=channel_layouts=stereo,loudnorm=I=-18:TP=-2",
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-ar", "48000", "-shortest", str(film)],
                       check=True)
    spec = work / "qa-spec.json"
    spec.write_text('{"film": "_upload_case", "kind": "music", "music": false, "lines": [],'
                    ' "format": {"duration": 40.0, "tol": 0.2}}', encoding="utf-8")
    rc = subprocess.run([sys.executable, str(HERE.parent / "qa.py"), "check", str(film), "--spec", str(spec),
                         "--out", str(work)], capture_output=True, text=True)
    with tempfile.TemporaryDirectory() as td:
        pkg = Path(td) / "测试片-上传"
        pkg.mkdir()
        (pkg / "测试片.mp4").write_bytes(film.read_bytes())
        (pkg / "youtube-description.txt").write_text(upload_text(
            title="测试片", chapters=[(0, "开头"), (10, "中间"), (20, "后来"), (30, "结尾")], duration=40.0,
            body=["一段测试。"], own_tags=["测试"], settings=["类别：教育"]), encoding="utf-8")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=c=navy:s=1280x720", "-frames:v", "1",
                        str(pkg / "youtube-cover.jpg")], check=True)
        info, found = upload.check_folder(pkg, qa.require)
    ok = rc.returncode == 0 and not found
    print(f"{'PASS' if ok else 'MISS'}  a complete package passes   check exit {rc.returncode}"
          + ("" if ok else f" | {rc.stdout[-600:]} | {[f['title'] for f in found]}"))
    return ok


if __name__ == "__main__":
    sys.exit(main())
