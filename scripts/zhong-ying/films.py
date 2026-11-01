"""The 中英阅读 films (ZHONG-YING.md): which lessons, which works, where everything lives.

Each film is one lesson of 语言的桥's 看得见的诗 (lucas-academy-lang) read aloud with the narration the lesson
already has: every verse once in Chinese (Fangfang) and then once in English (Louise), verse by verse. Each work
of the lesson is painted with its art-lab living painting (lucas-visual-art-lab, living.html): the Chinese reading
paints the picture onto blank paper stroke by stroke, the English reading adds living brushes to it.
"""
from __future__ import annotations

import json
import os
import pathlib
import subprocess

REPO = pathlib.Path(__file__).resolve().parents[2]


def _playground() -> pathlib.Path:
    """The folder holding the sibling repositories (the video repo may be a worktree several levels down)."""
    for parent in REPO.parents:
        if (parent / "lucas-academy-lang").is_dir():
            return parent
    raise SystemExit("lucas-academy-lang not found next to this repository")


PLAYGROUND = _playground()
# A lesson not yet merged lives in a lang worktree: ZHONG_YING_LANG points there (e.g. ../lucas-academy-lang-beauty).
LANG = pathlib.Path(os.environ.get("ZHONG_YING_LANG", PLAYGROUND / "lucas-academy-lang"))
MEDIA = PLAYGROUND / "lucas-academy-media"
DATA = PLAYGROUND / "lucas-academy-video-data" / "zhong-ying"
PUBLIC = REPO / "public" / "zhong-ying"
FPS = 30

# The intro line, spoken over the title card in both voices (owner, 2026-10-26).
INTRO = {
    "zh": "学习/语言/最好/的/方式/是/朗读/。/\n/不论/你/是/想/学/中文/还是/英文/，/跟/我们/一起/读/吧/。",
    "en": "The best way to learn a language is to read it aloud.\nWhether you want to learn Chinese or English, read along with us.",
}


def intro_words(lang: str) -> list[str]:
    """The intro as it lights up on screen ("\\n" is a line break)."""
    if lang == "zh":
        return INTRO["zh"].split("/")
    out = []
    for i, line in enumerate(INTRO["en"].split("\n")):
        out += (["\n"] if i else []) + line.split()
    return out


def intro_spoken(lang: str) -> str:
    return "".join(w for w in intro_words(lang) if w != "\n") if lang == "zh" else INTRO["en"].replace("\n", " ")

# Every film's last line, read on the end card after the closing (owner, 2026-10-28: wording B of three proposed),
# in the intro's voices so the series opens and closes with the same two.
SUBSCRIBE = {"zh": "喜欢的话，请订阅，也在留言里告诉我们你最喜欢哪一句。下次见！",
             "en": "If you enjoyed it, subscribe, and tell us in the comments which line you liked best. See you next time!"}

# Per film: its works (each with the title and author as shown, and "say", the title and author as read aloud before
# the work's first verse — owner, 2026-10-27; dates and Bible versions stay on screen only) and "closing", the
# owner's one or two lines read after the last work.
FILMS: dict[str, dict] = {
    "climb-higher": {
        "title": {"zh": "爬高一点，看远一点", "en": "Climb Higher, See Farther"},
        "closing": {"zh": "诗人爬上一层楼，孩子爬上樱桃树，都想看得更远。是什么样的心，才能让我们看得更远呢？",
                    "en": "The poet climbed one floor higher, the child climbed the cherry tree; both wanted to see "
                          "farther. What kind of heart lets us see farther?"},
        "works": [
            {"id": "deng-guanque-lou", "units": [1, 2], "style": "ink",
             "title": {"zh": "登鹳雀楼", "en": "On the Stork Tower"}, "by": {"zh": "唐 · 王之涣", "en": "Wang Zhihuan · Tang dynasty"},
             "say": {"zh": "登鹳雀楼。唐，王之涣。", "en": "On the Stork Tower, by Wang Zhihuan, Tang dynasty."}},
            {"id": "foreign-lands", "units": [3, 4, 5, 6], "style": "oil",
             "title": {"zh": "外面的世界", "en": "Foreign Lands"}, "by": {"zh": "斯蒂文森 · 1885", "en": "Robert Louis Stevenson · 1885"},
             "say": {"zh": "外面的世界。斯蒂文森。", "en": "Foreign Lands, by Robert Louis Stevenson."}},
            {"id": "psalm-121", "units": [7, 8], "style": "watercolour",
             "title": {"zh": "诗篇 121:1–2", "en": "Psalm 121:1–2"}, "by": {"zh": "圣经 · 和合本", "en": "The Bible · NIV"},
             "say": {"zh": "诗篇第一百二十一篇，第一到二节。", "en": "Psalm 121, verses 1 and 2."}},
        ],
    },
    "little-boats": {
        "title": {"zh": "小船去远方", "en": "Little Boats, Far Away"},
        "closing": {"zh": "小船漂向远方，不知道会被谁捞上岸。走远路的人不必害怕：等候耶和华的，必从新得力。",
                    "en": "Little boats float far away, not knowing who will bring them ashore. On a long road, we "
                          "need not fear: those who hope in the Lord will renew their strength."},
        "works": [
            {"id": "zao-fa-baidi", "units": [1, 2], "style": "ink",
             "title": {"zh": "早发白帝城", "en": "Leaving Baidi at Dawn"}, "by": {"zh": "唐 · 李白", "en": "Li Bai · Tang dynasty"},
             "say": {"zh": "早发白帝城。唐，李白。", "en": "Leaving Baidi at Dawn, by Li Bai, Tang dynasty."}},
            {"id": "where-go-the-boats", "units": [3, 4, 5, 6], "style": "oil",
             "title": {"zh": "小船漂到哪里去？", "en": "Where Go the Boats?"}, "by": {"zh": "斯蒂文森 · 1885", "en": "Robert Louis Stevenson · 1885"},
             "say": {"zh": "小船漂到哪里去？斯蒂文森。", "en": "Where Go the Boats? By Robert Louis Stevenson."}},
            {"id": "isaiah-40-31", "units": [7], "style": "watercolour",
             "title": {"zh": "以赛亚书 40:31", "en": "Isaiah 40:31"}, "by": {"zh": "圣经 · 和合本", "en": "The Bible · NIV"},
             "say": {"zh": "以赛亚书第四十章，第三十一节。", "en": "Isaiah, chapter 40, verse 31."}},
        ],
    },
    "can-beauty-last": {
        "title": {"zh": "美好能否留存？", "en": "Can Beauty Last?"},
        "lesson_voices": True,   # Sunny and Matthew voiced the lesson itself (lesson_voice.py); narration.py voices none of it
        # …except these, which the series voices read (Fangfang, Louise). Owner, 2026-10-29: Sunny's voice cracked on
        # the titles; the closing over the 回顾 is Fangfang's and Louise's, as in the other films.
        "series_voices": {"zh": ("titles", "closing"), "en": ("closing",)},
        # Draft (2026-10-27): the owner words the closing; until then this is a placeholder to time the film with.
        "closing": {"zh": "好雨按着时节来，夏天却过得太快。诗人把美好写进诗里，神把永远放在我们心里。什么样的美好，会一直留下来呢？",
                    "en": "The good rain comes in its season, and summer passes too soon. The poet wrote beauty into "
                          "his lines; God set eternity in our hearts. What kind of beauty lasts?"},
        "works": [
            {"id": "chun-ye-xi-yu", "units": [1, 2, 3, 4], "style": "ink",
             "title": {"zh": "春夜喜雨", "en": "Happy Rain on a Spring Night"}, "by": {"zh": "唐 · 杜甫", "en": "Du Fu · Tang dynasty"},
             "say": {"zh": "春夜喜雨。唐，杜甫。", "en": "Happy Rain on a Spring Night, by Du Fu, Tang dynasty."}},
            {"id": "sonnet-18", "units": [5, 6, 7, 8, 9, 10, 11], "style": "oil",
             "title": {"zh": "第十八首十四行诗", "en": "Sonnet 18"}, "by": {"zh": "莎士比亚 · 1609", "en": "William Shakespeare · 1609"},
             "say": {"zh": "第十八首十四行诗。莎士比亚。", "en": "Sonnet 18, by William Shakespeare."}},
            {"id": "ecclesiastes-3-11", "units": [12], "style": "watercolour",
             "title": {"zh": "传道书 3:11", "en": "Ecclesiastes 3:11"}, "by": {"zh": "圣经 · 和合本", "en": "The Bible · NIV"},
             "say": {"zh": "传道书第三章，第十一节。", "en": "Ecclesiastes, chapter 3, verse 11."}},
        ],
    },
}

RECORDED = ("sunny", "matthew")  # people's readings: Sunny's Chinese (sunny_voice.py), Matthew's English (matthew_voice.py)


def clip(film: str, unit: int, lang: str) -> pathlib.Path:
    """A verse's voice: a person's recording when there is one (RECORDED), else the series' AI take at speed 1.0
    (narration.py) once chosen, else the lesson's published clip (read at 0.75; the first cut)."""
    for who in RECORDED:
        own = DATA / "narration" / who / lang / f"{film}-v{unit:02d}.wav"
        if own.exists():
            return own
    chosen = DATA / "narration" / "verses" / "chosen.json"
    picks = json.loads(chosen.read_text()) if chosen.exists() else {}
    if f"{lang}/{film}-v{unit:02d}" in picks:
        return chosen.parent / lang / f"{picks[f'{lang}/{film}-v{unit:02d}']['take']}.wav"
    # A lesson voiced for the series from the start (can-beauty-last: Sunny and Matthew, lesson_voice.py) uses its
    # own published clips.
    return LANG / "public" / "audio" / film / lang / f"v{unit:02d}-whole.mp3"


def extra(line_id: str, lang: str) -> pathlib.Path:
    """The chosen take of a title (<work id>-title) or a closing (<film>-closing) line (narration.py extras), or, for
    a film whose lesson was voiced for the series (lesson_voices) and a line the series voices don't read
    (series_voices), the take lesson_voice.py picked in its readers' voices (narration.py lesson-extras)."""
    chosen = DATA / "narration" / "extras" / "chosen.json"
    picks = json.loads(chosen.read_text())
    if f"{lang}/{line_id}" in picks:
        return chosen.parent / lang / f"{picks[f'{lang}/{line_id}']['take']}.wav"
    return DATA / "narration" / "lesson-extras" / lang / f"{line_id}.wav"


def texts(film: str) -> list[dict]:
    """The lesson's units: lang's word tokens and English, plus the narrated text of both languages.

    The narrated text comes from lucas-academy-media's narration scripts (data/processed/lucas-lang, git-ignored
    there); for scripture it is the only place the English (NIV) exists outside lang's Worker.
    """
    units = json.loads(subprocess.run(["node", str(REPO / "scripts/zhong-ying/texts.mjs"), str(LANG), film],
                                      capture_output=True, text=True, check=True).stdout)
    for lang in ("zh", "en"):
        own = DATA / "lang" / film / f"{film}-{lang}.json"           # lesson_voice.py's scripts (can-beauty-last)
        source = own if own.exists() else MEDIA / "data/processed/lucas-lang" / f"{film}-{lang}.json"
        lines = json.loads(source.read_text())["lines"]
        spoken = {int(line["verseId"].split(".")[-1]): line["text"] for line in lines if line["unitId"] == "whole"}
        for unit in units:
            unit[f"spoken_{lang}"] = spoken[unit["n"]]
    return units
