#!/usr/bin/env python3
"""YouTube title, description (zh + en together), tags, upload settings and cover for the 焰火 film.

    python youtube.py OUTDIR      -> OUTDIR/youtube-description.txt, OUTDIR/youtube-cover.jpg

Same layout as the other Debussy films (one bilingual title / description / cover, English line a little bigger on the
cover; 【标题】【简介】【标签】【上传设置】). Chapters = the seven sections of film_plan.py; tags follow scripts/youtube_tags.py.
"""
import pathlib, sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = pathlib.Path(__file__).parent; ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT / "scripts")); sys.path.insert(0, str(HERE))
from youtube_tags import hashtags, tags  # noqa: E402
from film_plan import SECTIONS, XF       # noqa: E402

DATA = pathlib.Path("/Users/yqin/repo/playground/lucas-academy-video-data/debussy-impressions")
FONTS = pathlib.Path("/Users/yqin/repo/playground/lucas-academy-video-data/jesu/fonts")

TITLE_EN = "Fireworks | Light Up the Paintings"
TITLE_ZH = "焰火｜点亮名画"                                   # proposed; the owner sets titles
COVER = dict(section="rhone", frame=670, crop_top=0.0, lift=30)  # Van Gogh's Rhône with fireworks among his stars
FILE = "焰火.mp4"

PAINTINGS = {   # chapter line per section: title | painter, year | where it hangs
  "venice": "暮色中的圣乔治马焦雷岛 San Giorgio Maggiore at Dusk｜莫奈 Monet, 1908｜卡迪夫威尔士国家博物馆 National Museum Cardiff",
  "parliament": "国会大厦，日落 The Houses of Parliament, Sunset｜莫奈 Monet, 1903｜华盛顿国家美术馆 National Gallery of Art, Washington",
  "montmartre": "夜晚的蒙马特大道 The Boulevard Montmartre at Night｜毕沙罗 Pissarro, 1897｜伦敦国家美术馆 National Gallery, London",
  "rhone": "罗讷河上的星夜 Starry Night Over the Rhône｜梵高 Van Gogh, 1888｜巴黎奥赛博物馆 Musée d'Orsay, Paris",
  "beijing": "北京之夜 A Night over Beijing｜我们拍的照片，AI 照莫奈画伦敦暮色的笔法画成 our own photo, painted by AI after Monet's London dusks",
  "rocket": "黑与金的夜曲：坠落的火箭 Nocturne in Black and Gold – The Falling Rocket｜惠斯勒 Whistler, 1875｜底特律美术馆 Detroit Institute of Arts",
  "montorgueil": "蒙托格伊街，1878 年 6 月 30 日的节日 The Rue Montorgueil, Celebration of 30 June 1878｜莫奈 Monet, 1878｜巴黎奥赛博物馆 Musée d'Orsay, Paris",
}

INTRO_ZH = ("德彪西《焰火》，配 7 幅黄昏和夜晚的画：威尼斯、伦敦、巴黎、阿尔勒、北京……每一幅都从真实的景色开始，天色慢慢暗下来，"
            "我们走进画里；一根火柴（还有点灯人的灯杆、蜡烛、仙女棒、线香、点火筒、火炬）把画面点亮，点着引信，焰火升空，"
            "每一朵都在音乐的重音上绽开。焰火的形状和轨迹照真的焰火来算：牡丹、菊花、垂柳、棕榈、光环、十字、噼啪闪光，"
            "颜料却是印象派的笔触。")
INTRO_EN = ("Debussy's Feux d'artifice (Fireworks) over 7 paintings of dusk and night: Venice, London, Paris, Arles, Beijing… Each "
            "one starts as a real scene; the light slowly fades and we step into the painting. A match (and a lamplighter's pole, a "
            "taper, a sparkler, an incense stick, a portfire, a torch) lights up the picture and the fuse, the rockets rise, and every "
            "burst opens on an accent of the music. The shapes and paths follow real fireworks: peonies, chrysanthemums, willows, "
            "palms, rings, crossettes, crackling stars, laid on in Impressionist brushstrokes.")
CLAUDES_ZH = ("这一集里有三个 Claude：作曲家克劳德·德彪西、画家克劳德·莫奈（7 幅画里有 3 幅是他的，北京那幅也照他的笔法画），"
              "和 AI Claude，每一朵焰火落在哪个音上、怎么飞，是我们和它一起编排的。第四个 Claude 是信息论之父克劳德·香农，"
              "四个人的故事在《你认识 Claude 吗？》里：中文 https://youtu.be/-_eloejjteY ｜ English https://youtu.be/3sZcFf7P-V4")
CLAUDES_EN = ("Three Claudes made this one: the composer Claude Debussy, the painter Claude Monet (3 of the 7 paintings are his, and "
              "the Beijing one is painted in his manner), and Claude the AI, with which we arranged which note each firework bursts "
              "on and how it flies. The fourth is Claude Shannon, the father of information theory; their story is in \"Do You Know "
              "Claude?\": English https://youtu.be/3sZcFf7P-V4 | 中文 https://youtu.be/-_eloejjteY")
ABOUT_ZH = ("《焰火》是德彪西《前奏曲》第二册的最后一首（1913 年出版），一般认为写的是巴黎国庆夜里的焰火；曲子快结束时，远远传来几句《马赛曲》。"
            "最后一幅莫奈画的正是巴黎的节日：1878 年 6 月 30 日，整条街挂满三色旗。这 7 幅活画也放在网上，可以自己动手放焰火："
            "https://art-lab.lucasacademy.org/living")
ABOUT_EN = ("Feux d'artifice is the last piece of Debussy's second book of Préludes (published 1913), usually heard as fireworks "
            "over Paris on Bastille Day; near the end, a few bars of La Marseillaise are heard from far away. The last painting is a Paris "
            "celebration too: Monet's Rue Montorgueil on 30 June 1878, every window hung with the tricolour. The 7 living paintings "
            "are online, and you can set off the fireworks yourself: https://art-lab.lucasacademy.org/living")
MUSIC_ZH = ("音乐：克劳德·德彪西《前奏曲》第二册第 12 首《焰火》，Stefano Ligoratti 钢琴现场演奏，授权 CC BY 3.0"
            "（https://creativecommons.org/licenses/by/3.0/），来自 IMSLP（https://imslp.org/wiki/Special:ImagefromIndex/220928）；"
            "我们调整了响度。")
MUSIC_EN = ("Music: Claude Debussy, Préludes, Book II, No. 12, Feux d'artifice, performed live by Stefano Ligoratti (piano), "
            "licensed CC BY 3.0 (https://creativecommons.org/licenses/by/3.0/), via IMSLP "
            "(https://imslp.org/wiki/Special:ImagefromIndex/220928); loudness adjusted.")
AI_ZH = ("关于画面：每幅画开头的写实景色是 AI 依据原画想象还原的（Codex 图像生成），不是历史照片；北京那幅开头是我们自己拍的照片，"
         "画是 AI 照着照片画的。火柴、灯杆、蜡烛、仙女棒、线香、点火筒和火炬也是 AI 照每幅画的笔法画的。天色变暗、火光、焰火、"
         "烟和水里的倒影是我们写的程序画出来的。其余 6 幅画作都是公有领域，图像来自各博物馆的开放获取。")
AI_EN = ("About the images: the realistic scene at the start of each painting is an AI reconstruction imagined from the painting "
         "(Codex image generation), not a historical photo; the Beijing one starts from our own photograph, and its painting was "
         "made by AI from that photo. The match, pole, taper, sparkler, incense stick, portfire and torch were painted by AI in each "
         "painting's manner. The falling dusk, the flames, the fireworks, the smoke and the reflections on the water are drawn by "
         "our own code. The other 6 paintings are in the public domain; the images come from the museums' open-access collections.")
QUESTION_ZH = "如果让你点亮一幅画，你会选哪一幅，放什么样的焰火？这也是我们在 Lucas Academy 一起学习、一起思考的问题。"
QUESTION_EN = ("If you could light up one painting, which would you choose, and what fireworks would you set off? It's the kind of "
               "question we think about together at Lucas Academy.")
OWN_HASHTAGS = ["debussy", "fireworks", "impressionism", "vangogh", "classicalmusic", "livingpainting"]
OWN_TAGS = ["焰火", "德彪西", "前奏曲", "莫奈", "梵高", "印象派", "活画", "debussy", "claude debussy", "feux d'artifice", "fireworks",
            "preludes", "claude monet", "monet", "van gogh", "pissarro", "whistler", "impressionism", "impressionist painting",
            "living painting", "classical music", "piano", "art and music", "claude", "你认识claude吗"]

def mmss(t): return f"{int(t // 60)}:{int(t % 60):02d}"

def chapters():
    out = []
    for s in SECTIONS:
        t = 0.0 if s["span"][0] == 0 else (s["span"][0] + XF if s["id"] != "montorgueil" else s["span"][0])
        out.append(f"{mmss(t)} {PAINTINGS[s['id']]}")
    return out

def background():
    im = Image.open(DATA / "feux/film" / COVER["section"] / "frames-live" / f"{COVER['frame']:05d}.jpg").convert("RGB")
    W, H = 1280, 720; k = W / im.width
    im = im.resize((W, round(im.height * k)), Image.LANCZOS); y = round(COVER["crop_top"] * im.height)
    return im.crop((0, y, W, y + H))

def cover(img, en, zh, lift=0):
    """English line a little bigger, Chinese line a little smaller, together near the bottom (as the other Debussy films)."""
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
    out = pathlib.Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
    title = f"{TITLE_EN} · {TITLE_ZH}"
    desc = "\n".join([INTRO_ZH, INTRO_EN, "", CLAUDES_ZH, CLAUDES_EN, "", ABOUT_ZH, ABOUT_EN, "",
                      "—— 7 幅画 · The 7 paintings ——", *chapters(), "",
                      MUSIC_ZH, MUSIC_EN, "", AI_ZH, AI_EN, "", QUESTION_ZH, QUESTION_EN, "", hashtags(OWN_HASHTAGS)])
    end = SECTIONS[-1]["span"][1]
    upload = f"""【上传设置 / Upload settings】
· 一个视频：{FILE}（1920×1080，30 fps，时长 {int(end // 60)} 分 {int(round(end % 60))} 秒；没有旁白也没有字幕）
· 标题、简介都是中英文合在一起的一份，不用再加语言翻译
· 视频语言：中文
· 章节：简介里的时间点（0:00 起）会自动变成章节（每幅画一章，共 7 章，每章都超过 20 秒）
· 封面（1280×720）：youtube-cover.jpg
· 字幕：无
· Altered or synthetic content（经过修改或合成的内容）：是 —— 每幅画开头的写实景色是 AI 依据原画还原的、看起来像真实场景；点火的工具是 AI 画的；北京那幅画是 AI 照照片画的
· 类别：Education"""
    doc = ["【标题 / Title】", title, "", "【简介 / Description】", desc, "", "【标签 / Tags】", tags(OWN_TAGS), "", upload, ""]
    (out / "youtube-description.txt").write_text("\n".join(doc))
    print(f"title {len(title)} chars, description {len(desc)} chars (limits 100 / 5000)"); assert len(title) <= 100 and len(desc) <= 5000
    cover(background(), TITLE_EN, TITLE_ZH, COVER["lift"]).save(out / "youtube-cover.jpg", quality=92)
    print("wrote", out)

if __name__ == "__main__":
    main()
