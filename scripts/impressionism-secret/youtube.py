"""Chinese and English YouTube titles, descriptions and tags for 你知道印象派的秘密吗？

    python3 scripts/impressionism-secret/youtube.py

Writes out/impressionism-secret/youtube-description.{zh,en}.txt (title, description
ending in the hashtags, tags, upload settings) and docs/impressionism-secret/sources.md
(every picture's source page and licence, from the media manifests). One upload:
English is the default audio, Chinese is a dub; chapters come from the shared timeline,
identical for both languages. Tags follow scripts/youtube_tags.py.
"""
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from youtube_tags import DEFAULT as DEFAULT_TAGS, hashtags  # noqa: E402

OUT = ROOT / "out/impressionism-secret"
PUB = (ROOT / "public/impressionism-secret").resolve()
SOURCES_MD = ROOT / "docs/impressionism-secret/sources.md"
SOURCES_URL = "https://github.com/yancyqin/lucas-academy-video/blob/main/docs/impressionism-secret/sources.md"

TITLE = {"zh": "你知道印象派的秘密吗？｜从信息学看马奈、莫奈、德加、莫里索、雷诺阿、塞尚",
         "en": "Do You Know the Secret of Impressionism? | Manet, Monet, Degas, Morisot, Renoir, Cézanne and Information"}

LEAD = {  # v10 (owner 2026-11-04): questions first; the painters' own words where they left any
    "zh": """这位画家，把芭蕾舞演员的头切掉了。大家花钱来看的，他为什么偏偏切掉？

这一集认识六位印象派画家：马奈、莫奈、德加、莫里索、雷诺阿、塞尚。每一位我们都问同一个问题：在他眼里，什么最重要，什么可以去掉？他们自己说过的，我们引原话；没说过的，我们只提问题，留给你想。从沙龙、马奈的《草地上的午餐》《奥林匹亚》和 1874 年第一次展览讲起，一直到莫奈和卡米耶、德加的舞者、莫里索的摇篮、雷诺阿的光斑和塞尚的苹果。

作者：Eunice Yue, Yancy Qin ｜ Lucas Academy
中文配音：播放器 设置 → 音轨 → 中文。字幕有中文和英文。""",
    "en": """This painter cut off the dancers' heads. Why cut off the very thing people paid to see?

Meet six Impressionist painters: Manet, Monet, Degas, Morisot, Renoir and Cézanne. For each one we ask the same question: in their eyes, what mattered most, and what could be left out? Where they said it themselves, we quote them; where they didn't, we only ask, and leave the answer to you. From the Paris Salon, Manet's Luncheon on the Grass and Olympia, and the first exhibition of 1874, to Monet and Camille, Degas's dancers, Morisot's cradle, Renoir's dappled light and Cézanne's apples.

By Eunice Yue, Yancy Qin | Lucas Academy
Chinese audio: in the player, choose Settings → Audio track → Chinese. Subtitles are in English and Chinese.""",
}

CHAPTERS = {  # README "YouTube chapters": 2–4 characters / one or two words
    "im00": ("开场", "Opening"), "im02": ("沙龙", "Salon"), "im03": ("马奈", "Manet"), "im04": ("奥林匹亚", "Olympia"),
    "im05": ("马奈莫奈", "Manet & Monet"), "im06": ("1874", "1874"), "im07": ("莫奈", "Monet"), "im08": ("德加", "Degas"),
    "im09": ("莫里索", "Morisot"), "im10": ("雷诺阿", "Renoir"), "im11": ("塞尚", "Cézanne"),
    "im13": ("秘密", "Secret"), "im14": ("结尾", "End"),
}

NOTES = {
    "zh": """说明
· 《草地上的午餐》和《奥林匹亚》含裸体（艺术史名作）；从 {nudity_start} 起展示。事先有跳过提示，可按进度条跳到「马奈莫奈」一章。
· 画面里的画作和照片都是原作（公有领域或 CC0）。以下是 AI 生成的，由原画想象还原，不是历史影像：会动的场景（作者用 Muse 生成的短视频；撑阳伞的山坡一段用 MiniMax），以及四张实景图（吹笛少年的房间、协和广场、摇篮的纱、苹果桌，Codex 生成）。
· 旁白为 AI 合成配音。文案由作者与 Claude 合作完成，史实和引语已逐条核对出处。
· 主要出处：迪雷《马奈传》1902；普鲁斯特《马奈回忆》1913；左拉《L'Événement》1866-05-07；勒鲁瓦《Le Charivari》1874-04-25；佩里《American Magazine of Art》1927；莫奈致若弗鲁瓦信 1890-10-07；克列孟梭《克劳德·莫奈：睡莲》1928；乔治·摩尔《Impressions and Opinions》1891；沃拉尔《德加》1924；莫里索笔记（奥赛博物馆 2019 年展览引）；德尼《L'Occident》1907；塞尚致贝尔纳信 1904；香农 1948；奥赛博物馆《草地上的午餐》《奥林匹亚》《歌剧院的乐队》藏品页。""",
    "en": """Notes
· Luncheon on the Grass and Olympia include nudity (landmarks of art history), shown from {nudity_start}. A warning appears beforehand; use the progress bar to skip to "Manet & Monet".
· Every painting and photograph on screen is the original (public domain or CC0). AI-generated, imagined from the paintings, not historical footage: the moving scenes (short videos the authors made with Muse; the windy hill with the parasol, MiniMax) and four real-scene pictures (the fifer's room, the Place de la Concorde, the cradle's gauze, the table of apples; Codex).
· Narration: AI-synthesized voice. Script written by the authors with Claude; facts and quotations were checked against their sources.
· Main sources: Duret, Histoire d'Édouard Manet, 1902; Antonin Proust, Édouard Manet: Souvenirs, 1913; Zola, L'Événement, 7 May 1866; Leroy, Le Charivari, 25 April 1874; Lilla Cabot Perry, American Magazine of Art, 1927; Monet to Geffroy, 7 October 1890; Clemenceau, Claude Monet: The Water Lilies, 1928 (trans. Bruce Michelson); George Moore, Impressions and Opinions, 1891; Vollard, Degas, 1924 (trans. 1927); Morisot's notebook (quoted by the Musée d'Orsay, 2019); Maurice Denis, L'Occident, 1907; Cézanne to Émile Bernard, 1904; Shannon, 1948; Musée d'Orsay collection pages for Luncheon on the Grass, Olympia and The Orchestra at the Opera.""",
}

MUSIC = {
    "zh": "音乐：萨蒂《裸体歌舞》第一、二首（Michael Laucke 演奏，公有领域；Robin Alciatore 演奏，公有领域）；福雷《第一小提琴奏鸣曲》第二乐章（Yeh Che-Jui、嘉义市交响乐团，CC BY 3.0，Wikimedia Commons）",
    "en": "Music: Satie, Gymnopédies Nos. 1 and 2 (Michael Laucke, public domain; Robin Alciatore, public domain); Fauré, Violin Sonata No. 1, II. Andante (Yeh Che-Jui, Chiayi Symphony Orchestra, CC BY 3.0, via Wikimedia Commons)",
}

# The description's hashtag line: YouTube ignores every hashtag when there are more than 15, and the 9 project
# defaults come first, so 6 of the film's own fit (v10, owner 2026-11-04: "tag 太少了").
HASHTAGS = ["impressionism", "monet", "manet", "degas", "renoir", "cezanne"]
# The tags block, written as hashtags (owner 2026-11-04: "用 # 和空格，词之间没有空格"); YouTube's tag box allows 500 characters.
TAGS = {"zh": ["印象派", "莫奈", "马奈", "德加", "莫里索", "雷诺阿", "塞尚", "奥林匹亚", "印象日出", "撑阳伞的女人", "歌剧院的乐队",
               "舞蹈课", "煎饼磨坊的舞会", "圣维克多山", "芭蕾", "名画欣赏", "西方美术史", "艺术史", "美育", "油画", "信息论", "香农",
               "impressionism", "claudemonet", "edouardmanet", "edgardegas", "berthemorisot", "renoir", "cezanne"],
        "en": ["impressionism", "claudemonet", "edouardmanet", "edgardegas", "berthemorisot", "renoir", "paulcezanne",
               "olympia", "impressionsunrise", "womanwithaparasol", "thedanceclass", "orchestraattheopera", "ballet",
               "moulindelagalette", "montsaintevictoire", "camillemonet", "famouspaintings", "arthistoryforkids",
               "artforkids", "paintingsexplained", "informationtheory", "claudeshannon", "musee dorsay"]}


def tag_line(own: list[str]) -> str:
    """The tags block as hashtags: the film's own, then the project defaults, each without spaces, no repeats."""
    seen, words = set(), []
    for t in [*own, *DEFAULT_TAGS]:
        w = t.replace(" ", "").replace("#", "").lower()
        if w and w not in seen:
            seen.add(w)
            words.append(w)
    line = " ".join(f"#{w}" for w in words)
    assert len(line) <= 500, f"tags are {len(line)} characters"
    return line


UPLOAD = """【上传设置 / Upload settings】
· One upload: impressionism-secret.en.mp4, English as the default audio (v6, 2026-11-02)
· Studio → Languages → Chinese: the Chinese title and description, and impressionism-secret.zh.m4a as the Chinese dub
· Subtitles: impressionism-secret.en.srt and impressionism-secret.zh.srt (both line up with either audio track)
· Thumbnail: cover.en.jpg (Morisot saying "shh", design B2; on the cover: The Secret of Impressionism); cover.zh.jpg (印象派的秘密) if a Chinese thumbnail can be set. Alternative on Degas's own painting: cover-degas.en.jpg / cover-degas.zh.jpg
· Altered or synthetic content: Yes (synthesized narration; AI-generated video scenes and four pictures)
· Audience: check YouTube's age and made-for-kids settings for artistic nudity before publishing
· Category: Education"""


def stamp(t: float) -> str:
    t = int(t)
    return f"{t // 60}:{t % 60:02d}"


def chapters(lang: str) -> list[str]:
    tl = json.loads((ROOT / "src/data/impressionism-secret.json").read_text(encoding="utf-8"))
    rows = []
    for sec, (zh, en) in CHAPTERS.items():
        t = 0 if sec == "im00" else tl["chapters"][sec]
        if sec == "im05":
            t = math.ceil(t)  # The displayed skip must land after artistic nudity ends.
        rows.append(f"{stamp(t)} {zh if lang == 'zh' else en}")
    return rows


def sources() -> None:
    lines = ["# 你知道印象派的秘密吗？ — picture and music sources", "",
             "Every painting and photograph is public domain or CC0. AI-generated (not marked on screen): the moving",
             "scenes (the authors' AI video clips, listed below) and, since v10, four Codex real-scene pictures that no clip",
             "repeats: real-fifer-1866, real-concorde-1875, real-cradle-1872, real-apples-still-life.", ""]
    for folder in ("art", "portraits"):
        rows = json.loads((PUB / folder / "manifest.json").read_text(encoding="utf-8"))
        lines += [f"## {folder}", "", "| file | work | source | licence |", "| --- | --- | --- | --- |"]
        for r in sorted(rows, key=lambda r: r["name"]):
            work = " · ".join(x for x in (r.get("artist"), r.get("title", "").replace("File:", ""), r.get("date")) if x)
            lines.append(f"| {r['name']} | {work} | {r['source']} | {r.get('license', '')} |")
        lines.append("")
    lines += ["## AI video", "",
              "- Salon clips (muse-m1 reversed, muse-m3, muse-m2): generated by the authors with Muse.",
              "- Scenes imagined from the paintings, generated by the authors: the windy hill with the parasol (MiniMax) and her face (Muse),",
              "  Saint-Lazare, Le Havre at dawn, the Opéra pit, the Moulin de la Galette and Sainte-Victoire (gen-*, Muse).",
              "- Dancers, made by the authors with Muse for 听得见的舞 (The Dance You Can Hear) and registered to their paintings:",
              "  Degas, The Dance Class, The Star, Rehearsal on Stage, Waiting, Dancers at the Barre, Blue Dancers;",
              "  Renoir, Dance at Bougival, Dance in the City.",
              "- Every clip is played from a copy with frames interpolated to 60 fps by ffmpeg (minterpolate).", "",
              "## music", "", "```", (PUB / "music/SOURCES.txt").read_text(encoding="utf-8").strip(), "```", ""]
    SOURCES_MD.parent.mkdir(parents=True, exist_ok=True)
    SOURCES_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    sources()
    timeline = json.loads((ROOT / "src/data/impressionism-secret.json").read_text())
    luncheon = next(c for c in timeline["cues"] if c["id"] == "im03-02")
    nudity_start = stamp(luncheon["start"] + 0.2 + 10.1266666667)
    for lang in ("zh", "en"):
        description = "\n".join([
            LEAD[lang], "", "章节" if lang == "zh" else "Chapters", *chapters(lang), "",
            NOTES[lang].format(nudity_start=nudity_start), "",
            ("画作和音乐的来源与许可：" if lang == "zh" else "Every picture's and recording's source and licence: ") + SOURCES_URL,
            MUSIC[lang], "", "Lucas Academy", "", hashtags(HASHTAGS),
        ])
        assert len(description) < 5000, f"{lang} description is {len(description)} characters"
        out = OUT / f"youtube-description.{lang}.txt"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(f"【标题 / Title】\n{TITLE[lang]}\n\n【简介 / Description】（约 {len(description)} 字符，上限 5000）\n"
                       f"{description}\n\n【标签 / Tags】\n{tag_line(TAGS[lang])}\n\n{UPLOAD}\n", encoding="utf-8")
        print(f"{out.relative_to(ROOT)}: description {len(description)} chars")


if __name__ == "__main__":
    main()
