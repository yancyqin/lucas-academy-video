"""YouTube title, description (chapters from each film's timeline), tags and cover for both films.

    python3 scripts/fun-informatics-01/youtube.py

Tags follow README "YouTube tags" (scripts/youtube_tags.py: lowercase, the default set first in the
hashtag line). Each file has the project's layout: 【标题】, 【简介】 (paste as is, ends in the hashtags),
【标签】 (the Studio tags field) and 【上传设置】. Writes out/fun-informatics-01/delivery/
youtube-description.{zh,en}.txt and youtube-cover.{zh,en}.jpg (1280×720, the big-question cover).
"""
import json
import re
import subprocess
import tempfile
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "out/fun-informatics-01/delivery"
PUB = ROOT / "public/fun-informatics-01"
SECTION = re.compile(r"^## (IT\d\d) · (.+)$")
sys.path.insert(0, str(ROOT / "scripts"))
from youtube_tags import hashtags, tags  # noqa: E402  (README "YouTube tags": lowercase, the default set)

TEXT = {
    "zh": {
        "title": "计算机怎么算 1+1=？｜趣味信息学1",
        "byline": "作者：Yancy Qin, Louise Yang | Lucas Academy",
        "lead": ("计算机的图像，能不能无限放大？计算机又是怎么算 1+1 的？\n\n"
                 "我们走进 Lucas Academy 太空博物馆里的「像素科学室」，从一个开关开始，一层一层往下看：比特、二进制、"
                 "规则、像素，两个开关怎么算出 1+1=10，游戏和分形是怎么“算”出来的，最后用香农的尺子量一量：信息到底是什么。"),
        "chapters": "章节",
        "credits": [
            "画面：Inception Space 太空博物馆 · 像素科学室（The Pixel Science Room），is.lucasacademy.org",
            "分形：用 z → z² + c 一帧一帧算出来的（海马谷，c ≈ −0.7436439 + 0.1318259i）",
            "电路画面：AI 生成",
            "“你最喜欢的游戏”一图：Printables 上 Link 透光浮雕（CC0）的像素重制；Link © Nintendo",
            "音乐：Echoes in the Void（Yancy，用 Suno 制作）",
            "配音：AI 合成语音",
        ],
        # after the 9 defaults, at most 6 of the film's own (15 in all); no spaces and no "+" in a hashtag
        "hashtags": ["趣味信息学", "信息论", "计算机", "香农", "二进制", "像素"],
        "tags": ["趣味信息学", "信息论", "香农", "比特", "二进制", "1+1", "像素", "分形", "曼德博集合", "计算机原理", "计算机怎么算", "儿童科学"],
        "paste": "可直接粘贴，约 {n} 字符，YouTube 上限 5000",
        "upload": """【上传设置 / Upload settings】
· 视频：fun-informatics-01.zh.mp4（1920×1080，{length}，−16 LUFS）
· 字幕：fun-informatics-01.zh.zh-Hans.srt（中文），fun-informatics-01.zh.en.srt（英文）
· 缩略图：youtube-cover.zh.jpg（1280×720）
· 视频语言：中文（简体）
· 观众：由你决定；选「专为儿童打造」会关掉评论和个性化广告
· 修改过或合成的内容：是（合成配音；电路画面由 AI 生成）
· 类别：教育""",
    },
    "en": {
        "title": "How Does a Computer Add 1 + 1=? | Fun Informatics 1",
        "byline": "By Yancy Qin, Louise Yang | Lucas Academy",
        "lead": ("Can a computer picture be zoomed in forever? And how does a computer add 1 + 1?\n\n"
                 "We walk into the Pixel Science Room of the Lucas Academy space museum and go down one layer at a time: "
                 "bits, binary, rules and pixels; how two switches add 1 + 1 = 10; how a game and a fractal are computed; "
                 "and finally Shannon's ruler for measuring what information is."),
        "chapters": "Chapters",
        "credits": [
            "Filmed in Inception Space · The Pixel Science Room, is.lucasacademy.org",
            "Fractal: computed frame by frame from z → z² + c (Seahorse Valley, c ≈ −0.7436439 + 0.1318259i)",
            "Circuit pictures: AI-generated",
            "“Your favorite game” image: a pixel remake of a CC0 Link lithophane on Printables; Link © Nintendo",
            "Music: Echoes in the Void (Yancy, made with Suno)",
            "Narration: AI-synthesized voice",
        ],
        "hashtags": ["funinformatics", "informationtheory", "computerscience", "claudeshannon", "binary", "pixels"],
        "tags": ["fun informatics", "information theory", "claude shannon", "bits", "binary", "1+1", "pixels", "fractal",
                 "mandelbrot set", "how computers work", "computer science", "science for kids"],
        "paste": "paste as is; about {n} characters, YouTube allows 5000",
        "upload": """【上传设置 / Upload settings】
· Video: fun-informatics-01.en.mp4 (1920×1080, {length}, −16 LUFS)
· Subtitles: fun-informatics-01.en.en.srt (English), fun-informatics-01.en.zh-Hans.srt (Chinese)
· Thumbnail: youtube-cover.en.jpg (1280×720)
· Video language: English
· Audience: your call; "Made for kids" turns off comments and personalized ads
· Altered or synthetic content: yes (synthesized voice; AI-generated circuit pictures)
· Category: Education""",
    },
}


def sections(lang: str) -> dict:
    """IT section -> its title in the edit file of that language."""
    src = ROOT / f"docs/fun-informatics-01/{lang}-edit.md"
    return {m.group(1).lower(): m.group(2).strip() for line in src.read_text(encoding="utf-8").splitlines() if (m := SECTION.match(line))}


def stamp(t: float) -> str:
    t = int(t)
    return f"{t // 60}:{t % 60:02d}"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for lang in ("zh", "en"):
        tl = json.loads((PUB / f"timeline.{lang}.json").read_text())
        names = sections(lang)
        first = {}
        for c in tl["cues"]:
            first.setdefault(c["section"], c["start"])
        lines = [f"0:00 {names['it00']}"] + [f"{stamp(first[s])} {names[s]}" for s in sorted(first) if s != "it00"]
        t = TEXT[lang]
        description = "\n\n".join([t["lead"], "\n".join([t["chapters"], *lines]), "\n".join(t["credits"]), t["byline"], hashtags(t["hashtags"])])
        content = (f"【标题 / Title】\n{t['title']}\n\n"
                   f"【简介 / Description】（{t['paste'].format(n=len(description))}）\n{description}\n\n"
                   f"【标签 / Tags】\n{tags(t['tags'])}\n\n"
                   f"{t['upload'].replace('{length}', stamp(round(tl['durationSeconds'])))}\n")
        (OUT / f"youtube-description.{lang}.txt").write_text(content, encoding="utf-8")
        with tempfile.TemporaryDirectory() as tmp:
            png = Path(tmp) / "cover.png"
            subprocess.run(["npx", "remotion", "still", "src/index.ts", f"FunInformatics01Cover{lang.capitalize()}", str(png), "--log=error"],
                           cwd=ROOT, check=True)
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(png), "-vf", "scale=1280:720:flags=lanczos", "-q:v", "2",
                            str(OUT / f"youtube-cover.{lang}.jpg")], check=True)
        print(f"{lang}: {OUT / f'youtube-description.{lang}.txt'} + cover")


if __name__ == "__main__":
    main()
