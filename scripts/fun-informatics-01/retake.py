"""Re-voice lines until Whisper (medium) hears the words that matter.

  ../lucas-academy-media/.conda/bin/python scripts/fun-informatics-01/retake.py zh it00-02=缩小 it05-04=星系
  ../lucas-academy-media/.conda/bin/python scripts/fun-informatics-01/retake.py en it04-01=01000001 it04-06=rule.*rule

Each ID=REGEX: the line is voiced again (lucas-narrate --only ID --force, same profile and settings) until the
transcript matches REGEX, up to TRIES times. Chinese and English number words are turned into digits before
matching, so 01000001 matches "零一零零零零零一" or "zero one zero zero zero zero zero one" read correctly.
"""
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import whisper

ROOT = Path(__file__).resolve().parents[2]
MEDIA = Path("/Users/yqin/repo/playground/lucas-academy-media")
TRIES = 4
EN_DIGITS = {"zero": "0", "oh": "0", "one": "1", "two": "2", "three": "3", "four": "4", "five": "5",
             "six": "6", "seven": "7", "eight": "8", "nine": "9"}


def digits(lang: str, text: str) -> str:
    if lang == "zh":
        return text.translate(str.maketrans("零一二三四五六七八九", "0123456789"))
    return re.sub(r"\b(zero|oh|one|two|three|four|five|six|seven|eight|nine)\b", lambda m: EN_DIGITS[m.group(1)], text.lower())


def variants(text: str):
    """The same words with different punctuation: the speech model gives the same take for the same text,
    so a retry needs a slightly different text to get a different reading."""
    yield text
    yield text.replace("：", "，").replace(": ", ", ")
    yield text.replace("、", "，").replace("; ", ", ")
    yield re.sub(r"[：、]", "，", text).replace("。", "，", 1).replace(": ", ", ").replace(". ", ", ", 1)


def squash(text: str) -> str:
    return re.sub(r"[\s,，。、：:;；!！?？\-—\"“”'’.]", "", text.lower())


def main() -> None:
    lang, wanted = sys.argv[1], dict(a.split("=", 1) for a in sys.argv[2:])
    script = ROOT / f"public/fun-informatics-01/narration/{lang}.json"
    out = MEDIA / f"outputs/louise/{lang}/fun-informatics-01-v2"
    model = whisper.load_model("medium", device="cpu")
    prompt = "以下是普通话的句子，使用简体中文。" if lang == "zh" else None
    data = json.loads(script.read_text())
    for line_id, pattern in wanted.items():
        best = None
        line = next(l for l in data["lines"] if l["id"] == line_id)
        for attempt, text in enumerate(variants(line["text"]), 1):
            with tempfile.TemporaryDirectory() as tmp:
                one = Path(tmp) / f"{lang}.json"
                one.write_text(json.dumps({**data, "lines": [{**line, "text": text}]}, ensure_ascii=False))
                subprocess.run([str(MEDIA / ".conda/bin/lucas-narrate"), str(one), "--profile", f"louise/{lang}", "--language", lang,
                                "--speed", "1.0", "--output-dir", str(out), "--only", line_id, "--force"],
                               cwd=MEDIA, check=True, capture_output=True)
            heard = model.transcribe(str(out / f"{line_id}.wav"), language=lang, initial_prompt=prompt, fp16=False)["text"]
            ok = re.search(pattern, squash(digits(lang, heard))) is not None
            print(f"[{lang}] {line_id} try {attempt}: {'OK ' if ok else 'BAD'} {heard.strip()}", flush=True)
            if ok:
                best = None
                break
            keep = out / f"{line_id}.try{attempt}.wav"
            shutil.copy(out / f"{line_id}.wav", keep)
            best = best or keep
        if best:
            print(f"[{lang}] {line_id}: no take matched /{pattern}/ in {TRIES} tries; the last take stays, listen to it", flush=True)


if __name__ == "__main__":
    main()
