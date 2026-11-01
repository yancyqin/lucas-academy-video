"""Word timings for every clip of a 中英阅读 film: the text is known, so this is alignment, never transcription.

    .venv-align/bin/python scripts/zhong-ying/align.py climb-higher [little-boats ...]

Decodes each verse's voice (films.clip: the chosen take, narration.py) and the intro takes to 48 kHz WAV under DATA/<film>/audio/ — the film's
mix is built from these same files, so the timings and the sound can't drift apart — and force-aligns the
narrated text with stable-ts. Chinese comes back character by character and is regrouped into lang's own word
tokens (the words that light up on screen); English is matched word by word against the displayed text.
The works' titles and the film's closing lines (films.extra: the chosen takes, narration.py extras) are aligned
the same way; they have no lang tokens, so their Chinese lights up character by character.
Writes DATA/<film>/align.json: {"<unit>": {"zh": [{text, start, end}], "en": [...]}, "intro": {...},
"titles": {"<work id>": {...}}, "closing": {...}}.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
from films import DATA, FILMS, SUBSCRIBE, clip, extra, intro_spoken, intro_words, texts  # noqa: E402

PUNCT = re.compile(r"[\s，。、；：？！“”‘’「」《》（）—…,.;:?!\"'()\-–]+")


def decode(src, dst):
    dst.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-ac", "1", "-ar", "48000", str(dst)], check=True)
    return dst


def display_words(lang: str, unit: dict) -> list[str]:
    """What lights up on screen, in reading order ("\\n" marks a line break)."""
    if lang == "zh":
        return unit["tokens"]
    text = unit["en"] or unit["spoken_en"]
    out = []
    for i, line in enumerate(text.split("\n")):
        if i:
            out.append("\n")
        out += line.split()
    return out


def plain_words(text: str, lang: str) -> list[str]:
    """What lights up for a line without lang tokens: each 汉字 (punctuation as its own token, which gets no time),
    or each English word."""
    return re.findall(r"[一-鿿]|[^一-鿿]+", text) if lang == "zh" else text.split()


def char_times(result) -> list[tuple[str, float, float]]:
    """Every aligned letter or 汉字 with its time; a multi-character word shares its span evenly."""
    chars = []
    for w in result.all_words():
        letters = PUNCT.sub("", w.word)
        if not letters:
            continue
        step = (w.end - w.start) / len(letters)
        chars += [(c.lower(), w.start + k * step, w.start + (k + 1) * step) for k, c in enumerate(letters)]
    return chars


def timed(words: list[str], chars) -> list[dict]:
    """Give each displayed word the span of its own letters (punctuation and line breaks get no time)."""
    out, at = [], 0
    for word in words:
        letters = PUNCT.sub("", word).lower()
        if not letters:
            out.append({"text": word, "start": None, "end": None})
            continue
        span = chars[at:at + len(letters)]
        if len(span) < len(letters) or "".join(c for c, _, _ in span) != letters:
            got = "".join(c for c, _, _ in chars[at:at + len(letters)])
            raise SystemExit(f"alignment lost its place at {word!r} (got {got!r})")
        out.append({"text": word, "start": round(span[0][1], 3), "end": round(span[-1][2], 3)})
        at += len(letters)
    return out


def speech_onset(wav) -> float:
    """When the voice starts (energy), to correct the aligner's first word: it sometimes starts it at 0 over a
    leading silence, or late after a soft first syllable. A short sound standing alone before the voice is not the
    voice: little-boats-v03-b opens with a 0.15 s burst 0.45 s before its first word, and taking that for the onset
    put the burst into the film (小船去远方 1:03)."""
    import numpy as np

    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(wav), "-ac", "1", "-ar", "16000", "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    env = np.convolve(np.abs(np.frombuffer(raw, np.float32)), np.ones(160) / 160, "same")[::160]   # 10 ms
    loud = np.flatnonzero(env > 0.06 * env.max())
    gaps = np.flatnonzero(np.diff(loud) > 20)          # quiet stretches longer than 200 ms split the sounds
    starts, ends = np.r_[loud[0], loud[gaps + 1]], np.r_[loud[gaps], loud[-1]]
    k = 0
    while k + 1 < len(starts) and ends[k] - starts[k] < 30 and starts[k + 1] - ends[k] >= 30:
        k += 1                                         # under 0.3 s, then 0.3 s of quiet: skip it
    return float(starts[k] / 100)


def spread_runs(words: list[dict], wav) -> list[dict]:
    """The aligner sometimes gives a line's last few characters one and the same start (下次见 all at 8.3 s, though
    下 starts at 7.89): spread such a run over the voice, from the first sound after the word before it to the run's
    end, one equal share per character, so the light doesn't jump them all at once. For the titles and closing lines
    only: no painting waits on their words."""
    import numpy as np

    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(wav), "-ac", "1", "-ar", "16000", "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    env = np.convolve(np.abs(np.frombuffer(raw, np.float32)), np.ones(160) / 160, "same")[::160]   # 10 ms
    loud = env > 0.06 * env.max()
    said = [w for w in words if w["start"] is not None]
    i = 0
    while i < len(said):
        j = i
        while j + 1 < len(said) and said[j + 1]["start"] == said[i]["start"]:
            j += 1
        if j > i:
            after = said[i - 1]["end"] + 0.03 if i else 0.0
            on = np.flatnonzero(loud[int(after * 100):])
            a = min(after + on[0] / 100 if len(on) else said[i]["start"], said[i]["start"])
            b = max(w["end"] for w in said[i:j + 1])
            step = (b - a) / (j - i + 1)
            for k, w in enumerate(said[i:j + 1]):
                w["start"], w["end"] = round(a + k * step, 3), round(a + (k + 1) * step, 3)
        i = j + 1
    return words


def pull_back(words: list[dict], wav) -> list[dict]:
    """The aligner sometimes puts a line's word in the silence after it, squeezed against the next word ("his lines;
    God": lines at 8.06–8.16 s, though it is said at 7.08–7.38 and the quiet runs to 8.16): a word under 0.2 s that
    starts after a quiet stretch, while 0.25 s or more of voice no word covers runs on from the word before, goes back
    onto that voice (subscribe, 2.0 s → 1.5, as Whisper hears it).
    For the titles and closing lines only, like spread_runs."""
    import numpy as np

    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(wav), "-ac", "1", "-ar", "16000", "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    env = np.convolve(np.abs(np.frombuffer(raw, np.float32)), np.ones(160) / 160, "same")[::160]   # 10 ms
    loud = env > 0.06 * env.max()
    said = [w for w in words if w["start"] is not None]
    for before, w in zip(said, said[1:]):
        if w["end"] - w["start"] >= 0.2 or w["start"] - before["end"] < 0.3:
            continue
        frames = loud[int(before["end"] * 100):int(w["start"] * 100)]
        quiet = np.flatnonzero(np.convolve(~frames, np.ones(20), "valid") == 20)   # the first 200 ms of quiet
        voice = (quiet[0] if len(quiet) else len(frames)) / 100
        if voice >= 0.25:                              # not a word's own tail ("hearts." trails 0.16 s of its s)
            w["start"], w["end"] = before["end"], round(before["end"] + voice, 3)
    return words


def fix_first(words: list[dict], wav, lang: str) -> list[dict]:
    first = next(w for w in words if w["start"] is not None)
    onset = speech_onset(wav)
    early, late = first["start"] < onset - 0.1, first["start"] > onset + 0.12
    if (early or (late and lang == "zh")) and onset < first["end"] - 0.05:
        first["start"] = round(onset, 3)
    return words


def main():
    import stable_whisper

    model = stable_whisper.load_model("medium", device="cpu")
    for film in sys.argv[1:]:
        out = {}
        for unit in texts(film):
            out[str(unit["n"])] = {}
            for lang in ("zh", "en"):
                wav = decode(clip(film, unit["n"], lang), DATA / film / "audio" / f"{lang}-v{unit['n']:02d}.wav")
                result = model.align(str(wav), unit[f"spoken_{lang}"], language=lang)
                out[str(unit["n"])][lang] = fix_first(timed(display_words(lang, unit), char_times(result)), wav, lang)
                print(film, unit["n"], lang, " ".join(f"{w['text']}@{w['start']}" for w in out[str(unit["n"])][lang] if w["start"] is not None))
        out["intro"] = {}
        for lang in ("zh", "en"):
            wav = DATA / "narration" / f"intro-{lang}.wav"     # the chosen take (ZHONG-YING.md)
            if not wav.exists():
                print(f"!! no intro take {wav}: choose one first")
                continue
            result = model.align(str(wav), intro_spoken(lang), language=lang)
            out["intro"][lang] = fix_first(timed(intro_words(lang), char_times(result)), wav, lang)
        out["titles"] = {w["id"]: {} for w in FILMS[film]["works"]}
        lines = [(out["titles"][w["id"]], f"{w['id']}-title", w["say"]) for w in FILMS[film]["works"]]
        out["closing"] = {}
        lines.append((out["closing"], f"{film}-closing", FILMS[film]["closing"]))
        out["subscribe"] = {}
        lines.append((out["subscribe"], "subscribe", SUBSCRIBE))
        for into, line_id, say in lines:
            for lang in ("zh", "en"):
                wav = decode(extra(line_id, lang), DATA / film / "audio" / f"{lang}-{line_id}.wav")
                result = model.align(str(wav), say[lang], language=lang)
                into[lang] = pull_back(spread_runs(fix_first(timed(plain_words(say[lang], lang), char_times(result)), wav,
                                                             lang), wav), wav)
                print(film, line_id, lang, " ".join(f"{w['text']}@{w['start']}" for w in into[lang] if w["start"] is not None))
        (DATA / film / "align.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
