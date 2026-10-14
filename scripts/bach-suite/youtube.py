"""YouTube titles, descriptions, tags and upload settings -> DATA/build/youtube-description.txt

One video (no narration, no subtitles) with a Chinese title + description and an English
translation of both for Studio → Languages. Chapters come from build/timings.json; the credits the
licences require (CC BY music and images, the Jesu section's own credits) come from the source
lists, so they follow the edit. Tags follow the channel rule in scripts/youtube_tags.py.
"""
import importlib.util
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).parent
ROOT = HERE.parent.parent
EDIT = json.loads((HERE / "edit.json").read_text())
DATA = pathlib.Path(EDIT["data"])
sys.path.insert(0, str(ROOT / "scripts"))
from youtube_tags import hashtags, tags  # noqa: E402


def jesu_module():
    """The Jesu film's own description module: its CC BY lines, Pexels names and public sources."""
    sys.path.insert(0, str(ROOT / "scripts/jesu"))
    spec = importlib.util.spec_from_file_location("jesu_youtube", ROOT / "scripts/jesu/youtube.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


TITLE_ZH = "巴赫精选｜看得见的音乐：C大调前奏曲 · 大提琴前奏曲 · 加沃特 · G弦上的咏叹调 · 耶稣，世人仰望的喜悦"
TITLE_EN = "The Best of Bach, Illustrated | Prelude in C · Cello Suite No. 1 · Gavotte · Air · Jesu, Joy"

INTRO_ZH = ("巴赫最常被听到的五首曲子，每一首配一段画面：城市的一天、边走边想的艺术史、玩耍的小动物、从午后到黑夜的光，"
            "最后是从创世到再来。其中四首也出现在动画《新世纪福音战士》（EVA）里。没有旁白，只有音乐。")
INTRO_EN = ("Five of Bach's best-loved pieces, each with its own pictures: a city's day, a walk through art history, "
            "animals at play, light from afternoon to night, and finally creation to the return of Christ. "
            "Four of them are also heard in Neon Genesis Evangelion. No narration, only the music.")

# id -> (zh chapter, en chapter)
CHAPTERS = {
    "prelude": ("C 大调前奏曲 BWV 846 · 城市的一天：黎明出发，行色匆匆，黄昏回家",
                "Prelude in C major, BWV 846 · A city's day: out at dawn, the rush, home at dusk"),
    "cello": ("第一大提琴组曲 · 前奏曲 BWV 1007 · 边走边想：从古希腊到文艺复兴",
              "Cello Suite No. 1, Prelude, BWV 1007 · Thinking while walking: from ancient Greece to the Renaissance"),
    "gavotte": ("E 大调第三号无伴奏小提琴组曲 · 加沃特回旋曲 BWV 1006 · 玩耍",
                "Violin Partita No. 3, Gavotte en Rondeau, BWV 1006 · Play"),
    "air": ("D 大调第三号管弦乐组曲 · G 弦上的咏叹调 BWV 1068 · 光：从午后到黑夜",
            "Orchestral Suite No. 3, Air (on the G String), BWV 1068 · Light, from afternoon into night"),
    "jesu": ("耶稣，世人仰望的喜悦 BWV 147 · 从创世到再来",
             "Jesu, Joy of Man's Desiring, BWV 147 · From creation to his return"),
}

ART_ZH = ("第二首里的作品（按年代）：《沉思的雅典娜》浮雕（约公元前 460）· 庞贝《柏拉图学园》马赛克（公元前 1 世纪）· "
          "乔托《约阿希姆在牧羊人中》（1305）· 米开利诺《但丁与神曲》（1465）· 安托内罗《书房里的圣哲罗姆》（1475）· "
          "博斯《旅人》（约 1500）· 乔尔乔内《三位哲学家》（约 1509）· 拉斐尔《雅典学派》（1509–11）\n"
          "高潮处的文艺复兴名作：波提切利《维纳斯的诞生》· 达·芬奇《维特鲁威人》《最后的晚餐》《蒙娜丽莎》· "
          "丢勒《1500 年自画像》· 米开朗基罗《创造亚当》· 拉斐尔《西斯廷圣母》《卡斯蒂廖内像》《基督显圣容》")
ART_EN = ("Works in the second piece, in order: the Mourning Athena relief (c. 460 BC) · the Plato's Academy mosaic "
          "from Pompeii (1st c. BC) · Giotto, Joachim among the Shepherds (1305) · Domenico di Michelino, Dante and "
          "the Three Kingdoms (1465) · Antonello da Messina, St Jerome in his Study (1475) · Bosch, The Wayfarer "
          "(c. 1500) · Giorgione, The Three Philosophers (c. 1509) · Raphael, The School of Athens (1509–11)\n"
          "The High Renaissance at the climax: Botticelli, The Birth of Venus · Leonardo, Vitruvian Man, The Last "
          "Supper, Mona Lisa · Dürer, Self-Portrait (1500) · Michelangelo, The Creation of Adam · Raphael, The Sistine "
          "Madonna, Baldassare Castiglione, The Transfiguration")

MUSIC_ZH = [
    "C 大调前奏曲：Kimiko Ishizaka 钢琴（Open Well-Tempered Clavier，CC0）",
    "大提琴前奏曲：Chris 演奏（Wikimedia Commons，CC0）",
    "加沃特回旋曲：Vicond 演奏，CC BY 3.0 — https://commons.wikimedia.org/wiki/File:J.S.Bach_partita_No.3_Gavotte_in_Rondeau.ogg（加了轻微混响）",
    "G 弦上的咏叹调：美国空军乐团弦乐团（公有领域）",
    "耶稣，世人仰望的喜悦：Orchestra Gli Armonici（CC0，Musopen），去掉了合唱",
]
MUSIC_EN = [
    "Prelude in C: Kimiko Ishizaka, piano (Open Well-Tempered Clavier, CC0)",
    "Cello Prelude: played by Chris (Wikimedia Commons, CC0)",
    "Gavotte en Rondeau: played by Vicond, CC BY 3.0 — https://commons.wikimedia.org/wiki/File:J.S.Bach_partita_No.3_Gavotte_in_Rondeau.ogg (light reverb added)",
    "Air: Air Force Strings, United States Air Force Band (public domain)",
    "Jesu, Joy of Man's Desiring: Orchestra Gli Armonici (CC0, Musopen), choir removed",
]
NO_AI_ZH = "没有 AI 生成的画面或音乐；音乐都是真实的演奏录音。"
NO_AI_EN = "No AI-generated images, video or music; every piece is a real recorded performance."

OWN_HASHTAGS = ["bach", "classicalmusic", "baroquemusic", "renaissanceart", "evangelion", "relaxingmusic"]
OWN_TAGS = ["巴赫", "巴赫精选", "古典音乐", "bach", "best of bach", "j.s. bach", "classical music", "baroque music",
            "prelude in c major", "bwv 846", "cello suite no 1", "bwv 1007", "gavotte en rondeau", "bwv 1006",
            "air on the g string", "bwv 1068", "jesu joy of man's desiring", "bwv 147", "evangelion",
            "school of athens", "renaissance art", "time lapse"]

UPLOAD = """【上传设置 / Upload settings】
· 一个视频：巴赫精选.mp4（1920×1080，30 fps，14:46；没有旁白也没有字幕，中英文共用）
· 视频语言：中文；标题、简介用上面的【中文标题】【中文简介】（章节时间在简介里，YouTube 会自动分章）
· Studio → 语言 → 添加英语：标题、简介用【English title】【English description】
· 封面（1280×720）：中文 youtube-cover.zh.jpg 作主封面；英文 youtube-cover.en.jpg 在 Studio 能按语言设封面时给英语用
· 字幕：无
· Altered or synthetic content: No
· 类别：Music（或 Education）"""


def stamp(sec):
    sec = int(sec)
    return f"{sec // 60}:{sec % 60:02d}"


def credits_block():
    """Pexels names (this film + the Jesu section), the CC BY images, and the public sources."""
    foot = json.loads((DATA / "footage/sources.json").read_text())
    # which clips the film uses comes from the edit itself, not a flag that can go stale
    used = {s["src"].replace("-reversed", "").replace("P10-", "P1-") for p in EDIT["pieces"].values()
            for s in p.get("shots", []) if s.get("src") and not s["src"].startswith("art:")}
    pexels = list(dict.fromkeys(r["author"] for r in foot if r["file"] in used))
    art = json.loads((DATA / "art/sources.json").read_text())
    used_art = {s["src"][4:] for p in EDIT["pieces"].values() for s in p.get("shots", []) if s.get("src", "").startswith("art:")}
    used_art |= {pp["src"][4:].split("/")[-1] for p in EDIT["pieces"].values() for s in p.get("shots", []) for pp in s.get("pops", [])}
    cc = [f"· {r['artist'] or r['credit']} — {r['license']} — {r['page']}" for r in art
          if r["file"] in used_art and r["license"].upper().startswith("CC BY")]
    J = jesu_module()
    jcc, jpex = J.credit_lines()
    pexels = list(dict.fromkeys(pexels + jpex))
    return ["Pexels: " + ", ".join(pexels),
            "Paintings & sculpture: public domain / CC0 via Wikimedia Commons (museum photographs and Google Arts & Culture)",
            "Jesu section, public domain: " + J.PUBLIC,
            "Creative Commons:", *cc, *jcc]


def main():
    timings = json.loads((DATA / "build/timings.json").read_text())["pieces"]
    chap_zh = [f"{stamp(t['start'])} {CHAPTERS[t['id']][0]}" for t in timings]
    chap_en = [f"{stamp(t['start'])} {CHAPTERS[t['id']][1]}" for t in timings]
    block = credits_block()
    zh = [INTRO_ZH, "", *chap_zh, "", ART_ZH, "", "—— 音乐 ——", *MUSIC_ZH, "",
          "画面署名 / Credits:", *block, "", NO_AI_ZH, "", hashtags(OWN_HASHTAGS)]
    en = [INTRO_EN, "", *chap_en, "", ART_EN, "", "—— Music ——", *MUSIC_EN, "",
          "Credits:", *block, "", NO_AI_EN, "", hashtags(OWN_HASHTAGS)]
    zh, en = "\n".join(zh), "\n".join(en)
    out = ["【中文标题】", TITLE_ZH, "", "【English title】", TITLE_EN, "",
           "【中文简介】", zh, "", "【English description】", en, "",
           "【标签 / Tags】", tags(OWN_TAGS), "", UPLOAD, ""]
    path = DATA / "build/youtube-description.txt"
    path.write_text("\n".join(out))
    for name, t, d in (("zh", TITLE_ZH, zh), ("en", TITLE_EN, en)):
        print(f"{name}: title {len(t)} chars, description {len(d)} chars (limits 100 / 5000)")
        assert len(t) <= 100 and len(d) <= 5000
    print(path)


if __name__ == "__main__":
    main()
