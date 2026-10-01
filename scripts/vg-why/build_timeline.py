"""Build the shared zh/en timeline for "Why Did Van Gogh Paint Them?".

Reads the confirmed cue script and the per-cue narration WAVs from
lucas-academy-media, then writes:
  src/data/vg-why-paint-them.json          cue timeline for Remotion
  public/vg-why-paint-them/audio/{zh,en}.wav  full-length narration tracks
  out/vg-why-paint-them/{zh-Hans,en}.srt   YouTube captions, one per language

Every cue lasts max(zh, en) + pause, so one picture edit carries either track,
and both caption files share the same time codes: any caption language lines
up with either audio track.
"""
import array
import json
import sys
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MEDIA = ROOT.parent / "lucas-academy-media"
SCRIPT = MEDIA / "data/scripts/vg-why-paint-them/cues.json"
VOICES = {
    "zh": MEDIA / "outputs/fangfang/zh/vg-why-paint-them",
    "en": MEDIA / "outputs/louise/en/vg-why-paint-them",
}
FPS = 30
RATE = 24000
LEAD_IN = 1.0      # picture before the first word
ONSET = 0.2        # breath at the start of every cue
GAP = 0.55         # after every cue
SECTION_GAP = 0.9  # extra at the end of a section
END_CARD = 7.0
# CosyVoice copies the reference recording's room tone: fangfang's takes open
# with ~0.9 s of it at about -48 dBFS before the first word. Trimming it keeps
# each voice on its cue (and the captions on the voice); frames within 30 dB of
# a take's loudest are speech, and a little air is kept around the words.
TRIM_DB = 30
PAD_LEAD, PAD_TAIL = 0.2, 0.2
TRIM_FADE = 0.02
# Extra time to look at the picture after a line (issue #3: 看画的停顿).
HOLD = {
    "vg01-04": 0.8, "vg02-02": 0.6, "vg02-04": 0.8, "vg03-04": 1.0, "vg03-05": 1.0,
    # The Roulin family: one by one, then the wall of portraits ("again and again").
    "vg03-06": 1.0, "vg03-07": 2.5, "vg04-02": 1.0, "vg05-04": 0.8, "vg06-06": 1.0, "vg07-02": 0.8,
    "vg05-05": 1.5, "vg06-04": 1.2, "vg07-05": 1.0, "vg08-03": 1.2,
    "vg09-02": 1.0, "vg09-04": 1.8, "vg09-05": 1.8, "vg09-06": 1.8,
    "vg09-07": 1.2, "vg10-09": 0.8, "vg11-01": 2.0, "vg11-02": 1.8, "vg11-03": 2.2,
}


def read_wav(path: Path) -> array.array:
    with wave.open(str(path)) as w:
        assert w.getframerate() == RATE and w.getnchannels() == 1 and w.getsampwidth() == 2, path
        return array.array("h", w.readframes(w.getnframes()))


def trim(clip: array.array) -> array.array:
    hop = RATE // 50
    energy = [sum(v * v for v in clip[i:i + hop]) / hop for i in range(0, len(clip) - hop + 1, hop)]
    floor = max(energy) * 10 ** (-TRIM_DB / 10)
    voiced = [i for i, e in enumerate(energy) if e > floor]
    if not voiced:
        return clip
    start = max(0, voiced[0] * hop - round(PAD_LEAD * RATE))
    end = min(len(clip), (voiced[-1] + 1) * hop + round(PAD_TAIL * RATE))
    out = clip[start:end]
    n = min(round(TRIM_FADE * RATE), len(out) // 2)
    for i in range(n):
        out[i] = int(out[i] * i / n)
        out[-1 - i] = int(out[-1 - i] * i / n)
    return out


def srt_time(t: float) -> str:
    ms = round(t * 1000)
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def main() -> None:
    cues = json.loads(SCRIPT.read_text())["cues"]
    if "--estimate" in sys.argv:
        # Layout work before narration exists: silent clips of a guessed length.
        guess = {"zh": lambda c: len(c["zh"]) / 4.2, "en": lambda c: len(c["en"].split()) / 2.5}
        samples = {lang: {c["id"]: array.array("h", bytes(2 * round(guess[lang](c) * RATE))) for c in cues} for lang in VOICES}
    else:
        raw = {lang: {c["id"]: read_wav(d / f"{c['id']}.wav") for c in cues} for lang, d in VOICES.items()}
        samples = {lang: {cid: trim(clip) for cid, clip in clips.items()} for lang, clips in raw.items()}
        for lang in VOICES:
            cut = sum(len(raw[lang][k]) - len(samples[lang][k]) for k in raw[lang]) / RATE
            print(f"{lang}: trimmed {cut:.1f}s of room tone")

    t = LEAD_IN
    timeline = []
    for i, c in enumerate(cues):
        dur = {lang: len(samples[lang][c["id"]]) / RATE for lang in VOICES}
        speech = max(dur.values())
        last_in_section = i + 1 == len(cues) or cues[i + 1]["section"] != c["section"]
        slot = ONSET + speech + GAP + HOLD.get(c["id"], 0) + (SECTION_GAP if last_in_section else 0)
        timeline.append({
            "id": c["id"], "section": c["section"], "zh": c["zh"], "en": c["en"],
            "start": round(t, 3), "end": round(t + slot, 3),
            "speech": {lang: {"start": round(t + ONSET, 3), "end": round(t + ONSET + d, 3)} for lang, d in dur.items()},
        })
        t += slot
    total = t + END_CARD

    audio_dir = ROOT / "public/vg-why-paint-them/audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    for lang in VOICES:
        track = array.array("h", bytes(2 * round(total * RATE)))
        for cue in timeline:
            at = round(cue["speech"][lang]["start"] * RATE)
            clip = samples[lang][cue["id"]]
            track[at:at + len(clip)] = clip
        with wave.open(str(audio_dir / f"{lang}.wav"), "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(RATE)
            w.writeframes(track.tobytes())

    out = ROOT / "out/vg-why-paint-them"
    out.mkdir(parents=True, exist_ok=True)

    def write_srt(name: str, text, lang: str | None) -> None:
        blocks = []
        for n, cue in enumerate(timeline, 1):
            # A caption stays up from the first word until just before the next cue.
            start = cue["speech"][lang]["start"] if lang else cue["start"] + ONSET
            end = cue["end"] - 0.1
            blocks.append(f"{n}\n{srt_time(start)} --> {srt_time(end)}\n{text(cue)}\n")
        (out / name).write_text("\n".join(blocks), encoding="utf-8")

    write_srt("zh-Hans.srt", lambda c: c["zh"], "zh")
    write_srt("en.srt", lambda c: c["en"], "en")

    data = {"fps": FPS, "durationSeconds": round(total, 3), "endCardStart": round(t, 3), "cues": timeline}
    (ROOT / "src/data/vg-why-paint-them.json").write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n")
    print(f"{len(timeline)} cues, {total:.1f}s ({total/60:.1f} min)")
    for lang in VOICES:
        print(lang, f"speech {sum(len(v) for v in samples[lang].values())/RATE:.1f}s")


if __name__ == "__main__":
    main()
