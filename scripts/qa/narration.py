"""配音校对: every line is cut out of the audio the film actually plays (after speed changes, splices and the mix),
Whisper listens to it, and what it heard is compared with what the voice was asked to say.

One finding per line, verdict = the worst of its problems (thresholds in T are starting values, calibrated on the
中英阅读 films 2026-11-20):
  fail    a wrong number; a negation lost or added; words heard that the script does not have (a garbled tail, a
          stray word, a phrase said twice); a pause over 1.2 s inside the line; a pace far off the film's own; several
          units heard differently.
  unsure  one unit heard differently (a name, a polyphone, or Whisper's own guess); a pause that splits a word
          (座头|鲸); a risky word the second model hears differently; a question put to the audience (tone); a click
          before or after the words; a line much louder or softer than the rest. These go to the listening page.
"""
from __future__ import annotations

import difflib
import json
import logging
import re
from pathlib import Path

import numpy as np

from common import FAIL, PASS, UNSURE, db, item, rms_db, short_hash, worst
from textnorm import joiner, number_ands, same_sound, units, with_pinyin

T = {
    "pad": 0.25,               # s of context cut around a line (never into the neighbour's speech)
    "fail_ratio": 0.90,        # long lines: below this is a fail
    "short_units": 20,         # shorter lines: 1 differing unit = unsure, 2+ = fail
    "gap_fail": 1.2,           # s of silence inside one line
    "split_word": 0.35,        # s of pause inside one word (jieba) — 座头|鲸 (classical verse pauses 2+3: 谁知|盘中餐 ≈ 0.3)
    "split_single": 0.45,      # s of pause before/after a lone content character jieba could not join
    "pause_no_mark": 0.7,      # s of pause where the script has no punctuation, between words
    "pace_fail": (0.55, 1.6),  # × the median pace of its group (spec line "group", else language)
    "pace_min_units": 8,       # shorter lines (titles) have no stable pace
    "pace_unsure": (0.7, 1.4),  # poems are read slower than prose on purpose
    "level_unsure_db": 2.5,    # a line's level vs the median line (voice track only)
    "click_db": -50.0,         # a click: a ≤ 4 ms burst above this level ...
    "click_over": 20.0,        # ... standing this many dB over the 30 ms around it
}
ZH_PROMPT = "以下是普通话的句子。"
VERBATIM_EN = "Umm, so, so I I think, like, we we would would, uh, you know... Hmm."
PITFALLS = json.loads((Path(__file__).with_name("pitfalls.json")).read_text(encoding="utf-8"))
FILLERS = {"嗯", "呃", "啊", "诶", "哦", "唉", "um", "uh", "hmm", "mm", "ah", "oh"}
FUNCTION_ZH = set("的了是在我你他她它们也就都和与吗呢吧啊呀这那有不没很又还把被给让说着过地得一个")
SR = 16000


class Listener:
    """Whisper models, loaded once, with a cache keyed by the exact audio so a re-run only listens to what changed."""

    def __init__(self, cache_path: Path, primary: str = "medium", second: str = "small"):
        import whisper
        self.whisper, self.names, self.models = whisper, {"primary": primary, "second": second}, {}
        self.cache_path = cache_path
        self.cache = json.loads(cache_path.read_text()) if cache_path.exists() else {}

    def model(self, which: str):
        name = self.names[which]
        if name not in self.models:
            self.models[name] = self.whisper.load_model(name)
        return self.models[name]

    def hear(self, audio: np.ndarray, lang: str, prompt: str = "", which: str = "primary") -> dict:
        key = short_hash(self.names[which], lang, prompt, audio.tobytes())
        if key not in self.cache:
            r = self.model(which).transcribe(audio, language=lang, fp16=False, initial_prompt=prompt or None,
                                             word_timestamps=True, condition_on_previous_text=False)
            words = [{"w": w["word"], "s": round(w["start"], 3), "e": round(w["end"], 3)}
                     for seg in r["segments"] for w in seg.get("words", [])]
            self.cache[key] = {"text": r["text"].strip(), "words": words}
        return self.cache[key]

    def save(self):
        self.cache_path.write_text(json.dumps(self.cache, ensure_ascii=False))


def merge_digits(words: list[dict]) -> list[dict]:
    """Whisper splits a number into tokens (「1」「36」); read them as one (136 → 一百三十六)."""
    out = []
    for w in words:
        if out and re.fullmatch(r"\s*[\d.,%]+", w["w"]) and re.search(r"\d[\d.,%]*$", out[-1]["w"].strip()):
            out[-1] = {"w": out[-1]["w"] + w["w"].strip(), "s": out[-1]["s"], "e": w["e"]}
        else:
            out.append(dict(w))
    return out


def heard_units(words: list[dict], lang: str) -> tuple[list[dict], list[int]]:
    got, owner = [], []
    for i, w in enumerate(words):
        for u in units(w["w"], lang):
            got.append(u)
            owner.append(i)
    if lang == "zh":
        for u in got:
            u.pop("py", None)
        with_pinyin(got)
    else:   # Whisper's words arrive one at a time, so the "and" inside a number is dropped here, across words
        drop = number_ands(got)
        got, owner = [u for k, u in enumerate(got) if k not in drop], [o for k, o in enumerate(owner) if k not in drop]
    return got, owner


def compare(want: list[dict], got: list[dict], lang: str):
    """difflib on exact units, then differences that are only another spelling of the same sound fold into equal."""
    raw = difflib.SequenceMatcher(None, [u["u"] for u in want], [u["u"] for u in got], autojunk=False).get_opcodes()
    ops = []
    for op, a1, a2, b1, b2 in raw:
        if op == "replace":
            a, b = want[a1:a2], got[b1:b2]
            if (a2 - a1 == b2 - b1 and all(same_sound(x, y, lang) for x, y in zip(a, b))) or \
               "".join(x["u"] for x in a) == "".join(y["u"] for y in b):
                op = "equal"
        if ops and ops[-1][0] == op == "equal":
            ops[-1] = ("equal", ops[-1][1], a2, ops[-1][3], b2)
        else:
            ops.append((op, a1, a2, b1, b2))
    errs = sum(max(a2 - a1, b2 - b1) for op, a1, a2, b1, b2 in ops if op != "equal")
    same = sum(min(a2 - a1, b2 - b1) for op, a1, a2, b1, b2 in ops if op == "equal")
    ratio = 2 * same / max(1, len(want) + len(got))
    return ops, errs, ratio


def diff_segments(want, got, ops, lang) -> list[dict]:
    j = joiner(lang)
    return [{"op": op, "a": j.join(u["c"] for u in want[a1:a2]), "b": j.join(u["c"] for u in got[b1:b2])}
            for op, a1, a2, b1, b2 in ops]


def matched(ops) -> dict[int, int]:
    m = {}
    for op, a1, a2, b1, b2 in ops:
        if op == "equal":
            for k in range(a2 - a1):
                m[a1 + k] = b1 + min(k, b2 - b1 - 1)
    return m


def risky_positions(want: list[dict], lang: str, extra: list[str]) -> set[int]:
    """Indices of units that a second model must also hear right: numerals, negations, known pitfalls."""
    pos = {i for i, u in enumerate(want) if u["num"] or u["neg"]}
    keys = [u["u"] for u in want]
    for word in PITFALLS[lang]["risky"] + list(extra or []):
        wu = [u["u"] for u in units(word, lang)]
        for i in range(len(keys) - len(wu) + 1):
            if wu and keys[i:i + len(wu)] == wu:
                pos.update(range(i, i + len(wu)))
    return pos


def mark_names(want: list[dict], names: list[str], lang: str) -> list[dict]:
    """Names and titles from the spec (李绅, 耶利米哀歌, Rossetti): Whisper spells them its own way, so a difference
    there is only 拿不准, never a fail on its own."""
    keys = [u["u"] for u in want]
    for name in names:
        nu = [u["u"] for u in units(name, lang)]
        for i in range(len(keys) - len(nu) + 1):
            if nu and keys[i:i + len(nu)] == nu:
                for k in range(i, i + len(nu)):
                    want[k]["name"] = True
    return want


def CJK_ONLY(text: str) -> str:
    return "".join(re.findall(r"[一-鿿]", text))


_jieba = None


def zh_words(chars: str) -> list[int]:
    """For each character, the index of the jieba word it belongs to."""
    global _jieba
    if _jieba is None:
        import jieba
        jieba.setLogLevel(logging.WARNING)
        _jieba = jieba
    out = []
    for k, w in enumerate(_jieba.cut(chars, HMM=True)):
        out += [k] * len(w)
    return out


def pauses(audio: np.ndarray, t0: float, t1: float, rate: int = SR, min_len: float = 0.2) -> list[tuple[float, float]]:
    """Silent stretches inside the speech (10 ms frames more than 30 dB under the line's loud frames). Whisper's
    Chinese character times are contiguous — a pause hides inside a character — so pauses come from the sound."""
    a, b = int(t0 * rate), int(t1 * rate)
    x = audio[a:b]
    hop = int(0.01 * rate)
    n = len(x) // hop
    if n < 5:
        return []
    e = np.sqrt((x[: n * hop].astype(np.float64).reshape(n, hop) ** 2).mean(axis=1)) + 1e-9
    quiet = 20 * np.log10(e) < 20 * np.log10(np.percentile(e, 95)) - 30
    out, k = [], 0
    while k < n:
        if quiet[k]:
            j = k
            while j < n and quiet[j]:
                j += 1
            if (j - k) * 0.01 >= min_len and k > 0 and j < n:
                out.append((t0 + k * 0.01, t0 + j * 0.01))
            k = j
        else:
            k += 1
    return out


def odd_pauses(want, got, ops, owner, words, lo, lang, sound, free: bool = False) -> tuple[list, list]:
    """Pauses the script does not ask for: inside a word (座头|鲸 — one word read as two), a long one where there is
    no punctuation, and any stop over gap_fail. A line marked free (poetry and scripture read aloud: 谁知|盘中餐,
    我的心|等候主) keeps only the gap_fail rule. Returns (unsure findings, fail findings)."""
    if not words:
        return [], []
    m = matched(ops)
    inv = {b: a for a, b in m.items()}
    wid = zh_words("".join(u["c"] for u in want)) if lang == "zh" else list(range(len(want)))
    unit_span = [(words[owner[k]]["s"] + lo, words[owner[k]]["e"] + lo) for k in range(len(got))]
    unsure, fail = [], []
    for p0, p1 in pauses(sound, lo + words[0]["s"], lo + words[-1]["e"]):
        g = p1 - p0
        # The boundary between heard units j and j+1 that touches the pause (Whisper hangs the pause on the end of
        # one character or the start of the next, so the boundary time sits at one edge of the pause).
        def dist(k):
            t = (unit_span[k][1] + unit_span[k + 1][0]) / 2
            return 0.0 if p0 - 0.05 <= t <= p1 + 0.05 else min(abs(t - p0), abs(t - p1))
        if len(got) < 2:
            continue
        j = min(range(len(got) - 1), key=dist)
        if dist(j) > 0.15 or j not in inv or j + 1 not in inv:
            continue
        a = inv[j]
        if inv[j + 1] != a + 1:
            continue
        pair = want[a]["c"] + joiner(lang) + want[a + 1]["c"]
        if want[a]["p"]:
            if g > 2.0:
                unsure.append((f"「{pair}」之间停了 {g:.1f} 秒", "停得比较久", p0, p1))
            continue
        if g > T["gap_fail"]:
            fail.append((f"「{pair}」中间停了 {g:.1f} 秒", "句子中间停住了", p0, p1))
            continue
        if free:
            continue
        if lang == "zh":
            same_word = wid[a] == wid[a + 1]
            lone = [k for k in (a, a + 1) if wid.count(wid[k]) == 1 and want[k]["c"] not in FUNCTION_ZH]
            if same_word and g >= T["split_word"]:
                unsure.append((f"「{pair}」中间停了 {g:.2f} 秒", "一个词被读断了", p0, p1))
                continue
            if lone and g >= T["split_single"]:
                unsure.append((f"「{pair}」中间停了 {g:.2f} 秒", "可能把一个词读断了（稿子这里没有标点）", p0, p1))
                continue
        if g >= T["pause_no_mark"]:
            unsure.append((f"「{pair}」中间停了 {g:.2f} 秒", "稿子这里没有标点", p0, p1))
    return unsure, fail


TAKE = {"n": 2048, "hop": 640, "bands": 32, "lo": 80.0, "hi": 4000.0, "floor": 50.0}


def take_print(x: np.ndarray) -> str:
    """A coarse picture of how one recording sounds, for decisions.same_take: 32 bands from 80 Hz to 4 kHz every
    40 ms (128 ms windows), each as one byte, starting at the first sound and ending at the last. The same take
    moved on the timeline or put through AAC again gives almost the same print; another take of the same words —
    other rhythm, other melody — does not. Level does not matter (bytes are relative to the loudest band)."""
    import base64
    x = np.asarray(x, np.float32)
    n, hop, bands = TAKE["n"], TAKE["hop"], TAKE["bands"]
    if len(x) > 400:   # start at the speech itself, so a few ms more or less silence in front changes nothing
        w = 80
        level = np.sqrt(np.convolve(x.astype(np.float64) ** 2, np.ones(w) / w, "same"))
        loud = np.where(level > level.max() * 10 ** (-30 / 20))[0]
        if len(loud):
            x = x[loud[0]: loud[-1] + 1]
    if len(x) < n + hop:
        x = np.pad(x, (0, n + hop - len(x)))
    frames = np.lib.stride_tricks.sliding_window_view(x, n)[::hop] * np.hanning(n).astype(np.float32)
    power = np.abs(np.fft.rfft(frames, axis=1)) ** 2
    freq = np.fft.rfftfreq(n, 1 / SR)
    edges = np.geomspace(TAKE["lo"], TAKE["hi"], bands + 1)
    level = np.stack([power[:, (freq >= a) & (freq < b)].sum(axis=1) for a, b in zip(edges[:-1], edges[1:])], axis=1)
    d = 10 * np.log10(level + 1e-12)
    d = np.clip(d - d.max(), -TAKE["floor"], 0.0)
    q = np.round((d + TAKE["floor"]) / TAKE["floor"] * 255).astype(np.uint8)
    return f"t1:{bands}:" + base64.b64encode(q.tobytes()).decode("ascii")


def clicks(voice: np.ndarray, regions: list[tuple[float, float]], rate: int) -> list[float]:
    """CosyVoice leaves ~1 ms clicks in the silence before or after a take (zh it01-02, |sample| 650). A click is a
    burst of at most a few ms standing well over the 30 ms around it — breath and word tails are longer."""
    found = []
    hop = max(1, int(0.001 * rate))
    for r0, r1 in regions:
        a, b = max(0, int(r0 * rate)), min(len(voice), int(r1 * rate))
        n = (b - a) // hop
        if n < 40:
            continue
        p = np.abs(voice[a:a + n * hop]).reshape(n, hop).max(axis=1)
        for k in np.argsort(p)[::-1][:5]:
            if db(p[k]) < T["click_db"]:
                break
            before, after = p[max(0, k - 30): max(0, k - 3)], p[k + 4: k + 31]
            if len(before) < 8 or len(after) < 8:
                continue
            # quiet on BOTH sides: a word's onset is loud after, a take's hard end is loud before
            ref = max(np.median(before), np.median(after)) + 1e-7
            if db(p[k]) - db(ref) >= T["click_over"]:
                found.append(round(r0 + k * hop / rate, 3))
                break
    return found


def check(spec: dict, played: np.ndarray, voice: np.ndarray | None, listener: Listener, log=print) -> tuple[list, list]:
    """Returns (per-line results, findings: one per line that is not a clean pass)."""
    lines = spec["lines"]
    prompts = spec.get("prompt") or {}
    results = []
    for i, line in enumerate(lines):
        lang = line["lang"]
        prev_end = lines[i - 1]["end"] if i else 0.0
        next_start = lines[i + 1]["start"] if i + 1 < len(lines) else len(played) / SR
        lo = max(0.0, line["start"] - T["pad"], min(line["start"], prev_end + 0.05))
        hi = min(len(played) / SR, line["end"] + T["pad"], max(line["end"], next_start - 0.05))
        clip = played[int(lo * SR): int(hi * SR)]
        prompt = (ZH_PROMPT if lang == "zh" else "") + prompts.get(lang, "")
        h = listener.hear(clip, lang, prompt)
        words = merge_digits(h["words"])
        want = mark_names(units(line["text"], lang), spec.get("names", []), lang)
        got, owner = heard_units(words, lang)
        ops, errs, ratio = compare(want, got, lang)
        if line.get("caption"):
            alt = mark_names(units(line["caption"], lang), spec.get("names", []), lang)
            ops2, errs2, ratio2 = compare(alt, got, lang)
            if errs2 < errs:
                want, ops, errs, ratio = alt, ops2, errs2, ratio2
        res = {"id": line["id"], "lang": lang, "start": line["start"], "end": line["end"], "lo": round(lo, 3),
               "hi": round(hi, 3), "text": line["text"], "heard": h["text"], "ratio": round(ratio, 3), "errs": errs,
               "units": len(want), "diff": diff_segments(want, got, ops, lang), "problems": [],
               "question": bool(line.get("question"))}
        probs = res["problems"]

        def add(verdict, code, title, detail="", t0=None, t1=None):
            probs.append({"verdict": verdict, "code": code, "title": title, "detail": detail,
                          "t0": round(t0 if t0 is not None else line["start"], 3),
                          "t1": round(t1 if t1 is not None else line["end"], 3)})

        # Words heard that the script does not have.
        extra_edge, extra_mid, stray = [], [], []
        for op, a1, a2, b1, b2 in ops:
            added = (b2 - b1) - (a2 - a1)
            heard_txt = joiner(lang).join(u["c"] for u in got[b1:b2])
            if op == "insert":
                if a1 == 0 or a1 == len(want):
                    extra_edge.append(heard_txt)
                elif added >= 2:
                    extra_mid.append(heard_txt)
                elif want[a1 - 1]["p"]:
                    stray.append(heard_txt)
            elif op == "replace" and added >= 3:
                extra_mid.append(heard_txt)
        fillers = [x for x in extra_edge if x.strip() in FILLERS]
        if fillers:  # a breath Whisper writes as 嗯 — or a real filler: listen
            add(UNSURE, "narration.filler", "句首或句尾听到一个语气词（可能是呼吸声，也可能真读了）", "、".join(fillers))
        extra_edge = [x for x in extra_edge if x.strip() not in FILLERS]
        if extra_edge:
            add(FAIL, "narration.extra_edge", "句首或句尾多出了词", "、".join(extra_edge))
        if extra_mid:
            add(FAIL, "narration.extra", "句中多出了词（重复了，或夹了怪字）", "、".join(extra_mid))
        if stray:
            add(UNSURE, "narration.stray", "两句之间多了一个字", "、".join(stray))
        # Numbers and negations carry the meaning: any difference there is a fail.
        bad_num = [joiner(lang).join(u["c"] for u in want[a1:a2]) + "→" + joiner(lang).join(u["c"] for u in got[b1:b2])
                   for op, a1, a2, b1, b2 in ops
                   if op != "equal" and any(u["num"] for u in want[a1:a2])]
        if bad_num:
            add(FAIL, "narration.number", "数字听起来不对", "、".join(bad_num))
        n_want, n_got = sum(u["neg"] for u in want), sum(u["neg"] for u in got)
        if n_want != n_got:
            add(FAIL, "narration.negation", "否定词数量不对（意思可能反了）", f"稿子 {n_want} 个，听到 {n_got} 个")
        # A repeated phrase in the script that Whisper wrote once (it merges repeats: 「胜于守夜的，等候天亮」×2).
        repeat_drop = [joiner(lang).join(u["c"] for u in want[a1:a2]) for op, a1, a2, b1, b2 in ops
                       if op == "delete" and a2 - a1 >= 2 and a1 >= a2 - a1
                       and [u["u"] for u in want[a1 - (a2 - a1):a1]] == [u["u"] for u in want[a1:a2]]]
        name_errs = sum(max(a2 - a1, b2 - b1) for op, a1, a2, b1, b2 in ops
                        if op == "replace" and all(u.get("name") for u in want[a1:a2]))
        drop_errs = sum(len(x) for x in repeat_drop) if lang == "zh" else sum(len(x.split()) for x in repeat_drop)
        plain = errs - name_errs - drop_errs
        if name_errs:
            names_heard = "、".join(f"{joiner(lang).join(u['c'] for u in want[a1:a2])}→{joiner(lang).join(u['c'] for u in got[b1:b2])}"
                                   for op, a1, a2, b1, b2 in ops if op == "replace" and all(u.get("name") for u in want[a1:a2]))
            add(UNSURE, "narration.name", "名字听得不一样（Whisper 常拼不对名字，请听读音）", names_heard)
        if repeat_drop:
            add(UNSURE, "narration.repeat_drop", "稿子里重复的一段只听到一遍（Whisper 常把重复只写一遍，请听是不是读了两遍）",
                "、".join(repeat_drop))
        second = None
        if 0 < plain <= 2 and not (extra_edge or extra_mid or bad_num):
            # Whisper medium often writes the commoner character (一 for 疑, 叉 for 杈). If the second model hears
            # the script's own characters at every place medium did not, the sound is there: pass.
            h2 = listener.hear(clip, lang, prompt, which="second")
            got2, _ = heard_units(merge_digits(h2["words"]), lang)
            ops2, _, _ = compare(want, got2, lang)
            m2 = matched(ops2)
            diff_pos = [k for op, a1, a2, b1, b2 in ops if op in ("replace", "delete")
                        and not all(u.get("name") for u in want[a1:a2]) for k in range(a1, a2)]
            second = h2["text"]
            if diff_pos and all(k in m2 for k in diff_pos) and not any(o[0] == "insert" for o in ops):
                res["second_agrees"] = second
                plain = 0
        if plain > 0:
            short = len(want) < T["short_units"]
            if (short and plain >= 2) or (not short and ratio < T["fail_ratio"] and plain >= 2):
                add(FAIL, "narration.text", f"有 {plain} 处和稿子不一样", f"相似度 {ratio:.2f}")
            elif not (extra_edge or extra_mid or bad_num):
                add(UNSURE, "narration.text", f"有 {plain} 处和稿子不一样",
                    f"相似度 {ratio:.2f}" + (f"；small 听到：{second}" if second else ""))
        # Timing inside the line.
        if words:
            sound = voice if voice is not None else played
            soft, hard = odd_pauses(want, got, ops, owner, words, lo, lang, sound, bool(line.get("free_pauses")))
            for title, detail, t0, t1 in hard:
                add(FAIL, "narration.gap", title, detail, t0, t1)
            for title, detail, t0, t1 in soft:
                add(UNSURE, "narration.pause", title, detail, t0, t1)
            span = words[-1]["e"] - words[0]["s"]
            res["pace"] = round(len(want) / span, 3) if span > 0.3 else None
        else:
            add(FAIL, "narration.silent", "这一句什么也没听到")
            res["pace"] = None
        # A second model on the words that have gone wrong before (numbers, negations, pitfalls).
        risky = risky_positions(want, lang, spec.get("risky"))
        if risky and not any(p["verdict"] == FAIL for p in probs):
            h2 = listener.hear(clip, lang, prompt, which="second")
            got2, _ = heard_units(merge_digits(h2["words"]), lang)
            ops2, _, _ = compare(want, got2, lang)
            m1, m2 = matched(ops), matched(ops2)
            off = sorted(p for p in risky if p in m1 and p not in m2)
            if off:
                shown = "、".join(dict.fromkeys(want[p]["c"] for p in off))
                add(UNSURE, "narration.risky", f"易错词「{shown}」两个模型听得不一样",
                    f"medium：{h['text']} ／ small：{h2['text']}")
            res["heard_second"] = h2["text"]
        if lang == "en" and words:
            hv = listener.hear(clip, lang, VERBATIM_EN, which="second")
            gv, _ = heard_units(merge_digits(hv["words"]), lang)
            keys = [u["u"] for u in want]
            reps = [gv[k]["c"] for k in range(1, len(gv)) if gv[k]["u"] == gv[k - 1]["u"]
                    and not any(keys[j] == keys[j - 1] == gv[k]["u"] for j in range(1, len(keys)))]
            opsv, _, _ = compare(want, gv, lang)
            for op, a1, a2, b1, b2 in opsv:   # a phrase said twice: the inserted words repeat the script next to them
                n = b2 - b1
                if op == "insert" and n >= 2 and 0 < a1 < len(want):
                    ins = [u["u"] for u in gv[b1:b2]]
                    if ins == keys[max(0, a1 - n):a1] or ins == keys[a1:a1 + n]:
                        reps.append(" ".join(u["c"] for u in gv[b1:b2]))
            if reps:
                add(FAIL, "narration.repeat", "有词说了两遍", "、".join(reps) + f"（逐字听写：{hv['text']}）")
        if line.get("question"):
            add(UNSURE, "narration.tone", "向观众提问的一句：语气要好奇，不是批评")
        for rule in PITFALLS[lang].get("listen", []):
            if rule["text"].lower() in line["text"].lower():
                add(UNSURE, "narration.articulation", f"「{rule['text']}」须核听完整字音及衔接", rule["why"])
        # The voice alone (when the film keeps it): clicks and level. Needs exact speech times, not caption times.
        if voice is not None and words:
            spans = [(lo + w["s"], lo + w["e"]) for w in words]
            res["level_db"] = round(rms_db(np.concatenate([voice[int(a * SR): int(b * SR)] for a, b in spans])), 2)
            if not line.get("from_captions"):
                first, last = line["start"], line["end"]   # the spec's speech times (Whisper's edges drift)
                regions = [(max(prev_end + 0.1, first - 0.7), first - 0.12),
                           (last + 0.12, min(next_start - 0.1, last + 0.7))]
                for t in clicks(voice, regions, SR):
                    add(UNSURE, "narration.click", f"{'句首' if t < line['start'] else '句尾'}有咔哒声", f"在 {t:.2f} 秒",
                        t - 0.4, t + 0.4)
        results.append(res)
        verdict = worst(p["verdict"] for p in probs)
        log(f"{'OK  ' if verdict == PASS else ('??  ' if verdict == UNSURE else 'FAIL')} {line['id']:<22} "
            f"{ratio:.2f} e{errs} | {h['text'][:70]}" + ("" if verdict == PASS else "  <- " + "; ".join(p["title"] for p in probs)))
    # Pace and level against the film's own median, per language.
    group = {l["id"]: f"{l['lang']}:{l.get('group', '')}" for l in lines}
    for g in set(group.values()):
        rows = [r for r in results if group[r["id"]] == g and r.get("pace") and r["units"] >= T["pace_min_units"]]
        if len(rows) >= 4:
            med = float(np.median([r["pace"] for r in rows]))
            for r in rows:
                x = r["pace"] / med
                v = FAIL if not T["pace_fail"][0] <= x <= T["pace_fail"][1] else \
                    UNSURE if not T["pace_unsure"][0] <= x <= T["pace_unsure"][1] else None
                if v:
                    r["problems"].append({"verdict": v, "code": "narration.pace", "title": f"语速是全片的 {x:.2f} 倍",
                                          "detail": "", "t0": r["start"], "t1": r["end"]})
    for lang in {r["lang"] for r in results}:
        lv = [r for r in results if r["lang"] == lang and r.get("level_db") is not None]
        if len(lv) >= 4:
            med = float(np.median([r["level_db"] for r in lv]))
            for r in lv:
                if abs(r["level_db"] - med) > T["level_unsure_db"]:
                    r["problems"].append({"verdict": UNSURE, "code": "narration.level",
                                          "title": f"这句比别的句子{'响' if r['level_db'] > med else '轻'} {abs(r['level_db'] - med):.1f} dB",
                                          "detail": "", "t0": r["start"], "t1": r["end"]})
    findings, nth = [], {}
    for r in results:
        nth[r["lang"], r["text"]] = nth.get((r["lang"], r["text"]), 0) + 1   # which of the lines with these words
        if not r["problems"] and r.get("second_agrees"):
            # Not asked, but shown (collapsed) on the page: small may agree with the script out of its language prior.
            findings.append(item("narration", PASS, "narration.second_pass",
                                 f"{r['id']}：medium 听到的字不一样，small 听到的和稿子一样，自动算通过",
                                 f"small：{r['second_agrees']}", t0=r["start"], t1=r["end"],
                                 key=short_hash("second", r["id"], r["heard"]), line=r["id"], lang=r["lang"],
                                 text=r["text"], heard=r["heard"], diff=r["diff"], lo=r["lo"], hi=r["hi"]))
            continue
        if not r["problems"]:
            continue
        # What a decision is tied to. The key names the line (its words, and which of the lines with those words)
        # and the kinds of doubt; the take print names the recording, so decisions.holds() can tell the same take in
        # a new render (approval stays) from another take Whisper writes the same way (asked again). What Whisper
        # heard and where the line sits are NOT in the key: both change between renders of one recording.
        codes = sorted({p["code"] for p in r["problems"]})
        sound = voice if voice is not None else played
        v = worst(p["verdict"] for p in r["problems"])
        findings.append(item("narration", v, "narration.line", f"{r['id']}：" + "；".join(p["title"] for p in r["problems"]),
                             "；".join(p["detail"] for p in r["problems"] if p["detail"]),
                             t0=r["start"], t1=r["end"],
                             key=short_hash("line", r["lang"], r["text"], nth[r["lang"], r["text"]], *codes),
                             take=take_print(sound[int(r["lo"] * SR): int(r["hi"] * SR)]),
                             line=r["id"], lang=r["lang"], text=r["text"], heard=r["heard"], diff=r["diff"],
                             lo=r["lo"], hi=r["hi"], problems=r["problems"]))
    return results, findings


def lint(spec: dict) -> list[dict]:
    """Before voicing: spellings the voices are known to get wrong in the SPOKEN text."""
    out = []
    for line in spec["lines"]:
        for rule in PITFALLS[line["lang"]]["avoid"]:
            hit = (rule["text"] in line["text"]) if "text" in rule else re.search(rule["pattern"], line["text"], re.I)
            if hit:
                out.append(item("script", UNSURE, "script.pitfall", f"{line['id']}：{rule['why']}", line["text"],
                                line=line["id"]))
    return out
