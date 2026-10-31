"""Whisper check of the English takes against what each line reads (narrate_en.py's lines.json).

  ../lucas-academy-media/.conda/bin/python scripts/ai-sycophancy/check_en.py [--only id,id] [--take N]
Like check.py for the Chinese: Whisper small, then medium for a line under 0.88; the score compares words (lower
case, letters and digits only; numbers are compared as the voice says them). A low score is a prompt to read the
transcript, not a verdict. Results are merged into out/ai-sycophancy/narration/check-en.json.
"""
import difflib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import narrate_en  # noqa: E402

OUT = narrate_en.OUT
REPORT = ROOT / "out/ai-sycophancy/narration/check-en.json"


def norm(s: str) -> list:
    if re.search(r"\d", s):  # Whisper writes digits, sometimes glued to words ("8pm"): say them as the voice does
        s = re.sub(r"(\d)([a-zA-Z])", r"\1 \2", re.sub(r"(?<=\d)\.(?=\d)", " point ", s))
        try:
            s = narrate_en.spoken(s)
        except AssertionError:
            s = re.sub(r"\d", " ", s)
    return re.sub(r"[^a-z0-9 ]", " ", s.lower().replace("’", "'").replace("'", "").replace(".", "")).split()


args = sys.argv[1:]
lines = json.loads((OUT / "lines.json").read_text())
if "--only" in args:
    ids = set(args[args.index("--only") + 1].split(","))
    lines = [l for l in lines if l["id"] in ids]
take = args[args.index("--take") + 1] if "--take" in args else ""
wav_of = lambda l: OUT / (f"{l['id']}.take{take}.wav" if take else f"{l['id']}.wav")  # noqa: E731
lines = [l for l in lines if wav_of(l).exists()]

import whisper  # noqa: E402

models = {}


def hear(size, wav):
    models.setdefault(size, whisper.load_model(size))
    return models[size].transcribe(str(wav), language="en", condition_on_previous_text=False)["text"].strip()


results = {}
for l in lines:
    want = norm(l["spoken"])
    heard = hear("small", wav_of(l))
    score, model = difflib.SequenceMatcher(None, want, norm(heard)).ratio(), "small"
    if score < 0.88:
        heard2 = hear("medium", wav_of(l))
        score2 = difflib.SequenceMatcher(None, want, norm(heard2)).ratio()
        if score2 > score:
            heard, score, model = heard2, score2, "medium"
    key = f"{l['id']}.take{take}" if take else l["id"]
    results[key] = {"score": round(score, 3), "model": model, "heard": heard}
    print(f"{key} {score:.2f}{'  <-- check' if score < 0.88 else ''} [{model}] | {heard}", flush=True)

REPORT.parent.mkdir(parents=True, exist_ok=True)
merged = json.loads(REPORT.read_text()) if REPORT.exists() else {}
merged.update(results)
REPORT.write_text(json.dumps(merged, ensure_ascii=False, indent=1))
