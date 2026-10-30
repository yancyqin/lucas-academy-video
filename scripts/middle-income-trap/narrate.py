"""Voice 「跨越中等收入陷阱」 in Yancy's voice from docs/middle-income-trap/voice-direction.md, one WAV per line.

Run with lucas-academy-media's Python:
  ../lucas-academy-media/.conda/bin/python scripts/middle-income-trap/narrate.py --speed 1.2 [--question-speed 1.1] [--only id,id | --section sc00] [--take N]
  ../lucas-academy-media/.conda/bin/python scripts/middle-income-trap/narrate.py --check-only
  … narrate.py --speed 1.2 --question-speed 1.1 --reuse <old outputs dir> [--plan]

zh only for now (Yancy, 2026-10-25: 先出中文). zero-shot-instruct with one delivery for the film and a different
one only where the mood changes (SCRIPT-AND-VOICE.md §4–5); no instruction asks for a slow pace. The base speed is
picked by ear from 1.2 / 1.3 / 1.4 on SC00; `慢 0.9` lines play at 0.9x the base. Before voicing, every directed line
is checked against the caption script: same characters once tags and punctuation are gone, unless it has a 读 line.
A line whose caption ends in a question (？ or ？”) is voiced at --question-speed instead (Yancy, 2026-10-25: 问问题的
句子慢一些，1.1 倍；陈述句 1.2); build_timeline.py leaves a pause after it.
Takes go to lucas-academy-media/outputs/yancy/zh/middle-income-trap-v3/s<speed>/ (the speed the line was voiced at);
existing takes are kept. --reuse copies a take from an earlier run (v0.5, 2026-10-26: the v0.4 takes in
middle-income-trap-v1) when the line is read with the same words, tone, slowness and speed, so a renumbered or moved
line keeps the take that is in the film; --plan lists what would be voiced and stops.
"""
import json
import os
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs/middle-income-trap"
for parent in ROOT.parents:
    if (parent / "lucas-academy-media").is_dir():
        MEDIA = parent / "lucas-academy-media"
        break
else:
    raise SystemExit("Cannot find lucas-academy-media")

TONE = {
    "基准": "请用真诚、有热情、有感染力的语气，像跟朋友、跟家长聊天那样说。",
    "凝重": "请用真诚、凝重一点的语气，像在讲一段让人心疼的往事。",
    "希望": "请用温和、真诚、带着希望的语气。",
}
CAPTION = re.compile(r"^- (sc\d\d-\d\d) \| (.+)$")
SECTION = re.compile(r"^## (SC\d\d) · .*｜语气 ([^\s（]+)")
DIRECTED = re.compile(r"^(sc\d\d-\d\d) \| (.+)$")
SPOKEN = re.compile(r"^\s+读 \| (.+)$")
QUESTION = re.compile(r"？”?$")
PUNCT = re.compile(r"[，。、；：？！…“”‘’《》（）—\-·,.;:?!\"'()\s%]")


def bare(s: str) -> str:
    return PUNCT.sub("", re.sub(r"</?strong>", "", s))


def load():
    captions = {}
    for raw in (DOCS / "zh-edit.md").read_text().splitlines():
        m = CAPTION.match(raw)
        if m:
            captions[m[1]] = m[2]
    lines, tone = [], None
    for raw in (DOCS / "voice-direction.md").read_text().splitlines():
        if m := SECTION.match(raw):
            tone = m[2]
        elif m := DIRECTED.match(raw):
            text, *notes = [p.strip() for p in m[2].split("｜")]
            pause = next((float(re.match(r"停顿 ([\d.]+)", n)[1]) for n in notes if n.startswith("停顿")), None)
            slow = next((float(re.search(r"慢 ([\d.]+)", n)[1]) for n in notes if re.search(r"慢 [\d.]", n)), 1.0)
            lines.append({"id": m[1], "direction": text, "spoken": text, "tone": tone, "pause": pause, "slow": slow})
        elif (m := SPOKEN.match(raw)) and lines:
            lines[-1]["spoken"] = m[1].strip()
    problems = [l["id"] for l in lines if l["spoken"] == l["direction"] and bare(l["direction"]) != bare(captions[l["id"]])]
    missing = sorted(set(captions) - {l["id"] for l in lines})
    if problems or missing:
        raise SystemExit(f"direction differs from the captions: {problems}; not directed: {missing}")
    for l in lines:
        l["caption"] = captions[l["id"]]
        if re.search(r"\d", bare(l["spoken"])):
            raise SystemExit(f"{l['id']}: digits left in what the voice reads")
    return lines


args = sys.argv[1:]
lines = load()
if "--check-only" in args:
    print(f"{len(lines)} lines directed, all match the captions")
    raise SystemExit
speed = float(args[args.index("--speed") + 1])
qspeed = float(args[args.index("--question-speed") + 1]) if "--question-speed" in args else speed
only = set(args[args.index("--only") + 1].split(",")) if "--only" in args else None
section = args[args.index("--section") + 1] if "--section" in args else None
take = args[args.index("--take") + 1] if "--take" in args else ""
for l in lines:
    l["speed"] = qspeed if QUESTION.search(l["caption"]) else speed
    l["out"] = MEDIA / f"outputs/yancy/zh/middle-income-trap-v3/s{l['speed']:.2f}"
if "--reuse" in args:
    old_root = Path(args[args.index("--reuse") + 1])
    for l in lines:
        dest = l["out"] / f"{l['id']}.wav"
        src = old_root / f"s{l['speed']:.2f}"
        if dest.exists() or not (src / "lines.json").exists():
            continue
        key = (l["spoken"], l["tone"], l["slow"], l["speed"])
        same = [o["id"] for o in json.loads((src / "lines.json").read_text())
                if (o["spoken"], o["tone"], o["slow"], o["speed"]) == key and (src / f"{o['id']}.wav").exists()]
        if same:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src / f"{same[0]}.wav", dest)
            print(f"reuse {same[0]} -> {l['id']}")
todo = [l for l in lines if (only is None or l["id"] in only) and (section is None or l["id"].startswith(section))]
todo = [l for l in todo if take or not (l["out"] / f"{l['id']}.wav").exists()]
if not todo:
    print("nothing to voice")
    raise SystemExit
if "--plan" in args:
    print(f"{len(todo)} to voice:", " ".join(f"{l['id']}@{l['speed'] * l['slow']:.2f}" for l in todo))
    raise SystemExit

os.chdir(MEDIA)
sys.path.insert(0, str(MEDIA / "src"))
import torch  # noqa: E402

torch.set_num_threads(int(os.environ.get("NARRATE_THREADS", "4")))
torch.set_num_interop_threads(2)
from lucas_media.cosyvoice_engine import CosyVoiceEngine  # noqa: E402
from lucas_media.joke import DEFAULT_PEAK_DBFS, add_peak_headroom, save_wav  # noqa: E402

engine = CosyVoiceEngine(MEDIA / "profiles/yancy/zh/profile.json")
for n, line in enumerate(todo, 1):
    speech, rate, _ = engine.synthesize(line["spoken"], target_language="zh", mode="zero-shot-instruct",
                                        instruction=TONE[line["tone"]], speed=line["speed"] * line["slow"])
    line["out"].mkdir(parents=True, exist_ok=True)
    path = line["out"] / (f"{line['id']}.take{take}.wav" if take else f"{line['id']}.wav")
    save_wav(path, add_peak_headroom(speech, peak_dbfs=DEFAULT_PEAK_DBFS), rate)
    secs = speech.shape[1] / rate
    print(f"[{n}/{len(todo)}] {line['id']} {secs:.2f}s {len(bare(line['spoken'])) / secs:.1f} 字/s -> {path.name}", flush=True)
for out in {l["out"] for l in lines}:
    (out / "lines.json").write_text(json.dumps([{k: v for k, v in l.items() if k != "out"} for l in lines],
                                               ensure_ascii=False, indent=1))
