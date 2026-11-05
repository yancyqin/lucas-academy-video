#!/usr/bin/env python3
"""youtube-description.txt for 听得见的舞: a Chinese title + description and an English one (the 牧神午后 layout, owner
10-21: 「给我中英文独立的标题和介绍」), chapters at each piece's start in the joined film, tags from scripts/youtube_tags.py.

  python3 scripts/gymnopedies/youtube.py OUTDIR      (reads film/film.json written by film.py for the chapter times)
"""
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from youtube_tags import hashtags, tags

DATA = Path("/Users/yqin/repo/playground/lucas-academy-video-data/satie-gymnopedies")
FILE = "听得见的舞.mp4"

TITLE_ZH = "听得见的舞｜萨蒂《裸体歌舞》1–3 × 德加的舞者"
TITLE_EN = "The Dance You Can Hear | Satie's Gymnopédies 1–3 × Degas's Dancers"

INTRO_ZH = ("萨蒂的三首《裸体歌舞》，只用钢琴。德加和雷诺阿画里的舞者，从油画里慢慢活过来；真实的芭蕾舞者跟着音符走走停停——"
            "琴键按下去，她们就动一下；音符之间，她们几乎停住。舞是看的，这一次也能听见。")
INTRO_EN = ("Satie's three Gymnopédies, on solo piano. The dancers in Degas's and Renoir's paintings slowly come to life, and real "
            "ballet dancers move with the notes: each time a key goes down they move, and between the notes they almost stop. "
            "A dance you watch, and this time one you can hear.")
ABOUT_ZH = ("《裸体歌舞》（Gymnopédies）是埃里克·萨蒂 1888 年写的三首慢板钢琴曲，名字来自古希腊斯巴达的节日 gymnopaedia，"
            "少年们在节日里裸身跳舞。三首用同一种摇摆的三拍子，只是情绪不同：第一首「缓慢而痛苦」，第二首「缓慢而忧伤」，"
            "第三首「缓慢而庄重」。德彪西很喜欢它们，1896–97 年把其中两首改编成了管弦乐。")
ABOUT_EN = ("Erik Satie wrote the three Gymnopédies in 1888. The name comes from the gymnopaedia, a festival in ancient Sparta "
            "where young men danced naked. All three sway in the same slow triple time, each in its own mood: \"slow and "
            "painful\", \"slow and sad\", \"slow and grave\". Debussy loved them and orchestrated two of them in 1896–97.")
PIECES_ZH = ["第一首 Gymnopédie No. 1 · 缓慢而痛苦 Lent et douloureux", "第二首 Gymnopédie No. 2 · 缓慢而忧伤 Lent et triste",
             "第三首 Gymnopédie No. 3 · 缓慢而庄重 Lent et grave"]
PIECES_EN = ["Gymnopédie No. 1 · Lent et douloureux (slow and painful)", "Gymnopédie No. 2 · Lent et triste (slow and sad)",
             "Gymnopédie No. 3 · Lent et grave (slow and grave)"]
PAINTINGS_ZH = [   # in the order they appear
    "第一首：德加《舞台上的舞者（明星）》约 1876–77，奥赛博物馆；《把杆前练习的舞者》1877，大都会艺术博物馆；《舞蹈课》1874，大都会艺术博物馆",
    "第二首：雷诺阿《布吉瓦尔之舞》1883，波士顿美术馆；《煎饼磨坊的舞会》1876，奥赛博物馆；《乡村之舞》《城市之舞》1883，奥赛博物馆",
    "第三首：德加《舞台上的排练》约 1874，奥赛博物馆；《歌剧院的乐队》约 1870，奥赛博物馆；《等待》约 1882，盖蒂博物馆与诺顿·西蒙美术馆共藏；《蓝色舞者》1898，普希金造型艺术博物馆",
]
PAINTINGS_EN = [
    "No. 1: Degas, The Star (Dancer on Stage), c. 1876–77, Musée d'Orsay; Dancers Practicing at the Barre, 1877, The Met; The Dance Class, 1874, The Met",
    "No. 2: Renoir, Dance at Bougival, 1883, Museum of Fine Arts, Boston; Bal du moulin de la Galette, 1876, Musée d'Orsay; Dance in the Country and Dance in the City, 1883, Musée d'Orsay",
    "No. 3: Degas, The Rehearsal on Stage, c. 1874, Musée d'Orsay; The Orchestra at the Opera, c. 1870, Musée d'Orsay; Waiting, c. 1882, J. Paul Getty Museum and Norton Simon Art Foundation; Blue Dancers, 1898, Pushkin Museum",
]
MUSIC_ZH = ("音乐：埃里克·萨蒂《裸体歌舞》。第一首：Daria Baiocchi 演奏，CC0（公有领域贡献），来自 IMSLP / Wikimedia Commons。"
            "第二、三首：\"Gymnopedie No 2\" \"Gymnopedie No 3\" Kevin MacLeod (incompetech.com)，"
            "Licensed under Creative Commons: By Attribution 3.0 License http://creativecommons.org/licenses/by/3.0/ 。我们调整了响度。")
MUSIC_EN = ("Music: Erik Satie, Gymnopédies. No. 1 performed by Daria Baiocchi, CC0 (public domain dedication), via IMSLP / "
            "Wikimedia Commons. Nos. 2 and 3: \"Gymnopedie No 2\" and \"Gymnopedie No 3\" Kevin MacLeod (incompetech.com), "
            "Licensed under Creative Commons: By Attribution 3.0 License http://creativecommons.org/licenses/by/3.0/ . Loudness adjusted.")
FOOTAGE_ZH = "真人舞者的影片来自 Pexels：cottonbro studio、Anastasia Shura、Pavel Danilyuk。我们按音符给它们变了速。"
FOOTAGE_EN = ("Footage of real dancers from Pexels: cottonbro studio, Anastasia Shura, Pavel Danilyuk. We retimed it to follow "
              "the notes.")
AI_ZH = ("关于画面：画里的场景变成“真实”的那一刻，是 AI 依据原画想象还原的（Codex 图像生成），舞者的动作是 AI 生成的视频"
         "（Muse），不是历史影像；煎饼磨坊和歌剧院乐池两段来自我们的影片《你知道印象派的秘密吗？》，同样由 AI 生成。"
         "画作本身都是公有领域，图像来自各博物馆的开放获取和 Wikimedia Commons。")
AI_EN = ("About the images: the moments where a painting turns \"real\" are AI reconstructions imagined from the painting (Codex "
         "image generation), and the dancers' movement there is AI-generated video (Muse), not historical footage; the Moulin de "
         "la Galette and opera-pit clips come from our film \"Do You Know the Secret of Impressionism?\" and are AI-generated too. "
         "The paintings themselves are in the public domain; the images come from the museums' open-access collections and "
         "Wikimedia Commons.")
OWN_HASHTAGS = ["satie", "gymnopedie", "degas", "ballet", "classicalmusic", "piano"]
OWN_TAGS = ["听得见的舞", "裸体歌舞", "萨蒂", "德加", "雷诺阿", "芭蕾", "钢琴", "古典音乐", "satie", "eriksatie", "gymnopédie",
            "gymnopedie", "gymnopedieno1", "degas", "renoir", "ballet", "dancers", "piano", "classicalmusic", "impressionism",
            "artandmusic"]   # the ones the owner used on upload (11-03)

def mmss(t): return f"{int(t // 60)}:{int(t % 60):02d}"

def main():
    out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
    film = json.load(open(DATA / "film/film.json"))
    starts, total = film["starts"], film["duration"]
    ch_zh = [f"{mmss(t)} {p}" for t, p in zip(starts, PIECES_ZH)]
    ch_en = [f"{mmss(t)} {p}" for t, p in zip(starts, PIECES_EN)]
    desc_zh = "\n".join([INTRO_ZH, "", ABOUT_ZH, "", *ch_zh, "", "—— 画 ——", *PAINTINGS_ZH, "", MUSIC_ZH, "", FOOTAGE_ZH, "",
                         AI_ZH, "", hashtags(OWN_HASHTAGS)])
    desc_en = "\n".join([INTRO_EN, "", ABOUT_EN, "", *ch_en, "", "—— The paintings ——", *PAINTINGS_EN, "", MUSIC_EN, "",
                         FOOTAGE_EN, "", AI_EN, "", hashtags(OWN_HASHTAGS)])
    upload = f"""【上传设置 / Upload settings】
· 一个视频：{FILE}（1920×1080，30 fps，时长 {int(total // 60)} 分 {int(total % 60)} 秒；纯音乐，没有旁白、字幕或画面文字，中英文观众看同一个视频）
· 标题、简介：上传时填【中文标题】【中文简介】；再到「字幕」→「添加语言」→ 英语 →「标题和说明」，填【English title】【English description】（英文界面的观众会看到英文版）
· 视频语言：中文
· 章节：简介里的三个时间点（0:00 起）会自动变成章节，每首一章
· 封面（1280×720，两组做 A/B 测试，中英文各一张）：A《明星》youtube-cover.zh.jpg / youtube-cover.en.jpg；B《舞蹈课》youtube-cover-dance-class.zh.jpg / youtube-cover-dance-class.en.jpg。A 是你选的 Muse 画面（原构图，主角以外的背景稍微虚化），B 是 Codex 把你选的那一帧延伸成的横幅；标题放在你画的位置。「测试和比较」一次最多放 3 张
· 字幕：无
· Altered or synthetic content（经过修改或合成的内容）：是 —— 画作变成“真实”场景的画面和其中舞者的动作是 AI 生成的，看起来像真实场景
· 类别：Education"""
    doc = ["【中文标题】", TITLE_ZH, "", "【中文简介】", desc_zh, "", "【English title】", TITLE_EN, "",
           "【English description】", desc_en, "", "【标签 / Tags】", tags(OWN_TAGS), "", upload, ""]
    for t in (TITLE_ZH, TITLE_EN): assert len(t) <= 100
    for d in (desc_zh, desc_en): assert len(d) <= 5000
    (out / "youtube-description.txt").write_text("\n".join(doc))
    print(f"zh: title {len(TITLE_ZH)}, description {len(desc_zh)} · en: title {len(TITLE_EN)}, description {len(desc_en)} chars -> {out}")

if __name__ == "__main__":
    main()
