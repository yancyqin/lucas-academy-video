"""Narration inputs for 「法国人走上街头，出路在哪里？」 (NEWS-EDUCATION-01.md) from docs/news-education-01/{zh,en}-edit.md.

Both tracks are Yancy's voice (yancy/zh): Chinese in zero-shot-instruct, English cross-lingual with the instruction in
the system slot (narrate.py), each section with its own delivery. The owner (2026-10-20): the opening must sound grave,
not light. Captions keep the script; the voice reads numbers spelled out (English) and a few respellings.

  python3 scripts/news-education-01/narration.py      # writes public/news-education-01/narration/{zh,en}.json + cues
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs/news-education-01"
OUT = ROOT / "public/news-education-01/narration"
LINE = re.compile(r"^- (sc\d\d-\d\d) \| (.+)$")
VOICE = "yancy/zh"

TONE = {
    "zh": {
        "grave": "请用沉稳、凝重的语气，像新闻纪录片的旁白，语速稍慢，不要轻快。",
        "story": "请用沉稳、平和的语气，像在给家长们讲一段历史，清楚，不急，不要轻快。",
        "scripture": "请用平静、庄重、温和的语气，慢慢地说。",
        "class": "请用平和、真诚的语气，像老师和家长认真地聊天，不急不慢。",
        "personal": "请用真诚、低沉一点的语气，像在讲一件自己后悔的事，慢慢地说。",
        "hope": "请用温和、真诚、带着希望的语气，慢慢地说。",
        "question": "请用温和、真诚的语气提问，像在邀请对方一起想一想，不着急。",
    },
    "en": {
        "grave": "Speak in a grave, serious, measured voice, like a documentary narrator reporting difficult news. Slow and steady, never light or cheerful.",
        "story": "Speak in a calm, steady, serious voice, like telling parents a piece of history. Clear and unhurried, never light or cheerful.",
        "scripture": "Speak in a quiet, reverent, gentle voice, slowly.",
        "class": "Speak in a calm, sincere voice, like a teacher talking earnestly with parents. Unhurried.",
        "personal": "Speak in a sincere, low, reflective voice, like telling a story you regret. Slowly.",
        "hope": "Speak in a warm, sincere, hopeful voice, slowly.",
        "question": "Ask this warmly and sincerely, inviting the listener to think it over. Unhurried.",
    },
}
SECTION_TONE = {"sc00": "grave", "sc01": "grave", "sc02": "story", "sc03": "story", "sc04": "story", "sc05": "story",
                "sc06": "scripture", "sc07": "story", "sc08": "class", "sc09": "personal", "sc10": "hope", "sc11": "hope"}
LINE_TONE = {"sc03-04": "grave", "sc11-01": "question"}
# What the voice reads where it differs from the caption (polyphones, names).
SPOKEN = {
    "zh": {
        "sc05-03": ("选立官长", "选立官掌"),  # 长 = zhǎng here
    },
    "en": {
        # of their own accord was heard as 「if they're on a cord」; the plain rewrite then stopped after its first
        # sentence (2026-10-20): one breath, commas instead of full stops
        "sc04-21": ("Institutions limit power. People choose to lay power down. We need both.",
                    "Institutions limit power, and people choose to lay power down: we need both."),
    },
}

ONES = "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen".split()
TENS = "_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()


def words(n: int) -> str:
    if n < 20:
        return ONES[n]
    if n < 100:
        t, o = divmod(n, 10)
        return TENS[t] + (f"-{ONES[o]}" if o else "")
    if n < 1000:
        h, r = divmod(n, 100)
        return f"{ONES[h]} hundred" + (f" {words(r)}" if r else "")
    if n < 1_000_000:
        th, r = divmod(n, 1000)
        return f"{words(th)} thousand" + (f" {words(r)}" if r else "")
    raise ValueError(n)


def year(n: int) -> str:
    hi, lo = divmod(n, 100)
    if lo == 0:
        return f"{words(hi)} hundred"
    return f"{words(hi)} {'oh-' + ONES[lo] if lo < 10 else words(lo)}"


ORD = {"17": "seventeenth"}


def spoken_en(text: str) -> str:
    text = text.replace("Jr.", "Junior").replace(" AI,", " A.I.,").replace("Ask AI", "Ask A.I.")
    text = re.sub(r"October (\d{1,2})\b", lambda m: "October " + ORD[m[1]], text)
    text = re.sub(r"\b(1[5-9]\d\d|20\d\d)\b", lambda m: year(int(m[1])), text)
    text = re.sub(r"\b(\d{1,3}(?:,\d{3})+|\d+)\b", lambda m: words(int(m[1].replace(",", ""))), text)
    assert not re.search(r"\d", text), text
    return text


def parse(lang: str) -> dict:
    cues = {}
    for raw in (DOCS / f"{lang}-edit.md").read_text(encoding="utf-8").splitlines():
        if m := LINE.match(raw.strip()):
            cues[m[1]] = m[2].strip()
    return cues


def build(lang: str) -> list:
    cues = parse(lang)
    lines, captions = [], []
    for cid, text in cues.items():
        read = text
        if lang == "en":
            read = spoken_en(read)
        if cid in SPOKEN[lang]:
            old, new = SPOKEN[lang][cid]
            assert old in read, (cid, read)
            read = read.replace(old, new)
        if lang == "zh":
            read = read.replace("〇", "零")  # 二〇二六 came out garbled (heard 「这课 26 年」, 2026-10-20): the voice reads 零
            assert not re.search(r"\d", read), (cid, read)
        tone = LINE_TONE.get(cid, SECTION_TONE[cid[:4]])
        lines.append({"id": cid, "text": read, "instruct": TONE[lang][tone], "tone": tone,
                      "mode": "zero-shot-instruct" if lang == "zh" else "cross-lingual-instruct", "speed": 1.0})
        captions.append({"id": cid, "section": cid[:4], "text": text, "spoken": read})
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{lang}.json").write_text(json.dumps({"voice": VOICE, "language": lang, "lines": lines}, ensure_ascii=False, indent=1) + "\n")
    (OUT / f"cues.{lang}.json").write_text(json.dumps(captions, ensure_ascii=False, indent=1) + "\n")
    print(f"{lang}: {len(lines)} lines -> {OUT}")
    return list(cues)


if __name__ == "__main__":
    zh, en = build("zh"), build("en")
    assert zh == en, sorted(set(zh) ^ set(en))
