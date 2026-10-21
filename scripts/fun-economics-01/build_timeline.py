"""Timeline for 「一根冰棍，要花多少钱？」 (FUN-ECONOMICS-01.md), paced by its own narration.

Reads public/fun-economics-01/narration/cues.<lang>.json (narration.py) and the takes in lucas-academy-media: Louise
for the narrator, Eunice for Mary's lines. Writes, for <lang> zh or en,
  public/fun-economics-01/timeline.<lang>.json   cue timeline Remotion loads before rendering
  public/fun-economics-01/audio/<lang>.wav       narration track
  public/fun-economics-01/audio/<lang>.mix.wav   narration over the music bed, -16 LUFS
  out/fun-economics-01/delivery/fun-economics-01.<lang>.zh-Hans.srt and .en.srt
Each film has captions in both languages (owner, 2026-10-15): the two scripts share cue ids, so the other
language's line is shown over the same cue.

Trimming, levelling and the ducked music mix are whole-person-01's, imported, not copied. The bed has three
pieces, each levelled to the same loudness and crossfaded at the section where its part of the film begins:
the Minuet in G (OC00–OC02), Joplin's Solace (OC03–OC05) and Satie's first Gymnopédie (OC06 to the end).
A missing take is stood in for by silence of an estimated length, and the timeline is marked draft.

  python3 scripts/fun-economics-01/build_timeline.py [--lang en] [--srt-only]
"""
import array
import importlib.util
import json
import math
import os
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PUB = ROOT / "public/fun-economics-01"
DELIVERY = ROOT / "out/fun-economics-01/delivery"
FILM_NAME = "fun-economics-01"


def _media() -> Path:
    if os.environ.get("LUCAS_MEDIA"):
        return Path(os.environ["LUCAS_MEDIA"])
    for parent in ROOT.parents:
        if (parent / "lucas-academy-media").is_dir():
            return parent / "lucas-academy-media"
    raise SystemExit("set LUCAS_MEDIA to a lucas-academy-media checkout")


MEDIA = _media()
_spec = importlib.util.spec_from_file_location("wp01", ROOT / "scripts/whole-person-01/build_timeline.py")
wp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(wp)
wp.PEAK_DB = -2.5  # AAC headroom for the final <= -1.5 dBTP ceiling (-2.0 gave -1.4 dBTP on the English film)

VOICES = {
    "zh": {"narrator": MEDIA / "outputs/louise/zh/fun-economics-01-v1", "mary": MEDIA / "outputs/eunice/zh/fun-economics-01-mary-v1"},
    "en": {"narrator": MEDIA / "outputs/louise/en/fun-economics-01-v1", "mary": MEDIA / "outputs/eunice/en/fun-economics-01-mary-v1"},
}
SRT_TAG = {"zh": "zh-Hans", "en": "en"}
TITLE = {"zh": "一根冰棍，要花多少钱？", "en": "How Much Does an Ice Pop Cost?"}
FPS, RATE = 30, wp.RATE
LEAD_IN, ONSET, GAP, SECTION_GAP, END_CARD = 0.8, 0.15, 0.4, 0.9, 8.0
# Seconds after a line for the picture: a question to think about, a card to read, an animation to finish.
HOLD = {
    "oc00-01": 0.3, "oc00-05": 2.0, "oc00-07": 3.5,
    "oc01-01": 1.0, "oc01-04": 1.5,
    "oc02-03": 1.5, "oc02-05": 1.0, "oc02-07": 1.5,
    "oc03-03": 1.0, "oc03-04": 1.5,
    "oc04-04": 1.0, "oc04-05": 2.0, "oc04-06": 1.5, "oc04-07": 1.5, "oc04-08": 2.0, "oc04-15": 0.5,
    "oc04-16": 1.0, "oc04-17": 1.5, "oc04-18": 1.5, "oc04-19": 2.0, "oc04-20": 1.0, "oc04-21": 1.5,
    "oc04-22": 2.0, "oc04-23": 1.0, "oc04-24": 2.0,
    "oc05-01": 1.0, "oc05-02": 2.5, "oc05-03": 1.5, "oc05-04": 1.5, "oc05-05": 2.0,
    "oc06-01": 1.0, "oc06-02": 1.0, "oc06-03": 3.0, "oc06-04": 2.0,
    "oc07-01": 4.0,
}
MUSIC = PUB / "music"
BED = [("oc00", MUSIC / "minuet-in-g-musopen.ogg"), ("oc03", MUSIC / "solace-joplin.ogg"), ("oc06", MUSIC / "gymnopedie-1-macleod.ogg")]
BED_XFADE, BED_LUFS = 3.0, -23.0


def listing(sub: str, exts: tuple) -> list:
    d = PUB / sub
    return sorted(str(f.relative_to(d)) for f in d.rglob("*") if f.suffix.lower() in exts) if d.is_dir() else []


def seconds(path: Path) -> float:
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                                capture_output=True, text=True, check=True).stdout.strip())


def music_bed(cues: list, total: float, out: Path) -> None:
    """The three pieces, each looped to cover its part and levelled to BED_LUFS, crossfaded into one bed."""
    starts = [0.0] + [next(c["start"] for c in cues if c["id"].startswith(sec)) for sec, _ in BED[1:]]
    ends = starts[1:] + [total + 1.0]
    with tempfile.TemporaryDirectory() as tmp:
        parts = []
        for k, ((_, src), a, b) in enumerate(zip(BED, starts, ends)):
            need = b - a + (BED_XFADE if k < len(BED) - 1 else 0)
            length = seconds(src)
            loops = max(1, math.ceil((need - 2) / (length - 2)))
            inputs = sum((["-i", str(src)] for _ in range(loops)), [])
            chain, last = [], "[0:a]"
            for n in range(1, loops):
                chain.append(f"{last}[{n}:a]acrossfade=d=2:c1=tri:c2=tri[l{n}]")
                last = f"[l{n}]"
            chain.append(f"{last}atrim=0:{need:.3f},asetpts=PTS-STARTPTS,aresample=48000,"
                         f"aformat=sample_fmts=flt:channel_layouts=stereo,loudnorm=I={BED_LUFS}:TP=-3:LRA=11[o]")
            part = Path(tmp, f"part{k}.wav")
            subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(chain), "-map", "[o]",
                            "-ar", "48000", "-c:a", "pcm_f32le", str(part)], check=True)
            parts.append(part)
        inputs = sum((["-i", str(p)] for p in parts), [])
        chain, last = [], "[0:a]"
        for n in range(1, len(parts)):
            chain.append(f"{last}[{n}:a]acrossfade=d={BED_XFADE}:c1=tri:c2=tri[x{n}]")
            last = f"[x{n}]"
        chain.append(f"{last}atrim=0:{total + 1:.3f},asetpts=PTS-STARTPTS[bed]")
        subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(chain), "-map", "[bed]",
                        "-ar", "48000", "-c:a", "pcm_f32le", str(out)], check=True)


LINE_CHARS = 22  # a Latin letter or digit counts half: 22 Chinese characters or 44 Latin ones


def width(text: str) -> float:
    return sum(0.5 if ord(ch) < 0x2E80 else 1 for ch in text)


def caption_lines(text: str, lang: str) -> list:
    """Chinese: clauses (split after punctuation) packed into lines of at most LINE_CHARS, a clause too long for a
    line broken at the limit. English: each sentence (a very short one joined to the next) broken between words into
    lines of at most 42 letters, as even as possible, preferring a break after a comma."""
    if lang == "en":
        return [ln for sentence in en_sentences(text) for ln in balanced(sentence.split(" "))]
    clauses = [c for c in re.split(r"(?<=[，、：；。！？])", text) if c.strip()]
    lines, cur = [], ""
    for c in clauses:
        if cur and width(cur + c) > LINE_CHARS:
            lines.append(cur)
            cur = ""
        while width(c) > LINE_CHARS:
            k = 1
            while width(c[:k + 1]) <= LINE_CHARS:
                k += 1
            lines.append(c[:k])
            c = c[k:]
        cur += c
    lines.append(cur)
    return lines


EN_LINE = 42


def en_sentences(text: str) -> list:
    out = []
    for s in re.split(r"(?<=[.!?”])\s+(?=[A-Z“0-9$])", text):
        if out and len(out[-1]) < 16:  # "Right." alone would flash by: keep it with the next sentence
            out[-1] += " " + s
        else:
            out.append(s)
    return out


def balanced(words: list) -> list:
    """Fewest, most even lines of at most EN_LINE letters (least squared slack), a little readier to break after
    punctuation."""
    n = len(words)
    best = [(0.0, 0)] + [(math.inf, 0)] * n
    for j in range(1, n + 1):
        for i in range(j - 1, -1, -1):
            line = " ".join(words[i:j])
            if len(line) > EN_LINE and j - i > 1:
                break
            cost = best[i][0] + (EN_LINE - len(line)) ** 2 + 2000 - (300 if line[-1] in ",;:" else 0)
            if cost < best[j][0]:
                best[j] = (cost, i)
    lines, j = [], n
    while j:
        i = best[j][1]
        lines.append(" ".join(words[i:j]))
        j = i
    return lines[::-1]


def caption_units(cue: dict, text: str, lang: str) -> list:
    """A cue's caption in blocks of at most two lines; a new sentence prefers a new block. Timed by each block's
    share of the speech; the last block holds to the end of the cue's slot."""
    blocks, cur = [], []
    for ln in caption_lines(text, lang):
        sentence_start = cur and cur[-1].rstrip("”")[-1:] in "。！？.!?"
        if len(cur) == 2 or (sentence_start and len(cur) == 1 and width(cur[0]) > LINE_CHARS / 2):
            blocks.append(cur)
            cur = []
        cur.append(ln)
    blocks.append(cur)
    a, b = cue["speech"]["start"], cue["speech"]["end"]
    total = sum(width("".join(bl)) for bl in blocks)
    out, t = [], a
    for i, bl in enumerate(blocks):
        end = cue["end"] - 0.1 if i == len(blocks) - 1 else t + (b - a) * width("".join(bl)) / total
        out.append((t, end, "\n".join(bl)))
        t = end
    return out


def write_srt(cues: list, lang: str) -> None:
    """The film's own language, and the other language over the same cues."""
    DELIVERY.mkdir(parents=True, exist_ok=True)
    own = json.loads((PUB / f"narration/cues.{lang}.json").read_text())
    for caption_lang in ("zh", "en"):
        texts = {c["id"]: c["text" if caption_lang == lang else "translation"] for c in own}
        units = [u for c in cues for u in caption_units(c, texts[c["id"]], caption_lang)]
        blocks = [f"{n}\n{wp.srt_time(a)} --> {wp.srt_time(b)}\n{text}\n" for n, (a, b, text) in enumerate(units, 1)]
        (DELIVERY / f"{FILM_NAME}.{lang}.{SRT_TAG[caption_lang]}.srt").write_text("\n".join(blocks), encoding="utf-8")
        print(f"  {caption_lang} captions: {len(units)} blocks")


def build(lang: str) -> None:
    cue_text = json.loads((PUB / f"narration/cues.{lang}.json").read_text())
    ids = [c["id"] for c in cue_text]
    footage = listing("footage", (".mp4",))
    missing, clips, trims = [], {}, {}
    for c in cue_text:
        path = VOICES[lang][c["speaker"]] / f"{c['id']}.wav"
        if path.is_file():
            raw = wp.read_wav(path)
            cut = wp.trim(raw)
            trims[c["id"]] = round(raw.tobytes().find(cut.tobytes()) / 2 / RATE, 3)
            clips[c["id"]] = wp.level(cut)
        else:
            missing.append(c["id"])
            clips[c["id"]] = wp.estimate(lang, c["spoken"])
    t, cues = LEAD_IN, []
    for n, c in enumerate(cue_text):
        speech = len(clips[c["id"]]) / RATE
        last_in_section = n + 1 == len(ids) or ids[n + 1][:4] != c["id"][:4]
        slot = ONSET + speech + GAP + HOLD.get(c["id"], 0) + (SECTION_GAP if last_in_section else 0)
        cues.append({"id": c["id"], "section": c["section"], "speaker": c["speaker"], "text": c["text"],
                     "start": round(t, 3), "end": round(t + slot, 3), "trim": trims.get(c["id"], 0.0),
                     "speech": {"start": round(t + ONSET, 3), "end": round(t + ONSET + speech, 3)}})
        t += slot
    total = t + END_CARD
    audio = PUB / "audio"
    audio.mkdir(parents=True, exist_ok=True)
    track = array.array("h", bytes(2 * round(total * RATE)))
    for cue in cues:
        at = round(cue["speech"]["start"] * RATE)
        clip = clips[cue["id"]]
        track[at:at + len(clip)] = clip
    wp.write_wav(audio / f"{lang}.wav", track, RATE)
    bed = audio / f"music-bed.{lang}.wav"
    music_bed(cues, total, bed)
    wp.MUSIC = bed
    wp.mix_with_music(audio / f"{lang}.wav", audio / f"{lang}.mix.wav", cues, total)
    DELIVERY.mkdir(parents=True, exist_ok=True)
    write_srt(cues, lang)
    data = {"lang": lang, "fps": FPS, "leadIn": LEAD_IN, "title": TITLE, "draft": bool(missing),
            "durationSeconds": round(total, 3), "endCardStart": round(t, 3),
            "images": listing("images", (".png", ".jpg")), "art": listing("art", (".png", ".jpg")),
            "footage": footage, "footageSeconds": {name: seconds(PUB / "footage" / name) for name in footage},
            "cues": cues}
    marks = PUB / f"markers.{lang}.json"
    if marks.exists():
        data["markers"] = json.loads(marks.read_text())
    (PUB / f"timeline.{lang}.json").write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n")
    print(f"{lang}: {len(cues)} cues, {total:.1f}s ({total / 60:.1f} min)")
    if missing:
        print(f"  ESTIMATED (no wav yet): {len(missing)} lines, e.g. {', '.join(missing[:6])}")


if __name__ == "__main__":
    import sys
    LANG = sys.argv[sys.argv.index("--lang") + 1] if "--lang" in sys.argv else "zh"
    if "--srt-only" in sys.argv:  # captions only, from the existing timeline (safe while a render is running)
        write_srt(json.loads((PUB / f"timeline.{LANG}.json").read_text())["cues"], LANG)
    else:
        build(LANG)
