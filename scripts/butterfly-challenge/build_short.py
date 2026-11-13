"""Time the two vertical shorts (docs/butterfly-challenge/shorts.md): timeline, en/zh mixes and SRTs per short.

  /Users/yqin/repo/playground/lucas-academy-video/.venv-align/bin/python scripts/butterfly-challenge/build_short.py

One round of the film each — the two groups that fooled both AIs. Like the film: one picture for both voice tracks,
every line in a slot as long as its longer take, both languages starting at the slot's start; the Chopin waltz from
its opening, ducked under the voice (music_ducking). Writes public/butterfly-challenge/shorts/<name>.json and
out/butterfly-challenge/shorts/<name>/{mix.en.wav, mix.zh.wav, <name>.en.srt, <name>.zh-Hans.srt}.
"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
_argv, sys.argv = sys.argv, sys.argv[:1]
import build_timeline as bt  # noqa: E402  (film helpers: mit, en_cues, zh_cues, pair_data, USABLE, music)
import narrate  # noqa: E402
import narrate_shorts as ns  # noqa: E402
sys.argv = _argv

ROOT = bt.ROOT
PUB = ROOT / "public/butterfly-challenge/shorts"
OUT = ROOT / "out/butterfly-challenge/shorts"
SR, FPS = bt.SR, 30
SHORTS = {  # name: (pair, reveal line, about line)
    "blue-mormon": (2, "sc02-01", "sc02-02"),
    "leopard": (4, "sh04-01", "sc04-02"),
}
LEAD, COUNT, REVEAL_LEAD, REVEAL_TAIL, CLIP_LEAD, CLIP_TAIL, END = 0.6, 5.0, 0.9, 0.8, 0.8, 1.6, 0.6


def captions(lid: str) -> dict:
    """A line's caption in each language: the film's (zh-edit / en-edit) or a short's own (narrate_shorts)."""
    if lid in ns.LINES:
        return {lang: ns.LINES[lid][lang][0] for lang in ("zh", "en")}
    zh = {l["id"]: l["caption"] for l in narrate.load(1.1, 1.1)}
    en = {l["id"]: l["caption"] for l in narrate.load_en(1.1)}
    strip = lambda s: s.replace("【公布】", "").replace("【reveal】", "")  # noqa: E731
    return {"zh": strip(zh[lid]), "en": strip(en[lid])}


def build(name: str, n: int, reveal_id: str, about_id: str) -> None:
    p = next(x for x in bt.pair_data() if x["n"] == n)
    audio = {lang: np.zeros(int(90 * SR), np.float32) for lang in ("en", "zh")}
    placed = {"en": {}, "zh": {}}
    slots = {}

    def put(lid, t):
        ends = []
        for lang in ("en", "zh"):
            y = bt.mit.decode(narrate.takes_dir("louise", lang) / "s1.10" / f"{lid}.wav", trim=True)
            i = int(t * SR)
            audio[lang][i:i + len(y)] += y
            placed[lang][lid] = (round(t, 3), round(t + len(y) / SR, 3))
            ends.append(t + len(y) / SR)
        slots[lid] = (round(t, 3), round(max(ends), 3))
        return max(ends)

    e = put("sh-intro", LEAD)
    count_at = e + 0.5
    reveal = count_at + COUNT
    clip = max(reveal + 3.2, put(reveal_id, reveal + REVEAL_LEAD) + REVEAL_TAIL)
    end = max(clip + 5.0, put(about_id, clip + CLIP_LEAD) + CLIP_TAIL)
    total = end + END
    need = end - clip + 0.5
    a, b = bt.USABLE[p["key"]]
    rate = 1.0 if b - a >= need else max(0.5 if p["fps"] >= 50 else 0.8, (b - a) / need)
    plays = (b - a) / rate
    hold = round(plays, 3) if plays < need else None
    still = f"pairs/{n:02d}-{p['real']}.jpg" if hold is not None and need - hold > 3.0 else None
    tl = {"fps": FPS, "durationSeconds": round(total, 3), "pair": p, "count": round(count_at, 3), "reveal": round(reveal, 3),
          "clip": round(clip, 3), "end": round(end, 3),
          "video": {"src": f"clips/{p['key']}.mp4", "from": a, "rate": round(rate, 4), "hold": hold,
                    "last": f"clips/{p['key']}.last.jpg", "still": still},
          "lines": {k: {"start": s, "end": t} for k, (s, t) in slots.items()}}
    out = OUT / name
    out.mkdir(parents=True, exist_ok=True)
    nsamp = int(total * SR)
    bed = bt.mit.ffread(bt.MUSIC)[:nsamp]
    bed *= 10 ** ((bt.BED_LUFS - bt.mit.lufs(bed)) / 20)
    for lang in ("en", "zh"):
        cues = [{"speech": {"start": s, "end": t}} for s, t in placed[lang].values()]
        bt.music_ducking.envelope(cues, total, bt.BED_LUFS, out / f"env.{lang}.wav")
        env = bt.mit.ffread(out / f"env.{lang}.wav")
        m = min(len(env), nsamp, len(bed))
        mix = audio[lang][:m] + bed[:m] * env[:m]
        mix *= 10 ** ((bt.FINAL_LUFS - bt.mit.lufs(mix)) / 20)
        sf.write(out / f"mix.{lang}.raw.wav", mix, SR, subtype="FLOAT")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(out / f"mix.{lang}.raw.wav"), "-af",
                        f"alimiter=limit={10 ** (bt.FINAL_TP / 20):.4f}:attack=5:release=60:level=false",
                        "-c:a", "pcm_s24le", str(out / f"mix.{lang}.wav")], check=True)
    # captions on the English track's timing (every line starts at the same moment in the Chinese track)
    en_srt, zh_srt = [], []
    for lid, (s, t) in sorted(placed["en"].items(), key=lambda kv: kv[1][0]):
        c = captions(lid)
        en_srt += list(bt.en_cues(c["en"], s, t))
        zh_srt += list(bt.zh_cues(c["zh"], s, t))
    for tag, cues_ in (("en", en_srt), ("zh-Hans", zh_srt)):
        (out / f"{name}.{tag}.srt").write_text(
            "".join(f"{k}\n{bt.mit.stamp(a)} --> {bt.mit.stamp(b)}\n{s}\n\n" for k, (a, b, s) in enumerate(cues_, 1)))
    PUB.mkdir(parents=True, exist_ok=True)
    (PUB / f"{name}.json").write_text(json.dumps(tl, ensure_ascii=False, indent=1))
    print(f"{name}: {total:.1f} s (count {count_at:.1f}, reveal {reveal:.1f}, clip {clip:.1f}); video rate {rate}, hold {hold}, still {still}")


if __name__ == "__main__":
    for name, (n, r, about) in SHORTS.items():
        build(name, n, r, about)
