"""Voice the English track of 「你爱听 AI 说「是的」吗？」 in Yancy's voice from docs/ai-sycophancy/en-edit.md, one WAV per line.

  ../lucas-academy-media/.conda/bin/python scripts/ai-sycophancy/narrate_en.py [--only id,id] [--part 1/2] [--take N] [--plan]

As in 「跨越中等收入陷阱」 (scripts/middle-income-trap/narrate_en.py): the yancy/zh profile read through CosyVoice
cross-lingual with the delivery instruction in the system slot, statements at SPEED and questions at QSPEED, each
line in the mood its Chinese line has in voice-direction.md (narrate.py works that out). Captions keep digits; the
voice reads them spelled out, dates as ordinals. Takes go to lucas-academy-media/outputs/yancy/en/ai-sycophancy-v1/;
existing takes are kept. At most two processes at once (memory budget); --part k/n splits what is left.
"""
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import narrate  # noqa: E402  (the Chinese lines and their moods)

DOCS = ROOT / "docs/ai-sycophancy"
MEDIA = narrate.MEDIA
OUT = MEDIA / "outputs/yancy/en/ai-sycophancy-v1"
SPEED, QSPEED = 1.1, 1.0
TONE = {
    "基准": "Speak in a sincere, warm, heartfelt voice, like talking with friends and parents about something you care about. Natural pace.",
    "凝重": "Speak in a sincere, grave voice, like telling a painful story. Steady and calm.",
    "温和": "Speak in a warm, sincere, hopeful voice.",
}
LINE = re.compile(r"^- (sc\d\d-\d\d) \| (.+)$")
QUESTION = re.compile(r"\?[\"”’]?$")
# Words the voice gets wrong as written: say them the way they sound.
SAY = {"AIs": "A.I.s", "AI": "A.I.", "OpenAI": "Open A.I.", "ChatGPT": "Chat G.P.T.", "US": "U.S.", "UK": "U.K.",
       "Dongtai": "Dong-tie", "Jiangsu": "Jyang-soo"}
MONTHS = "January|February|March|April|May|June|July|August|September|October|November|December"

ONES = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve",
        "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen"]
TENS = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]
ORD = {"one": "first", "two": "second", "three": "third", "five": "fifth", "eight": "eighth", "nine": "ninth", "twelve": "twelfth"}


def words(n: int) -> str:
    if n < 20:
        return ONES[n]
    if n < 100:
        t, o = divmod(n, 10)
        return TENS[t] + (f"-{ONES[o]}" if o else "")
    if n < 1000:
        h, r = divmod(n, 100)
        return f"{ONES[h]} hundred" + (f" {words(r)}" if r else "")
    if n < 2000 and n % 100 == 0:  # 1,800 is "eighteen hundred"
        return f"{words(n // 100)} hundred"
    th, r = divmod(n, 1000)
    return f"{words(th)} thousand" + (f" {words(r)}" if r else "")


def ordinal(n: int) -> str:
    head, _, last = words(n).rpartition("-")
    last = ORD.get(last) or (last[:-1] + "ieth" if last.endswith("y") else last + "th")
    return f"{head}-{last}" if head else last


def year(n: int) -> str:
    hi, lo = divmod(n, 100)
    return f"{words(hi)} {'oh-' + ONES[lo] if 0 < lo < 10 else words(lo)}"


def spoken(text: str) -> str:
    for a, b in SAY.items():
        text = re.sub(rf"(?<![\w.]){re.escape(a)}(?=\W|$)", b, text)
    text = re.sub(rf"\b({MONTHS}) (\d{{1,2}})\b", lambda m: f"{m[1]} {ordinal(int(m[2]))}", text)
    text = re.sub(r"\b(\d+)(?:st|nd|rd|th)\b", lambda m: ordinal(int(m[1])), text)
    text = re.sub(r"\b((?:19|20)\d\d)\b", lambda m: year(int(m[1])), text)
    text = re.sub(r"(\d+)%", lambda m: words(int(m[1])) + " percent", text)
    text = re.sub(r"\b(\d{1,3}(?:,\d{3})+|\d+)\b", lambda m: words(int(m[1].replace(",", ""))), text)
    assert not re.search(r"\d", text), text
    return text


def load() -> list:
    mood = {l["id"]: l["tone"] for l in narrate.load()}
    lines = []
    for raw in (DOCS / "en-edit.md").read_text().splitlines():
        if m := LINE.match(raw):
            cid, text = m[1], m[2].strip()
            q = bool(QUESTION.search(text))
            lines.append({"id": cid, "caption": text, "spoken": spoken(text), "tone": mood[cid], "question": q,
                          "instruct": TONE[mood[cid]], "speed": QSPEED if q else SPEED})
    if {l["id"] for l in lines} != set(mood):
        raise SystemExit(f"en-edit ids differ from the Chinese: {sorted(set(mood) ^ {l['id'] for l in lines})}")
    return lines


if __name__ == "__main__":
    args = sys.argv[1:]
    lines = load()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "lines.json").write_text(json.dumps(lines, ensure_ascii=False, indent=1))
    only = set(args[args.index("--only") + 1].split(",")) if "--only" in args else None
    take = args[args.index("--take") + 1] if "--take" in args else ""
    todo = [l for l in lines if (only is None or l["id"] in only) and (take or not (OUT / f"{l['id']}.wav").exists())]
    if "--part" in args:
        k, n = map(int, args[args.index("--part") + 1].split("/"))
        todo = todo[k - 1::n]
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
    for n, line in enumerate(todo, 1):
        gen = engine.model.inference_cross_lingual(f"You are a helpful assistant. {line['instruct']}<|endofprompt|>" + line["spoken"],
                                                   str(engine.reference_audio), stream=False, speed=line["speed"])
        speech, rate = torch.cat([x["tts_speech"].cpu() for x in gen], dim=1), engine.model.sample_rate
        path = OUT / (f"{line['id']}.take{take}.wav" if take else f"{line['id']}.wav")
        save_wav(path, add_peak_headroom(speech, peak_dbfs=DEFAULT_PEAK_DBFS), rate)
        secs = speech.shape[1] / rate
        print(f"[{n}/{len(todo)}] {line['id']} {secs:.2f}s {len(line['spoken'].split()) / secs:.1f} w/s -> {path.name}", flush=True)
