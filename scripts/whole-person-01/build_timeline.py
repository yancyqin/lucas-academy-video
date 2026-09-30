"""Build the shared zh/en timeline for "全人教育①：老师的权柄从哪里来？".

lucas-academy-media#5. Reads the confirmed line scripts and per-line narration
WAVs from lucas-academy-media, then writes:
  src/data/whole-person-01.json            cue timeline for Remotion
  public/whole-person-01/audio/{zh,en}.wav full-length narration tracks
  out/whole-person-01/{zh-Hans,en}.srt     single-language captions
  out/whole-person-01/bilingual.srt        zh + en on one caption

The zh and en scripts were split into sentences independently, so a cue pairs
one or more zh lines with one or more en lines of the same meaning (CUES).
Every cue lasts max(zh, en) + pause, so one picture edit carries either track.

A missing WAV is stood in for by silence of an estimated length (and reported),
so layout work can start before narration finishes.
"""
import array
import json
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MEDIA = ROOT.parent / "lucas-academy-media"
SCRIPTS = {
    "zh": MEDIA / "data/scripts/whole-person-01-authority-zh.json",
    "en": MEDIA / "data/scripts/whole-person-01-authority-en.json",
}
VOICES = {
    "zh": MEDIA / "outputs/yancy/zh/whole-person-01-d",   # Yancy, instruct tone + emphasis
    "en": MEDIA / "outputs/louise/en/whole-person-01",
}
FPS = 30
RATE = 24000
LEAD_IN = 4.0      # title card before the first word
ONSET = 0.2        # breath at the start of every cue
GAP = 0.55         # after every cue
JOIN = 0.3         # between two lines of one language inside a cue
SECTION_GAP = 1.0  # extra at the end of a section
END_CARD = 9.0
# Extra time to read a card or look at a picture after a line.
HOLD = {
    "wp02-01": 1.2, "wp06-02": 0.8, "wp06-04": 0.8, "wp07-05": 0.8,
    "wp09-06": 1.0, "wp10-03": 1.8, "wp10-04": 2.5,
}

# Cue id -> (zh line ids, en line ids). Ids not listed pair one-to-one.
GROUPS = {
    "wp04-01": (["wp04-01", "wp04-02"], ["wp04-01"]),
    "wp04-03": (["wp04-03"], ["wp04-02"]),
    "wp04-04": (["wp04-04"], ["wp04-03"]),
    "wp04-05": (["wp04-05"], ["wp04-04"]),
    "wp04-06": (["wp04-06"], ["wp04-05"]),
    "wp06-01": (["wp06-01"], ["wp06-01"]),
    "wp06-02": (["wp06-02"], ["wp06-02", "wp06-03", "wp06-04"]),
    "wp06-03": (["wp06-03"], ["wp06-05"]),
    "wp06-04": (["wp06-04"], ["wp06-06", "wp06-07"]),
    "wp07-01": (["wp07-01"], ["wp07-01"]),
    "wp07-02": (["wp07-02"], ["wp07-02", "wp07-03"]),
    "wp07-03": (["wp07-03"], ["wp07-04"]),
    "wp07-04": (["wp07-04"], ["wp07-05"]),
    "wp07-05": (["wp07-05"], ["wp07-06"]),
    "wp08-03": (["wp08-03", "wp08-04"], ["wp08-03"]),
    "wp08-05": (["wp08-05"], ["wp08-04"]),
}
GROUPED_SECTIONS = {"wp04", "wp06", "wp07"}  # every line of these is in GROUPS
SKIP = {"wp08-04"}  # zh line absorbed into cue wp08-03


def read_wav(path: Path) -> array.array:
    with wave.open(str(path)) as w:
        assert w.getframerate() == RATE and w.getnchannels() == 1 and w.getsampwidth() == 2, path
        return array.array("h", w.readframes(w.getnframes()))


def estimate(lang: str, text: str) -> array.array:
    seconds = len(text) / 4.2 if lang == "zh" else len(text.split()) / 2.5
    return array.array("h", bytes(2 * round(seconds * RATE)))


def srt_time(t: float) -> str:
    ms = round(t * 1000)
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def build_cues(lines: dict) -> list[dict]:
    cues = []
    for zid in lines["zh"]:
        if zid in SKIP:
            continue
        if zid[:4] in GROUPED_SECTIONS or zid in GROUPS:
            if zid not in GROUPS:
                continue
            zh_ids, en_ids = GROUPS[zid]
        else:
            zh_ids, en_ids = [zid], [zid]
        cues.append({"id": zid, "section": zid[:4], "zh_ids": zh_ids, "en_ids": en_ids})
    # Every line of both languages must be spoken exactly once.
    for lang, key in (("zh", "zh_ids"), ("en", "en_ids")):
        used = [i for c in cues for i in c[key]]
        assert sorted(used) == sorted(lines[lang]), f"{lang} lines not covered once: {set(lines[lang]) ^ set(used)}"
    return cues


def main() -> None:
    lines = {lang: {l["id"]: l["text"] for l in json.loads(p.read_text())["lines"]} for lang, p in SCRIPTS.items()}
    title = {lang: json.loads(p.read_text())["title"] for lang, p in SCRIPTS.items()}
    cues = build_cues(lines)

    missing = []
    samples = {}
    for lang, d in VOICES.items():
        samples[lang] = {}
        for lid, text in lines[lang].items():
            path = d / f"{lid}.wav"
            if path.is_file():
                samples[lang][lid] = read_wav(path)
            else:
                missing.append(f"{lang}/{lid}")
                samples[lang][lid] = estimate(lang, text)

    def span(lang: str, ids: list[str]) -> float:
        return sum(len(samples[lang][i]) for i in ids) / RATE + JOIN * (len(ids) - 1)

    t = LEAD_IN
    timeline = []
    for i, c in enumerate(cues):
        dur = {"zh": span("zh", c["zh_ids"]), "en": span("en", c["en_ids"])}
        last_in_section = i + 1 == len(cues) or cues[i + 1]["section"] != c["section"]
        slot = ONSET + max(dur.values()) + GAP + HOLD.get(c["id"], 0) + (SECTION_GAP if last_in_section else 0)
        timeline.append({
            "id": c["id"], "section": c["section"],
            "zh": "".join(lines["zh"][j] for j in c["zh_ids"]),
            "en": " ".join(lines["en"][j] for j in c["en_ids"]),
            "zhIds": c["zh_ids"], "enIds": c["en_ids"],
            "start": round(t, 3), "end": round(t + slot, 3),
            "speech": {lang: {"start": round(t + ONSET, 3), "end": round(t + ONSET + d, 3)} for lang, d in dur.items()},
        })
        t += slot
    total = t + END_CARD

    audio_dir = ROOT / "public/whole-person-01/audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    for lang in VOICES:
        track = array.array("h", bytes(2 * round(total * RATE)))
        key = "zhIds" if lang == "zh" else "enIds"
        for cue in timeline:
            at = round(cue["speech"][lang]["start"] * RATE)
            for lid in cue[key]:
                clip = samples[lang][lid]
                track[at:at + len(clip)] = clip
                at += len(clip) + round(JOIN * RATE)
        with wave.open(str(audio_dir / f"{lang}.wav"), "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(RATE)
            w.writeframes(track.tobytes())

    out = ROOT / "out/whole-person-01"
    out.mkdir(parents=True, exist_ok=True)

    def write_srt(name: str, text, lang: str | None) -> None:
        blocks = []
        for n, cue in enumerate(timeline, 1):
            start = cue["speech"][lang]["start"] if lang else cue["start"] + ONSET
            end = cue["end"] - 0.1
            blocks.append(f"{n}\n{srt_time(start)} --> {srt_time(end)}\n{text(cue)}\n")
        (out / name).write_text("\n".join(blocks), encoding="utf-8")

    write_srt("zh-Hans.srt", lambda c: c["zh"], "zh")
    write_srt("en.srt", lambda c: c["en"], "en")
    write_srt("bilingual.srt", lambda c: f"{c['zh']}\n{c['en']}", None)

    def present(sub: str, exts: tuple[str, ...]) -> list[str]:
        d = ROOT / "public/whole-person-01" / sub
        return sorted(f.name for f in d.iterdir() if f.suffix.lower() in exts) if d.is_dir() else []

    data = {
        "fps": FPS, "title": title, "leadIn": LEAD_IN,
        "concepts": present("concept", (".png", ".jpg")), "footage": present("footage", (".mp4", ".mov", ".webm")),
        "durationSeconds": round(total, 3), "endCardStart": round(t, 3), "cues": timeline,
    }
    (ROOT / "src/data/whole-person-01.json").write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n")
    print(f"{len(timeline)} cues, {total:.1f}s ({total/60:.1f} min)")
    for lang in VOICES:
        print(lang, f"speech {sum(len(v) for v in samples[lang].values())/RATE:.1f}s")
    if missing:
        print(f"ESTIMATED (no wav yet): {len(missing)} lines, e.g. {', '.join(missing[:6])}")


if __name__ == "__main__":
    main()
