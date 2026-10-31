"""Timeline, Chinese narration mix and captions for 「你爱听 AI 说「是的」吗？」, the way 「跨越中等收入陷阱」 does it.

  /Users/yqin/repo/playground/lucas-academy-video/.venv-align/bin/python scripts/ai-sycophancy/build_timeline.py [--no-music]

Reads every line's settings from narrate.py's lines.json (lucas-academy-media outputs/yancy/zh/ai-sycophancy-v1/; the
take is s<speed>/<id>.wav), the chapter names from docs/ai-sycophancy/zh-draft.md, the shots from
scripts/ai-sycophancy/edit.json and the clips' lengths from footage/selection.json in lucas-academy-video-data. A take
is trimmed at -40 dBFS (stray vocoder blips at the ends dropped), faded in and out and levelled to -23 LUFS. Lines are
GAP apart, SECTION_GAP at a new chapter, or the direction's 停顿; after a question at least QUESTION_GAP.

Each footage shot plays its clip from `in` at the rate that fits the shot (never below the clip's MIN_RATE, which
depends on its frame rate); a shot the clip cannot cover is listed and the build stops, since the fix belongs in
edit.json (a card or a chat over the rest), not a frozen frame.

Writes public/ai-sycophancy/timeline.json, out/ai-sycophancy/narration.zh.wav, out/ai-sycophancy/mix.zh.wav (with
the music) and out/ai-sycophancy/delivery/ai-sycophancy.zh-Hans.srt.
"""
import json
import re
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts/middle-income-trap"))
import build_timeline as mit  # noqa: E402  (decode, music mix, shots, captions: same as 「跨越中等收入陷阱」)

MEDIA = mit.MEDIA
DATA = next(p / "lucas-academy-video-data" for p in ROOT.parents if (p / "lucas-academy-video-data").is_dir())
TAKES = MEDIA / "outputs/yancy/zh/ai-sycophancy-v1"
FOOT = DATA / "ai-sycophancy/footage"
SR = mit.SR
LEAD, GAP, SECTION_GAP, END_HOLD, QUESTION_GAP = 0.6, 0.45, 1.5, 9.0, 1.2
END_CARD = 1.0
# music (the series' licensed beds, as in 「跨越中等收入陷阱」): each starts with a line, so the beds follow the script
BEDS = [("sc00-01", "fun-economics-01/public/fun-economics-01/music/gymnopedie-1-macleod.ogg"),
        ("sc01-18", "journey/music/candidates/air-bwv1068-usaf-strings.mp3"),
        ("sc03-01", "fun-economics-01/public/fun-economics-01/music/gymnopedie-1-macleod.ogg"),
        ("sc07-01", "journey/music/jesu-gli-armonici-cc0-novocals.wav")]
SECTION = re.compile(r"^## (SC\d\d) · (.+)$")


def min_rate(fps: str) -> float:
    """How slow a clip may play: real slow motion only from a high frame rate."""
    a, _, b = fps.partition("/")
    f = float(a) / float(b or 1)
    return 0.45 if f >= 49 else 0.75


def footage_plan(shots: list) -> list:
    clips = {s["shot"]: s for s in json.loads((FOOT / "selection.json").read_text())}
    problems = []
    for s in shots:
        if s["k"] not in ("footage", "green"):
            continue
        c = clips[s["clip"]]
        avail = float(c["probe"]["duration"]) - s.get("in", 0.0) - 0.1
        need = s["end"] - s["start"] + 0.8  # the cross-fade into the next shot plays this clip too
        rate = min(1.0, avail / need) if need > 0 else 1.0
        s["rate"] = round(max(rate, 0.3), 3)
        s["fps"] = c["probe"]["fps"]
        if rate < min_rate(c["probe"]["fps"]):
            problems.append(f"{s['clip']} at {s['start']:.1f}s: needs {need:.1f}s, has {avail:.1f}s "
                            f"(rate {rate:.2f} < {min_rate(c['probe']['fps'])})")
    return problems


def main():
    args = sys.argv[1:]
    lines_cfg = json.loads((TAKES / "lines.json").read_text())
    names, section_of = {}, {}
    for raw in (ROOT / "docs/ai-sycophancy/zh-draft.md").read_text().splitlines():
        if m := SECTION.match(raw):
            names[m[1]] = m[2].strip()
    hold = LEAD + (lines_cfg[0]["pause"] or 0.0)  # the title card holds before the first line
    audio, t, prev = [np.zeros(int(hold * SR), np.float32)], hold, None
    lines, chapters = {}, []
    for l in lines_cfg:
        sec = l["id"][:4].upper()
        if prev is not None:
            gap = l["pause"] if l["pause"] is not None else (SECTION_GAP if sec != prev[0] else GAP)
            if prev[1]:
                gap = max(gap, QUESTION_GAP)
            audio.append(np.zeros(int(gap * SR), np.float32))
            t += gap
        if not chapters or chapters[-1]["id"] != sec:
            if chapters:
                chapters[-1]["end"] = round(t, 3)
            chapters.append({"id": sec, "name": names[sec], "start": 0.0 if not chapters else round(t, 3)})
        y = mit.decode(TAKES / f"s{l['speed']:.2f}" / f"{l['id']}.wav", trim=True)
        lines[l["id"]] = {"start": round(t, 3), "end": round(t + len(y) / SR, 3), "text": l["caption"]}
        audio.append(y)
        t += len(y) / SR
        prev = (sec, l["question"])
    audio.append(np.zeros(int(END_HOLD * SR), np.float32))
    t += END_HOLD
    chapters[-1]["end"] = round(t, 3)
    narration = np.concatenate(audio)
    peak = float(np.max(np.abs(narration)))
    if peak > 0.89:
        narration *= 0.89 / peak

    out = ROOT / "out/ai-sycophancy"
    (out / "delivery").mkdir(parents=True, exist_ok=True)
    sf.write(out / "narration.zh.wav", narration, SR)
    slots = {k: (v["start"], v["end"]) for k, v in lines.items()}
    end_card = max(v["end"] for v in lines.values()) + END_CARD

    edit = json.loads((ROOT / "scripts/ai-sycophancy/edit.json").read_text())
    mit.ROOT, mit.DATA = ROOT, DATA / "ai-sycophancy"
    mit.BEDS = [(cid, path) for cid, path in BEDS]
    shots = resolve(edit["shots"], slots, end_card, t)
    problems = footage_plan(shots)
    if problems:
        print("clips too short for their shots (fix edit.json):\n  " + "\n  ".join(problems))
        if "--draft" not in args:
            raise SystemExit(1)
    if "--no-music" not in args:
        firsts = {cid: cid for cid, _ in BEDS}
        mit.music_mix(narration, slots, firsts, [], t, out)
    for c in chapters:
        c["en"], c["enShort"] = edit["chapters"][c["id"]]
    timeline = {"fps": 30, "durationSeconds": round(t, 3), "lines": lines, "chapters": chapters, "shots": shots}
    pub = ROOT / "public/ai-sycophancy"
    pub.mkdir(parents=True, exist_ok=True)
    (pub / "timeline.json").write_text(json.dumps(timeline, ensure_ascii=False, indent=1))

    srt, n = [], 0
    for start, end, text in sorted((v["start"], v["end"], v["text"]) for v in lines.values()):
        for a, b, piece in mit.srt_pieces(re.sub(r"【[^】]*】", "", text), start, end):
            n += 1
            srt.append(f"{n}\n{mit.stamp(a)} --> {mit.stamp(b)}\n{piece}\n")
    (out / "delivery/ai-sycophancy.zh-Hans.srt").write_text("\n".join(srt))
    print(f"{len(lines)} lines, {len(shots)} shots, {t / 60:.1f} min")
    for c in chapters:
        print(f"  {mit.stamp(c['start'])[:8]}  {c['name']}")


def resolve(edit: list, slots: dict, end_card: float, total: float) -> list:
    """edit.json with every anchor resolved: "sc01-02" is that line's start, "sc01-02@0.5" halfway through it."""
    def at(a):
        if a == "title":
            return 0.0
        if a == "end":
            return end_card
        k, _, frac = a.partition("@")
        s, e = slots[k]
        return s + (float(frac) if frac else 0.0) * (e - s)

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


if __name__ == "__main__":
    main()
