"""Each film's YouTube upload text: 【标题】【简介】【标签】【上传设置】 (README "YouTube tags").

    python3 scripts/fun-informatics-04/youtube.py [--lang en]

Chapters come from public/fun-informatics-04/timeline.json; the credits list only the sources the film's shots
actually use (footage-sources.json, clips.json); tags follow scripts/youtube_tags.py. Writes
out/fun-informatics-04/delivery/youtube-description.<lang>.txt.
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from youtube_tags import hashtags, tags  # noqa: E402

LANG = sys.argv[sys.argv.index("--lang") + 1] if "--lang" in sys.argv else "zh"
PUB = ROOT / "public/fun-informatics-04"
OUT = ROOT / "out/fun-informatics-04/delivery"
FILM = ROOT / f"out/fun-informatics-04/{LANG}/delivery/fun-informatics-04.{LANG}.mp4"
TITLE = "诺贝尔奖：光遗传学是什么？从信息学的角度看｜趣味信息学4"
OWN_TAGS = ["趣味信息学", "光遗传学", "诺贝尔奖", "信息学", "神经科学", "科普"]
MORE_TAGS = ["通道视紫红质", "编码与解码", "比特", "绿藻", "眼睛", "视网膜", "诺贝尔生理学或医学奖", "optogenetics", "nobel prize"]
INTRO = """你有没有想过：要是大脑里也有开关，按一下，会发生什么？

2026 年的诺贝尔生理学或医学奖，颁给了光遗传学。它的故事从一碟绿水开始：一个单细胞的小绿藻，怎么知道光在哪边？科学家在它身上找到一道「光一照就开」的门，把它装进神经细胞，从外面用光就能按下神经细胞的开关。后来，一位看不见东西的病人戴上一副会发光的眼镜，练了几个月，认出了马路上的斑马线（只有一位病人，部分恢复，治疗还在临床试验中）。

这一期，我们从信息学的角度看光遗传学：开关和比特，编码和解码，最后聊聊圣经里的光。"""
SOURCES = """资料
· 诺贝尔奖新闻稿和科普背景：https://www.nobelprize.org/prizes/medicine/2026/press-release/
· 那位病人：Sahel 等，Nature Medicine，2021（doi:10.1038/s41591-021-01351-4）"""


def mmss(s: float) -> str:
    s = int(s)
    return f"{s // 60}:{s % 60:02d}"


def duration(path: Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                         capture_output=True, text=True).stdout
    return float(out or 0)


EN = {
    "title": "The Nobel Prize: What Is Optogenetics? Seen Through Informatics | Fun Informatics 4",
    "own": ["fun informatics", "optogenetics", "nobel prize", "informatics", "neuroscience", "science for kids"],
    "more": ["channelrhodopsin", "encoding and decoding", "bits", "algae", "the eye", "retina",
             "nobel prize in physiology or medicine", "光遗传学"],
    "intro": """Have you ever wondered: if the brain had switches too, what would happen if you pressed one?

The 2026 Nobel Prize in Physiology or Medicine went to the discoveries behind optogenetics. Its story starts with a dish of green water: how does a single-celled alga know where the light is? Scientists found a "door" in it that opens when light shines on it, put it into nerve cells, and could then press a nerve cell's switch from the outside, with light. Later, a man who could no longer see wore a pair of glasses that give off light, practised for a few months, and began to make out the crosswalk on the street (one patient, partial recovery; the treatment is still in clinical trials).

In this episode, we look at optogenetics through the lens of informatics: switches and bits, encoding and decoding, and, at the end, light in the Bible.""",
    "sources": """Sources
· The Nobel Prize press release and popular science background: https://www.nobelprize.org/prizes/medicine/2026/press-release/
· The patient: Sahel et al., Nature Medicine, 2021 (doi:10.1038/s41591-021-01351-4)""",
    "chapters": {"OG00": "Does the Brain Have Switches?", "dish": "A Dish of Green Water", "OG01": "Switches: 0 and 1 from Episode 1"},
}


def main() -> None:
    tl = json.loads((PUB / f"timeline.{LANG}.json").read_text())
    clips = json.loads((PUB / "clips.json").read_text())
    src = json.loads((ROOT / "docs/fun-informatics-04/footage-sources.json").read_text())
    used = {clips[s["clip"]]["source"] for s in tl["shots"] if s.get("clip")}
    pexels = sorted({src["pexels"][s[7:]]["by"] for s in used if s.startswith("pexels:")})
    commons = [src["commons"][s[8:]] for s in sorted(used) if s.startswith("commons:")]
    dish = tl["lines"]["og00-06"]["start"] - 0.5

    if LANG == "zh":
        names = {"OG00": "大脑里也有开关吗？", "OG01": "开关：回顾第一期的 0 和 1"}
        chapters = [(0.0, names["OG00"]), (dish, "一碟绿水")]
        chapters += [(c["start"], names.get(c["id"], c["name"])) for c in tl["chapters"][1:]]
        credits = ["画面",
                   "· 诺贝尔奖插图：© The Nobel Committee for Physiology or Medicine. Ill. Mattias Karlén（中文标注是本片加的）",
                   *[f"· 实验录像（Wikimedia Commons）：{c['by']}，{c['license']}，https://commons.wikimedia.org/wiki/File:{c['file']}"
                     for c in commons],
                   f"· 实拍（Pexels）：{'、'.join(pexels)}",
                   "· 趣味信息学第一期的画面",
                   "· 标「AI 生成 · 示意」的画面由 AI 生成（视频片段用 Muse，图片用 Codex）",
                   "音乐：莫扎特《小星星变奏曲》K. 265，Simone Renzi 演奏，CC BY 3.0，"
                   "https://commons.wikimedia.org/wiki/File:Mozart_-_12_Variations_K._265_-_Simone_Renzi.mp3（按段落剪辑）",
                   "经文：和合本",
                   "配音：AI 合成语音（旁白使用 Louise 的授权声线）"]
        title, intro, sources, byline, own, more = TITLE, INTRO, SOURCES, "作者：Yancy Qin | Lucas Academy", OWN_TAGS, MORE_TAGS
        heading = "章节"
    else:
        c_en = EN["chapters"]
        chapters = [(0.0, c_en["OG00"]), (dish, c_en["dish"])]
        chapters += [(c["start"], c_en.get(c["id"], c["en"])) for c in tl["chapters"][1:]]
        credits = ["Pictures",
                   "· Illustrations: © The Nobel Committee for Physiology or Medicine. Ill. Mattias Karlén",
                   *[f"· Lab recording (Wikimedia Commons): {c['by']}, {c['license']}, https://commons.wikimedia.org/wiki/File:{c['file']}"
                     for c in commons],
                   f"· Footage (Pexels): {', '.join(pexels)}",
                   "· Pictures from Fun Informatics 1",
                   "· Shots marked \"AI-generated · illustrative\" were made with AI (video clips with Muse, images with Codex)",
                   "Music: W. A. Mozart, 12 Variations on \"Ah vous dirai-je, Maman\", K. 265, played by Simone Renzi, CC BY 3.0, "
                   "https://commons.wikimedia.org/wiki/File:Mozart_-_12_Variations_K._265_-_Simone_Renzi.mp3 (edited into sections)",
                   "Scripture: World English Bible; John 1:5 from the King James Version",
                   "Voice: AI speech synthesis (the narrator uses Louise's licensed voice)"]
        title, intro, sources, byline, own, more = EN["title"], EN["intro"], EN["sources"], "By Yancy Qin | Lucas Academy", EN["own"], EN["more"]
        heading = "Chapters"
    chapter_text = "\n".join(f"{mmss(t)} {n}" for t, n in chapters)
    description = "\n\n".join([intro, f"{heading}\n" + chapter_text, sources, "\n".join(credits), byline, hashtags(own)])
    dur = duration(FILM) if FILM.exists() else tl["durationSeconds"]
    if LANG == "zh":
        settings = f"""· 视频：fun-informatics-04.zh.mp4（1920×1080，{mmss(dur)}，−16 LUFS）
· 字幕：fun-informatics-04.zh.zh-Hans.srt（中文），fun-informatics-04.zh.en.srt（英文）
· 缩略图：youtube-cover.zh.jpg（1280×720）
· 视频语言：中文（简体）
· 观众：由你决定；选「专为儿童打造」会关掉评论和个性化广告
· 修改过或合成的内容：是（合成配音；部分画面由 AI 生成，片中已标注）
· 类别：教育
· 章节：简介里的时间点会自动变成章节，第一章是 0:00"""
        count = f"（可直接粘贴，约 {len(description)} 字符，YouTube 上限 5000）"
    else:
        settings = f"""· Video: fun-informatics-04.en.mp4 (1920×1080, {mmss(dur)}, −16 LUFS)
· Captions: fun-informatics-04.en.en.srt (English), fun-informatics-04.en.zh-Hans.srt (Chinese)
· Thumbnail: youtube-cover.en.jpg (1280×720)
· Video language: English
· Audience: your choice; "made for kids" turns off comments and personalised ads
· Altered or synthetic content: yes (synthetic voice; some shots AI-generated, labelled in the film)
· Category: Education
· Chapters: the timestamps in the description become chapters; the first is 0:00"""
        count = f"(paste as is, about {len(description)} characters; YouTube allows 5000)"
    text = f"""【标题 / Title】
{title}

【简介 / Description】{count}
{description}

【标签 / Tags】
{tags([*own, *more])}

【上传设置 / Upload settings】
{settings}
"""
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"youtube-description.{LANG}.txt").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
