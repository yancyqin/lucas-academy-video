"""Whisper check of the film's takes against what each line reads (narrate.py's lines.json), as ai-sycophancy/check.py.

  ../lucas-academy-media/.conda/bin/python scripts/butterfly-challenge/check.py [--voice yancy] [--speed 1.2 --qspeed 1.1]
      [--lang en] [--section sc01 | --only id,id] [--take N]
Whisper small first; a line under 0.88 is heard again by medium. A low score is a prompt to listen and read the
transcript, not a verdict: read every transcript for meaning slips too (蛱 jiá, the measure word 只, 长, 莳萝, the
English model names). Results merge into out/butterfly-challenge/<voice>-<speed>/check.json.
"""
import difflib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import narrate  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
NUM = "零〇一二三四五六七八九十百千万两"


def norm(s: str) -> str:
    s = re.sub(r"</?strong>", "", s).lower()
    if LANG == "en":  # words, numbers spelled out as the voice reads them
        return " ".join(re.findall(r"[a-z]+", s.replace("gpt", "g p t").replace("-", " ")))
    return "".join(ch for ch in s if ("一" <= ch <= "鿿" and ch not in NUM) or "a" <= ch <= "z")


args = sys.argv[1:]
LANG = narrate.opt(args, "--lang", "zh")
voice = narrate.opt(args, "--voice", "yancy")
speed, qspeed = float(narrate.opt(args, "--speed", "1.2")), float(narrate.opt(args, "--qspeed", "1.1"))
take = narrate.opt(args, "--take", "")
lines = narrate.load_en(speed) if LANG == "en" else narrate.load(speed, qspeed)
if "--only" in args:
    ids = set(narrate.opt(args, "--only", "").split(","))
    lines = [l for l in lines if l["id"] in ids]
if "--section" in args:
    lines = [l for l in lines if l["id"].startswith(narrate.opt(args, "--section", ""))]
lines = [l for l in lines if narrate.take_path(l, voice, take, LANG).exists()]
REPORT = ROOT / f"out/butterfly-challenge/{voice}-{speed:.2f}/check.{LANG}.json"

import whisper  # noqa: E402

models = {}


def hear(size, wav):
    models.setdefault(size, whisper.load_model(size))
    r = models[size].transcribe(str(wav), language=LANG, condition_on_previous_text=False,
                                initial_prompt="以下是普通话的句子。" if LANG == "zh" else None)
    return r["text"].strip()


results = {}
for l in lines:
    wav = narrate.take_path(l, voice, take, LANG)
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
