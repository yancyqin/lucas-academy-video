"""Lay out a 中英阅读 film: the intro, then work by work its title and author and every verse, each in Chinese and
then in English, the owner's closing lines, and on the end card the series' last line (subscribe, leave a comment).

    python3 scripts/zhong-ying/build_timeline.py climb-higher

Reads DATA/<film>/align.json (align.py) and writes, into public/zhong-ying/<film>/ (git-ignored: it carries the
NIV text):
  timeline.json   what the film shows when: cues with their words' times, works, chapters, every reveal region's
                  and living stroke's start (film seconds)
  narration.wav   the voices on the film's clock, levelled to −16 LUFS (there is no music)
"""
from __future__ import annotations

import json
import re
import subprocess
import sys

import numpy as np

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
from films import DATA, FILMS, FPS, PUBLIC, intro_words, texts  # noqa: E402
from paintings import LIVING, REGIONS, find_word  # noqa: E402

SR = 48000
PRE, POST = 0.08, 0.12           # kept around each line's sound (sound_span)
INTRO_AT = 1.6                   # the title card settles first
INTRO_GAP = 0.8                  # between the intro's Chinese and English
AFTER_INTRO = 1.4
TITLE_AT = 0.6                   # a work's title shows, then it is read (with its author) over the blank paper
TITLE_GAP = 1.0                  # the title's English, then the first verse
ZH_EN_GAP = 0.7                  # a verse's Chinese, then its English
VERSE_GAP = 1.1                  # one verse to the next
HOLD = 3.2                       # after a work's last verse: watch it alive
LIVING_TAIL = 1.4                # with a MiniMax clip: alive this long, then it dissolves into the clip (minimax_prep.py)
CLOSING_AT = 0.8                 # after the last work: its closing lines, over its finished picture
CLOSING_HOLD = 2.5
RECAP_FADE = 1.0                 # one MiniMax clip dissolving into the next in the look back (paint.py)
SUBSCRIBE_AT = 1.2               # on the end card, once it has come up: the series' last line (films.SUBSCRIBE)
END_CARD = 4.5                   # after it, the card alone (YouTube's end-screen elements need ≥ 5 s of card)


LINE_LUFS = -20.0                # every line levelled to this before mixing (takes differ by a few dB)


def load(path) -> np.ndarray:
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    meter = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(path), "-af", "ebur128", "-f", "null", "-"],
                           capture_output=True, text=True).stderr
    lufs = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", meter)[-1])
    return np.frombuffer(raw, np.float32) * 10 ** ((LINE_LUFS - lufs) / 20)


def sound_span(audio: np.ndarray, a: float, b: float) -> tuple[float, float]:
    """Where to cut a line: out from the aligned speech [a, b] to where the voice has really gone quiet (the aligner
    can put a first word's start after its first sound, and a cut inside a sound clicks), plus PRE / POST."""
    hop = SR // 100
    env = np.sqrt(np.convolve(audio ** 2, np.ones(hop) / hop, "same")[::hop] + 1e-12)
    # Quiet: 42 dB under the line's loudest moment, or within 6 dB of the take's own floor (Fangfang's zero-shot
    # takes carry a faint hiss just above −42 dB, so the cut used to walk back through a second of it).
    quiet = env < max(env.max() * 10 ** (-42 / 20), np.percentile(env, 10) * 2)
    i, j = int(a * 100), min(len(env) - 1, int(b * 100))
    while i > 0 and not quiet[max(0, i - 8):i].all():      # back until 80 ms of quiet
        i -= 1
    while j < len(env) - 1 and not quiet[j:j + 15].all():  # on until 150 ms of quiet
        j += 1
    return max(0.0, i / 100 - PRE), min(len(audio) / SR, j / 100 + POST)


def fade(audio: np.ndarray, fade_in: float = 0.02, fade_out: float = 0.06) -> np.ndarray:
    """Raised-cosine fades so no cut can click."""
    n_in, n_out = (min(int(d * SR), len(audio) // 2) for d in (fade_in, fade_out))
    audio[:n_in] *= 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, n_in))
    audio[len(audio) - n_out:] *= 0.5 + 0.5 * np.cos(np.linspace(0, np.pi, n_out))
    return audio


def strays(audio: np.ndarray) -> list[str]:
    """A short sound standing alone at a line's head or tail (a click, a breath, a burst the model made — 小船去远方
    1:03 in the third cut): reported, so a cut that keeps one is seen before the film is rendered."""
    hop = SR // 100
    env = np.sqrt(np.convolve(audio ** 2, np.ones(hop) / hop, "same")[::hop] + 1e-12)
    loud = np.flatnonzero(env > env.max() * 10 ** (-30 / 20))
    gaps = np.flatnonzero(np.diff(loud) > 20)          # quiet stretches longer than 200 ms split the sounds
    starts, ends = np.r_[loud[0], loud[gaps + 1]], np.r_[loud[gaps], loud[-1]]
    out = []
    if len(starts) > 1 and ends[0] - starts[0] < 30 and starts[1] - ends[0] >= 30:
        out.append(f"head, {starts[0] / 100:.2f} s")
    if len(starts) > 1 and ends[-1] - starts[-1] < 30 and starts[-1] - ends[-2] >= 30:
        out.append(f"tail, {starts[-1] / 100:.2f} s")
    return out


def speech_span(words: list[dict]) -> tuple[float, float]:
    timed = [w for w in words if w["start"] is not None]
    return timed[0]["start"], timed[-1]["end"]


def main(film: str):
    spec = FILMS[film]
    align = json.loads((DATA / film / "align.json").read_text())
    units = {u["n"]: u for u in texts(film)}
    out_dir = PUBLIC / film
    out_dir.mkdir(parents=True, exist_ok=True)

    cues, placed = [], []                         # placed: (film start, samples)
    t = INTRO_AT

    def place(kind, lang, wav, words, work=None, unit=None):
        nonlocal t
        a, b = speech_span(words)
        audio = load(wav)
        a0, b0 = sound_span(audio, a, b)
        audio = fade(audio[int(a0 * SR):int(b0 * SR)].copy())
        for where in strays(audio):
            print(f"!! {film} {kind} {lang} work {work} unit {unit}: a stray sound at the {where}")
        start = t
        shift = start - a0
        cue = {"kind": kind, "lang": lang, "work": work, "unit": unit, "start": round(start, 3),
               "end": round(start + len(audio) / SR, 3), "speech": [round(a + shift, 3), round(b + shift, 3)],
               "words": [{"text": w["text"], "start": None if w["start"] is None else round(w["start"] + shift, 3),
                          "end": None if w["end"] is None else round(w["end"] + shift, 3)} for w in words]}
        cues.append(cue)
        placed.append((start, audio))
        t = cue["end"]
        return cue

    for lang in ("zh", "en"):
        words = align["intro"][lang]
        assert [w["text"] for w in words] == intro_words(lang), "align.json's intro is out of date"
        place("intro", lang, DATA / "narration" / f"intro-{lang}.wav", words)
        t += INTRO_GAP if lang == "zh" else AFTER_INTRO

    works, chapters = [], [{"zh": "开始", "en": "Start", "start": 0.0}]
    for wi, work in enumerate(spec["works"]):
        w_start = t
        t += TITLE_AT
        for lang in ("zh", "en"):
            place("title", lang, DATA / film / "audio" / f"{lang}-{work['id']}-title.wav",
                  align["titles"][work["id"]][lang], wi)
            t += ZH_EN_GAP if lang == "zh" else TITLE_GAP
        verse_cues = []
        clip = PUBLIC / film / f"minimax-{work['id']}.json"
        minimax = json.loads(clip.read_text()) if clip.exists() else None
        for k, n in enumerate(work["units"]):
            for lang in ("zh", "en"):
                cue = place("verse", lang, DATA / film / "audio" / f"{lang}-v{n:02d}.wav", align[str(n)][lang], wi, n)
                verse_cues.append(cue)
                last = k == len(work["units"]) - 1 and lang == "en"
                t += ZH_EN_GAP if lang == "zh" else (VERSE_GAP if not last else 0)
        if minimax:     # painted → alive → moving: the clip plays out after the last verse
            minimax = {"from": round(t + LIVING_TAIL, 3), "seconds": minimax["seconds"], "file": clip.with_suffix(".mp4").name}
            t = minimax["from"] + minimax["seconds"] + 0.4
        else:
            t += HOLD
        cue_of = {(c["unit"], c["lang"]): c for c in verse_cues}

        # The Chinese words paint the regions in; each region runs until the next one in its verse starts.
        regions = []
        for spec_r in REGIONS[work["id"]]:
            cue = cue_of[(spec_r["unit"], "zh")]
            regions.append({**spec_r, "start": find_word(cue["words"], spec_r["at"])["start"]})
        for n in work["units"]:
            mine = sorted((r for r in regions if r["unit"] == n), key=lambda r: r["start"])
            for i, r in enumerate(mine):
                end = mine[i + 1]["start"] if i + 1 < len(mine) else cue_of[(n, "zh")]["speech"][1] + 0.35
                r["end"] = max(end, r["start"] + (1.3 if r["r"] < 6 else 0.8))   # small details need time too
        living = []
        for entry in LIVING[work["id"]]:
            cue = cue_of[(entry["unit"], "en")]
            living.append({**entry, "start": find_word(cue["words"], entry["at"])["start"]})

        works.append({**work, "start": round(w_start, 3), "end": round(t, 3), "minimax": minimax,
                      "paint_from": cue_of[(work["units"][0], "zh")]["start"],
                      "living_from": cue_of[(work["units"][0], "en")]["start"],
                      "regions": regions, "living": living})
        chapters.append({"zh": work["title"]["zh"], "en": work["title"]["en"], "start": round(w_start, 3)})
    # The owner's closing lines. When the works have MiniMax clips, they are read over a look back (回顾): every work
    # plays once more, in order, each in its own share of the time, holding its last frame until it dissolves into
    # the next (owner, 2026-10-27) — its MiniMax clip from the start or, for a work without one, the end of its own
    # panel, alive (Where Go the Boats: MiniMax failed it three times; owner, 2026-10-28: 「就这样就可以」). A film
    # with no clips at all reads them over the last work's finished picture.
    recap = None
    if any(w["minimax"] for w in works):
        recap = {"start": round(t, 3)}
        chapters.append({"zh": "回顾", "en": "Looking back", "start": round(t, 3)})
    t += CLOSING_AT
    for lang in ("zh", "en"):
        place("closing", lang, DATA / film / "audio" / f"{lang}-{film}-closing.wav", align["closing"][lang],
              None if recap else len(works) - 1)
        t += ZH_EN_GAP if lang == "zh" else CLOSING_HOLD
    if recap:
        share = (t - recap["start"]) / len(works)
        recap.update(end=round(t, 3), fade=RECAP_FADE, clips=[
            {"work": w["id"], "from": round(recap["start"] + i * share, 3),
             **({"file": w["minimax"]["file"], "skip": 0} if w["minimax"] else
                {"file": f"paint-{w['id']}.mp4", "skip": round(max(0.0, w["end"] - w["start"] - share - RECAP_FADE), 3)})}
            for i, w in enumerate(works)])
    else:
        works[-1]["end"] = round(t, 3)
    end_card = t
    t += SUBSCRIBE_AT
    for lang in ("zh", "en"):
        place("subscribe", lang, DATA / film / "audio" / f"{lang}-subscribe.wav", align["subscribe"][lang])
        t += ZH_EN_GAP if lang == "zh" else 0
    duration = round(t + END_CARD, 3)
    if chapters[1]["start"] < 10:                      # YouTube wants every chapter ≥ 10 s: fold a short
        chapters.pop(0)                                # intro into the first work's chapter, from 0:00
        chapters[0]["start"] = 0.0
    for i, ch in enumerate(chapters):
        ch["end"] = chapters[i + 1]["start"] if i + 1 < len(chapters) else duration

    mix = np.zeros(int(duration * SR) + SR, np.float32)
    for start, audio in placed:
        i = int(round(start * SR))
        mix[i:i + len(audio)] += audio
    raw = out_dir / "narration-raw.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", str(raw)],
                   input=mix.tobytes(), check=True)
    level(raw, out_dir / "narration.wav")

    timeline = {"film": film, "fps": FPS, "durationSeconds": duration, "endCardStart": round(end_card, 3),
                "title": spec["title"], "cues": cues, "works": works, "recap": recap, "chapters": chapters}
    (out_dir / "timeline.json").write_text(json.dumps(timeline, ensure_ascii=False, indent=1))
    print(f"{film}: {duration:.1f} s, {len(cues)} cues, chapters " +
          ", ".join(f"{c['zh']} {c['start']:.1f}" for c in chapters))


def level(src, dst, target=-16.0):
    """Two-pass loudnorm to −16 LUFS, −3 dBTP (the channel's delivery level)."""
    probe = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(src), "-af", f"loudnorm=I={target}:TP=-3:LRA=11:print_format=json",
                            "-f", "null", "-"], capture_output=True, text=True).stderr
    m = json.loads(probe[probe.rindex("{"):probe.rindex("}") + 1])
    af = (f"loudnorm=I={target}:TP=-3:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
          f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-af", af, "-ar", str(SR), "-ac", "2", str(dst)], check=True)


if __name__ == "__main__":
    for name in sys.argv[1:]:
        main(name)
