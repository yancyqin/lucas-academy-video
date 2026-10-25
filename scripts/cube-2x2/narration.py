"""Narration inputs for 「二阶魔方怎么还原？」 / "How Do You Solve a 2×2 Cube?" (CUBE-2X2.md).

docs/cube-2x2/{en,zh}-edit.md are the source of truth: the English narration and the Chinese track, the same cue
ids in both, the same footage and the same examples, so one cues.json carries both captions. This writes public/cube-2x2/narration/{zh,en}.json in lucas-narrate's line format (what
the voice READS: cube notation spelled out, R′ as "R 撇" / "R prime", R2 as "R 两下" / "R two", runs of moves
separated so each letter is heard) and how: speed and tone per line, see TONE) and cues.json (what the captions SHOW). Each line gets its voice's default
delivery from scripts/voice_defaults.py.

  python3 scripts/cube-2x2/narration.py
  ../lucas-academy-media/.conda/bin/python scripts/cube-2x2/narrate.py zh
"""
import importlib.util
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "docs/cube-2x2"
OUT = ROOT / "public/cube-2x2/narration"
spec = importlib.util.spec_from_file_location("fi01_narration", ROOT / "scripts/fun-informatics-01/narration.py")
shared = importlib.util.module_from_spec(spec)
spec.loader.exec_module(shared)
shared.SECTION = re.compile(r"^## (CB\d\d)\b")
shared.LINE = re.compile(r"^- (cb\d\d-\d\d) \| (.+)$")
VOICE = {"zh": "louise/zh", "en": "louise/en"}

# One move of cube notation, and a run of them ("R U R′ U′").
MOVE = r"[RUFLDB](?:′|2)?"
RUN = re.compile(rf"(?<![A-Za-z]){MOVE}(?:\s+{MOVE})*(?![A-Za-z0-9])")
# R2 is "R 两下" in Chinese: read "R 二", the 二 sounds like the letter R, so U2 came out as "U, R" (v0.1 take).
SUFFIX = {"zh": {"′": "撇", "2": "两下"}, "en": {"′": " prime", "2": " two"}}
# Delivery (owner, 2026-10-25): the voices' 1.0 has been too slow in every film, so about 1.25×, with the tone
# set by what a line does. The hook dares the viewer; teaching is brisk and clear; a line that reads a whole
# algorithm is a little slower, so every letter is heard; the closing question is warmer and unhurried.
SPEED = 1.25
TONE = {
    "hook": {"en": "Speak with energy and a playful sense of challenge, quick and confident, like daring a child to try something fun.",
             "zh": "请用有活力、带点挑战感的语气，说得轻快、自信，像在邀请孩子接受一个好玩的挑战。"},
    "teach": {"en": "Speak in a clear, friendly, upbeat voice at a brisk pace, like a coach showing a child a neat trick.",
              "zh": "请用清楚、亲切、轻快的语气，节奏利落，像教练在教孩子一个小窍门。"},
    "close": {"en": "Speak warmly and thoughtfully, a little slower, inviting the listener to think.",
              "zh": "请用温暖、若有所思的语气，稍微放慢，邀请听的人一起想一想。"},
}
HOOK = {"cb00-01", "cb00-02", "cb00-03"}
ALGORITHM = {"cb02-05": 1.05, "cb03-02": 1.05, "cb04-03": 1.05}
CLOSE = {"cb06-02": 1.1}


def delivery(lang, cid):
    """lucas-narrate's per-line instruct, mode and speed for one line."""
    tone = "hook" if cid in HOOK else "close" if cid in CLOSE else "teach"
    settings = shared.line_settings(VOICE[lang], TONE[tone][lang])
    settings["speed"] = ALGORITHM.get(cid) or CLOSE.get(cid) or SPEED
    return settings
JOIN = {"zh": "，", "en": ", "}

# Line-specific readings, as (caption, spoken) swaps applied before the notation is spelled out.
SPOKEN = {
    "zh": {
        "cb01-01": [("跟个数字 2", "跟个数字二")],
    },
    "en": {
        "cb01-01": [("and a 2 means twice", "and a two means twice")],
        # The v0.1 take dropped "it" ("to lift out first").
        "cb02-09": [("once to lift it out first", "once, to lift it out first")],
        # The v0.1 take ran "do the algorithm once" together ("duty algorithm wants").
        "cb04-04": [("do the algorithm once from anywhere", "do the algorithm... once, from anywhere")],
    },
}


def notation(lang, text):
    """Spell out cube notation so the voice says every letter: R U R′ U′ → R，U，R撇，U撇 / R, U, R prime, U prime."""
    def say(match):
        moves = match.group(0).split()
        return JOIN[lang].join(m[0] + "".join(SUFFIX[lang][s] for s in m[1:]) for m in moves)
    return RUN.sub(say, text)


def spoken(lang, cid, text):
    for caption, read in SPOKEN[lang].get(cid, []):
        assert caption in text, (cid, caption)
        text = text.replace(caption, read)
    text = notation(lang, text)
    assert not re.search(r"\d|′", shared.plain(text)), f"{lang} {cid}: needs a SPOKEN form: {text}"
    return text


def main():
    zh, _ = shared.parse(SRC / "zh-edit.md")
    en, _ = shared.parse(SRC / "en-edit.md")
    assert list(zh) == list(en), "zh and en must have the same cue ids in the same order"
    OUT.mkdir(parents=True, exist_ok=True)
    for lang, cues in (("zh", zh), ("en", en)):
        lines = [{"id": cid, "text": spoken(lang, cid, cue["text"]), **delivery(lang, cid)} for cid, cue in cues.items()]
        (OUT / f"{lang}.json").write_text(json.dumps(
            {"voice": VOICE[lang], "language": lang, "lines": lines}, ensure_ascii=False, indent=2) + "\n")
    cues = [{"id": cid, "section": zh[cid]["section"], "zh": shared.plain(zh[cid]["text"]),
             "en": shared.plain(en[cid]["text"])} for cid in zh]
    (OUT / "cues.json").write_text(json.dumps(cues, ensure_ascii=False, indent=2) + "\n")
    print(f"{len(cues)} cues per language -> {OUT}")


if __name__ == "__main__":
    main()
