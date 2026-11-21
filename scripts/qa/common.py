"""Shared helpers for the automatic video checks (scripts/qa, README "Automatic checks")."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "out" / "qa"            # reports go here by default (git-ignored), never next to someone else's render

PASS, UNSURE, FAIL = "pass", "unsure", "fail"
RANK = {PASS: 0, UNSURE: 1, FAIL: 2}
LABEL = {PASS: "通过", UNSURE: "拿不准", FAIL: "不通过"}


def sha256(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while block := f.read(chunk):
            h.update(block)
    return h.hexdigest()


def short_hash(*parts) -> str:
    h = hashlib.sha1()
    for p in parts:
        h.update(p if isinstance(p, bytes) else str(p).encode())
        h.update(b"\0")
    return h.hexdigest()[:12]


def ffprobe(path: Path) -> dict:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)],
                         capture_output=True, text=True, check=True).stdout
    return json.loads(out)


def decode_audio(path: Path, rate: int = 16000, stream: str = "a:0"):
    """The whole audio track as mono float32 at `rate` (what the viewer hears, downmixed)."""
    import numpy as np
    pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-map", f"0:{stream}", "-ac", "1", "-ar", str(rate),
                          "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(pcm, np.float32).copy()


def db(x: float) -> float:
    import math
    return 20 * math.log10(max(float(x), 1e-9))


def rms_db(x) -> float:
    import numpy as np
    return db(np.sqrt(np.mean(np.square(x, dtype=np.float64)))) if len(x) else -180.0


def item(area: str, verdict: str, code: str, title: str, detail: str = "", *, t0: float | None = None,
         t1: float | None = None, key: str | None = None, **extra) -> dict:
    """One finding. `code` is machine-readable (e.g. narration.extra), `title`/`detail` are for Yancy (Chinese)."""
    d = {"area": area, "verdict": verdict, "code": code, "title": title, "detail": detail}
    if t0 is not None:
        d["t0"] = round(float(t0), 3)
    if t1 is not None:
        d["t1"] = round(float(t1), 3)
    d["key"] = key or short_hash(area, code, title, detail, d.get("t0"), d.get("t1"))
    d.update(extra)
    return d


def worst(verdicts) -> str:
    return max(verdicts, key=lambda v: RANK[v], default=PASS)


def mmss(t: float) -> str:
    m, s = divmod(max(0.0, float(t)), 60)
    return f"{int(m)}:{s:04.1f}"
