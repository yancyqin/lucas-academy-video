"""Whisper every narration line and flag ones that drift from the script.

Run with the lucas-academy-media env (it has whisper):
  ../lucas-academy-media/.conda/bin/python scripts/whole-person-01/check_lines.py SCRIPT.json WAV_DIR zh|en

Prints lines whose transcript matches the script below 0.9. Chinese flags are
often homophones (权柄→全柄); listen before re-voicing.
"""
import json
import re
import sys
import difflib
import whisper

script, wav_dir, lang = sys.argv[1], sys.argv[2], sys.argv[3]
model = whisper.load_model("small", device="cpu")
lines = {l["id"]: re.sub(r"</?strong>", "", l["text"]) for l in json.load(open(script))["lines"]}
if lang == "zh":
    norm = lambda s: list(re.sub(r"[^一-鿿A-Za-z]", "", s))
    prompt = "以下是普通话的句子，使用简体中文。"
else:
    norm = lambda s: re.sub(r"[^a-z ]", "", s.lower().replace("'", "").replace("’", "")).split()
    prompt = None
for i, text in lines.items():
    heard = model.transcribe(f"{wav_dir}/{i}.wav", language=lang, initial_prompt=prompt, fp16=False)["text"]
    ratio = difflib.SequenceMatcher(None, norm(text), norm(heard)).ratio()
    if ratio < 0.9:
        print(f"{ratio:.2f} {i}\n   script {text}\n   heard  {heard}", flush=True)
print("checked", len(lines), flush=True)
