"""Timeline, Chinese narration mix and captions for 「跨越中等收入陷阱」 (MIDDLE-INCOME-TRAP.md).

  .venv-align/bin/python scripts/middle-income-trap/build_timeline.py [--speed 1.2] [--question-speed 1.1] [--listen] [--draft]

--draft stands in silence for takes not voiced yet, to look at the picture early; never render or deliver from it.

Reads the caption script (docs/middle-income-trap/zh-edit.md: lines and the Li Lu clips, in order), the pauses in
voice-direction.md, Yancy's takes (lucas-academy-media outputs/yancy/zh/middle-income-trap-v3/s<speed>/; a line
ending in a question from s<question-speed>/) and the clips (lucas-academy-video-data/middle-income-trap/clips/).
After a question there is at least QUESTION_GAP of silence, a breath to think (Yancy, 2026-10-25). Each take is
trimmed at -40 dBFS (stray vocoder blips at the ends dropped), faded in and out, and levelled to -23 LUFS; each clip
keeps its own sound, levelled the same way, with short fades. No music yet: this is the cut Yancy listens to before
the English and the picture (2026-10-25).

Writes public/middle-income-trap/timeline.json (lines, clips, chapters), out/middle-income-trap/narration.zh.wav,
out/middle-income-trap/mix.zh.wav (with the music), the shots from scripts/middle-income-trap/edit.json,
out/middle-income-trap/delivery/middle-income-trap.zh-Hans.srt and, with --listen, an mp3 of the whole film in the
data folder's samples/.
"""
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import soundfile as sf

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import music_ducking  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
for parent in ROOT.parents:
    if (parent / "lucas-academy-media").is_dir():
        MEDIA = parent / "lucas-academy-media"
        DATA = parent / "lucas-academy-video-data/middle-income-trap"
        break
args = sys.argv[1:]
SPEED = float(args[args.index("--speed") + 1]) if "--speed" in args else 1.2
QSPEED = float(args[args.index("--question-speed") + 1]) if "--question-speed" in args else SPEED
TAKES = MEDIA / f"outputs/yancy/zh/middle-income-trap-v3/s{SPEED:.2f}"
QTAKES = MEDIA / f"outputs/yancy/zh/middle-income-trap-v3/s{QSPEED:.2f}"
QUESTION = re.compile(r"？”?$")
CLIPS = {"A": "lilu_A_trap.mp4", "B": "lilu_B_zero_sum.mp4", "C": "lilu_C_circle.mp4"}
SR = 48000
LEAD, GAP, SECTION_GAP, BEFORE_CLIP, AFTER_CLIP, END_HOLD, QUESTION_GAP = 0.6, 0.45, 1.5, 0.6, 0.8, 8.0, 1.2
END_CARD = 1.0  # the end card comes up this long after the last line
LUFS = music_ducking.LINE_LUFS
# Music (video-plan.md): the series' licensed pieces, one per stretch, looped to fill and crossfaded; none under
# Li Lu's own voice (out QUIET[0] before a clip, back QUIET[1] after it, as in fun-informatics-03).
# Each bed starts with a chapter (its first line), so renumbered lines don't move the music.
BEDS = [("SC00", "fun-economics-01/public/fun-economics-01/music/gymnopedie-1-macleod.ogg"),
        ("SC06", "journey/music/candidates/air-bwv1068-usaf-strings.mp3"),
        ("SC07", "journey/music/jesu-gli-armonici-cc0-novocals.wav")]
BED_LUFS, XFADE, QUIET = -20.0, 4.0, (1.2, 1.0)
FINAL_LUFS, FINAL_TP = -16.0, -2.2
SRT_MAX = 22

DOCS = ROOT / "docs/middle-income-trap"
SECTION = re.compile(r"^## (SC\d\d) · (.+)$")
LINE = re.compile(r"^- (sc\d\d-\d\d) \| (.+)$")
CLIP = re.compile(r"^> 原声 ([A-Z])（.*?）｜中文字幕：(.+)$")
DIRECTED = re.compile(r"^(sc\d\d-\d\d) \| (.+)$")


def pauses() -> dict:
    out = {}
    for raw in (DOCS / "voice-direction.md").read_text().splitlines():
        if m := DIRECTED.match(raw):
            for note in m[2].split("｜")[1:]:
                if n := re.match(r"\s*停顿 ([\d.]+)", note):
                    out[m[1]] = float(n[1])
    return out


def items():
    out, section = [], None
    for raw in (DOCS / "zh-edit.md").read_text().splitlines():
        if m := SECTION.match(raw):
            section = (m[1], m[2].strip())
        elif m := LINE.match(raw):
            out.append({"kind": "line", "id": m[1], "text": m[2], "section": section})
        elif m := CLIP.match(raw):
            out.append({"kind": "clip", "id": f"clip{m[1]}", "src": CLIPS[m[1]], "text": m[2], "section": section})
    return out


def speech_bounds(y: np.ndarray) -> tuple:
    """The span above -40 dBFS, minus the stray vocoder blips CosyVoice sometimes leaves at either end: a burst of at
    most 30 ms, 80 ms or more away from the speech (5-10 ms, ~1.5-2 kHz; Yancy heard them as 哔哔, 2026-10-25)."""
    hop = int(0.005 * SR)
    env = np.sqrt(np.add.reduceat(y ** 2, np.arange(0, len(y), hop)) / hop)
    on = np.flatnonzero(20 * np.log10(env + 1e-9) > -40)
    if not len(on):
        return 0, len(y)
    runs = np.split(on, np.flatnonzero(np.diff(on) > 1) + 1)
    while len(runs) > 1 and len(runs[0]) <= 6 and runs[1][0] - runs[0][-1] >= 16:
        runs.pop(0)
    while len(runs) > 1 and len(runs[-1]) <= 6 and runs[-1][0] - runs[-2][-1] >= 16:
        runs.pop()
    return runs[0][0] * hop, (runs[-1][-1] + 1) * hop


def decode(path: Path, trim: bool) -> np.ndarray:
    with tempfile.NamedTemporaryFile(suffix=".wav") as t:
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(path), "-vn", "-ac", "1", "-ar", str(SR), t.name],
                       check=True)
        y, _ = sf.read(t.name, dtype="float32")
        if trim:  # a take: keep 20 ms before and 50 ms after the speech
            a, b = speech_bounds(y)
            y = y[max(a - int(0.02 * SR), 0):b + int(0.05 * SR)].copy()
            sf.write(t.name, y, SR)
        r = subprocess.run(["ffmpeg", "-nostats", "-i", t.name, "-af", "ebur128", "-f", "null", "-"],
                           capture_output=True, text=True)
        loud = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", r.stderr)[-1])
    y = y * (10 ** ((LUFS - loud) / 20))
    # short fades so no line or clip starts or stops with a step out of silence (a click)
    n_in, n_out = (int(0.01 * SR), int(0.03 * SR)) if trim else (int(0.15 * SR), int(0.3 * SR))
    y[:n_in] *= np.linspace(0, 1, n_in)
    y[-n_out:] *= np.linspace(1, 0, n_out)
    return y


def ffread(path: Path) -> np.ndarray:
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).copy()


def lufs(y: np.ndarray) -> float:
    with tempfile.NamedTemporaryFile(suffix=".wav") as t:
        sf.write(t.name, y, SR, subtype="FLOAT")
        r = subprocess.run(["ffmpeg", "-nostats", "-i", t.name, "-af", "ebur128", "-f", "null", "-"],
                           capture_output=True, text=True)
    return float(re.findall(r"I:\s+(-?[\d.]+) LUFS", r.stderr)[-1])


def music_mix(narration: np.ndarray, slots: dict, firsts: dict, clips: list, total: float, out: Path, lang: str = "zh") -> None:
    """Music bed under the narration (music_ducking.py), none under the clips; one gain to FINAL_LUFS, then a limiter."""
    lib = DATA.parent
    bed = np.zeros(len(narration), np.float32)
    starts = [slots[firsts[sec]][0] - (LEAD if k == 0 else 1.2) for k, (sec, _) in enumerate(BEDS)] + [total]
    for k, (cid, path) in enumerate(BEDS):
        piece = ffread(lib / path)
        piece *= 10 ** ((BED_LUFS - lufs(piece)) / 20)
        a, b = max(0.0, starts[k]), min(total, starts[k + 1] + (XFADE if k + 1 < len(BEDS) else 0))
        n = int((b - a) * SR)
        seg = np.tile(piece, int(np.ceil(n / len(piece))) + 1)[:n].copy()
        f = int(XFADE * SR)
        if k > 0:
            seg[:f] *= np.linspace(0, 1, f)
        if k + 1 < len(BEDS):
            seg[-f:] *= np.linspace(1, 0, f)
        i = int(a * SR)
        bed[i:i + n] += seg[: len(bed) - i]
    cues = [{"speech": {"start": a, "end": b}} for a, b in slots.values()]
    env_path = out / f"env.{lang}.wav"
    music_ducking.envelope(cues, total, BED_LUFS, env_path,
                           quiet=[(c["start"] - QUIET[0], c["end"] + QUIET[1]) for c in clips])
    env = ffread(env_path)
    n = min(len(env), len(bed), len(narration))
    mix = narration[:n] + bed[:n] * env[:n]
    mix *= 10 ** ((FINAL_LUFS - lufs(mix)) / 20)
    sf.write(out / f"mix.{lang}.raw.wav", mix, SR, subtype="FLOAT")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(out / f"mix.{lang}.raw.wav"), "-af",
                    f"alimiter=limit={10 ** (FINAL_TP / 20):.4f}:attack=5:release=60:level=false",
                    "-c:a", "pcm_s24le", str(out / f"mix.{lang}.wav")], check=True)


def shots(slots: dict, end_card: float, total: float) -> list:
    """edit.json with every anchor resolved: a shot's start and end in the film, its inner times from its start."""
    def at(a):
        if a == "title":
            return 0.0
        if a == "end":
            return end_card
        k, _, frac = a.partition("@")
        s, e = slots[k]
        return s + (float(frac) if frac else 0.0) * (e - s)

    edit = json.loads((ROOT / "scripts/middle-income-trap/edit.json").read_text())["shots"]
    out = []
    for i, s in enumerate(edit):
        start = at(s["at"])
        end = at(edit[i + 1]["at"]) if i + 1 < len(edit) else total
        shot = {"start": round(start, 3), "end": round(end, 3)}
        for k, v in s.items():
            if k == "at":
                continue
            if k.endswith("At"):
                v = [round(at(x) - start, 3) for x in v] if isinstance(v, list) else round(at(v) - start, 3)
            shot[k] = v
        out.append(shot)
    return out


def srt_pieces(text: str, start: float, end: float):
    parts = [p for p in re.split(r"(?<=[，。；：？！、])", text) if p.strip()]
    merged = []
    for p in parts:
        if merged and len(merged[-1]) + len(p) <= SRT_MAX:
            merged[-1] += p
        else:
            merged.append(p)
    total = sum(len(p) for p in merged)
    t = start
    for p in merged:
        d = (end - start) * len(p) / total
        yield t, t + d, p.rstrip("，。；、")
        t += d


def stamp(s: float) -> str:
    ms = int(round(s * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def main():
    gaps = pauses()
    seq = items()
    hold = LEAD + gaps.get(seq[0]["id"], 0.0)  # the title card holds before the first line
    audio, t, prev = [np.zeros(int(hold * SR), np.float32)], hold, None
    lines, clips, chapters = {}, [], []
    for it in seq:
        if prev is not None:
            first_in_section = it["section"] != prev["section"]
            if it["kind"] == "clip":
                gap = BEFORE_CLIP
            elif it["id"] in gaps:
                gap = gaps[it["id"]]
            elif prev["kind"] == "clip":
                gap = AFTER_CLIP
            else:
                gap = SECTION_GAP if first_in_section else GAP
            if prev["kind"] == "line" and QUESTION.search(prev["text"]):
                gap = max(gap, QUESTION_GAP)
            audio.append(np.zeros(int(gap * SR), np.float32))
            t += gap
        if not chapters or chapters[-1]["id"] != it["section"][0]:
            if chapters:
                chapters[-1]["end"] = round(t, 3)
            chapters.append({"id": it["section"][0], "name": it["section"][1], "start": 0.0 if not chapters else round(t, 3)})
        if it["kind"] == "line":
            wav = (QTAKES if QUESTION.search(it["text"]) else TAKES) / f"{it['id']}.wav"
            if wav.exists():
                y = decode(wav, trim=True)
            elif "--draft" in args:  # picture check only: silence as long as the line would take at ~4.6 字/s
                y = np.zeros(int(len(it["text"]) / 4.6 * SR), np.float32)
            else:
                raise SystemExit(f"missing take {wav}")
            lines[it["id"]] = {"start": round(t, 3), "end": round(t + len(y) / SR, 3), "text": it["text"]}
        else:
            y = decode(DATA / "clips" / it["src"], trim=False)
            clips.append({"id": it["id"], "src": it["src"], "start": round(t, 3), "end": round(t + len(y) / SR, 3),
                          "text": it["text"]})
        audio.append(y)
        t += len(y) / SR
        prev = it
    audio.append(np.zeros(int(END_HOLD * SR), np.float32))
    t += END_HOLD
    chapters[-1]["end"] = round(t, 3)
    narration = np.concatenate(audio)
    peak = float(np.max(np.abs(narration)))
    if peak > 0.89:
        narration *= 0.89 / peak

    out = ROOT / "out/middle-income-trap"
    (out / "delivery").mkdir(parents=True, exist_ok=True)
    sf.write(out / "narration.zh.wav", narration, SR)
    slots = {k: (v["start"], v["end"]) for k, v in lines.items()} | {c["id"]: (c["start"], c["end"]) for c in clips}
    end_card = max(v["end"] for v in lines.values()) + END_CARD
    firsts = {}
    for it in seq:
        if it["kind"] == "line":
            firsts.setdefault(it["section"][0], it["id"])
    music_mix(narration, slots, firsts, clips, t, out)
    names = json.loads((ROOT / "scripts/middle-income-trap/edit.json").read_text())["chapters"]
    for c in chapters:
        c["en"], c["enShort"] = names[c["id"]]
    timeline = {"fps": 30, "durationSeconds": round(t, 3), "speed": SPEED, "questionSpeed": QSPEED, "lines": lines, "clips": clips,
                "chapters": chapters, "shots": shots(slots, end_card, t)}
    pub = ROOT / "public/middle-income-trap"
    pub.mkdir(parents=True, exist_ok=True)
    (pub / "timeline.json").write_text(json.dumps(timeline, ensure_ascii=False, indent=1))

    cues = sorted([(v["start"], v["end"], v["text"]) for v in lines.values()] +
                  [(c["start"], c["end"], c["text"]) for c in clips])
    srt, n = [], 0
    for start, end, text in cues:
        for a, b, piece in srt_pieces(text, start, end):
            n += 1
            srt.append(f"{n}\n{stamp(a)} --> {stamp(b)}\n{piece}\n")
    (out / "delivery/middle-income-trap.zh-Hans.srt").write_text("\n".join(srt))

    print(f"{len(lines)} lines, {len(clips)} clips, {len(timeline['shots'])} shots, {t / 60:.1f} min")
    for c in chapters:
        print(f"  {stamp(c['start'])[:8]}  {c['name']}")
    if "--listen" in args:
        mp3 = DATA / (f"samples/全片试听_中文_语速{SPEED:g}.mp3" if QSPEED == SPEED else
                      f"samples/全片试听_中文_陈述{SPEED:g}_问句{QSPEED:g}.mp3")
        mp3.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(out / "narration.zh.wav"), "-ac", "2", "-b:a", "192k",
                        str(mp3)], check=True)
        print(mp3)


if __name__ == "__main__":
    main()
