"""The voice direction for the Language Bridge films: how each line is *performed*.

The subtitle text (zh/en in src/scripts/reciprocal-doors.json) is the approved
script and never changes here. Each line gets a spoken form (`say`) that may add
only emphasis tags and punctuation (…… ！ ？ ，) -- the words stay identical,
which `apply` checks -- plus a speed, a tone and the pause before it.

The arc, scene by scene:
  RD01 storytelling, curious -> a gentle stumble -> a thoughtful turn ("但……")
  RD02 practical and reassuring, ends warm ("先了解他")
  RD03 a lift of discovery -> two contrasting cases -> the open question
  (Names: Mary = the girl, more at ease in English; Jacob = the boy, more at ease in Chinese.)
  RD04 bright and playful -> the definition, slow -> joyful peak ("都教，也都学！")
  RD05 a small problem -> the aha ("画画！") -> the key term, slow -> a real question
  RD06 the liveliest scene: story, dialogue, "switch!", encouragement, calm teacher
  RD07 a clear rhythmic triad (文字 / 声音 / 图画) -> the principle, deliberate
  RD08 sincere ("还有一件事，很重要") -> hopeful -> heartfelt wish
  RD09 warm, turned to parents -> heartfelt close
  RD10 the title callback -> anticipation -> joyful, warm last line

    python3 scripts/reciprocal-doors-direction.py apply
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "src/scripts/reciprocal-doors.json"

S = "<strong>"
E = "</strong>"


def b(word: str) -> str:
    return f"{S}{word}{E}"


# id: (zh spoken, en spoken, speed, tone, pause-before in seconds or None)
# Chinese spoken text has no "……": in the one lively style it made lines drag
# (pace down to 0.40x of the film); pauses between lines come from the timeline.
# Checked with Whisper after synthesis. Two lessons: a stressed English "can"
# is heard as "can't" (never emphasise it), and wrapping "哪一步难" whole let the
# question end come out as "哪一步呢" -- emphasise the word that must survive.
# speed: 0.82 opening/most weighty · 0.85 weighty · 0.9 base · 0.95 lively
# tone:  默认 (fangfang/louise's own reading) · 亮 (brighter, keeps the reference)
DIRECTION: dict[str, tuple[str, str, float, str, float | None]] = {
    # RD01 · storytelling, curious; a gentle stumble; a thoughtful turn
    "rd01-01": ("想象一个孩子。", "Imagine a child.", 0.82, "默认", 1.0),
    "rd01-02": (f"别人把故事{b('念给他听')}，他{b('能')}说出发生了什么。",
                f"When someone {b('reads a story aloud')}, he can tell us what happened.", 0.9, "默认", 0.8),
    "rd01-03": (f"轮到{b('自己读')}，有些字，却让他停下来。",
                f"When he reads it {b('himself')}, some words... stop him.", 0.85, "默认", 0.6),
    "rd01-04": (f"我们在学习{b('阅读障碍')}的资料时，注意到这样的情况。",
                f"We noticed examples like this while learning about {b('dyslexia')}.", 0.9, "默认", 0.7),
    "rd01-05": (f"有些孩子，{b('认字、拼写')}很困难。",
                f"Some children find {b('word reading and spelling')} difficult.", 0.9, "默认", None),
    "rd01-06": (f"但单看这一点，还{b('不能')}知道这个孩子能{b('理解')}什么、能{b('做')}什么。",
                f"That alone does {b('not')} tell us everything they can {b('understand')}, or {b('do')}.", 0.85, "默认", 0.75),
    # RD02 · practical, reassuring, ends warm
    "rd02-01": (f"所以，我们可以看看：这个孩子{b('需要什么帮助')}？",
                f"So we can ask: what {b('help')} does this child need?", 0.9, "默认", None),
    "rd02-02": (f"如果今天是{b('理解故事')}，可以听、看图，再聊一聊。",
                f"If today's goal is to {b('understand a story')}, we can listen, look at pictures, and talk about it.", 0.95, "默认", None),
    "rd02-03": (f"需要{b('练认字')}时，就{b('认真')}练认字，也给合适的帮助。",
                f"When the goal is {b('word reading')}, we practise reading with suitable support.", 0.9, "默认", None),
    "rd02-04": (f"每个孩子的情况{b('不一样')}，我们要先{b('了解他')}。",
                f"Each child is {b('different')}. We need to get to know the child {b('in front of us')}.", 0.85, "默认", 0.65),
    # RD03 · a lift of discovery; two cases; the open question
    "rd03-01": (f"这启发我们想到{b('中英文学习')}。",
                f"This led us to think about learning... {b('Chinese and English')}.", 0.9, "亮", None),
    "rd03-02": (f"比如，一个孩子能{b('听懂')}中文，却还不认识很多{b('汉字')}。",
                f"One child may {b('understand')} spoken Chinese but know only a few Chinese {b('characters')}.", 0.9, "默认", 0.55),
    "rd03-03": (f"{b('另一个')}孩子读中文比较顺，讲{b('英文')}时却需要帮助。",
                f"{b('Another')} may read Chinese more easily but need help speaking {b('English')}.", 0.9, "默认", None),
    "rd03-04": (f"这些情况和阅读障碍，有{b('不同的原因')}。",
                f"These difficulties have {b('different causes')} from dyslexia.", 0.85, "默认", 0.65),
    "rd03-05": (f"它们提醒我们一个相似的问题：哪一步{b('难')}？还能{b('从哪里开始')}？",
                f"They invite a similar teaching question: {b('which step')} is difficult, and {b('where else')} can we begin?", 0.88, "默认", 0.6),
    # RD04 · bright and playful; the definition, slow; joyful peak
    "rd04-01": (f"我们来设想{b('两个')}孩子。",
                f"Let's imagine... {b('two')} children.", 0.9, "亮", None),
    "rd04-02": (f"Jacob 用{b('中文')}讲故事比较顺，Mary 用{b('英文')}讲比较顺。",
                f"Jacob tells stories more easily in {b('Chinese')}. Mary tells them more easily in {b('English')}.", 0.92, "默认", None),
    # The names are English words now, so the swap is carried by the languages.
    "rd04-03": (f"学{b('中文')}时，Jacob 可以帮 Mary；学{b('英文')}时，Mary 可以帮 Jacob。",
                f"Jacob can help Mary with {b('Chinese')}, and Mary can help Jacob with {b('English')}.", 0.92, "默认", None),
    "rd04-04": (f"这就是“{b('互惠')}”：我有能帮{b('你')}的地方，你也有能帮{b('我')}的地方。",
                f"That is... {b('reciprocity')}: I have something that can help {b('you')}, and you have something that can help {b('me')}.", 0.85, "默认", 0.85),
    "rd04-05": (f"两个人{b('都教')}，也{b('都学')}！",
                f"{b('Both')} children teach, and {b('both')} learn!", 0.9, "亮", 0.55),
    # RD05 · a small problem; the aha; the key term; a real question
    "rd05-01": (f"可是，一开始话还说不通，{b('怎么办')}？",
                f"What if they {b('cannot yet')} explain everything to each other?", 0.88, "默认", None),
    "rd05-02": (f"我们想到{b('画画')}！",
                f"We thought of... {b('drawing')}!", 0.9, "亮", 0.85),
    "rd05-03": (f"两个人可以先画{b('同一个')}故事，看{b('同一张')}图。",
                f"They can draw the {b('same')} story and look at the {b('same')} picture.", 0.95, "默认", None),
    "rd05-04": (f"图画让他们有一件可以{b('一起看')}、{b('一起说')}的事。",
                f"Now they have something to {b('look at')} and {b('talk about')} together.", 0.9, "默认", None),
    "rd05-05": (f"这是他们{b('共同的渠道')}。",
                f"Drawing is {b('a channel they share')}.", 0.85, "默认", 0.55),
    "rd05-06": (f"看图之后，也要问问对方：你想表达的，是{b('这个意思')}吗？",
                f"They still need to ask each other: is this what you {b('meant')}?", 0.9, "默认", 0.6),
    # RD06 · the liveliest scene
    "rd06-01": (f"比如，他们一起画一个小故事：{b('杯子倒了')}，朋友来{b('帮忙')}。",
                f"For example, they draw a small story: {b('a cup tips over')}, and a friend comes to {b('help')}.", 0.95, "亮", None),
    "rd06-02": ("", "", 0.95, "默认", None),  # parts: narration lead-in + the taught phrase
    "rd06-03": ("", "", 0.95, "默认", None),
    "rd06-04": (f"然后，{b('交换')}！",
                f"Then they... {b('switch')}!", 0.9, "亮", 0.55),
    "rd06-05": (f"Mary 试着说{b('中文')}，Jacob 试着说{b('英文')}。",
                f"Mary tries the {b('Chinese')}, and Jacob tries the {b('English')}.", 0.92, "默认", None),
    "rd06-06": (f"说不顺？可以听一听，{b('再试一次')}。",
                f"If a phrase is difficult, they can listen, and {b('try again')}.", 0.9, "亮", None),
    "rd06-07": (f"遇到不认识的字，就把这个字{b('找出来')}，{b('一起学')}。",
                f"If a written word is unfamiliar, they {b('find it')} and learn it {b('together')}.", 0.92, "默认", None),
    "rd06-08": (f"老师在旁边，帮他们{b('确认意思')}。",
                f"Their teacher helps them {b('check the meaning')}.", 0.88, "默认", 0.6),
    # RD07 · a clear triad, then the principle
    "rd07-01": (f"{b('文字')}，让我们学着{b('自己读')}。",
                f"{b('Written words')} help us learn to read {b('for ourselves')}.", 0.9, "默认", None),
    "rd07-02": (f"{b('声音')}，可以示范{b('怎么说')}。",
                f"{b('Sound')} can show us how a phrase is {b('spoken')}.", 0.9, "默认", 0.35),
    "rd07-03": (f"{b('图画')}，帮我们{b('一起')}谈故事。",
                f"{b('Pictures')} give us something to discuss {b('together')}.", 0.9, "默认", 0.35),
    "rd07-04": (f"什么时候用哪一种，要看这次{b('想学什么')}。",
                f"We choose what to use by asking what we {b('want to learn')}.", 0.85, "默认", 0.75),
    "rd07-05": (f"{b('理解故事')}时，可以先看图、听故事。",
                f"To {b('understand a story')}, we may begin with pictures and listening.", 0.92, "默认", 0.55),
    "rd07-06": (f"{b('练认字')}时，可以{b('先试着读')}，需要时，再用声音和图画帮忙。",
                f"To {b('practise word reading')}, we can {b('try reading first')}, and add sound or pictures when needed.", 0.92, "默认", None),
    # RD08 · sincere, hopeful, heartfelt
    "rd08-01": (f"还有一件事，{b('很重要')}：",
                f"There is something else... we {b('care about')}.", 0.82, "默认", 1.0),
    "rd08-02": (f"学英文时，中文{b('也')}可以继续用；",
                f"Chinese can {b('keep growing')} while a child learns English.", 0.9, "默认", 0.6),
    "rd08-03": (f"学中文时，英文{b('也')}有用。",
                f"English {b('still matters')} while a child learns Chinese.", 0.9, "默认", 0.3),
    "rd08-04": (f"喜欢画画的孩子，可以{b('继续画')}，也用画{b('帮助大家')}学。",
                f"A child who enjoys drawing can {b('keep drawing')}, and use it to {b('help the group')} learn.", 0.92, "亮", 0.55),
    "rd08-05": (f"我们希望孩子学会{b('新的')}东西，同时，把{b('原来会的')}，用得更好。",
                f"We want children to learn something {b('new')}, while making good use of what they {b('already know')}.", 0.85, "默认", 0.7),
    # RD09 · warm, turned to parents
    "rd09-01": (f"{b('父母和孩子')}，也可以这样试。",
                f"{b('Parents and children')} can try this too.", 0.9, "默认", 1.0),
    "rd09-02": (f"父母更习惯{b('中文')}，孩子更习惯{b('英文')}，可以一起画、一起讲{b('同一个')}故事。",
                f"If parents are more comfortable in {b('Chinese')} and children in {b('English')}, they can draw and tell the {b('same')} story together.", 0.92, "默认", None),
    "rd09-03": (f"父母说出自己的意思，孩子帮助找英文的说法，再{b('一起确认')}。",
                f"A parent shares what they mean, a child helps find the English words, and they {b('check it together')}.", 0.92, "默认", None),
    "rd09-04": (f"{b('两代人')}都有可以{b('分享')}的东西，也都有可以{b('学习')}的东西。",
                f"{b('Both generations')} have something to {b('share')}, and something to {b('learn')}.", 0.85, "默认", 0.7),
    # RD10 · callback, anticipation, joyful close
    "rd10-01": (f"这就是“{b('语言的桥')}”。",
                f"This is our... {b('Language Bridge')}.", 0.85, "默认", 1.0),
    "rd10-02": (f"我们从阅读障碍教育得到启发，正在设计{b('中英双语')}的多媒体学习方式。",
                f"Inspired by dyslexia education, we are designing ways to learn through {b('Chinese, English')}, words, sound, and pictures.", 0.9, "默认", 0.6),
    "rd10-03": (f"从{b('一个共同的故事')}开始：",
                f"We can begin with {b('one shared story')}.", 0.88, "默认", 0.6),
    "rd10-04": (f"{b('你教我')}一句，{b('我教你')}一句，我们{b('一起')}多懂一点！",
                f"{b('You')} teach me a phrase, {b('I')} teach you a phrase, and we understand a little more {b('together')}!", 0.85, "亮", 0.55),
}

# rd06-02 / rd06-03 are spoken in parts; the taught phrase keeps its slow, plain reading.
PART_SPEED = {"narration": 0.95, "demo": 0.75}


def words(text: str, lang: str) -> str:
    text = re.sub(r"</?strong>", "", text).replace("’", "'")
    if lang == "zh":
        return re.sub(r"[^一-鿿A-Za-z']", "", text)
    return " ".join(re.sub(r"[^a-z' ]", " ", text.lower()).split())


def apply() -> None:
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    chunks = {c["id"]: c for s in source["segments"] for c in s["chunks"]}
    if set(chunks) != set(DIRECTION):
        raise SystemExit(f"Direction/script mismatch: {sorted(set(chunks) ^ set(DIRECTION))}")
    for cid, (zh, en, speed, tone, pause) in DIRECTION.items():
        chunk = chunks[cid]
        # The approved subtitle text is plain; strip any tags left by earlier drafts.
        chunk["zh"] = re.sub(r"</?strong>", "", chunk["zh"])
        chunk["en"] = re.sub(r"</?strong>", "", chunk["en"])
        for key in ("say", "speed", "tone", "pause"):
            chunk.pop(key, None)
        if "parts" in chunk:
            for track in ("zh", "en"):
                for part in chunk["parts"][track]:
                    part["speed"] = PART_SPEED["demo" if part.get("demo") else "narration"]
        else:
            for lang, spoken in (("zh", zh), ("en", en)):
                if words(spoken, lang) != words(chunk[lang], lang):
                    raise SystemExit(f"{cid} {lang}: spoken words differ from the subtitle\n  say: {words(spoken, lang)}\n  sub: {words(chunk[lang], lang)}")
            chunk["say"] = {"zh": zh, "en": en}
            chunk["speed"] = speed
        if tone != "默认":
            chunk["tone"] = tone
        if pause is not None:
            chunk["pause"] = pause
    SOURCE.write_text(json.dumps(source, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    counts = {t: sum(1 for d in DIRECTION.values() if d[3] == t) for t in ("默认", "亮")}
    emphasis = sum(d[0].count(S) for d in DIRECTION.values())
    print(f"Direction applied: {len(DIRECTION)} lines, {emphasis} zh emphases, tones {counts}")


if __name__ == "__main__":
    {"apply": apply}[sys.argv[1]]()
