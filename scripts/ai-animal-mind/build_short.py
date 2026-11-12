"""Vertical shorts from 「动物想什么？AI 知道吗？」: one picture, an English and a Chinese voice track, for AiAnimalShort.

  /Users/yqin/repo/playground/lucas-academy-video/.venv-align/bin/python scripts/ai-animal-mind/build_short.py [ocean|animals ...]

Yancy 2026-11-11: 「出2个短视频吧，多用动物。一个用海洋动物，开场用G10；一个用其他动物」, then 「给英文视频配单独的中文音轨
就好了」: like the film, each short is one English video with a separate Chinese audio track. So the two languages share
one timeline: each line (shorts.json) gets the longer of its English and Chinese takes, a voice starts at its line's
start, the film's real animal recordings follow the same lines (the music fades right out under them), and the shots
hang on that shared timing. No captions are burned in (they would contradict the Chinese track); the English title
stays at the top, and each language gets its own SRT. The K. 265 bed ducks under every voice (music_ducking.py) and
lifts in the wordless animal montages.

Writes public/ai-animal-mind/shorts/<name>.json (the picture), out/ai-animal-mind/shorts/<name>.{en,zh}.wav and
<name>.{en,zh-Hans}.srt.
"""
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

NAMES = [a for a in sys.argv[1:] if not a.startswith("--")]
sys.argv = sys.argv[:1]
# the film's builder (takes, recordings, K. 265, captions), loaded under its own name: it imports the middle-income-trap
# build_timeline as `mit`, which a plain `import build_timeline` from this folder would shadow
_spec = importlib.util.spec_from_file_location("aam_build_timeline", Path(__file__).resolve().parent / "build_timeline.py")
bt = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bt)

mit, music_ducking, SR = bt.mit, bt.music_ducking, bt.SR
ROOT = bt.ROOT
SHORTS = json.loads((ROOT / "scripts/ai-animal-mind/shorts.json").read_text())["shorts"]
PUB, OUT = bt.PUB / "shorts", bt.OUT / "shorts"
GAP, QUESTION_GAP, END_HOLD, TAIL_BOOST_DB = 0.35, 0.6, 0.8, 5.0
LANGS = ("en", "zh")
TITLE = ["What Are Animals Thinking?", "Does AI Know?"]  # the English video's title


def bed(names: list, total: float) -> np.ndarray:
    src = mit.ffread(bt.K265_SOURCE)
    order = list(bt.K265)
    names = list(names)
    while sum(bt.K265[x][1] - bt.K265[x][0] for x in names) < total + 1:
        names.append(order[(order.index(names[-1]) + 1) % len(order)])
    y = np.concatenate([src[int(bt.K265[x][0] * SR):int(bt.K265[x][1] * SR)] for x in names])[: int(total * SR)].copy()
    y *= 10 ** ((mit.BED_LUFS - mit.lufs(y)) / 20)
    return y


def srt(lang: str, spans: list, cap: dict) -> str:
    """The film's caption splitting, timed to this language's own speech."""
    out, n = [], 0
    for lid, a, b in spans:
        text = cap[lid]
        if lang == "zh":
            parts = list(mit.srt_pieces(text, a, b))
        else:
            ps = bt.fi4captions.pieces(text)
            tot, x, parts = sum(len(p) for p in ps), a, []
            for p in ps:
                y = x + (b - a) * len(p) / tot
                parts.append((x, y, bt.fi4captions.two_lines(p)))
                x = y
        for x, y, piece in parts:
            n += 1
            out.append(f"{n}\n{mit.stamp(x)} --> {mit.stamp(y)}\n{piece}\n")
    return "\n".join(out)


def build(name: str) -> None:
    spec = SHORTS[name]
    question = {l["id"]: l["question"] for l in bt.direction()}
    film_sounds = bt.EDIT.get("sounds", [])
    voice = {lang: [] for lang in LANGS}
    t, sounds, shots, slots, tails, prev_q, pad = 0.25, [], [], [], [], False, {lang: 0.0 for lang in LANGS}
    for beat in spec["beats"]:
        if slots or sounds:
            t += QUESTION_GAP if prev_q else GAP
        start = t
        if "line" in beat:
            lid = beat["line"]
            takes = {lang: bt.take(lang, lid) for lang in LANGS}
            if any(y is None for y in takes.values()):
                raise SystemExit(f"a take for {lid} is missing")
            slot = max(len(y) / SR for y in takes.values())
            for lang, y in takes.items():
                voice[lang].append((t, y, lid))
                pad[lang] += slot - len(y) / SR
            a, b = t, t + slot
            slots.append((lid, a, b))
            end = b
            prev_q = question[lid]
        else:
            a = b = t
            end = t + beat["dur"]
            prev_q = False
        if beat.get("sounds"):
            u = b + bt.SND_LEAD if "line" in beat else t + beat.get("sound_at", 0.3)
            group = [e for e in film_sounds if e["after"] == beat["sounds"]]
            for e in group:
                y = bt.sound_clip(e)
                sounds.append((u, y, e))
                u += len(y) / SR + e.get("gap", bt.SND_BETWEEN)
            end = max(end, u - group[-1].get("gap", bt.SND_BETWEEN) + (bt.SND_TAIL if "line" in beat else 0.0))
        tail_from = end
        end += beat.get("tail", 0.0)
        for s in beat.get("shots", []):
            at = s["at"]
            when = b + float(at[1:]) if isinstance(at, str) else a + float(at) * (b - a)
            shots.append({"k": "clip", "clip": s["clip"], "in": s.get("in", 0.0), "start": round(when, 3)})
        ts = beat.get("tail_shots", [])
        if ts:
            span_a = tail_from if "line" in beat else start
            step = (end - span_a) / len(ts)
            shots += [{"k": "clip", "clip": c, "in": 0.0, "start": round(span_a + i * step, 3)} for i, c in enumerate(ts)]
            if "line" in beat or not beat.get("sounds"):
                tails.append((span_a, end))
        t = end
    total = round(t + END_HOLD, 3)

    # the picture: each shot runs to the next one; slow a short clip down rather than freeze it
    clips = json.loads((bt.PUB / "clips.json").read_text())
    shots.sort(key=lambda s: s["start"])
    shots[0]["start"] = 0.0  # a short opens on its picture, not on the 0.25 s lead before the first sound
    problems = []
    for i, s in enumerate(shots):
        s["end"] = shots[i + 1]["start"] if i + 1 < len(shots) else total
        c = clips.get(s["clip"])
        if c is None:
            problems.append(f"{s['clip']} not staged (run assets.py)")
            continue
        need = s["end"] - s["start"] + bt.FADE
        rate = min(1.0, (c["probe"]["duration"] - s["in"] - 0.1) / need)
        s["rate"] = round(max(rate, 0.3), 3)
        if rate < bt.min_rate(c["probe"]["fps"], s["clip"].startswith("muse-")):
            problems.append(f"{s['clip']} at {s['start']:.1f}s needs {need:.1f}s (rate {rate:.2f})")
    if problems:
        raise SystemExit("picture problems (fix shorts.json):\n  " + "\n  ".join(problems))
    PUB.mkdir(parents=True, exist_ok=True)
    tl = {"fps": 30, "durationSeconds": total, "lang": "en", "title": TITLE, "shots": shots, "captions": [],
          "sounds": [{"name": e.get("name", e["src"]), "start": round(a, 3)} for a, _, e in sounds]}
    (PUB / f"{name}.json").write_text(json.dumps(tl, ensure_ascii=False, indent=1))

    # one mix per language on that timeline: voices, recordings, and the music ducked under both (silent under a
    # recording), lifted in the montages
    music = bed(spec["music"], total)
    quiet = [(a, a + len(y) / SR) for a, y, e in sounds if not e.get("bed")]
    music_ducking.FADE_IN, music_ducking.FADE_OUT = 0.4, 2.0  # a short starts on its picture and ends crisply
    OUT.mkdir(parents=True, exist_ok=True)
    for lang in LANGS:
        n = int(total * SR) + SR
        mix_v = np.zeros(n, np.float32)
        for a, y, _ in voice[lang] + sounds:
            k = int(a * SR)
            mix_v[k:k + len(y)] += y[: n - k]
        mix_v = mix_v[: int(total * SR)]
        cues = [{"speech": {"start": a, "end": a + len(y) / SR}} for a, y, _ in voice[lang] + sounds]
        env_path = OUT / f"env.{name}.{lang}.wav"
        music_ducking.envelope(cues, total, mit.BED_LUFS, env_path, quiet=quiet)
        env = mit.ffread(env_path)
        tt = np.arange(len(env)) / SR
        for lo, hi in tails:
            env *= 10 ** (TAIL_BOOST_DB * np.clip(np.minimum((tt - lo) / 0.6, (hi - tt) / 0.6), 0, 1) / 20)
        m = min(len(env), len(music), len(mix_v))
        mix = mix_v[:m] + music[:m] * env[:m]
        mix *= 10 ** ((mit.FINAL_LUFS - mit.lufs(mix)) / 20)
        raw = OUT / f"{name}.{lang}.raw.wav"
        sf.write(raw, mix, SR, subtype="FLOAT")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(raw), "-af",
                        f"alimiter=limit={10 ** (mit.FINAL_TP / 20):.4f}:attack=5:release=60:level=false",
                        "-c:a", "pcm_s24le", str(OUT / f"{name}.{lang}.wav")], check=True)
        raw.unlink()
        spans = [(lid, a, a + len(y) / SR) for a, y, lid in voice[lang]]
        (OUT / f"{name}.{'zh-Hans' if lang == 'zh' else 'en'}.srt").write_text(srt(lang, spans, bt.captions(lang)))
    print(f"{name}: {total:.1f} s, {len(slots)} lines, {len(sounds)} recordings, {len(shots)} shots; "
          f"waiting for the other language: en {pad['en']:.1f} s, zh {pad['zh']:.1f} s")


if __name__ == "__main__":
    for nm in NAMES or list(SHORTS):
        build(nm)
