"""Check the finished films, render the covers and write the upload texts for 「二阶魔方怎么还原？」 (CUBE-2X2.md §6).
Never uploads, and moves nothing out of the repo: everything lands in out/cube-2x2/delivery/.

    python3 scripts/cube-2x2/package.py [zh|en] [--no-covers]

For each film (out/cube-2x2/delivery/cube-2x2.LANG.mp4) it runs Fun Informatics 3's checks: no black frames,
-16 LUFS within 0.5 dB, true peak at or under -1.0 dBTP, length matching the timeline. Its report goes to
out/cube-2x2/delivery-check.LANG.json. The cover is a Remotion still (Cube2x2CoverZh / Cube2x2CoverEn, one
language each: README "YouTube covers"), scaled to 1280×720. The upload text has the title, the description with
chapters and credits, the tags and the upload settings (README "YouTube tags"): upload.LANG.txt.
"""
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PUB = ROOT / "public/cube-2x2"
OUT = ROOT / "out/cube-2x2"
DELIVERY = OUT / "delivery"
sys.path.insert(0, str(ROOT / "scripts"))
from youtube_tags import hashtags, tags  # noqa: E402

spec = importlib.util.spec_from_file_location("fi03_package", ROOT / "scripts/fun-informatics-03/package.py")
fi03 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fi03)

TITLE = {"zh": "二阶魔方怎么还原？", "en": "How Do You Solve a 2×2 Cube?"}
TOPICS = {"zh": ["魔方", "二阶魔方", "魔方教程", "puzzle", "rubikscube", "2x2"],
          "en": ["rubikscube", "2x2", "cubing", "puzzle", "howtosolve", "algorithms"]}
CHAPTERS = {
    "zh": {"cb00": "只有八块", "cb01": "先认识它：颜色和字母", "cb02": "第一步：白色的一层", "cb03": "第二步：顶面全黄",
           "cb04": "第三步：换好四个角", "cb05": "再看一遍", "cb06": "最后一个问题"},
    "en": {"cb00": "Only eight pieces", "cb01": "Meet the cube: colours and letters", "cb02": "Step one: the white layer",
           "cb03": "Step two: a yellow top", "cb04": "Step three: the last corners", "cb05": "Once more", "cb06": "One last question"},
}
MUSIC = """W. A. Mozart, 12 Variations on "Ah vous dirai-je, Maman", K. 265 — Simone Renzi, piano. CC BY 3.0.
https://commons.wikimedia.org/wiki/File:Mozart_-_12_Variations_K._265_-_Simone_Renzi.mp3
https://creativecommons.org/licenses/by/3.0/"""


def check(lang):
    """Fun Informatics 3's delivery check (package.py), on this film."""
    tl = json.loads((PUB / f"timeline.{lang}.json").read_text())
    film = DELIVERY / f"cube-2x2.{lang}.mp4"
    assert not tl["draft"], "the timeline still has estimated lines"
    probe = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type,width,height,r_frame_rate",
                                       "-of", "json", str(film)], capture_output=True, text=True, check=True).stdout)
    video = next(s for s in probe["streams"] if s["codec_type"] == "video")
    duration = float(probe["format"]["duration"])
    black = subprocess.run(["ffmpeg", "-v", "info", "-i", str(film), "-vf", "blackdetect=d=0.05:pix_th=0.06", "-an", "-f", "null", "-"],
                           capture_output=True, text=True).stderr.count("black_start")
    ebu = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(film), "-vn", "-af", "ebur128=peak=true", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    lufs = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", ebu)[-1])
    peak = float(re.findall(r"Peak:\s+(-?[\d.]+) dBFS", ebu)[-1])
    report = {"film": film.name, "sha256": fi03.sha(film), "bytes": film.stat().st_size, "width": video["width"], "height": video["height"],
              "fps": video["r_frame_rate"], "seconds": round(duration, 3), "timelineSeconds": tl["durationSeconds"],
              "blackFrames": black, "lufs": lufs, "truePeakDbtp": peak}
    problems = []
    if (video["width"], video["height"]) != (1920, 1080):
        problems.append("not 1920x1080")
    if abs(duration - tl["durationSeconds"]) > 0.2:
        problems.append(f"length {duration:.2f}s against the timeline's {tl['durationSeconds']:.2f}s")
    if black:
        problems.append(f"{black} black stretches")
    if abs(lufs + 16) > 0.5:
        problems.append(f"{lufs} LUFS")
    if peak > -1.0:
        problems.append(f"true peak {peak} dBTP")
    report["problems"] = problems
    (OUT / f"delivery-check.{lang}.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(lang, json.dumps({k: report[k] for k in ("seconds", "blackFrames", "lufs", "truePeakDbtp", "problems")}, ensure_ascii=False))
    assert not problems, problems
    return tl, report


def chapters(tl, lang):
    lines = []
    for prefix, title in CHAPTERS[lang].items():
        cue = next(c for c in tl["cues"] if c["id"].startswith(prefix))
        lines.append(f"{'00:00' if prefix == 'cb00' else fi03.stamp(cue['start'])} {title}")
    return "\n".join(lines)


def text(lang, tl, report):
    ending = next(c for c in tl["cues"] if c["id"] == "cb06-01")[lang]
    if lang == "zh":
        description = f"""二阶魔方只有八块，却能打乱成三百六十七万多种样子。每一种都能还原吗？能！
这一集用初学者的方法，三步还原二阶魔方：白色的一层（一个小动作 R U R′ U′）、顶面全黄（小鱼公式 R U R′ U R U2 R′）、换好四个角（R′ F R′ B2 R F′ R′ B2 R2）。

作者 Lucas Academy Team
中文配音为 AI 合成，使用 Louise 的授权声线。画面全部来自 Lucas Academy 的网页魔方：
https://is.lucasacademy.org/cube/ 打开「Solve it for me」，它会一步一步还原给你看，从二阶到十一阶都可以。

{chapters(tl, "zh")}

背景音乐：{MUSIC}
本片对录音做了选段、拼接、交叉淡化和音量调整。

{ending}

{hashtags(TOPICS["zh"])}
"""
        head = f"{TITLE['zh']}｜三步还原，只用两个公式"
        settings = f"""· 视频：cube-2x2.zh.mp4（1920×1080，30 fps，{fi03.stamp(round(report['seconds']))}，{report['lufs']:.0f} LUFS）
· 字幕：cube-2x2.zh.zh-Hans.srt、cube-2x2.zh.en.srt
· 缩略图：cover.zh.jpg（1280×720）
· 视频语言：中文（简体）
· 观众：由作者选择
· 修改过或合成的内容：是（合成配音）
· 类别：教育"""
        labels = ("【标题 / Title】", "【简介 / Description】", "【标签 / Tags】", "【上传设置 / Upload settings】")
    else:
        description = f"""A 2×2 cube has only eight pieces, yet it can be scrambled more than three and a half million ways. Can every one be solved? Yes!
This film solves it the beginner's way, in three steps: the white layer (one little move, R U R′ U′), a yellow top (Sune, R U R′ U R U2 R′) and the last corners (R′ F R′ B2 R F′ R′ B2 R2).

By Lucas Academy Team
The narration is AI-generated with Louise's licensed voice. Every picture comes from Lucas Academy's web cube:
https://is.lucasacademy.org/cube/ Press "Solve it for me" and it solves any cube from 2×2 to 11×11, step by step.

{chapters(tl, "en")}

Music: {MUSIC}
The recording was excerpted, joined, crossfaded and levelled for this film.

{ending}

{hashtags(TOPICS["en"])}
"""
        head = f"{TITLE['en']} Three Steps, Two Algorithms"
        settings = f"""· Video: cube-2x2.en.mp4 (1920×1080, 30 fps, {fi03.stamp(round(report['seconds']))}, {report['lufs']:.0f} LUFS)
· Captions: cube-2x2.en.en.srt, cube-2x2.en.zh-Hans.srt
· Thumbnail: cover.en.jpg (1280×720)
· Video language: English
· Audience: the author's choice
· Altered or synthetic content: yes (synthetic narration)
· Category: Education"""
        labels = ("【标题 / Title】", "【简介 / Description】", "【标签 / Tags】", "【上传设置 / Upload settings】")
    assert len(description) <= 5000, len(description)
    return f"""{labels[0]}
{head}

{labels[1]}（{len(description)}）
{description}
{labels[2]}
{tags(TOPICS[lang])}

{labels[3]}
{settings}
"""


def cover(lang):
    png = DELIVERY / f"cover.{lang}.png"
    comp = "Cube2x2CoverZh" if lang == "zh" else "Cube2x2CoverEn"
    subprocess.run(["npx", "remotion", "still", "src/index.ts", comp, str(png), "--log=error"], cwd=ROOT, check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(png), "-vf", "scale=1280:720", "-q:v", "2", str(png.with_suffix(".jpg"))], check=True)
    png.unlink()


if __name__ == "__main__":
    langs = [a for a in sys.argv[1:] if a in ("zh", "en")] or ["zh", "en"]
    DELIVERY.mkdir(parents=True, exist_ok=True)
    for lang in langs:
        tl, report = check(lang)
        (DELIVERY / f"upload.{lang}.txt").write_text(text(lang, tl, report))
        if "--no-covers" not in sys.argv:
            cover(lang)
        print(f"{lang}: upload.{lang}.txt" + ("" if "--no-covers" in sys.argv else f", cover.{lang}.jpg"))
