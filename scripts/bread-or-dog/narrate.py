"""Voice 「怎么骗过 AI：面包还是狗？」 from docs/bread-or-dog/voice-direction.md (zh) and en-edit.md (en), one WAV per line.

Run with lucas-academy-media's Python, at most two processes at once (memory budget):
  ../lucas-academy-media/.conda/bin/python scripts/bread-or-dog/narrate.py [--lang en] [--voice louise] [--speed 1.1]
      [--only id,id | --section sc01] [--part 1/2] [--take N] [--plan]
  ../lucas-academy-media/.conda/bin/python scripts/bread-or-dog/narrate.py --check-only

Copied from scripts/butterfly-challenge/narrate.py. Yancy, 2026-11-16: 「Louise 1.1，英文视频配中文音轨」 — louise/en 1.1 is
the default track, louise/zh 1.1 the Chinese m4a. zero-shot-instruct, one base delivery for the film (no pace words);
sc02-09, the question to the viewer, reads curious. Before voicing, every directed zh line is checked against the caption
script (zh-edit.md): same characters once tags and punctuation are gone, unless it has a 读 line; what the voice reads
must have no digits and no 〇. Takes go to lucas-academy-media/outputs/<voice>/<lang>/bread-or-dog-v1/s<speed>/.
"""
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs/bread-or-dog"
MEDIA = next(p / "lucas-academy-media" for p in ROOT.parents if (p / "lucas-academy-media").is_dir())
RUN = "bread-or-dog-v2"  # v0.4 script (2026-11-16); unchanged lines copied from bread-or-dog-v1

TONE = {"基准": "请用轻松、温暖、有点俏皮的语气，像跟朋友、跟家长分享一个好玩的小实验。",
        "base": "Please speak in a light, warm, playful voice, like sharing a fun little experiment with friends and parents.",
        # sc02-09, Yancy 11-16: 「你觉得，Astra 说『柴犬肉桂卷』，是被骗了，还是在陪我玩？」 — curious, never quizzing
        "好奇": "请用好奇、温暖的语气，像在和朋友聊天，真心想听听对方怎么想，不是在考问。",
        "curious": "Please speak with warm, playful curiosity, like wondering aloud with a friend and really wanting their opinion, never quizzing."}
EN_LINE = re.compile(r"^- (sc\d\d-\d\d) \| (.+)$")
EN_SPOKEN = re.compile(r"^\s+读 \| (.+)$")
EN_TONE = re.compile(r"^\s+语气 \| (\w+)$")
CAPTION = re.compile(r"^- (sc\d\d-\d\d) \| (.+)$")
SECTION = re.compile(r"^## (SC\d\d) · .*｜语气 ([^\s（]+)")
DIRECTED = re.compile(r"^(sc\d\d-\d\d) \| (.+)$")
SPOKEN = re.compile(r"^\s+读 \| (.+)$")
QUESTION = re.compile(r"？[」”]?$")
PUNCT = re.compile(r"[，。、；：？！…“”‘’「」『』《》（）—\-·+,.;:?!\"'()\s%]")


def bare(s: str) -> str:
    return PUNCT.sub("", re.sub(r"</?strong>|【[^】]*】", "", s))


def opt(args, name, default):
    return args[args.index(name) + 1] if name in args else default


def takes_dir(voice: str, lang: str = "zh") -> Path:
    return MEDIA / f"outputs/{voice}/{lang}/{RUN}"


def take_path(line: dict, voice: str, take: str = "", lang: str = "zh") -> Path:
    return takes_dir(voice, lang) / f"s{line['speed']:.2f}" / (f"{line['id']}.take{take}.wav" if take else f"{line['id']}.wav")


def load_en(speed: float = 1.1):
    """The English track: en-edit.md's captions, spoken as written unless a 读 line says otherwise."""
    lines = []
    for raw in (DOCS / "en-edit.md").read_text().splitlines():
        if m := EN_LINE.match(raw):
            cap = m[2].strip()
            lines.append({"id": m[1], "caption": cap, "spoken": re.sub(r"【[^】]*】", "", cap), "tone": "base",
                          "pause": None, "reveal": False, "question": cap.endswith("?"),
                          "speed": speed, "lang": "en"})
        elif (m := EN_SPOKEN.match(raw)) and lines:
            lines[-1]["spoken"] = m[1].strip()
        elif (m := EN_TONE.match(raw)) and lines:
            lines[-1]["tone"] = m[1]
    zh_ids = [l["id"] for l in load()]
    if [l["id"] for l in lines] != zh_ids:
        raise SystemExit("en-edit.md and zh-edit.md must have the same line ids in the same order")
    for l in lines:
        if re.search(r"\d", l["spoken"]):
            raise SystemExit(f"{l['id']}: digits left in what the English voice reads")
        if re.search(r"\b(can't|won't|don't|isn't|didn't)\b", l["spoken"], re.I):
            raise SystemExit(f"{l['id']}: a contraction Louise's English can flip (use cannot, will not, ...)")
    return lines


def load(speed: float = 1.2, qspeed: float = 1.1):
    captions = {}
    for raw in (DOCS / "zh-edit.md").read_text().splitlines():
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
            lines.append({"id": m[1], "direction": text, "spoken": text, "tone": own, "pause": pause})
        elif (m := SPOKEN.match(raw)) and lines:
            lines[-1]["spoken"] = m[1].strip()
    problems = [l["id"] for l in lines if l["spoken"] == l["direction"] and bare(l["direction"]) != bare(captions[l["id"]])]
    missing = sorted(set(captions) - {l["id"] for l in lines})
    if problems or missing:
        raise SystemExit(f"direction differs from the captions: {problems}; not directed: {missing}")
    for l in lines:
        l["caption"] = captions[l["id"]]
        l["reveal"] = False
        l["question"] = bool(QUESTION.search(l["caption"]))
        l["speed"] = qspeed if l["question"] else speed
        if re.search(r"[\d〇]", bare(l["spoken"])):
            raise SystemExit(f"{l['id']}: digits or 〇 left in what the voice reads")
        if l["tone"] not in TONE:
            raise SystemExit(f"{l['id']}: unknown tone {l['tone']}")
    return lines


if __name__ == "__main__":
    args = sys.argv[1:]
    voice = opt(args, "--voice", "louise")  # Yancy 2026-11-16: Louise 1.1
    lang = opt(args, "--lang", "zh")
    lines = (load_en(float(opt(args, "--speed", "1.1"))) if lang == "en"
             else load(float(opt(args, "--speed", "1.1")), float(opt(args, "--qspeed", "1.1"))))
    if "--check-only" in args:
        print(f"{len(lines)} lines directed, all match the captions; {sum(l['question'] for l in lines)} questions,"
              f" {sum(l['reveal'] for l in lines)} reveal lines")
        raise SystemExit
    only = set(opt(args, "--only", "").split(",")) - {""} or None
    section = opt(args, "--section", None)
    take = opt(args, "--take", "")
    out = takes_dir(voice, lang)
    out.mkdir(parents=True, exist_ok=True)
    (out / "lines.json").write_text(json.dumps(lines, ensure_ascii=False, indent=1))
    todo = [l for l in lines if (only is None or l["id"] in only) and (section is None or l["id"].startswith(section))]
    todo = [l for l in todo if take or not take_path(l, voice, "", lang).exists()]
    if "--part" in args:
        k, n = map(int, opt(args, "--part", "1/1").split("/"))
        todo = todo[k - 1::n]
    if not todo:
        print("nothing to voice")
        raise SystemExit
    if "--plan" in args:
        print(f"{voice}: {len(todo)} to voice:", " ".join(f"{l['id']}@{l['speed']:.2f}" for l in todo))
        raise SystemExit

    os.chdir(MEDIA)
    sys.path.insert(0, str(MEDIA / "src"))
    import torch  # noqa: E402

    torch.set_num_threads(int(os.environ.get("NARRATE_THREADS", "4")))
    torch.set_num_interop_threads(2)
    from lucas_media.cosyvoice_engine import CosyVoiceEngine  # noqa: E402
    from lucas_media.joke import DEFAULT_PEAK_DBFS, add_peak_headroom, save_wav  # noqa: E402

    engine = CosyVoiceEngine(MEDIA / f"profiles/{voice}/{lang}/profile.json")
    for n, line in enumerate(todo, 1):
        speech, rate, _ = engine.synthesize(line["spoken"], target_language=lang, mode="zero-shot-instruct",
                                            instruction=TONE[line["tone"]], speed=line["speed"])
        path = take_path(line, voice, take, lang)
        path.parent.mkdir(parents=True, exist_ok=True)
        save_wav(path, add_peak_headroom(speech, peak_dbfs=DEFAULT_PEAK_DBFS), rate)
        secs = speech.shape[1] / rate
        rate_txt = (f"{len(line['spoken'].split()) / secs:.1f} words/s" if lang == "en"
                    else f"{len(bare(line['spoken'])) / secs:.1f} 字/s")
        print(f"[{n}/{len(todo)}] {line['id']} {secs:.2f}s {rate_txt}"
              f" -> {path.parent.name}/{path.name}", flush=True)
