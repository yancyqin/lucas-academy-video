"""Package a rendered 中英阅读 film for YouTube: captions in both languages and the upload notes.

    python3 scripts/zhong-ying/package.py climb-higher <upload dir>

Copies out/zhong-ying/<film>/<film>.mp4 and writes, beside it:
  <film>.zh-Hans.srt / <film>.en.srt   each verse in that language for as long as it is read in either language
                                        (so the Chinese track translates the English reading and the other way round)
  upload.txt                           title, description (chapters, links, credits, NIV notice), tags, settings
The covers are made by cover.py (ZHONG-YING.md §Cover) into the same folder.
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts/zhong-ying"))
from youtube_tags import hashtags, tags  # noqa: E402

TOPIC = ["chinese", "english", "readaloud", "poetry", "bible", "中英阅读"]
NIV = ("Scripture quotations taken from The Holy Bible, New International Version® NIV®. Copyright © 1973, 1978, "
       "1984, 2011 by Biblica, Inc.™ Used by permission. All rights reserved worldwide.")
ABOUT = {
    "climb-higher": {
        "zh": "这一集读三篇，都是爬到高处往远处看：唐诗《登鹳雀楼》（王之涣）、斯蒂文森的《外面的世界》（Foreign Lands）、诗篇 121:1–2。",
        "en": "Three readings about climbing higher to see farther: “On the Stork Tower” (Wang Zhihuan, Tang dynasty), Robert Louis Stevenson’s “Foreign Lands”, and Psalm 121:1–2.",
        "sources_zh": "《登鹳雀楼》和斯蒂文森的 “Foreign Lands”（1885，选第 1、4 节）是公有领域，互译由 Lucas Academy 完成。诗篇中文为和合本（公有领域），英文为 NIV。",
        "sources_en": "“On the Stork Tower” and Stevenson’s “Foreign Lands” (1885, stanzas 1 and 4) are in the public domain; the translations are by Lucas Academy. Psalm 121: Chinese Union Version (public domain); English NIV.",
        "read_zh": "《登鹳雀楼》和诗篇的中文由 Sunny 朗读，《外面的世界》的英文由 Matthew 朗读",
        "read_en": "The Chinese of “On the Stork Tower” and the Psalm is read by Sunny, the English of “Foreign Lands” by Matthew",
    },
    "little-boats": {
        "zh": "这一集读三篇，都是小船去远方：唐诗《早发白帝城》（李白）、斯蒂文森的《小船漂到哪里去？》（Where Go the Boats?）、以赛亚书 40:31。",
        "en": "Three readings about little boats going far away: “Leaving Baidi at Dawn” (Li Bai, Tang dynasty), Robert Louis Stevenson’s “Where Go the Boats?”, and Isaiah 40:31.",
        "sources_zh": "《早发白帝城》和斯蒂文森的 “Where Go the Boats?”（1885）是公有领域，互译由 Lucas Academy 完成。以赛亚书中文为和合本（公有领域），英文为 NIV。",
        "sources_en": "“Leaving Baidi at Dawn” and Stevenson’s “Where Go the Boats?” (1885) are in the public domain; the translations are by Lucas Academy. Isaiah 40:31: Chinese Union Version (public domain); English NIV.",
        "read_zh": "《早发白帝城》和以赛亚书的中文由 Sunny 朗读，《小船漂到哪里去？》的英文由 Matthew 朗读",
        "read_en": "The Chinese of “Leaving Baidi at Dawn” and Isaiah is read by Sunny, the English of “Where Go the Boats?” by Matthew",
    },
    "can-beauty-last": {
        "zh": "这一集读三篇，都在问美好能不能留下来：唐诗《春夜喜雨》（杜甫）、莎士比亚的《第十八首十四行诗》（Sonnet 18）、传道书 3:11。",
        "en": "Three readings that ask whether beauty can last: “Happy Rain on a Spring Night” (Du Fu, Tang dynasty), William Shakespeare’s Sonnet 18, and Ecclesiastes 3:11.",
        "sources_zh": "《春夜喜雨》和莎士比亚的《第十八首十四行诗》（1609）是公有领域，互译由 Lucas Academy 完成。传道书中文为和合本（公有领域），英文为 NIV。",
        "sources_en": "“Happy Rain on a Spring Night” and Shakespeare’s Sonnet 18 (1609) are in the public domain; the translations are by Lucas Academy. Ecclesiastes 3:11: Chinese Union Version (public domain); English NIV.",
        # The lesson was voiced for the series from the start (lesson_voice.py): every verse, title and the closing
        # in Sunny's and Matthew's voices made with AI; the opening, the Chinese titles, the closing (films.series_voices)
        # and the last line are Fangfang's and Louise's.
        "voices_zh": "中文由 Sunny、英文由 Matthew 配音，用他们自己的录音由 AI 合成；开头、中文题目、回顾和最后一句为 AI 合成，使用 Fangfang（中文）和 Louise（英文）的授权声线。",
        "voices_en": "The Chinese is voiced by Sunny and the English by Matthew, made with AI from their own recordings; the opening, the Chinese titles, the look back and the last line are AI-generated with Fangfang's (Chinese) and Louise's (English) licensed voices.",
    },
}


def stamp(s: float, srt: bool = False) -> str:
    if srt:
        ms = round(s * 1000)
        return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"
    s = int(s)
    return f"{s // 60:02d}:{s % 60:02d}"


def text_of(cue) -> str:
    sep = "" if cue["lang"] == "zh" else " "
    out = ""
    for w in cue["words"]:
        if w["text"] == "\n":
            out += "\n"
        else:
            out += (sep if out and not out.endswith("\n") and w["start"] is not None else "") + w["text"]
    return out.strip()


def srt(tl, lang: str) -> str:
    """One caption per spoken cue, always in this track's language: the intro, each title, each verse and the
    closing are shown while either language reads them."""
    by_unit = {(c["unit"], c["lang"]): c for c in tl["cues"] if c["kind"] == "verse"}
    by_kind = {(c["kind"], c["work"], c["lang"]): c for c in tl["cues"] if c["kind"] != "verse"}
    items = []
    for c in tl["cues"]:
        same = by_unit[(c["unit"], lang)] if c["kind"] == "verse" else by_kind[(c["kind"], c["work"], lang)]
        items.append((c["start"], c["end"], text_of(same)))
    return "\n".join(f"{i}\n{stamp(a, True)} --> {stamp(b, True)}\n{t}\n" for i, (a, b, t) in enumerate(items, 1))


def main(film: str, dest: Path):
    tl = json.loads((ROOT / "public/zhong-ying" / film / "timeline.json").read_text())
    video = ROOT / "out/zhong-ying" / film / f"{film}.mp4"
    dest.mkdir(parents=True, exist_ok=True)
    shutil.copy2(video, dest / video.name)
    for lang, tag in (("zh", "zh-Hans"), ("en", "en")):
        (dest / f"{film}.{tag}.srt").write_text(srt(tl, lang))
    about = ABOUT[film]
    title = tl["title"]
    first = tl["works"][0]["id"]
    chapters_zh = "\n".join(f"{stamp(c['start'])} {c['zh']}" for c in tl["chapters"])
    chapters_en = "\n".join(f"{stamp(c['start'])} {c['en']}" for c in tl["chapters"])
    moving = any(w.get("minimax") for w in tl["works"])     # works that end as a MiniMax clip; 回顾 replays them all
    each = all(w.get("minimax") for w in tl["works"])
    moves_zh = about.get("moves_zh", ("每篇" if each else "有的篇") + "读到最后一句，画再动起来；最后一起回顾。") if moving else ""
    moves_en = about.get("moves_en", f" As {'each reading' if each else 'some readings'} reaches its last line, the picture starts to move, and at the end we look back at all three.") if moving else ""
    made_zh = "，最后一句时动起来的画面由 MiniMax 海螺生成" if moving else ""
    made_en = f", and the moving pictures under the last line of {'each reading' if each else 'the readings'} were made with MiniMax Hailuo" if moving else ""
    made_how = " and motion" if moving else ""
    voices_zh = about.get("voices_zh") or f"{about['read_zh']}；其余配音（开头、题目、结尾和其他句子）为 AI 合成，使用 Fangfang（中文）和 Louise（英文）的授权声线。"
    voices_en = about.get("voices_en") or (f"{about['read_en']}; the rest of the narration (the intro, the titles, the closing and the "
                                           "other lines) is AI-generated with Fangfang's (Chinese) and Louise's (English) licensed voices.")
    lesson = f"https://lang.lucasacademy.org/?lesson={film}"
    art = f"https://art-lab.lucasacademy.org/living?w={first}"
    notes = f"""【标题 / Title】
【中英阅读】{title['zh']} | {title['en']}

【简介 / Description】
学习语言最好的方式是朗读。不论你是想学中文还是英文，跟我们一起读吧。
{about['zh']}每一句先读中文，再读英文；读到哪个词，哪个词就亮起来。读中文时，画一笔一笔画出来；读英文时，画上的东西活起来。{moves_zh}

The best way to learn a language is to read it aloud. Whether you want to learn Chinese or English, read along with us.
{about['en']} Every verse is read in Chinese, then in English, and each word lights up as it is read. While the Chinese is read, the picture is painted in stroke by stroke; while the English is read, it comes alive.{moves_en}

课文、生词和逐句朗读 · The lesson, its words and every line read aloud: {lesson}
自己来画活画 · Paint the living pictures yourself: {art}

{chapters_zh}

{chapters_en}

作者 Lucas Academy Team · By Lucas Academy Team
{voices_zh}画由 AI 生成，会动的笔刷来自 Lucas Academy 美术实验室的活画{made_zh}。
{voices_en} The pictures are AI-generated, the living brushes come from Lucas Academy's art lab{made_en}.
{about['sources_zh']}
{about['sources_en']}
{NIV}

{hashtags(TOPIC)}

【标签 / Tags】
{tags(TOPIC)}

【上传设置 / Upload settings】
· Video: {video.name} (1920×1080, 30 fps, {stamp(tl['durationSeconds'])}; −16 LUFS)
· Captions: {film}.zh-Hans.srt (中文), {film}.en.srt (English) — each verse in that language while it is read in either
· Thumbnail: cover.a.zh.jpg (双语朗读 big, the title beneath it); English: cover.a.en.jpg
· Video language: Chinese
· Altered or synthetic content: yes (partly synthetic narration, AI-generated pictures{made_how})
· Category: Education
"""
    (dest / "upload.txt").write_text(notes)
    print(f"{dest}: {video.name}, 2 captions, upload.txt")


if __name__ == "__main__":
    main(sys.argv[1], Path(sys.argv[2]))
