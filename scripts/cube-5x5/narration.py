"""Narration inputs for 「五阶魔方怎么还原？」 / "How Do You Solve a 5×5 Cube?" (CUBE-5X5.md).

docs/cube-5x5/{en,zh}-edit.md are the source of truth, as the 2×2 film's are: the same cue ids in both, so one
cues.json carries both captions. The 2×2 film's narration.py does the work (its parser, tones, speeds and
notation spelling); this film adds the big cube's notation, where a number in front picks an inner layer (2L is
read "two L" / 「第二层 L」) and M, E and S are the middle layers, and its own line settings.

  python3 scripts/cube-5x5/narration.py
  ../lucas-academy-media/.conda/bin/python scripts/cube-2x2/narrate.py zh cube-5x5
"""
import importlib.util
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("cube2x2_narration", ROOT / "scripts/cube-2x2/narration.py")
c2 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c2)
shared = c2.shared
shared.SECTION = re.compile(r"^## (CF\d\d)\b")
shared.LINE = re.compile(r"^- (cf\d\d-\d\d) \| (.+)$")
SRC = ROOT / "docs/cube-5x5"
OUT = ROOT / "public/cube-5x5/narration"

# One move: an optional inner-layer number in front ("2L"), a face or middle layer, then ′ or 2.
MOVE = r"(?:2(?=[RUFLDB]))?[RUFLDBMES](?:′|2)?"
RUN = re.compile(rf"(?<![A-Za-z0-9]){MOVE}(?:\s+{MOVE})*(?![A-Za-z0-9])")
# "二" next to a letter is heard as "R" (the 2×2 film's v0.1 take), so the layer number is read as a word.
LAYER = {"zh": "第二层", "en": "two "}

HOOK = {"cf00-01", "cf00-02", "cf00-03", "cf00-04"}
# Lines that read a whole algorithm, a little slower so every letter is heard.
ALGORITHM = {cid: 1.05 for cid in ("cf05-02", "cf05-03", "cf06-01", "cf07-01", "cf08-02", "cf09-01", "cf10-04", "cf11-02")}
CLOSE = {"cf12-03": 1.1}
# Per-language exceptions: the eleven-move edge algorithm ran together in Chinese at 1.05× (v0.1).
SLOWER = {"zh": {"cf09-01": 0.95}, "en": {}}

# Line-specific readings, as (caption, spoken) swaps applied before the notation is spelled out.
SPOKEN = {
    "zh": {
        "cf02-01": [("跟个数字 2", "跟个数字二")],
        # "R 前面写个数字二" (v0.1) was heard as "2 前面": R and 二 sound alike, so the voice says it in words; the
        # card on screen at that moment shows 2R.
        "cf02-02": [("2R 是右边数过来第二层", "比如右边数过来的第二层")],
    },
    "en": {
        "cf00-04": [("Part 2", "Part two")],
        "cf02-01": [("and a 2 after it means twice", "and a two after it means twice")],
        # The v0.1 take ran "anywhere: R′" together ("bar prime").
        "cf08-02": [("once, from anywhere:", "once, from anywhere.")],
        # The v0.1 take said "solved: it" as "soft, but".
        "cf09-02": [("The frame is solved: it looks", "The frame is solved. It looks")],
    },
}


def delivery(lang, cid):
    tone = "hook" if cid in HOOK else "close" if cid in CLOSE else "teach"
    settings = shared.line_settings(c2.VOICE[lang], c2.TONE[tone][lang])
    settings["speed"] = SLOWER[lang].get(cid) or ALGORITHM.get(cid) or CLOSE.get(cid) or c2.SPEED
    return settings


def notation(lang, text):
    """Spell out cube notation: U 2L U′ → U，第二层L，U撇 / U, two L, U prime."""
    def one(move):
        layer = LAYER[lang] if move[0] == "2" else ""
        move = move[1:] if layer else move
        return layer + move[0] + "".join(c2.SUFFIX[lang][s] for s in move[1:])

    return RUN.sub(lambda match: c2.JOIN[lang].join(one(m) for m in match.group(0).split()), text)


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
            {"voice": c2.VOICE[lang], "language": lang, "lines": lines}, ensure_ascii=False, indent=2) + "\n")
    cues = [{"id": cid, "section": zh[cid]["section"], "zh": shared.plain(zh[cid]["text"]),
             "en": shared.plain(en[cid]["text"])} for cid in zh]
    (OUT / "cues.json").write_text(json.dumps(cues, ensure_ascii=False, indent=2) + "\n")
    print(f"{len(cues)} cues per language -> {OUT}")


if __name__ == "__main__":
    main()
