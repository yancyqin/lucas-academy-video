"""Generate the missing Language Bridge narration lines, each checked by Whisper.

For every line of a track whose WAV is missing, synthesize it with the line's
own settings (text, instruct, mode, speed from the media script), transcribe
it, and keep the first take that reads right: a whole-line match (English
>= 0.9, Chinese >= 0.94 with common homophones folded) plus any words a line
must or must not contain. Up to TRIES takes; a line with no good take is
reported and left missing.

Run with the lucas-academy-media environment:
    cd ../lucas-academy-media && PYTHONPATH=src .conda/bin/python ../lucas-academy-video/scripts/reciprocal-doors-retake.py en
"""
from __future__ import annotations

import difflib
import json
import re
import sys
from pathlib import Path

import importlib.util
import tempfile

import soundfile as sf
import whisper
from lucas_media.cosyvoice_engine import CosyVoiceEngine
from lucas_media.joke import add_peak_headroom, save_wav

# Judge each take as the film plays it: after the same tightening (edges and
# long pauses), which can pull a stray end sound up against the last word.
_spec = importlib.util.spec_from_file_location("tighten", Path(__file__).resolve().parent / "reciprocal-doors-tighten.py")
_tighten = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_tighten)

MEDIA = Path(__file__).resolve().parent.parent.parent / "lucas-academy-media"
TRACKS = {
    # track: (voice, [(media script, spoken language)])
    "zh": ("fangfang/zh", [("reciprocal-doors-zh", "zh"), ("reciprocal-doors-zh-demo-en", "en")]),
    "en": ("louise/en", [("reciprocal-doors-en", "en"), ("reciprocal-doors-en-demo-zh", "zh")]),
}
TRIES = 4
# Words that must / must not be heard: every one of these was a real slip once.
RULES = {
    ("en", "rd01-02"): (["can tell"], ["can't", "cannot"]),
    ("en", "rd05-04"): (["now they"], ["you know"]),
    ("en", "rd07-05"): (["understand a story"], []),
    # A line that stops on "we can say," tends to sprout an extra syllable ("dumb", "tat"):
    # these must be heard word for word (EXACT below).
    ("en", "rd06-03-p1"): (["we can say"], ["dumb", "tat", "tch"]),
    ("en", "rd10-01"): (["language bridge"], ["quote"]),
    ("en", "rd08-01"): (["there is"], []),
    ("en", "rd09-03"): (["a parent shares", "the english words"], []),
    ("en", "rd06-05"): (["tries the"], []),
    ("zh", "rd01-02"): (["把故事"], []),
    ("zh", "rd02-03"): (["练认字|練認字"], ["恋人"]),
    ("zh", "rd03-05"): (["难|難"], ["呵呵"]),  # a stretched breath turned into 呵呵
    ("zh", "rd05-04"): (["事"], ["事儿"]),
    ("zh", "rd06-04"): (["交换|交換"], ["的"]),
    ("zh", "rd06-06"): (["听一听|聽一聽"], []),
    ("zh", "rd09-01"): (["这样试|這樣試"], []),
    # One-style re-voicing, 2026-10-01: a dropped word and three tone slips got past 0.85.
    ("zh", "rd01-05"): (["有些孩子"], []),
    ("zh", "rd06-01"): (["倒了"], ["到了"]),
    ("zh", "rd07-05"): (["理解故事时"], ["答"]),
    ("zh", "rd07-06"): (["练认字|練認字"], ["脸认字", "恋爱"]),
    ("zh", "rd07-03"): (["图画|圖畫"], ["读话"]),
    ("zh", "rd09-02"): (["一起讲|一起講"], []),
    ("zh", "rd06-08"): (["确认意思|確認意思"], ["一次"]),
}
EXACT = {("en", "rd06-03-p1"), ("en", "rd10-01")}
HOMOPHONES = str.maketrans({"它": "他", "她": "他", "的": "得", "地": "得", "话": "画", "話": "画"})


def norm(text: str, lang: str) -> str:
    text = re.sub(r"</?strong>", "", text)
    if lang == "zh":
        return re.sub(r"[^一-鿿]", "", text.translate(HOMOPHONES))
    return " ".join(re.sub(r"[^a-z' ]", " ", text.lower().replace("’", "'")).split())


def main() -> None:
    track, wanted = sys.argv[1], set(sys.argv[2:])
    voice, scripts = TRACKS[track]
    out = MEDIA / "outputs" / voice / "reciprocal-doors"
    engine = asr = None
    failed = []
    for name, lang in scripts:
        for line in json.loads((MEDIA / "data/scripts" / f"{name}.json").read_text(encoding="utf-8"))["lines"]:
            target = out / f"{line['id']}.wav"
            if (wanted and line["id"] not in wanted) or (not wanted and target.exists()):
                continue
            if engine is None:
                engine = CosyVoiceEngine(voice)
                asr = whisper.load_model("medium", device="cpu")
            must, must_not = RULES.get((track, line["id"]), ([], []))
            prompt = "以下是普通话的句子，使用简体中文。" if lang == "zh" else None
            for attempt in range(1, TRIES + 1):
                speech, sr, mode = engine.synthesize(
                    line["text"],
                    target_language=lang,
                    mode=(line.get("mode") or "instruct") if line.get("instruct") else "auto",
                    speed=line.get("speed", 0.9),
                    instruction=line.get("instruct", ""),
                )
                trial = out / f"{line['id']}.try{attempt}.wav"
                save_wav(trial, add_peak_headroom(speech, peak_dbfs=-2.0), sr)
                y, sr_read = sf.read(trial, dtype="float32")
                with tempfile.NamedTemporaryFile(suffix=".wav") as played:
                    sf.write(played.name, _tighten.tighten(y, sr_read), sr_read, subtype="PCM_16")
                    heard = asr.transcribe(played.name, language=lang, fp16=False, initial_prompt=prompt)["text"].strip()
                ratio = difflib.SequenceMatcher(None, norm(line.get("check", line["text"]), lang), norm(heard, lang)).ratio()
                flat = heard.lower()
                reads = (
                    (ratio == 1.0 if (track, line["id"]) in EXACT else ratio >= (0.94 if lang == "zh" else 0.9))
                    and all(any(a in flat for a in m.split("|")) for m in must)
                    and not any(n in flat for n in must_not)
                )
                print(f"{line['id']} try {attempt} ({mode}, {speech.shape[1] / sr:.2f}s) ratio {ratio:.2f} {'OK' if reads else 'retry'} | {heard}", flush=True)
                if reads:
                    trial.replace(target)
                    break
            else:
                failed.append(line["id"])
            for leftover in out.glob(f"{line['id']}.try*.wav"):
                leftover.unlink()
    print(f"done; no good take for: {', '.join(failed) or 'none'}")


if __name__ == "__main__":
    main()
