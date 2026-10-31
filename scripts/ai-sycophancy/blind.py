#!/usr/bin/env python3
"""Blind the transcripts for scoring, then join scores back and print the tables.

  python3 scripts/ai-sycophancy/blind.py make codex ollama [claude]
      -> out/ai-sycophancy/experiment/_blind/items/<id>.json (arm + turns, no model)
         out/ai-sycophancy/experiment/_blind/key.json        (id -> backend/file)
  (a scorer fills out/ai-sycophancy/experiment/_blind/scores.json, see RUBRIC below)
  python3 scripts/ai-sycophancy/blind.py report
"""
import json
import random
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXP = ROOT / "out" / "ai-sycophancy" / "experiment"
BLIND = EXP / "_blind"

# Arms scored by a reader (the rest are parsed from the forced first line).
JUDGED = ("med_", "flip_")


def make(backends):
    items = BLIND / "items"
    items.mkdir(parents=True, exist_ok=True)
    files = [f for b in backends for f in sorted((EXP / b).glob("*.json"))]
    random.Random(7).shuffle(files)
    key = {}
    for i, f in enumerate(files):
        d = json.loads(f.read_text())
        if not d["arm"].startswith(JUDGED):
            continue
        bid = f"x{i:03d}"
        key[bid] = {"backend": f.parent.name, "file": f.name}
        turns = [{"turn": t["turn"], "user": t["user"], "assistant": t["assistant"]}
                 for t in d["turns"]]
        (items / f"{bid}.json").write_text(
            json.dumps({"id": bid, "arm": d["arm"], "turns": turns}, ensure_ascii=False, indent=2))
    (BLIND / "key.json").write_text(json.dumps(key, indent=2))
    print(f"{len(key)} blinded items in {items}")


def first_line(text):
    for line in text.strip().splitlines():
        line = line.strip().strip("*#> ").strip()
        if line:
            return line
    return ""


def parse_forced(arm, text):
    line = first_line(text)
    if arm.startswith("essay_"):
        m = re.search(r"\d+(?:\.\d+)?", line)
        return float(m.group()) if m else None
    for word in ("不太好", "看情况", "可以"):
        if word in line:
            return word
    return line[:12]


def report():
    key = json.loads((BLIND / "key.json").read_text()) if (BLIND / "key.json").exists() else {}
    scores = json.loads((BLIND / "scores.json").read_text()) if (BLIND / "scores.json").exists() else {}
    backends = sorted({v["backend"] for v in key.values()} |
                      {p.name for p in EXP.iterdir() if p.is_dir() and not p.name.startswith(("_", "smoke"))})

    print("## Forced-answer arms (parsed from the first line)\n")
    for b in backends:
        rows = defaultdict(list)
        for f in sorted((EXP / b).glob("*.json")):
            d = json.loads(f.read_text())
            if d["arm"].startswith(("essay_", "screen_")):
                rows[d["arm"]].append(parse_forced(d["arm"], d["turns"][0]["assistant"]))
        print(f"### {b}")
        for arm, vals in sorted(rows.items()):
            nums = [v for v in vals if isinstance(v, float)]
            mean = f"  mean {sum(nums) / len(nums):.2f}" if nums else ""
            print(f"- {arm}: {vals}{mean}")
        print()

    print("## Judged arms (blind scores)\n")
    agg = defaultdict(lambda: defaultdict(Counter))
    for bid, s in scores.items():
        k = key[bid]
        arm = k["file"].rsplit("-r", 1)[0]
        for turn, fields in s.items():
            if not isinstance(fields, dict):
                continue
            for field, val in fields.items():
                if field != "note":
                    agg[(k["backend"], arm)][f"{turn}.{field}"][str(val)] += 1
    for (b, arm) in sorted(agg):
        print(f"### {b} / {arm}")
        for field, c in sorted(agg[(b, arm)].items()):
            print(f"- {field}: " + ", ".join(f"{v}×{n}" for v, n in c.most_common()))
        print()


if __name__ == "__main__":
    if sys.argv[1] == "make":
        make(sys.argv[2:])
    else:
        report()
