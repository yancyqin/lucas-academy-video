"""Upload texts for the Twinkle Variations drawing film and its vertical short -> DATA/package/

    youtube-description.txt         the film: 【中文标题】【中文简介】【English title】【English description】【标签】【上传设置】
    youtube-description.short.txt   the short: one bilingual title (the short itself is bilingual), credits, #shorts

Same layout as 牧神午后 (separate zh / en title and description); tags and hashtags from scripts/youtube_tags.py.
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from youtube_tags import hashtags, tags  # noqa: E402

DATA = pathlib.Path("/Users/yqin/repo/playground/lucas-academy-video-data/twinkle-stars")
FILM, SHORT = "小星星变奏曲.mp4", "小星星-竖屏.mp4"
COMMONS = "https://commons.wikimedia.org/wiki/File:Mozart_-_12_Variations_K._265_-_Simone_Renzi.mp3"
CCBY = "https://creativecommons.org/licenses/by/3.0/"

TITLE_ZH = "小星星变奏曲｜跟着莫扎特画画"
TITLE_EN = "Twinkle Variations | Drawing with Mozart"

INTRO_ZH = ("莫扎特《小星星变奏曲》的主题和第一变奏，配一本孩子的蜡笔画本。每一笔都落在音符上：先用黑色蜡笔勾轮廓，"
            "再一拍一块地涂颜色，最后补上天上的小星星。画完了，星星就跟着节拍一闪一闪。")
INTRO_EN = ("The theme and first variation of Mozart's Twinkle Variations, with a child's crayon sketchbook. Every stroke lands "
            "on a note: first the outlines in black crayon, then the colours, one patch per beat, and last the little stars in "
            "the sky. When the picture is done, the stars twinkle in time with the music.")
ABOUT_ZH = ("这段旋律原本是一首法国老歌《妈妈，我要告诉你》（Ah ! vous dirai-je, maman）；后来英文配上了“Twinkle, Twinkle, "
            "Little Star”，就是我们唱的《小星星》。莫扎特在维也纳为它写了 12 段变奏（K. 265），这里是主题和第一段。")
ABOUT_EN = ("The tune began as an old French song, \"Ah ! vous dirai-je, maman\"; English later set \"Twinkle, Twinkle, Little "
            "Star\" to it. In Vienna, Mozart wrote 12 variations on it (K. 265); this is the theme and the first one.")
TIMES_ZH = ["0:00 主题 · 小星星醒来了", "0:49 第一变奏 · 彩虹滑梯"]
TIMES_EN = ["0:00 Theme · The little star wakes up", "0:49 Variation 1 · The rainbow slide"]
MUSIC_ZH = ("音乐：W. A. Mozart, 12 Variations on \"Ah vous dirai-je, Maman\", K. 265（莫扎特《小星星变奏曲》）。\n"
            f"钢琴及录音：Simone Renzi。录音许可：CC BY 3.0。\n{COMMONS}\n{CCBY}\n本片只用了主题和第一变奏，并调整了音量。")
MUSIC_EN = ("Music: W. A. Mozart, 12 Variations on \"Ah vous dirai-je, Maman\" (Twinkle, Twinkle, Little Star), K. 265.\n"
            f"Piano and recording: Simone Renzi, licensed under CC BY 3.0.\n{COMMONS}\n{CCBY}\n"
            "Modifications: the theme and first variation only; volume adjusted.")
AI_ZH = ("关于画面：两幅蜡笔画、书桌和蜡笔都是 AI 生成的图（Codex 图像生成）。画画的过程不是录下来的，"
         "是我们写的程序把画拆成一笔一笔，跟着音乐的节拍画出来。")
AI_EN = ("About the images: the two crayon drawings, the desk and the crayon are AI-generated images (Codex image generation). "
         "The drawing is not a recording: our own program takes each picture apart stroke by stroke and draws it to the beat.")
BYLINE_ZH, BYLINE_EN = "作者 Yancy Qin | Lucas Academy", "By Yancy Qin | Lucas Academy"
OWN_HASHTAGS = ["mozart", "twinklevariations", "classicalmusic", "musicforkids", "kidsdrawing", "crayondrawing"]
OWN_TAGS = ["小星星", "小星星变奏曲", "莫扎特", "蜡笔画", "儿童画", "古典音乐", "给孩子的古典音乐",
            "mozart", "twinkle twinkle little star", "twinkle variations", "k 265", "ah vous dirai-je maman",
            "mozart for kids", "classical music for kids", "crayon drawing", "kids drawing", "drawing to music", "simone renzi"]

SHORT_TITLE = "一闪一闪亮晶晶，能画出来吗？ Can you draw \"Twinkle, Twinkle\"?"


def main():
    out = DATA / "package"; out.mkdir(exist_ok=True)
    tail = hashtags(OWN_HASHTAGS)
    desc_zh = "\n".join([INTRO_ZH, "", ABOUT_ZH, "", *TIMES_ZH, "", MUSIC_ZH, "", AI_ZH, "", BYLINE_ZH, "", tail])
    desc_en = "\n".join([INTRO_EN, "", ABOUT_EN, "", *TIMES_EN, "", MUSIC_EN, "", AI_EN, "", BYLINE_EN, "", tail])
    upload = f"""【上传设置 / Upload settings】
· 一个视频：{FILM}（1920×1080，30 fps，1 分 31 秒；没有旁白也没有字幕）
· 标题、简介：上传时填【中文标题】【中文简介】；再到「字幕」→「添加语言」→ 英语 → 「标题和说明」，填【English title】【English description】（英文界面的观众会看到英文版）
· 视频语言：中文
· 时间点：简介里的 0:00 / 0:49 可以点，但只有两段，不会生成章节（YouTube 至少要 3 个、每个 10 秒以上）
· 封面（1280×720）：youtube-cover.zh.jpg；英文版 youtube-cover.en.jpg 可放进「测试和比较」或留作英文封面
· 字幕：无
· Altered or synthetic content（经过修改或合成的内容）：是 —— 书桌和蜡笔是看起来像真实照片的 AI 生成图，两幅画也是 AI 生成的
· 类别：Education"""
    doc = ["【中文标题】", TITLE_ZH, "", "【中文简介】", desc_zh, "", "【English title】", TITLE_EN, "",
           "【English description】", desc_en, "", "【标签 / Tags】", tags(OWN_TAGS), "", upload, ""]
    for d in (desc_zh, desc_en): assert len(d) <= 5000
    assert len(TITLE_ZH) <= 100 and len(TITLE_EN) <= 100
    (out / "youtube-description.txt").write_text("\n".join(doc))

    sdesc = "\n".join([
        "莫扎特《小星星变奏曲》的主题：一笔一个音符，画完星星跟着节拍一闪一闪。",
        "The theme of Mozart's Twinkle Variations: one stroke per note, and when it's done the stars twinkle to the beat.", "",
        MUSIC_ZH.replace("本片只用了主题和第一变奏", "本片只用了主题"), "",
        MUSIC_EN.replace("the theme and first variation only", "the theme only"), "",
        AI_ZH.replace("两幅蜡笔画", "蜡笔画"), AI_EN.replace("the two crayon drawings", "the crayon drawing"), "",
        f"{BYLINE_ZH} · {BYLINE_EN.replace('By ', 'by ')}", "",
        "#shorts " + hashtags(OWN_HASHTAGS[:5])])        # 15 hashtags at most, or YouTube ignores them all
    supload = f"""【上传设置 / Upload settings】
· 一个竖屏短视频：{SHORT}（1080×1920，30 fps，48.6 秒）
· 标题和简介中英文合在一份（视频里的文字本身就是中英文）
· 「相关视频」：长片上传后，在 Studio 里把这个短视频的「相关视频」设成长片
· Altered or synthetic content（经过修改或合成的内容）：是 —— 书桌和蜡笔是看起来像真实照片的 AI 生成图，画也是 AI 生成的
· 类别：Education"""
    sdoc = ["【标题 / Title】", SHORT_TITLE, "", "【简介 / Description】", sdesc, "", "【标签 / Tags】", tags(OWN_TAGS), "", supload, ""]
    assert len(SHORT_TITLE) <= 100 and len(sdesc) <= 5000
    (out / "youtube-description.short.txt").write_text("\n".join(sdoc))
    print(f"film: zh title {len(TITLE_ZH)}, description {len(desc_zh)} · en title {len(TITLE_EN)}, description {len(desc_en)}; "
          f"short: title {len(SHORT_TITLE)}, description {len(sdesc)}; tags {len(tags(OWN_TAGS))} chars")


if __name__ == "__main__":
    main()
