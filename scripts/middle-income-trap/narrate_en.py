"""Voice the English track of 「跨越中等收入陷阱」 in Yancy's voice from docs/middle-income-trap/en-edit.md, one WAV per line.

Run with lucas-academy-media's Python:
  ../lucas-academy-media/.conda/bin/python scripts/middle-income-trap/narrate_en.py [--only id,id] [--take N] [--plan]

Same as 「法国人走上街头」's English (scripts/news-education-01/narrate.py): the yancy/zh profile read through CosyVoice
cross-lingual, with the delivery instruction in the system slot. Each section keeps the Chinese track's mood
(voice-direction.md: 基准 / 凝重 / 希望) and the Chinese `慢 0.9` lines are slowed the same way. The English has to fit
the Chinese timing (the picture is finished), so statements go a little faster than 「法国人」 (SPEED) and questions
are read at QSPEED (Yancy, 2026-10-25: 问问题的句子慢一些). Captions keep digits; the voice reads them spelled out.
Takes go to lucas-academy-media/outputs/yancy/en/middle-income-trap-v2/; existing takes are kept.
"""
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs/middle-income-trap"
for parent in ROOT.parents:
    if (parent / "lucas-academy-media").is_dir():
        MEDIA = parent / "lucas-academy-media"
        break
OUT = MEDIA / "outputs/yancy/en/middle-income-trap-v2"
SPEED, QSPEED = 1.1, 1.0
TONE = {
    "基准": "Speak in a sincere, warm, engaged voice, like talking with friends and parents about something you care about. Natural, lively pace.",
    "凝重": "Speak in a sincere, grave voice, like telling a painful story. Steady and calm.",
    "希望": "Speak in a warm, sincere, hopeful voice.",
}
LINE = re.compile(r"^- (sc\d\d-\d\d) \| (.+)$")
SECTION = re.compile(r"^## (SC\d\d) · .*｜语气 ([^\s（]+)")
DIRECTED = re.compile(r"^(sc\d\d-\d\d) \| (.+)$")
QUESTION = re.compile(r"\?[\"”]?$")
# Words the voice gets wrong as written: say them the way they sound.
SAY = {"AI": "A.I.", "PhD": "P.H.D", "Jr.": "Junior", "Woessmann": "Wossmann", "Freire": "Fray-ree", "Gen Z": "Gen Zee"}

ONES = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve",
        "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen"]
TENS = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]


def words(n: int) -> str:
    if n < 20:
        return ONES[n]
    if n < 100:
        t, o = divmod(n, 10)
        return TENS[t] + (f"-{ONES[o]}" if o else "")
    if n < 1000:
        h, r = divmod(n, 100)
        return f"{ONES[h]} hundred" + (f" {words(r)}" if r else "")
    th, r = divmod(n, 1000)
    return f"{words(th)} thousand" + (f" {words(r)}" if r else "")


def year(n: int) -> str:
    hi, lo = divmod(n, 100)
    return f"{words(hi)} {'oh-' + ONES[lo] if 0 < lo < 10 else words(lo)}"


def spoken(text: str) -> str:
    for a, b in SAY.items():
        text = re.sub(rf"\b{re.escape(a)}(?=\W|$)", b, text)
    text = re.sub(r"\b(1[89]\d\d)\b", lambda m: year(int(m[1])), text)
    text = re.sub(r"(\d+)%", lambda m: words(int(m[1])) + " percent", text)
    text = re.sub(r"\b(\d{1,3}(?:,\d{3})+|\d+)\b", lambda m: words(int(m[1].replace(",", ""))), text)
    assert not re.search(r"\d", text), text
    return text


def load() -> list:
    tone, mood, slow = None, {}, {}
    for raw in (DOCS / "voice-direction.md").read_text().splitlines():
        if m := SECTION.match(raw):
            tone = m[2]
        elif m := DIRECTED.match(raw):
            mood[m[1]] = tone
            if s := re.search(r"慢 ([\d.]+)", m[2]):
                slow[m[1]] = float(s[1])
    lines = []
    for raw in (DOCS / "en-edit.md").read_text().splitlines():
        if m := LINE.match(raw):
            cid, text = m[1], m[2].strip()
            speed = (QSPEED if QUESTION.search(text) else SPEED) * slow.get(cid, 1.0)
            lines.append({"id": cid, "caption": text, "spoken": spoken(text), "tone": mood[cid],
                          "instruct": TONE[mood[cid]], "speed": round(speed, 3)})
    zh = {m[1] for raw in (DOCS / "zh-edit.md").read_text().splitlines() if (m := LINE.match(raw))}
    if {l["id"] for l in lines} != zh:
        raise SystemExit(f"en-edit ids differ from zh-edit: {sorted(zh ^ {l['id'] for l in lines})}")
    return lines


args = sys.argv[1:]
lines = load()
only = set(args[args.index("--only") + 1].split(",")) if "--only" in args else None
take = args[args.index("--take") + 1] if "--take" in args else ""
todo = [l for l in lines if (only is None or l["id"] in only) and (take or not (OUT / f"{l['id']}.wav").exists())]
if "--plan" in args or not todo:
    print(f"{len(todo)} to voice:", " ".join(f"{l['id']}@{l['speed']}" for l in todo))
    raise SystemExit

os.chdir(MEDIA)
sys.path.insert(0, str(MEDIA / "src"))
import torch  # noqa: E402

torch.set_num_threads(int(os.environ.get("NARRATE_THREADS", "4")))
torch.set_num_interop_threads(2)
from lucas_media.cosyvoice_engine import CosyVoiceEngine  # noqa: E402
from lucas_media.joke import DEFAULT_PEAK_DBFS, add_peak_headroom, save_wav  # noqa: E402

engine = CosyVoiceEngine(MEDIA / "profiles/yancy/zh/profile.json")
OUT.mkdir(parents=True, exist_ok=True)
for n, line in enumerate(todo, 1):
    gen = engine.model.inference_cross_lingual(f"You are a helpful assistant. {line['instruct']}<|endofprompt|>" + line["spoken"],
                                               str(engine.reference_audio), stream=False, speed=line["speed"])
    speech, rate = torch.cat([x["tts_speech"].cpu() for x in gen], dim=1), engine.model.sample_rate
    path = OUT / (f"{line['id']}.take{take}.wav" if take else f"{line['id']}.wav")
    save_wav(path, add_peak_headroom(speech, peak_dbfs=DEFAULT_PEAK_DBFS), rate)
    secs = speech.shape[1] / rate
    print(f"[{n}/{len(todo)}] {line['id']} {secs:.2f}s {len(line['spoken'].split()) / secs:.1f} w/s -> {path.name}", flush=True)
(OUT / "lines.json").write_text(json.dumps(lines, ensure_ascii=False, indent=1))
