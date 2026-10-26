"""Check the finished film, render the cover and write the upload text for "How Do You Solve a 5×5 Cube?"
(CUBE-5X5.md §6). Never uploads; everything lands in out/cube-5x5/delivery/.

    python3 scripts/cube-5x5/package.py [--no-cover]

The 2×2 film's package.py does the checks (no black frames, -16 LUFS, true peak at or under -1 dBTP on both
audio streams and on the Chinese track, the timeline's length) and the cover (Cube5x5Cover, 1280×720); this gives
it the 5×5 film's names, chapters and description. The series' tags are the 2×2 film's with #5x5 for #2x2.
"""
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("cube2x2_package", ROOT / "scripts/cube-2x2/package.py")
c2 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c2)
c2.FILM, c2.COVER = "cube-5x5", "Cube5x5Cover"
c2.PUB = ROOT / "public/cube-5x5"
c2.OUT = ROOT / "out/cube-5x5"
c2.DELIVERY = c2.OUT / "delivery"
c2.SERIES_TAGS = ["5x5" if tag == "2x2" else tag for tag in c2.SERIES_TAGS]
fi03 = c2.fi03

TITLE = {"en": "How Do You Solve a 5×5 Cube?", "zh": "五阶魔方怎么还原？"}
c2.CHAPTERS = {
    "en": {"cf00": "The challenge, and the online cube", "cf01": "The idea: a 3×3 inside", "cf02": "The letters",
           "cf03": "Part 1, step 1: the white cross", "cf04": "Step 2: the white corners", "cf05": "Step 3: the middle layer",
           "cf06": "Step 4: the yellow cross", "cf07": "Step 5: the yellow face", "cf08": "Step 6: the yellow corners",
           "cf09": "Step 7: the yellow edges", "cf10": "Part 2: the edges (commutators)", "cf11": "Part 3: the centres",
           "cf12": "Once more, and practise online"},
    "zh": {"cf00": "挑战，和网页魔方", "cf01": "一张图看懂：里面藏着三阶", "cf02": "字母",
           "cf03": "第一部分，第 1 步：白色十字", "cf04": "第 2 步：白色的角", "cf05": "第 3 步：中间层",
           "cf06": "第 4 步：黄色十字", "cf07": "第 5 步：顶面全黄", "cf08": "第 6 步：黄色的角",
           "cf09": "第 7 步：黄色的棱", "cf10": "第二部分：拼边（交换子）", "cf11": "第三部分：拼中心",
           "cf12": "再看一遍，在网上练"},
}


def text(tl, report):
    ending = {lang: next(c for c in tl["cues"] if c["id"] == "cf12-03")[lang] for lang in ("en", "zh")}
    en = f"""A 75-digit number: that's how many ways a 5×5 cube can be scrambled. Most people never solve one. By the end of this video, you will.
The secret: inside every 5×5 hides a 3×3. This film solves it in three parts: the frame, like a 3×3 (all seven beginner steps, so you learn the 3×3 too); then the edges; then the centres. Parts 2 and 3 use one big idea, the commutator: A B A′ B′. Every move gets a card on screen, every time it is used.
Already know the 3×3? Skip to Part 2 with the chapters below.

Try it online, right now: https://is.lucasacademy.org/cube/ — free. Press "Step by step" and it walks you through every move, on any cube from 2×2 to 11×11.

中文配音：在音轨设置里选「中文」。

By Lucas Academy Team
The narration is AI-generated with Louise's licensed voices (English, and a Chinese audio track). Every picture comes from Lucas Academy's web cube.

{c2.chapters(tl, "en")}

Music: {c2.MUSIC}
The recording was excerpted, joined, crossfaded and levelled for this film.

{ending["en"]}

{c2.hashtags()}
"""
    zh = f"""五阶魔方能打乱成一个七十五位数那么多种样子，大多数人一次都没还原过。看完这个视频，你就会了。
秘密是：每个五阶魔方里都藏着一个三阶。这一集分三部分还原：先拼骨架，就像拼三阶（初学者七步全讲，三阶也一起学会）；再拼边；最后拼中心。第二、三部分只用一个大想法：交换子 A B A′ B′。每用到一个转动，屏幕上都有它的卡片。
已经会三阶？用下面的章节直接跳到第二部分。

现在就能在网上试：https://is.lucasacademy.org/cube/ 免费。点 Step by step，它会一步一步带你还原，二阶到十一阶都可以。

作者 Lucas Academy Team
配音为 AI 合成，使用 Louise 的授权声线（英文原声，另有中文音轨）。

{c2.chapters(tl, "zh")}

背景音乐：{c2.MUSIC}

{ending["zh"]}
"""
    assert len(en) <= 5000 and len(zh) <= 5000
    return f"""【标题 / Title】
{TITLE['en']} The 3×3 Hiding Inside

【简介 / Description】（{len(en)}）
{en}
【中文标题和简介 / Chinese title and description】（YouTube Studio → 语言 / Languages → 添加翻译）
{TITLE['zh']}｜里面藏着一个三阶

{zh}
【标签 / Tags】
{c2.tags()}

【上传设置 / Upload settings】
· Video: cube-5x5.mp4 (1920×1080, 30 fps, {fi03.stamp(round(report['seconds']))}; its first audio stream is English, {report['lufs']['en']:.0f} LUFS)
· Chinese audio track: cube-5x5.zh-track.wav (same length; Studio → Languages → Add audio track → 中文 / Chinese)
· Captions: cube-5x5.en.srt (English), cube-5x5.zh-Hans.srt (中文)
· Thumbnail: cover.jpg (1280×720)
· Video language: English
· Audience: the author's choice
· Altered or synthetic content: yes (synthetic narration)
· Category: Education
"""


if __name__ == "__main__":
    c2.DELIVERY.mkdir(parents=True, exist_ok=True)
    tl, report = c2.check()
    (c2.DELIVERY / "upload.txt").write_text(text(tl, report))
    if "--no-cover" not in sys.argv:
        c2.cover()
    print("upload.txt" + ("" if "--no-cover" in sys.argv else ", cover.jpg"))
