"""Remove only independently verified extras outside the approved sentence.

Uses a cached small-model boundary, then verifies the candidate with medium.
Original WAVs are preserved; the script never repairs missing/internal words.
"""
import argparse
import hashlib
import importlib.util
import json
import shutil
from pathlib import Path

import whisper

spec = importlib.util.spec_from_file_location("fi02_check", Path(__file__).with_name("check.py"))
check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", required=True)
    args = ap.parse_args()
    model = check.JoinedLatinWords(whisper.load_model("medium", device="cpu"))
    check.shared.units = check.units
    lines = json.loads((check.ROOT / "public/fun-informatics-02/narration/zh.json").read_text())["lines"]
    report = json.loads(check.OUT.read_text())["cues"]
    backup = check.ROOT / "out/fun-informatics-02/retakes"
    backup.mkdir(parents=True, exist_ok=True)
    for cid in args.only.split(","):
        record = report[cid]
        path = check.VOICES / (cid + ".wav")
        if hashlib.sha256(path.read_bytes()).hexdigest() != record["sha256"]:
            raise SystemExit(f"{cid}: source changed; recheck before cutting")
        candidate = backup / (cid + ".candidate.wav")
        cached = record["analyses"].get("small", record["analyses"].get("medium"))
        if not check.shared.cut_edges(path, cached, candidate):
            print(f"{cid}: no removable edge", flush=True)
            continue
        verified = check.shared.analyse(model, candidate, record["spoken"], "zh", "以下是普通话科普旁白，使用简体中文。")
        if verified["score"] < .95 or verified["extra"] or verified["odd"]:
            print(f"{cid}: candidate retained for inspection, not installed: {verified['heard']}", flush=True)
            continue
        original = backup / (cid + ".original-" + record["sha256"][:8] + ".wav")
        shutil.copy2(path, original)
        shutil.copy2(candidate, path)
        report[cid] = {"sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "spoken": record["spoken"], "analyses": {"medium": verified}, "repair": {"operation": "cut extra speech outside script at a silence boundary", "original": str(original.relative_to(check.ROOT)), "originalSha256": record["sha256"]}}
        check.save(report, lines)
        print(f"{cid}: installed verified cut, {verified['score']:.3f}: {verified['heard']}", flush=True)


if __name__ == "__main__":
    main()
