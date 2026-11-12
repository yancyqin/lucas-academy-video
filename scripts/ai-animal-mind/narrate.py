"""Voice 「动物想什么？AI 知道吗？」 from docs/ai-animal-mind/voice-direction.<lang>.md, one WAV per line.

Run with lucas-academy-media's Python, at most two processes at once (memory budget):
  ../lucas-academy-media/.conda/bin/python scripts/ai-animal-mind/narrate.py [--lang en|zh] [--voice louise] [--speed 1.1]
        [--only id,id | --section am01] [--part 1/2] [--take N] [--plan | --check-only]

Copied from scripts/fun-informatics-04/narrate.py. The English track comes first (Yancy 2026-11-10: Louise; the Chinese
track after Yancy confirms it), so --lang defaults to en: captions en-draft.md, direction voice-direction.en.md.
zero-shot-instruct, one speed for every line. A section's `｜语气 X` sets its tone, a line's own `｜语气 X` overrides it,
`停顿 N` is the silence before the line (build_timeline.py), `读 |` is what the voice reads when it differs from the
caption. Every directed line must match its caption once punctuation and quotes are gone, unless it has a 读 line; what
the voice reads has no digits and no 〇. Takes go to lucas-academy-media/outputs/<voice>/<lang>/ai-animal-mind-v1/s<speed>/,
with every line's settings in ai-animal-mind-v1/lines.json; existing takes are kept.
"""
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs/ai-animal-mind"
MEDIA = next(p / "lucas-academy-media" for p in ROOT.parents if (p / "lucas-academy-media").is_dir())
ARGS = sys.argv[1:]
LANG = ARGS[ARGS.index("--lang") + 1] if "--lang" in ARGS else "en"
VOICE = ARGS[ARGS.index("--voice") + 1] if "--voice" in ARGS else "louise"
SPEED = float(ARGS[ARGS.index("--speed") + 1]) if "--speed" in ARGS else 1.1
TAKES = MEDIA / f"outputs/{VOICE}/{LANG}/ai-animal-mind-v1"
SCRIPT, DIRECTION = (f"{LANG}-draft.md", "voice-direction.md" if LANG == "zh" else f"voice-direction.{LANG}.md")

TONE = {
    "基准": "请用亲切、好奇的语气，像跟朋友、跟家长一起发现一件有意思的事那样说。",
    "好奇": "请用好奇、温暖的语气，像在和朋友一起琢磨一个问题，不是在考问。",
    "温和": "请用温和、真诚的语气，像在安静地分享一段心里的话。",
    "base": "Please speak in a warm, curious voice, like discovering something interesting together with friends and parents.",
    "curious": "Please speak with warm curiosity, like wondering about a question together with a friend, never quizzing.",
    "gentle": "Please speak gently and sincerely, like quietly sharing something close to your heart.",
}
CAPTION = re.compile(r"^- (am\d\d-\d\d) \| (.+)$")
SECTION = re.compile(r"^## (AM\d\d) · .*｜语气 ([^\s（]+)")
DIRECTED = re.compile(r"^(am\d\d-\d\d) \| (.+)$")
SPOKEN = re.compile(r"^\s+读 \| (.+)$")
QUESTION = re.compile(r"[？?][」”\"]?$")
PUNCT = re.compile(r"[，。、；：？！…“”‘’「」『』《》（）—\-·+,.;:?!\"'()\s%]")


def bare(s: str) -> str:
    return PUNCT.sub("", re.sub(r"</?strong>|【[^】]*】", "", s))


def take_path(line: dict, take: str = "") -> Path:
    return TAKES / f"s{line['speed']:.2f}" / (f"{line['id']}.take{take}.wav" if take else f"{line['id']}.wav")


def load():
    captions = {}
    for raw in (DOCS / SCRIPT).read_text().splitlines():
        if m := CAPTION.match(raw):
            captions[m[1]] = m[2]
    lines, tone = [], None
    for raw in (DOCS / DIRECTION).read_text().splitlines():
        if m := SECTION.match(raw):
            tone = m[2]
        elif m := DIRECTED.match(raw):
            text, *notes = [p.strip() for p in m[2].split("｜")]
            own = next((n.split()[1] for n in notes if n.startswith("语气 ")), tone)
            pause = next((float(re.match(r"停顿 ([\d.]+)", n)[1]) for n in notes if n.startswith("停顿")), None)
            lines.append({"id": m[1], "direction": text, "spoken": text, "tone": own, "pause": pause})
        elif (m := SPOKEN.match(raw)) and lines:
            lines[-1]["spoken"] = m[1].strip()
    problems = [l["id"] for l in lines if l["spoken"] == l["direction"] and bare(l["direction"]) != bare(captions[l["id"]])]
    missing = sorted(set(captions) - {l["id"] for l in lines})
    if problems or missing:
        raise SystemExit(f"direction differs from the captions: {problems}; not directed: {missing}")
    for l in lines:
        l["caption"] = captions[l["id"]]
        l["question"] = bool(QUESTION.search(l["caption"]))
        l["speed"] = SPEED
        if re.search(r"[\d〇]", bare(l["spoken"])):
            raise SystemExit(f"{l['id']}: digits or 〇 left in what the voice reads")
        if l["tone"] not in TONE:
            raise SystemExit(f"{l['id']}: unknown tone {l['tone']}")
    return lines


if __name__ == "__main__":
    args = ARGS
    lines = load()
    if "--check-only" in args:
        print(f"{len(lines)} lines directed, all match the captions; {sum(l['question'] for l in lines)} questions")
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
        print(f"{len(todo)} to voice:", " ".join(f"{l['id']}({l['tone']}@{l['speed']:.2f})" for l in todo))
        raise SystemExit

    os.chdir(MEDIA)
    sys.path.insert(0, str(MEDIA / "src"))
    import torch  # noqa: E402

    torch.set_num_threads(int(os.environ.get("NARRATE_THREADS", "4")))
    torch.set_num_interop_threads(2)
    from lucas_media.cosyvoice_engine import CosyVoiceEngine  # noqa: E402
    from lucas_media.joke import DEFAULT_PEAK_DBFS, add_peak_headroom, save_wav  # noqa: E402

    engine = CosyVoiceEngine(MEDIA / f"profiles/{VOICE}/{LANG}/profile.json")
    for n, line in enumerate(todo, 1):
        speech, rate, _ = engine.synthesize(line["spoken"], target_language=LANG, mode="zero-shot-instruct",
                                            instruction=TONE[line["tone"]], speed=line["speed"])
        path = take_path(line, take)
        path.parent.mkdir(parents=True, exist_ok=True)
        save_wav(path, add_peak_headroom(speech, peak_dbfs=DEFAULT_PEAK_DBFS), rate)
        secs = speech.shape[1] / rate
        unit = len(bare(line["spoken"])) if LANG == "zh" else len(line["spoken"].split())
        print(f"[{n}/{len(todo)}] {line['id']} {secs:.2f}s {unit / secs:.1f} {'字' if LANG == 'zh' else 'w'}/s"
              f" -> {path.parent.name}/{path.name}", flush=True)
