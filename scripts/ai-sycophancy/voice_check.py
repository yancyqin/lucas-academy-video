"""Whisper check of the 试音 takes against what each line should read (voice-test.md 读 lines).

  ../lucas-academy-media/.conda/bin/python scripts/ai-sycophancy/voice_check.py fangfang 1.3 [yancy 1.2 …]
A low score is a prompt to listen and read the transcript, not a verdict.
"""
import difflib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MEDIA = next(p / "lucas-academy-media" for p in ROOT.parents if (p / "lucas-academy-media").is_dir())
NUM = "零〇一二三四五六七八九十百千万两"

spoken = {}
for raw in (ROOT / "docs/ai-sycophancy/voice-test.md").read_text().splitlines():
    if m := re.match(r"^(sc\d\d-\d\d) ｜", raw):
        last = m[1]
    elif m := re.match(r"^\s+读 \| (.+)$", raw):
        spoken[last] = m[1].strip()


def norm(s: str) -> str:
    return "".join(ch for ch in re.sub(r"</?strong>", "", s) if "一" <= ch <= "鿿" and ch not in NUM)


import whisper  # noqa: E402

model = whisper.load_model("small")
args = sys.argv[1:]
for voice, speed in zip(args[::2], args[1::2]):
    takes = MEDIA / f"outputs/{voice}/zh/ai-sycophancy-test/s{float(speed):.2f}"
    for sid, text in spoken.items():
        r = model.transcribe(str(takes / f"{sid}.wav"), language="zh", condition_on_previous_text=False,
                             initial_prompt="以下是普通话的句子。")
        heard = r["text"].strip()
        score = difflib.SequenceMatcher(None, norm(text), norm(heard)).ratio()
        print(f"{voice} {sid} {score:.2f}{'  <-- check' if score < 0.88 else ''} | {heard}", flush=True)
