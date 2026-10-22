"""Check and package 「法国人走上街头，出路在哪里？」 for upload: one Desktop folder with only what goes to YouTube.

  python3 scripts/news-education-01/package.py [--check-only]

The film has two audio tracks (owner, 2026-10-20): Chinese is the video's own track, English goes up in Studio as an
added audio track (the en-audio WAV); both caption files go up too. The description is written in Chinese with an
English translation for Studio's "add language". Credits come from the sources files next to the footage and art.
"""
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FILM = "news-education-01"
PUB = ROOT / "public" / FILM
OUT = ROOT / "out" / FILM
DELIVERY = OUT / "delivery"
NAME = "法国人走上街头出路在哪里"
DEST = Path.home() / "Desktop" / f"{NAME}-上传"
sys.path.insert(0, str(ROOT / "scripts"))
from youtube_tags import hashtags, tags  # noqa: E402

TITLE = {"zh": "法国人走上街头，出路在哪里？｜从新闻看教育",
         "en": "The French Take to the Streets. Where Is the Way Out? | Lessons from the Headlines"}
TOPICS = ["france", "protest", "genz", "criticalliteracy", "constitution", "nonviolence"]
CHAPTERS = [("sc00", "法国，这个月", "France, this month"), ("sc01", "不只是法国", "Not only France"),
            ("sc02", "方案一大堆", "A pile of solutions"), ("sc03", "每一方都有理", "Every side has a point"),
            ("sc04", "限制权力的权力", "Power that limits power"), ("sc05", "清教徒", "The Puritans"),
            ("sc06", "圣经", "The Bible"), ("sc07", "甘地和金", "Gandhi and King"), ("sc08", "教室", "The classroom"),
            ("sc09", "滑雪场", "On the ski slope"), ("sc10", "护住这份善意", "Protecting kindness"),
            ("sc11", "结尾的问题", "The question")]


def stamp(t: float) -> str:
    t = int(t)
    return f"{t // 60:02d}:{t % 60:02d}" if t < 3600 else f"{t // 3600}:{t // 60 % 60:02d}:{t % 60:02d}"


def credits(lang: str) -> str:
    rows = [r.split("\t") for r in (PUB / "footage/list.tsv").read_text().splitlines() if r.strip()]
    pexels = sorted({r[3] for r in rows})
    art = json.loads((PUB / "art/sources.json").read_text())
    licensed = [f"· {a['title'][5:]} — {re.sub(r'\s+', ' ', a['artist'])[:60]}, {a['license']} {a['page']}" for a in art.values()
                if a["license"] not in ("Public domain", "CC0")]
    pd = [a["title"][5:].rsplit(".", 1)[0] for a in art.values() if a["license"] in ("Public domain", "CC0")]
    music = ("· J.S. Bach, Air (Orchestral Suite No. 3, BWV 1068) — U.S. Air Force Strings, public domain\n"
             "· Erik Satie, Gymnopédie No. 1 — Kevin MacLeod (incompetech.com), CC BY 3.0 https://creativecommons.org/licenses/by/3.0/\n"
             "· J.S. Bach, Jesu, Joy of Man's Desiring (BWV 147) — Orchestra Gli Armonici, CC0")
    if lang == "zh":
        return (f"视频素材：Pexels（{'、'.join(pexels)}）；滑雪画面为作者自己拍摄。\n"
                f"图片（Wikimedia Commons）：\n" + "\n".join(licensed) + f"\n其余为公有领域：{'；'.join(pd)}。\n"
                f"音乐：\n{music}\n本片对录音做了循环、淡入淡出和音量调整。\n经文：约翰福音 13:13–14、12:24，和合本。")
    return (f"Footage: Pexels ({', '.join(pexels)}); the ski runs are the author's own.\n"
            f"Images (Wikimedia Commons):\n" + "\n".join(licensed) + f"\nPublic domain: {'; '.join(pd)}.\n"
            f"Music:\n{music}\nThe recordings are looped, faded and level-adjusted in the film.\n"
            f"Scripture: John 13:13–14, 12:24, World English Bible (public domain).")


def describe(lang: str, chapters: str) -> str:
    if lang == "en":
        return f"""In October 2026, France saw its biggest riots in years. It started with a high school that had no teachers; within weeks more than a thousand high schools were caught up, schools were burned, and thousands of teenagers were detained. In the past few years young people have filled the streets from Bangladesh and Nepal to Indonesia, the Philippines and India. Protest can change who holds power. It is much harder to change how power is held.
Students have the right to protest; governments have the power to keep order. Both sides are right, and both use what they have to the limit. This episode looks for a way out that starts much earlier, at home and in the classroom: laying down the power you think you have, and caring more about the other side's rights. From Washington handing back his commission, Madison's "if men were angels", the Puritans' law that every town should teach children to read, Jesus washing his disciples' feet and the grain of wheat, to Gandhi and King, and a day on a ski slope.

By Yancy Qin | Lucas Academy
Script written with Claude; the narration is AI-voiced in Yancy's own voice. One video, two audio tracks (Chinese and English), captions in both languages.

{chapters}

Sources for the news: Wikipédia / Wikipedia (2026 French lycée movement), The Conversation (2026-08-24), Council on Foreign Relations (2025-11-20), Al Jazeera (2026-02-13), Himal Press. Figures for France as of mid-October 2026.
{credits('en')}

Next time, at home, in the classroom or in the street, when you have right on your side and strength in your hands, will you lay down just a little first? That is also the question we learn and think about together, at Lucas Academy.

{hashtags(TOPICS)}
"""
    return f"""二〇二六年十月，法国发生了近年来最大规模的骚乱。事情从一所缺老师的高中开始，几个星期里上千所高中卷了进来，学校被烧，几千个十几岁的孩子被拘留。这几年，从孟加拉、尼泊尔到印尼、菲律宾、印度，年轻人一次又一次走上街头。抗议能换掉掌权的人，却很难换掉掌权的方式。
学生有抗议的权利，政府有维持秩序的权力：两边都有理，也都把自己的用到了底。这一集想找一条更早开始的出路，从家里和教室里开始：放下自己以为的权力，更在乎对方的权利。从华盛顿交还兵权、麦迪逊的「如果人都是天使」、清教徒要每个镇都教孩子读书，到耶稣给门徒洗脚和一粒麦子，再到甘地和马丁·路德·金，还有滑雪场上的一天。

作者 Yancy Qin | Lucas Academy
文案与 Claude 合作完成；配音为 AI 合成（作者本人的音色）。一个视频，中英两条音轨，中英文字幕。

{chapters}

新闻资料：维基百科法文版和英文版（2026 年法国高中生运动）、The Conversation（2026-08-24）、美国外交关系委员会 CFR（2025-11-20）、半岛电视台（2026-02-13）、Himal Press。法国的数字截至 2026 年 10 月中旬。
{credits('zh')}

下一次，在家里、在教室里、在街上，你手里有理、也有力的时候，会先放下一点点吗？这也是我们在 Lucas Academy 一起学习、一起思考的问题。

{hashtags(TOPICS)}
"""


def probe(path: Path, *entries: str) -> str:
    return subprocess.run(["ffprobe", "-v", "error", *entries, "-of", "csv=p=0", str(path)], capture_output=True, text=True).stdout.strip()


def loudness(path: Path, stream: str) -> str:
    p = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(path), "-map", stream, "-af", "ebur128=peak=true", "-f", "null", "-"],
                       capture_output=True, text=True)
    i = re.findall(r"I:\s+(-?[\d.]+) LUFS", p.stderr)
    pk = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", p.stderr)
    return f"{i[-1]} LUFS, peak {pk[-1]} dBFS"


def main() -> None:
    tl = json.loads((PUB / "timeline.json").read_text())
    assert not tl["draft"], "draft timeline"
    film = DELIVERY / f"{FILM}.mp4"
    en_audio = DELIVERY / f"{FILM}.en-audio.wav"
    dur = float(probe(film, "-show_entries", "format=duration"))
    assert abs(dur - tl["durationSeconds"]) < 1.0, (dur, tl["durationSeconds"])
    streams = probe(film, "-show_entries", "stream=codec_type,width,height:stream_tags=language").splitlines()
    print("film", stamp(dur), streams)
    print("zh track", loudness(film, "0:a:0"), "| en track", loudness(film, "0:a:1"))
    black = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(film), "-vf", "blackdetect=d=1.0:pix_th=0.06", "-an", "-f", "null", "-"],
                           capture_output=True, text=True).stderr
    blacks = re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", black)
    print("black stretches ≥1 s:", blacks or "none")
    for name in ("zh-Hans", "en"):
        srt = (DELIVERY / f"{FILM}.{name}.srt").read_text()
        print(f"{name}.srt: {srt.count(' --> ')} captions")
    chapters = "\n".join(f"{stamp(tl['lines'][f'{p}-01']['start']) if p != 'sc00' else '00:00'} {zh} / {en}" for p, zh, en in CHAPTERS)
    zh, en = describe("zh", chapters), describe("en", chapters)
    assert len(zh) <= 5000 and len(en) <= 5000, (len(zh), len(en))
    if "--check-only" in sys.argv:
        return
    cover = DELIVERY / "youtube-cover.jpg"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(DELIVERY / "youtube-cover.png"), "-q:v", "3", str(cover)], check=True)
    text = DELIVERY / "upload.txt"
    text.write_text(f"""【标题 / Title】
{TITLE['zh']}

【简介 / Description】（中文，可直接粘贴，{len(zh)} 字符）
{zh}
【英文标题和简介 / English title and description】（在 Studio「语言」里添加英文翻译时粘贴）
{TITLE['en']}

{en}
【标签 / Tags】
{tags(TOPICS)}

【上传设置 / Upload settings】
· 视频：{NAME}.mp4（1920×1080，{stamp(dur)}；中文音轨在视频里）
· 英文音轨：{NAME}-英文音轨.wav，在 Studio「语言」→ 添加语言「英语」→ 音轨，上传这个文件
· 字幕：{NAME}-中文字幕.srt（中文简体）和 {NAME}-英文字幕.srt（English），两份都上传
· 缩略图：{NAME}-封面.jpg（1280×720）
· 视频语言：中文（简体）
· 观众：由作者选择
· 修改过或合成的内容：是（合成配音）
· 类别：教育
""")
    files = {film: f"{NAME}.mp4", en_audio: f"{NAME}-英文音轨.wav", DELIVERY / f"{FILM}.zh-Hans.srt": f"{NAME}-中文字幕.srt",
             DELIVERY / f"{FILM}.en.srt": f"{NAME}-英文字幕.srt", cover: f"{NAME}-封面.jpg", text: f"{NAME}-上传描述.txt"}
    DEST.mkdir(parents=True, exist_ok=True)
    manifest = []
    for source, name in files.items():
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        shutil.copy2(source, DEST / name)
        assert hashlib.sha256((DEST / name).read_bytes()).hexdigest() == digest, name
        manifest.append({"file": name, "sha256": digest, "bytes": (DEST / name).stat().st_size})
    (OUT / "package-manifest.json").write_text(json.dumps({"destination": str(DEST), "files": manifest}, ensure_ascii=False, indent=2) + "\n")
    print(f"copied to {DEST}")


def english() -> None:
    """The English cover and an English-only title and description (chapters in English), for the English audience."""
    tl = json.loads((PUB / "timeline.json").read_text())
    chapters = "\n".join(f"{stamp(tl['lines'][f'{p}-01']['start']) if p != 'sc00' else '00:00'} {en}" for p, _, en in CHAPTERS)
    description = describe("en", chapters)
    assert len(description) <= 5000, len(description)
    cover = DELIVERY / "youtube-cover.en.jpg"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(DELIVERY / "youtube-cover.en.png"), "-q:v", "3", str(cover)], check=True)
    text = DELIVERY / "upload.en.txt"
    text.write_text(f"""Title
{TITLE['en']}

Description ({len(description)} characters, paste as is)
{description}
Tags
{tags(TOPICS)}

Thumbnail: {NAME}-英文封面.jpg (1280×720)
""")
    DEST.mkdir(parents=True, exist_ok=True)
    for source, name in ((cover, f"{NAME}-英文封面.jpg"), (text, f"{NAME}-英文标题和描述.txt")):
        shutil.copy2(source, DEST / name)
        print(DEST / name)


if __name__ == "__main__":
    english() if "--english" in sys.argv else main()
