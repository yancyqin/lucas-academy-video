"""Whisper (medium) every take in takes/<lang>/ and compare with the script; flag differences and extra tail words."""
import difflib
import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
import whisper

HERE = Path(__file__).resolve().parents[2] / "out/leaf-truck"   # takes and checks (git-ignored)
langs = sys.argv[1:] or ["zh", "en"]
model = whisper.load_model("medium")
report = json.loads((HERE / "checks/takes.json").read_text()) if (HERE / "checks/takes.json").exists() else {}


def norm(s, lang):
    s = s.lower().replace("’", "'")
    if lang == "zh":
        s = re.sub(r"[^\w]", "", s)
        for a, b in (("11", "十一"), ("14", "十四"), ("47", "四十七"), ("他", "它")):
            s = s.replace(a, b)
        return s
    s = re.sub(r"\b11\b", "eleven", s)
    s = re.sub(r"\b14\b", "fourteen", s)
    s = re.sub(r"\b47\b", "forty seven", s).replace("cm", "centimeters").replace("-", " ")
    return " ".join(re.sub(r"[^a-z0-9' ]", " ", s).split())


for lang in langs:
    rows = json.loads((HERE / f"takes/{lang}.json").read_text())
    for r in rows:
        key = f"{lang}/{r['id']}"
        wav = HERE / f"takes/{lang}/{r['id']}.wav"
        if not wav.exists():
            continue
        if key in report and report[key].get("mtime") == wav.stat().st_mtime:
            continue
        pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", str(wav), "-ar", "16000", "-ac", "1", "-f", "f32le", "-"],
                             capture_output=True, check=True).stdout
        heard = model.transcribe(np.frombuffer(pcm, np.float32), language=lang, fp16=False,
                                 initial_prompt="以下是普通话的句子。" if lang == "zh" else None)["text"].strip()
        a, b = norm(r["text"], lang), norm(heard, lang)
        ratio = difflib.SequenceMatcher(None, a, b).ratio()
        report[key] = {"text": r["text"], "heard": heard, "ratio": round(ratio, 3), "same": a == b,
                       "longer": len(b) > len(a) + (2 if lang == "zh" else 6), "mtime": wav.stat().st_mtime}
        flag = "OK  " if a == b else ("DIFF" if ratio < .97 else "near")
        print(flag, key, f"{ratio:.3f}", "|", heard, flush=True)
(HERE / "checks/takes.json").write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n")
