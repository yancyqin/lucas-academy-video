"""Incremental Whisper checks with word times and content fingerprints.

Run with lucas-academy-media/.conda/bin/python. --watch checks newly completed
Chinese takes as they arrive, preserving earlier results; --model medium
rechecks suspects. It never creates English audio or changes any voice take.
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
spec = importlib.util.spec_from_file_location("shared_voice_check", MEDIA / "scripts/check_narration.py")
shared = importlib.util.module_from_spec(spec)
spec.loader.exec_module(shared)


def units(text, language):
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
            elif record["sha256"] == report[cid]["sha256"]:
                report[cid]["analyses"] = {**record["analyses"], **report[cid]["analyses"]}
    results = [x["analyses"].get("medium", x["analyses"].get("small")) for x in report.values()]
    median = float(np.median([x["pace"] for x in results if x]))
    for record in report.values():
        selected = record["analyses"].get("medium", record["analyses"].get("small"))
        record["flags"] = shared.problems(selected, .9, median)
    payload = {"language": "zh", "expected": len(lines), "checked": len(report), "medianPace": median, "flagged": [cid for cid,r in report.items() if r["flags"]], "cues": report}
    temporary = OUT.with_suffix(".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    temporary.replace(OUT)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--watch", action="store_true")
    ap.add_argument("--model", choices=("small", "medium"), default="small")
    ap.add_argument("--only", default="")
    ap.add_argument("--rescore", action="store_true", help="Recompute cached word grouping without new inference")
    args = ap.parse_args()
    shared.units = units
    lines = json.loads((ROOT / "public/fun-informatics-02/narration/zh.json").read_text())["lines"]
    wanted = set(args.only.split(",")) - {""}
    report = json.loads(OUT.read_text())["cues"] if OUT.exists() else {}
    model = JoinedLatinWords(whisper.load_model(args.model, device="cpu")) if not args.rescore else None
    if args.rescore:
        class CachedWords:
            def __init__(self, words): self.words = words
            def transcribe(self, *args, **kwargs): return {"segments": [{"words": self.words}]}
        by_id = {line["id"]: line for line in lines}
        for cid, record in report.items():
            for name, analysis in list(record["analyses"].items()):
                if "_cut" in analysis:
                    cached = JoinedLatinWords(CachedWords(analysis["_cut"]["words"]))
                    record["analyses"][name] = shared.analyse(cached, VOICES / (cid+".wav"), by_id[cid]["text"], "zh", "")
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
            if old and old["sha256"] == digest and args.model in old["analyses"]:
                continue
            if old and old["sha256"] != digest:
                old = None
            prompt = "以下是普通话科普旁白。术语：Claude、克劳德·莫奈、克劳德·香农、德彪西、冗余、睡莲、池塘、独轮车、抛球杂耍、信息论、噪声、注意力、Lucas Academy。"
            result = shared.analyse(model, path, line["text"], "zh", prompt)
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
    print(f"Checked {len(report)}/{len(lines)} Chinese cues; report -> {OUT}", flush=True)


if __name__ == "__main__":
    main()
