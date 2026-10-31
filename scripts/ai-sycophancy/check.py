"""Whisper check of the film's takes against what each line reads (narrate.py's lines.json).

  ../lucas-academy-media/.conda/bin/python scripts/ai-sycophancy/check.py [--section sc01 | --only id,id] [--take N]
Whisper small first; a line under 0.88 is heard again by medium (small writes traditional characters and drops words
at pauses). A low score is a prompt to listen and read the transcript, not a verdict: read every transcript for
meaning slips too. Results are merged into out/ai-sycophancy/narration/check.json.
"""
import difflib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MEDIA = next(p / "lucas-academy-media" for p in ROOT.parents if (p / "lucas-academy-media").is_dir())
TAKES = MEDIA / "outputs/yancy/zh/ai-sycophancy-v1"
REPORT = ROOT / "out/ai-sycophancy/narration/check.json"
NUM = "零〇一二三四五六七八九十百千万两"


def norm(s: str) -> str:
    s = re.sub(r"</?strong>", "", s).lower()
    return "".join(ch for ch in s if ("一" <= ch <= "鿿" and ch not in NUM) or "a" <= ch <= "z")


def wav_of(line: dict) -> Path:
    return TAKES / f"s{line['speed']:.2f}" / (f"{line['id']}.take{take}.wav" if take else f"{line['id']}.wav")


args = sys.argv[1:]
lines = json.loads((TAKES / "lines.json").read_text())
if "--only" in args:
    ids = set(args[args.index("--only") + 1].split(","))
    lines = [l for l in lines if l["id"] in ids]
if "--section" in args:
    lines = [l for l in lines if l["id"].startswith(args[args.index("--section") + 1])]
take = args[args.index("--take") + 1] if "--take" in args else ""
lines = [l for l in lines if wav_of(l).exists()]

import whisper  # noqa: E402

models = {}


def hear(size, wav):
    models.setdefault(size, whisper.load_model(size))
    r = models[size].transcribe(str(wav), language="zh", condition_on_previous_text=False,
                                initial_prompt="以下是普通话的句子。")
    return r["text"].strip()


results = {}
for l in lines:
    wav = wav_of(l)
    heard = hear("small", wav)
    score = difflib.SequenceMatcher(None, norm(l["spoken"]), norm(heard)).ratio()
    model = "small"
    if score < 0.88:
        heard2 = hear("medium", wav)
        score2 = difflib.SequenceMatcher(None, norm(l["spoken"]), norm(heard2)).ratio()
        if score2 > score:
            heard, score, model = heard2, score2, "medium"
    key = f"{l['id']}.take{take}" if take else l["id"]
    results[key] = {"score": round(score, 3), "model": model, "heard": heard}
    print(f"{key} {score:.2f}{'  <-- check' if score < 0.88 else ''} [{model}] | {heard}", flush=True)

REPORT.parent.mkdir(parents=True, exist_ok=True)
merged = json.loads(REPORT.read_text()) if REPORT.exists() else {}
merged.update(results)
REPORT.write_text(json.dumps(merged, ensure_ascii=False, indent=1))
