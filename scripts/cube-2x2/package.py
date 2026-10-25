"""Check the finished film, render the cover and write the upload text for "How Do You Solve a 2×2 Cube?"
(CUBE-2X2.md §6). Never uploads, and moves nothing out of the repo: everything lands in out/cube-2x2/delivery/.

    python3 scripts/cube-2x2/package.py [--no-cover]

The film (cube-2x2.mp4: English first, the Chinese track as a second audio stream) gets Fun Informatics 3's
checks: no black frames, -16 LUFS within 0.5 dB, true peak at or under -1.0 dBTP, length matching the
timeline; the Chinese track (cube-2x2.zh-track.wav, for YouTube Studio's "Add audio track") gets the same
loudness checks and must match the film's length. Report: out/cube-2x2/delivery-check.json. The cover is the
Remotion still Cube2x2Cover (the question in English, Chinese small under it), scaled to 1280×720. upload.txt
has the English title and description, the Chinese ones for YouTube's translations, the tags and the settings.
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

TITLE = {"en": "How Do You Solve a 2×2 Cube?", "zh": "二阶魔方怎么还原？"}
TOPICS = ["rubikscube", "2x2", "cubing", "puzzle", "howtosolve", "魔方"]
CHAPTERS = {
    "en": {"cb00": "Only eight pieces", "cb01": "Meet the cube: colours and letters", "cb02": "Part 1: the first layer",
           "cb03": "Part 2: the top layer, step 1: a yellow top", "cb04": "Part 2, step 2: the corners", "cb05": "Once more",
           "cb06": "Practise online, and one last question"},
    "zh": {"cb00": "只有八块", "cb01": "先认识它：颜色和字母", "cb02": "第一部分：拼第一层", "cb03": "第二部分：拼顶层，第一步：顶面全黄",
           "cb04": "第二部分，第二步：换好四个角", "cb05": "再看一遍", "cb06": "在网上练，和最后一个问题"},
}
MUSIC = """W. A. Mozart, 12 Variations on "Ah vous dirai-je, Maman", K. 265 — Simone Renzi, piano. CC BY 3.0.
https://commons.wikimedia.org/wiki/File:Mozart_-_12_Variations_K._265_-_Simone_Renzi.mp3
https://creativecommons.org/licenses/by/3.0/"""


def loudness(path, stream="a:0"):
    ebu = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(path), "-map", f"0:{stream}", "-af", "ebur128=peak=true", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    return float(re.findall(r"I:\s+(-?[\d.]+) LUFS", ebu)[-1]), float(re.findall(r"Peak:\s+(-?[\d.]+) dBFS", ebu)[-1])


def check():
    """Fun Informatics 3's delivery check (package.py), on this film and on its Chinese track."""
    tl = json.loads((PUB / "timeline.json").read_text())
    film = DELIVERY / "cube-2x2.mp4"
    track = DELIVERY / "cube-2x2.zh-track.wav"
    assert not tl["draft"], "the timeline still has estimated lines"
    probe = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type,width,height,r_frame_rate:stream_tags=language",
                                       "-of", "json", str(film)], capture_output=True, text=True, check=True).stdout)
    video = next(s for s in probe["streams"] if s["codec_type"] == "video")
    audio = [s.get("tags", {}).get("language") for s in probe["streams"] if s["codec_type"] == "audio"]
    duration = float(probe["format"]["duration"])
    track_seconds = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(track)],
                                         capture_output=True, text=True, check=True).stdout)
    black = subprocess.run(["ffmpeg", "-v", "info", "-i", str(film), "-vf", "blackdetect=d=0.05:pix_th=0.06", "-an", "-f", "null", "-"],
                           capture_output=True, text=True).stderr.count("black_start")
    lufs, peak = loudness(film, "a:0")
    zh_lufs, zh_peak = loudness(film, "a:1")
    report = {"film": film.name, "sha256": fi03.sha(film), "bytes": film.stat().st_size, "width": video["width"], "height": video["height"],
              "fps": video["r_frame_rate"], "seconds": round(duration, 3), "timelineSeconds": tl["durationSeconds"], "audio": audio,
              "blackFrames": black, "lufs": {"en": lufs, "zh": zh_lufs}, "truePeakDbtp": {"en": peak, "zh": zh_peak},
              "zhTrack": {"file": track.name, "sha256": fi03.sha(track), "seconds": round(track_seconds, 3)}}
    problems = []
    if (video["width"], video["height"]) != (1920, 1080):
        problems.append("not 1920x1080")
    if abs(duration - tl["durationSeconds"]) > 0.2:
        problems.append(f"length {duration:.2f}s against the timeline's {tl['durationSeconds']:.2f}s")
    if abs(track_seconds - duration) > 0.2:
        problems.append(f"Chinese track {track_seconds:.2f}s against the film's {duration:.2f}s")
    if audio != ["eng", "chi"]:
        problems.append(f"audio streams {audio}, not English then Chinese")
    if black:
        problems.append(f"{black} black stretches")
    for lang, value in (("en", lufs), ("zh", zh_lufs)):
        if abs(value + 16) > 0.5:
            problems.append(f"{lang}: {value} LUFS")
    for lang, value in (("en", peak), ("zh", zh_peak)):
        if value > -1.0:
            problems.append(f"{lang}: true peak {value} dBTP")
    report["problems"] = problems
    (OUT / "delivery-check.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: report[k] for k in ("seconds", "audio", "blackFrames", "lufs", "truePeakDbtp", "problems")}, ensure_ascii=False))
    assert not problems, problems
    return tl, report


def chapters(tl, lang):
    lines = []
    for prefix, title in CHAPTERS[lang].items():
        cue = next(c for c in tl["cues"] if c["id"].startswith(prefix))
        lines.append(f"{'00:00' if prefix == 'cb00' else fi03.stamp(cue['start'])} {title}")
    return "\n".join(lines)


def text(tl, report):
    ending = {lang: next(c for c in tl["cues"] if c["id"] == "cb06-02")[lang] for lang in ("en", "zh")}
    en = f"""A 2×2 cube has only eight pieces, yet it can be scrambled more than three and a half million ways. Can every one be solved? Yes!
This film solves it the beginner's way, in two parts: the first layer (one little move, R U R′ U′), then the top layer: a yellow top (Sune, R U R′ U R U2 R′) and the last corners (R′ F R′ B2 R F′ R′ B2 R2). Every move gets a card on screen, every time it is used.

No cube? Practise online: https://is.lucasacademy.org/cube/ — turn it, scramble it, and press "Solve it for me" to be walked through every step, on any cube from 2×2 to 11×11.

中文配音：在音轨设置里选「中文」。

By Lucas Academy Team
The narration is AI-generated with Louise's licensed voices (English, and a Chinese audio track). Every picture comes from Lucas Academy's web cube.

{chapters(tl, "en")}

Music: {MUSIC}
The recording was excerpted, joined, crossfaded and levelled for this film.

{ending["en"]}

{hashtags(TOPICS)}
"""
    zh = f"""二阶魔方只有八块，却能打乱成三百六十七万多种样子。每一种都能还原吗？能！
这一集用初学者的方法，分两部分还原：先拼第一层（一个小动作 R U R′ U′），再拼顶层：顶面全黄（小鱼公式 R U R′ U R U2 R′）、换好四个角（R′ F R′ B2 R F′ R′ B2 R2）。每用到一个转动，屏幕上都有它的卡片。

没有魔方？在网上也能练：https://is.lucasacademy.org/cube/ 点「Solve it for me」，它会一步一步带你还原，二阶到十一阶都可以。

作者 Lucas Academy Team
配音为 AI 合成，使用 Louise 的授权声线（英文原声，另有中文音轨）。

{chapters(tl, "zh")}

背景音乐：{MUSIC}

{ending["zh"]}
"""
    assert len(en) <= 5000 and len(zh) <= 5000
    return f"""【标题 / Title】
{TITLE['en']} Two Parts, Two Algorithms

【简介 / Description】（{len(en)}）
{en}
【中文标题和简介 / Chinese title and description】（YouTube Studio → 语言 / Languages → 添加翻译）
{TITLE['zh']}｜两部分还原，只用两个公式

{zh}
【标签 / Tags】
{tags(TOPICS)}

【上传设置 / Upload settings】
· Video: cube-2x2.mp4 (1920×1080, 30 fps, {fi03.stamp(round(report['seconds']))}; its first audio stream is English, {report['lufs']['en']:.0f} LUFS)
· Chinese audio track: cube-2x2.zh-track.wav (same length; Studio → Languages → Add audio track → 中文 / Chinese)
· Captions: cube-2x2.en.srt (English), cube-2x2.zh-Hans.srt (中文)
· Thumbnail: cover.jpg (1280×720)
· Video language: English
· Audience: the author's choice
· Altered or synthetic content: yes (synthetic narration)
· Category: Education
"""


def cover():
    png = DELIVERY / "cover.png"
    subprocess.run(["npx", "remotion", "still", "src/index.ts", "Cube2x2Cover", str(png), "--log=error"], cwd=ROOT, check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(png), "-vf", "scale=1280:720", "-q:v", "2", str(png.with_suffix(".jpg"))], check=True)
    png.unlink()


if __name__ == "__main__":
    DELIVERY.mkdir(parents=True, exist_ok=True)
    tl, report = check()
    (DELIVERY / "upload.txt").write_text(text(tl, report))
    if "--no-cover" not in sys.argv:
        cover()
    print("upload.txt" + ("" if "--no-cover" in sys.argv else ", cover.jpg"))
