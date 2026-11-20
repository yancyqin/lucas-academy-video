"""Acceptance test for the narration and mix checks: known-bad audio must land in the right verdict.

    .venv-align/bin/python scripts/qa/tests/test_narration.py [FILM_MP4 SPEC MUSIC]

Defaults use a 中英阅读 film (read only) and its spec from `qa.py spec zhongying`, and a free Mozart recording for
the music bed. Each case cuts one line out of the real film, breaks it the way a voice has broken before, and checks
that the finding appears — and that the untouched line does not have it.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import mix  # noqa: E402
import narration as N  # noqa: E402
import spec as S  # noqa: E402
from common import FAIL, OUT, PASS, UNSURE, decode_audio  # noqa: E402

ZY = Path("/Users/yqin/repo/playground/lucas-academy-video/.claude/worktrees/video-animals-children-footage-dc629f")
FILM = Path(sys.argv[1]) if len(sys.argv) > 1 else ZY / "out/zhong-ying/who-woke-you/who-woke-you.mp4"
SPEC = Path(sys.argv[2]) if len(sys.argv) > 2 else OUT / "who-woke-you/qa-spec.json"
MUSIC = Path(sys.argv[3]) if len(sys.argv) > 3 else Path(
    "/Users/yqin/repo/playground/lucas-academy-video-data/fun-informatics-03/public/music/mozart-k265-renzi.mp3")
SR = N.SR


def one_line(line: dict, audio: np.ndarray, voice: np.ndarray | None, *, text: str | None = None):
    """A tiny film holding just this line (with 1 s either side), and its spec."""
    a, b = int((line["start"] - 1.0) * SR), int((line["end"] + 1.0) * SR)
    l2 = {**line, "start": 1.0, "end": 1.0 + line["end"] - line["start"], "question": False,
          "free_pauses": False}   # judged as prose narration (Yancy's films), not as a poem read aloud
    if text is not None:
        l2["text"] = text
    return audio[a:b].copy(), (voice[a:b].copy() if voice is not None else None), l2


def run(name, spec, played, voice, listener, expect_code, expect_verdict):
    res, items = N.check(spec, played, voice, listener, log=lambda *_: None)
    got = {(p["code"], p["verdict"]) for i in items for p in i.get("problems", [i])}
    codes = expect_code if isinstance(expect_code, tuple) else (expect_code,)
    ok = any((c, expect_verdict) in got or (expect_verdict == UNSURE and (c, FAIL) in got) for c in codes)
    if expect_code is None:
        ok = not items
    print(f"{'PASS' if ok else 'MISS'}  {name:<34} expected {expect_code or 'nothing'} {expect_verdict or ''} | "
          f"got {sorted(got) or 'nothing'} | heard: {res[0]['heard'][:60]}", flush=True)
    return ok


def ducked_mix(voice: np.ndarray, spec: dict, flat: bool = False) -> np.ndarray:
    """The voices with a music bed under them: at the film's ducking (README "Music under narration", 9 dB under
    the voice in a gap, 20 dB under while someone speaks) or at one flat level."""
    import tempfile
    sys.path.insert(0, str(HERE.parents[1]))
    import music_ducking
    n = len(voice)
    bed = np.resize(decode_audio(MUSIC), n)
    speech = np.concatenate([voice[int(l["start"] * SR): int(l["end"] * SR)] for l in spec["lines"]])
    bed *= float(np.sqrt(np.mean(speech ** 2)) / np.sqrt(np.mean(bed ** 2))) * 10 ** (-9 / 20)
    if flat:
        return voice + bed * 10 ** (-6 / 20)
    cues = [{"speech": {"start": l["start"], "end": l["end"]}} for l in spec["lines"]]
    with tempfile.TemporaryDirectory() as td:
        env_path = Path(td) / "env.wav"
        music_ducking.envelope(cues, n / SR, -23.0, env_path)
        env = np.resize(decode_audio(env_path, rate=SR), n)
    return voice + bed * env / max(float(env.max()), 1e-6)


def main() -> int:
    if not FILM.exists() or not SPEC.exists() or not MUSIC.exists():
        print(f"SKIP: needs {FILM}, {SPEC} (qa.py spec zhongying …) and {MUSIC}; pass other paths as arguments")
        return 0
    spec = S.load(SPEC)
    film_audio = decode_audio(FILM)
    film_voice = decode_audio(Path(spec["voice_audio"])) if spec.get("voice_audio") else None
    listener = N.Listener(OUT / "_narration_cases" / "asr-cache.json")
    (OUT / "_narration_cases").mkdir(parents=True, exist_ok=True)
    results = []
    modes = [("clean voice + voice track", film_audio, film_voice, None)]
    if film_voice is not None:
        # the same cases with music under the voice and no separate voice track (what most films give the check);
        # a pause the voice makes is filled with the music, ducked, as the mix would have it
        under = ducked_mix(np.zeros_like(film_voice), spec) * 10 ** (-11 / 20)
        modes.append(("music under the voice, no voice track", ducked_mix(film_voice, spec), None, under))
    for label, played, voice, under in modes:
        print(f"\n== {label}")
        cases(spec, played, voice, listener, results, under)
        listener.save()
    if film_voice is not None:
        # the whole film with music under it must not fail more lines than without
        counts = []
        for label, played, voice, _ in modes:
            _, items = N.check(spec, played, voice, listener, log=lambda *_: None)
            counts.append((sum(i["verdict"] == FAIL for i in items), sum(i["verdict"] == UNSURE for i in items)))
            print(f"whole film, {label}: fail {counts[-1][0]}, 拿不准 {counts[-1][1]}")
        listener.save()
        ok = counts[1][0] <= counts[0][0] and counts[1][1] <= counts[0][1] + 2
        results.append(ok)
        print(f"{'PASS' if ok else 'MISS'}  music adds no failures and at most two 拿不准")
    music_cases(spec, film_voice if film_voice is not None else film_audio, results)
    print(f"\n{sum(results)}/{len(results)} cases as expected")
    return 0 if all(results) else 1


def cases(spec, played, voice, listener, results, under=None) -> None:
    def gap(n: int) -> np.ndarray:
        """What a pause the voice makes sounds like in this mix: silence, or the music under the voice."""
        return np.zeros(n, np.float32) if under is None else under[SR * 5: SR * 5 + n].astype(np.float32)

    by = {l["id"]: l for l in spec["lines"]}
    zh = next(l for l in spec["lines"] if l["lang"] == "zh" and l["id"].startswith("verse") and "不" in l["text"])
    zh2 = next(l for l in spec["lines"] if l["lang"] == "zh" and l["id"].startswith("verse") and l is not zh)
    en = next(l for l in spec["lines"] if l["lang"] == "en" and l["id"].startswith("verse")
              and " not " not in f" {l['text'].lower()} " and "n't" not in l["text"] and "’t" not in l["text"])
    num = next((l for l in spec["lines"] if l["lang"] == "en" and any(c.isdigit() for c in l["text"])), None)

    def case(name, line, code, verdict, *, text=None, edit=None, edit_voice=True):
        p, v, l2 = one_line(line, played, voice, text=text)
        if edit:
            p, v = edit(p, v, l2)
        s = {**spec, "lines": [l2]}
        results.append(run(name, s, p, v, listener, code, verdict))

    def words_of(p, l2):
        clip = p[int((l2["start"] - 0.25) * SR): int((l2["end"] + 0.25) * SR)]
        return N.Listener.hear(listener, clip, l2["lang"], (N.ZH_PROMPT if l2["lang"] == "zh" else ""))["words"], l2["start"] - 0.25

    # 0. the untouched lines pass (or at least carry none of the codes tested below)
    case("untouched zh line", zh, None, None)
    case("untouched en line", en, None, None)

    # 1. a phrase said twice (sc07-02 「我们之前聊过批判性素养」 twice)
    def dup(p, v, l2):
        w, off = words_of(p, l2)
        a, b = int((off + w[1]["s"]) * SR), int((off + w[min(4, len(w) - 1)]["e"]) * SR)
        ins = lambda x: None if x is None else np.concatenate([x[:b], gap(int(0.15 * SR)) if x is p else
                                                               np.zeros(int(0.15 * SR), np.float32), x[a:b], x[b:]])
        l2["end"] += (b - a) / SR + 0.15
        return ins(p), ins(v)
    case("phrase said twice (en)", en, ("narration.extra", "narration.repeat"), FAIL, edit=dup)
    case("phrase said twice (zh)", zh2, ("narration.extra", "narration.repeat"), FAIL, edit=dup)

    # 2. a garbled tail after the last word (CosyVoice ~1 s babble: 「先进方」)
    other = by[next(i for i in by if i != zh["id"] and by[i]["lang"] == "zh" and by[i]["id"].startswith("verse"))]
    def tail(p, v, l2):
        src = played[int(other["start"] * SR): int((other["start"] + 0.9) * SR)]
        e = int((l2["end"] + 0.05) * SR)
        put = lambda x: None if x is None else np.concatenate([x[:e], src, x[e:]])
        l2["end"] += 0.9
        return put(p), put(v)
    case("garbled tail (zh)", zh, "narration.extra_edge", FAIL, edit=tail)

    # 3. a wrong number (the voice says 3, the script says 4)
    if num:
        case("wrong number (en)", num, "narration.number", FAIL, text=num["text"].replace("3", "4", 1))
    # 4. a negation lost / added (can't → can)
    case("negation lost (zh 不)", zh, "narration.negation", FAIL, text=zh["text"].replace("不", "", 1))
    words = en["text"].split()
    case("negation added in script (en)", en, "narration.negation", FAIL,
         text=" ".join(words[:2] + ["not"] + words[2:]))

    # 5. a click in the leading silence (zh it01-02: |sample| 650 at 0.62 s)
    def click(p, v, l2):
        k = int((l2["start"] - 0.3) * SR)
        for x in (p, v):
            if x is not None:
                x[k:k + 16] += 0.03 * np.hanning(16).astype(np.float32)
        return p, v
    if voice is not None:
        case("click before the first word", en, "narration.click", UNSURE, edit=click)

    # 6. a word split in two (座头鲸 → 座头 | 鲸): a pause between two characters of one word
    def split(p, v, l2):
        w, off = words_of(p, l2)
        chars = [x for x in w if len(N.CJK_ONLY(x["w"])) == 1]
        text = "".join(N.CJK_ONLY(x["w"]) for x in chars)
        wid = N.zh_words(text)
        k = next(i for i in range(1, len(text) - 1) if wid[i] == wid[i + 1] and wid.count(wid[i]) >= 2)
        t = int((chars[k]["e"] + off) * SR)
        put = lambda x: None if x is None else np.concatenate([x[:t], gap(int(0.5 * SR)) if x is p else
                                                               np.zeros(int(0.5 * SR), np.float32), x[t:]])
        l2["end"] += 0.5
        return put(p), put(v)
    case("word split by a pause (zh)", zh2, "narration.pause", UNSURE, edit=split)


def music_cases(spec, voice, results) -> None:
    """7. the music bed: flat vs ducked (README "Music under narration")."""
    print("\n== music bed")
    mspec = {**spec, "music": True}
    for name, mixd, want in (("flat music bed", ducked_mix(voice, spec, flat=True), FAIL),
                             ("ducked music bed", ducked_mix(voice, spec), None)):
        info, found = mix.ducking(mixd, mspec)
        verdicts = {f["verdict"] for f in found}
        ok = (want in verdicts) if want else not found
        results.append(ok)
        print(f"{'PASS' if ok else 'MISS'}  {name:<34} median rise {info.get('median_rise_db')} dB over {info.get('gaps')} gaps"
              f" | {[f['title'] for f in found]}", flush=True)


if __name__ == "__main__":
    sys.exit(main())
