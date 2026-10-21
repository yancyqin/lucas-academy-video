#!/usr/bin/env python3
"""YouTube title, description (zh + en), tags, upload settings and covers for one piece of the Debussy film.

  youtube.py edits/01-mer.json OUTDIR     -> OUTDIR/youtube-description.txt, youtube-cover.jpg
One bilingual title, description and cover (owner 2026-10-15: 中英文放到一起; English line slightly bigger on the cover).
Chapters come from the edit list (one per painting); painting credits from paintings.json; the music credit
from music/sources.json. Tags follow scripts/youtube_tags.py.
"""
import io, json, pathlib, re, subprocess, sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = pathlib.Path(__file__).parent; ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from youtube_tags import hashtags, tags  # noqa: E402
DATA = pathlib.Path("/Users/yqin/repo/playground/lucas-academy-video-data/debussy-impressions")
FONTS = pathlib.Path("/Users/yqin/repo/playground/lucas-academy-video-data/jesu/fonts")

PIECES = {
 "mer1": {
  "title_en": "The Sea | Claude Monet X Claude Debussy",
  "title_zh": "大海| 克劳德·莫奈X 克劳德·德彪西",
  "cover_bg": "real/aligned/sea-2.png", "cover_crop_top": 0.02,
  "claudes_zh": ("其实有 4 个 Claude：画家克劳德·莫奈、作曲家克劳德·德彪西、信息论之父克劳德·香农，还有 AI Claude，这部片子就是我们和它一起做的。"
                 "四个 Claude 的故事在《你认识 Claude 吗？》里：中文 https://youtu.be/-_eloejjteY ｜ English https://youtu.be/3sZcFf7P-V4"),
  "claudes_en": ("There are actually four Claudes: the painter Claude Monet, the composer Claude Debussy, Claude Shannon, the father of "
                 "information theory, and Claude the AI, which we made this film with. Their story is in \"Do You Know Claude?\": "
                 "English https://youtu.be/3sZcFf7P-V4 | 中文 https://youtu.be/-_eloejjteY"),
  "intro_zh": ("德彪西《大海》第一乐章《海上，从黎明到正午》，配莫奈等画家的 11 幅海与河：从勒阿弗尔港口的日出，"
               "沿塞纳河到阿让特伊的帆，再到正午的诺曼底海岸。每一幅画先从一张“那一刻的照片”开始，慢慢溶成画家留下的样子。"),
  "about_zh": ("画家克劳德·莫奈（1840–1926）和作曲家克劳德·德彪西（1862–1918）都是法国人。"
               "“印象派”这个名字来自莫奈 1872 年的《印象·日出》，就是片子的第一幅画；人们也把德彪西叫作印象派，他自己并不喜欢这个说法。"
               "《大海》1905 年首演，初版乐谱的封面用的是葛饰北斋的《神奈川冲浪里》。"),
  "intro_en": ("The first movement of Debussy's La mer, \"From dawn to noon on the sea\", over 11 paintings of the sea and the Seine "
               "by Monet and his circle: sunrise in the harbour of Le Havre, the sails of Argenteuil, then the Normandy coast at noon. "
               "Each painting begins as a photograph of that moment and slowly dissolves into what the painter left us."),
  "about_en": ("The painter Claude Monet (1840–1926) and the composer Claude Debussy (1862–1918) were both French. "
               "\"Impressionism\" took its name from Monet's Impression, Sunrise (1872), the film's first painting; Debussy was called "
               "an Impressionist too, a label he disliked. La mer was first performed in 1905, and its first edition carried Hokusai's "
               "Great Wave on the cover."),
  "question_zh": "你觉得，照片里的那一刻，和莫奈画下的那一刻，哪一个更像你记忆里的大海？这也是我们在 Lucas Academy 一起学习、一起思考的问题。",
  "question_en": "Which feels closer to the sea you remember: the photograph of that moment, or the moment Monet painted? It's the kind of question we think about together at Lucas Academy.",
  "music_zh": "音乐：克劳德·德彪西《大海》第一乐章《海上，从黎明到正午》，Lawrence Odom 管乐改编，美国空军乐队（音乐会管乐团）演奏，公有领域（美国政府作品）。",
  "music_en": "Music: Claude Debussy, La mer, I. \"De l'aube à midi sur la mer\", concert-band arrangement by Lawrence Odom, performed by the United States Air Force Band (Concert Band). Public domain (U.S. government work).",
  "own_hashtags": ["debussy", "monet", "impressionism", "lamer", "classicalmusic", "claudemonet"],
  "own_tags": ["大海", "德彪西", "莫奈", "印象派", "印象日出", "debussy", "claude debussy", "la mer", "claude monet", "monet",
               "impressionism", "impression sunrise", "impressionist painting", "classical music", "art and music", "normandy", "argenteuil", "claude", "claude shannon", "你认识claude吗"],
  "file": "大海.mp4",
 },
}

PIECES["clair"] = {
  "title_en": "Clair de lune | Moon You Can See",
  "title_zh": "月光｜看得见的月光",                                  # owner's title, verbatim (2026-10-16)
  "cover_lift": 70,                                                 # owner: title higher, not so close to the bottom
  "cover_bg": "clair/cover/beijing-cover.png", "cover_crop_top": 0.0,   # owner: 北京那个图，更模糊、更印象派 (Codex repaint)
  "claudes_zh": ("这一集里有两个 Claude：作曲家克劳德·德彪西，和 AI Claude，画面怎么跟着旋律呼吸，是我们和它一起编排的。"
                 "其实一共有 4 个 Claude，另外两个是画家克劳德·莫奈和信息论之父克劳德·香农，故事在《你认识 Claude 吗？》里："
                 "中文 https://youtu.be/-_eloejjteY ｜ English https://youtu.be/3sZcFf7P-V4"),
  "claudes_en": ("Two Claudes made this one: the composer Claude Debussy, and Claude the AI, with which we arranged how the picture "
                 "breathes with the melody. There are actually four Claudes; the other two are the painter Claude Monet and Claude "
                 "Shannon, the father of information theory. Their story is in \"Do You Know Claude?\": English "
                 "https://youtu.be/3sZcFf7P-V4 | 中文 https://youtu.be/-_eloejjteY"),
  "intro_zh": ("德彪西《月光》，配 24 个月夜。22 张是真实的照片，在旋律里慢慢变成一幅印象派的画；另外 2 张是毕沙罗和梵高的真画。"
               "画面跟着旋律呼吸：旋律升起时变亮、变清楚，落到低音、乐句换气时变暗、变朦胧。最后一张月亮，是我们自己拍的。"),
  "intro_en": ("Debussy's Clair de lune over 24 moonlit nights. Twenty-two real photographs slowly turn into Impressionist paintings "
               "as the melody moves; two are real paintings by Pissarro and Van Gogh. The picture breathes with the melody: brighter "
               "and clearer as it rises, darker and softer in the bass and in the breaths between phrases. The last moon is one we "
               "photographed ourselves."),
  "about_zh": "《月光》是德彪西《贝加莫组曲》的第三首，大约 1890 年写成，1905 年才出版。曲名来自法国诗人魏尔伦的诗《月光》。",
  "about_en": ("Clair de lune is the third piece of Debussy's Suite bergamasque, begun around 1890 and published only in 1905. Its "
               "title comes from Paul Verlaine's poem \"Clair de lune\"."),
  "question_zh": "你听《月光》的时候，眼前浮现的是一张照片，还是一幅画？这也是我们在 Lucas Academy 一起学习、一起思考的问题。",
  "question_en": "When you listen to Clair de lune, do you see a photograph or a painting? It's the kind of question we think about together at Lucas Academy.",
  "music_zh": ("音乐：克劳德·德彪西《贝加莫组曲》第三首《月光》，Laurens Goedhart 钢琴演奏（2011），授权 CC BY 3.0"
               "（https://creativecommons.org/licenses/by/3.0/），来自 Wikimedia Commons；我们调整了响度。"),
  "music_en": ("Music: Claude Debussy, Suite bergamasque, III. Clair de lune, performed by Laurens Goedhart (2011), licensed CC BY 3.0 "
               "(https://creativecommons.org/licenses/by/3.0/), via Wikimedia Commons; loudness adjusted."),
  "own_hashtags": ["debussy", "clairdelune", "impressionism", "piano", "classicalmusic", "moonlight"],
  "own_tags": ["月光", "德彪西", "贝加莫组曲", "印象派", "钢琴", "debussy", "claude debussy", "clair de lune", "suite bergamasque",
               "moonlight", "impressionism", "impressionist painting", "piano", "classical music", "art and music", "van gogh",
               "pissarro", "monet", "whistler", "claude", "你认识claude吗"],
  "file": "月光.mp4",
}

PIECES["faune"] = {
  "title_en": "Afternoon of a Faun | Paintings Come Alive",
  "title_zh": "牧神午后｜活起来的画",                                  # proposed; the owner sets titles
  "cover_lift": 40,
  "cover_bg": "faune/cover/cover-bg.png", "cover_crop_top": 0.0,
  "claudes_zh": ("这一集里有三个 Claude：作曲家克劳德·德彪西、画家克劳德·莫奈（12 幅画里有 9 幅是他的），和 AI Claude，"
                 "画家怎么跟着音乐落笔、魔法棒什么时候让画活起来，是我们和它一起编排的。第四个 Claude 是信息论之父克劳德·香农，"
                 "四个人的故事在《你认识 Claude 吗？》里：中文 https://youtu.be/-_eloejjteY ｜ English https://youtu.be/3sZcFf7P-V4"),
  "claudes_en": ("Three Claudes made this one: the composer Claude Debussy, the painter Claude Monet (9 of the 12 paintings are his), "
                 "and Claude the AI, with which we arranged when the painter's brush meets the music and when the wand wakes each "
                 "painting up. The fourth is Claude Shannon, the father of information theory; their story is in \"Do You Know "
                 "Claude?\": English https://youtu.be/3sZcFf7P-V4 | 中文 https://youtu.be/-_eloejjteY"),
  "intro_zh": ("德彪西《牧神午后前奏曲》，配 12 幅印象派画家画的大自然：塞纳河的晨雾、地中海边的松树、悬崖上的风、罂粟花田、"
               "睡莲池……每一幅都从画家写生的地方开始：一个懒洋洋的画家，跟着音乐一笔一笔把画画出来；镜头推近画布，"
               "一根魔法棒再一样一样地让它活起来：水在动，风在吹，云在飘，蝴蝶飞过来。最后留一点时间，静静地看它。"),
  "intro_en": ("Debussy's Prelude to the Afternoon of a Faun over 12 Impressionist paintings of nature: morning mist on the Seine, "
               "a pine by the Mediterranean, wind on a cliff, a field of poppies, the water-lily pond… Each one starts where the "
               "painter set up the easel: a lazy painter paints it stroke by stroke with the music, the camera moves in, and a magic "
               "wand brings it to life one thing at a time: the water ripples, the wind blows, the clouds drift, a butterfly comes by. "
               "Then there is a moment just to watch."),
  "about_zh": ("《牧神午后前奏曲》1894 年 12 月在巴黎首演，灵感来自诗人马拉美的诗《牧神的午后》。开头那段长笛独奏非常有名。"
               "这 12 幅活画也放在网上，可以自己动手让画活起来：https://art-lab.lucasacademy.org/living"),
  "about_en": ("The Prelude was first performed in Paris in December 1894, inspired by Stéphane Mallarmé's poem \"The Afternoon of "
               "a Faun\"; its opening flute solo is one of the most famous in music. The 12 living paintings are online too, and you "
               "can bring them to life yourself: https://art-lab.lucasacademy.org/living"),
  "question_zh": "如果你也有一根魔法棒，你最想让哪一幅画活过来？这也是我们在 Lucas Academy 一起学习、一起思考的问题。",
  "question_en": "If you had a magic wand, which painting would you bring to life? It's the kind of question we think about together at Lucas Academy.",
  "music_zh": ("音乐：克劳德·德彪西《牧神午后前奏曲》，哥伦比亚大学管弦乐团演奏，Jeffrey Milarsky 指挥（2002 年秋季音乐会现场），"
               "公有领域，来自 Musopen（https://musopen.org/music/42994-prelude-to-the-afternoon-of-a-faun/）；我们调整了响度。"),
  "music_en": ("Music: Claude Debussy, Prélude à l'après-midi d'un faune, performed by the Columbia University Orchestra, conducted by "
               "Jeffrey Milarsky (Fall 2002 concert, live). Public domain, via Musopen "
               "(https://musopen.org/music/42994-prelude-to-the-afternoon-of-a-faun/); loudness adjusted."),
  "own_hashtags": ["debussy", "afternoonofafaun", "impressionism", "monet", "classicalmusic", "livingpainting"],
  "own_tags": ["牧神午后", "牧神午后前奏曲", "德彪西", "莫奈", "印象派", "活画", "debussy", "claude debussy", "afternoon of a faun",
               "prelude to the afternoon of a faun", "claude monet", "monet", "sisley", "renoir", "berthe morisot", "impressionism",
               "impressionist painting", "living painting", "classical music", "art and music", "claude", "你认识claude吗"],
  "file": "牧神午后.mp4",
  # owner 10-21: 「给我中英文独立的标题和介绍」 — a Chinese title + description, and an English one for YouTube's
  # translation of the title and description; each links only to "Do You Know Claude?" in its own language
  "split": True,
  "claudes_zh_only": ("这一集里有三个 Claude：作曲家克劳德·德彪西、画家克劳德·莫奈（12 幅画里有 9 幅是他的），和 AI Claude，"
                      "画家怎么跟着音乐落笔、魔法棒什么时候让画活起来，是我们和它一起编排的。第四个 Claude 是信息论之父克劳德·香农，"
                      "四个人的故事在《你认识 Claude 吗？》里：https://youtu.be/-_eloejjteY"),
  "claudes_en_only": ("Three Claudes made this one: the composer Claude Debussy, the painter Claude Monet (9 of the 12 paintings are "
                      "his), and Claude the AI, with which we arranged when the painter's brush meets the music and when the wand wakes "
                      "each painting up. The fourth is Claude Shannon, the father of information theory; their story is in \"Do You "
                      "Know Claude?\": https://youtu.be/3sZcFf7P-V4"),
}

def faune_lines(lang=None):
    """One chapter per painting, at the section's first note (the plan); title, painter, year and museum from the
    living page's WORKS (the same strings the art lab shows)."""
    plan = json.load(open(DATA / "faune/film/plan.json"))
    html = open("/Users/yqin/repo/playground/lucas-visual-art-lab-faune/living.html").read()
    lines = []
    for k, s in enumerate(plan):
        i = html.index(f'"faune-{s["id"]}":'); blk = html[i:html.index("brushes:[", i)]
        tz, te = re.search(r'title:\{ zh:"([^"]+)", en:"([^"]+)" \}', blk).groups()
        bz, be = re.search(r'by:\{ zh:"([^"]+)", en:"([^"]+)" \}', blk).groups()
        pz, yz, mz = [x.strip() for x in bz.split(" · ")]; pe, ye, me = [x.strip() for x in be.split(" · ")]
        pz_short = pz.split("·")[-1]; pe_short = pe.split()[-1]          # 莫奈 Monet, 莫里索 Morisot, 雷诺阿 Renoir
        t = mmss(0 if k == 0 else s['s0'])
        lines.append(f"{t} {tz}｜{pz_short}，{yz} 年｜{mz}" if lang == "zh" else f"{t} {te} | {pe_short}, {ye} | {me}" if lang == "en"
                     else f"{t} {tz} {te}｜{pz_short} {pe_short}, {ye}｜{mz} {me}")
    return lines

CLAIR_EN = {"moonpath": "A path of moonlight", "lilac-branches": "Full moon in bare branches", "mackerel-moon": "Moon in mackerel clouds",
            "birds-branches": "Birds and the full moon", "lavender": "Lavender and the moon", "alpenglow": "Moonrise over pink peaks",
            "moonrise-sea": "Moonrise over the sea", "stilt-hut": "A stilt hut over the sea", "dubrovnik": "The moon over Dubrovnik",
            "alicante-sail": "Waves and a far sail", "fjord-clouds": "Moonlit clouds over a fjord", "pink-moon-boat": "A boat under a pink moon",
            "fishing-pier": "A fishing-village pier", "cobble-street": "A cobblestone street under the stars",
            "river-village": "A river village under the stars", "swiss-village": "A village below snowy peaks",
            "cypresses": "Cypresses under the stars", "cypress-sea": "A cypress by the sea", "milkyway-lake": "The Milky Way in a lake",
            "frozen-lake": "A frozen lake on a winter night", "lone-tree": "A lone tree and the full moon", "eave-moon": "Full moon in the clouds"}
CLAIR_ZH = {"eave-moon": "云中满月"}
PAINTERS = [("惠斯勒", "Whistler"), ("莫里索", "Morisot"), ("西涅克", "Signac"), ("梵高", "Van Gogh"), ("雷诺阿", "Renoir"),
            ("莫奈", "Monet"), ("克罗斯", "Cross"), ("毕沙罗", "Pissarro"), ("西斯莱", "Sisley")]
CLAIR_SECTIONS = [  # (first shot id, zh, en) - chapters by musical section: several pictures are under 10 s, and one
    ("moonpath", "开头的主题：只有月亮", "Opening theme: the moon alone"),            # chapter under 10 s disables them all
    ("lavender", "渐渐升起，到高点", "Rising to the peak"),
    ("moonrise-sea", "海上月出，琶音流动起来", "Moonrise; the arpeggios begin to flow"),
    ("fishing-pier", "高潮：港口和灯火", "The climax: harbours and lights"),
    ("night-1", "平静下来", "Calming"),
    ("swiss-village", "主题回来：小镇和星空", "The theme returns: villages and stars"),
    ("frozen-lake", "琶音的回声：冬夜", "The arpeggio's echo: a winter night"),
    ("eave-moon", "渐弱，到最后一个和弦", "Fading to the last chord"),
]

def clair_lines(ed, paintings):
    D = DATA / "clair"
    frames = json.load(open(D / "frames/frames.json")); cands = {c["id"]: c for c in json.load(open(D / "candidates.json"))}
    style = {pathlib.Path(a["path"]).stem: a.get("style", "") for a in json.load(open(D / "paint/generated-assets.json"))}
    shots = [s for s in ed["shots"] if not s.get("drop")]; first = {f: (zh, en) for f, zh, en in CLAIR_SECTIONS}
    out = []
    for s in shots:
        k = s["id"]
        if k in first:
            zh, en = first[k]; t = 0 if k == shots[0]["id"] else s["breath_cut"]
            if out: out.append("")
            out.append(f"{mmss(t)} {zh} {en}")
        if k.startswith("night-"):
            p = paintings[k]; tz, te = split_zh_en(p["title"]); az, ae = split_zh_en(p["artist"]); mz, me = museum_parts(p["museum"])
            ae_short = "Van Gogh" if "Gogh" in ae else ae.split()[-1]
            out.append(f"· {tz} {te}｜{az.split('·')[-1]} {ae_short}, {p['year']}｜{mz} {me}（真画 real painting）")
            continue
        pz, pe = next(((z, e) for z, e in PAINTERS if z in style.get(k, "")), ("", ""))
        who = f"{cands[frames[k]['pexels']]['photographer']} / Pexels" if k in frames else "我们自己拍的 our own photo"
        zh = CLAIR_ZH.get(k, s["zh"])
        out.append(f"· {zh} {CLAIR_EN[k]}｜仿{pz} after {pe}｜{who}")
    return out

def split_zh_en(s):
    m = re.match(r"^([^A-Za-z]*?)\s*([A-Za-z].*)$", s.strip())
    return (m.group(1).strip(), m.group(2).strip()) if m else (s.strip(), "")

def museum_parts(s):
    s = re.sub(r"（[^）]*）", "", s).strip(); return split_zh_en(s)

def mmss(t): return f"{int(t // 60)}:{int(t % 60):02d}"

def chapters(ed, paintings):
    zh, en = [], []
    for sh in ed["shots"]:
        p = paintings[sh["id"]]
        tz, te = split_zh_en(p["title"]); az, ae = split_zh_en(p["artist"]); mz, me = museum_parts(p["museum"])
        az_short = az.split("·")[-1]; ae_short = ae.split()[-1]
        yz = p["year"]; ye = yz.replace("约 ", "c. ")
        zh.append(f"{mmss(sh['at'])} {tz} {te}｜{az_short} {ae_short}, {ye}｜{mz} {me}")
    return zh, en

def background(cfg):
    im = Image.open(DATA / cfg["cover_bg"]).convert("RGB"); W, H = 1280, 720
    k = W / im.width; im = im.resize((W, round(im.height * k)), Image.LANCZOS); y = round(cfg["cover_crop_top"] * im.height)
    return im.crop((0, y, W, y + H))

def cover(img, en, zh, lift=0):
    """English line a little bigger, Chinese line a little smaller, together near the bottom (owner 2026-10-15);
    `lift` px raises both lines (and the shade under them) for covers where the bottom edge is too low."""
    W, H = img.size
    shade = Image.new("L", (W, H), 0); d = ImageDraw.Draw(shade)
    top = H * 0.50 - lift
    for y in range(H):
        u = (y - top) / (H - top); d.line([(0, y), (W, y)], fill=int(190 * max(0.0, u) ** 1.2))
    img = Image.composite(Image.new("RGB", (W, H), (0, 0, 0)), img, shade)
    fe = ImageFont.truetype(str(FONTS / "NotoSerifSC-Regular.otf"), 56); fz = ImageFont.truetype(str(FONTS / "NotoSerifSC-Regular.otf"), 47)
    text = Image.new("RGBA", (W, H), (0, 0, 0, 0)); t = ImageDraw.Draw(text)
    t.text((W / 2, H - 112 - lift), en, font=fe, fill=(255, 255, 255, 255), anchor="ms")
    t.text((W / 2, H - 46 - lift), zh, font=fz, fill=(242, 232, 210, 255), anchor="ms")
    glow = text.getchannel("A").filter(ImageFilter.GaussianBlur(10))
    halo = Image.merge("RGBA", (*Image.new("RGB", (W, H), (0, 0, 0)).split(), glow.point(lambda v: int(v * 0.85))))
    out = Image.alpha_composite(Image.alpha_composite(img.convert("RGBA"), halo), text).convert("RGB")
    bw = max(t.textlength(en, font=fe), t.textlength(zh, font=fz)); assert bw < W - 60, f"title too wide ({bw:.0f}px)"
    return out

def main():
    edit, out = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
    ed = json.loads(edit.read_text()); cfg = PIECES[ed["piece"]]
    paintings = {p["id"]: p for p in json.load(open(DATA / "paintings.json"))}
    if ed["piece"] == "faune":
        chapter_lines = faune_lines(); head = "—— 12 幅活画 · The 12 living paintings ——"
        ai_zh = ("关于画面：画架后面的写实风景是 AI 依据每幅原画想象还原的（Codex 图像生成），不是历史照片；风景里的动态（水、风、云、"
                 "人物）也是 AI 生成的视频（MiniMax Hailuo）。画架、画笔和魔法棒也是 AI 照着每幅画的笔法画的。画家作画的过程是电脑模拟的油画笔触，不是画家真实的作画过程。画里的动态（水、风、云、光、"
                 "蝴蝶、花瓣）是我们写的程序让原画的颜料动起来；其中 3 幅画里飘来的新云由 AI 照原画的笔法延伸。画作本身都是公有领域，"
                 "图像来自各博物馆的开放获取。")
        ai_en = ("About the images: the realistic landscapes behind the easel are AI reconstructions imagined from each painting "
                 "(Codex image generation), not historical photos, and their motion (water, wind, clouds, people) is AI-generated "
                 "video (MiniMax Hailuo); the easels, brushes and wands were also painted by AI in each "
                 "painting's manner. The painting process is a computer simulation of oil brushstrokes, not how the painters really "
                 "worked. The motion in the paintings (water, wind, clouds, light, butterflies, petals) is our own code moving the "
                 "paint of the original; in 3 of them the new clouds drifting in were extended by AI in the painter's manner. The "
                 "paintings themselves are in the public domain; the images come from the museums' open-access collections.")
    elif ed["piece"] == "clair":
        chapter_lines = clair_lines(ed, paintings)
        head = "—— 月夜 · The nights（画名｜AI 画仿哪位画家｜照片作者 · title | AI painting after | photographer）——"
        ai_zh = ("关于画面：22 幅印象派的画是 AI 照着照片画的（Codex 图像生成），只借那位画家的笔法，不是他们的作品；"
                 "其中 2 张照片也由 AI 向两边延伸成了横幅。毕沙罗和梵高两幅是真画（公有领域，来自博物馆的开放获取），"
                 "它们开头的“照片”是 AI 依据原画想象还原的，不是历史照片。")
        ai_en = ("About the images: the 22 Impressionist paintings were painted by AI from the photographs (Codex image generation), "
                 "borrowing only each painter's manner; they are not those painters' works. Two of the photographs were also widened "
                 "to 16:9 by AI. The Pissarro and the Van Gogh are real paintings (public domain, museum open access); the "
                 "\"photograph\" at their start is an AI reconstruction imagined from the painting, not a historical photo.")
    else:
        chapter_lines, _ = chapters(ed, paintings); head = "—— 画 · The paintings ——"
        n_anim = sum(1 for s_ in ed["shots"] if s_.get("anim"))
        ai_zh = ("关于画面：每幅画开头的“照片”是 AI 依据原画想象还原的（Codex 图像生成），不是历史照片；"
                 f"其中 {n_anim} 幅画里的动态也是 AI 生成的（MiniMax 海螺）。画作本身都是公有领域，图像来自各博物馆的开放获取。")
        ai_en = ("About the images: the \"photograph\" at the start of each painting is an AI reconstruction imagined from the painting "
                 f"(Codex image generation), not a historical photo; the motion in {n_anim} of the paintings is AI-generated too (MiniMax Hailuo). "
                 "The paintings themselves are in the public domain; the images come from the museums' open-access collections.")
    title = f"{cfg['title_en']} · {cfg['title_zh']}"
    desc = "\n".join([cfg["intro_zh"], cfg["intro_en"], "",
                      cfg["claudes_zh"], cfg["claudes_en"], "",
                      cfg["about_zh"], cfg["about_en"], "",
                      head, *chapter_lines, "",
                      cfg["music_zh"], cfg["music_en"], "",
                      ai_zh, ai_en, "",
                      cfg["question_zh"], cfg["question_en"], "",
                      hashtags(cfg["own_hashtags"])])
    chap_note = "（按乐段分 8 章，每章都超过 10 秒；按图分的话有几张不到 10 秒，YouTube 就不显示章节了）" if ed["piece"] == "clair" else ""
    synth = ("是 —— 画架后面的写实风景是 AI 依据原画还原的、看起来像真实场景，风景里的动态是 AI 生成的视频；画架、画笔、魔法棒是 AI 画的；新飘来的云由 AI 延伸"
             if ed["piece"] == "faune" else
             "是 —— 印象派的画是 AI 照着照片画的，两张照片由 AI 延伸成横幅，两幅真画开头的写实“照片”是 AI 还原的、看起来像真实场景"
             if ed["piece"] == "clair" else "是 —— 每幅画开头的写实“照片”是 AI 生成的、看起来像真实场景，部分画面的动态也是 AI 生成的")
    if ed["piece"] == "faune": chap_note = "（每幅画一章，共 12 章，每章都超过 25 秒）"
    upload = f"""【上传设置 / Upload settings】
· 一个视频：{cfg['file']}（1920×1080，30 fps，时长 {int(ed['end'] // 60)} 分 {int(ed['end'] % 60)} 秒；没有旁白也没有字幕）
· 标题、简介都是中英文合在一起的一份，不用再加语言翻译
· 视频语言：中文
· 章节：简介里的时间点（0:00 起）会自动变成章节{chap_note}
· 封面（1280×720）：youtube-cover.jpg
· 字幕：无
· Altered or synthetic content（经过修改或合成的内容）：{synth}
· 类别：Education"""
    doc = ["【标题 / Title】", title, "", "【简介 / Description】", desc, "", "【标签 / Tags】", tags(cfg["own_tags"]), "", upload, ""]
    if cfg.get("split"):                                          # one title + description per language
        lz, le = faune_lines("zh"), faune_lines("en")
        desc_zh = "\n".join([cfg["intro_zh"], "", cfg["claudes_zh_only"], "", cfg["about_zh"], "", "—— 12 幅活画 ——", *lz, "",
                             cfg["music_zh"], "", ai_zh, "", cfg["question_zh"], "", hashtags(cfg["own_hashtags"])])
        desc_en = "\n".join([cfg["intro_en"], "", cfg["claudes_en_only"], "", cfg["about_en"], "", "—— The 12 living paintings ——", *le, "",
                             cfg["music_en"], "", ai_en, "", cfg["question_en"], "", hashtags(cfg["own_hashtags"])])
        upload = upload.replace("· 标题、简介都是中英文合在一起的一份，不用再加语言翻译\n",
                                "· 标题、简介：上传时填【中文标题】【中文简介】；再到「字幕」→「添加语言」→ 英语 → 「标题和说明」，"
                                "填【English title】【English description】（英文界面的观众会看到英文版）\n")
        doc = ["【中文标题】", cfg["title_zh"], "", "【中文简介】", desc_zh, "", "【English title】", cfg["title_en"], "",
               "【English description】", desc_en, "", "【标签 / Tags】", tags(cfg["own_tags"]), "", upload, ""]
        for d_ in (desc_zh, desc_en): assert len(d_) <= 5000
        print(f"zh: title {len(cfg['title_zh'])}, description {len(desc_zh)} · en: title {len(cfg['title_en'])}, description {len(desc_en)} chars")
    (out / "youtube-description.txt").write_text("\n".join(doc))
    print(f"title {len(title)} chars, description {len(desc)} chars (limits 100 / 5000)"); assert len(title) <= 100 and len(desc) <= 5000
    cover(background(cfg), cfg["title_en"], cfg["title_zh"], cfg.get("cover_lift", 0)).save(out / "youtube-cover.jpg", quality=92)
    print("wrote", out)

if __name__ == "__main__":
    main()
