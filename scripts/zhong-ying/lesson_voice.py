"""Voice a 语言的桥 lesson in Sunny's Chinese and Matthew's English (owner, 2026-10-28: 「现在声音可以了」 — Sunny for
the poems and scripture, Matthew for Shakespeare), as WAVs for lang's publish-audio.mjs.

    lucas-academy-media/.conda/bin/python scripts/zhong-ying/lesson_voice.py <scripts dir> <lesson> zh|en [--takes 3]
        [--only v06-whole,…]      more takes of just these lines (the takes already made stay in the running)

<scripts dir>/<lesson>-<lang>.json comes from lang's narration-scripts.mjs ({lines: [{id, verseId, text, hash}]};
it holds the fetched NIV, so it lives outside every repository). Writes <scripts dir>/<lang>/<id>.wav (16-bit PCM)
and <scripts dir>/<lang>/takes.json (every take, what Whisper heard, the pick).

The voices are made the way the owner approved (emotion_lab.py `sunny`): each copies its speaker's own expressive
reading of the same kind of text, and is never faster than that reading ("朗读速度不要太快").
  zh  Sunny — prompt: her 登鹳雀楼 (poems) or her 诗篇 121 (scripture), from her voice samples (sunny_voice.py).
      Takes she already made and the owner heard are reused: REUSE (a whole poem is cut into its couplets at the
      pauses between them).
  en  Matthew — prompt: his own reading of Foreign Lands, stanza 1 (matthew_voice.py, the version the owner chose).
Each line gets --takes takes; Whisper (by sound: toneless pinyin / letters) must hear it right, then the take with
the most pitch movement wins (if no take is heard right, the one heard best: a wrong word beats a lively one).
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from emotion_lab import ASSISTANT, pitch_stats, say  # noqa: E402
from films import DATA, MEDIA  # noqa: E402
from narration import heard_right, syllables  # noqa: E402

SUNNY_RAW = DATA / "narration" / "sunny" / "zh-raw"
SUNNY_TAKES = DATA / "narration" / "emotion-lab" / "sunny"
MATTHEW = DATA / "narration" / "matthew"
PROMPTS = {
    "zh-poem": ([SUNNY_RAW / "climb-higher-v01.wav", SUNNY_RAW / "climb-higher-v02.wav"],
                "白日依山尽，黄河入海流。欲穷千里目，更上一层楼。", 1.9),
    "zh-scripture": ([SUNNY_RAW / "climb-higher-v07.wav", SUNNY_RAW / "climb-higher-v08.wav"],
                     "我要向山举目；我的帮助从何而来？我的帮助从造天地的耶和华而来。", 2.1),
    "en": ([MATTHEW / "en" / "climb-higher-v03.wav", MATTHEW / "en" / "climb-higher-v04.wav"],
           "Up into the cherry tree, Who should climb but little me? I held the trunk with both my hands, And looked abroad in foreign lands.",
           None),
}
# Takes the owner already heard (emotion_lab.py sunny, 2026-10-28): lesson → line ids → (take, its text).
REUSE = {
    "can-beauty-last": {
        ("v01-whole", "v02-whole", "v03-whole", "v04-whole"): SUNNY_TAKES / "chunye-2.wav",
        ("v12-whole",): SUNNY_TAKES / "chuandao-13.wav",
    },
}


def ff(*args):
    subprocess.run(["ffmpeg", "-v", "error", "-y", *map(str, args)], check=True)


def rate(path, text, lang):
    """Syllables per second over the whole reading, pauses included."""
    import numpy as np
    import soundfile as sf

    x, r = sf.read(str(path))
    env = np.convolve(np.abs(x), np.ones(r // 50) / (r // 50), "same")
    on = np.nonzero(env > 0.05 * env.max())[0]
    return syllables(text, lang) / ((on[-1] - on[0]) / r)


def rank(m, lang):
    """Whisper-clean takes first, the most animated of them; if none is clean, the one Whisper heard best."""
    clean = m["heard_right"] >= (0.94 if lang == "zh" else 0.97)
    return (clean, m["pitch_sd"], 0) if clean else (clean, m["heard_right"], m["pitch_sd"])


def split_at_pauses(wav, parts: int):
    """Cut a whole reading into `parts` equal-length pieces of text at the pauses nearest where they should fall."""
    import numpy as np
    import soundfile as sf

    x, r = sf.read(str(wav))
    hop = r // 100
    env = np.sqrt(np.convolve(x ** 2, np.ones(hop) / hop, "same")[::hop])
    loud = env > env.max() * 10 ** (-40 / 20)
    on = np.nonzero(loud)[0]
    first, last = on[0], on[-1]
    runs, i = [], first
    while i < last:                                   # quiet runs of 150 ms or more inside the reading
        if not loud[i]:
            j = i
            while j < last and not loud[j]:
                j += 1
            if j - i >= 15:
                runs.append((i, j))
            i = j
        i += 1
    cuts = []
    for k in range(1, parts):
        expected = first + (last - first) * k / parts
        near = [run for run in runs if abs((run[0] + run[1]) / 2 - expected) < (last - first) / parts / 2]
        if not near:
            raise SystemExit(f"{wav.name}: no pause near piece {k}")
        a, b = max(near, key=lambda run: (run[1] - run[0]) - abs((run[0] + run[1]) / 2 - expected) * 0.2)
        cuts.append((a + b) / 2 / 100)
    edges = [0.0, *cuts, len(x) / r]
    return [(edges[k], edges[k + 1]) for k in range(parts)]


def main():
    opts = {k: sys.argv[sys.argv.index(k) + 1] for k in ("--takes", "--only") if k in sys.argv}
    args = [a for a in sys.argv[1:] if not a.startswith("--") and a not in opts.values()]
    takes = int(opts.get("--takes", 3))
    only = set(opts["--only"].split(",")) if "--only" in opts else None     # retake just these lines, keep the rest
    scripts, lesson, lang = Path(args[0]), args[1], args[2]
    lines = json.loads((scripts / f"{lesson}-{lang}.json").read_text())["lines"]
    out = scripts / lang
    out.mkdir(parents=True, exist_ok=True)

    import torch
    import torchaudio
    import whisper

    sys.path.insert(0, str(MEDIA / "src"))
    from lucas_media.cosyvoice_engine import CosyVoiceEngine

    profile = "sunny/zh" if lang == "zh" else "louise/en"            # the engine needs a profile to load; the
    engine = CosyVoiceEngine(MEDIA / "profiles" / profile / "profile.json")   # voice itself comes from PROMPTS
    model, sr = engine.model, engine.model.sample_rate
    asr = whisper.load_model("medium")
    prompt_note = "以下是普通话的句子，使用简体中文。" if lang == "zh" else None

    def heard(path):
        return asr.transcribe(str(path), language=lang, initial_prompt=prompt_note)["text"]

    def pcm(src, dst, start=None, end=None):
        cut = ["-ss", f"{start:.3f}", "-to", f"{end:.3f}"] if start is not None else []
        ff(*cut, "-i", src, "-af", "afade=t=in:d=0.02,areverse,afade=t=in:d=0.05,areverse", "-ac", "1", "-c:a", "pcm_s16le", dst)

    record = json.loads((out / "takes.json").read_text()) if only and (out / "takes.json").exists() else {}
    done = {l["id"] for l in lines if only and l["id"] not in only}
    if lang == "zh" and not only:
        for ids, take in REUSE.get(lesson, {}).items():
            pieces = split_at_pauses(take, len(ids)) if len(ids) > 1 else [(None, None)]
            for lid, (a, b) in zip(ids, pieces):
                line = next(l for l in lines if l["id"] == lid)
                pcm(take, out / f"{lid}.wav", a, b)
                h = heard(out / f"{lid}.wav")
                record[lid] = {"reused": take.name, "from": a, "to": b, "heard": h,
                               "heard_right": round(heard_right(line["text"], h, lang), 3)}
                print(f"{lid}: reused {take.name} {'' if a is None else f'{a:.2f}–{b:.2f}s'} heard {record[lid]['heard_right']} {h}", flush=True)
                done.add(lid)

    for line in lines:
        if line["id"] in done:
            continue
        kind = "en" if lang == "en" else ("zh-scripture" if line["verseId"].endswith(".12") and lesson == "can-beauty-last" else "zh-poem")
        clips, ref_text, cap = PROMPTS[kind]
        ref = out / f"prompt-{kind}.wav"
        if not ref.exists():
            ff(*sum((["-i", c] for c in clips), []), "-filter_complex",
               "".join(f"[{i}]" for i in range(len(clips))) + f"concat=n={len(clips)}:v=0:a=1", "-ar", "24000", ref)
        target = rate(ref, ref_text, lang) if cap is None else min(cap, rate(ref, ref_text, lang))
        text = say(line["text"]) if lang == "zh" else line["text"].replace("’", "'")
        tried = record.get(line["id"], {}).get("takes", []) if only else []
        best = None
        for m in tried:                                      # a retake competes with the takes already made
            key = rank(m, lang)
            if best is None or key > best[0]:
                best = (key, out / m["take"], m)
        for k in range(len(tried), len(tried) + takes):
            raw, speed = out / f"{line['id']}.take{k + 1}.wav", 1.0
            for _ in range(3):                               # never faster than the speaker's own reading
                g = model.inference_zero_shot(text, ASSISTANT + ref_text, str(ref), stream=False, speed=speed)
                torchaudio.save(str(raw), torch.concat([c["tts_speech"] for c in g], dim=1), sr)
                pace = rate(raw, line["text"], lang)
                if pace <= target * 1.05 or speed <= 0.8:
                    break
                speed = max(0.8, round(speed * target / pace, 2))
            h = heard(raw)
            m = {"take": raw.name, "speed": speed, "pace": round(pace, 2), "target": round(target, 2), "heard": h,
                 "heard_right": round(heard_right(line["text"], h, lang), 3), **pitch_stats(raw)}
            tried.append(m)
            print(f"{line['id']} take {k + 1}: speed {speed} pace {m['pace']}/{m['target']} pitch sd {m['pitch_sd']} "
                  f"heard {m['heard_right']} {h}", flush=True)
            key = rank(m, lang)
            if best is None or key > best[0]:
                best = (key, raw, m)
        pcm(best[1], out / f"{line['id']}.wav")
        record[line["id"]] = {"pick": best[2]["take"], "clean": best[0][0], "takes": tried}
    (out / "takes.json").write_text(json.dumps(record, ensure_ascii=False, indent=1))
    flagged = [lid for lid, r in record.items() if r.get("clean") is False or r.get("heard_right", 1) < 0.94]
    print(f"{lang}: {len(record)} lines" + (f"; Whisper not sure about {', '.join(flagged)}" if flagged else ", all heard right"))


if __name__ == "__main__":
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    main()
