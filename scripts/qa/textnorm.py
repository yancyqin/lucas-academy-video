"""Turn a script line and a Whisper transcript into comparable units.

Chinese is compared character by character; where the characters differ, their toned pinyin (pypinyin, read in the
context of the whole line) decides: Whisper picks characters by context, so a homophone it chooses (近卫 for 进位,
他/她/它, 小 for 晓) is the same sound and passes, while a different syllable or tone (拉 là for 落 luò, 审调 for
省掉) is a real difference. English is compared word by word with contractions
expanded, so "can't" vs a heard "can" leaves a missing "not". Digits are read out (Whisper writes 75% and 1666
where the voice said 百分之七十五 / 一六六六) — never stripped, so a wrong number is caught.
"""
from __future__ import annotations

import re

from pypinyin import Style, lazy_pinyin

ZH_DIGITS = "零一二三四五六七八九"
ZH_NUMERALS = set("零〇一二三四五六七八九十百千万亿两幺")
ZH_NEGATION = set("不没别无未非莫勿")
EN_NEGATION = {"not", "no", "never", "nothing", "nobody", "none", "neither", "nor", "nowhere"}
EN_NUMBERS = set("zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen "
                 "sixteen seventeen eighteen nineteen twenty thirty forty fifty sixty seventy eighty ninety hundred "
                 "thousand million billion first second third half".split())
CJK = re.compile(r"[一-鿿]")
# English words Whisper writes another way although the voice said them right (script word -> what Whisper writes).
EN_WEAK = {"the", "a", "an", "of", "off", "to", "in", "on", "at", "and", "for", "is", "his", "as"}
HEARD_AS = {"psalm": ("sum", "some", "salm"), "psalms": ("sums", "somes"), "verses": ("versus", "vs")}
# Punctuation that marks a place the voice may pause.
PAUSE_MARKS = set("，。！？；：、,.!?;:—…「」『』“”\"()（）《》\n")

CONTRACTIONS = {"can't": "can not", "cannot": "can not", "won't": "will not", "shan't": "shall not",
                "ain't": "is not", "aint": "is not", "it's": "it is", "that's": "that is", "there's": "there is",
                "here's": "here is", "what's": "what is", "he's": "he is", "she's": "she is", "let's": "let us",
                "n't": " not", "'re": " are", "'m": " am", "'ve": " have", "'ll": " will",
                "'d": " would"}
SPELLING = {"colour": "color", "harbour": "harbor", "recognise": "recognize", "practised": "practiced",
            "practising": "practicing", "grey": "gray", "favourite": "favorite", "centre": "center", "okay": "ok"}

_SMALL = ("zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen "
          "seventeen eighteen nineteen").split()
_TENS = "zero ten twenty thirty forty fifty sixty seventy eighty ninety".split()


def en_number(n: int, year: bool = False) -> str:
    if year and 1100 <= n <= 2099 and n % 100 and not 2000 <= n <= 2009:
        return en_number(n // 100) + " " + (("oh " + _SMALL[n % 100]) if n % 100 < 10 else en_number(n % 100))
    if n < 20:
        return _SMALL[n]
    if n < 100:
        return _TENS[n // 10] + (" " + _SMALL[n % 10] if n % 10 else "")
    if n < 1000:
        return _SMALL[n // 100] + " hundred" + (" " + en_number(n % 100) if n % 100 else "")
    if n < 1_000_000:
        return en_number(n // 1000) + " thousand" + (" " + en_number(n % 1000) if n % 1000 else "")
    return " ".join(_SMALL[int(d)] for d in str(n))


def zh_number(n: int) -> str:
    if n < 10:
        return ZH_DIGITS[n]
    if n < 100:
        tens, ones = divmod(n, 10)
        return ("" if tens == 1 else ZH_DIGITS[tens]) + "十" + (ZH_DIGITS[ones] if ones else "")
    if n < 10000:
        out, zero = "", False
        for unit, size in (("千", 1000), ("百", 100), ("十", 10), ("", 1)):
            d, n = divmod(n, size)
            if d:
                out += ("零" if zero and out else "") + ZH_DIGITS[d] + unit
                zero = False
            else:
                zero = True
        return out
    return "".join(ZH_DIGITS[int(d)] for d in str(n))


def _zh_digits(text: str) -> str:
    text = re.sub(r"(\d+(?:\.\d+)?)%", lambda m: "百分之" + m[1], text)
    text = re.sub(r"(\d{4})(?=年)", lambda m: "".join(ZH_DIGITS[int(d)] for d in m[1]), text)   # 2026年 → 二零二六年
    text = re.sub(r"(\d+)\.(\d+)", lambda m: zh_number(int(m[1])) + "点" + "".join(ZH_DIGITS[int(d)] for d in m[2]), text)
    return re.sub(r"\d+", lambda m: zh_number(int(m[0])), text).replace("〇", "零")


def units(text: str, lang: str) -> list[dict]:
    """[{u: comparison key, c: what to show, p: a pause mark follows, num: numeral, neg: negation}]"""
    text = re.sub(r"<[^>]+>", "", text or "")
    if lang == "zh":
        return _zh_units(text)
    return _en_units(text)


def _zh_units(text: str) -> list[dict]:
    text = _zh_digits(text.lower())
    out: list[dict] = []
    run = ""

    def flush_cjk(s: str):
        if not s:
            return
        for ch in s:
            out.append({"u": ch, "c": ch, "p": False, "num": ch in ZH_NUMERALS, "neg": ch in ZH_NEGATION})

    i = 0
    while i < len(text):
        ch = text[i]
        if CJK.match(ch):
            run += ch
            i += 1
            continue
        flush_cjk(run)
        run = ""
        m = re.match(r"[a-z]+", text[i:])
        if m:
            out.append({"u": m[0], "c": m[0], "p": False, "num": False, "neg": False})
            i += len(m[0])
            continue
        if ch in PAUSE_MARKS and out:
            out[-1]["p"] = True
        i += 1
    flush_cjk(run)
    return with_pinyin(out)


def with_pinyin(us: list[dict]) -> list[dict]:
    """Toned pinyin for the Chinese units, read in the context of the whole line (polyphones: 一只 zhī)."""
    cjk = [u for u in us if CJK.match(u["c"])]
    for u, py in zip(cjk, lazy_pinyin("".join(u["c"] for u in cjk), style=Style.TONE3, neutral_tone_with_five=True)):
        u["py"] = py
    for u in us:
        u.setdefault("py", u["u"])
    return us


def same_sound(a: dict, b: dict, lang: str) -> bool:
    """Two different spellings Whisper may choose for one sound: Chinese homophones with the same tone (进位/近卫,
    他/她, 晓/小 — the same toned syllable IS the same sound, numerals included: 十/时), English plural/third-person
    -s (Whisper's grammar, not the voice), and English words that sound alike (quays/keys). The sound-alike rule
    never applies to a number word: "close" there is another number."""
    if lang == "zh":
        return a["py"] == b["py"]
    x, y = a["u"], b["u"]
    if x in EN_WEAK and y in EN_WEAK:          # the/a, of/off, in/on: Whisper's guess on an unstressed word
        return True
    if min(len(x), len(y)) >= 3 and (x == y + "s" or y == x + "s"):
        return True
    if y in HEARD_AS.get(x, ()):
        return True
    if a.get("num") or b.get("num"):           # eight/eighty, sixty/sixth, million/billion: a number is never
        return False                           # "close enough" — a different word there is a different number
    if min(len(x), len(y)) >= 4 and abs(len(x) - len(y)) <= 1:   # quays/keys, christina/cristina, hoeing/howing
        import jellyfish
        mx, my = jellyfish.metaphone(x), jellyfish.metaphone(y)
        return mx == my or (min(len(mx), len(my)) >= 3 and jellyfish.levenshtein_distance(mx, my) <= 1)
    return False


def names_in(text: str) -> set[str]:
    """Capitalised English words that do not start a sentence or a verse line: names (Meng Haoran, Rossetti, Lord)."""
    out = set()
    for m in re.finditer(r"[A-Za-z][A-Za-z'’]*", text):
        before = text[:m.start()].rstrip(" \t\"“‘'(")
        if m[0][0].isupper() and m[0] != "I" and before and before[-1] not in ".!?;:\n":
            out.add(m[0].lower().replace("’", "'").split("'")[0])
    return out


def _en_units(text: str) -> list[dict]:
    caps = names_in(text)
    text = text.lower().replace("’", "'").replace("‘", "'").replace("–", " ").replace("—", " — ")
    for k, v in CONTRACTIONS.items():
        text = re.sub(r"\b" + re.escape(k) + r"\b" if k[0].isalpha() else re.escape(k) + r"\b", v, text)
    text = re.sub(r"(\d+)%", lambda m: m[1] + " percent", text)
    text = re.sub(r"\b(\d{4})\b", lambda m: en_number(int(m[1]), year=True), text)
    text = re.sub(r"\b\d+\b", lambda m: en_number(int(m[0])), text)
    text = text.replace("-", " ")
    out: list[dict] = []
    for m in re.finditer(r"[a-z0-9']+|[^\sa-z0-9']", text):
        tok = m[0]
        if re.fullmatch(r"[a-z0-9']+", tok):
            w = tok.strip("'")
            if not w:
                continue
            w = SPELLING.get(w, w)
            out.append({"u": w, "c": w, "py": w, "p": False, "num": w in EN_NUMBERS, "neg": w in EN_NEGATION,
                        "name": w in caps})
        elif tok in PAUSE_MARKS and out:
            out[-1]["p"] = True
    return [u for k, u in enumerate(out) if k not in number_ands(out)]


def number_ands(us: list[dict]) -> set[int]:
    """The "and" inside a number: "one hundred and thirty-six" and "one hundred thirty-six" both read 136."""
    return {k for k in range(1, len(us) - 1) if us[k]["u"] == "and" and not us[k - 1]["p"]
            and us[k - 1]["u"] in ("hundred", "thousand") and us[k + 1].get("num")}


def joiner(lang: str) -> str:
    return "" if lang == "zh" else " "
