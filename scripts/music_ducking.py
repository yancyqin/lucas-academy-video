"""The project's default for music under narration (owner, 2026-10-16; README "Music under narration").

The music audibly makes room whenever a voice comes in and comes back as soon as it stops: in every gap of
MIN_GAP seconds or more, not only in long pauses. whole-person-01's envelope (used by Fun Informatics 1 and 2)
raised the music only in pauses of 2.5 s or more, so through a stretch of narration it sat at one flat level
and never seemed to give way; the owner heard that on Fun Informatics 3 and asked for this as the default.

A film's timeline builder swaps it in for the shared envelope:

    sys.path.insert(0, str(ROOT / "scripts"))
    import music_ducking
    wp.music_envelope = music_ducking.envelope            # or a lambda passing quiet=[(start, end), ...]

Levels are relative to the voice, which every builder levels to LINE_LUFS before mixing.
"""
from __future__ import annotations

import array
import math
import subprocess
from pathlib import Path

LINE_LUFS = -23.0   # the level every narration line is brought to (whole-person-01)
UNDER_DB = -20.0    # music under a voice, dB re the voice
GAP_DB = -9.0       # music in a gap between voices, dB re the voice
MIN_GAP = 0.8       # shorter gaps stay down, so the music does not pump between phrases
ATTACK = 0.35       # seconds the music takes to step back before a voice starts
RELEASE = 0.8       # seconds it takes to come back after a voice ends
FADE_IN, FADE_OUT = 2.0, 5.0  # the film's first and last seconds
QUIET_FADE = (0.6, 0.8)       # into and out of a stretch with no music at all
ENV_RATE = 1000


def _smooth(x: float) -> float:
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def envelope(cues: list, total: float, bed_lufs: float, path: Path, quiet=()) -> None:
    """The music bed's gain over time, as 32-bit float (it can exceed unity for a quiet bed).

    cues: anything with ["speech"]["start"/"end"], voices and other sounds the music should make room for.
    quiet: (start, end) stretches with no music at all, e.g. a listening test.
    """
    spans = []
    for a, b in sorted((c["speech"]["start"], c["speech"]["end"]) for c in cues):
        if spans and a - spans[-1][1] < MIN_GAP:
            spans[-1][1] = max(spans[-1][1], b)
        else:
            spans.append([a, b])
    n = math.ceil(total * ENV_RATE)
    duck = [0.0] * n
    for a, b in spans:
        lo, hi = max(0, round((a - ATTACK) * ENV_RATE)), min(n, round((b + RELEASE) * ENV_RATE))
        for k in range(lo, hi):
            t = k / ENV_RATE
            d = 1.0 if a <= t <= b else _smooth((t - (a - ATTACK)) / ATTACK) if t < a else _smooth(1 - (t - b) / RELEASE)
            if d > duck[k]:
                duck[k] = d
    base = LINE_LUFS - bed_lufs
    env = array.array("f", [0.0] * n)
    for k in range(n):
        level = GAP_DB + (UNDER_DB - GAP_DB) * duck[k]  # moves in dB
        edge = min(1.0, k / (FADE_IN * ENV_RATE), (n - k) / (FADE_OUT * ENV_RATE))
        env[k] = 10 ** ((base + level) / 20) * edge
    for a, b in quiet:
        for k in range(max(0, round((a - QUIET_FADE[0]) * ENV_RATE)), min(n, round((b + QUIET_FADE[1]) * ENV_RATE))):
            t = k / ENV_RATE
            g = min(1.0, max(0.0, (a - t) / QUIET_FADE[0]), max(0.0, (t - b) / QUIET_FADE[1]))
            env[k] *= g
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(ENV_RATE), "-ac", "1", "-i", "-",
                    "-c:a", "pcm_f32le", str(path)], input=env.tobytes(), check=True)
