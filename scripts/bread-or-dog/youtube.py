"""YouTube upload text for 「怎么骗过 AI：面包还是狗？」, English and Chinese.

    python3 scripts/bread-or-dog/youtube.py --tag film-v04

The film is one video with the English voice as its default track and the Chinese track added in Studio (Yancy,
2026-11-16), so one text per language: 【标题】【简介】【标签】【上传设置】 (README "YouTube tags"; tags from
scripts/youtube_tags.py). Chapters come from public/bread-or-dog/timeline.json.
Writes out/bread-or-dog/<tag>/youtube-description.{en,zh}.txt. (A vertical short was made on 2026-11-17 and dropped by
Yancy the same day: 「感觉不需要短视频」.)
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from youtube_tags import hashtags, tags  # noqa: E402

args = sys.argv[1:]
OUT = ROOT / "out/bread-or-dog" / (args[args.index("--tag") + 1] if "--tag" in args else "film-v04")
TL = json.loads((ROOT / "public/bread-or-dog/timeline.json").read_text())

PEXELS = "Stephen, Ruxanda Scutelnic, Oliver King, Travel with Lenses, Andreas Schnabl, Nadin Sh, Nataliya Vaitkevich, Gu Ko, Sena, Ellie Burgin"
MUSIC_URL = "https://www.youtube.com/watch?v=Yv18lq16QOU"
RESEARCH = [
    ("Mariya Yao, Chihuahua or Muffin? Searching for the Best Computer Vision API (TOPBOTS, 2017)",
     "https://www.freecodecamp.org/news/chihuahua-or-muffin-my-search-for-the-best-computer-vision-api-cbda4d6b425d/"),
    ("Geirhos et al., ImageNet-trained CNNs are biased towards texture (ICLR 2019)", "https://arxiv.org/abs/1811.12231"),
    ("Vaswani et al., Attention Is All You Need (NIPS 2017)", "https://arxiv.org/abs/1706.03762"),
    ("Dosovitskiy et al., An Image is Worth 16x16 Words (ICLR 2021)", "https://arxiv.org/abs/2010.11929"),
    ("Geirhos et al., Partial success in closing the gap between human and machine vision (NeurIPS 2021)", "https://arxiv.org/abs/2106.07411"),
    ("Radford et al., Learning Transferable Visual Models From Natural Language Supervision (CLIP, ICML 2021)", "https://arxiv.org/abs/2103.00020"),
]
CHAPTERS = {"en": ["It used to be hard", "Trick 1: the cake dog", "Trick 2: a trap in the question", "Trick 3: invisible noise",
                   "Trick 4: a note that says BREAD", "Why today's AI is hard to fool"],
            "zh": ["以前这是道难题", "第一招：蛋糕狗", "第二招：话里带坑", "第三招：看不见的噪点", "第四招：一张写着「面包」的便签",
                   "为什么现在的 AI 这么难骗"]}


def stamp(s: float) -> str:
    s = int(s)
    return f"{s // 60}:{s % 60:02d}"


def chapters(lang: str) -> str:
    starts = [0.0] + [TL["sections"][k][0] for k in ("sc01", "sc02", "sc03", "sc04", "sc05")]
    return "\n".join(f"{stamp(t)} {name}" for t, name in zip(starts, CHAPTERS[lang]))


TEXT = {
    "en": {
        "title": "Dog or Bread? How to Fool an AI",
        "intro": "AI mixing up dogs and bread is an old joke. Is today's AI still that easy to fool? I tried six AIs, from "
                 "AlexNet (2012) to Claude Fable 5.2 and GPT-6-Astra (2026), and four tricks: an AI-made \"Shiba\" that is "
                 "really a cake, a trap in the question, noise your eyes cannot see, and a sticky note that says BREAD. At the "
                 "end: why is today's AI so hard to fool?",
        "how": "How the test was done: each question was a new chat with no context and no internet; the older models "
               "(AlexNet, ResNet-50, CLIP ViT-B/32, LLaVA 1.6 7B) ran on my computer. Fable and Astra were asked once more on "
               "every trick that fooled them, with the same result. The noise was calculated against ResNet-50 itself. These "
               "are examples, not statistics.",
        "research": "Research mentioned",
        "credits": ["Pictures and video",
                    f"· Photos (Pexels): {PEXELS}, and other Pexels photographers in the look-alike grid",
                    "· Cat with elephant skin: Geirhos et al., texture-vs-shape (CC BY 4.0, https://github.com/rgeirhos/texture-vs-shape)",
                    "· AI pictures: Codex (OpenAI image generation): the cake Shiba, the puppy on the baking tray",
                    "· The cut: Muse (AI video)"],
        "music": f"Music: George Frideric Handel, Concerto Grosso in B-flat major, Op. 6 No. 7, V. Hornpipe, L'Arco Magico Chamber "
                 f"Orchestra, conducted by Antonio Puccio; Creative Commons Attribution (CC BY), {MUSIC_URL} (excerpt, loudness adjusted)",
        "voice": "Voice: AI speech synthesis (the narrator uses Louise's licensed voice)",
        "byline": "By Yancy Qin | Lucas Academy",
        "tags": ["ai", "artificial intelligence", "computer vision", "machine learning", "dog or bread", "chihuahua or muffin",
                 "transformer", "attention", "adversarial examples", "claude", "gpt", "is it cake"],
        "settings": "· Audio: English (default track); add the Chinese track (bread-or-dog.zh.m4a) under Languages\n"
                    "· Captions: both SRTs (en, zh-Hans), timed to the English track; the lines start at the same moments in the Chinese track\n"
                    "· Thumbnail: youtube-cover.en.jpg (A, \"Dog or Cake?\"); alternate B (\"Can AI Still Be Fooled?\")\n"
                    "· Altered or synthetic content: Yes (the AI-made cake dog, the Muse cut, the synthetic voice)\n"
                    "· Made for kids: No",
    },
    "zh": {
        "title": "狗还是面包？怎么骗过 AI",
        "intro": "AI 分不清狗和面包，是个很老的笑话了。现在的 AI 还这么好骗吗？我试了六个 AI，从 2012 年的 AlexNet，到 2026 年的 "
                 "Claude Fable 5.2 和 GPT-6-Astra，想了四招：AI 画的「柴犬」其实是蛋糕、在问题里挖个坑、加一层人眼看不出的噪点、"
                 "贴一张写着「面包」的便签。最后讲讲：为什么现在的 AI 这么难骗？",
        "how": "测试是怎么做的：每个问题都是一个新的对话，没有上下文、不能上网；老一点的模型（AlexNet、ResNet-50、CLIP ViT-B/32、"
               "LLaVA 1.6 7B）在我自己的电脑上跑。Fable 和 Astra 每次被骗，都在新对话里再问了一次，答案一样。噪点是照着 ResNet-50 "
               "自己算出来的。这些是举例，不是统计。",
        "research": "片中提到的研究",
        "credits": ["画面",
                    f"· 照片（Pexels）：{PEXELS}，以及格子图里的其他 Pexels 摄影师",
                    "· 大象皮的猫：Geirhos et al., texture-vs-shape（CC BY 4.0，https://github.com/rgeirhos/texture-vs-shape）",
                    "· AI 图：Codex（OpenAI 图像生成）：蛋糕柴犬、烤盘上的小狗",
                    "· 切蛋糕：Muse（AI 视频）"],
        "music": f"音乐：亨德尔《降B大调大协奏曲》Op. 6 No. 7 第五乐章 Hornpipe，L'Arco Magico 室内乐团，Antonio Puccio 指挥；"
                 f"知识共享署名许可（CC BY），{MUSIC_URL}（节选，调整了响度）",
        "voice": "配音：AI 合成语音（旁白使用 Louise 的授权声线）",
        "byline": "作者：Yancy Qin | Lucas Academy",
        "tags": ["人工智能", "ai", "计算机视觉", "机器学习", "狗还是面包", "吉娃娃还是松饼", "transformer", "注意力机制", "对抗样本",
                 "claude", "gpt", "科普"],
        "settings": "· 音轨：英文是默认音轨；中文音轨（bread-or-dog.zh.m4a）在「语言」里添加\n"
                    "· 字幕：en 和 zh-Hans 两个 SRT，按英文音轨的时间；中文音轨每句开始的时间一样\n"
                    "· 封面：youtube-cover.zh.jpg（A「这是狗，还是蛋糕？」）；备选 B「AI 还能被骗吗？」\n"
                    "· 经过修改或合成的内容：是（AI 画的蛋糕狗、Muse 切蛋糕的视频、合成语音）\n"
                    "· 面向儿童：否",
    },
}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    head = ("【标题】", "【简介】", "【标签】", "【上传设置】")
    for lang, t in TEXT.items():
        research = t["research"] + "\n" + "\n".join(f"· {name}: {url}" if lang == "en" else f"· {name}：{url}" for name, url in RESEARCH)
        body = "\n\n".join([t["intro"], chapters(lang), t["how"], research, "\n".join(t["credits"]), t["music"], t["voice"],
                            t["byline"], hashtags(t["tags"])])
        text = f"{head[0]}\n{t['title']}\n\n{head[1]}\n{body}\n\n{head[2]}\n{tags(t['tags'])}\n\n{head[3]}\n{t['settings']}\n"
        (OUT / f"youtube-description.{lang}.txt").write_text(text)
        print(lang, len(body), "characters in the description")


if __name__ == "__main__":
    main()
