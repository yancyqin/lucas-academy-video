"""The QA spec: what a film is supposed to contain, so the checks know what to compare against.

A film's pipeline writes one `qa-spec.json` next to its timeline (or an adapter here makes one):

{
  "film": "who-woke-you",
  "kind": "narrated",                 # narrated | music | short
  "lines": [                          # every spoken line, on the FILM's clock (seconds)
    {"id": "intro-zh", "lang": "zh", "start": 1.70, "end": 10.07,
     "text": "学习语言最好的方式是朗读。…",   # what the voice was asked to say (the SPOKEN text)
     "caption": "…",                  # optional: the caption text, also accepted as a match
     "question": false}               # optional: a question put to the audience → its tone goes to Yancy
  ],
  "voice_audio": "path/narration.wav",  # required with music: true; voices on the film's clock
  "music_source": "path/music-raw.wav", # un-ducked music, on the entire film's clock
  "music_audio": "path/music-mixed.wav",# the actual added music stem, after fades and ducking
  "music": true,                      # is there a music bed that must duck under the voices?
  "loudness": {"lufs": -16, "tol": 0.5, "tp_max": -1.0},
  "format": {"width": 1920, "height": 1080, "fps": 30, "duration": 209.32, "tol": 0.15},
  "captions": [{"path": "film.zh-Hans.srt", "lang": "zh"}, {"path": "film.en.srt", "lang": "en"}],
  "shots": [{"id": "G1", "start": 20.86, "end": 31.5, "kind": "footage", "static": false}],
                                      # kind: footage (real/Muse/MiniMax video: must move), painting, still, title,
                                      # animation; static: true = nothing may move at all
                                      # camera_motion: false only when a global camera model does not apply
                                      # (drawn strokes/icons); "review" for foreground-dominated camera estimates.
                                      # Neither disables black/glitch/static/frozen-footage checks.
  "transitions": [[31.5, 33.0]],      # dissolves/fades (picture checks skip them)
  "planned_black": [[0, 0.5]],        # black that is meant to be there
  "prompt": {"zh": "孟浩然", "en": "Haoran"},   # names to bias Whisper's spelling (use sparingly)
  "names": ["孟浩然", "Meng Haoran"],  # names and titles: a difference there is 拿不准, never a fail on its own
  (a line may also carry "group": lines are paced against the median of their group, e.g. verse vs title;
   and "free_pauses": true for poetry/scripture read aloud, where a pause without punctuation is the reader's choice)
  "risky": ["落", "刹"]               # extra words/characters this film should double-check
}

Narrated films with music also supply `music_source` (the un-ducked full-timeline
track) and `music_audio` (the exact music stem added to `voice_audio`). Music covers
the entire film by default. Any `music_exceptions` entry needs start, end, reason
and actual owner_evidence; never invent an exception for a test or story.

Paths are relative to the spec file. Required evidence depends on kind and music;
missing required music stems fail rather than silently skipping the check.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

DEFAULT_LOUDNESS = {"narrated": {"lufs": -16.0, "tol": 0.5, "tp_max": -1.0},
                    "short": {"lufs": -16.0, "tol": 1.0, "tp_max": -1.0},
                    "music": {"lufs": -18.0, "tol": 0.7, "tp_max": -1.0}}


def load(path: Path) -> dict:
    spec = json.loads(Path(path).read_text(encoding="utf-8"))
    base = Path(path).resolve().parent
    for key in ("voice_audio", "music_audio", "music_source"):
        if spec.get(key):
            spec[key] = str((base / spec[key]).resolve())
    for c in spec.get("captions", []):
        c["path"] = str((base / c["path"]).resolve())
    return normalise(spec)


def normalise(spec: dict) -> dict:
    spec.setdefault("_music_declared", "music" in spec)   # the gate wants music: true/false said out loud
    spec.setdefault("kind", "narrated")
    spec.setdefault("lines", [])
    spec.setdefault("music", False)
    lo = dict(DEFAULT_LOUDNESS.get(spec["kind"], DEFAULT_LOUDNESS["narrated"]))
    lo.update(spec.get("loudness") or {})
    spec["loudness"] = lo
    for i, line in enumerate(spec["lines"]):
        line.setdefault("id", f"L{i + 1:03d}")
        if "question" not in line:
            line["question"] = False
    spec["lines"].sort(key=lambda l: l["start"])
    return spec


def save(spec: dict, path: Path) -> None:
    clean = {k: v for k, v in spec.items() if not k.startswith("_")}
    Path(path).write_text(json.dumps(clean, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------------------------------------------
# Adapters


def from_zhongying(timeline: Path) -> dict:
    """中英阅读 (scripts/zhong-ying/build_timeline.py): cues carry the script's own tokens (align.py forces the
    known text), so joining them gives the text the voice was asked to read. No music; narration.wav is the
    voices on the film's clock."""
    timeline = Path(timeline).resolve()
    t = json.loads(timeline.read_text(encoding="utf-8"))
    lines, seen = [], {}
    for c in t["cues"]:
        words = [w["text"] for w in c["words"]]
        # A verse's line breaks are places the reader pauses: keep them (as "\n", a pause mark).
        if c["lang"] == "zh":
            text = "".join(words).strip()
        else:
            text = re.sub(r" *\n *", "\n", re.sub(r"[ \t]+", " ", " ".join(words))).strip()
        base = "-".join(str(p) for p in (c["kind"], c.get("work"), c.get("unit"), c["lang"]) if p is not None)
        seen[base] = seen.get(base, 0) + 1
        cid = base if seen[base] == 1 else f"{base}-{seen[base]}"
        a, b = c["speech"]
        lines.append({"id": cid, "lang": c["lang"], "start": a, "end": b, "text": text, "group": c["kind"],
                      "free_pauses": c["kind"] == "verse",   # poems and scripture read aloud pause where they like
                      # the series' own questions to the viewer (intro/closing/subscribe), not a poem's
                      "question": c["kind"] in ("intro", "closing", "subscribe") and bool(re.search(r"[？?]", text))})
    names = set()
    for w in t.get("works", []):
        for field in ("title", "by"):
            for lang in ("zh", "en"):
                v = (w.get(field) or {}).get(lang, "")
                parts = re.split(r"[\s·・,，、:：]+", v) if lang == "zh" else re.split(r"\s*[·,]\s*", v)
                names.update(p for p in parts if len(p) >= 2 and p.lower() not in ("tang dynasty", "song dynasty"))
    # Footage = where a MiniMax/Muse clip really plays (it must move). Without a clip (`minimax` null) the clip span
    # shows the painting, which may stand still.
    shots, transitions = [], []
    for w in t.get("works", []):
        op = w.get("opening") or {}
        if op.get("until") is not None and op.get("fade"):
            transitions.append([op["until"] - op["fade"], op["until"]])
        if not w.get("minimax"):
            continue
        if op.get("file"):
            shots.append({"id": f"{w['id']}-open", "start": w["start"], "end": op["until"] - op.get("fade", 0),
                          "kind": "footage"})
        if w.get("clip_span"):
            a, b = w["clip_span"]
            shots.append({"id": f"{w['id']}-clip", "start": a, "end": b, "kind": "footage"})
    recap = t.get("recap") or {}
    clips = recap.get("clips", [])
    for k, c in enumerate(clips):
        end = clips[k + 1]["from"] if k + 1 < len(clips) else recap["end"]
        if c.get("file", "").startswith("clip-"):
            shots.append({"id": f"recap-{c['work']}", "start": c["from"], "end": end, "kind": "footage"})
        if k:
            f = recap.get("fade", 1.0)
            transitions.append([c["from"] - f, c["from"] + f])
    if recap:
        f = recap.get("fade", 1.0)
        transitions.append([recap["end"] - f, recap["end"] + f])
    spec = {"film": t.get("film", timeline.parent.name), "kind": "narrated", "lines": lines, "music": False,
            "format": {"width": 1920, "height": 1080, "fps": t.get("fps", 30), "duration": t.get("durationSeconds"),
                       "tol": 0.15},
            "shots": shots, "transitions": transitions, "names": sorted(names)}
    voice = timeline.parent / "narration.wav"
    if voice.exists():
        spec["voice_audio"] = str(voice)
    return normalise(spec)


SRT_TIME = re.compile(r"(\d+):(\d+):(\d+)[,.](\d+)\s*-->\s*(\d+):(\d+):(\d+)[,.](\d+)")


def read_srt(path: Path) -> list[dict]:
    blocks = []
    for chunk in re.split(r"\n\s*\n", Path(path).read_text(encoding="utf-8-sig").strip()):
        rows = [r for r in chunk.splitlines() if r.strip()]
        k = next((i for i, r in enumerate(rows) if SRT_TIME.search(r)), None)
        if k is None:
            continue
        m = SRT_TIME.search(rows[k])
        h1, m1, s1, f1, h2, m2, s2, f2 = (int(x) for x in m.groups())
        blocks.append({"index": rows[0].strip() if k == 1 else None,
                       "start": h1 * 3600 + m1 * 60 + s1 + f1 / 1000, "end": h2 * 3600 + m2 * 60 + s2 + f2 / 1000,
                       "lines": rows[k + 1:]})
    return blocks


def from_srt(path: Path, lang: str, merge_gap: float = 0.3) -> list[dict]:
    """Fallback when a film has no timeline adapter: each caption run (blocks closer than merge_gap merged)
    becomes a line. Caption text is compared, so a respelled SPOKEN word (洛 for 落) still matches by sound."""
    lines = []
    for b in read_srt(path):
        text = ("" if lang == "zh" else " ").join(r.strip() for r in b["lines"])
        if lines and b["start"] - lines[-1]["end"] < merge_gap:
            lines[-1]["end"] = b["end"]
            lines[-1]["text"] += ("" if lang == "zh" else " ") + text
        else:
            lines.append({"lang": lang, "start": b["start"], "end": b["end"], "text": text})
    for i, line in enumerate(lines):
        line["id"] = f"{lang}-{i + 1:03d}"
        line["question"] = bool(re.search(r"[？?]\s*$", line["text"]))
        line["from_captions"] = True
    return lines
