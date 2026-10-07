"""Write the YouTube title + description for both Language Bridge films.

Chapter times come from each film's own timeline, so re-run this after the
narration (and therefore the timeline) changes:

    python3 scripts/reciprocal-doors-youtube.py

Writes out/reciprocal-doors/delivery/youtube-description.{zh,en}.txt.
"""
from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "out/reciprocal-doors/delivery"
MEDIA = ROOT.parent / "lucas-academy-media"
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from youtube_tags import hashtags, tags  # noqa: E402  (README "YouTube tags": lowercase, the default set)

# The music credit (CC BY 3.0 asks for it with every upload) lives with the mix;
# read it from the source, so this runs without the mix's numpy / soundfile.
MUSIC_CREDIT = next(
    ast.literal_eval(node.value)
    for node in ast.parse((ROOT / "scripts/reciprocal-doors-tracks.py").read_text(encoding="utf-8")).body
    if isinstance(node, ast.Assign) and any(getattr(t, "id", None) == "MUSIC_CREDIT" for t in node.targets)
)

CHAPTERS = {
    "zh": {
        "rd01": "听懂了，读起来却很难",
        "rd02": "多开一个入口",
        "rd03": "我们想到双语课堂",
        "rd04": "两个孩子：互惠",
        "rd05": "共同的渠道：先一起看见",
        "rd06": "一次互教，可以怎样发生？",
        "rd07": "文字、声音、图画，各有用处",
        "rd08": "学新的，也让原来的继续长",
        "rd09": "这条渠道，也可以连接两代人",
        "rd10": "语言的桥",
    },
    "en": {
        "rd01": "When listening is easy but reading is hard",
        "rd02": "Another way in",
        "rd03": "Thinking about bilingual learning",
        "rd04": "Two children: reciprocity",
        "rd05": "Drawing, a channel they share",
        "rd06": "Teaching each other, step by step",
        "rd07": "Words, sound and pictures",
        "rd08": "Learning something new, keeping what you know",
        "rd09": "Parents and children",
        "rd10": "Language Bridge",
    },
}

TEXT = {
    "zh": {
        "title": "语言的桥：你教我，我教你",
        "body": """有的孩子，听别人念故事时什么都明白；轮到自己读，却被一些字卡住。我们在学习阅读障碍教育时注意到：认字难，并不等于理解难，也不能说明一个孩子能做什么。

这启发我们想到中英双语的孩子：有人中文讲得顺，有人英文讲得顺。如果让他们用各自擅长的语言互相教，再用画画作为共同的渠道，会怎样？

这支短片用两个虚构的孩子 Mary 和 Jacob，讲我们正在设计的学习方式：
· 文字、声音、图画，各有用处：理解故事时，先看图、听故事；练认字时，先试着读，需要时再用声音和图画帮忙。
· 互惠：我有能帮你的地方，你也有能帮我的地方。
· 学新的语言时，原来的语言和长处也继续长。
· 父母和孩子也可以这样一起学。

👉 试试「语言的桥」：https://lang.lucasacademy.org
（现在可以读「爱的篇章」，哥林多前书 13 章）
📰 Lucas Academy Weekly：https://lucasacademy.org/weekly""",
        "chapters": "章节",
        "notes": """说明
· 片中阅读障碍的例子是假设案例，Mary 和 Jacob 是虚构人物，不代表任何真实学生。这是我们正在设计的教学构想，不是诊断、治疗建议或研究结论。
· 插画为概念示意（AI 生成）。旁白为合成的朗读声音（CosyVoice）。
· 背景音乐：{music}
· 产品画面中的英文经文：The Holy Bible, New International Version® NIV® Copyright © 1973, 1978, 1984, 2011 by Biblica, Inc.® Used by permission. All rights reserved worldwide. 中文经文来源：YouVersion。""",
        "hashtags": hashtags(["双语教育", "中英双语", "阅读障碍", "语言学习"]),
        "tags": tags(["双语教育", "中英双语", "中文学习", "英文学习", "阅读障碍", "亲子共学", "儿童教育", "语言学习", "语言的桥"]),
    },
    "en": {
        "title": "Language Bridge: You Teach Me, I Teach You",
        "body": """A child can follow a story perfectly when someone reads it aloud, then get stuck on the words when reading alone. Learning about dyslexia taught us that word reading is only one part of what a child can understand and do.

That gave us an idea for bilingual kids. One is more at ease in Chinese, another in English. What if they teach each other in the language each knows best, and use drawing as a channel they share?

In this short film, two fictional children, Mary and Jacob, show the idea:
• Words, sound and pictures each have a job: to understand a story, begin with pictures and listening; to practise word reading, try reading first and add sound or pictures when needed.
• Reciprocity: I have something that can help you, and you have something that can help me.
• A new language can grow while the first one keeps growing too.
• Parents and children can learn this way together.

👉 Try Language Bridge: https://lang.lucasacademy.org
(Reading now: The Love Chapter, 1 Corinthians 13)
📰 Lucas Academy Weekly: https://lucasacademy.org/weekly""",
        "chapters": "Chapters",
        "notes": """Notes
• The dyslexia example is hypothetical, and Mary and Jacob are fictional; they do not represent any real student. This is a teaching idea we are designing, not a diagnosis, treatment advice or a research result.
• Illustrations are concept art (AI-generated). Narration: synthesized reading voices (CosyVoice).
• Music: {music}
• English Scripture in the product screens: The Holy Bible, New International Version® NIV® Copyright © 1973, 1978, 1984, 2011 by Biblica, Inc.® Used by permission. All rights reserved worldwide. Chinese Scripture source: YouVersion.""",
        "hashtags": hashtags(["bilingualkids", "learningchinese", "dyslexia", "languagelearning"]),
        "tags": tags(["bilingual kids", "learning chinese", "learning english", "dyslexia", "reading support", "parents and children", "language learning", "language bridge"]),
    },
}


def stamp(seconds: float) -> str:
    m, s = divmod(int(seconds), 60)
    return f"{m}:{s:02d}"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for lang, text in TEXT.items():
        timeline = json.loads((ROOT / f"src/scripts/reciprocal-doors.timeline.{lang}.json").read_text(encoding="utf-8"))
        # YouTube chapters: the first must be 0:00 (it takes in the title card).
        lines = [f"{'0:00' if i == 0 else stamp(s['start'])} {CHAPTERS[lang][s['id']]}" for i, s in enumerate(timeline["segments"])]
        # Chapter times are only final when every line of this film has its take.
        voice = {"zh": "fangfang/zh", "en": "louise/en"}[lang]
        script = json.loads((MEDIA / "data/scripts" / f"reciprocal-doors-{lang}.json").read_text(encoding="utf-8"))
        pending = [l["id"] for l in script["lines"] if not (MEDIA / "outputs" / voice / "reciprocal-doors" / f"{l['id']}.wav").exists()]
        draft = (" ⚠️ 配音还在重录，章节时间待更新 / narration being re-recorded, times will change") if (pending or timeline.get("missing")) else ""
        notes = text["notes"].replace("{music}", MUSIC_CREDIT)
        description = "\n\n".join([text["body"], f"{text['chapters']}{draft}\n" + "\n".join(lines), notes, text["hashtags"]])
        content = (
            f"【标题 / Title】\n{text['title']}\n\n"
            f"【简介 / Description】（可直接粘贴，约 {len(description)} 字符，YouTube 上限 5000）\n{description}\n\n"
            f"【标签 / Tags】\n{text['tags']}\n"
        )
        path = OUT / f"youtube-description.{lang}.txt"
        path.write_text(content, encoding="utf-8")
        print(f"{path.name}: {len(description)} chars, {len(lines)} chapters{', DRAFT chapters' if draft else ''}")


if __name__ == "__main__":
    main()
