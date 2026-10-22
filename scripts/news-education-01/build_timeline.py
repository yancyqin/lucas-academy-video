"""Timeline, mixes and captions for 「法国人走上街头，出路在哪里？」 (NEWS-EDUCATION-01.md).

One picture, two audio tracks (owner, 2026-10-20): every line gets one slot as long as the longer of its zh and en takes
plus a pause, both voices start at the slot's start, and the shots (scripts/news-education-01/edit.json) hang on the
slots. So the picture, the zh mix, the en mix and both caption files all share one clock.

  .venv-align/bin/python scripts/news-education-01/build_timeline.py [--draft]

--draft fills a line that has no take yet with silence of an estimated length, to preview the picture early.
Writes public/news-education-01/timeline.json (read by NewsEducation01Video.tsx) and, in out/news-education-01/:
narration.{zh,en}.wav, mix.{zh,en}.wav (music under the voice, README "Music under narration"), and
delivery/news-education-01.{zh-Hans,en}.srt.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parents[2]
FILM = "news-education-01"
PUB = ROOT / "public" / FILM
OUT = ROOT / "out" / FILM
sys.path.insert(0, str(ROOT / "scripts"))
import music_ducking  # noqa: E402

for parent in ROOT.parents:
    if (parent / "lucas-academy-media").is_dir():
        MEDIA = parent / "lucas-academy-media"
        break
TAKES = {lang: MEDIA / f"outputs/yancy/{lang}/{FILM}-v1" for lang in ("zh", "en")}
SR = 48000
FPS = 30
LEAD = 1.2             # picture before the first line
GAP = 0.45             # between lines
SECTION_GAP = 1.5      # between sections
QUESTION_GAP = 1.2     # after a question put to the viewer
TITLE_HOLD = 3.5       # the title card after sc00-09
END_HOLD = 9.0         # end card after the last line
QUESTIONS = {"sc00-01", "sc01-05", "sc06-01", "sc08-01", "sc11-01"}
LINE_LUFS = music_ducking.LINE_LUFS
# Music beds: one piece per part, looped to fill, crossfaded at the part boundaries.
BEDS = [("sc00-01", "music/air-usaf-strings.mp3"), ("sc04-01", "music/gymnopedie-1-macleod.ogg"),
        ("sc08-01", "music/jesu-gli-armonici-novocals.wav")]
BED_LUFS = -20.0
XFADE = 4.0
FINAL_LUFS, FINAL_TP = -16.0, -1.5


def ffread(path: Path) -> np.ndarray:
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).copy()


def lufs(x: np.ndarray) -> float:
    p = subprocess.run(["ffmpeg", "-hide_banner", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", "-af", "ebur128", "-f", "null", "-"],
                       input=x.astype(np.float32).tobytes(), capture_output=True)
    m = re.findall(r"I:\s+(-?[\d.]+) LUFS", p.stderr.decode())
    return float(m[-1]) if m else -70.0


def trim(x: np.ndarray) -> np.ndarray:
    """From 0.05 s before the first sound to 0.15 s after the last (sound = a 10 ms window above -40 dBFS)."""
    w = int(0.01 * SR)
    n = len(x) // w
    rms = np.sqrt((x[: n * w].reshape(n, w) ** 2).mean(axis=1) + 1e-12)
    loud = np.where(20 * np.log10(rms) > -40)[0]
    if not len(loud):
        return x
    a = max(0, loud[0] * w - int(0.05 * SR))
    b = min(len(x), (loud[-1] + 1) * w + int(0.15 * SR))
    return x[a:b]


def estimate(lang: str, text: str) -> float:
    if lang == "zh":
        return len(re.findall(r"[\u4e00-\u9fff]", text)) / 3.6 + 0.5
    return len(text.split()) / 2.4 + 0.5


def load_cues(lang: str) -> list:
    return json.loads((PUB / f"narration/cues.{lang}.json").read_text())


def build(draft: bool) -> None:
    cues = {lang: load_cues(lang) for lang in ("zh", "en")}
    ids = [c["id"] for c in cues["zh"]]
    assert ids == [c["id"] for c in cues["en"]]
    takes, missing = {"zh": {}, "en": {}}, []
    for lang in ("zh", "en"):
        for c in cues[lang]:
            wav = TAKES[lang] / f"{c['id']}.wav"
            if wav.exists():
                x = trim(ffread(wav))
                x = x * 10 ** ((LINE_LUFS - lufs(x)) / 20)
                takes[lang][c["id"]] = x
            elif draft:
                takes[lang][c["id"]] = np.zeros(int(estimate(lang, c["text"]) * SR), np.float32)
                missing.append(f"{lang}:{c['id']}")
            else:
                raise SystemExit(f"no take for {lang} {c['id']} (run narrate.py, or --draft)")
    # slots
    slots, t = {}, LEAD
    for i, cid in enumerate(ids):
        dur = max(len(takes["zh"][cid]), len(takes["en"][cid])) / SR
        slots[cid] = (t, t + dur)
        nxt = ids[i + 1] if i + 1 < len(ids) else None
        gap = GAP
        if cid in QUESTIONS:
            gap = QUESTION_GAP
        if nxt and nxt[:4] != cid[:4]:
            gap = SECTION_GAP
        if cid == "sc00-09":
            gap = TITLE_HOLD
        t += dur + gap
    total = t - GAP + END_HOLD
    # narration tracks and per-language cue times
    lang_cues = {}
    for lang in ("zh", "en"):
        track = np.zeros(int(total * SR) + SR, np.float32)
        out = []
        for c in cues[lang]:
            a = slots[c["id"]][0]
            x = takes[lang][c["id"]]
            i = int(round(a * SR))
            track[i:i + len(x)] += x
            out.append({"id": c["id"], "start": round(a, 3), "end": round(a + len(x) / SR, 3), "text": c["text"],
                        "speech": {"start": round(a, 3), "end": round(a + len(x) / SR, 3)}})
        lang_cues[lang] = out
        OUT.mkdir(parents=True, exist_ok=True)
        sf.write(OUT / f"narration.{lang}.wav", track[: int(total * SR)], SR, subtype="FLOAT")
    # music bed
    bed = np.zeros(int(total * SR), np.float32)
    starts = [slots[cid][0] - (LEAD if cid == "sc00-01" else 1.2) for cid, _ in BEDS] + [total]
    for k, (cid, path) in enumerate(BEDS):
        piece = ffread(PUB / path)
        piece = piece * 10 ** ((BED_LUFS - lufs(piece)) / 20)
        a, b = max(0.0, starts[k]), min(total, starts[k + 1] + (XFADE if k + 1 < len(BEDS) else 0))
        n = int((b - a) * SR)
        reps = int(np.ceil(n / len(piece))) + 1
        seg = np.tile(piece, reps)[:n].copy()
        f = int(XFADE * SR)
        if k > 0:
            seg[:f] *= np.linspace(0, 1, f)
        if k + 1 < len(BEDS):
            seg[-f:] *= np.linspace(1, 0, f)
        i = int(a * SR)
        bed[i:i + n] += seg[: len(bed) - i]
    sf.write(OUT / "bed.wav", bed, SR, subtype="FLOAT")
    for lang in ("zh", "en"):
        env_path = OUT / f"env.{lang}.wav"
        music_ducking.envelope(lang_cues[lang], total, BED_LUFS, env_path)
        env = ffread(env_path)  # resampled to SR by ffmpeg
        n = min(len(env), len(bed))
        voice = sf.read(OUT / f"narration.{lang}.wav", dtype="float32")[0]
        mix = voice[:n] + bed[:n] * env[:n]
        mix *= 10 ** ((FINAL_LUFS - lufs(mix)) / 20)  # one fixed gain, then a peak limiter (no riding the level)
        sf.write(OUT / f"mix.{lang}.raw.wav", mix, SR, subtype="FLOAT")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(OUT / f"mix.{lang}.raw.wav"), "-af",
                        f"alimiter=limit={10 ** (FINAL_TP / 20):.4f}:attack=5:release=60:level=false",
                        "-c:a", "pcm_s24le", str(OUT / f"mix.{lang}.wav")], check=True)
    # shots
    edit = json.loads((ROOT / "scripts" / FILM / "edit.json").read_text())["shots"]
    shots = []
    for s in edit:
        at, frac = (s["at"].split("@") + [None])[:2]
        a, b = slots[at]
        start = a if frac is None else a + float(frac) * (b - a)
        if at == "sc00-01":
            start = 0.0
        shot = {k: v for k, v in s.items() if k != "at"}
        shot["start"] = round(start, 3)
        if "numFrom" in s:
            shot["numAt"] = round(slots[s["numFrom"]][0], 3)
        if s.get("k") == "quote":
            shot["focusAt"] = [round(slots[f][0], 3) for f in s["focus"]]
        shots.append(shot)
    for i, s in enumerate(shots):
        s["end"] = shots[i + 1]["start"] if i + 1 < len(shots) else round(total, 3)
    footage = {}
    for f in sorted((PUB / "footage").glob("*.mp4")):
        footage[f.name] = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(f)],
                                               capture_output=True, text=True).stdout)
    for s in shots:
        if s["k"] == "clip":
            need = (s["end"] - s["start"] + 1.0) * s.get("rate", 1.0)
            have = footage[s["src"]] - s.get("from", 0)
            if have < need:
                print(f"  short clip: {s['src']} has {have:.1f}s, shot needs {need:.1f}s at rate {s.get('rate', 1.0)} "
                      f"(slows to {have / (s['end'] - s['start'] + 1.0):.2f})")
    marks = {cid: {"start": round(slots[cid][0], 3), "end": round(slots[cid][1], 3)} for cid in ids}
    tl = {"fps": FPS, "durationSeconds": round(total, 3), "draft": bool(missing), "shots": shots, "lines": marks,
          "footageSeconds": footage, "endCardStart": round(slots["sc11-03"][0], 3)}
    (PUB / "timeline.json").write_text(json.dumps(tl, ensure_ascii=False, indent=1))
    # captions
    (OUT / "delivery").mkdir(parents=True, exist_ok=True)
    for lang, name in (("zh", "zh-Hans"), ("en", "en")):
        (OUT / "delivery" / f"{FILM}.{name}.srt").write_text(srt(lang_cues[lang], lang), encoding="utf-8")
    print(f"timeline {total / 60:.0f}:{total % 60:04.1f}, {len(shots)} shots" + (f", {len(missing)} lines estimated" if missing else ""))


def chunks(text: str, lang: str) -> list:
    """Caption pieces: split at punctuation, then pack into lines of at most 22 characters (zh) / 70 (en)."""
    limit = 22 if lang == "zh" else 70
    parts = re.split(r"(?<=[，。；：？！、,.;:?!])\s*", text) if lang == "zh" else re.split(r"(?<=[,.;:?!])\s+", text)
    out, cur = [], ""
    for p in [p for p in parts if p.strip()]:
        if cur and len(cur) + len(p) > limit:
            out.append(cur)
            cur = p
        else:
            cur = (cur + ("" if lang == "zh" else " ") + p).strip() if cur else p
    if cur:
        out.append(cur)
    return [re.sub(r"[，、；：]$", "", c) if lang == "zh" else c for c in out]


def srt_time(t: float) -> str:
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def srt(cues: list, lang: str) -> str:
    rows, n = [], 1
    for c in cues:
        pieces = chunks(c["text"], lang)
        weights = [max(1, len(p)) for p in pieces]
        a, b = c["speech"]["start"], c["speech"]["end"]
        t = a
        for p, w in zip(pieces, weights):
            d = (b - a) * w / sum(weights)
            rows.append(f"{n}\n{srt_time(t)} --> {srt_time(t + d)}\n{p}\n")
            n += 1
            t += d
    return "\n".join(rows)


if __name__ == "__main__":
    build("--draft" in sys.argv)
