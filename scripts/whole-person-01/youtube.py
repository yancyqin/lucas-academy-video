"""Write the YouTube title, description, tags and thumbnail for both films.

Chapter times and lengths come from each film's own timeline, so re-run this
after `npm run wp01:timeline` (and the render) whenever the narration changes:

    npm run wp01:youtube

Writes out/whole-person-01/delivery/youtube-description.{zh,en}.txt and
youtube-thumbnail.{zh,en}.jpg (the title frame, 1280×720).
"""
from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "out/whole-person-01/delivery"
COMPOSITION = {"zh": "WholePersonZh", "en": "WholePersonEn"}
THUMBNAIL_FRAME = 150  # 5 s in: the title card over the transit chamber

NIV = ("The Holy Bible, New International Version® NIV® Copyright © 1973, 1978, 1984, 2011 by Biblica, Inc.® "
       "Used by permission. All rights reserved worldwide.")
NLT = ("Holy Bible, New Living Translation, copyright © 1996, 2004, 2015 by Tyndale House Foundation. "
       "Used by permission of Tyndale House Publishers, Carol Stream, Illinois 60188. All rights reserved.")

# YouTube chapters start at the line named here; the first one is always 0:00.
CHAPTERS = {
    "zh": {
        "wp00-01": "谁是教育者？",
        "wp00-04": "学习是拥有，而不是被喂养",
        "wp01-01": "理念 1 · 权柄",
        "wp01-12": "Lucas 和 Matthew 的画",
        "wp02-01": "理念 2 · 目标",
        "wp03-01": "理念 3 · 互教互学",
        "wp04-01": "理念 4 · 引导探索",
        "wp05-01": "理念 5 · 你来作主",
        "wp06-01": "全人教育的五个理念",
    },
    "en": {
        "wp00-01": "Who is an educator?",
        "wp00-04": "Learning is about owning, not being fed",
        "wp01-01": "Principle 1 · Authority",
        "wp01-12": "Lucas and Matthew's drawings",
        "wp02-01": "Principle 2 · Purpose",
        "wp03-01": "Principle 3 · Learning from each other",
        "wp04-01": "Principle 4 · Guided discovery",
        "wp05-01": "Principle 5 · You are the boss",
        "wp06-01": "The five principles",
    },
}

TEXT = {
    "zh": {
        "title": "我们怎样陪孩子成长：全人教育的五个理念",
        "body": """谁是教育者？老师、父母、朋友，孩子都可以是教育者。如果你这样想，这个视频，就是给你的。

学习是拥有，而不是被喂养。这支短片讲 Lucas Academy 全人教育的五个理念，并配上孩子们在 Lucas Academy 使用和创作的作品：
· 权柄：当孩子对权柄说“不”，我们带着好奇心问：为什么？——批判性素养（critical literacy）与问题化（problematizing）。我们相信，教育者应该是 authoritative（有权威又温暖），而不是 authoritarian（专制）。
· 目标：我们不塑造你的孩子，我们帮助他们发现自己的价值。（以弗所书 2:10）
· 互教互学：学习者、教育者和志愿者组成的社区，和孩子一起学习。（希伯来书 10:24）
· 引导探索：只比孩子领先一步，让探索充满乐趣；也领先一千步，让旅程安全。（诗篇 119:105）
· 你来作主：孩子定方向，教育者做孩子的 agent。（创世记 1:28）

📖 全文《全人教育理念的根基》：https://lucasacademy.org/research/whole-person-education
🚀 Inception Space 太空博物馆：https://is.lucasacademy.org
🌉 语言的桥：https://lang.lucasacademy.org
🐍 Snake-Lab 公开排行榜：https://lucasacademy.org/challenge
🌐 Lucas Academy：https://lucasacademy.org""",
        "chapters": "章节",
        "notes": f"""说明
· 片中 Lucas 和 Matthew 的画经家长同意使用；最终作品为 Inception Space 展出版本（轻微修整、增亮）。
· 旁白：Yancy 本人的声音，经 CosyVoice 声音克隆合成。
· 画面：Lucas Academy 的应用录屏（Inception Space、Art Lab、语言的桥、Snake-Lab）。
· 背景音乐：《Echoes in the Void》，Yancy 用 Suno 创作（Inception Space「Journey of Art」房间配乐）。
· 爱因斯坦引用：《论教育》（On Education，1936）。
· 中文经文：和合本。画面中的英文经文：{NIV} 以弗所书 2:10 英文：{NLT}""",
        "hashtags": "#全人教育 #基督教教育 #亲子教育 #批判性素养 #LucasAcademy",
        "tags": "全人教育, 基督教教育, 亲子教育, 家长, 教育理念, 批判性素养, 问题化, 引导探索, Inception Space, Art Lab, 语言的桥, Snake-Lab, Lucas Academy",
        "upload": """【上传设置 / Upload settings】
· 视频：whole-person-five-principles.zh.mp4（1920×1080，{length}，−16 LUFS）
· 缩略图：youtube-thumbnail.zh.jpg（1280×720）
· 字幕：whole-person-five-principles.zh.zh-Hans.srt →「中文（简体）」；whole-person-five-principles.zh.en.srt →「英语」（两份都按中文配音计时）
· 视频语言：中文（简体）
· 观众：否，不是专为儿童打造的（这支片子是对家长说的）
· 修改过或合成的内容：是（旁白是合成声音；YouTube 要求披露「合成人物声音来旁白」）
· 类别：教育
· 公开范围：由你决定""",
    },
    "en": {
        "title": "How We Grow Alongside Our Kids: Five Principles of Whole-Person Education",
        "body": """Who is an educator? Teachers, parents, friends, and kids can all be educators. If you see it that way, this video is for you.

Learning is about owning, not being fed. This short film walks through Lucas Academy's five principles of whole-person education, alongside things kids use and make at Lucas Academy:
• Authority: when a child says no to authority, we ask why, with curiosity — critical literacy and problematizing. We believe educators should be authoritative, with both authority and warmth, rather than authoritarian.
• Purpose: we don't shape your kids; we help them discover their own value. (Ephesians 2:10)
• Learning from each other: a community of learners, educators, and volunteers, learning together with kids. (Hebrews 10:24)
• Guided discovery: one step ahead so the journey is fun, a thousand steps ahead so it is safe. (Psalm 119:105)
• You are the boss: kids set the direction; educators act as their agents. (Genesis 1:28)

📖 Read the essay, "The Foundations of Whole-Person Education": https://lucasacademy.org/research/whole-person-education
🚀 Inception Space: https://is.lucasacademy.org
🌉 Language Bridge: https://lang.lucasacademy.org
🐍 Snake-Lab public ranking: https://lucasacademy.org/challenge
🌐 Lucas Academy: https://lucasacademy.org""",
        "chapters": "Chapters",
        "notes": f"""Notes
• Lucas's and Matthew's drawings are shared with their parent's permission; the finished artworks are the versions shown in Inception Space (lightly cleaned up and brightened).
• Narration: a synthesized reading voice (CosyVoice).
• Footage: screen recordings of Lucas Academy's apps (Inception Space, Art Lab, Language Bridge, Snake-Lab).
• Music: "Echoes in the Void", made by Yancy with Suno (the Journey of Art room in Inception Space).
• Einstein quotation: "On Education" (1936).
• Scripture quotations marked NIV are taken from {NIV} Ephesians 2:10 is taken from the {NLT}""",
        "hashtags": "#WholePersonEducation #ChristianEducation #Parenting #CriticalLiteracy #LucasAcademy",
        "tags": "whole-person education, Christian education, parenting, educators, critical literacy, problematizing, guided discovery, Inception Space, Art Lab, Language Bridge, Snake-Lab, Lucas Academy",
        "upload": """【上传设置 / Upload settings】
· Video: whole-person-five-principles.en.mp4 (1920×1080, {length}, −16 LUFS)
· Thumbnail: youtube-thumbnail.en.jpg (1280×720)
· Captions: whole-person-five-principles.en.en.srt → English; whole-person-five-principles.en.zh-Hans.srt → Chinese (Simplified) (both timed to the English narration)
· Video language: English
· Audience: No, it's not made for kids (it is addressed to parents)
· Altered or synthetic content: Yes (the narration is a synthesized voice)
· Category: Education
· Visibility: your call""",
    },
}


def stamp(seconds: float) -> str:
    m, s = divmod(int(seconds), 60)
    return f"{m}:{s:02d}"


def thumbnail(lang: str) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        frame = Path(tmp) / "frame.png"
        subprocess.run(["npx", "remotion", "still", "src/index.ts", COMPOSITION[lang], str(frame),
                        f"--frame={THUMBNAIL_FRAME}", "--timeout=240000", "--log=error"], cwd=ROOT, check=True)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(frame), "-vf", "scale=1280:720:flags=lanczos",
                        "-q:v", "3", str(OUT / f"youtube-thumbnail.{lang}.jpg")], check=True)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for lang, text in TEXT.items():
        timeline = json.loads((ROOT / f"public/whole-person-01/timeline.{lang}.json").read_text(encoding="utf-8"))
        start = {c["id"]: c["start"] for c in timeline["cues"]}
        lines = [f"{'0:00' if i == 0 else stamp(start[cue])} {name}" for i, (cue, name) in enumerate(CHAPTERS[lang].items())]
        description = "\n\n".join([text["body"], f"{text['chapters']}\n" + "\n".join(lines), text["notes"], text["hashtags"]])
        length = stamp(round(timeline["durationSeconds"]))
        content = (
            f"【标题 / Title】\n{text['title']}\n\n"
            f"【简介 / Description】（可直接粘贴，约 {len(description)} 字符，YouTube 上限 5000）\n{description}\n\n"
            f"【标签 / Tags】\n{text['tags']}\n\n"
            f"{text['upload'].replace('{length}', length)}\n"
        )
        path = OUT / f"youtube-description.{lang}.txt"
        path.write_text(content, encoding="utf-8")
        print(f"{path.name}: {len(description)} chars, {len(lines)} chapters, film {length}")
        thumbnail(lang)
        print(f"youtube-thumbnail.{lang}.jpg")


if __name__ == "__main__":
    main()
