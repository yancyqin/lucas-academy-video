"""Upload texts for 小星星的莫扎特画本 (the Mozart sketchbook film) -> DATA/package/youtube-description.txt

    python sketchbook_youtube.py

Bach-suite layout: 【中文标题】【English title】【中文简介】【English description】【标签 / Tags】【上传设置】. The chapters
come from the assembled film's chapters.json and the recording credits from music/sources.json (Twinkle from the Renzi
lines), so both follow the film. Every CC BY recording gets title, performer, source link, its own licence link and the
change made (volume only). Tags and hashtags from scripts/youtube_tags.py.
"""
import json
import pathlib
import sys
import urllib.parse

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from youtube_tags import hashtags, tags  # noqa: E402

DATA = pathlib.Path("/Users/yqin/repo/playground/lucas-academy-video-data/mozart-sketchbook")
FILM = "小星星的莫扎特画本.mp4"
CHAPTERS = DATA / "film/mozart-sketchbook-v2.chapters.json"
RENZI = "https://commons.wikimedia.org/wiki/File:Mozart_-_12_Variations_K._265_-_Simone_Renzi.mp3"
DE_BRA = "https://imslp.org/wiki/Eine_kleine_Nachtmusik,_K.525_(Mozart,_Wolfgang_Amadeus)"     # file #869387 is listed here

TITLE_ZH = "小星星的莫扎特画本｜跟着莫扎特画画：费加罗、魔笛、第40号交响曲、弦乐小夜曲、小星星变奏曲"
TITLE_EN = "Little Star's Mozart Sketchbook | Drawing to Figaro, The Magic Flute, Symphony No. 40 & More"

INTRO_ZH = ("莫扎特的十首曲子，一本画本。从早上到夜里，54 幅画跟着音乐一笔一笔画出来，每首换一种画法（见下面的章节）。"
            "每幅画有自己的主角（小老鼠、小刺猬、王子和捕鸟人、动物乐队……），"
            "一颗小黄星星藏在每一幅里，找找它在哪儿；到了《小星星变奏曲》，它自己当主角。没有旁白，只有音乐。")
INTRO_EN = ("Ten pieces by Mozart, one sketchbook. From morning to night, 54 pictures are drawn stroke by stroke to the music, "
            "each piece in its own medium (see the chapters). Every picture has its "
            "own characters (mice, a hedgehog, a prince and a bird-catcher, an animal band…), and a little yellow star hides in each one. Can you find it? In the Twinkle "
            "Variations, the star takes the lead. No narration, only the music.")
HOW_ZH = ("怎么画：先打稿或勾线，再一块一块上颜色，每一笔都落在音乐的节拍上；一幅画完停几秒，画里的星星跟着节拍闪一闪，"
          "再换下一张纸。书桌上的光也从早上换到夜里。")
HOW_EN = ("How it's drawn: the sketch or outlines first, then the colour patch by patch, every stroke on the beat; when a "
          "picture is done, its stars twinkle in time before the next sheet comes in. The desk light moves from morning to night.")

# key: (zh piece, en piece, zh medium, en medium, zh story, en story)
PIECES = {
    "05": ("《费加罗的婚礼》序曲 K.492", "The Marriage of Figaro, K. 492: Overture", "马克笔", "marker",
           "小老鼠们的婚礼日", "The mice's wedding day"),
    "20": ("F 大调嬉游曲 K.138 · 第一乐章", "Divertimento in F, K. 138: I. Allegro", "水彩", "watercolour",
           "小刺猬的上午花园", "A hedgehog's morning garden"),
    "06": ("《魔笛》序曲 K.620", "The Magic Flute, K. 620: Overture", "水粉", "gouache",
           "王子、捕鸟人和魔笛", "The prince, the bird-catcher and the magic flute"),
    "10": ("《大组曲》K.361 · 终曲", "Gran Partita, K. 361: VII. Finale", "油画棒", "oil pastel",
           "动物管乐队游行", "The animal wind band's parade"),
    "16": ("A 大调单簧管协奏曲 K.622 · 回旋曲", "Clarinet Concerto in A, K. 622: III. Rondo", "彩铅", "coloured pencil",
           "小狐狸和小兔子捉迷藏", "Hide-and-seek with a fox and a bunny"),
    "01": ("g 小调第40号交响曲 K.550 · 第一乐章", "Symphony No. 40 in G minor, K. 550: I. Molto allegro", "油画", "oil paint",
           "大风的傍晚，红帽子小女孩回家", "A windy evening: a girl in a red hat heads home"),
    "27": ("《弦乐小夜曲》K.525（手风琴版，全曲）", "Eine kleine Nachtmusik, K. 525 (accordions, complete)", "钢笔淡彩",
           "pen and wash", "小熊手风琴乐队的晚上", "An evening with the accordion bears"),
    "17": ("《小星星变奏曲》K.265（全曲）", "Twinkle Variations, K. 265 (complete)", "蜡笔", "crayon",
           "小星星自己的夜晚：主题和 12 段变奏", "Little Star's own night: the theme and 12 variations"),
    "15": ("单簧管协奏曲 K.622 · 柔板", "Clarinet Concerto, K. 622: II. Adagio", "色粉", "soft pastel",
           "小男孩的摇篮曲", "A lullaby for a little boy"),
    "07": ("《大组曲》K.361 · 柔板", "Gran Partita, K. 361: III. Adagio", "彩墨", "Chinese ink and colour",
           "夜深了，湖边", "Late at night by the lake"),
}

# who plays, in each language; the licence and link come from sources.json
PLAYERS = {
    "musopen": ("Musopen Symphony（2012）", "Musopen Symphony (2012)"),
    "marines": ("美国海军陆战队乐队（United States Marine Band，2021）", "United States Marine Band (2021)"),
    "krumpoeck": ("Markus Krumpöck（单簧管），Merkur Orchester Wiener Neustadt，Willibald Zwittkovits 指挥（1999 现场）",
                  "Markus Krumpöck (clarinet), Merkur Orchester Wiener Neustadt, cond. Willibald Zwittkovits (live, 1999)"),
    "tsumugi": ("管弦乐团紬（Tsumugi Orchestra），井上京指挥（2010 现场）",
                "The Tsumugi Orchestra, conducted by Takashi Inoue (live, 2010)"),
    "debra": ("Paul De Bra（Professor P）改编并演奏（一个人多轨录四台手风琴和低音手风琴，2023；他的录音省略了部分反复）",
              "arranged and played by Paul De Bra, “Professor P” (4 accordions + bass accordion, multitracked, 2023; "
              "some repeats omitted)"),
    "renzi": ("Simone Renzi（钢琴）", "Simone Renzi (piano)"),
}
PLAYED_BY = {"01": "musopen", "05": "musopen", "06": "musopen", "07": "marines", "10": "marines", "15": "krumpoeck",
             "16": "krumpoeck", "20": "tsumugi", "27": "debra", "17": "renzi"}
CC = {"CC BY 2.5": "https://creativecommons.org/licenses/by/2.5/", "CC BY 3.0": "https://creativecommons.org/licenses/by/3.0/",
      "CC BY 4.0": "https://creativecommons.org/licenses/by/4.0/"}
CHANGES_ZH = "改动：每首只调整了音量（增益和限幅），都是整首，没有剪。作曲是公有领域（莫扎特 1791 年去世）。"
CHANGES_EN = ("Changes: volume only (gain and a limiter); every recording is used in full. The compositions are in the public "
              "domain (Mozart died in 1791).")

AI_ZH = ("关于画面：54 幅画、书桌和画笔都是 AI 生成的图（Codex 图像生成）。画画的过程不是录下来的，是我们写的程序把每幅画"
         "拆成一笔一笔，跟着音乐的节拍画出来。")
AI_EN = ("About the images: the 54 pictures, the desks and the tools are AI-generated (Codex image generation). The drawing "
         "is not a recording: our own program takes each picture apart stroke by stroke and draws it to the beat.")
BYLINE_ZH, BYLINE_EN = "作者 Yancy Qin | Lucas Academy", "By Yancy Qin | Lucas Academy"

OWN_HASHTAGS = ["mozart", "classicalmusic", "musicforkids", "kidsart", "twinklevariations", "drawing"]
OWN_TAGS = ["小星星的莫扎特画本", "莫扎特", "小星星变奏曲", "费加罗的婚礼", "魔笛", "第40号交响曲", "弦乐小夜曲", "单簧管协奏曲",
            "古典音乐", "给孩子的古典音乐", "儿童画", "mozart", "mozart for kids", "classical music for kids",
            "marriage of figaro overture", "magic flute overture", "symphony no 40", "eine kleine nachtmusik",
            "clarinet concerto k 622", "gran partita", "twinkle variations", "drawing to music", "kids drawing", "watercolor"]


def link(url):
    """A link YouTube's autolinker keeps whole: quotes, parentheses and non-ASCII percent-encoded."""
    head, path = url.split("/wiki/", 1)
    return head + "/wiki/" + urllib.parse.quote(urllib.parse.unquote(path), safe=":_,-.")


def stamp(sec):
    sec = int(sec)
    h, m, s = sec // 3600, sec // 60 % 60, sec % 60
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def credits():
    """One line per piece in film order, zh and en (piece — players — licence — source), then each CC licence's link once."""
    src = json.loads((DATA / "music/sources.json").read_text())
    src["17"] = {"license": "CC BY 3.0", "page": RENZI}
    src["27"] = {**src["27"], "page": DE_BRA}
    zh, en = [], []
    for c in json.loads(CHAPTERS.read_text()):
        k = c["key"]; r = src[k]; p = PIECES[k]; who = PLAYERS[PLAYED_BY[k]]
        lic = next((name for name in CC if r["license"].startswith(name)), None)
        page = link(r["page"]) + (" （IMSLP #869387）" if k == "27" else "")
        page_en = link(r["page"]) + (" (IMSLP #869387)" if k == "27" else "")
        if lic:
            zh.append(f"· {p[0]} — {who[0]} — {lic} — {page}")
            en.append(f"· {p[1]} — {who[1]} — {lic} — {page_en}")
        else:
            why_zh = "公有领域（美国政府作品）" if PLAYED_BY[k] == "marines" else "公有领域"
            why_en = "public domain (US government work)" if PLAYED_BY[k] == "marines" else "public domain"
            zh.append(f"· {p[0]} — {who[0]} — {why_zh} — {page}")
            en.append(f"· {p[1]} — {who[1]} — {why_en} — {page_en}")
    zh.append("授权链接：" + " · ".join(f"{name} {url}" for name, url in CC.items()))
    en.append("Licences: " + " · ".join(f"{name} {url}" for name, url in CC.items()))
    return zh, en


def main():
    chapters = json.loads(CHAPTERS.read_text())
    assert chapters[0]["t"] == 0 and len(chapters) >= 3
    assert all(b["t"] - a["t"] >= 10 for a, b in zip(chapters, chapters[1:]))
    chap_zh = [f"{stamp(c['t'])} {PIECES[c['key']][0]} · {PIECES[c['key']][2]} · {PIECES[c['key']][4]}" for c in chapters]
    chap_en = [f"{stamp(c['t'])} {PIECES[c['key']][1]} · {PIECES[c['key']][3]} · {PIECES[c['key']][5]}" for c in chapters]
    music_zh, music_en = credits()
    tail = hashtags(OWN_HASHTAGS)
    zh = "\n".join([INTRO_ZH, "", HOW_ZH, "", *chap_zh, "", "—— 音乐 ——", *music_zh, CHANGES_ZH, "", AI_ZH, "",
                    BYLINE_ZH, "", tail])
    en = "\n".join([INTRO_EN, "", HOW_EN, "", *chap_en, "", "—— Music ——", *music_en, CHANGES_EN, "", AI_EN, "",
                    BYLINE_EN, "", tail])
    upload = f"""【上传设置 / Upload settings】
· 一个视频：{FILM}（1920×1080，30 fps，1:11:44；没有旁白也没有字幕，中英文共用）
· 视频语言：中文；标题、简介用【中文标题】【中文简介】；再到「字幕」→「添加语言」→ 英语 → 「标题和说明」，填【English title】【English description】
· 章节：简介里 10 个时间点（第一个是 0:00，每段都远超 10 秒），YouTube 会自动分章
· 封面（1280×720）：youtube-cover.zh.jpg 作主封面；英文版 youtube-cover.en.jpg 可放进「测试和比较」或留作英文封面
· 字幕：无
· Altered or synthetic content（经过修改或合成的内容）：是 —— 书桌和画笔是看起来像真实照片的 AI 生成图，54 幅画也是 AI 生成的
· 观众：由你决定；选「专为儿童打造」会关掉评论和个性化广告
· 类别：Education（或 Music）
· Content ID：小星星那段（Renzi 的录音，{stamp(next(c['t'] for c in chapters if c['key'] == '17'))} 起）在《小星星变奏曲》短片上被误认过；如果又被认领，申诉文字在 lucas-academy-video-data/twinkle-stars/content-id-dispute.txt（理由选 License）。其他录音是公有领域或 CC BY，被认领时同样申诉"""
    doc = ["【中文标题】", TITLE_ZH, "", "【English title】", TITLE_EN, "", "【中文简介】", zh, "",
           "【English description】", en, "", "【标签 / Tags】", tags(OWN_TAGS), "", upload, ""]
    for name, t, d in (("zh", TITLE_ZH, zh), ("en", TITLE_EN, en)):
        print(f"{name}: title {len(t)} chars, description {len(d)} chars / {len(d.encode())} bytes (limits 100 / 5000)")
        assert len(t) <= 100 and len(d.encode()) <= 5000 and "<" not in t + d and ">" not in t + d   # counted in bytes, the stricter reading
    out = DATA / "package"; out.mkdir(exist_ok=True)
    (out / "youtube-description.txt").write_text("\n".join(doc))
    print(out / "youtube-description.txt", f"· tags {len(tags(OWN_TAGS))} chars")


if __name__ == "__main__":
    main()
