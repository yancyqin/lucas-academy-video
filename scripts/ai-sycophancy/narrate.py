"""Voice 「你爱听 AI 说「是的」吗？」 in Yancy's voice from docs/ai-sycophancy/voice-direction.md, one WAV per line.

Run with lucas-academy-media's Python, at most two processes at once (memory budget):
  ../lucas-academy-media/.conda/bin/python scripts/ai-sycophancy/narrate.py [--only id,id | --section sc01] [--part 1/2] [--take N] [--plan]
  ../lucas-academy-media/.conda/bin/python scripts/ai-sycophancy/narrate.py --check-only

yancy/zh, zero-shot-instruct, set up like 「跨越中等收入陷阱」 (Yancy 2026-10-30: 还是用我的声音配吧，就按第二期的配置来):
statements at SPEED, a line whose caption ends in a question at QSPEED, `慢 0.9` lines at 0.9x their speed.
A section's `｜语气 X` sets its tone; a line's own `｜语气 X` overrides it for that line. Before voicing, every directed
line is checked against the caption script (zh-draft.md): same characters once tags, punctuation and 【notes】 are
gone, unless it has a 读 line; what the voice reads must have no digits and no 〇.
Takes go to lucas-academy-media/outputs/yancy/zh/ai-sycophancy-v1/s<speed>/ (the speed the line was voiced at), with
every line's settings in ai-sycophancy-v1/lines.json; existing takes are kept.
--part k/n voices every n-th line of what is left, so two processes can split the film.
"""
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs/ai-sycophancy"
MEDIA = next(p / "lucas-academy-media" for p in ROOT.parents if (p / "lucas-academy-media").is_dir())
VOICE, SPEED, QSPEED = "yancy", 1.2, 1.1
TAKES = MEDIA / f"outputs/{VOICE}/zh/ai-sycophancy-v1"

TONE = {
    "基准": "请用真诚、温暖、有感情的语气，像跟朋友、跟家长聊天那样说。",
    "凝重": "请用真诚、凝重一点的语气，像在讲一段让人心疼的往事。",
    "温和": "请用温和、真诚、带着希望的语气。",
}
CAPTION = re.compile(r"^- (sc\d\d-\d\d) \| (.+)$")
SECTION = re.compile(r"^## (SC\d\d) · .*｜语气 ([^\s（]+)")
DIRECTED = re.compile(r"^(sc\d\d-\d\d) \| (.+)$")
SPOKEN = re.compile(r"^\s+读 \| (.+)$")
QUESTION = re.compile(r"？[」”]?$")
PUNCT = re.compile(r"[，。、；：？！…“”‘’「」『』《》（）—\-·+,.;:?!\"'()\s%]")


def bare(s: str) -> str:
    return PUNCT.sub("", re.sub(r"</?strong>|【[^】]*】", "", s))


def take_path(line: dict, take: str = "") -> Path:
    return TAKES / f"s{line['speed']:.2f}" / (f"{line['id']}.take{take}.wav" if take else f"{line['id']}.wav")


def load():
    captions = {}
    for raw in (DOCS / "zh-draft.md").read_text().splitlines():
        if m := CAPTION.match(raw):
            captions[m[1]] = m[2]
    lines, tone = [], None
    for raw in (DOCS / "voice-direction.md").read_text().splitlines():
        if m := SECTION.match(raw):
            tone = m[2]
        elif m := DIRECTED.match(raw):
            text, *notes = [p.strip() for p in m[2].split("｜")]
            own = next((n.split()[1] for n in notes if n.startswith("语气 ")), tone)
            pause = next((float(re.match(r"停顿 ([\d.]+)", n)[1]) for n in notes if n.startswith("停顿")), None)
            slow = next((float(re.search(r"慢 ([\d.]+)", n)[1]) for n in notes if re.search(r"慢 [\d.]", n)), 1.0)
            lines.append({"id": m[1], "direction": text, "spoken": text, "tone": own, "pause": pause, "slow": slow})
        elif (m := SPOKEN.match(raw)) and lines:
            lines[-1]["spoken"] = m[1].strip()
    problems = [l["id"] for l in lines if l["spoken"] == l["direction"] and bare(l["direction"]) != bare(captions[l["id"]])]
    missing = sorted(set(captions) - {l["id"] for l in lines})
    if problems or missing:
        raise SystemExit(f"direction differs from the captions: {problems}; not directed: {missing}")
    for l in lines:
        l["caption"] = captions[l["id"]]
        l["question"] = bool(QUESTION.search(l["caption"]))
        l["speed"] = QSPEED if l["question"] else SPEED
        if re.search(r"[\d〇]", bare(l["spoken"])):
            raise SystemExit(f"{l['id']}: digits or 〇 left in what the voice reads")
        if l["tone"] not in TONE:
            raise SystemExit(f"{l['id']}: unknown tone {l['tone']}")
    return lines


if __name__ == "__main__":
    args = sys.argv[1:]
    lines = load()
    if "--check-only" in args:
        print(f"{len(lines)} lines directed, all match the captions; {sum(l['question'] for l in lines)} questions at {QSPEED}")
        raise SystemExit
    only = set(args[args.index("--only") + 1].split(",")) if "--only" in args else None
    section = args[args.index("--section") + 1] if "--section" in args else None
    take = args[args.index("--take") + 1] if "--take" in args else ""
    TAKES.mkdir(parents=True, exist_ok=True)
    (TAKES / "lines.json").write_text(json.dumps(lines, ensure_ascii=False, indent=1))
    todo = [l for l in lines if (only is None or l["id"] in only) and (section is None or l["id"].startswith(section))]
    todo = [l for l in todo if take or not take_path(l).exists()]
    if "--part" in args:
        k, n = map(int, args[args.index("--part") + 1].split("/"))
        todo = todo[k - 1::n]
    if not todo:
        print("nothing to voice")
        raise SystemExit
    if "--plan" in args:
        print(f"{len(todo)} to voice:", " ".join(f"{l['id']}({l['tone']}@{l['speed'] * l['slow']:.2f})" for l in todo))
        raise SystemExit

    os.chdir(MEDIA)
    sys.path.insert(0, str(MEDIA / "src"))
    import torch  # noqa: E402

    torch.set_num_threads(int(os.environ.get("NARRATE_THREADS", "4")))
    torch.set_num_interop_threads(2)
    from lucas_media.cosyvoice_engine import CosyVoiceEngine  # noqa: E402
    from lucas_media.joke import DEFAULT_PEAK_DBFS, add_peak_headroom, save_wav  # noqa: E402

    engine = CosyVoiceEngine(MEDIA / f"profiles/{VOICE}/zh/profile.json")
    for n, line in enumerate(todo, 1):
        speech, rate, _ = engine.synthesize(line["spoken"], target_language="zh", mode="zero-shot-instruct",
                                            instruction=TONE[line["tone"]], speed=line["speed"] * line["slow"])
        path = take_path(line, take)
        path.parent.mkdir(parents=True, exist_ok=True)
        save_wav(path, add_peak_headroom(speech, peak_dbfs=DEFAULT_PEAK_DBFS), rate)
        secs = speech.shape[1] / rate
        print(f"[{n}/{len(todo)}] {line['id']} {secs:.2f}s {len(bare(line['spoken'])) / secs:.1f} 字/s"
              f" -> {path.parent.name}/{path.name}", flush=True)
