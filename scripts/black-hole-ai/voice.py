"""Louise narration takes for 「We Build A BlackHole with AI」 (docs/black-hole-ai/{en,zh}-edit.md, 21 lines each).

The owner-confirmed Louise path (lucas-academy-media AGENTS.md and docs/PRODUCTION-CHECKLIST.md, 2026-11-24):
  zh  direct local Qwen3-TTS-12Hz-1.7B-Base-8bit ICL clone of profiles/louise/zh (.venv-tts-comparison), no CosyVoice
      conversion afterwards. The Base model has no instruction input (mlx_audio ignores `instruct` on the ICL path),
      so the Chinese delivery comes from the reference recording and the text, not from a per-section direction.
  en  direct local CosyVoice3 with profiles/louise/en (.conda), zero-shot-instruct as scripts/voice_defaults.py
      ("louise/en"), with this film's own one-sentence direction per section.
  Natural speed 1.0, no cloud TTS, no splicing, no padding, no trimming: a take is what the model produced (only a
  whole-take gain when its peak is over 0.88).

Every try is kept as audio/<lang>/takes/<id>.take<N>.wav (+ .json with its exact settings); `manifest` byte-copies the
chosen take to audio/<lang>/<id>.wav and writes audio/manifest.json. A take is never overwritten: its file is keyed
by spoken text, model, mode, direction, seed, temperature and the profile + reference hashes.

    W=/Users/yqin/repo/playground/lucas-academy-video/.claude/worktrees/black-hole-ai-film
    M=/Users/yqin/repo/playground/lucas-academy-media
    cd $W
    # 1. voice, one heavy process at a time
    HF_HUB_OFFLINE=1 $M/.venv-tts-comparison/bin/python -B scripts/black-hole-ai/voice.py synth zh --take 1
    HF_HUB_OFFLINE=1 $M/.conda/bin/python -B scripts/black-hole-ai/voice.py synth en --take 1
    # 2. listen: Whisper medium + small through scripts/qa/narration.py's own rules (and the pitfalls list)
    /Users/yqin/repo/playground/lucas-academy-video/.venv-align/bin/python -B scripts/black-hole-ai/voice.py check
    # 3. a retake is the next take number = the next seed, same text and settings (up to 3 per wording; a line
    #    reworded in the edit file continues the numbering, 4-6 then 7-9, so no earlier try is ever overwritten)
    HF_HUB_OFFLINE=1 $M/.venv-tts-comparison/bin/python -B scripts/black-hole-ai/voice.py synth zh --take 2 --only bh02-05
    # 4. choose (CHOICES below records every hand decision) and write the manifest
    python3 -B scripts/black-hole-ai/voice.py manifest
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EDIT = ROOT / "docs/black-hole-ai"
PITFALLS = json.loads((ROOT / "scripts/qa/pitfalls.json").read_text(encoding="utf-8"))


def beside(name: str) -> Path:
    """lucas-academy-media / lucas-academy-video-data sit beside the main checkout; from a worktree, further up."""
    for parent in ROOT.parents:
        if (parent / name).is_dir():
            return parent / name
    raise SystemExit(f"{name} not found beside {ROOT}")


MEDIA = beside("lucas-academy-media")
DATA = beside("lucas-academy-video-data") / "black-hole-ai-20261126/v01"
AUDIO = DATA / "audio"
CHECKS = DATA / "checks"
QWEN_BASE = MEDIA / "models/Qwen3-TTS-12Hz-1.7B-Base-8bit"
COSYVOICE = MEDIA / "models/Fun-CosyVoice3-0.5B"
LANGS = ("zh", "en")

# Spoken forms the edit files' headers do not list. English years are written as digits in the script; the
# pitfalls lint (scripts/qa/pitfalls.json) wants words in the spoken text, and natural English reads them as
# "twenty fifteen" (PRODUCTION-CHECKLIST: 英文年份遵循自然英语读法). Captions keep the digits.
EXTRA_SPOKEN = {
    "en": {"bh01-03": [("2015", "twenty fifteen")], "bh01-04": [("2024", "twenty twenty-four")]},
    "zh": {},
}

# English direction per section (CosyVoice zero-shot-instruct keeps the reference's own rhythm and timbre).
EN_DIRECTION = {
    "BH00": "Please speak in a lively, confident voice, like opening an exciting story for a curious child.",
    "BH01": "Please speak in a clear, friendly and curious voice, like explaining something wonderful to a ten-year-old.",
    "BH02": "Please speak in a clear, friendly and curious voice, like explaining something wonderful to a ten-year-old.",
    "BH03": "Please speak in a calm, softly awed and unhurried voice, like watching something amazing together.",
    "BH04": "Please speak in a warm, friendly and encouraging voice, like inviting a child to try it.",
}
EN_MODE = {s: "zero-shot-instruct" for s in EN_DIRECTION}
ZH_TEMPERATURE = 0.55          # memory-combined v09 (owner-approved direct Qwen Base Louise)
ZH_MAX_TOKENS = 2048

# Names Whisper spells its own way: a difference there is a listening question, never a fail on its own.
NAMES = {
    "en": ["Einstein's", "NASA's", "Goddard", "Kip Thorne", "Interstellar", "Kerr", "Sagittarius", "Teleport Orb",
           "The Manifold", "Black Hole Journey", "lucas academy"],
    "zh": ["爱因斯坦", "NASA", "戈达德", "基普·索恩", "星际穿越", "克尔", "人马座", "Manifold", "Black Hole Journey",
           "lucas academy"],
}
# Pace on the speech span (first to last sound). en: the brief's 2.2–3.2 words/s; zh: syllables/s (pace_units).
PACE = {"en": (2.2, 3.2), "zh": (3.0, 6.0)}

# Hand decisions after reading the ASR report (checks/asr.<lang>.json) and, for pause flags, re-transcribing each take
# cut at its own pauses: (lang, id) -> (take, reason). A reason starting "doubtful:" marks the line doubtful.
# Everything else takes the default rule (the first take that passes every automatic check).
CHOICES: dict[tuple[str, str], tuple[int, str]] = {
    ("zh", "bh00-02"): (1, "Both tries were flagged for a pause in 「来的」; cut at their pauses and re-heard, the pauses fall at "
                           "。 and ，(…做出来的。| 你也可以…博物馆里 | 自己绕着它飞。), not inside a word. Take 1 keeps the livelier hook pace."),
    ("zh", "bh01-02"): (1, "Only a name spelling (戈→哥, same syllable gē) and the risky 量: the second model wrote 涼 (liáng), the "
                           "right reading of 量 as 'measure'."),
    ("zh", "bh02-02"): (2, "The pause flag is the 0.85 s full stop after 物理 (re-heard in pieces: 然后，AI写出了物理。| 克尔…的形状 | "
                           "一个细心的逐步求解器 | 带着…); medium heard 克 here (科 in take 1). 度规 is written 杜圭 = same syllables."),
    ("zh", "bh02-04"): (3, "Take 3 has no sound outside the words; take 1 has a 10 ms tick after the last word, take 2 a 200 ms "
                           "sound after it."),
    ("zh", "bh02-06"): (4, "Reworded by the coordinator 2026-11-27 (光的频移 → 光的颜色偏移) because in all three takes of the "
                           "old wording (takes 1-3, kept as superseded) both Whisper models wrote 平移 (píng) for 频移 (pín). "
                           "Take 4, the first try of the new wording, passes every automatic check."),
    ("zh", "bh02-08"): (2, "Whole-line medium wrote 误差不到1% in all three takes while small heard 十亿分之一 in all three; cut at "
                           "its pauses, take 2's last piece is heard by medium as 十亿分之一 too (take 1's as '1%1亿'; take 3 "
                           "also has 算处 for 算出). Accepted by the coordinator 2026-11-27; goes to the owner's listening review."),
    ("zh", "bh03-04"): (6, "Reworded by the coordinator 2026-11-27 (边界：事件视界 → 那条边界，叫作事件视界): of the old wording's "
                           "takes 1-3 (superseded), two garbled 事件 and one broke the term. New wording: take 4 garbles 事件 "
                           "(世间世界, fail); take 5 has the right syllables but a 0.24 s pause after 这里; take 6 passes every "
                           "automatic check: medium hears the term's syllables (writes 事件世界; 视界 and 世界 are both shì jiè) "
                           "with no pause inside it, both on the whole line and cut at its pauses. The second model (small) "
                           "writes 世界世界 for takes 5 and 6: listen to 事件. The fallback wording (视界 alone) was not needed."),
    ("zh", "bh04-01"): (2, "The spelled-out URL makes the line long by nature. Take 2 pauses after 去 (0.57 s; take 1: 0.91 s), after "
                           "the URL (0.56 s) and at the full stop; take 3 adds a 0.59 s pause inside 房间|打开."),
    ("en", "bh02-02"): (3, "Takes 1 and 2 were both heard as 'The current metric'; take 3 is heard as 'The Kerr metric' but has "
                           "a 20 ms sound (-34 dB vs speech) at 0.15 s, 0.39 s before the first word. Accepted by the "
                           "coordinator 2026-11-27: the timeline builder trims the silence before the first word."),
    ("en", "bh02-04"): (3, "Take 3 is heard exactly as scripted ('Here is the picture') but has a 10 ms sound at -40 dB at "
                           "0.04 s, 0.68 s before the first word (take 2: no edge sound, heard as 'Here's the picture'; take 1: "
                           "a click before the first word). Accepted by the coordinator 2026-11-27: the timeline builder trims "
                           "the silence before the first word."),
    ("en", "bh03-01"): (3, "Take 1 was heard as 'close to the hull', take 2 as 'grabs our shit' and it ends abruptly; take 3 is "
                           "heard exactly as scripted."),
    ("en", "bh03-02"): (3, "All three tries are slow (1.63 / 1.69 / 1.82 words/s against 2.2-3.2; three short comma phrases "
                           "under the calm BH03 direction), words right in all. Take 3 is the quickest and both models hear it "
                           "exactly. Accepted by the coordinator 2026-11-27: the slow, calm delivery suits the fall."),
}

# What ASR cannot settle: listen for these in the chosen take.
LISTEN: dict[tuple[str, str], list[str]] = {
    ("zh", "bh00-01"): ["倒着 dào"],
    ("zh", "bh01-02"): ["量 liáng", "NASA"],
    ("zh", "bh01-03"): ["二零一五年 read digit by digit (Whisper writes 2015 either way; its span, 2015+年 = 0.86 s, fits five "
                        "syllables rather than seven)", "120 ms sound (-35 dB) after the last word"],
    ("zh", "bh01-04"): ["二零二四年 read digit by digit (2024+年 = 0.90 s, fits five syllables)", "NASA"],
    ("zh", "bh02-02"): ["度规 dù guī", "克尔 kè"],
    ("zh", "bh02-04"): ["调试 tiáo"],
    ("zh", "bh02-06"): ["朝 cháo", "冲 chōng"],
    ("zh", "bh02-08"): ["落 luò", "十亿分之一 (owner's listening review)"],
    ("zh", "bh03-03"): ["转 zhuàn"],
    ("zh", "bh03-04"): ["事件 shì jiàn (the second model writes 世界世界)"],
    ("zh", "bh03-05"): ["人马座 A 星"],
    ("zh", "bh04-01"): ["i s 点 lucas academy 点 org", "Manifold, Black Hole Journey"],
    ("en", "bh00-01"): ["140 ms breath-like sound (-29 dB) before the first word"],
    ("en", "bh01-02"): ["Goddard (the second model wrote 'Gutter')"],
    ("en", "bh01-03"): ["'twenty fifteen' (Whisper writes 2015 however the year is read)"],
    ("en", "bh01-04"): ["'twenty twenty-four' (Whisper writes 2024 however the year is read)"],
    ("en", "bh02-02"): ["Kerr", "20 ms sound (-34 dB) at 0.15 s, before the first word"],
    ("en", "bh02-04"): ["10 ms faint sound (-40 dB) at 0.04 s"],
    ("en", "bh03-02"): ["pace: slow for the brief"],
    ("en", "bh03-05"): ["Sagittarius A star"],
    ("en", "bh04-01"): ["is dot lucas academy dot org"],
}


# --------------------------------------------------------------------------------------------- the script

def sha(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def lint(lang: str, ident: str, spoken: str) -> list[str]:
    hits = []
    for rule in PITFALLS[lang]["avoid"]:
        if ("text" in rule and rule["text"] in spoken) or ("pattern" in rule and re.search(rule["pattern"], spoken, re.I)):
            hits.append(f"{lang} {ident}: {rule['why']}")
    if re.search(r"\*|\w\.\w", spoken):
        hits.append(f"{lang} {ident}: a symbol or URL left in the spoken text")
    return hits


def load(lang: str) -> list[dict]:
    text = (EDIT / f"{lang}-edit.md").read_text(encoding="utf-8")
    rules, rows, section = {}, [], None
    rule_re = re.compile(r'^- (bh\d\d-\d\d): "(.+?)" → "(.+?)"' if lang == "en" else r"^- (bh\d\d-\d\d)：「(.+?)」→「(.+?)」")
    for line in text.splitlines():
        if m := re.match(r"^## (BH\d\d)\b", line):
            section = m[1]
        elif section is None and (m := rule_re.match(line)):
            rules.setdefault(m[1], []).append((m[2], m[3]))
        elif m := re.match(r"^- (bh\d\d-\d\d) \| (.+)$", line):
            assert section and m[1].upper().startswith(section), (lang, m[1], section)
            rows.append({"id": m[1], "lang": lang, "section": section, "caption": m[2].strip()})
    assert len(rows) == 21 and len({r["id"] for r in rows}) == 21, (lang, len(rows))
    header_rules = sum(len(v) for v in rules.values())
    assert header_rules == {"en": 2, "zh": 4}[lang], (lang, rules)
    for ident, extra in EXTRA_SPOKEN[lang].items():
        rules.setdefault(ident, []).extend(extra)
    by_id = {r["id"]: r for r in rows}
    for r in rows:
        r["spoken"] = r["caption"]
        r["spoken_forms"] = []
    for ident, pairs in rules.items():
        r = by_id[ident]
        for written, said in pairs:
            assert r["spoken"].count(written) == 1, (lang, ident, written)
            r["spoken"] = r["spoken"].replace(written, said)
            r["spoken_forms"].append({"written": written, "spoken": said,
                                      "source": "edit header" if (written, said) not in EXTRA_SPOKEN[lang].get(ident, []) else "voice.py EXTRA_SPOKEN"})
    if lang == "zh":   # 「参考了 2015 年」→「参考了 二零一五年」: no space left between two Chinese characters
        for r in rows:
            r["spoken"] = re.sub(r"(?<=[一-鿿])\s+(?=[一-鿿])", "", r["spoken"])
    problems = [h for r in rows for h in lint(lang, r["id"], r["spoken"])]
    assert not problems, problems
    return rows


def both() -> dict[str, list[dict]]:
    out = {lang: load(lang) for lang in LANGS}
    assert [r["id"] for r in out["en"]] == [r["id"] for r in out["zh"]]
    return out


def seed_for(lang: str, ident: str, take: int) -> int:
    s, n = int(ident[2:4]), int(ident[5:7])
    return 1126_000_000 + (0 if lang == "zh" else 500_000) + s * 10_000 + n * 100 + take


def take_path(lang: str, ident: str, take: int) -> Path:
    return AUDIO / lang / "takes" / f"{ident}.take{take}.wav"


def config_for(row: dict, take: int) -> dict:
    lang = row["lang"]
    profile = MEDIA / f"profiles/louise/{lang}/profile.json"
    p = json.loads(profile.read_text())
    assert p["consent"], profile
    ref = profile.parent / p["reference_audio"]
    common = dict(id=row["id"], lang=lang, section=row["section"], caption=row["caption"], spoken=row["spoken"],
                  voice=f"louise/{lang}", profile=str(profile.relative_to(MEDIA)), profile_sha256=sha(profile),
                  reference_sha256=sha(ref), take=take, seed=seed_for(lang, row["id"], take), speed=1.0,
                  cloud_requests=0, voice_conversion=False)
    if lang == "zh":
        return dict(common, engine="direct local Qwen3-TTS Base ICL (mlx_audio)", model=QWEN_BASE.name,
                    mode="icl", instruction=None, lang_code="Chinese", temperature=ZH_TEMPERATURE,
                    max_tokens=ZH_MAX_TOKENS)
    mode = EN_MODE[row["section"]]
    return dict(common, engine="direct local CosyVoice3 (lucas_media.cosyvoice_engine)", model=COSYVOICE.name,
                mode=mode, instruction=EN_DIRECTION[row["section"]] if mode == "zero-shot-instruct" else None,
                temperature=None)


# ----------------------------------------------------------------------------------------------- voicing

def speech_span(a, sr: int) -> dict:
    """Where the sound is (10 ms frames within 35 dB of the loud frames), and how each end of the file sounds."""
    import numpy as np
    hop = int(sr * 0.01)
    n = len(a) // hop
    e = np.sqrt((a[: n * hop].astype(np.float64).reshape(n, hop) ** 2).mean(axis=1)) + 1e-9
    ref = float(np.percentile(e, 95))
    loud = np.flatnonzero(e > ref * 10 ** (-35 / 20))
    start, end = loud[0] * hop / sr, (loud[-1] + 1) * hop / sr
    db = lambda x: float(20 * np.log10(max(float(np.sqrt(np.mean(np.square(x, dtype=np.float64)))), 1e-9) / ref))
    w = int(sr * 0.03)
    return dict(speech_start=round(start, 3), speech_end=round(end, 3), speech_seconds=round(end - start, 3),
                lead_silence=round(start, 3), tail_silence=round(len(a) / sr - end, 3),
                first_30ms_db_vs_speech=round(db(a[:w]), 1), last_30ms_db_vs_speech=round(db(a[-w:]), 1))


def edge_sounds(a, sr: int) -> tuple[list[str], list[str]]:
    """An isolated sound before the first word or after the last one, apart from the speech by >= 0.15 s of silence
    (10 ms frames, -40 dB vs the loud frames). Up to 50 ms it is a tick/pop (flag: retake); longer is usually a
    breath (note: listen). Returns (flags, notes)."""
    import numpy as np
    hop = sr // 100
    n = len(a) // hop
    e = np.sqrt((a[: n * hop].astype(np.float64).reshape(n, hop) ** 2).mean(axis=1)) + 1e-9
    ref = np.percentile(e, 95)
    loud = 20 * np.log10(e / ref) > -40
    segs, k = [], 0
    while k < n:
        if loud[k]:
            j = k
            while j < n and loud[j]:
                j += 1
            segs.append((k, j))
            k = j
        else:
            k += 1
    flags, notes = [], []
    if len(segs) < 2:
        return flags, notes
    for where, s, apart in (("before the first word", segs[0], segs[1][0] - segs[0][1]),
                            ("after the last word", segs[-1], segs[-1][0] - segs[-2][1])):
        if s[1] - s[0] <= 20 and apart >= 15:
            peak = 20 * np.log10(e[s[0]:s[1]].max() / ref)
            text = f"{(s[1] - s[0]) * 10} ms sound {where} at {s[0] / 100:.2f} s ({peak:.0f} dB vs speech, {apart / 100:.2f} s apart)"
            (flags if s[1] - s[0] <= 5 else notes).append(text)
    return flags, notes


def pace_units(row: dict) -> int:
    if row["lang"] == "en":
        return len(re.findall(r"[A-Za-z0-9']+", row["spoken"].replace("-", " ")))
    # zh: syllables. A Chinese character is one; an English word counts its vowel groups (academy 3, Journey 2).
    latin = re.findall(r"[A-Za-z]+", row["spoken"])
    return len(re.findall(r"[一-鿿]", row["spoken"])) + sum(max(1, len(re.findall(r"[aeiou]+", w.lower()))) for w in latin)


def own_flags(row: dict, d: dict) -> list[str]:
    """What the audio itself says, before anyone listens: abrupt ends (a cut word Whisper would fill in), pace."""
    flags = []
    if d["last_30ms_db_vs_speech"] > -30 or d["tail_silence"] < 0.02:
        flags.append(f"ends abruptly (last 30 ms {d['last_30ms_db_vs_speech']} dB vs speech, {d['tail_silence']} s after the last sound)")
    if d["first_30ms_db_vs_speech"] > -30:
        flags.append(f"starts abruptly (first 30 ms {d['first_30ms_db_vs_speech']} dB vs speech)")
    lo, hi = PACE[row["lang"]]
    if not lo <= d["pace"] <= hi:
        flags.append(f"pace {d['pace']} {'words' if row['lang'] == 'en' else 'units'}/s outside {lo}-{hi}")
    return flags


class Voice:
    def __init__(self, lang: str):
        self.lang = lang
        self.engine = None

    def load(self):
        os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
        os.environ.setdefault("HF_HUB_OFFLINE", "1")
        profile = MEDIA / f"profiles/louise/{self.lang}/profile.json"
        self.profile = json.loads(profile.read_text())
        assert self.profile["consent"]
        self.ref = profile.parent / self.profile["reference_audio"]
        if self.lang == "zh":
            from mlx_audio.tts.utils import load_model
            self.engine = load_model(str(QWEN_BASE))
            return
        import torch
        from functools import wraps
        sys.path.insert(0, str(MEDIA / "src"))
        from lucas_media.cosyvoice_engine import CosyVoiceEngine
        torch.set_num_threads(4)
        torch.set_num_interop_threads(1)
        engine = CosyVoiceEngine(profile)
        if torch.backends.mps.is_available():     # the flow on the GPU, as memory-combined v09
            original = engine.model.model.flow.inference
            engine.model.model.flow.to("mps")

            @wraps(original)
            def mps_flow(**kwargs):
                mel, extra = original(**{k: v.to("mps") if isinstance(v, torch.Tensor) else v for k, v in kwargs.items()})
                return mel.cpu(), extra
            engine.model.model.flow.inference = mps_flow
        frontend = engine.model.frontend          # the reference's tokens/features once, not per line
        for key in ["_extract_speech_token", "_extract_speech_feat", "_extract_spk_embedding"]:
            method, cache = getattr(frontend, key), {}

            def cached(path, *args, _method=method, _cache=cache, **kwargs):
                if str(path) != str(engine.reference_audio):
                    return _method(path, *args, **kwargs)
                if "value" not in _cache:
                    _cache["value"] = _method(path, *args, **kwargs)
                return _cache["value"]
            setattr(frontend, key, cached)
        self.engine = engine

    def synth(self, config: dict):
        import numpy as np
        if self.engine is None:
            self.load()
        if self.lang == "zh":
            import mlx.core as mx
            mx.random.seed(config["seed"])
            chunks = list(self.engine.generate(text=config["spoken"], ref_audio=str(self.ref),
                                               ref_text=self.profile["reference_text"], lang_code="Chinese",
                                               temperature=config["temperature"], max_tokens=config["max_tokens"],
                                               stream=False))
            assert chunks, config["id"]
            a = np.concatenate([np.asarray(c.audio, dtype=np.float32).reshape(-1) for c in chunks])
            sr, tokens = chunks[0].sample_rate, sum(c.token_count for c in chunks)
            mx.clear_cache()
            return a, sr, tokens
        import torch
        torch.manual_seed(config["seed"])
        with torch.inference_mode():
            a, sr, mode = self.engine.synthesize(config["spoken"], target_language="en", mode=config["mode"],
                                                 speed=1.0, instruction=config["instruction"] or "")
        assert mode == config["mode"], (mode, config["mode"])
        return a.detach().cpu().numpy().reshape(-1).astype(np.float32), sr, None


def cmd_synth(lang: str, take: int, only: set[str]):
    import numpy as np
    import soundfile as sf
    rows = both()[lang]
    unknown = only - {r["id"] for r in rows}
    assert not unknown, unknown
    voice = Voice(lang)
    (AUDIO / lang / "takes").mkdir(parents=True, exist_ok=True)
    made = cached = 0
    for row in rows:
        if only and row["id"] not in only:
            continue
        p = take_path(lang, row["id"], take)
        meta = p.with_suffix(".json")
        config = config_for(row, take)
        if p.exists() or meta.exists():
            d = json.loads(meta.read_text())
            assert d["config"] == config, f"{p.name} exists with other settings; never overwrite a take (use a new take or version)"
            assert d["sha256"] == sha(p), f"{p.name} changed on disk"
            print("CACHED", lang, p.name, flush=True)
            cached += 1
            continue
        began = time.monotonic()
        a, sr, tokens = voice.synth(config)
        seconds = len(a) / sr
        assert len(a) and np.isfinite(a).all() and float(np.abs(a).max()) > 0.005, (row["id"], "empty or not finite")
        assert 0.5 < seconds < 45, (row["id"], seconds)
        gain = min(1.0, 0.88 / float(np.abs(a).max()))
        a = a * gain
        sf.write(p, a, sr, subtype="PCM_24")
        d = dict(config=config, sha256=sha(p), seconds=round(seconds, 3), sample_rate=sr, whole_take_gain=round(gain, 4),
                 token_count=tokens, elapsed_seconds=round(time.monotonic() - began, 1), **speech_span(a, sr))
        d["pace_units"] = pace_units(row)
        d["pace"] = round(d["pace_units"] / d["speech_seconds"], 2)
        d["flags"] = own_flags(row, d)
        meta.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n")
        made += 1
        print(f"TAKE {lang} {p.name} {d['seconds']:.2f}s speech {d['speech_seconds']:.2f}s pace {d['pace']} "
              f"in {d['elapsed_seconds']}s {'; '.join(d['flags'])}", flush=True)
    print(f"{lang} take {take}: {made} new, {cached} cached", flush=True)


# ----------------------------------------------------------------------------------------------- listening

def takes_of(lang: str) -> list[tuple[dict, Path, dict]]:
    out = []
    rows = {r["id"]: r for r in load(lang)}
    for meta in sorted((AUDIO / lang / "takes").glob("*.take*.json")):
        d = json.loads(meta.read_text())
        row = rows[d["config"]["id"]]
        if d["config"]["spoken"] != row["spoken"]:
            continue                      # a take of an older script line
        out.append((row, meta.with_suffix(".wav"), d))
    return out


def cmd_check():
    """Each language's takes laid end to end (1 s apart) and put through scripts/qa/narration.py's check, the same
    rules the film's final QA uses: Whisper medium, a second model (small) on numbers, negations and the pitfalls
    list, a verbatim pass for repeats (en), pauses, clicks, pace and level against the takes' own median."""
    import numpy as np
    sys.path.insert(0, str(ROOT / "scripts/qa"))
    import narration
    from common import decode_audio, worst
    CHECKS.mkdir(parents=True, exist_ok=True)
    listener = narration.Listener(CHECKS / "whisper-cache.json")
    for lang in LANGS:
        entries = takes_of(lang)
        if not entries:
            continue
        gap = np.zeros(narration.SR, np.float32)
        pieces, lines, t = [gap], [], len(gap) / narration.SR
        for row, wav, d in entries:
            a = decode_audio(wav, narration.SR)
            span = speech_span(a, narration.SR)
            line = {"id": f"{row['id']}.take{d['config']['take']}", "lang": lang, "text": row["spoken"],
                    "start": round(t + span["speech_start"], 3), "end": round(t + span["speech_end"], 3)}
            if row["caption"] != row["spoken"]:
                line["caption"] = row["caption"]
            lines.append(line)
            pieces += [a, gap]
            t += (len(a) + len(gap)) / narration.SR
        played = np.concatenate(pieces)
        spec = {"lines": lines, "names": NAMES[lang]}
        print(f"--- {lang}: {len(lines)} takes", flush=True)
        try:
            results, _ = narration.check(spec, played, played, listener, log=lambda s: print(s, flush=True))
        finally:
            listener.save()
        # Takes of an earlier wording are not listened to again; their last report stays (manifest: superseded).
        old = CHECKS / f"asr.{lang}.json"
        report = {k: v for k, v in (json.loads(old.read_text()) if old.exists() else {}).items()
                  if k not in {line["id"] for line in lines}}
        import soundfile as sf
        for (row, wav, d), r in zip(entries, results):
            edge_flags, edge_notes = edge_sounds(*sf.read(wav, dtype="float32"))
            report[r["id"]] = {"sha256": d["sha256"], "spoken": row["spoken"], "verdict": worst(p["verdict"] for p in r["problems"]),
                               "edge_flags": edge_flags, "edge_notes": edge_notes, "heard": r["heard"], "heard_second": r.get("heard_second") or r.get("second_agrees"),
                               "ratio": r["ratio"], "errs": r["errs"], "diff": [x for x in r["diff"] if x["op"] != "equal"],
                               "problems": r["problems"], "pace_vs_whisper": r.get("pace")}
        (CHECKS / f"asr.{lang}.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        print(f"wrote {CHECKS / f'asr.{lang}.json'}", flush=True)


# ----------------------------------------------------------------------------------------------- choosing

RANK = {"pass": 0, "unsure": 1, "fail": 2}


def cmd_manifest():
    lines, totals = [], {}
    for lang in LANGS:
        asr = json.loads((CHECKS / f"asr.{lang}.json").read_text())
        rows = load(lang)
        for row in rows:
            tries, superseded = [], []
            for meta in sorted((AUDIO / lang / "takes").glob(f"{row['id']}.take*.json"), key=lambda p: int(p.stem.split("take")[1])):
                d = json.loads(meta.read_text())
                if d["config"]["spoken"] != row["spoken"]:      # a try of an earlier wording: kept, listed, never chosen
                    a = asr.get(f"{row['id']}.take{d['config']['take']}", {})
                    superseded.append({"take": d["config"]["take"], "seed": d["config"]["seed"], "spoken": d["config"]["spoken"],
                                       "file": str(meta.with_suffix(".wav").relative_to(DATA)), "seconds": d["seconds"],
                                       "sha256": d["sha256"], "asr_verdict": a.get("verdict"), "heard": a.get("heard")})
                    continue
                key = f"{row['id']}.take{d['config']['take']}"
                a = asr.get(key)
                assert a and a["sha256"] == d["sha256"], f"{lang} {key} has not been checked (run check)"
                tries.append((d, meta.with_suffix(".wav"), a))
            assert tries, (lang, row["id"])
            manual = CHOICES.get((lang, row["id"]))
            for t in tries:   # what the audio itself says, under the current rules: pace, abrupt ends, edge ticks
                t[0]["pace_units"] = pace_units(row)
                t[0]["pace"] = round(t[0]["pace_units"] / t[0]["speech_seconds"], 2)
                t[0]["flags"] = own_flags(row, t[0]) + t[2]["edge_flags"]
            clean = [t for t in tries if t[2]["verdict"] == "pass" and not t[0]["flags"]]
            if manual:
                chosen = next(t for t in tries if t[0]["config"]["take"] == manual[0])
                reason, status = manual[1], "doubtful" if manual[1].startswith("doubtful:") else "pass (reviewed)"
            elif clean:
                chosen, reason, status = clean[0], "first take to pass every automatic check", "pass"
            else:
                chosen = min(tries, key=lambda t: (RANK[t[2]["verdict"]], len(t[0]["flags"]), -t[2]["ratio"]))
                reason, status = "no take passed every check; best of the tries kept", "doubtful"
            d, wav, a = chosen
            out = AUDIO / lang / f"{row['id']}.wav"
            shutil.copyfile(wav, out)
            assert sha(out) == d["sha256"]
            c = d["config"]
            lines.append({
                "id": row["id"], "lang": lang, "section": row["section"], "caption": row["caption"],
                "spoken": row["spoken"], "spoken_forms": row["spoken_forms"], "file": str(out.relative_to(DATA)),
                "engine": c["engine"], "model": c["model"], "mode": c["mode"], "instruction": c["instruction"],
                "reference_profile": {"voice": c["voice"], "profile": c["profile"], "profile_sha256": c["profile_sha256"],
                                      "reference_sha256": c["reference_sha256"]},
                "seed": c["seed"], "settings": {k: c.get(k) for k in ("speed", "temperature", "max_tokens", "lang_code")
                                                if c.get(k) is not None} | {"cloud_requests": 0, "voice_conversion": False},
                "seconds": d["seconds"], "speech_seconds": d["speech_seconds"], "pace": d["pace"], "sample_rate": d["sample_rate"],
                "whole_take_gain": d["whole_take_gain"], "sha256": d["sha256"],
                "asr": {"medium": a["heard"], "second": a["heard_second"], "verdict": a["verdict"], "ratio": a["ratio"],
                        "differences": a["diff"], "problems": [f"{p['verdict']}: {p['title']} {p['detail']}".strip() for p in a["problems"]]},
                "own_flags": d["flags"], "edge_notes": a["edge_notes"], "listen_for": LISTEN.get((lang, row["id"]), []),
                "status": status, "chosen_take": c["take"], "why": reason,
                "takes": [{"take": t[0]["config"]["take"], "seed": t[0]["config"]["seed"], "file": str(t[1].relative_to(DATA)),
                           "seconds": t[0]["seconds"], "sha256": t[0]["sha256"], "asr_verdict": t[2]["verdict"],
                           "heard": t[2]["heard"], "own_flags": t[0]["flags"]} for t in tries],
                "superseded_takes": superseded,
            })
        mine = [l for l in lines if l["lang"] == lang]
        totals[lang] = {"lines": len(mine), "file_seconds": round(sum(l["seconds"] for l in mine), 2),
                        "speech_seconds": round(sum(l["speech_seconds"] for l in mine), 2),
                        "doubtful": [l["id"] for l in mine if l["status"] == "doubtful"]}
    manifest = {"film": "We Build A BlackHole with AI", "version": "v01", "generated": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "script": {lang: f"docs/black-hole-ai/{lang}-edit.md" for lang in LANGS}, "generator": "scripts/black-hole-ai/voice.py",
                "path": {"zh": "direct local Qwen3-TTS-12Hz-1.7B-Base-8bit ICL, profiles/louise/zh, no conversion",
                         "en": "direct local CosyVoice3 (Fun-CosyVoice3-0.5B) zero-shot-instruct, profiles/louise/en"},
                "notes": ["Chinese delivery is not steered per section: the Qwen Base ICL path has no instruction input.",
                          "English years spoken as 'twenty fifteen' / 'twenty twenty-four' (voice.py EXTRA_SPOKEN); captions keep digits.",
                          "ASR passing is not proof of clean sound: polyphones, digit-by-digit Chinese years and timbre need listening."],
                "totals": totals, "lines": lines}
    (AUDIO / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    for lang in LANGS:
        print(lang, totals[lang])
    for l in lines:
        print(f"{l['lang']} {l['id']} take{l['chosen_take']} {l['seconds']:.2f}s {l['status']} {l['asr']['verdict']} {l['own_flags'] or ''}")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("synth")
    s.add_argument("lang", choices=LANGS)
    s.add_argument("--take", type=int, default=1, choices=range(1, 10))   # 1-3 per wording; a reworded line goes on at 4, 7
    s.add_argument("--only", default="")
    sub.add_parser("check")
    sub.add_parser("manifest")
    sub.add_parser("script")
    args = ap.parse_args()
    if args.cmd == "synth":
        cmd_synth(args.lang, args.take, set(args.only.split(",")) - {""})
    elif args.cmd == "check":
        cmd_check()
    elif args.cmd == "manifest":
        cmd_manifest()
    else:
        for lang, rows in both().items():
            for r in rows:
                print(lang, r["id"], r["section"], r["spoken"] if r["spoken"] == r["caption"] else f"{r['spoken']}   [caption: {r['caption']}]")


if __name__ == "__main__":
    main()
