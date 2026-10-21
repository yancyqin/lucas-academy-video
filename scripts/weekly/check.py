"""Listen to every trimmed take with Whisper and flag the ones that do not say what the voice was given.

Run with lucas-academy-media's Python. Chinese is heard with an initial prompt that keeps Whisper in simplified
characters; a line is flagged below 0.94 (Chinese) or 0.90 (English) similarity, the thresholds that caught real
slips in earlier films. Chinese uses the medium model (small answers in traditional characters). Names (Avi, Matthew,
Claude …) and homophones (梵/繁, 蚀/十, 页/夜) are false alarms: read every flagged transcript.

  ../lucas-academy-media/.conda/bin/python scripts/weekly/check.py 001 zh   (and en)
writes out/weekly/<ep>/check.<lang>.json
"""
import difflib
import hashlib
import json
import re
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[2]
SIMILAR = {"zh": 0.94, "en": 0.90}
SAME = str.maketrans({"她": "他", "它": "他", "妳": "你"})  # Whisper cannot hear which 他 it is


DIGITS = "零一二三四五六七八九"


def cn_number(n: int) -> str:
    if n < 10:
        return DIGITS[n]
    if n < 100:
        tens, ones = divmod(n, 10)
        return ("" if tens == 1 else DIGITS[tens]) + "十" + (DIGITS[ones] if ones else "")
    return "".join(DIGITS[int(d)] for d in str(n))  # a year: 1666 is 一六六六


def norm(text: str, lang: str) -> str:
    """What was read and what was heard, compared without punctuation; Chinese numbers in characters (Whisper
    writes 75% and 1666 where the voice read 百分之七十五 and 一六六六)."""
    if lang == "en":
        return re.sub(r"[^a-z]", "", text.lower().replace("-", " "))
    text = re.sub(r"(\d+)%", lambda m: "百分之" + m[1], text)
    text = re.sub(r"\d+", lambda m: cn_number(int(m[0])), text)
    return re.sub(r"[^\w]|_", "", text.translate(SAME)).lower()


def main(ep: str, lang: str) -> None:
    import whisper  # lucas-academy-media's environment

    pub = ROOT / "public/weekly" / ep / "narration"
    lines = json.loads((pub / f"script.{lang}.json").read_text())["lines"]
    out = ROOT / "out/weekly" / ep / f"check.{lang}.json"
    old = json.loads(out.read_text())["lines"] if out.exists() else {}
    model = whisper.load_model("medium" if lang == "zh" else "small")  # small writes Chinese in traditional characters
    report = {}
    for line in lines:
        wav = pub / lang / f"{line['id']}.wav"
        if not wav.is_file():
            continue
        digest = hashlib.sha256(wav.read_bytes()).hexdigest()
        if old.get(line["id"], {}).get("sha256") == digest:
            report[line["id"]] = old[line["id"]]
            continue
        result = model.transcribe(str(wav), language=lang, condition_on_previous_text=False,
                                  initial_prompt="以下是普通话的句子，使用简体中文。" if lang == "zh" else None)
        heard = "".join(s["text"] for s in result["segments"]).strip()
        ratio = difflib.SequenceMatcher(None, norm(line["text"], lang), norm(heard, lang)).ratio()
        flagged = ratio < SIMILAR[lang]
        report[line["id"]] = {"sha256": digest, "text": line["text"], "heard": heard, "ratio": round(ratio, 3), "flagged": flagged}
        print(f"{line['id']} {ratio:.2f} {'FLAG ' if flagged else ''}{heard}", flush=True)
    out.parent.mkdir(parents=True, exist_ok=True)
    flagged = [cid for cid, r in report.items() if r["flagged"]]
    out.write_text(json.dumps({"checked": len(report), "of": len(lines), "flagged": flagged, "lines": report}, ensure_ascii=False, indent=1) + "\n")
    print(f"{lang}: checked {len(report)}/{len(lines)}, flagged {len(flagged)}: {', '.join(flagged)}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
