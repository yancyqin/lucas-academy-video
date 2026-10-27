"""Whisper check of the 「跨越中等收入陷阱」 takes: transcript vs. what the voice should read.

Run with lucas-academy-media's Python (Whisper):
  ../lucas-academy-media/.conda/bin/python scripts/middle-income-trap/check.py --speed 1.3 [--model small|medium] [--only id,id]

Reads the takes and lines.json that narrate.py wrote under outputs/yancy/zh/middle-income-trap-v3/s<speed>/ and
writes check.json next to them. A low score is a prompt to listen and read the transcript, not a verdict
(homophones, names, classical Chinese). Run it again on the audio that actually plays if the film is stretched.
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
args = sys.argv[1:]
speed = float(args[args.index("--speed") + 1])
model_name = args[args.index("--model") + 1] if "--model" in args else "small"
only = set(args[args.index("--only") + 1].split(",")) if "--only" in args else None
TAKES = MEDIA / f"outputs/yancy/zh/middle-income-trap-v3/s{speed:.2f}"
lines = json.loads((TAKES / "lines.json").read_text())
THRESHOLD = 0.88
NUM = "零〇一二三四五六七八九十百千万两"

import whisper  # noqa: E402


def norm(s: str) -> str:
    s = re.sub(r"</?strong>", "", s)
    return "".join(ch for ch in s if "一" <= ch <= "鿿" and ch not in NUM)


model = whisper.load_model(model_name)
out = {}
for line in lines:
    wav = TAKES / f"{line['id']}.wav"
    if (only and line["id"] not in only) or not wav.exists():
        continue
    r = model.transcribe(str(wav), language="zh", condition_on_previous_text=False,
                         initial_prompt="以下是普通话的句子。")
    heard = r["text"].strip()
    score = difflib.SequenceMatcher(None, norm(line["spoken"]), norm(heard)).ratio()
    out[line["id"]] = {"score": round(score, 3), "heard": heard}
    flag = "  <-- check" if score < THRESHOLD else ""
    print(f"{line['id']} {score:.2f}{flag}", flush=True)
    if flag:
        print(f"    want: {norm(line['spoken'])}\n    heard: {heard}", flush=True)
path = TAKES / "check.json"
old = json.loads(path.read_text()) if path.exists() else {}
old.update(out)
path.write_text(json.dumps(old, ensure_ascii=False, indent=1))
