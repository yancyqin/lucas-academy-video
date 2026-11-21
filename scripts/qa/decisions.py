"""Yancy's 通过 / 重配 on the 拿不准 items (decisions.json in a report folder), and which of them still hold.

A decision on a narration line is about one recording. It is saved together with that line's take print
(narration.take_print: a coarse picture of how the recording sounds) and holds only while the line still plays that
recording. The same take moved on the timeline or encoded again keeps its approval; another take of the same words
— even one Whisper writes the same way, with the same length — is asked again.

A byte hash cannot do this: the four 中英阅读 cuts reuse one take of their opening line, and its samples differ in
every film (another offset, another AAC encode). Measured on real voices, 2026-11-20:
- the same take scores 1.00 across those four films and against each film's AAC mix, and ≥ 0.93 with the line's
  times moved by ±0.1 s or with music under it (86 lines);
- another recording of a line scores ≤ 0.68, as recorded and when stretched to the same length: 24 real retakes
  by the same voices, 5 of them of exactly the same words (≤ 0.66), the rest with a word or two edited.
The limit is 0.90, nearer the same-take side on purpose: a wrong "another take" costs one more listen, a wrong
"same take" lets a recording through unheard. The print is coarse — one recording with its pitch or tempo changed
by a few percent still scores 0.93–0.99, so a lightly processed copy counts as the same take.
tests/test_rules.py repeats both directions.

No numpy in this file: the gate has to run on any python3.
"""
from __future__ import annotations

import base64
import datetime as dt
import hashlib
import json
import math
from pathlib import Path

SAME_TAKE = 0.90        # similarity (0–1) from which two prints are one recording
LAGS = 8                # frames either way (40 ms each) one print may sit off the other


def report_id(report: dict) -> str:
    """Names one run of the checks. The listening page carries it, so a page left open from before the film was
    checked again cannot approve the new recordings with clips of the old ones."""
    parts = (report.get("sha256"), report.get("audio_sha256"), report.get("created"))
    return hashlib.sha1("\0".join(str(p) for p in parts).encode()).hexdigest()[:12]


def load(folder: Path) -> dict:
    p = Path(folder) / "decisions.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def _save(folder: Path, all_: dict) -> None:
    path = Path(folder) / "decisions.json"
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(all_, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    tmp.replace(path)


def _rows(print_: str | None) -> tuple[int, bytes] | None:
    try:
        version, bands, data = (print_ or "").split(":", 2)
        return (int(bands), base64.b64decode(data)) if version == "t1" and int(bands) > 0 else None
    except (ValueError, TypeError):
        return None


def _corr(x: bytes, y: bytes) -> float:
    n = len(x)
    if n < 2:
        return 0.0
    mx, my = sum(x) / n, sum(y) / n
    sxy = sxx = syy = 0.0
    for a, b in zip(x, y):
        da, db = a - mx, b - my
        sxy += da * db
        sxx += da * da
        syy += db * db
    return sxy / math.sqrt(sxx * syy) if sxx > 0 and syy > 0 else 0.0


def similarity(a: str | None, b: str | None) -> float:
    """How alike two take prints are: 1 = the same recording, around 0 = unrelated; 0 when either is missing.
    One print is slid over the other (a breath kept or cut at either end moves where a print starts), and the two
    must overlap almost entirely: a take that is clearly longer or shorter is another take."""
    ra, rb = _rows(a), _rows(b)
    if not ra or not rb or ra[0] != rb[0]:
        return 0.0
    bands, x, y = ra[0], ra[1], rb[1]
    fa, fb = len(x) // bands, len(y) // bands
    if min(fa, fb) < 5 or abs(fa - fb) > max(LAGS, 0.1 * max(fa, fb)):
        return 0.0
    best = 0.0
    for k in range(-LAGS, LAGS + 1):
        u, v = (x[k * bands:], y) if k >= 0 else (x, y[-k * bands:])
        m = min(len(u), len(v))
        if m >= 0.85 * min(len(x), len(y)):
            best = max(best, _corr(u[:m], v[:m]))
    return best


def same_take(a: str | None, b: str | None) -> bool:
    return similarity(a, b) >= SAME_TAKE


def holds(item: dict, decision: dict | None) -> bool:
    """Does this saved decision still apply to this finding? A narration line carries a take print: the decision
    must have been given on the same recording."""
    if not decision or decision.get("decision") not in ("pass", "redo"):
        return False
    return same_take(item["take"], decision.get("take")) if item.get("take") else True


def decision_for(item: dict, decisions: dict) -> str | None:
    d = decisions.get(item["key"])
    return d["decision"] if holds(item, d) else None


def record(folder: Path, key: str, decision: str | None, note: str = "", title: str = "",
           seen: str | None = None) -> dict:
    """Save (or with decision None, withdraw) one decision. The take print comes from the folder's own report.json,
    never from the caller: the decision is tied to what the report says was checked. `seen` is the report_id the
    decider was looking at; KeyError when that is not the folder's current report, or when the report has no such
    finding (both: a page left open from before the last check)."""
    folder = Path(folder)
    all_ = load(folder)
    if decision is None:
        all_.pop(key, None)
    else:
        if decision not in ("pass", "redo"):
            raise ValueError(f"decision must be pass or redo, not {decision!r}")
        entry = {"decision": decision, "note": (note or "").strip(), "title": title or "",
                 "at": dt.datetime.now().isoformat(timespec="seconds")}
        report = folder / "report.json"
        if report.exists():
            current = json.loads(report.read_text(encoding="utf-8"))
            if seen is not None and seen != report_id(current):
                raise KeyError(key)
            found = next((i for i in current["items"] if i["key"] == key), None)
            if found is None:
                raise KeyError(key)
            entry["title"] = entry["title"] or found.get("title", "")
            if found.get("take"):
                entry["take"] = found["take"]
        all_[key] = entry
    _save(folder, all_)
    return all_


def prune(folder: Path, report: dict) -> list[dict]:
    """After a new check: drop the decisions whose line now plays another recording, so the listening page and the
    gate agree that they are open again. Returns what was dropped."""
    all_ = load(folder)
    by_key = {i["key"]: i for i in report["items"]}
    gone = [dict(all_[k], key=k) for k in list(all_) if k in by_key and not holds(by_key[k], all_[k])]
    if gone:
        for g in gone:
            all_.pop(g["key"])
        _save(folder, all_)
    return gone
