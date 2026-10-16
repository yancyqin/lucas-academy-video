"""Narration inputs for 「一根冰棍，要花多少钱？」 (FUN-ECONOMICS-01.md), from docs/fun-economics-01/{zh,en}-edit.md.

Two voices read each film. The narrator, 姐姐, is Louise with the project default (README "Narration voices").
Mary is Eunice: her profile only has an English reference, so her Chinese lines use instruct mode with the
prompt Yancy picked from the four test takes on 2026-10-15 (prompt D); her English lines use the same prompt.
Lines that start with 「Mary：」 / "Mary:" are hers; the prefix is neither read nor captioned.

What the voice READS differs from what the captions SHOW, done here so no line is hand-edited. Chinese: Arabic
numerals are spelled out (年份 digit by digit, 2 before a measure word as 两), and 行 in the sense of a row is
written 航 so it cannot come out as xíng. English: numbers, $ and the signs × − + = are spelled out in words.

  python3 scripts/fun-economics-01/narration.py        # writes both languages
  then scripts/fun-economics-01/narrate.py (lucas-academy-media's Python) voices each file.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "docs/fun-economics-01"
OUT = ROOT / "public/fun-economics-01/narration"
sys.path.insert(0, str(ROOT / "scripts"))
from voice_defaults import line_settings  # noqa: E402

SECTION = re.compile(r"^## ([A-Z]{2}\d\d)\b")  # OC00 here; HX00 in 「你会算 7×8 吗？」
OVERALL = re.compile(r"^(整体语气|整体语速|Overall tone|Overall speed):\s*(.*)$")
LINE = re.compile(r"^- ([a-z]{2}\d\d-\d\d) \| (.+)$")
TRANSLATION = re.compile(r"^> (.+)$")  # under a line: its translation, the other-language captions of this film
NARRATOR = {"zh": "louise/zh", "en": "louise/en"}
MARY = {"zh": "Mary：", "en": "Mary:"}
MARY_VOICE = "eunice/en"
MARY_PROMPT = "Speak like a curious, playful seven-year-old girl: bright, light and innocent."
MARY_SPEED = 1.05
# Questions put to the viewer get their own curious instruction (FUN-ECONOMICS-01.md §6, memory: questions read curious).
QUESTION = {
    "zh": "请用好奇、温和的语气提问，像和孩子一起想一想，不着急，句末微微上扬。",
    "en": "Please ask this with gentle, curious wonder, like thinking it over together with a child: unhurried, rising a little at the end.",
}
QUESTIONS = {"oc00-01", "oc00-05", "oc04-05", "oc04-17", "oc07-01"}
DIGITS = "零一二三四五六七八九"
# Re-takes after the Whisper check, and readings: a changed text gives a new take; the captions keep the script's words.
RETAKE = {
    "zh": {
        "oc00-07": ("对，一共七块钱。买冰棍是这样，那学一样东西，又要花多少钱呢？", "对。一共七块钱。买冰棍是这样；那学一样东西，又要花多少钱呢？"),  # 冰棍 heard as 冰罐
        "oc04-01": ("滚瓜烂熟", "滚瓜烂赎"),  # 熟 heard as 树 by both models: 赎 is shú
        "oc04-15": ("第四条路，只用翻倍和减半。", "第四条路：只用翻倍，和减半。"),  # the first 翻倍 heard as 半倍
        "oc06-03": ("耶稣说：「马大！马大！", "耶稣说：马大！马大！"),  # 耶稣 heard as 技术 / 祭祀
        "oc04-02": ("七八五十六！", "七八，五十六！"),  # Mary: heard as 756 / 750
    },
    "en": {
        "oc02-03": ("Frédéric Bastiat", "Frederic Bastia"),  # French: the final t is silent
        # can't was heard as can (the meaning flips): read cannot
        "oc02-06": ("a fee and a new skill. What you can't see is what that afternoon would have been: maybe",
                    "a fee, and a new skill! What you cannot see is what that afternoon would have been. Maybe"),  # skill heard as scale
        "oc03-01": ("another price you can't see", "another price you cannot see"),
        "oc05-04": ("Seeing what can't be seen", "Seeing what cannot be seen"),
        "oc04-07": ("Path two: split and join.", "Path two. Split, and join."),  # heard as 「Pi on join」 by both models
    },
}
MEASURE = "根个份行列枚块只次"
ROWS = ("oc04",)  # sections whose 行 means a row of dots (háng); anywhere else it needs a look
CUES = 51  # v0.8: the finger path is one line (oc04-08); oc04-09..14 moved to 「你会算 7×8 吗？」
ONES = ("zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen "
        "seventeen eighteen nineteen").split()
TENS = "_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()


def cn_number(n: int) -> str:
    if n < 10:
        return DIGITS[n]
    if n < 100:
        tens, ones = divmod(n, 10)
        return ("" if tens == 1 else DIGITS[tens]) + "十" + (DIGITS[ones] if ones else "")
    if n == 100:  # the finger road's 10 × 10
        return "一百"
    raise ValueError(f"no spoken form for {n}")


def en_number(n: int) -> str:
    if n < 20:
        return ONES[n]
    if n < 100:
        tens, ones = divmod(n, 10)
        return TENS[tens] + (f"-{ONES[ones]}" if ones else "")
    if n == 100:
        return "one hundred"
    raise ValueError(f"no spoken form for {n}")


def spoken_zh(text: str) -> str:
    text = re.sub(r"</?strong>", "", text)
    text = re.sub(r"(\d{4})\s*年", lambda m: "".join("零一二三四五六七八九"[int(d)] for d in m[1]) + "年", text)  # 〇 was dropped (oc02-03)
    text = re.sub(r"\b2\s*(?=[" + MEASURE + "])", "两", text)
    text = re.sub(r"\d+", lambda m: cn_number(int(m[0])), text)
    text = re.sub(r"\s+(?=[一-鿿])|(?<=[一-鿿])\s+", "", text)
    text = text.replace("行", "航")  # every 行 in this script is a row of dots (build() checks they are all in OC04)
    assert not re.search(r"\d", text), text
    return text


def spoken_en(text: str) -> str:
    text = re.sub(r"</?strong>", "", text)
    text = re.sub(r"\b(1[0-9])(\d\d)\b", lambda m: f"{en_number(int(m[1]))} {en_number(int(m[2]))}", text)  # 1850: eighteen fifty
    text = re.sub(r"\$(\d+)", lambda m: en_number(int(m[1])) + (" dollar" if m[1] == "1" else " dollars"), text)
    for sign, word in (("×", "times"), ("−", "minus"), ("+", "plus"), ("=", "equals")):
        text = text.replace(f" {sign} ", f" {word} ")
    text = re.sub(r"\d+", lambda m: en_number(int(m[0])), text)
    text = re.sub(r"(^|[.!?]\s+)([a-z])", lambda m: m[1] + m[2].upper(), text)  # a sentence that starts with a number
    assert not re.search(r"[\d×−+=$]", text), text
    return text


def parse(lang: str):
    cues, tone, section, last = {}, "", None, None
    for raw in (SRC / f"{lang}-edit.md").read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if (m := TRANSLATION.match(line)) and last:
            cues[last]["translation"] = m[1].strip()
            last = None
        elif m := OVERALL.match(line):
            if m[1] in ("整体语气", "Overall tone"):
                tone = m[2].strip()
        elif m := SECTION.match(line):
            section = m[1].lower()
        elif m := LINE.match(line):
            cid, text = m.groups()
            assert cid.startswith(section), f"{cid} not under {section}"
            cues[cid] = {"section": section, "text": text.strip()}
            last = cid
    return cues, tone


def build(lang: str) -> list:
    cues, tone = parse(lang)
    assert len(cues) == CUES, len(cues)
    assert all(c.get("translation") for c in cues.values()), "every line needs its > translation (the other captions)"
    if lang == "zh":
        assert all(cid.startswith(ROWS) for cid, cue in cues.items() if "行" in cue["text"]), "行 outside a rows section: check its reading"
    spoken = spoken_zh if lang == "zh" else spoken_en
    narrator, mary, captions = [], [], []
    for cid, cue in cues.items():
        text, speaker = cue["text"], "narrator"
        if text.startswith(MARY[lang]):
            text, speaker = text[len(MARY[lang]):].strip(), "mary"
        read = spoken(text)
        if cid in RETAKE[lang]:
            old, new = RETAKE[lang][cid]
            assert old in read, (cid, read)
            read = read.replace(old, new)
            if lang == "zh" and cid == "oc06-03":
                read = read.replace("。」", "。")
        if speaker == "mary":
            mary.append({"id": cid, "text": read, "instruct": MARY_PROMPT, "mode": "instruct", "speed": MARY_SPEED})
        else:
            settings = line_settings(NARRATOR[lang], QUESTION[lang] if cid in QUESTIONS else tone)
            narrator.append({"id": cid, "text": read, **settings})
        captions.append({"id": cid, "section": cue["section"], "speaker": speaker,
                         "text": re.sub(r"</?strong>", "", text), "translation": re.sub(r"</?strong>", "", cue["translation"]),
                         "spoken": read})
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{lang}.json").write_text(json.dumps({"voice": NARRATOR[lang], "language": lang, "lines": narrator}, ensure_ascii=False, indent=1) + "\n")
    (OUT / f"mary-{lang}.json").write_text(json.dumps({"voice": MARY_VOICE, "language": lang, "lines": mary}, ensure_ascii=False, indent=1) + "\n")
    (OUT / f"cues.{lang}.json").write_text(json.dumps(captions, ensure_ascii=False, indent=1) + "\n")
    print(f"{lang}: {len(narrator)} narrator lines, {len(mary)} Mary lines -> {OUT}")
    return [c["id"] for c in captions]


def main() -> None:
    zh, en = build("zh"), build("en")
    assert zh == en, "zh and en must have the same cue ids in the same order"


if __name__ == "__main__":
    main()
