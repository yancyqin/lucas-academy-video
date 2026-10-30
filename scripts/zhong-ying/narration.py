"""The 中英阅读 films' own narration: every verse re-voiced at speed 1.0 (owner, 2026-10-26: the lesson clips at
0.75 read too slowly, and the delivery could be much better).

    python3 scripts/zhong-ying/narration.py scripts      # write the lucas-narrate scripts (two takes per line)
    python3 scripts/zhong-ying/narration.py choose       # after lucas-narrate + check_narration: pick a take per line
    python3 scripts/zhong-ying/narration.py extras       # the titles and closing lines (three takes each)
    python3 scripts/zhong-ying/narration.py extras subscribe   # one line or one film's only: <lang>-subscribe.json, -check.json
    python3 scripts/zhong-ying/narration.py choose extras
    python3 scripts/zhong-ying/narration.py lesson-extras can-beauty-last   # a lesson_voices film's titles + closing,
                                                       # for lesson_voice.py DATA/narration/lesson-extras <film> <lang> --only …

One reading for the whole series per voice (README "Narration voices": zero-shot-instruct keeps the reference
voice and adds the instruction), so nothing sounds 忽快忽慢. Chinese polyphones the model may misread get CosyVoice3
pinyin tokens in the spoken text only; Whisper checks the plain text (the *-check.json scripts).

Files, all in DATA/narration/verses/:
  zh.json, en.json              lucas-narrate scripts (spoken text, speed, mode, instruction), ids <lesson>-vNN-<take>
  zh-check.json, en-check.json  the same ids with the plain text, for check_narration.py
  zh/, en/                      the takes and Whisper's whisper-check.json
  chosen.json                   the take used for every line, and why
The titles and closing lines (owner, 2026-10-27) are read in the intro's voices, which the owner kept: Fangfang plain
zero-shot, Louise with the intro's instruction. Their files are the same, in DATA/narration/extras/.
"""
from __future__ import annotations

import json
import re
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from films import DATA, FILMS, MEDIA, SUBSCRIBE  # noqa: E402

DIR = DATA / "narration" / "verses"
TAKES = "ab"
STYLE = {
    "zh": {"voice": "fangfang/zh", "mode": "zero-shot-instruct", "speed": 1.0,
           "instruct": "请用亲切、有感情的语气，像给孩子朗读诗歌一样读。"},
    "en": {"voice": "louise/en", "mode": "zero-shot-instruct", "speed": 1.0,
           "instruct": "Please read aloud in a warm, expressive voice, like reading a poem to a child."},
}
XDIR = DATA / "narration" / "extras"
XTAKES = "abc"
XSTYLE = {
    "zh": {"speed": 1.0},
    "en": {"speed": 1.0, "mode": "zero-shot-instruct",
           "instruct": "Please speak in a curious, unhurried voice, like discovering something together with a child."},
}
# Characters with more than one reading, spelled out for the voice (the text on screen keeps the characters).
SPOKEN = {
    "朝辞": "[zh][āo]辞",          # 朝 zhāo, morning (not cháo)
    "一日还": "一日[h][uán]",       # 还 huán, return
    "万重山": "万[ch][óng]山",      # 重 chóng, layer upon layer
    "磨坊": "[m][ò]坊",            # 磨 mò, mill
    "漂": "[p][iāo]",              # 漂 piāo, float (owner, 2026-10-27: 「它们最后会漂到哪里」 was read piǎo / piào)
    "杜甫": "杜[f][ǔ]",            # 甫 fǔ (Fangfang's takes without it: Whisper heard 杜福 / 渡府)
}
# Takes picked by ear or by a measurement Whisper can't make, over choose()'s pick: line → (take, why).
PINNED = {
    "zh/little-boats-v04": ("little-boats-v04-d", "漂 read piāo three times (level pitch; Whisper writes 飄), the pace of "
                                                 "take b, which read the last two 漂 falling"),
    "zh/little-boats-v06": ("little-boats-v06-a", "in the films the owner approved; its clicks lie before the cut, "
                                                 "which choose()'s whole-take stray check can't see"),
    "zh/climb-higher-v07": ("climb-higher-v07-b", "unused (Sunny reads it); kept as it was"),
    "zh/little-boats-closing": ("little-boats-closing-i", "owner, 2026-10-27: take b read 「必，从新得力」; i keeps the comma "
                                                         "after 的 and runs 必 into 从 most smoothly of nine takes (d–f as "
                                                         "written, g–i without the comma)"),
    "zh/chun-ye-xi-yu-title": ("chun-ye-xi-yu-title-e", "the one take Whisper heard as 「春夜喜雨，唐，杜甫」: a–c (甫 as "
                                                     "written) were heard 杜福 / 渡府, d and f (甫 spelled fǔ) 渡府 / 杜腐"),
    "zh/can-beauty-last-closing": ("can-beauty-last-closing-a", "b and c pause between 好 and 雨 (Whisper writes 「好，雨」); "
                                                             "a reads 好雨 as one word, word for word to the medium model"),
    "en/can-beauty-last-closing": ("can-beauty-last-closing-b", "both Whisper models hear \"God set eternity\" (a: one hears "
                                                             "\"said\"; c: both do); one hears \"in a season\", the other \"its\""),
    "en/subscribe": ("subscribe-c", "take b, the nearest pace, reads \"which line you like best\" (two Whisper models "
                                    "agree); c reads it as written, with the pause after \"subscribe\""),
}


def lines(lang: str) -> list[dict]:
    out = []
    for film, spec in FILMS.items():
        if spec.get("lesson_voices"):
            continue
        narrated = json.loads((MEDIA / "data/processed/lucas-lang" / f"{film}-{lang}.json").read_text())["lines"]
        text = {int(l["verseId"].split(".")[-1]): l["text"] for l in narrated if l["unitId"] == "whole"}
        for work in spec["works"]:
            for n in work["units"]:
                out.append({"id": f"{film}-v{n:02d}", "text": text[n]})
    return out


def extra_lines(lang: str) -> list[dict]:
    """Every work's title and author as read aloud (<work id>-title), every film's closing (<film>-closing) and the
    series' last line (subscribe)."""
    out = []
    for film, spec in FILMS.items():
        titles = [{"id": f"{work['id']}-title", "film": film, "text": work["say"][lang]} for work in spec["works"]]
        closing = [{"id": f"{film}-closing", "film": film, "text": spec["closing"][lang]}]
        if spec.get("lesson_voices"):
            ours = spec.get("series_voices", {}).get(lang, ())
            out += (titles if "titles" in ours else []) + (closing if "closing" in ours else [])
            continue
        out += titles + closing
    out.append({"id": "subscribe", "text": SUBSCRIBE[lang]})
    return out


def write_extras(only: str = ""):
    XDIR.mkdir(parents=True, exist_ok=True)
    name = f"-{only}" if only else ""
    for lang, style in XSTYLE.items():
        say, check = [], []
        for line in extra_lines(lang):
            if only and only not in (line["id"], line.get("film")):
                continue
            for take in XTAKES:
                lid = f"{line['id']}-{take}"
                say.append({"id": lid, "text": spoken(line["text"]) if lang == "zh" else line["text"], **style})
                check.append({"id": lid, "text": line["text"]})
        (XDIR / f"{lang}{name}.json").write_text(json.dumps({"lines": say}, ensure_ascii=False, indent=1))
        (XDIR / f"{lang}{name}-check.json").write_text(json.dumps({"lines": check}, ensure_ascii=False, indent=1))
        print(f"{lang}: {len(say)} takes → {XDIR / f'{lang}{name}.json'}")


def write_lesson_extras(film: str):
    """A film whose lesson its readers voiced (lesson_voices: Sunny and Matthew) has its titles and closing read in
    their voices too: lesson_voice.py's script format, in DATA/narration/lesson-extras/."""
    spec, out = FILMS[film], DATA / "narration" / "lesson-extras"
    out.mkdir(parents=True, exist_ok=True)
    for lang in ("zh", "en"):
        ours = spec.get("series_voices", {}).get(lang, ())
        lines = [{"id": f"{w['id']}-title", "verseId": "title", "text": w["say"][lang]} for w in spec["works"]
                 if "titles" not in ours]
        if "closing" not in ours:
            lines.append({"id": f"{film}-closing", "verseId": "closing", "text": spec["closing"][lang]})
        (out / f"{film}-{lang}.json").write_text(json.dumps({"lines": lines}, ensure_ascii=False, indent=1))
    print(f"{out}: {film}-zh.json, {film}-en.json; --only " + ",".join(l["id"] for l in lines))


def spoken(text: str) -> str:
    for plain, voiced in SPOKEN.items():
        text = text.replace(plain, voiced)
    return text


def write_scripts():
    DIR.mkdir(parents=True, exist_ok=True)
    for lang, style in STYLE.items():
        say, check = [], []
        for line in lines(lang):
            for take in TAKES:
                lid = f"{line['id']}-{take}"
                say.append({"id": lid, "text": spoken(line["text"]) if lang == "zh" else line["text"],
                            "speed": style["speed"], "mode": style["mode"], "instruct": style["instruct"]})
                check.append({"id": lid, "text": line["text"]})
        (DIR / f"{lang}.json").write_text(json.dumps({"lines": say}, ensure_ascii=False, indent=1))
        (DIR / f"{lang}-check.json").write_text(json.dumps({"lines": check}, ensure_ascii=False, indent=1))
        print(f"{lang}: {len(say)} takes → {DIR / f'{lang}.json'}")


def syllables(text: str, lang: str) -> int:
    if lang == "zh":
        return len(re.findall(r"[一-鿿]", text))
    return sum(max(1, len(re.findall(r"[aeiouy]+", w.lower()))) for w in re.findall(r"[A-Za-z'-]+", text))


NUMBERS = {"10,000": "ten thousand", "10000": "ten thousand", "1000": "a thousand", "100": "a hundred"}
DIGITS_ZH = "零一二三四五六七八九"


def number_words(n: int, lang: str) -> str:
    """0–999 the way the titles say them ("Psalm 121" → one hundred twenty-one / 一百二十一), so Whisper's digits
    compare with the spoken text by sound."""
    if lang == "zh":
        h, t, o = n // 100, n // 10 % 10, n % 10
        out = (DIGITS_ZH[h] + "百" if h else "") + (DIGITS_ZH[t] + "十" if t else ("零" if h and o else ""))
        out = out[1:] if out.startswith("一十") else out
        return (out + (DIGITS_ZH[o] if o else "")) or "零"
    ones = "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen " \
           "seventeen eighteen nineteen".split()
    tens = "_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()
    h, rest = divmod(n, 100)
    words = [ones[h], "hundred"] if h else []
    if rest or not h:
        words.append(ones[rest] if rest < 20 else tens[rest // 10] + (ones[rest % 10] if rest % 10 else ""))
    return "".join(words)


def heard_right(expected: str, heard: str, lang: str) -> float:
    """How much of the line Whisper heard, by SOUND: Whisper writes classical words as homophones (白地 for 白帝,
    墨方 for 磨坊) and sometimes in traditional characters, so Chinese is compared as toneless pinyin; English as
    letters, so "forever" / "for ever" and "10,000" / "ten thousand" agree."""
    from difflib import SequenceMatcher

    if lang == "zh":
        from pypinyin import lazy_pinyin

        def key(t):
            t = re.sub(r"\d+", lambda m: number_words(int(m.group()), "zh"), t)
            return lazy_pinyin(re.sub(r"[^一-鿿]", "", t))
    else:
        def key(t):
            for digits, words in NUMBERS.items():
                t = t.replace(digits, words)
            t = re.sub(r"\d+", lambda m: number_words(int(m.group()), "en"), t)
            return list(re.sub(r"[^a-z]", "", t.lower().replace(" and ", " ")))
    return SequenceMatcher(None, key(expected), key(heard)).ratio()


def choose(kind: str = "verses"):
    """Per line: the takes Whisper heard right (by sound) with no stray sound at their head or tail
    (build_timeline.strays), then the one whose pace is closest to that voice's median.
    Run with lucas-academy-media's Python (pypinyin, soundfile). kind: verses, or extras (titles and closings)."""
    import numpy as np
    import soundfile as sf

    from build_timeline import load, strays

    folder, each_line = (XDIR, extra_lines) if kind == "extras" else (DIR, lines)
    chosen = {}
    for lang in STYLE:
        report = {}
        for path in sorted((folder / lang).glob("whisper-check*.json")):
            report.update(json.loads(path.read_text()))
        threshold = 0.94 if lang == "zh" else 0.97
        takes = {}
        for line in each_line(lang):
            for path in sorted((folder / lang).glob(f"{line['id']}-?.wav")):
                lid = path.stem
                x, sr = sf.read(path)
                env = np.convolve(np.abs(x), np.ones(sr // 50) / (sr // 50), "same")
                sound = (env > 0.05 * env.max()).sum() / sr          # seconds of voice, pauses left out
                r = report.get(lid, {})
                takes[lid] = {"line": line["id"], "score": round(heard_right(line["text"], r.get("heard", ""), lang), 3),
                              "heard": r.get("heard", ""), "pace": syllables(line["text"], lang) / sound,
                              "problems": r.get("odd", []) + [f"heard more than the line: {w}" for w in r.get("extra", [])]
                                          + [f"stray sound at the {w}" for w in strays(load(path))]}
        median = statistics.median(t["pace"] for t in takes.values())
        for line in each_line(lang):
            mine = {lid: t for lid, t in takes.items() if t["line"] == line["id"]}
            pin = PINNED.get(f"{lang}/{line['id']}")
            if pin and pin[0] in mine:
                chosen[f"{lang}/{line['id']}"] = {"take": pin[0], "score": mine[pin[0]]["score"], "pinned": pin[1]}
                print(f"{lang} {line['id']}: {pin[0]} pinned — {pin[1]}")
                continue
            good = {lid: t for lid, t in mine.items() if t["score"] >= threshold and not t["problems"]} or mine
            best = min(good, key=lambda lid: abs(good[lid]["pace"] / median - 1) - good[lid]["score"])
            t = mine[best]
            chosen[f"{lang}/{line['id']}"] = {"take": best, "score": t["score"], "pace": round(t["pace"] / median, 3),
                                              "clean": best in good and good is not mine}
            flag = "" if chosen[f"{lang}/{line['id']}"]["clean"] else "  !! no take passed Whisper"
            print(f"{lang} {line['id']}: {best} score {t['score']:.3f} pace ×{t['pace'] / median:.2f}{flag}")
            if flag:
                for lid, other in mine.items():
                    print(f"     {lid} {other['score']:.3f} {other['heard']}")
    (folder / "chosen.json").write_text(json.dumps(chosen, ensure_ascii=False, indent=1))


def retake(lang: str, line_id: str, takes: str = "cde"):
    """More takes of one line: <lang>-retake.json for lucas-narrate and <lang>-retake-check.json for Whisper.
    (check_narration.py rewrites whisper-check.json with only what it checked, so keep the earlier one under
    another whisper-check.*.json name first; choose() reads them all.)"""
    style = STYLE[lang]
    text = next(l["text"] for l in lines(lang) if l["id"] == line_id)
    ids = [f"{line_id}-{t}" for t in takes]
    say = [{"id": i, "text": spoken(text) if lang == "zh" else text, "speed": style["speed"], "mode": style["mode"],
            "instruct": style["instruct"]} for i in ids]
    (DIR / f"{lang}-retake.json").write_text(json.dumps({"lines": say}, ensure_ascii=False, indent=1))
    (DIR / f"{lang}-retake-check.json").write_text(json.dumps({"lines": [{"id": i, "text": text} for i in ids]},
                                                              ensure_ascii=False, indent=1))
    print(f"{lang}: {', '.join(ids)}")


if __name__ == "__main__":
    {"scripts": write_scripts, "choose": choose, "retake": retake, "extras": write_extras,
     "lesson-extras": write_lesson_extras}[sys.argv[1]](*sys.argv[2:])
