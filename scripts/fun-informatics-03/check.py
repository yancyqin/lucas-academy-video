"""Whisper check of every Fun Informatics 3 take, with word times kept for cutting the radio test words.

    ../lucas-academy-media/.conda/bin/python scripts/fun-informatics-03/check.py --lang zh [--model medium] [--only ns01-03]

Episode 2's check (scripts/fun-informatics-02/check.py) does the work: its text normalisation, its
Latin-word joining and its report writer. This only points it at episode 3's takes, report and
vocabulary. Checks never alter a take. Report: out/fun-informatics-03/narration-check[.en].json.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("fi02_check", ROOT / "scripts/fun-informatics-02/check.py")
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)

PROMPT = {
    "zh": "以下是普通话科普旁白。词语：幺幺零、幺二零、拐、洞、对讲机、噪声、冗余、你画我猜、双胞胎、克劳德·香农、Lucas Academy。",
    "en": "English educational narration. Bravo, Delta, Tango, niner, walkie-talkie, Pictionary, redundancy, Claude Shannon, Lucas Academy.",
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", choices=("zh", "en"), default="zh")
    ap.add_argument("--model", choices=("small", "medium"), default="small")
    ap.add_argument("--only", default="")
    args = ap.parse_args()
    base.LANG = args.lang
    base.VOICES = base.MEDIA / f"outputs/louise/{args.lang}/fun-informatics-03-v1"
    base.OUT = ROOT / f"out/fun-informatics-03/narration-check{'.en' if args.lang == 'en' else ''}.json"
    base.OUT.parent.mkdir(parents=True, exist_ok=True)
    base.shared.units = base.units
    lines = json.loads((ROOT / f"public/fun-informatics-03/narration/{args.lang}.json").read_text())["lines"]
    wanted = set(args.only.split(",")) - {""}
    report = json.loads(base.OUT.read_text())["cues"] if base.OUT.exists() else {}
    import torch
    import whisper
    torch.set_num_threads(2)
    model = whisper.load_model(args.model, device="cpu")
    if args.lang == "zh":
        model = base.JoinedLatinWords(model)
    for line in lines:
        cid = line["id"]
        path = base.VOICES / f"{cid}.wav"
        if (wanted and cid not in wanted) or not path.is_file():
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        old = report.get(cid)
        if old and old["sha256"] == digest and old.get("spoken") == line["text"] and args.model in old["analyses"]:
            continue
        analyses = old["analyses"] if old and old["sha256"] == digest and old.get("spoken") == line["text"] else {}
        analyses[args.model] = base.shared.analyse(model, path, line["text"], args.lang, PROMPT[args.lang])
        report[cid] = {"sha256": digest, "spoken": line["text"], "analyses": analyses}
        base.save(report, lines)
        r = analyses[args.model]
        print(f"{cid}: {r['score']:.3f} | {r['heard']}", flush=True)
    final = json.loads(base.OUT.read_text())
    print(f"checked {final['checked']}/{final['expected']}; flagged: {final['flagged']}")
    for cid in final["flagged"]:
        print(f"  {cid}: {final['cues'][cid]['flags']}")


if __name__ == "__main__":
    main()
