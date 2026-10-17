"""Check the finished films and fill the Desktop upload folder (FUN-INFORMATICS-03.md §5.6). Never uploads.

    python3 scripts/fun-informatics-03/package.py [--check-only | --replace]

--replace swaps new renders of the films (and their regenerated upload texts) into an existing upload folder; the
versions they replace go to the Trash, where the owner can still restore them.

For each film in out/fun-informatics-03/delivery/fun-informatics-03.{zh,en}.mp4 it checks the picture and sound
(no black frames, -16 LUFS within 0.5 dB, true peak at or under -1.0 dBTP, length matching the timeline) and records
the result in out/fun-informatics-03/delivery-check.LANG.json. Then it writes each film's upload text (title,
description with chapters, tags, upload settings; README "YouTube tags") and moves the upload files into one new
Desktop folder, 「报数为什么说幺-上传」: the films, their captions, covers and texts, nothing else. The files are
moved, not copied, so only one copy exists; each moved file is checked against its recorded sha256.
"""
import hashlib
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PUB = ROOT / "public/fun-informatics-03"
OUT = ROOT / "out/fun-informatics-03"
DELIVERY = OUT / "delivery"
DEST = Path.home() / "Desktop/报数为什么说幺-上传"
sys.path.insert(0, str(ROOT / "scripts"))
from youtube_tags import hashtags, tags  # noqa: E402

NAME = "报数为什么说幺"
TOPICS = {"zh": ["趣味信息学", "信息论", "噪声", "冗余", "你画我猜", "香农"],
          "en": ["FunInformatics", "InformationTheory", "Noise", "Redundancy", "Pictionary", "Shannon"]}
CHAPTERS = {
    "zh": {"ns00": "报数为什么说「幺」？", "ns01": "一，还是七？", "ns02": "你画我猜", "ns03": "噪声、冗余和一个问题"},
    "en": {"ns00": "Why do pilots say Bravo?", "ns01": "B, or D?", "ns02": "Pictionary", "ns03": "Noise, redundancy and a question"},
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stamp(seconds):
    m, s = divmod(int(seconds), 60)
    return f"{m:02d}:{s:02d}"


def check(lang):
    tl = json.loads((PUB / f"timeline.{lang}.json").read_text())
    film = DELIVERY / f"fun-informatics-03.{lang}.mp4"
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
    report = {"film": film.name, "sha256": sha(film), "bytes": film.stat().st_size, "width": video["width"], "height": video["height"],
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
        lines.append(f"{'00:00' if prefix == 'ns00' else stamp(cue['start'])} {title}")
    return "\n".join(lines)


def text_zh(tl, report):
    description = f"""一和七，在对讲机里为什么容易听混？报警电话 110，为什么常常念成「幺幺零」？
这一集跟噪声过过招，学会对付它的第一招：把容易听混的，说得不一样。再和家人、朋友玩两轮你画我猜，看看画画里的噪声和冗余。

趣味信息学第三集。上一集《你认识 Claude 吗？》讲了冗余：你能猜到的那部分。

作者 Yancy Qin, Louise Yang | Lucas Academy
文案与 Claude 合作完成；中文配音为 AI 合成，使用 Louise 的授权声线。

{chapters(tl, "zh")}

对讲机试听的两个字从旁白录音里截出，加上对讲机的音色和静电噪声。
你画我猜是家人和朋友的真实录像，做了防抖、调色和背景虚化，只保留猜中那一刻的原声。插图由 AI 生成，已在画面标识。

背景音乐是莫扎特的《小星星变奏曲》：同一个旋律加了十二种花样，你还是一下就认得出来，这也是一种不怕噪声的冗余。
音乐：W. A. Mozart, 12 Variations on "Ah vous dirai-je, Maman", K. 265。
钢琴及录音：Simone Renzi。录音许可：CC BY 3.0。
https://commons.wikimedia.org/wiki/File:Mozart_-_12_Variations_K._265_-_Simone_Renzi.mp3
https://creativecommons.org/licenses/by/3.0/
本片对录音做了选段、拼接、交叉淡化和音量调整。

延伸阅读：Claude E. Shannon, A Mathematical Theory of Communication（1948）。

生活里也有噪声：吵闹的教室、着急的时候、生气的时候。你有没有一句话，特别怕别人听错？你会怎么说，让它好好地传到对方那里？
这是我们在 Lucas Academy 一起学习、一起思考的问题。

{hashtags(TOPICS["zh"])}
"""
    assert len(description) <= 5000, len(description)
    return f"""【标题 / Title】
报数为什么说「幺」？｜趣味信息学3 Fun Informatics 3

【简介 / Description】（可直接粘贴，{len(description)} 字符）
{description}
【标签 / Tags】
{tags(TOPICS["zh"])}

【上传设置 / Upload settings】
· 视频：{NAME}-中文版.mp4（1920×1080，30 fps，{stamp(round(report['seconds']))}，{report['lufs']:.0f} LUFS）
· 字幕：{NAME}-中文字幕.srt、{NAME}-English.srt（英文字幕翻译的是这部中文片的台词）
· 缩略图：{NAME}-封面.jpg（1280×720）
· 视频语言：中文（简体）
· 观众：由作者选择
· 修改过或合成的内容：是（合成配音；AI 配图）
· 类别：教育
"""


def text_en(tl, report):
    description = f"""Why do “B” and “D” get mixed up on a crackly radio? Why do pilots say “Bravo” instead of “B”?
In this episode we take on noise and learn the first trick for beating it: if two things sound alike, say them differently. Then we play two rounds of Pictionary with family and friends, to find the noise, and the redundancy, in drawings.

Fun Informatics, episode 3. Last time, “Do You Know Claude?” was about redundancy: the part you can predict.

By Yancy Qin, Louise Yang | Lucas Academy
Script developed with Claude. English narration uses Louise’s authorised AI-cloned voice.

{chapters(tl, "en")}

The radio-test letters are cut from the narration and given a walkie-talkie sound with static.
The Pictionary clips are real footage of family and friends, steadied, colour-corrected and with the background blurred; only the moments of the right guesses keep their original sound. Illustrations are AI-generated and labelled on screen.

The music is Mozart’s Twinkle Variations: one tune dressed up twelve different ways, and you still recognise it at once. That is redundancy holding up against noise, too.
Music: W. A. Mozart, 12 Variations on “Ah vous dirai-je, Maman” (Twinkle, Twinkle, Little Star), K. 265.
Piano and recording: Simone Renzi, licensed under CC BY 3.0.
https://commons.wikimedia.org/wiki/File:Mozart_-_12_Variations_K._265_-_Simone_Renzi.mp3
https://creativecommons.org/licenses/by/3.0/
Modifications: excerpts, joins, crossfades and volume changes.

Further reading: Claude E. Shannon, A Mathematical Theory of Communication (1948).

There’s noise in everyday life too: a loud classroom, being in a hurry, being upset. Is there something you’d really hate to be misheard? How would you say it so it gets through? We learn and think about these questions together at Lucas Academy.

{hashtags(TOPICS["en"])}
"""
    assert len(description) <= 5000, len(description)
    return f"""Title
Why Do Pilots Say “Bravo”? | Fun Informatics 3

Description ({len(description)} characters)
{description}
Tags
{tags(TOPICS["en"])}

Upload settings
Video: {NAME}-英文版.mp4, 1920×1080, 30 fps, {stamp(round(report['seconds']))}, {report['lufs']:.0f} LUFS
Captions: {NAME}-英文版-English.srt and {NAME}-英文版-中文字幕.srt (the Chinese captions translate this English film)
Thumbnail: {NAME}-英文封面.jpg (1280×720)
Video language: English
Altered or synthetic content: Yes (AI-cloned narration; AI-generated illustrations)
Category: Education
Audience: selected by the author
"""


def replace(results):
    """Swap the new films and texts into DEST; the old ones go to the Trash. Captions and covers stay as they are."""
    swaps = {
        "fun-informatics-03.zh.mp4": f"{NAME}-中文版.mp4", "upload.zh.txt": f"{NAME}-上传描述.txt",
        "fun-informatics-03.en.mp4": f"{NAME}-英文版.mp4", "upload.en.txt": f"{NAME}-英文上传描述.txt",
    }
    assert all((DELIVERY / k).is_file() for k in swaps) and all((DEST / v).is_file() for v in swaps.values())
    trash = Path.home() / ".Trash" / f"{NAME}-上传-旧版-{datetime.now():%Y%m%d-%H%M%S}"
    trash.mkdir(parents=True)
    manifest = {m["file"]: m for m in json.loads((OUT / "package-manifest.json").read_text())["files"]}
    for source, name in swaps.items():
        shutil.move(str(DEST / name), str(trash / name))
        digest = sha(DELIVERY / source)
        shutil.move(str(DELIVERY / source), str(DEST / name))
        assert sha(DEST / name) == digest, name
        manifest[name] = {"file": name, "sha256": digest, "bytes": (DEST / name).stat().st_size}
    for name, m in manifest.items():  # captions and covers did not move: they must still match
        assert sha(DEST / name) == m["sha256"], name
    (OUT / "package-manifest.json").write_text(json.dumps({"destination": str(DEST), "files": list(manifest.values())}, ensure_ascii=False, indent=2) + "\n")
    print(f"replaced {len(swaps)} files in {DEST}; the old ones are in {trash}")


def main():
    results = {lang: check(lang) for lang in ("zh", "en")}
    if "--check-only" in sys.argv:
        return
    if "--replace" in sys.argv:
        (DELIVERY / "upload.zh.txt").write_text(text_zh(*results["zh"]), encoding="utf-8")
        (DELIVERY / "upload.en.txt").write_text(text_en(*results["en"]), encoding="utf-8")
        return replace(results)
    (DELIVERY / "upload.zh.txt").write_text(text_zh(*results["zh"]), encoding="utf-8")
    (DELIVERY / "upload.en.txt").write_text(text_en(*results["en"]), encoding="utf-8")
    files = {
        "fun-informatics-03.zh.mp4": f"{NAME}-中文版.mp4",
        "fun-informatics-03.zh.zh-Hans.srt": f"{NAME}-中文字幕.srt",
        "fun-informatics-03.zh.en.srt": f"{NAME}-English.srt",
        "cover.zh.jpg": f"{NAME}-封面.jpg",
        "upload.zh.txt": f"{NAME}-上传描述.txt",
        "fun-informatics-03.en.mp4": f"{NAME}-英文版.mp4",
        "fun-informatics-03.en.en.srt": f"{NAME}-英文版-English.srt",
        "fun-informatics-03.en.zh-Hans.srt": f"{NAME}-英文版-中文字幕.srt",
        "cover.en.jpg": f"{NAME}-英文封面.jpg",
        "upload.en.txt": f"{NAME}-英文上传描述.txt",
    }
    sources = {DELIVERY / k: v for k, v in files.items()}
    missing = [p.name for p in sources if not p.is_file()]
    assert not missing, missing
    assert not DEST.exists() or not any(DEST.iterdir()), f"{DEST} already has files; empty it or pick a new name first"
    DEST.mkdir(parents=True, exist_ok=True)
    manifest = []
    for source, name in sources.items():
        digest = sha(source)
        target = DEST / name
        shutil.move(str(source), str(target))
        assert sha(target) == digest, name
        manifest.append({"file": name, "sha256": digest, "bytes": target.stat().st_size})
    (OUT / "package-manifest.json").write_text(json.dumps({"destination": str(DEST), "files": manifest}, ensure_ascii=False, indent=2) + "\n")
    for m in manifest:
        print(f"  {m['file']}  {m['bytes'] / 1e6:.1f} MB")
    print(f"-> {DEST}")


if __name__ == "__main__":
    main()
