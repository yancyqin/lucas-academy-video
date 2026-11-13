"""YouTube upload text for 「Challenge: Which Butterflies Are Real?」, English and Chinese.

    python3 scripts/butterfly-challenge/youtube.py --tag <tag>

One video with the English voice as its default track and a Chinese track added in Studio (Yancy, 2026-11-12), so
one text per language: 【标题】【简介】【标签】【上传设置】 (README "YouTube tags"; tags from scripts/youtube_tags.py).
Credits: the eight CC BY photographers by name (photos/credits.json), the CC BY 2.0 Commons video, the Pexels
videographers, Codex for the AI pictures, the music (CC BY 3.0) and the licensed voice. Writes
out/butterfly-challenge/<tag>/youtube-description.{en,zh}.txt.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from youtube_tags import hashtags, tags  # noqa: E402

DATA = next(p / "lucas-academy-video-data/butterfly-challenge" for p in ROOT.parents if (p / "lucas-academy-video-data").is_dir())
args = sys.argv[1:]
OUT = ROOT / "out/butterfly-challenge" / args[args.index("--tag") + 1]

PEXELS = "Nithin PA, R Bude, Adolph Haben, Nicky Pe, Анатолий, Chris F, Hao Le, Matheus Bertelli, Joolsmagools"
COMMONS = "https://commons.wikimedia.org/wiki/File:Glasswinged_butterfly_(Greta_oto)_in_motion.webm"
MUSIC_URL = "https://archive.org/details/musopen-chopin-complete-works-flac"
BLUE = "https://commons.wikimedia.org/wiki/File:2022-09-02_(452)_LJUBLJANA_Krajinski_park_Tivoli_LEPIDOPTERA_Polyommatus_icarus_NAVADNI_MODRIN.webm"

TEXT = {
    "en": {
        "title": "Challenge: Which Butterflies Are Real? Play Against AI",
        "intro": "Ten pairs of butterflies. In each pair, one is a real photograph and the other was drawn by AI. You get five "
                 "seconds a pair. Can you tell which one is real?\n\nI asked two AIs to play too, GPT-6-Astra and Claude Fable "
                 "5.2, with no hints and no internet, just the two pictures. After each answer you meet the real butterfly: "
                 "where it lives and how common it is.",
        "how": "How the test was done: every pair was a new chat with no context; both pictures were cut to the same size "
               "and saved without metadata. The AI pictures are real, common species in invented scenes, drawn by Codex "
               "(OpenAI image generation). This was a game, so after seeing their answers I redrew the AI pictures in pairs "
               "3, 4, 5, 7 and 8 (some from the reasons the AIs gave, some to look sharper and more real) and asked again; "
               "the film shows the last answer for each pair.",
        "credits": ["Pictures and videos",
                    "· Real photos (iNaturalist, cropped to 16:9): {photos} (CC BY 4.0, https://creativecommons.org/licenses/by/4.0/); two more CC0",
                    "{pages}",
                    f"· Glasswing video: Brandon (Flickr: bpprice), CC BY 2.0 (https://creativecommons.org/licenses/by/2.0/), via Wikimedia Commons, trimmed and slowed, {COMMONS}",
                    f"· Common Blue with open wings: NaIzletuSi, CC BY 3.0 (https://creativecommons.org/licenses/by/3.0/), via Wikimedia Commons, trimmed, {BLUE}",
                    f"· Videos (Pexels): {PEXELS}",
                    "· AI pictures: Codex (OpenAI image generation)",
                    "· Thumbnail photos (iNaturalist, CC BY 4.0): Dimitǎr Boevski (https://www.inaturalist.org/observations/203242996), Cheongweei Gan, Jason Eckberg"],
        "music": f"Music: Frédéric Chopin, Grande valse brillante in E-flat major, Op. 18, played by Olga Gurevich "
                 f"(Musopen, 2012), CC0, {MUSIC_URL}",
        "voice": "Voice: AI speech synthesis (the narrator uses Louise's licensed voice)",
        "byline": "By Yancy Qin | Lucas Academy",
        "tags": ["butterflies", "butterfly", "ai", "ai art", "real or ai", "ai challenge", "gpt", "claude", "nature",
                 "insects", "quiz"],
        "settings": "· Audio: English (default track); add the Chinese track (the .zh.m4a) under Languages\n"
                    "· Captions: both SRTs (en, zh-Hans), timed to the English track; the lines start at the same moments in the Chinese track\n"
                    "· Altered or synthetic content: Yes (the AI-drawn butterflies and the synthetic voice)\n"
                    "· Made for kids: No",
    },
    "zh": {
        "title": "Challenge 猜一猜哪些蝴蝶是真的？和AI比一比",
        "intro": "十组蝴蝶。每组里，一只是真实拍到的照片，另一只是 AI 画的。每组五秒，你能猜出哪一只是真的吗？\n\n"
                 "我还请了两个 AI 一起猜：GPT-6-Astra 和 Claude Fable 5.2。不给提示，不能上网，只看两张图。每公布一次答案，"
                 "我们就认识一种真蝴蝶：它住在哪儿，常不常见。",
        "how": "测试是怎么做的：每一组都是一个新的对话，没有上下文；两张图裁成一样大小，去掉了元数据。"
               "AI 画的是真实存在的常见蝴蝶，场景是编的，用的是 Codex（OpenAI 图像生成）。这是一场游戏，"
               "所以看过它们的回答以后，我重画了第 3、4、5、7、8 组的 AI 图（有的照它们说的理由，有的为了更清楚、更逼真），"
               "又问了一次；片子里用的是每组最后一次的回答。",
        "credits": ["画面",
                    "· 真实照片（iNaturalist，裁成 16:9）：{photos}（CC BY 4.0，https://creativecommons.org/licenses/by/4.0/）；另两张 CC0",
                    "{pages}",
                    f"· 玻璃翼蝶视频：Brandon（Flickr: bpprice），CC BY 2.0（https://creativecommons.org/licenses/by/2.0/），维基共享资源，剪短并放慢，{COMMONS}",
                    f"· 展翅的眼灰蝶：NaIzletuSi，CC BY 3.0（https://creativecommons.org/licenses/by/3.0/），维基共享资源，剪短，{BLUE}",
                    f"· 视频（Pexels）：{PEXELS}",
                    "· AI 蝴蝶图：Codex（OpenAI 图像生成）",
                    "· 封面照片（iNaturalist，CC BY 4.0）：Dimitǎr Boevski（https://www.inaturalist.org/observations/203242996）、Cheongweei Gan、Jason Eckberg"],
        "music": f"音乐：肖邦《降E大调华丽大圆舞曲》Op. 18，Olga Gurevich 演奏（Musopen，2012），CC0，{MUSIC_URL}",
        "voice": "配音：AI 合成语音（旁白使用 Louise 的授权声线）",
        "byline": "作者：Yancy Qin | Lucas Academy",
        "tags": ["蝴蝶", "butterflies", "ai", "ai绘画", "真假", "挑战", "gpt", "claude", "大自然", "昆虫", "科普"],
        "settings": "· 音轨：英文是默认音轨；中文音轨（.zh.m4a）在「语言」里添加\n"
                    "· 字幕：en 和 zh-Hans 两个 SRT，按英文音轨的时间；中文音轨每句开始的时间一样\n"
                    "· 经过修改或合成的内容：是（AI 画的蝴蝶、合成语音）\n"
                    "· 面向儿童：否",
    },
}


def main() -> None:
    credits = json.loads((DATA / "photos/credits.json").read_text())
    names = [m[1] for c in credits.values() if (m := re.match(r"\(c\) (.+?), ", c["attribution"]))]
    OUT.mkdir(parents=True, exist_ok=True)
    for lang, t in TEXT.items():
        order = ["g1", "p08", "p15", "p16", "p17", "p18", "p26", "p44", "p67", "p69"]  # pair order
        pages = "\n".join(f"  {k + 1}. {credits[s]['page']}" for k, s in enumerate(order))
        cred = "\n".join(line.format(photos=("、" if lang == "zh" else ", ").join(names), pages=pages) for line in t["credits"])
        body = "\n\n".join([t["intro"], t["how"], cred, t["music"], t["voice"], t["byline"], hashtags(t["tags"])])
        head = ("【标题】", "【简介】", "【标签】", "【上传设置】")
        text = (f"{head[0]}\n{t['title']}\n\n{head[1]}\n{body}\n\n{head[2]}\n{tags(t['tags'])}\n\n{head[3]}\n{t['settings']}\n")
        (OUT / f"youtube-description.{lang}.txt").write_text(text)
        print(lang, len(body), "characters in the description")


if __name__ == "__main__":
    main()
