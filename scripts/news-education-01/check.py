"""Whisper check of every narration take of 「法国人走上街头，出路在哪里？」: transcript vs. what the voice should read.

Run with lucas-academy-media's Python (Whisper):
  ../lucas-academy-media/.conda/bin/python scripts/news-education-01/check.py zh|en [--model small|medium] [--only id,id]

Writes out/news-education-01/check.<lang>.json and prints the lines below the threshold. A low score is a prompt to
listen and read the transcript, not a verdict (homophones, digits, names).
"""
import difflib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for parent in ROOT.parents:
    if (parent / "lucas-academy-media").is_dir():
        MEDIA = parent / "lucas-academy-media"
        break
lang = sys.argv[1]
args = sys.argv[2:]
model_name = args[args.index("--model") + 1] if "--model" in args else "small"
only = set(args[args.index("--only") + 1].split(",")) if "--only" in args else None
TAKES = MEDIA / f"outputs/yancy/{lang}/news-education-01-v1"
lines = json.loads((ROOT / f"public/news-education-01/narration/{lang}.json").read_text())["lines"]
THRESHOLD = 0.88

import whisper  # noqa: E402

try:
    from opencc import OpenCC  # noqa: E402
    t2s = OpenCC("t2s").convert
except ImportError:
    t2s = lambda s: s  # noqa: E731

NUM = "零〇一二三四五六七八九十百千万两"


def norm(s: str) -> str:
    s = t2s(s).lower()
    if lang == "zh":
        return "".join(ch for ch in s if "一" <= ch <= "鿿" and ch not in NUM)
    s = re.sub(r"[^a-z' ]", " ", s)
    return " ".join(s.split())


model = whisper.load_model(model_name)
out = {}
for line in lines:
    if only and line["id"] not in only:
        continue
    wav = TAKES / f"{line['id']}.wav"
    if not wav.exists():
        continue
    r = model.transcribe(str(wav), language=lang, condition_on_previous_text=False,
                         initial_prompt="以下是普通话的句子。" if lang == "zh" else None)
    heard = r["text"].strip()
    a, b = norm(line["text"]), norm(heard)
    score = difflib.SequenceMatcher(None, a if lang == "zh" else a.split(), b if lang == "zh" else b.split()).ratio()
    out[line["id"]] = {"score": round(score, 3), "heard": heard}
    flag = "  <-- check" if score < THRESHOLD else ""
    print(f"{line['id']} {score:.2f}{flag}", flush=True)
    if flag:
        print(f"    want: {line['text']}\n    heard: {heard}", flush=True)
path = ROOT / f"out/news-education-01/check.{lang}.json"
old = json.loads(path.read_text()) if path.exists() else {}
old.update(out)
path.write_text(json.dumps(old, ensure_ascii=False, indent=1))
