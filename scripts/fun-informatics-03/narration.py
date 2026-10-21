"""Narration inputs for 「报数为什么说『幺』？」 / "Why Do Pilots Say 'Bravo'?" (FUN-INFORMATICS-03.md).

docs/fun-informatics-03/{zh,en}-edit.md are the source of truth. The two films use different examples, but
their cue ids line up section by section, so one cues.json carries both captions. This writes
public/fun-informatics-03/narration/{zh,en}.json in lucas-narrate's line format (what the voice READS:
digits spelled out, the 【按实拍改】 / [rewrite after filming] markers dropped) and cues.json (what the
captions SHOW). Each line gets its voice's default delivery from scripts/voice_defaults.py.

  python3 scripts/fun-informatics-03/narration.py
  ../lucas-academy-media/.conda/bin/python scripts/fun-informatics-03/narrate.py zh
"""
import importlib.util
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "docs/fun-informatics-03"
OUT = ROOT / "public/fun-informatics-03/narration"
spec = importlib.util.spec_from_file_location("fi01_narration", ROOT / "scripts/fun-informatics-01/narration.py")
shared = importlib.util.module_from_spec(spec)
spec.loader.exec_module(shared)
shared.SECTION = re.compile(r"^## (NS\d\d)\b")
shared.LINE = re.compile(r"^- (ns\d\d-\d\d) \| (.+)$")
VOICE = {"zh": "louise/zh", "en": "louise/en"}

# Placeholders for lines rewritten once the Pictionary drawings are in. The current wording is voiced
# so the timeline can be built now; those two lines get re-voiced if the real game differs.
MARKER = re.compile(r"^(【按实拍改】|\[rewrite after filming\])\s*")

# What the voice reads where it differs from the caption, as (caption, spoken) swaps: digits spelled out,
# and the spellings of the retakes kept in fun-informatics-03-v1 (retake.py, FUN-INFORMATICS-03.md §5.7).
SPOKEN = {
    "zh": {
        # 腰 reads only yāo; with 幺 the take read the second 幺 like 一 (vowel formants, 2026-10-15).
        "ns00-02": [("念「幺幺零」", "念「腰腰零」"), ("「幺二零」", "「腰二零」")],
        # The first take said 不太好说吧 twice.
        "ns01-03": [("不太好说吧？", "不太好说吧。")],
        "ns01-08": [("7 像根拐杖", "七像根拐杖"), ("0 像个洞", "零像个洞")],
        # Cashew, a friend's corgi, is said like the nut (the children say "Cashew" in IMG_8517). Louise's Chinese
        # voice reads the English spelling as Cashier or Cash, so the voice gets 卡舒 (kǎ shū); captions keep Cashew.
        "ns02-05": [("对，是一只狗，", "对，是一只狗！"), ("朋友家的柯基，Cashew！", "朋友家的柯基：卡舒！")],
        "ns02-07": [("只画 15 秒", "只画十五秒")],
        # Run together, 幺拐 came out as 妖怪; the pause keeps them two words.
        "ns02-10": [("和「幺」「拐」，", "和「腰」，「拐」，")],
    },
    "en": {
        # "bee." came out as "bean"; "B? D?" as "P? D?"; "Listen" was mumbled.
        "ns00-02": [('Not "bee." They say "Bravo." D is "Delta." T is "Tango."',
                     'Not "bee"! They say "Bravo". D is "Delta", T is "Tango".')],
        "ns01-03": [("B? D?", "B?... D?...")],
        # Voiced from "a tiny sound", read as "the tiny sound"; the caption follows the take, which also
        # gives radio test 1 its B, so it stays.
        "ns01-04": [("the tiny sound", "a tiny sound")],
        "ns01-06": [("Listen again.", "Listen again!")],
        # "corgi" came out as "quirky", "drawing" as "drawn", "guessed" as "gassed".
        "ns02-05": [("Yes, a dog: our friend's corgi, Cashew!", "Yes, a dog. Our friend's corgi... Cashew!")],
        "ns02-06": [("look alike, like", "look alike: like"), ("drawing flips", "drawing... flips")],
        "ns02-09": [("guessed at once.", "guessed at once!")],
    },
}


def spoken(lang, cid, text):
    text = MARKER.sub("", text)
    for caption, read in SPOKEN[lang].get(cid, []):
        assert caption in text, (cid, caption)
        text = text.replace(caption, read)
    assert not re.search(r"\d", shared.plain(text)), f"{lang} {cid}: digits need a SPOKEN form: {text}"
    return text


def main():
    zh, zh_tone = shared.parse(SRC / "zh-edit.md")
    en, en_tone = shared.parse(SRC / "en-edit.md")
    assert list(zh) == list(en), "zh and en must have the same cue ids in the same order"
    OUT.mkdir(parents=True, exist_ok=True)
    for lang, cues, tone in (("zh", zh, zh_tone), ("en", en, en_tone)):
        # The edit files' 整体语气 / Overall tone describe the default in words; the instruction itself
        # comes from voice_defaults, so this film reads exactly like episodes 1 and 2.
        lines = [{"id": cid, "text": spoken(lang, cid, cue["text"]), **shared.line_settings(VOICE[lang])}
                 for cid, cue in cues.items()]
        (OUT / f"{lang}.json").write_text(json.dumps(
            {"voice": VOICE[lang], "language": lang, "lines": lines}, ensure_ascii=False, indent=2) + "\n")
    cues = [{"id": cid, "section": zh[cid]["section"],
             "zh": shared.plain(MARKER.sub("", zh[cid]["text"])),
             "en": shared.plain(MARKER.sub("", en[cid]["text"]))} for cid in zh]
    (OUT / "cues.json").write_text(json.dumps(cues, ensure_ascii=False, indent=2) + "\n")
    print(f"{len(cues)} cues per language -> {OUT}")


if __name__ == "__main__":
    main()
