"""好奇新世界 · 第 1 期 (001–003 回顾): the picture, block by block, against the lines of docs/weekly/001/zh-edit.md.

Two films, one shot list (owner, 2026-10-20: a Chinese film and an English film, each paced to its own voice and
showing the products in its own language). A block plays its lines one after another and shows its shots; a shot
with "at" starts when that line starts, the others share the time left evenly. A block without lines lasts "dur" s.

Clip times are seconds in the recording, or a mark of it ("pause", ["rock1", 2.6], "end"): each language has its
own recordings (captures/<lang>/<name>.json holds the marks), so the same moment lands right in both films. A
recording or page missing in captures/en or stills/en is shared from zh (Newton, the Python homework and the museum
walk are English already). "{lang}" in a path, and a {"zh": …, "en": …} value, pick the film's own.
Paths are under public/weekly/001/ (captures/ and stills/ come from capture.cjs and stills.cjs; the rest from ASSETS).
"""

# public/weekly/001/<dest> <- <source>, relative to the playground folder; copied by scripts/weekly/assets.py
ASSETS = {
    "footage/coaster.mp4": "lucas-academy-video/roller-coaster-final/final-long.mp4",
    # a few seconds of each Fun Informatics film (the whole film is on the channel)
    **{f"footage/fi{n}.{lang}.mp4": (f"lucas-academy-video-data/fun-informatics-0{n}/out/delivery/fun-informatics-0{n}.{lang}.mp4", 0, 62)
       for n in (1, 2) for lang in ("zh", "en")},
    **{f"images/{n}.jpg": f"lucasgame-academy/weekly/assets/{n}.jpg" for n in (
        "chess-citadel", "chess-pocket", "chess-orbital", "chess-wizard", "chess-perspective", "chess-duel",
        "chess-astral-citadel", "chess-holokeep", "chess-eclipse-court", "chess-eclipse-court-revised",
        "manifold", "language-bridge-film-zh", "language-bridge-film-en", "deep-space")},
}

CONCEPT = ("概念图", "Concept art")  # Weekly 001/002 show these AI concept pictures as concept art; so do we
COMEBACK = [78, 120, 1764, 840]    # the in-page chess demos, cut out of the 1920×1080 recording (shown whole)
UNDERGROUND = [78, 88, 1764, 904]


def page(name, **kw):
    return {"kind": "page", "src": f"stills/{name}.png", **kw}


def clip(name, a, b, **kw):
    return {"kind": "clip", "src": f"captures/{name}.mp4", "from": a, "to": b, **kw}


def image(name, **kw):
    return {"kind": "image", "src": f"images/{name}.jpg", **kw}


BLOCKS = [
    # ---- 开场 ----
    {"cues": ["op00-01"], "lead": 0.4, "min": 13, "shots": [
        {"kind": "clip", "src": "footage/coaster.mp4", "from": 80.0, "to": 83.2},
        clip("avi", ["float", 0.2], ["float", 3.4]),
        clip("underground", ["rock1", -0.6], ["rock1", 2.6], crop=UNDERGROUND),
        clip("atelier", ["study5", 1.6], ["study5", 4.8]),
    ]},
    {"dur": 4.2, "shots": [{"kind": "title"}]},
    {"cues": ["op00-02", "op00-03"], "shots": [
        page("w003-questions"),
        {**page("w001-hero"), "at": "op00-03"},
        page("w002-hero"),
        page("w003-hero"),
    ]},

    # ---- 一 · 走进一座博物馆 ----
    {"dur": 3.4, "shots": [{"kind": "chapter", "n": "一", "zh": "走进一座博物馆", "en": "A museum you can walk into"}]},
    {"cues": ["mu01-01"], "shots": [page("w001-museum")]},
    {"cues": ["mu01-02", "mu01-03", "mu01-04"], "min": 52, "hold": {"mu01-02": 3.0, "mu01-03": 9.0}, "shots": [
        clip("van-gogh-room", 0.0, 51.0, label=("梵高房间", "The Van Gogh room"), keys=[["mu01-03", 15.0], ["mu01-04", 30.0]]),
    ]},
    {"cues": ["mu01-05"], "shots": [image("manifold", label=("Manifold 房间", "The Manifold"))]},
    {"cues": ["mu01-06", "mu01-07", "mu01-08"], "min": 30, "shots": [
        {"kind": "clip", "src": "footage/coaster.mp4", "from": 0.6, "to": 4.6},
        {"kind": "clip", "src": "footage/coaster.mp4", "from": 23.4, "to": 27.4},
        {"kind": "clip", "src": "footage/coaster.mp4", "from": 50.0, "to": 56.0, "at": "mu01-07"},
        {"kind": "clip", "src": "footage/coaster.mp4", "from": 76.0, "to": 89.5, "at": "mu01-08", "label": ("Golden Funnel", "Golden Funnel")},
    ]},
    {"cues": ["mu01-09", "mu01-10", "mu01-11"], "min": 30, "hold": {"mu01-10": 4.0}, "shots": [
        clip("avi", 0.0, "float", label=("太空宝宝 Avi", "Space Baby Avi")),
        {**clip("avi", "float", "end"), "at": "mu01-11"},
    ]},
    {"cues": ["mu01-12", "mu01-13"], "lead": 0.3, "min": 50, "shots": [
        page("w001-atelier"),
        clip("atelier", ["study1", 0.5], ["study1", 9.5], label=("五件三维作品", "Five 3D studies")),
        clip("atelier", ["study2", 0.9], ["study2", 9.9]),
        clip("atelier", ["study3", 1.0], ["study3", 10.0]),
        clip("atelier", ["study4", 1.2], ["study4", 10.2]),
        clip("atelier", ["study5", 0.6], "end"),
    ]},

    # ---- 二 · 熟悉的棋，新的规则 ----
    {"dur": 3.4, "shots": [{"kind": "chapter", "n": "二", "zh": "熟悉的棋，新的规则", "en": "A familiar game, new rules"}]},
    {"cues": ["ch02-01"], "shots": [page("w001-ideas")]},
    {"cues": ["ch02-02"], "shots": [image("chess-perspective", tag=CONCEPT)]},
    {"cues": ["ch02-03"], "min": 16, "shots": [
        image("chess-citadel", tag=CONCEPT), image("chess-pocket", tag=CONCEPT),
        image("chess-orbital", tag=CONCEPT), image("chess-wizard", tag=CONCEPT),
    ]},
    {"cues": ["ch02-04", "ch02-05"], "shots": [page("w001-balance")]},
    {"cues": ["ch02-06"], "shots": [image("chess-duel", tag=CONCEPT)]},
    {"cues": ["ch02-07", "ch02-08"], "min": 28, "shots": [
        page("w002-chess-design"),
        image("chess-eclipse-court", tag=CONCEPT),
        {**image("chess-eclipse-court-revised", tag=CONCEPT), "at": "ch02-08"},
        clip("pieces", ["launch", 1.7], "end", label=("三维棋子", "3D pieces")),
    ]},
    {"cues": ["ch02-09", "ch02-10"], "min": 42, "hold": {"ch02-09": 9.0}, "shots": [
        page("w002-chess"),
        # one take: the bots play fast, and the game pauses for a comeback just as the line explains it
        {**clip("comeback", ["play", 5.0], "end", crop=COMEBACK, label=("Comeback 复活规则", "The Comeback rule"), keys=[["ch02-10", ["pause", -0.5]]]), "at": ["ch02-09", 2.4]},
    ]},
    {"cues": ["ch02-11", "ch02-12", "ch02-13"], "min": 30, "hold": {"ch02-12": 4.0}, "shots": [
        page("w003-chess"),
        {**clip("underground", "play", "end", crop=UNDERGROUND, label=("Underground 落石", "Underground")), "at": "ch02-12"},
    ]},
    {"cues": ["ch02-14"], "shots": [page("w001-rules")]},

    # ---- 三 · 读经文，学语言 ----
    {"dur": 3.4, "shots": [{"kind": "chapter", "n": "三", "zh": "读经文，学语言", "en": "Reading Scripture, learning languages"}]},
    {"cues": ["wd03-01", "wd03-02", "wd03-03"], "min": 26, "shots": [
        clip("bible-sequence", 0.0, "end", label=("Bible Sequence", "Bible Sequence"), keys=[["wd03-02", "recall"]]),
    ]},
    {"cues": ["wd03-04"], "min": 14, "shots": [page("w003-wordplay"), clip("sentence-chars", 1.0, "segment@0")]},
    {"cues": ["wd03-05"], "min": 30, "shots": [clip("sentence-chars", "segment@0", ["done", 0.8], label=("接字", "Characters"))]},
    {"cues": ["wd03-06"], "min": 30, "shots": [clip("sentence-words", "segment@0", ["done", 0.8], label=("接词", "Words"))]},
    {"cues": ["wd03-07", "wd03-08"], "shots": [
        page("w001-doors"),
        {**image("language-bridge-film-{lang}", film=("语言的桥 · 你教我，我教你", "Language Bridge · You teach me, I teach you")), "at": "wd03-08"},
    ]},
    {"cues": ["wd03-09"], "min": 12, "shots": [clip("lang-class", 0.0, "journal", label=("语言的桥 · 课堂", "Language Bridge · the classroom"))]},
    {"cues": ["wd03-10", "wd03-11"], "min": 23, "shots": [
        page("w003-journal"),
        clip("lang-class", "journal", "end", label=("周记 · 第一期", "Weekly Journal · No. 1")),
    ]},

    # ---- 四 · 编程课 ----
    {"dur": 3.4, "shots": [{"kind": "chapter", "n": "四", "zh": "编程课", "en": "Coding class"}]},
    {"cues": ["cd04-01"], "shots": [page("w002-coding")]},
    {"cues": ["cd04-02"], "shots": [page("w002-coding-rainbow", source="leetcode4kids.com")]},
    {"cues": ["cd04-03", "cd04-04"], "min": 40, "hold": {"cd04-04": 6.0}, "shots": [
        page("w002-coding-body"),
        {**clip("glitch-arcade", 0.0, "end", label=("Glitch Arcade · 第 04 台", "The Glitch Arcade · cabinet 04")), "at": "cd04-04"},
    ]},
    {"cues": ["cd04-05", "cd04-06"], "min": 24, "shots": [
        page("w003-coding"),
        {**clip("score-homework", 1.0, 20.2, label=("Python 作业", "Python homework")), "at": "cd04-06"},
    ]},

    # ---- 五 · 还有更多可能 ----
    {"dur": 3.4, "shots": [{"kind": "chapter", "n": "五", "zh": "还有更多可能", "en": "More possibilities"}]},
    {"cues": ["mr05-01"], "shots": [page("w002-possibilities")]},
    {"cues": ["mr05-02", "mr05-03"], "min": 44, "hold": {"mr05-02": 3.0}, "shots": [
        page("w002-brainstorm"),
        {**clip("newton", 0.0, 39.4, label=("牛顿 + AI", "Newton + AI")), "at": "mr05-03"},
    ]},
    {"cues": ["mr05-04"], "min": 14, "shots": [
        {"kind": "film", "src": "footage/fi1.{lang}.mp4", "from": 5.5, "to": 11.5, "film": ("计算机怎么算 1+1=？", "How does a computer add 1 + 1?")},
        {"kind": "film", "src": "footage/fi2.{lang}.mp4", "from": {"zh": 53.5, "en": 49.0}, "to": {"zh": 59.5, "en": 55.0}, "film": ("你认识 Claude 吗？", "Do you know Claude?")},
    ]},
    {"cues": ["mr05-05", "mr05-06"], "shots": [page("w003-bio")]},

    # ---- 六 · 你的想法 ----
    {"dur": 3.4, "shots": [{"kind": "chapter", "n": "六", "zh": "你的想法", "en": "Your idea"}]},
    {"cues": ["yi06-01", "yi06-02", "yi06-03"], "hold": {"yi06-02": 2.0}, "shots": [page("w001-matthew")]},
    {"cues": ["yi06-04"], "shots": [page("w001-submit")]},
    {"cues": ["yi06-05"], "shots": [page("w003-questions")]},
    {"cues": ["yi06-06"], "lead": 0.8, "pad": 3.0, "shots": [{"kind": "question",
        "zh": "如果你的小想法真的做出来了，\n你最想先请谁来试一试？",
        "en": "If your small idea were real one day,\nwho would you invite to try it first?"}]},
    {"dur": 6.0, "shots": [{"kind": "end"}]},
]

# What the voices read where it differs from the captions (the captions keep the script's words).
SPOKEN = {
    "zh": {"xy 坐标": "X Y 坐标", "3D": "三D", "2D": "二D"},
    "en": {"x-y plane": "x y plane", "3D": "three-D", "2D": "two-D", "1666": "sixteen sixty-six",
           "John 3:16": "John three sixteen", "Möbius": "Mobius",
           # retakes after the Whisper check: heard "Enjoying is the door", "a cell rep"
           "Drawing is the door": "Drawing, is the door", "Biology: a Cell Rap.": "Biology: a cell rap!"},
}

# The episode's music bed (a new piece can come each week). Draft: the owner's Suno song "One Breath", the
# remastered instrumental (without lead vocal), 5:13, looped under the film.
MUSIC = {"src": "lucas-academy-video/public/audio/songs/one-breath-remaster-instrumental.mp3", "start": 0}
