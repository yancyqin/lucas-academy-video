"""YouTube titles, descriptions, tags and upload settings -> DATA/build/youtube-description.txt

One video (no narration, no subtitles) with a Chinese title + description and an
English translation of both for Studio → Languages. The Chinese description quotes
和合本, the English one NIV; both carry the credits the licences require. Tags follow the channel rule in scripts/youtube_tags.py
(read from origin/main when this branch doesn't have it yet).
"""
import json
import pathlib
import re
import subprocess
import sys
import types

HERE = pathlib.Path(__file__).parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))
import credits  # noqa: E402

EDIT = json.loads((HERE / "edit.json").read_text())
DATA = pathlib.Path(EDIT["data"])


def youtube_tags():
    path = ROOT / "scripts/youtube_tags.py"
    src = path.read_text() if path.exists() else subprocess.run(
        ["git", "-C", str(ROOT), "show", "origin/main:scripts/youtube_tags.py"],
        capture_output=True, text=True, check=True).stdout
    mod = types.ModuleType("youtube_tags")
    exec(src, mod.__dict__)
    return mod


TITLE_ZH = "耶稣，世人仰望的喜悦｜从创世到再来"
TITLE_EN = "Jesu, Joy of Man's Desiring | From Creation to His Return"

INTRO_ZH = "巴赫《耶稣，世人仰望的喜悦》"
INTRO_EN = ("Bach's \"Jesu, Joy of Man's Desiring\" over a journey from the birth of the universe to Earth, "
            "life, humankind, the cross, the dawn and the morning star. No narration — only the music, "
            "and the verses below.")

# (reference zh, 和合本, reference en, NIV) in the order the film reaches them
VERSES = [
    ("约翰福音 1:1–3", "太初有道，道与　神同在，道就是　神。这道太初与　神同在。万物是藉着他造的；凡被造的，没有一样不是藉着他造的。",
     "John 1:1–3", "In the beginning was the Word, and the Word was with God, and the Word was God. "
     "He was with God in the beginning. Through him all things were made; without him nothing was made that has been made."),
    ("歌罗西书 1:17", "他在万有之先；万有也靠他而立。",
     "Colossians 1:17", "He is before all things, and in him all things hold together."),
    ("约翰福音 1:4", "生命在他里头，这生命就是人的光。",
     "John 1:4", "In him was life, and that life was the light of all mankind."),
    ("约翰福音 1:14", "道成了肉身，住在我们中间，充充满满地有恩典有真理。我们也见过他的荣光，正是父独生子的荣光。",
     "John 1:14", "The Word became flesh and made his dwelling among us. We have seen his glory, the glory of the one "
     "and only Son, who came from the Father, full of grace and truth."),
    ("约翰福音 1:29", "看哪，　神的羔羊，除去世人罪孽的！",
     "John 1:29", "Look, the Lamb of God, who takes away the sin of the world!"),
    ("希伯来书 12:2", "仰望为我们信心创始成终的耶稣。他因那摆在前面的喜乐，就轻看羞辱，忍受了十字架的苦难，便坐在　神宝座的右边。",
     "Hebrews 12:2", "Fixing our eyes on Jesus, the pioneer and perfecter of faith. For the joy set before him he endured "
     "the cross, scorning its shame, and sat down at the right hand of the throne of God."),
    ("启示录 21:5", "坐宝座的说：“看哪，我将一切都更新了！”又说：“你要写上；因这些话是可信的，是真实的。”",
     "Revelation 21:5", "He who was seated on the throne said, \"I am making everything new!\" Then he said, "
     "\"Write this down, for these words are trustworthy and true.\""),
    ("启示录 22:16", "我是大卫的根，又是他的后裔。我是明亮的晨星。",
     "Revelation 22:16", "I am the Root and the Offspring of David, and the bright Morning Star."),
]

JOURNEY_ZH = ("宇宙诞生 → 深空 → 银河 → 地出 → 大气层的边缘 → 云海 → 微生物、开花、海洋、林间的光、蚂蚁、蜜蜂、鸟 → "
              "西斯廷礼拜堂《创造亚当》 → 夜里的城市 → 米开朗基罗《圣母怜子像》 → 走向日出 → 黎明 → 太空中的晨光 → 晨星")
JOURNEY_EN = ("Birth of the universe → deep space → the Milky Way → Earthrise → the edge of the atmosphere → "
              "a sea of clouds → microbes, a flower opening, the sea, light in the forest, ants, a bee, a bird → "
              "The Creation of Adam in the Sistine Chapel → cities at night → Michelangelo's Pietà → "
              "walking toward the sunrise → dawn → daybreak seen from orbit → the morning star")

MUSIC_ZH = "音乐：巴赫《耶稣，世人仰望的喜悦》BWV 147/10，Orchestra Gli Armonici 演奏，CC0（Musopen）。为做成纯器乐版，去掉了合唱。"
MUSIC_EN = ("Music: J. S. Bach, \"Jesus bleibet meine Freude\" (Jesu, Joy of Man's Desiring), BWV 147/10 — "
            "Orchestra Gli Armonici, CC0 (Musopen). The choir was removed for this instrumental version.")
NO_AI_ZH = "没有 AI 生成的画面或音乐；音乐是真实的乐团录音。"
NO_AI_EN = "No AI-generated images or video; the music is a real orchestral recording."
SCRIPTURE_ZH = "经文：和合本（公有领域）。"
SCRIPTURE_EN = ("Scripture quotations taken from The Holy Bible, New International Version® NIV® Copyright © 1973, "
                "1978, 1984, 2011 by Biblica, Inc.™ Used by permission. All rights reserved worldwide.")

OWN_HASHTAGS = ["bach", "jesujoyofmansdesiring", "creation", "scripture", "classicalmusic", "christianmusic"]
OWN_TAGS = ["耶稣世人仰望的喜悦", "jesu joy of man's desiring", "bach", "bwv 147", "creation", "gospel of john",
            "scripture", "bible verses", "classical music", "christian music", "nasa", "webb telescope",
            "michelangelo", "sistine chapel", "pieta"]

UPLOAD = """【上传设置 / Upload settings】
· 一个视频：耶稣，世人仰望的喜悦.mp4（1920×1080，30 fps；没有旁白也没有字幕，中英文共用）
· 视频语言：中文；标题、简介用上面的【中文标题】【中文简介】
· Studio → 语言 → 添加英语：标题、简介用【English title】【English description】
· 封面（1280×720）：中文 youtube-cover.zh.jpg 作主封面；英文 youtube-cover.en.jpg 在 Studio 能按语言设封面时给英语用
· 字幕：无（经文都在简介里）
· Altered or synthetic content: No
· 类别：Education"""


# Public-domain and CC0 sources, said once each (the per-shot list is in CREDITS.md)
PUBLIC = ("NASA (Goddard Scientific Visualization Studio, STScI / Hubble & Webb, LRO, Artemis II, "
          "ISS / Earth Observatory) · U.S. National Park Service · U.S. Department of State, photo by Ron Przysucha · "
          "Extemporalist (CC0)")


def credit_lines():
    """Creative Commons lines the licences require (author — licence — source), and Pexels names."""
    recs = credits.records()
    cc, pexels = [], []
    for s in EDIT["shots"]:
        r = recs.get(s["src"], {})
        lic = r.get("license", "")
        who = (r.get("credit") or r.get("author") or "").split(" (http")[0].split(" (Flickr")[0].strip()
        if "pexels" in lic.lower():
            pexels.append(who)
        elif "CC BY" in lic.upper():
            m = re.search(r"CC BY(-SA)?\s*([\d.]+)", lic.upper())
            cc.append(f"· {who} — CC BY{m.group(1) or ''} {m.group(2)} — {r.get('source_page_url', '')}")
    return list(dict.fromkeys(cc)), list(dict.fromkeys(pexels))


def main():
    tags = youtube_tags()
    cc, pexels = credit_lines()
    credits_block = ["Footage & images — public domain: " + PUBLIC,
                     "Pexels: " + ", ".join(pexels),
                     "Creative Commons:", *cc]
    zh = [INTRO_ZH, "", "—— 经文（和合本）——", ""]
    en = [INTRO_EN, "", "—— Scripture (NIV) ——", ""]
    for rz, tz, re_, te in VERSES:
        zh += [f"{rz}　{tz}", ""]
        en += [f"{re_}  {te}", ""]
    zh += ["—— 画面 ——", JOURNEY_ZH, "", MUSIC_ZH, "", "画面署名 / Credits:", *credits_block, "",
           NO_AI_ZH, SCRIPTURE_ZH, "", tags.hashtags(OWN_HASHTAGS)]
    en += ["—— The journey ——", JOURNEY_EN, "", MUSIC_EN, "", "Credits:", *credits_block, "",
           NO_AI_EN, "", SCRIPTURE_EN, "", tags.hashtags(OWN_HASHTAGS)]
    zh, en = "\n".join(zh), "\n".join(en)
    out = ["【中文标题】", TITLE_ZH, "", "【English title】", TITLE_EN, "",
           "【中文简介】", zh, "", "【English description】", en, "",
           "【标签 / Tags】", tags.tags(OWN_TAGS), "", UPLOAD, ""]
    path = DATA / "build/youtube-description.txt"
    path.write_text("\n".join(out))
    for name, t, d in (("zh", TITLE_ZH, zh), ("en", TITLE_EN, en)):
        print(f"{name}: title {len(t)} chars, description {len(d)} chars (limits 100 / 5000)")
        assert len(t) <= 100 and len(d) <= 5000
    print(path)


if __name__ == "__main__":
    main()
