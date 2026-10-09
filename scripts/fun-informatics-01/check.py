"""Whisper every narration line of one film and list the ones that may be misread.

  ../lucas-academy-media/.conda/bin/python scripts/fun-informatics-01/check.py zh|en

The transcript is compared with both what the voice reads (number words) and the caption (digits), after
turning number words into digits, so "零一零零零零零一" read right is not flagged for being heard as 01000001.
Lines below 0.86 with the small model are heard again with medium; only those still below are listed.
"""
import difflib
import json
import re
import sys
from pathlib import Path

import whisper

sys.path.insert(0, str(Path(__file__).parent))
from retake import digits  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
MEDIA = Path("/Users/yqin/repo/playground/lucas-academy-media")
lang = sys.argv[1]
spoken = {l["id"]: re.sub(r"</?strong>", "", l["text"]) for l in json.loads((ROOT / f"public/fun-informatics-01/narration/{lang}.json").read_text())["lines"]}
caption = {c["id"]: c[lang] for c in json.loads((ROOT / "public/fun-informatics-01/narration/cues.json").read_text())}
wavs = MEDIA / f"outputs/louise/{lang}/" / {"zh": "fun-informatics-01-v3", "en": "fun-informatics-01-v4"}[lang]  # build_timeline.TAKES
prompt = "以下是普通话的句子，使用简体中文。" if lang == "zh" else None


def norm(text: str) -> list:
    text = digits(lang, text.replace("+", " plus " if lang == "en" else "加"))
    if lang == "zh":
        return list(re.sub(r"[^0-9一-鿿A-Za-z]", "", text))
    return re.sub(r"[^a-z0-9 ]", " ", text.lower().replace("’", "").replace("'", "")).split()


def score(heard: str, i: str) -> float:
    return max(difflib.SequenceMatcher(None, norm(ref), norm(heard)).ratio() for ref in (spoken[i], caption[i]))


only = set(sys.argv[2:])  # optional: check just these ids (and only lines that exist yet)
small = whisper.load_model("small", device="cpu")
suspects = []
for i in spoken:
    if (only and i not in only) or not (wavs / f"{i}.wav").is_file():
        continue
    heard = small.transcribe(str(wavs / f"{i}.wav"), language=lang, initial_prompt=prompt, fp16=False)["text"]
    if score(heard, i) < 0.86:
        suspects.append(i)
print(f"[{lang}] small model: {len(suspects)} of {len(spoken)} lines below 0.86", flush=True)
medium = whisper.load_model("medium", device="cpu")
for i in suspects:
    heard = medium.transcribe(str(wavs / f"{i}.wav"), language=lang, initial_prompt=prompt, fp16=False)["text"]
    s = score(heard, i)
    if s < 0.86:
        print(f"{s:.2f} {i}\n   reads  {spoken[i]}\n   heard  {heard.strip()}", flush=True)
print(f"[{lang}] checked {len(spoken)}", flush=True)
