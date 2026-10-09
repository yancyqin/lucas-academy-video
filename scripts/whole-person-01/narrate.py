"""Voice "全人教育的五个理念" — zh (Yancy) and en (Louise), one WAV per script line.

Run from lucas-academy-media with its env (needs the local `zero-shot-instruct`
engine mode):
  .conda/bin/python ../lucas-academy-video/scripts/whole-person-01/narrate.py zh|en

Lines whose text is unchanged since the previous take set (PREVIOUS, with a
texts.json mapping old id -> text) are copied instead of re-synthesized, and an
existing output WAV is never overwritten — delete it to re-voice that line.
Subtitles always use the script text; SPOKEN only changes what the voice reads.
"""
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, "src")
from lucas_media.cosyvoice_engine import CosyVoiceEngine  # noqa: E402
from lucas_media.joke import DEFAULT_PEAK_DBFS, add_peak_headroom, save_wav  # noqa: E402

SCRIPT = "data/scripts/whole-person-five-ideas-{lang}.json"
# zh v10 / en v9 (2026-10-06 re-make, the film opens on 「孩子说“不”，你怎么办？」): four new lines each,
# every unchanged take reused from zh v9 (Yancy; v8 with the off-pitch lines re-voiced by pitch.py)
# and en v8 (Louise).
OUT = {"zh": "outputs/yancy/zh/whole-person-five-ideas-v10", "en": "outputs/louise/en/whole-person-five-ideas-v9"}
PREVIOUS = {"zh": "outputs/yancy/zh/whole-person-five-ideas-v9", "en": "outputs/louise/en/whole-person-five-ideas-v8"}
# 梵高 = fán gāo (Yancy's reading); the zh voice reads 凡高 correctly. The English
# terms in wp01-09 are spoken too (Yancy, 2026-10-04): commas instead of brackets.
ZH_SUBSTITUTIONS = {"梵高": "凡高"}
SPOKEN = {
    "zh": {
        "wp01-09": "这里涉及到两个重要的教育概念：批判性素养，critical literacy，和问题化，problematizing。",
        "wp01-19": "我们相信，在权柄的问题上，教育者应该是 authoritative，有权威又温暖，而不是 authoritarian，专制。",
        "wp04-04": "在圣经诗篇第一百一十九篇里，诗人写下了他被神引导的感受：“你的话是我脚前的灯，是我路上的光。”",
    },
    "en": {"wp00-00": "Your child says no. Hmm... now what?"},
}
# The en opening question is wondered aloud, not snapped: Louise read 「Now what?」 in 2 s and it sounded
# critical (owner, 2026-10-08: 「不是批评，应该是好奇，探索」). The caption and card keep the line as written.
INSTRUCTION = {
    "zh": {},
    "en": {"wp00-00": "Speak with warm, gentle curiosity, like a friend wondering aloud with other parents. "
                      "Soft and open, never scolding or annoyed."},
}


def main(lang: str) -> None:
    script = json.load(open(SCRIPT.format(lang=lang)))
    out = Path(OUT[lang])
    out.mkdir(parents=True, exist_ok=True)
    prev_dir = Path(PREVIOUS[lang])
    previous = json.load(open(prev_dir / "texts.json")) if (prev_dir / "texts.json").is_file() else {}
    by_text = {text: line_id for line_id, text in previous.items()}

    todo = []
    for line in script["lines"]:
        target = out / f"{line['id']}.wav"
        if target.exists():
            continue
        old_id = by_text.get(line["text"])
        if old_id and (prev_dir / f"{old_id}.wav").is_file():
            shutil.copy(prev_dir / f"{old_id}.wav", target)
            print(f"[{lang}] reuse {line['id']} <- {old_id}", flush=True)
        else:
            todo.append(line)

    engine = CosyVoiceEngine(script["voice"])
    for n, line in enumerate(todo, 1):
        text = SPOKEN[lang].get(line["id"], line["text"])
        if lang == "zh":
            for a, b in ZH_SUBSTITUTIONS.items():
                text = text.replace(a, b)
        instruction = INSTRUCTION[lang].get(line["id"])
        if instruction:
            kwargs = {"mode": "zero-shot-instruct", "instruction": instruction}
        else:
            kwargs = {"mode": script["mode"], "instruction": script["instruction"]} if "mode" in script else {}
        speech, rate, _ = engine.synthesize(text, target_language=lang, speed=script.get("speed", 1.0), **kwargs)
        save_wav(out / f"{line['id']}.wav", add_peak_headroom(speech, peak_dbfs=DEFAULT_PEAK_DBFS), rate)
        print(f"[{lang} {n}/{len(todo)}] {line['id']} {speech.shape[1] / rate:.2f}s", flush=True)
    json.dump({l["id"]: l["text"] for l in script["lines"]}, open(out / "texts.json", "w"), ensure_ascii=False, indent=1)
    print(f"[{lang}] voiced", flush=True)


if __name__ == "__main__":
    main(sys.argv[1])
