"""Whisper check of every take of 「二阶魔方怎么还原？」 (CUBE-2X2.md).

    ../lucas-academy-media/.conda/bin/python scripts/cube-2x2/check.py --lang zh [--model medium] [--only cb02-05]

Episode 2's check (scripts/fun-informatics-02/check.py) does the work: its text normalisation, its
Latin-word joining and its report writer. This only points it at this film's takes, report and
vocabulary. Checks never alter a take. Report: out/cube-2x2/narration-check[.en].json.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
# Episode 2's check finds lucas-academy-media beside the checkout; from a worktree it is further up.
for parent in ROOT.parents:
    if (parent / "lucas-academy-media").is_dir():
        os.environ.setdefault("LUCAS_MEDIA", str(parent / "lucas-academy-media"))
        break
spec = importlib.util.spec_from_file_location("fi02_check", ROOT / "scripts/fun-informatics-02/check.py")
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)

PROMPT = {
    "zh": "以下是普通话魔方教学旁白。词语：二阶魔方、角块、中心块、顺时针、R撇、U撇、小鱼公式、车头灯、顶层、Lucas Academy。",
    "en": "English cube-solving narration. Two-by-two cube, corners, clockwise, R prime, U prime, Sune, algorithm, headlights, Lucas Academy.",
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", choices=("zh", "en"), default="zh")
    ap.add_argument("--model", choices=("small", "medium"), default="small")
    ap.add_argument("--only", default="")
    args = ap.parse_args()
    base.LANG = args.lang
    base.VOICES = base.MEDIA / f"outputs/louise/{args.lang}/cube-2x2-v3"
    base.OUT = ROOT / f"out/cube-2x2/narration-check{'.en' if args.lang == 'en' else ''}.json"
    base.OUT.parent.mkdir(parents=True, exist_ok=True)
    base.shared.units = base.units
    lines = json.loads((ROOT / f"public/cube-2x2/narration/{args.lang}.json").read_text())["lines"]
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
