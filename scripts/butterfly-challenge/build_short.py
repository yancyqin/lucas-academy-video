"""Time the two vertical shorts (docs/butterfly-challenge/shorts.md): timeline and music mix per short.

  /Users/yqin/repo/playground/lucas-academy-video/.venv-align/bin/python scripts/butterfly-challenge/build_short.py

v2 (Yancy 2026-11-16: 「节奏太慢 节奏要紧凑很多很多！不要那么多废话，就是猜，猜完展示结果（视频）」): no voice, two
rounds a short. Each round: the two pictures, a 3-2-1 count, the reveal (green ✓ on the real one, red ✗ on the AI one,
each model's robot on the picture it picked), then the real butterfly's video. Music only — the Chopin waltz from its
first note — so one MP4 serves both languages and there are no captions. The reveals, cuts and round changes land on
the waltz's beats (BEATS, measured once with librosa in .venv-lipsync; this venv has no librosa).
Writes public/butterfly-challenge/shorts/<name>.json and out/butterfly-challenge/shorts/<name>/mix.wav.
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
import build_timeline as bt  # noqa: E402  (film helpers: mit, pair_data, USABLE, MUSIC, loudness targets)
sys.argv = _argv

ROOT = bt.ROOT
PUB = ROOT / "public/butterfly-challenge/shorts"
OUT = ROOT / "out/butterfly-challenge/shorts"
SR, FPS = bt.SR, 30

# name: rounds as (pair, where the real video starts in its clip, s). Yancy 11-16: 「一条两个蝴蝶，另一条要带上 glasswing
# 蝴蝶 再加个别的」 → the two groups that fooled both AIs; the glasswing + group 7 (Red-spotted Purple: Fable fooled,
# and its clip opens its wings at 22-26 s; the peacock clip of group 5 barely moves, so not that one).
SHORTS = {
    "mormon-leopard": [(2, 0.0), (4, 0.0)],
    "glasswing-purple": [(1, 3.0), (7, 21.6)],
}
# Yancy 11-16 on the 15.8 s cut: 「这也太短了吧 蝴蝶飞的视频可以长一点」 → the real video 3.5 → 7 s a round. A clip with less
# usable footage than that plays a little slower (never below RATE_FLOOR) rather than holding a frame.
COUNT, REVEAL_HOLD, CLIP_LEN, TAIL_FADE, RATE_FLOOR = 3.0, 1.4, 7.0, 0.4, 0.8

# beats of the waltz's opening (librosa beat_track on the FLAC, s); the music starts MUSIC_FROM into the file, just
# before the first note (onset 0.42 s)
BEATS = [0.44, 0.91, 1.37, 1.97, 2.44, 2.9, 3.41, 3.95, 4.41, 4.88, 5.39, 5.9, 6.41, 6.92, 7.43, 7.94, 8.41, 8.89, 9.43,
         9.91, 10.4, 10.94, 11.4, 11.89, 12.38, 12.84, 13.31, 13.79, 14.3, 14.77, 15.28, 15.72, 16.18, 16.7, 17.16, 17.65,
         18.16, 18.67, 19.09, 19.5, 19.97, 20.46, 20.92, 21.43, 21.94, 22.43, 22.96, 23.43, 23.92, 24.45, 24.98,
         25.43, 25.87, 26.33, 26.8, 27.28, 27.79, 28.26, 28.72, 29.16, 29.61, 30.07, 30.53, 31.0, 31.46, 31.9, 32.39,
         32.83, 33.3, 33.83, 34.3, 34.78, 35.29, 35.76, 36.2, 36.66, 37.13, 37.59, 38.08, 38.55, 38.99]
MUSIC_FROM = 0.40


def on_beat(t: float) -> float:
    """The beat (in the short's time) nearest to t."""
    return min((b - MUSIC_FROM for b in BEATS), key=lambda b: abs(b - t))


def build(name: str, rounds: list) -> None:
    pairs = {p["n"]: p for p in bt.pair_data()}
    t, out_rounds = 0.0, []
    for n, src_from in rounds:
        p = pairs[n]
        start = round(t, 3)
        reveal = on_beat(start + COUNT)
        clip = on_beat(reveal + REVEAL_HOLD)
        end = on_beat(clip + CLIP_LEN)
        a, b = bt.USABLE[p["key"]]
        need = end + 0.3 - clip  # the video stays up while the next round's pictures fade in
        rate = min(1.0, (b - src_from) / need)
        assert a <= src_from and rate >= RATE_FLOOR, f"pair {n}: {b - src_from:.2f} s usable from {src_from} s, {need:.2f} s needed"
        out_rounds.append({"pair": p, "start": start, "reveal": round(reveal, 3), "clip": round(clip, 3), "end": round(end, 3),
                           "video": {"src": f"clips/{p['key']}.mp4", "from": src_from, "rate": round(rate, 4)}})
        t = end
    total = round(t, 3)
    tl = {"fps": FPS, "durationSeconds": total, "rounds": out_rounds}

    out = OUT / name
    out.mkdir(parents=True, exist_ok=True)
    nsamp = int(total * SR)
    # stereo here (the film's bed is mono under the voice; with music alone the piano keeps its width)
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(MUSIC_FROM), "-i", str(bt.MUSIC), "-t", str(total),
                          "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True).stdout
    bed = np.frombuffer(raw, np.float32).reshape(-1, 2)[:nsamp].copy()
    fade = int(TAIL_FADE * SR)
    bed[-fade:] *= np.linspace(1, 0, fade)[:, None]  # the waltz goes on; fade it over the last TAIL_FADE s
    bed *= 10 ** ((bt.FINAL_LUFS - bt.mit.lufs(bed)) / 20)
    sf.write(out / "mix.raw.wav", bed, SR, subtype="FLOAT")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(out / "mix.raw.wav"), "-af",
                    f"alimiter=limit={10 ** (bt.FINAL_TP / 20):.4f}:attack=5:release=60:level=false",
                    "-c:a", "pcm_s24le", str(out / "mix.wav")], check=True)
    PUB.mkdir(parents=True, exist_ok=True)
    (PUB / f"{name}.json").write_text(json.dumps(tl, ensure_ascii=False, indent=1))
    plan = "; ".join(f"#{r['pair']['n']} {r['start']:.2f}/{r['reveal']:.2f}/{r['clip']:.2f}/{r['end']:.2f} ×{r['video']['rate']}"
                     for r in out_rounds)
    print(f"{name}: {total:.2f} s — round start/reveal/video/end: {plan}")


if __name__ == "__main__":
    for name, rounds in SHORTS.items():
        build(name, rounds)
