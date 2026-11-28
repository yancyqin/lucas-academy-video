"""The timeline, narration tracks, music, mixes, captions and QA specs for "We Build A BlackHole with AI"
(BLACK-HOLE-AI.md: decisions, footage events, picture plan, delivery).

One picture, two soundtracks (the cube films' rule, CUBE-2X2.md §4): English first, a Chinese audio track second.
Every line gets the time of the LONGER of its two takes and both takes' voiced onsets start together, so either
track matches the picture; each track gets its own mix, ducked from its own voice activity, and its own captions.

The fall (BH03) is not paced by the voice: it is one uncut take of f3-fall from clip 5.5 s (the plan: ~4.5 s; see FALL_FROM) to its end, and its
lines are anchored to the clip's events (BLACK-HOLE-AI.md, measured on the clip): bh03-01 starts at the museum's
"taken" cue (7.83), bh03-02 about 12 s later, bh03-03 at the museum's own ring cue (27.33, inside the whirl), bh03-04
ENDS before 79.0, bh03-05 STARTS at 80.10, just inside the horizon (79.9; coordinator 2026-11-27, was 80.5), and must
END by 92.5 (the fade to black begins at 92.63). A take that does not fit is never sped up: it goes into `misfits`, and the timeline is marked
as not deliverable until it is re-voiced (or the owner decides).

Picture time comes only from footage played at 1x on an integer frame map (no slow motion, no duplicated frames:
docs/PRODUCTION-CHECKLIST.md). Where the plan's footage is shorter than its narration:
  - f1-orbit under BH00-BH01 (about 71 s) plays straight when the take is long enough (the 80-s take of
    2026-11-27 is). Only a take shorter than its lines (the first one was 50 s) continues through ONE 1-s dissolve
    from frame k to frame k-987: the orbit is a circle with a period of 987 frames (32.9 s, measured from
    footage/f1-orbit/log.jsonl: same-phase frames differ by about 0.1 world unit and 0.1 deg of yaw).
  - the debug clips (d1-d5, 4-7 s each): the study page's own screenshots (stills/panel-*.png) fill the rest,
    with a slow push-in, and the CPU-check and shadow-edge facts get cards of their own.

Writes (public/black-hole-ai is the media folder's public/, outside Git):
  public/black-hole-ai/timeline.json                     cues, sections, shots, overlays, for Remotion
  public/black-hole-ai/audio/LANG.wav                    each language's narration on the film clock (voice stem)
  public/black-hole-ai/audio/music-source.wav            the un-ducked music bed on the film clock
  public/black-hole-ai/audio/LANG.music.wav              the music actually mixed under LANG (ducked)
  public/black-hole-ai/audio/LANG.mix.wav                voice + music, -16 LUFS (what the film plays)
  out/black-hole-ai/delivery/black-hole-ai.{en,zh-Hans}.srt
  out/black-hole-ai/qa/{film,zh-track}.qa-spec.json      the global QA's specs (scripts/qa/spec.py)

  python3 scripts/black-hole-ai/build_timeline.py                     # the real takes (audio/manifest.json)
  python3 scripts/black-hole-ai/build_timeline.py --placeholder DIR   # silent stand-ins in DIR, a draft timeline
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _venv() -> None:
    """numpy/scipy/soundfile live in the main checkout's .venv-align (as for scripts/qa); re-run there if needed."""
    try:
        import numpy  # noqa: F401
        import scipy  # noqa: F401
        import soundfile  # noqa: F401
    except ImportError:
        for parent in [ROOT, *ROOT.parents]:
            py = parent / ".venv-align/bin/python"
            if py.is_file() and Path(sys.executable).resolve() != py.resolve():
                os.execv(str(py), [str(py), "-B", *sys.argv])
        raise


_venv()

import argparse  # noqa: E402
import hashlib  # noqa: E402
import importlib.util  # noqa: E402
import json  # noqa: E402
import math  # noqa: E402
import re  # noqa: E402
import subprocess  # noqa: E402
import tempfile  # noqa: E402

import numpy as np  # noqa: E402
import soundfile as sf  # noqa: E402


sys.dont_write_bytecode = True   # modules are loaded from other checkouts (read-only): never leave .pyc beside them


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


voice = load_module("bh_voice", ROOT / "scripts/black-hole-ai/voice.py")   # the script (captions + spoken forms)


def _ducking():
    """The owner's ducking rules (AGENTS.md "Background music", 2026-11-26). This branch's music_ducking.py predates
    `speech_cues` (duck from actual voice activity) and `limit_under_voice`; the main checkout's working copy has
    them, so it is loaded read-only from there when this branch's copy lacks them."""
    own = load_module("music_ducking", ROOT / "scripts/music_ducking.py")
    if hasattr(own, "speech_cues") and hasattr(own, "limit_under_voice"):
        return own, str(ROOT / "scripts/music_ducking.py")
    for parent in ROOT.parents:
        cand = parent / "scripts/music_ducking.py"
        if cand.is_file() and cand.resolve() != (ROOT / "scripts/music_ducking.py").resolve():
            main = load_module("music_ducking_main", cand)
            if hasattr(main, "speech_cues") and hasattr(main, "limit_under_voice"):
                return main, str(cand)
    raise SystemExit("music_ducking.py with speech_cues/limit_under_voice not found")


ducking, DUCKING_FROM = _ducking()

FILM = "black-hole-ai"
PUB = ROOT / "public/black-hole-ai"
DATA = voice.DATA                                  # ../lucas-academy-video-data/black-hole-ai-20261126/v01
TAKES = DATA / "audio"                             # the voice takes + manifest.json (voice.py); never written here
OUT = ROOT / "out/black-hole-ai"
DELIVERY = OUT / "delivery"
QA = OUT / "qa"
LANGS = ("en", "zh")                               # English first (the film's own track); Chinese second
FPS, SR = 30, 48000

# ------------------------------------------------------------------------------------------- the plan's numbers

SECTIONS = {   # the edit files' headings = the chapters (bar + YouTube description)
    "BH00": ("Flying around a black hole", "绕着黑洞飞"),
    "BH01": ("What a real black hole looks like", "真实的黑洞长什么样"),
    "BH02": ("How we built it with AI", "我们怎么和 AI 一起做的"),
    "BH03": ("Falling in", "掉进去"),
    "BH04": ("Fly it yourself", "你自己来飞"),
}
LEAD_IN = 1.0          # the orbit fades up from black, then the first line
ONSET, GAP, SECTION_GAP = 0.15, 0.4, 0.9
XF = 0.35              # crossfade between shots (brief: calm, ~0.35 s)
XF_SECTION = 0.6       # a little longer between sections
HOLD = {               # extra seconds after a line: a card to read
    "bh00-02": 3.5,    # the title card, ~3.5 s (picture plan)
    "bh01-03": 1.0,    # the paper's citation
    "bh01-04": 0.4,
    "bh02-01": 1.2,    # the plan card's six bullets
    "bh02-02": 1.0,    # the code card
    "bh02-07": 1.2,    # the CPU-check numbers
    "bh02-08": 0.8,
}
END_HOLD = 6.0         # the end card (link + QR) after the last line
FADE_OUT = 1.0         # the film's last second fades to black (a planned edge)

# Footage (BLACK-HOLE-AI.md table): frames at 30 fps.
def _frames(name: str) -> int:
    """A clip's frame count, read from the file on every run (takes get re-captured and replaced)."""
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_packets", "-show_entries",
                          "stream=nb_read_packets", "-of", "csv=p=0", str(PUB / f"footage/{name}.mp4")],
                         capture_output=True, text=True, check=True).stdout
    return int(out.strip().split(",")[0])


CLIPS = {name: _frames(name) for name in ("f1-orbit", "f3-fall", "d1-picture", "d2-outcome", "d3-cost", "d4-shift",
                                          "d5-landmark")}
ORBIT_PERIOD = 987     # frames: one revolution of f1-orbit (32.9 s), see the module docstring
D3_GAIN = 8            # d3-cost is drawn at most RGB (24, 5, 9): shown 8x brighter (noted in BLACK-HOLE-AI.md)

# The fall, clip seconds (BLACK-HOLE-AI.md events; the ring cue from footage/f3-fall-v3/log.jsonl "bh-10-ring").
# The plan says "from ~4.5 s". At clip 5.23-5.33 (frames 157-158) the hole seizes the ship and throws it at twice its
# flight speed (the designed capture): the camera's step jumps from 0.56 to 1.12 world units per frame and the
# picture changes at once (frame difference 27.5 against ~5 around it). The fall starts at 5.5 s, after that
# step (kept by the coordinator, 2026-11-27): uncut from there, 2.3 s before the museum's "taken" cue.
FALL_FROM = 5.5
FALL = {"capture": 7.83, "ring": 27.33, "horizon": 79.9, "pull_in_end": 82.9, "fade": 92.63, "black": 93.37,
        "end": 93.4}
ANCHOR = {             # line -> ("start" | "end", clip second): where its voiced span must start / end
    "bh03-01": ("start", 7.83),
    "bh03-02": ("start", 7.83 + 12.0),
    "bh03-03": ("start", 27.33),
    "bh03-04": ("end", 78.6),      # must END before 79.0
    "bh03-05": ("start", 80.10),   # just inside the horizon (79.9); must END by 92.5, before the fade at 92.63
}
LIMITS = {"bh03-04": ("end_by", 79.0), "bh03-05": ("end_by", 92.5)}

# Music: Chopin, Nocturne in C-sharp minor, B. 49 — Frank Lévy (Musopen, public domain), 225.0 s.
MUSIC = PUB / "music/chopin-b49-frank-levy.flac"
MUSIC_END = 224.0      # the final chord has decayed below -75 dB here (measured, 0.25-s RMS)
REENTRY_OVERLAP = 1.6  # the quiet opening re-enters while the last chord dies away (its first chord is at 1.0 s)
LINE_LUFS, FILM_LUFS = ducking.LINE_LUFS, -16.0
VOICE_CEILING_DB = -2.5   # the voice stem's peak limiter (the mix sums it with music 20 dB down)
MIX_CEILING_DB = -2.0     # a safety limiter on the sum; it should (and is checked to) barely act

NAMES = voice.NAMES

# ------------------------------------------------------------------------------------------- takes


def ffmpeg_decode(path: Path, rate: int = SR, channels: int = 1) -> np.ndarray:
    pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-ac", str(channels), "-ar", str(rate),
                          "-f", "f32le", "-"], capture_output=True, check=True).stdout
    a = np.frombuffer(pcm, np.float32).copy()
    return a.reshape(-1, channels) if channels > 1 else a


def lufs_of(path: Path | None = None, data: np.ndarray | None = None, rate: int = SR) -> float:
    """Integrated loudness (EBU R128) of a file, or of float samples (mono or (n, 2))."""
    if path is not None:
        args, inp = ["-i", str(path)], None
    else:
        ch = 1 if data.ndim == 1 else data.shape[1]
        args, inp = ["-f", "f32le", "-ar", str(rate), "-ac", str(ch), "-i", "-"], np.ascontiguousarray(data, np.float32).tobytes()
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", *args, "-af", "ebur128=framelog=quiet", "-f", "null", "-"],
                       input=inp, capture_output=True, check=True)
    return float(re.findall(r"I:\s+(-?[\d.]+) LUFS", r.stderr.decode())[-1])


def voiced(a: np.ndarray, rate: int = SR) -> dict:
    """Where the sound is (voice.py's rule: 10-ms frames within 35 dB of the loud frames) and the pauses inside it."""
    hop = int(rate * 0.01)
    n = len(a) // hop
    e = np.sqrt((a[: n * hop].astype(np.float64).reshape(n, hop) ** 2).mean(axis=1)) + 1e-9
    ref = float(np.percentile(e, 95))
    if ref < 1e-6:                                   # a silent stand-in
        return {"start": 0.0, "end": len(a) / rate, "pauses": [], "silent": True}
    loud = e > ref * 10 ** (-35 / 20)
    idx = np.flatnonzero(loud)
    s, t = int(idx[0]), int(idx[-1]) + 1
    pauses, k = [], s
    while k < t:
        if not loud[k]:
            j = k
            while j < t and not loud[j]:
                j += 1
            if j - k >= 12:                          # 0.12 s or more of quiet inside the line
                pauses.append([round(k * 0.01, 3), round(j * 0.01, 3)])
            k = j
        else:
            k += 1
    return {"start": round(s * 0.01, 3), "end": round(t * 0.01, 3), "pauses": pauses, "silent": False}


def estimate_seconds(lang: str, text: str) -> float:
    """The brief's placeholder pace: en words / 2.6 s, zh characters / 4.2 s."""
    if lang == "en":
        return len(re.findall(r"[A-Za-z0-9']+", text)) / 2.6
    return len(re.findall(r"[一-鿿]", text) + re.findall(r"[A-Za-z]+", text)) / 4.2


def manifest_status(rows: dict) -> tuple[dict | None, list[str], list[str]]:
    """The manifest's chosen takes, read afresh on every run. Hard problems (a line missing, a file missing or not the
    manifest's bytes) stop the build; soft ones (a take voice.py marked doubtful, a take of an older script line) are
    built with, listed, and make the timeline not deliverable."""
    path = TAKES / "manifest.json"
    if not path.is_file():
        return None, ["audio/manifest.json does not exist yet"], []
    m = json.loads(path.read_text())
    by = {(l["lang"], l["id"]): l for l in m.get("lines", [])}
    hard, soft = [], []
    for lang in LANGS:
        for r in rows[lang]:
            line = by.get((lang, r["id"]))
            if line is None:
                hard.append(f"{lang} {r['id']}: not in the manifest")
                continue
            wav = DATA / line["file"]
            if not wav.is_file() or hashlib.sha256(wav.read_bytes()).hexdigest() != line["sha256"]:
                hard.append(f"{lang} {r['id']}: {line['file']} missing or not the manifest's sha256")
            if line.get("status") not in ("pass", "pass (reviewed)"):
                soft.append(f"{lang} {r['id']}: voice.py status {line.get('status')!r} (ASR {line['asr']['verdict']}"
                            + (f"; {'; '.join(line['own_flags'])}" if line.get("own_flags") else "") + ")")
            if line.get("spoken") != r["spoken"]:
                soft.append(f"{lang} {r['id']}: the take voices an older script line ({line.get('spoken')!r}); "
                            f"the edit now says {r['spoken']!r}: captions follow the take until it is re-voiced")
                r["caption"], r["spoken"] = line["caption"], line["spoken"]
    return (m if not hard else None), hard, soft


# The shared builder's trim (scripts/whole-person-01/build_timeline.py `trim`), on the levelled take: a take runs
# from its first stretch of speech (0.1 s+, peaking above SPEECH_DB) to its last, plus any sound within LEAD_GAP
# before it (a soft onset) or TAIL_GAP after it (a final consonant's release), plus KEEP. Anything else in the
# leading/trailing silence (the voice pass heard faint ticks and breaths there) is left out. The cut is always in
# KEEP seconds of real silence (below ACTIVE_DB), never inside speech; a 10-ms fade makes the edge clean.
ACTIVE_DB, SPEECH_DB = -50.0, -30.0
LEAD_GAP, TAIL_GAP, KEEP, EDGE_FADE = 0.1, 0.25, 0.05, 0.01


def trim(a: np.ndarray) -> tuple[np.ndarray, dict]:
    hop = SR // 100
    n = len(a) // hop
    db = 10 * np.log10((a[: n * hop].astype(np.float64).reshape(n, hop) ** 2).mean(axis=1) + 1e-12)
    runs = []
    for k, d in enumerate(db):
        if d > ACTIVE_DB:
            if runs and k - runs[-1][1] < 4:
                runs[-1][1], runs[-1][2] = k + 1, max(runs[-1][2], d)
            else:
                runs.append([k, k + 1, d])
    speech = [i for i, (x, y, d) in enumerate(runs) if y - x >= 10 and d > SPEECH_DB]
    if not speech:
        return a, {"cut_start": 0.0, "cut_end": round(len(a) / SR, 3), "dropped": []}
    first, last = speech[0], speech[-1]
    while first > 0 and runs[first][0] - runs[first - 1][1] < LEAD_GAP * 100:
        first -= 1
    while last + 1 < len(runs) and runs[last + 1][0] - runs[last][1] < TAIL_GAP * 100:
        last += 1
    k0 = max(0, runs[first][0] * hop - round(KEEP * SR))
    k1 = min(len(a), runs[last][1] * hop + round(KEEP * SR))
    dropped = [{"at": round(x * 0.01, 2), "ms": (y - x) * 10, "peak_dbfs": round(d, 1)}
               for i, (x, y, d) in enumerate(runs) if i < first or i > last]
    out = a[k0:k1].copy()
    f = round(EDGE_FADE * SR)
    ramp = (0.5 - 0.5 * np.cos(np.linspace(0, np.pi, f))).astype(np.float32)
    if k0 > 0:
        out[:f] *= ramp
    if k1 < len(a):
        out[-f:] *= ramp[::-1]
    return out, {"cut_start": round(k0 / SR, 3), "cut_end": round(k1 / SR, 3), "dropped": dropped}


def load_takes(rows: dict, placeholder: Path | None) -> tuple[dict, bool, list[str]]:
    """Every take trimmed at real silence, as 48-kHz mono float at LINE_LUFS, with its voiced span and pauses."""
    takes, soft = {lang: {} for lang in LANGS}, []
    manifest = None
    if placeholder is None:
        manifest, hard, soft = manifest_status(rows)
        if manifest is None:
            raise SystemExit("The takes are not ready:\n  " + "\n  ".join(hard)
                             + "\nBuild a draft with --placeholder DIR (silent stand-ins outside audio/).")
    by = {(l["lang"], l["id"]): l for l in (manifest or {}).get("lines", [])}
    for lang in LANGS:
        for r in rows[lang]:
            if placeholder is None:
                line = by[(lang, r["id"])]
                path = DATA / line["file"]
                source = {"file": line["file"], "sha256": line["sha256"], "take": line["chosen_take"], "status": line["status"]}
            else:
                path = placeholder / lang / f"{r['id']}.wav"
                seconds = round(estimate_seconds(lang, r["spoken"]), 3)
                if not path.is_file() or abs(sf.info(str(path)).duration - seconds) > 0.01:
                    path.parent.mkdir(parents=True, exist_ok=True)
                    sf.write(str(path), np.zeros(round(seconds * 24000), np.float32), 24000, subtype="PCM_24")
                source = {"file": str(path), "placeholder": True}
            a = ffmpeg_decode(path)
            silent = float(np.abs(a).max()) < 1e-6
            gain = 1.0 if silent else 10 ** ((LINE_LUFS - lufs_of(path)) / 20)
            a = (a * gain).astype(np.float32)
            cut = {"cut_start": 0.0, "cut_end": round(len(a) / SR, 3), "dropped": []}
            if not silent:
                a, cut = trim(a)
            span = voiced(a)
            takes[lang][r["id"]] = {"audio": a, "gain_db": round(20 * math.log10(gain), 2), "seconds": round(len(a) / SR, 3),
                                    **span, "trim": cut, "source": source}
    return takes, placeholder is not None, soft


# ------------------------------------------------------------------------------------------- the clock


def frame(t: float) -> int:
    return int(round(t * FPS))


def clip_to_film(f0: float, c: float) -> float:
    return f0 + (c - FALL_FROM)


def place_cues(rows: dict, takes: dict) -> tuple[list[dict], dict, list[dict]]:
    """Cue times for both languages, on one clock; the fall's lines on the clip's events."""
    ids = [r["id"] for r in rows["en"]]
    text = {lang: {r["id"]: r for r in rows[lang]} for lang in LANGS}
    span = lambda lang, cid: takes[lang][cid]["end"] - takes[lang][cid]["start"]  # noqa: E731
    cues, t = [], LEAD_IN
    marks, misfits = {}, []

    def cue(cid, speech_start):
        both = {}
        for lang in LANGS:
            tk = takes[lang][cid]
            at = speech_start - tk["start"]                      # where the take's first sample goes
            both[lang] = {"start": round(speech_start, 3), "end": round(speech_start + span(lang, cid), 3),
                          "place": round(at, 4), "pauses": [[round(at + a, 3), round(at + b, 3)] for a, b in tk["pauses"]]}
        longest = max(span(lang, cid) for lang in LANGS)
        r = text["en"][cid]
        return {"id": cid, "section": r["section"], "en": text["en"][cid]["caption"], "zh": text["zh"][cid]["caption"],
                "speech": {"start": round(speech_start, 3), "end": round(speech_start + longest, 3)}, "speeches": both}

    for n, cid in enumerate(ids):
        section = text["en"][cid]["section"]
        if section == "BH03":
            if "fall" not in marks:
                marks["fall"] = round(frame(t) / FPS, 4)          # the fall shot starts on a frame
            f0 = marks["fall"]
            kind, at = ANCHOR[cid]
            longest = max(span(lang, cid) for lang in LANGS)
            start = clip_to_film(f0, at) if kind == "start" else clip_to_film(f0, at) - longest
            if cues and start < cues[-1]["speech"]["end"] + 0.8:
                misfits.append({"id": cid, "problem": f"would start {cues[-1]['speech']['end'] + 0.8 - start:.2f} s "
                                "before the previous line has ended (+0.8 s)"})
                start = cues[-1]["speech"]["end"] + 0.8
            c = cue(cid, start)
            c["start"], c["end"] = round(start - ONSET, 3), round(c["speech"]["end"] + GAP, 3)
            c["clip"] = {"start": round(start - f0 + FALL_FROM, 3), "end": round(c["speech"]["end"] - f0 + FALL_FROM, 3)}
            if cid in LIMITS:
                _, limit = LIMITS[cid]
                if c["clip"]["end"] > limit + 1e-6:
                    over = {lang: round(c["speeches"][lang]["end"] - f0 + FALL_FROM - limit, 2) for lang in LANGS}
                    misfits.append({"id": cid, "problem": f"voiced from clip {c['clip']['start']:.2f} s to {c['clip']['end']:.2f} s; "
                                    f"it must end by {limit} s",
                                    "over_by_seconds": {k: v for k, v in over.items() if v > 0},
                                    "speech_seconds": {lang: round(span(lang, cid), 2) for lang in LANGS},
                                    "window_seconds": round(limit - c["clip"]["start"], 2)})
            cues.append(c)
            continue
        if section == "BH04" and "bh04" not in marks:
            f0 = marks["fall"]
            clip_end = clip_to_film(f0, FALL["end"])
            last = cues[-1]["speech"]["end"]
            marks["black_from"] = round(clip_to_film(f0, FALL["fade"]), 3)
            marks["bh04"] = round(frame(max(clip_end, last + 0.5)) / FPS, 4)
            t = marks["bh04"] + 0.8 - ONSET                        # the end card fades up, then the line
        c = cue(cid, t + ONSET)
        last_in_section = n + 1 == len(ids) or text["en"][ids[n + 1]]["section"] != section
        slot = ONSET + (c["speech"]["end"] - c["speech"]["start"]) + GAP + HOLD.get(cid, 0) + (SECTION_GAP if last_in_section else 0)
        c["start"], c["end"] = round(t, 3), round(t + slot, 3)
        cues.append(c)
        t += slot
    total = round(frame(cues[-1]["speech"]["end"] + END_HOLD) / FPS, 4)
    marks["end"] = total
    marks["end_card"] = marks["bh04"]
    return cues, marks, misfits


# ------------------------------------------------------------------------------------------- shots


def split_after(c: dict, late: bool = True) -> float:
    """The film time between a cue's first sentence and the rest, in each language: the real pause nearest to where
    the first sentence should end by its length (within 1 s), else that estimate. `late`: the later of the two
    languages (both have finished the first sentence); else the earlier (neither has started the second)."""
    times = []
    for lang in LANGS:
        s = c["speeches"][lang]
        sentence = re.split(r"(?<=[.。：:])\s*", c[lang], maxsplit=1)[0]   # zh bh02-05 turns at its colon
        est = s["start"] + (s["end"] - s["start"]) * len(sentence) / max(1, len(c[lang]))
        near = sorted((abs((p0 + p1) / 2 - est), p0, p1) for p0, p1 in s["pauses"] if abs((p0 + p1) / 2 - est) <= 1.0)
        if near:
            _, p0, p1 = near[0]
            times.append(p1 - 0.05 if late else p0 + 0.05)
        else:
            times.append(est)
    return max(times) if late else min(times)


def build_shots(cues: list[dict], marks: dict) -> tuple[list[dict], list[dict], list[dict]]:
    """Shots (picture layers on the film clock, frame-exact) and overlays (cards/labels), from the picture plan."""
    by = {c["id"]: c for c in cues}
    shots, overlays, notes = [], [], []

    def footage(name, a, b, src_from, **extra):
        fa, fb = frame(a), frame(b)
        s0 = int(src_from)
        assert fb > fa, (name, a, b)
        assert s0 >= 0 and s0 + (fb - fa) <= CLIPS[name], f"{name}: frames {s0}-{s0 + fb - fa} outside 0-{CLIPS[name]}"
        shots.append({"kind": "footage", "clip": name, "startFrame": fa, "endFrame": fb, "fromFrame": s0, **extra})
        return s0 + (fb - fa)

    def still(name, a, b, **extra):
        shots.append({"kind": "still", "image": name, "startFrame": frame(a), "endFrame": frame(b), **extra})

    def card(name, a, b, **extra):
        shots.append({"kind": "card", "card": name, "startFrame": frame(a), "endFrame": frame(b), **extra})

    def overlay(name, a, b, **extra):
        overlays.append({"kind": name, "start": round(a, 3), "end": round(b, 3), **extra})

    bh01 = [c for c in cues if c["section"] == "BH01"]
    bh02_first = next(c for c in cues if c["section"] == "BH02")
    # ---- BH00 + BH01: the orbit, straight when the take is long enough, else once more round (same phase)
    orbit_end = bh02_first["start"] + XF_SECTION
    if frame(orbit_end) <= CLIPS["f1-orbit"]:
        used = footage("f1-orbit", 0, orbit_end, 0, fadeIn=0.8, fadeFromBlack=True)
        notes.append(f"f1-orbit: one continuous shot, frames 0-{used - 1} of {CLIPS['f1-orbit']}")
    loop_at = None if frame(orbit_end) <= CLIPS["f1-orbit"] else 0.0
    for prev, nxt in zip(bh01, bh01[1:]) if loop_at is not None else []:
        mid = (prev["speech"]["end"] + nxt["speech"]["start"]) / 2
        if mid - 0.5 >= ORBIT_PERIOD / FPS + 0.2:
            loop_at = mid
            break
    if loop_at == 0.0:
        raise SystemExit("no pause in BH01 late enough for the orbit's same-phase dissolve")
    a_end = frame(loop_at + 0.5) if loop_at else 0
    if loop_at:
        footage("f1-orbit", 0, a_end / FPS, 0, fadeIn=0.8, fadeFromBlack=True)
        b_start = frame(loop_at - 0.5)
        used = footage("f1-orbit", b_start / FPS, orbit_end, b_start - ORBIT_PERIOD, fadeIn=1.0, samePhase=True)
        notes.append(f"f1-orbit: frames 0-{a_end - 1}, then a 1.0-s same-phase dissolve at {loop_at:.2f} s to frame "
                     f"{b_start - ORBIT_PERIOD} (one revolution, {ORBIT_PERIOD} frames, earlier), playing on to frame {used - 1}")
    b2 = by["bh00-02"]
    overlay("title", b2["speech"]["end"] + 0.3, by["bh00-03"]["speech"]["start"] - 0.15)
    for cid, ref in (("bh01-02", "ref-svs13326"), ("bh01-03", "ref-james2015"), ("bh01-04", "ref-svs14576")):
        c = by[cid]
        overlay(ref, c["speech"]["start"] + 0.3, c["end"] - 0.1)

    # ---- BH02: plan card, code card, the debug page
    c1, c2 = by["bh02-01"], by["bh02-02"]
    card("plan", c1["start"], c2["start"] + XF, fadeIn=XF_SECTION, steps=[round(c1["speech"]["start"] + (c1["speech"]["end"] - c1["speech"]["start"]) * k / 6, 3) for k in range(6)])
    card("code", c2["start"], by["bh02-03"]["start"] + XF, fadeIn=XF)

    def seconds(name):     # a clip's length, one frame short so frame rounding never runs past its end
        return (CLIPS[name] - 1) / FPS

    # bh02-03 + bh02-04: d1 | the page (panel-picture) for "This is our debug page." | back to d1 for "Here is the picture."
    c3, c4 = by["bh02-03"], by["bh02-04"]
    back = split_after(c4, late=False) - 0.2           # d1 is back before either language says "Here is the picture"
    group = (c4["end"] + XF) - c3["start"]
    still_len = max(1.6, group + XF - seconds("d1-picture"))   # d1 frames used = group + XF - still_len
    page_from = back - still_len
    s = footage("d1-picture", c3["start"], page_from + XF, 0, fadeIn=XF, label="picture")
    still("panel-picture", page_from, back + XF, fadeIn=XF, push=0.06, focus=[1130, 520], label="page")
    footage("d1-picture", back, c4["end"] + XF, s, fadeIn=XF, label="picture")
    # bh02-05: the page in the outcome view, then d2 with the legend
    c5 = by["bh02-05"]
    d2_len = min(seconds("d2-outcome"), c5["end"] + XF - c5["start"] - 1.6)
    d2_from = c5["end"] + XF - d2_len
    still("panel-outcome", c5["start"], d2_from + XF, fadeIn=XF, push=0.05, focus=[1130, 520], label="outcome-page")
    footage("d2-outcome", d2_from, c5["end"] + XF, 0, fadeIn=XF, label="outcome")
    overlay("legend", max(c5["speech"]["start"] + 0.6, split_after(c5) - 0.3), c5["end"] + XF)
    # bh02-06: d3 (brightened) for the cost; the page in the shift view, then d4
    c6 = by["bh02-06"]
    turn = split_after(c6)
    if turn + XF - c6["start"] > seconds("d3-cost"):
        still("panel-cost", c6["start"], turn + 2 * XF - seconds("d3-cost"), fadeIn=XF, push=0.04, focus=[1130, 520], label="cost-page")
        footage("d3-cost", turn + XF - seconds("d3-cost"), turn + XF, 0, fadeIn=XF, gain=D3_GAIN, label="cost")
    else:
        footage("d3-cost", c6["start"], turn + XF, 0, fadeIn=XF, gain=D3_GAIN, label="cost")
    rest = c6["end"] + XF - turn
    flex = rest - seconds("d4-shift")
    if flex > 0.05:                                   # the page in the shift view first (at least 1.2 s)
        page = max(1.2, flex)
        still("panel-shift", turn, turn + page + XF, fadeIn=XF, push=0.05, focus=[1130, 520], label="shift-page")
        footage("d4-shift", turn + page, c6["end"] + XF, 0, fadeIn=XF, label="shift")
    else:
        footage("d4-shift", turn, c6["end"] + XF, 0, fadeIn=XF, label="shift")
    # bh02-07 + bh02-08: the page's compare section, then d5 across the two lines, then the shadow-edge card
    c7, c8 = by["bh02-07"], by["bh02-08"]
    d5_from = max(c7["start"] + 1.6, c8["start"] - 3.0)
    d5_to = min(d5_from + seconds("d5-landmark") - XF, c8["end"] - 2.5)
    still("panel-compare", c7["start"], d5_from + XF, fadeIn=XF, push=0.05, focus=[700, 600], label="compare-page")
    footage("d5-landmark", d5_from, d5_to + XF, 0, fadeIn=XF, label="landmark")
    card("shadow-edge", d5_to, c8["end"] + XF_SECTION, fadeIn=XF)
    overlay("cpu-check", c7["speech"]["start"] + 0.2, c7["end"])

    # ---- BH03: the fall, uncut from clip FALL_FROM to its end
    f0 = marks["fall"]
    fall_from = frame(FALL_FROM)
    footage("f3-fall", f0, clip_to_film(f0, FALL["end"]), fall_from, fadeIn=XF_SECTION)
    # ---- BH04: the end card over the orbit (dimmed), the last frames of the clip
    e0 = marks["bh04"]
    length = frame(marks["end"]) - frame(e0)
    footage("f1-orbit", e0, marks["end"], CLIPS["f1-orbit"] - length, fadeIn=0.8, fadeFromBlack=True, dim=0.55)
    overlay("end-card", e0 + 0.3, marks["end"])

    # Shots are drawn in order; each one's fade-in overlaps the one before it.
    shots.sort(key=lambda s: s["startFrame"])
    for k, s in enumerate(shots):
        s["id"] = f"S{k + 1:02d}-{s.get('clip') or s.get('image') or s.get('card')}"
    return shots, overlays, notes


# ------------------------------------------------------------------------------------------- music


def music_bed(total: float) -> tuple[np.ndarray, dict]:
    """The nocturne from its first note, whole; if the film is longer, its quiet opening re-enters as the last chord
    dies away (both sides soft), and the film's own 5-s fade (music_ducking FADE_OUT) ends it."""
    src = ffmpeg_decode(MUSIC, SR, 2)
    n = round(total * SR)
    bed = np.zeros((n, 2), np.float32)
    first = src[: min(len(src), n)]
    bed[: len(first)] = first
    plan = {"source": "Chopin, Nocturne in C-sharp minor, B. 49 — Frank Lévy (Musopen, public domain)",
            "file": MUSIC.name, "segments": [{"film": [0.0, round(min(total, len(src) / SR), 3)], "file": [0.0, round(min(total, len(src) / SR), 3)]}]}
    if total > MUSIC_END:
        start = MUSIC_END - REENTRY_OVERLAP                 # film = file time for the first pass
        k0 = round(start * SR)
        tail = src[k0: round(MUSIC_END * SR)]
        fade_out = np.linspace(1, 0, len(tail), dtype=np.float32) ** 2
        bed[k0: k0 + len(tail)] = tail * fade_out[:, None]
        bed[k0 + len(tail):] = 0
        again = src[: n - k0]
        fade_in = np.minimum(1, np.arange(len(again)) / (REENTRY_OVERLAP * SR)).astype(np.float32)
        bed[k0: k0 + len(again)] += again * fade_in[:, None]
        plan["segments"] = [{"film": [0.0, MUSIC_END], "file": [0.0, MUSIC_END], "fade_out": [start, MUSIC_END]},
                            {"film": [round(start, 3), round(total, 3)], "file": [0.0, round(total - start, 3)],
                             "fade_in": [round(start, 3), round(start + REENTRY_OVERLAP, 3)],
                             "note": "the quiet opening again (first chord at file 1.0 s), under the end"}]
    return bed, plan


def mix(lang: str, cues: list[dict], takes: dict, total: float, bed: np.ndarray, bed_lufs: float, audio: Path) -> dict:
    """Voice and ducked music as stems on the film clock (48 kHz stereo), the film gain on both, then their sum."""
    n = round(total * SR)
    v = np.zeros(n, np.float32)
    for c in cues:
        a = takes[lang][c["id"]]["audio"]
        k = round(c["speeches"][lang]["place"] * SR)
        lo = max(0, k)
        v[lo: k + len(a)] += a[lo - k: n - k]
    gain = 1.0
    silent = float(np.abs(v).max()) < 1e-6                  # a draft with silent stand-ins: no film gain
    with tempfile.TemporaryDirectory() as tmp:
        env_path = Path(tmp) / "env.wav"
        for _ in range(1 if silent else 3):                  # the duck follows the voice at its final level
            activity = ducking.speech_cues(v * gain, SR)
            ducking.envelope(activity, total, bed_lufs, env_path)
            env, rate = sf.read(str(env_path), dtype="float32")
            g = np.interp(np.arange(n) / SR * rate, np.arange(len(env)), env).astype(np.float32)
            music = bed * g[:, None]
            music = ducking.limit_under_voice(music, v * gain, SR).astype(np.float32)
            assert np.isfinite(music).all(), "limit_under_voice returned non-finite samples"
            pre = np.repeat((v * gain)[:, None], 2, axis=1) + music * gain
            if not silent:
                gain *= 10 ** ((FILM_LUFS - lufs_of(data=pre)) / 20)
        voice_stem = np.repeat((v * gain)[:, None], 2, axis=1)
        raw = Path(tmp) / "voice.raw.wav"
        sf.write(str(raw), voice_stem, SR, subtype="FLOAT")
        lim = Path(tmp) / "voice.lim.wav"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(raw), "-af",
                        f"alimiter=limit={10 ** (VOICE_CEILING_DB / 20):.5f}:attack=5:release=50:level=false:latency=true",
                        "-c:a", "pcm_f32le", str(lim)], check=True)
        voice_stem, _ = sf.read(str(lim), dtype="float32")
        voice_stem = voice_stem[:n] if len(voice_stem) >= n else np.pad(voice_stem, ((0, n - len(voice_stem)), (0, 0)))
    music_stem = (music * gain).astype(np.float32)
    total_mix = voice_stem + music_stem
    peak_db = 20 * math.log10(max(1e-9, float(np.abs(total_mix).max())))
    ceiling = 10 ** (MIX_CEILING_DB / 20)
    over = int(np.sum(np.abs(total_mix) > ceiling))
    total_mix = np.clip(total_mix, -0.999, 0.999)
    sf.write(str(audio / f"{lang}.wav"), voice_stem, SR, subtype="FLOAT")
    sf.write(str(audio / f"{lang}.music.wav"), music_stem, SR, subtype="FLOAT")
    mixed = audio / f"{lang}.mix.wav"
    if over:   # a safety limiter only if the sum does pass the ceiling (it should not); reported either way
        tmpmix = audio / f"{lang}.mix.unlimited.wav"
        sf.write(str(tmpmix), total_mix, SR, subtype="FLOAT")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(tmpmix), "-af",
                        f"alimiter=limit={ceiling:.5f}:attack=5:release=50:level=false:latency=true",
                        "-c:a", "pcm_f32le", str(mixed)], check=True)
        tmpmix.unlink()
    else:
        sf.write(str(mixed), total_mix, SR, subtype="FLOAT")
    speech = [round(s["speech"]["end"] - s["speech"]["start"], 3) for s in activity]
    return {"film_gain_db": round(20 * math.log10(gain), 2), "mix_lufs": round(lufs_of(mixed), 2), "sum_peak_dbfs": round(peak_db, 2),
            "samples_over_mix_ceiling": over, "voice_activity_spans": len(speech)}


# ------------------------------------------------------------------------------------------- captions

ROW = {"en": 42, "zh": 22}        # scripts/qa/fmt.py: 42 characters (en), width 22 (zh), at most 2 rows


def width(s: str, lang: str) -> float:
    return len(s) if lang == "en" else sum(1 if re.match(r"[^\x00-\x7f]", ch) else 0.5 for ch in s)


def wrap(text: str, lang: str) -> list[str]:
    """Rows within the QA's width, broken at spaces (en) or anywhere but before punctuation (zh)."""
    limit = ROW[lang]
    if width(text, lang) <= limit:
        return [text]
    # Two rows split after a comma, when both fit: the most balanced such split.
    marks = "，、：；。？！" if lang == "zh" else ",:;.?!"
    cuts = [k + 1 for k, ch in enumerate(text[:-1]) if ch in marks]
    pairs = [(text[:k].strip(), text[k:].strip()) for k in cuts]
    pairs = [(a, b) for a, b in pairs if width(a, lang) <= limit and width(b, lang) <= limit]
    if pairs:
        a, b = min(pairs, key=lambda p: abs(width(p[0], lang) - width(p[1], lang)))
        if min(width(a, lang), width(b, lang)) >= 0.3 * width(text, lang):
            return [a, b]
    if lang == "en":
        words, rows, cur = text.split(), [], ""
        for w in words:
            if cur and len(cur) + 1 + len(w) > limit:
                rows.append(cur)
                cur = w
            else:
                cur = f"{cur} {w}".strip()
        rows.append(cur)
    else:   # never inside a Latin word, never before closing punctuation
        rows, cur = [], ""
        toks = re.findall(r"[A-Za-z0-9.*'’]+|\s+|.", text)
        cur_toks: list[str] = []
        for tok in toks:
            if width("".join(cur_toks) + tok, lang) > limit and "".join(cur_toks).strip():
                carry = []
                if tok in "，。？！；：、」）》":      # closing punctuation never starts a row: take a character down with it
                    carry = [cur_toks.pop()]
                rows.append("".join(cur_toks).rstrip())
                cur_toks = [t for t in carry + [tok] if t.strip() or carry]
            else:
                cur_toks.append(tok)
        rows.append("".join(cur_toks).strip())
    if len(rows) == 2:   # balance two rows
        if lang == "en":
            words = text.split()
            best = min(range(1, len(words)), key=lambda k: max(len(" ".join(words[:k])), len(" ".join(words[k:]))))
            a, b = " ".join(words[:best]), " ".join(words[best:])
            if len(a) <= limit and len(b) <= limit:
                rows = [a, b]
    return rows


def pieces(text: str, lang: str) -> list[str]:
    """Split at sentence ends, then at commas, until each piece fits two rows."""
    ends, commas = (".?!;:", ",") if lang == "en" else ("。？！；：", "，、")

    def cut(s, marks):
        out, cur = [], ""
        for k, ch in enumerate(s):
            cur += ch
            if ch in marks and (lang == "zh" or k + 1 == len(s) or s[k + 1] == " "):
                if not (lang == "en" and ch == "." and re.search(r"\b(?:is|lucasacademy)\.$", cur)):
                    out.append(cur.strip())
                    cur = ""
        if cur.strip():
            out.append(cur.strip())
        return out

    def fits(s):
        rows = wrap(s, lang)
        if lang == "zh" and len(rows) == 2 and rows[0][-1] not in "，、：；。？！":
            return False   # a Chinese caption breaks its two rows at punctuation, or becomes two captions
        return len(rows) <= 2

    def halves(s):
        """A clause with no comma that is still too long: cut between words near its middle, before a joining word
        when there is one close by (en), never inside a Latin word (zh)."""
        if lang == "en":
            words = s.split()
            join = {"and", "by", "behind", "that", "where", "for", "to", "of", "the", "with", "in", "at"}
            mid = len(s) / 2
            best = min(range(1, len(words)), key=lambda k: abs(len(" ".join(words[:k])) - mid)
                       - (6 if words[k].lower() in join else 0))
            a, b = " ".join(words[:best]), " ".join(words[best:])
        else:
            toks = re.findall(r"[A-Za-z0-9.*'’]+|\s+|.", s)
            acc, best, bestd = "", 1, 1e9
            for k in range(1, len(toks)):
                acc += toks[k - 1]
                if toks[k] in "，。？！；：、」）" or toks[k].isspace():
                    continue
                d = abs(width(acc, lang) - width(s, lang) / 2)
                if d < bestd:
                    best, bestd = k, d
            a, b = "".join(toks[:best]).strip(), "".join(toks[best:]).strip()
        return [x for part in (a, b) for x in (halves(part) if not fits(part) else [part])]

    out = []
    for sentence in cut(text, ends):
        if fits(sentence):
            out.append(sentence)
        else:
            parts = cut(sentence, commas)
            merged = []
            for p in parts:
                if merged and fits(merged[-1] + ("" if lang == "zh" else " ") + p):
                    merged[-1] = merged[-1] + ("" if lang == "zh" else " ") + p
                else:
                    merged.append(p)
            for p in merged:
                out += halves(p) if not fits(p) else [p]
    # merge short neighbours that still fit
    final = []
    for p in out:
        if final and width(final[-1] + p, lang) <= ROW[lang] * 1.6 and fits(final[-1] + ("" if lang == "zh" else " ") + p):
            final[-1] = final[-1] + ("" if lang == "zh" else " ") + p
        else:
            final.append(p)
    assert all(fits(p) for p in final), [p for p in final if not fits(p)]
    return final


def srt_time(t: float) -> str:
    ms = max(0, round(t * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def captions(cues: list[dict], total: float) -> dict:
    """Each language's written words, timed to its own voice: a line's pieces split its voiced span by length, each
    boundary moved to the nearest real pause within 0.8 s; no block overlaps the next."""
    DELIVERY.mkdir(parents=True, exist_ok=True)
    out = {}
    for name, lang in (("en", "en"), ("zh-Hans", "zh")):
        blocks = []
        for c in cues:
            s = c["speeches"][lang]
            parts = pieces(c[lang], lang)
            weights = [max(1.0, width(p, lang)) for p in parts]
            a, b = s["start"], s["end"]
            cuts, acc = [], 0.0
            for w in weights[:-1]:
                acc += w
                est = a + (b - a) * acc / sum(weights)
                near = [(abs((p0 + p1) / 2 - est), (p0 + p1) / 2) for p0, p1 in s["pauses"] if abs((p0 + p1) / 2 - est) <= 0.8]
                cuts.append(min(near)[1] if near else est)
            edges = [a, *sorted(cuts), b]
            for k, part in enumerate(parts):
                blocks.append([edges[k], edges[k + 1], part, k == len(parts) - 1])
        for k, blk in enumerate(blocks):
            nxt = blocks[k + 1][0] if k + 1 < len(blocks) else total
            if blk[3]:
                blk[1] = blk[1] + 0.5
            blk[1] = min(blk[1], nxt - 0.05, total)
        text = "\n".join(f"{k}\n{srt_time(a)} --> {srt_time(b)}\n" + "\n".join(wrap(part, lang)) + "\n"
                         for k, (a, b, part, _) in enumerate(blocks, 1))
        path = DELIVERY / f"{FILM}.{name}.srt"
        path.write_text(text, encoding="utf-8")
        out[lang] = {"file": str(path), "blocks": len(blocks)}
    return out


# ------------------------------------------------------------------------------------------- QA specs


def qa_specs(cues, rows, shots, marks, total, audio: Path) -> dict:
    """The global QA spec for the film (English track) and for the Chinese track (scripts/qa/spec.py)."""
    QA.mkdir(parents=True, exist_ok=True)
    text = {lang: {r["id"]: r for r in rows[lang]} for lang in LANGS}
    kinds = {"f1-orbit": "footage", "f3-fall": "footage", "d1-picture": "footage",
             # d2-d5 drift as slowly as d1 but are flat colour fields: every frame changes by less than picture.py's
             # freeze threshold (0.005-0.016 at 960 px, against 0.06; no two frames identical). They are page
             # renders of a visualisation, declared as animation, not as camera footage that must visibly move.
             "d2-outcome": "animation", "d3-cost": "animation", "d4-shift": "animation", "d5-landmark": "animation"}
    spec_shots, transitions = [], []
    for s in shots:
        a, b = s["startFrame"] / FPS, s["endFrame"] / FPS
        if s["kind"] == "footage":
            row = {"id": s["id"], "start": round(a, 3), "end": round(b, 3), "kind": kinds[s["clip"]],
                   "camera_motion": True,   # orbit and fall: continuous 3D camera moves; d1-d5: slow camera drifts
                   "note": {"f1-orbit": "continuous 3D chase-camera orbit (third person)",
                            "f3-fall": "one continuous 3D take: still view until the horizon, then first person with slow looks",
                            }.get(s["clip"], "debug-page render, slow automatic orbit drift")}
        elif s["kind"] == "still":
            row = {"id": s["id"], "start": round(a, 3), "end": round(b, 3), "kind": "still", "camera_motion": True,
                   "note": "study-page screenshot with a slow push-in (a smooth zoom: checked like a camera move)"}
        else:
            row = {"id": s["id"], "start": round(a, 3), "end": round(b, 3), "kind": "title", "camera_motion": False,
                   "note": "graphic card"}
        spec_shots.append(row)
        fade = s.get("fadeIn", 0)
        if fade and a > 0:
            transitions.append([round(a, 3), round(a + fade, 3)])
    e0 = marks["bh04"]
    planned_black = [[0.0, 0.8],                                          # the opening fades up from black
                     [marks["black_from"], round(e0 + 0.8, 3)],            # the fall's fade to black (planned edge)
                     [round(total - FADE_OUT, 3), round(total, 3)]]
    transitions.append([round(total - FADE_OUT, 3), round(total, 3)])
    specs = {}
    for track, lang in (("film", "en"), ("zh-track", "zh")):
        lines = []
        for c in cues:
            r = text[lang][c["id"]]
            s = c["speeches"][lang]
            row = {"id": c["id"], "lang": lang, "start": s["start"], "end": s["end"], "text": r["spoken"]}
            if r["caption"] != r["spoken"]:
                row["caption"] = r["caption"]
            lines.append(row)
        spec = {
            "film": FILM if track == "film" else f"{FILM}.zh-track",
            "kind": "narrated",
            "lines": lines,
            "voice_audio": os.path.relpath(audio / f"{lang}.wav", QA),
            "music_source": os.path.relpath(audio / "music-source.wav", QA),
            "music_audio": os.path.relpath(audio / f"{lang}.music.wav", QA),
            "music": True,
            "loudness": {"lufs": -16, "tol": 0.5, "tp_max": -1.0},
            "format": {"width": 1920, "height": 1080, "fps": FPS, "duration": round(total, 3), "tol": 0.15},
            "captions": [{"path": os.path.relpath(DELIVERY / f"{FILM}.zh-Hans.srt", QA), "lang": "zh"},
                         {"path": os.path.relpath(DELIVERY / f"{FILM}.en.srt", QA), "lang": "en"}],
            "shots": spec_shots,
            "transitions": transitions,
            "planned_black": planned_black,
            "names": NAMES[lang],
        }
        path = QA / f"{track}.qa-spec.json"
        path.write_text(json.dumps(spec, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        specs[track] = str(path)
    return specs


# ------------------------------------------------------------------------------------------- build


def build(placeholder: Path | None) -> None:
    rows = {lang: voice.load(lang) for lang in LANGS}
    assert [r["id"] for r in rows["en"]] == [r["id"] for r in rows["zh"]]
    takes, draft, problems = load_takes(rows, placeholder)
    cues, marks, misfits = place_cues(rows, takes)
    total = marks["end"]
    shots, overlays, notes = build_shots(cues, marks)
    sections = []
    for sid, (en, zh) in SECTIONS.items():
        first = next(c for c in cues if c["section"] == sid)
        start = 0.0 if not sections else (marks["fall"] if sid == "BH03" else marks["bh04"] if sid == "BH04" else first["start"])
        sections.append({"id": sid, "en": en, "zh": zh, "start": round(start, 3)})
    for k, s in enumerate(sections):
        s["end"] = sections[k + 1]["start"] if k + 1 < len(sections) else round(total, 3)
    audio = PUB / "audio"
    audio.mkdir(parents=True, exist_ok=True)
    bed, music_plan = music_bed(total)
    sf.write(str(audio / "music-source.wav"), bed, SR, subtype="FLOAT")
    bed_lufs = lufs_of(audio / "music-source.wav")
    mixes = {lang: mix(lang, cues, takes, total, bed, bed_lufs, audio) for lang in LANGS}
    subs = captions(cues, total)
    specs = qa_specs(cues, rows, shots, marks, total, audio)
    data = {
        "film": FILM, "title": "We Build A BlackHole with AI", "byline": "By Lucas Academy Team",
        "fps": FPS, "durationSeconds": round(total, 4), "durationInFrames": frame(total),
        "draft": draft, "deliverable": not draft and not misfits and not problems, "misfits": misfits,
        "takeWarnings": problems,
        "marks": {k: round(v, 3) for k, v in marks.items()}, "fall": {"from": FALL_FROM, **FALL},
        "sections": sections, "cues": [{k: v for k, v in c.items()} for c in cues], "shots": shots, "overlays": overlays,
        "fadeOut": FADE_OUT, "d3Gain": D3_GAIN, "notes": notes,
        "music": music_plan, "mix": mixes, "ducking": DUCKING_FROM,
        "takes": {lang: {cid: {k: v for k, v in t.items() if k not in ("audio", "pauses")} for cid, t in takes[lang].items()} for lang in LANGS},
    }
    (PUB / "timeline.json").write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    # ---- report
    print(f"{'DRAFT (placeholder takes) ' if draft else ''}{len(cues)} cues, {len(shots)} shots, {total:.2f} s "
          f"({int(total // 60)}:{total % 60:04.1f})")
    for s in sections:
        print(f"  {s['id']} {s['start']:7.2f} - {s['end']:7.2f}  {s['en']}")
    for n in notes:
        print("  " + n)
    for lang, m in mixes.items():
        print(f"  {lang} mix: {m}")
    print(f"  music: {json.dumps(music_plan['segments'])}")
    print(f"  captions: {subs}\n  QA specs: {specs}")
    if problems:
        print("  TAKE WARNINGS (built with; not deliverable until settled):")
        for w in problems:
            print(f"    {w}")
    trims = [(lang, cid, t["trim"]["dropped"]) for lang in LANGS for cid, t in takes[lang].items() if t["trim"]["dropped"]]
    for lang, cid, dropped in trims:
        print(f"  trimmed away from {lang} {cid}: {dropped}")
    if misfits:
        print("  MISFITS (not deliverable until re-voiced or decided):")
        for m in misfits:
            print(f"    {m}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--placeholder", type=Path, help="silent stand-in takes in this folder (never audio/); a draft")
    args = ap.parse_args()
    build(args.placeholder.resolve() if args.placeholder else None)
