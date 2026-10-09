"""Incremental Whisper checks with word times and content fingerprints.

Run with lucas-academy-media/.conda/bin/python. --watch checks newly completed
takes as they arrive, preserving earlier results; --model medium rechecks
suspects. --lang selects the film; checks never alter a voice take.
"""
import argparse
import hashlib
import importlib.util
import json
import os
import re
import time
import wave
from pathlib import Path

import numpy as np
import whisper

ROOT = Path(__file__).resolve().parents[2]
MEDIA = Path(os.environ.get("LUCAS_MEDIA", ROOT.parent / "lucas-academy-media"))
if not MEDIA.is_dir() and "LUCAS_MEDIA" not in os.environ:
    MEDIA = ROOT.parents[1] / "lucas-academy-media"  # .worktrees/<checkout>
VOICES = MEDIA / "outputs/louise/zh/fun-informatics-02-v1"
OUT = ROOT / "out/fun-informatics-02/narration-check.json"
LANG = "zh"
ORIGINAL_UNITS = None
spec = importlib.util.spec_from_file_location("shared_voice_check", MEDIA / "scripts/check_narration.py")
shared = importlib.util.module_from_spec(spec)
spec.loader.exec_module(shared)
ORIGINAL_UNITS = shared.units


def units(text, language):
    if language == "en":
        text = text.lower().replace("’", "'")
        for contraction, expanded in {"can't":"can not", "cannot":"can not", "don't":"do not", "doesn't":"does not", "didn't":"did not", "isn't":"is not", "aren't":"are not", "wasn't":"was not", "weren't":"were not", "won't":"will not", "wouldn't":"would not", "couldn't":"could not", "shouldn't":"should not", "it's":"it is", "that's":"that is", "there's":"there is", "he's":"he is", "we're":"we are", "they're":"they are", "you're":"you are", "i'm":"i am", "we've":"we have", "you've":"you have", "i've":"i have", "we'll":"we will", "you'll":"you will"}.items():
            text = re.sub(r"\b" + re.escape(contraction) + r"\b", expanded, text)
        for number, words in {"1840":"eighteen forty", "1872":"eighteen seventy two", "1916":"nineteen sixteen", "1918":"nineteen eighteen", "1948":"nineteen forty eight", "2017":"twenty seventeen", "1862":"eighteen sixty two"}.items():
            text = re.sub(r"\b" + number + r"\b", words, text)
        small = "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen".split()
        tens = "zero ten twenty thirty forty fifty sixty seventy eighty ninety".split()
        def number(match):
            n = int(match[0])
            if n < 20: return small[n]
            if n < 100: return tens[n // 10] + (" " + small[n % 10] if n % 10 else "")
            return match[0]
        text = re.sub(r"\b\d+\b", number, text)
        text = re.sub(r"\bell\b", "l", text)
        text = re.sub(r"\bdee\b", "d", text)
        for original, canonical in (("colour", "color"), ("harbour", "harbor"), ("recognise", "recognize"), ("practised", "practiced"), ("practising", "practicing")):
            text = text.replace(original, canonical)
        return ORIGINAL_UNITS(text, language)
    text = re.sub(r"<[^>]+>", "", text).lower()
    text = text.replace("claude", "克劳德").replace("claud", "克劳德")
    text = text.replace("克勞德", "克劳德").replace("香浓", "香农")
    # These spellings have identical Mandarin sounds, including tone. Do not
    # equate 荣誉/冗余 (different tones) or 身/声 (different nasal endings).
    text = text.translate(str.maketrans({"圆":"原","流":"留","化":"画","话":"画","造":"噪","借":"界","带":"代","是":"世","式":"世","她":"他","它":"他","良":"量","作":"做"}))
    text = text.translate(str.maketrans("〇零一二三四五六七八九梁", "00123456789量"))
    return re.findall(r"[一-鿿0-9a-z]", text)


class JoinedLatinWords:
    """Whisper timestamps C / la / ude separately; normalize the name once."""
    def __init__(self, model):
        self.model = model

    def transcribe(self, *args, **kwargs):
        result = self.model.transcribe(*args, **kwargs)
        for segment in result["segments"]:
            joined = []
            for word in segment.get("words", []):
                latin = bool(re.fullmatch(r"[a-zA-Z ,.!?。？！]+", word["word"]))
                previous_latin = joined and bool(re.fullmatch(r"[a-zA-Z ,.!?。？！]+", joined[-1]["word"]))
                if latin and previous_latin and not re.search(r"[.!?。？！]$", joined[-1]["word"]):
                    joined[-1]["word"] += word["word"]
                    joined[-1]["end"] = word["end"]
                else:
                    joined.append(dict(word))
            segment["words"] = joined
        return result


def trim_unmatched_tail(path, result, output):
    """A decoder can omit babble entirely; remove it only after the last word."""
    words=result["_cut"]["words"]
    if not words or result["score"]<.9 or result["extra"] or not result["odd"]:
        return False
    last=words[-1]["end"]
    if any(t<=last+.5 for t in result["odd"]): return False
    samples,rate=shared.read(path)
    quiet=shared.silence(samples,rate)
    boundary=shared.pause_near(quiet,last-.05,True)
    if boundary is None or boundary<last: return False
    cut=samples[:round(boundary*rate)].astype(np.float64)
    fade=round(.03*rate);cut[-fade:]*=np.linspace(1,0,fade)
    with wave.open(str(output),"wb") as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(rate)
        w.writeframes(cut.astype(np.int16).tobytes())
    return True


def save(report, lines):
    # A medium recheck may run while --watch notices a new small-model take.
    # Preserve analyses of the same file instead of overwriting that recheck.
    if OUT.exists():
        latest = json.loads(OUT.read_text())["cues"]
        for cid, record in latest.items():
            if cid not in report:
                report[cid] = record
            elif record["sha256"] == report[cid]["sha256"] and record.get("spoken") == report[cid].get("spoken"):
                report[cid]["analyses"] = {**record["analyses"], **report[cid]["analyses"]}
    results = [x["analyses"].get("medium", x["analyses"].get("small")) for x in report.values()]
    median = float(np.median([x["pace"] for x in results if x]))
    for record in report.values():
        selected = record["analyses"].get("medium", record["analyses"].get("small"))
        record["flags"] = shared.problems(selected, .9, median)
        if LANG == "en":
            expected = units(record["spoken"], "en")
            heard = units(selected["heard"], "en")
            if expected != heard:
                record["flags"].append("word mismatch needs review")
            if any(expected.count(word) != heard.count(word) for word in ("not", "no", "never")):
                record["flags"].append("possible negation change")
    payload = {"language": LANG, "expected": len(lines), "checked": len(report), "medianPace": median, "flagged": [cid for cid,r in report.items() if r["flags"]], "cues": report}
    temporary = OUT.with_suffix(".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    temporary.replace(OUT)


def main():
    global VOICES, OUT, LANG, ORIGINAL_UNITS
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", choices=("zh", "en"), default="zh")
    ap.add_argument("--watch", action="store_true")
    ap.add_argument("--model", choices=("small", "medium"), default="small")
    ap.add_argument("--only", default="")
    ap.add_argument("--rescore", action="store_true", help="Recompute cached word grouping without new inference")
    args = ap.parse_args()
    LANG = args.lang
    VOICES = MEDIA / f"outputs/louise/{LANG}/fun-informatics-02-v1"
    OUT = ROOT / f"out/fun-informatics-02/narration-check{'.en' if LANG == 'en' else ''}.json"
    ORIGINAL_UNITS = shared.units
    shared.units = units
    lines = json.loads((ROOT / f"public/fun-informatics-02/narration/{LANG}.json").read_text())["lines"]
    wanted = set(args.only.split(",")) - {""}
    report = json.loads(OUT.read_text())["cues"] if OUT.exists() else {}
    import torch
    torch.set_num_threads(2)
    model = whisper.load_model(args.model, device="cpu") if not args.rescore else None
    if model and LANG == "zh": model = JoinedLatinWords(model)
    if args.rescore:
        class CachedWords:
            def __init__(self, words): self.words = words
            def transcribe(self, *args, **kwargs): return {"segments": [{"words": self.words}]}
        by_id = {line["id"]: line for line in lines}
        for cid, record in report.items():
            for name, analysis in list(record["analyses"].items()):
                if "_cut" in analysis:
                    cached = CachedWords(analysis["_cut"]["words"])
                    if LANG == "zh": cached = JoinedLatinWords(cached)
                    record["analyses"][name] = shared.analyse(cached, VOICES / (cid+".wav"), by_id[cid]["text"], LANG, "")
        save(report, lines)
        print(f"Rescored {len(report)} takes", flush=True)
        return
    while True:
        checked = 0
        for line in lines:
            cid = line["id"]
            if wanted and cid not in wanted:
                continue
            path = VOICES / (cid + ".wav")
            if not path.is_file() or time.time() - path.stat().st_mtime < 1:
                continue
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            old = report.get(cid)
            if old and old["sha256"] == digest and old.get("spoken") == line["text"] and args.model in old["analyses"]:
                continue
            if old and (old["sha256"] != digest or old.get("spoken") != line["text"]):
                old = None
            prompt = "以下是普通话科普旁白。术语：Claude、克劳德·莫奈、克劳德·香农、德彪西、冗余、睡莲、池塘、独轮车、抛球杂耍、信息论、噪声、注意力、Lucas Academy。"
            if LANG == "en": prompt = "English educational narration. Claude Monet, Claude Shannon, Claude Debussy, Clair de lune, redundancy, Anthropic, Lucas Academy."
            result = shared.analyse(model, path, line["text"], LANG, prompt)
            analyses = old["analyses"] if old else {}
            analyses[args.model] = result
            report[cid] = {"sha256": digest, "spoken": line["text"], "analyses": analyses}
            save(report, lines)
            print(f"{cid}: {result['score']:.3f} | {result['heard']}", flush=True)
            checked += 1
        if not args.watch or len(report) == len(lines):
            break
        if checked == 0:
            time.sleep(8)
    print(f"Checked {len(report)}/{len(lines)} {LANG} cues; report -> {OUT}", flush=True)


if __name__ == "__main__":
    main()
