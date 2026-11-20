"""混音: loudness of the whole film, and whether the music really gives way to the voices (README "Music under
narration": 20 dB under a voice, 9 dB under in any gap of 0.8 s or more, 0.35 s attack, 0.8 s release)."""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

import numpy as np

from common import FAIL, PASS, UNSURE, item, rms_db

SR = 16000
DUCK = {"min_gap": 1.4,        # only gaps long enough for the music to come all the way back (0.8 + 0.35 + margin)
        "fail_db": 3.0,        # music in the gap less than this above the music right after the voice: flat bed
        "unsure_db": 5.5}      # the envelope's own difference is ~9–10 dB


def loudness(path: Path, spec: dict) -> tuple[dict, list]:
    err = subprocess.run(["ffmpeg", "-nostats", "-hide_banner", "-i", str(path), "-map", "0:a:0",
                          "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
    summary = err[err.rfind("Summary:"):]
    i = float(re.search(r"I:\s+(-?[\d.]+) LUFS", summary)[1])
    lra = float(re.search(r"LRA:\s+(-?[\d.]+) LU", summary)[1])
    tp = float(re.search(r"Peak:\s+(-?[\d.]+|-inf) dBFS", summary)[1])
    lo = spec["loudness"]
    found = []
    if abs(i - lo["lufs"]) > lo["tol"]:
        found.append(item("mix", FAIL, "mix.lufs", f"整体响度 {i:.1f} LUFS，标准是 {lo['lufs']:.0f}±{lo['tol']}",
                          "用 loudnorm 或增益调到标准", key="mix.lufs"))
    if tp > lo["tp_max"]:
        found.append(item("mix", FAIL, "mix.true_peak", f"真峰值 {tp:.1f} dBTP，上限 {lo['tp_max']:.1f}",
                          "加限幅（alimiter）", key="mix.true_peak"))
    return {"lufs": i, "lra": lra, "true_peak": tp}, found


def ducking(played: np.ndarray, spec: dict) -> tuple[dict, list]:
    """Mix-only measurement: in each long gap, the music after it has risen (middle of the gap) against the music
    right after the voice stopped (still ducked). Silence on both sides = no music there (skipped)."""
    if not spec.get("music") or not spec["lines"]:
        return {"skipped": "no music bed in the spec"}, []
    spans = []
    for line in spec["lines"]:
        a, b = line.get("speech", (line["start"], line["end"]))
        if spans and a - spans[-1][1] < 0.8:
            spans[-1][1] = max(spans[-1][1], b)
        else:
            spans.append([a, b])
    rows = []
    for (a0, b0), (a1, _) in zip(spans, spans[1:]):
        if a1 - b0 < DUCK["min_gap"]:
            continue
        after = played[int((b0 + 0.08) * SR): int((b0 + 0.22) * SR)]
        mid_a, mid_b = b0 + 0.85, a1 - 0.4
        if mid_b - mid_a < 0.15:
            continue
        mid = played[int(mid_a * SR): int(mid_b * SR)]
        r_after, r_mid = rms_db(after), rms_db(mid)
        if r_mid < -60 and r_after < -60:
            continue
        rows.append({"gap": [round(b0, 2), round(a1, 2)], "after_voice_db": round(r_after, 1),
                     "mid_gap_db": round(r_mid, 1), "rise_db": round(r_mid - r_after, 1)})
    found = []
    if not rows:
        return {"gaps": 0}, found
    rises = np.array([r["rise_db"] for r in rows])
    med = float(np.median(rises))
    flat = [r for r in rows if r["rise_db"] < DUCK["fail_db"]]
    approx = any(l.get("from_captions") for l in spec["lines"])
    if med < DUCK["fail_db"]:
        found.append(item("mix", UNSURE if approx else FAIL, "mix.ducking",
                          f"背景音乐没有随人声压低再抬起（空隙里只抬高 {med:.1f} dB）",
                          f"量了 {len(rows)} 个空隙；用 scripts/music_ducking.py 的包络重新混音", key="mix.ducking"))
    elif med < DUCK["unsure_db"] or len(flat) > max(1, len(rows) // 5):
        found.append(item("mix", UNSURE, "mix.ducking", f"音乐压低不明显（空隙里中位抬高 {med:.1f} dB）",
                          "、".join(f"{r['gap'][0]:.1f}s" for r in flat[:8]), key="mix.ducking",
                          t0=flat[0]["gap"][0] - 2 if flat else None, t1=flat[0]["gap"][1] + 1 if flat else None))
    return {"gaps": len(rows), "median_rise_db": round(med, 1), "rows": rows}, found
