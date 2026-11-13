"""Timeline, narration mix and captions for 「动物想什么？AI 知道吗？」 (AI-ANIMAL-TALK.md, docs/ai-animal-mind/).

  /Users/yqin/repo/playground/lucas-academy-video/.venv-align/bin/python scripts/ai-animal-mind/build_timeline.py [--lang en|zh] [--draft]

One picture, two voice tracks (Yancy 2026-11-10: English first with Louise, the Chinese track after the English is
confirmed; nothing written on screen). So every line gets one slot shared by both languages: the longer of its
English and its Chinese take, or, for a language not voiced yet, an estimate (English 14 letters/s, Chinese 3.6 字/s,
Louise's measured 3.75-3.9), never lengthening a voiced line by more than PAD_CAP. Lines are GAP apart, SECTION_GAP at a new section, the
direction's 停顿 when it has one, and at least QUESTION_GAP after a question. A voice starts at its slot's start. The
picture (scripts/ai-animal-mind/edit.json, anchored to line ids) is therefore the same for both tracks. With both
languages voiced (11-11) every slot is simply the longer take; the cost is the padding in the shorter track (printed).

Music (owner's rule: it ducks under every voice, music_ducking.py): Mozart's Twelve Variations on "Ah vous dirai-je,
Maman", K. 265, Simone Renzi (CC BY 3.0, as in Fun Informatics 3 and 4), each section its own variations; from
edit.json's jesu point on, Bach's "Jesu, Joy of Man's Desiring" (Gli Armonici, CC0, choir removed) from 148.1 s, the
same moment as the picture taken from the Jesu film, to the end of the film. edit.json's `boost` lifts the music in
the looking moments (the cats and dogs, the other animals, the Bach after am12-04).

Real animal sounds (Yancy 2026-11-11: 「讲动物声音的时候，有没有真实的动物声音样本可以试听呢？」): edit.json's `sounds`
puts a recording (docs/ai-animal-mind/sound-sources.json, files in lucas-academy-video-data/ai-animal-mind/sounds/raw)
in the gap after a line: the gap grows to fit it, in both tracks alike, and the music fades right out under it so the
animal is heard on its own (`"bed": true` keeps the music at its under-the-voice level instead: the elephant rumble,
mostly below 150 Hz, is close to silent on a phone). The music stays down from the end of the line to the recording.
Several entries after one line play one after another.

Writes public/ai-animal-mind/timeline.json (shots, line slots), out/ai-animal-mind/narration.<lang>.wav,
mix.<lang>.wav and delivery/ai-animal-mind.<lang>.{en,zh-Hans}.srt (each track gets both caption languages).
--draft stands in silence for lines not voiced yet.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts/middle-income-trap"))
ARGS = sys.argv[1:]
sys.argv = sys.argv[:1]  # the shared module reads its own flags at import
import build_timeline as mit  # noqa: E402
import music_ducking  # noqa: E402

sys.path.insert(0, str(ROOT / "scripts/fun-informatics-04"))
import captions as fi4captions  # noqa: E402

LANG = ARGS[ARGS.index("--lang") + 1] if "--lang" in ARGS else "en"
DRAFT = "--draft" in ARGS
MEDIA = mit.MEDIA
DATA = next(p / "lucas-academy-video-data" for p in ROOT.parents if (p / "lucas-academy-video-data").is_dir())
DOCS = ROOT / "docs/ai-animal-mind"
PUB = ROOT / "public/ai-animal-mind"
OUT = ROOT / "out/ai-animal-mind"
SR = mit.SR
VOICE, SPEED = "louise", 1.1
TAKES = {lang: MEDIA / f"outputs/{VOICE}/{lang}/ai-animal-mind-v1/s{SPEED:.2f}" for lang in ("en", "zh")}
LEAD, GAP, SECTION_GAP, QUESTION_GAP, FADE = 1.6, 0.45, 1.5, 1.2, 0.6
RATE = {"en": 14.0, "zh": 3.8}  # letters/s, 字/s: the estimate for a language not voiced yet (Louise zh 1.1: 3.75-3.9)
PAD_CAP = 1.2  # an estimate may lengthen a voiced line's slot by at most this; a longer Chinese take is fitted when it exists
EDIT = json.loads((ROOT / "scripts/ai-animal-mind/edit.json").read_text())
CAPTION = re.compile(r"^- (am\d\d-\d\d) \| (.+)$")
QUESTION = re.compile(r"[？?][」”\"]?$")

K265_SOURCE = DATA / "fun-informatics-03/public/music/mozart-k265-renzi.mp3"
K265 = {  # seconds in the recording (scripts/fun-informatics-03/build_timeline.py)
    "theme": (3.85, 47.85), "v1": (49.0, 89.8), "v2": (91.15, 132.5), "v3": (134.1, 176.15), "v4": (178.45, 218.55),
    "v5": (220.85, 260.4), "v6": (261.35, 303.0), "v7": (303.95, 345.7), "v8": (349.45, 397.85), "v9": (401.55, 452.9),
    "v10": (456.25, 496.0), "v11": (498.25, 651.1), "v12": (652.45, 724.25),
}
SOUNDS = DATA / "ai-animal-mind/sounds/raw"
SND_LEAD, SND_BETWEEN, SND_TAIL, SND_FADE = 0.5, 0.6, 0.9, (0.06, 0.3)  # s: after the line, between two, before the next line
SND_PEAK = 0.5  # -6 dBFS at the voices' level: clicks and squeals stay below the lines' own peaks
JESU_SOURCE = DATA / "jesu/music/jesu-gli-armonici-novocals-ft-noapplause.wav"
JESU_END = 193.0  # the music ends 192.5; the file fades out by 193.0 (edit.json of the Jesu film)
SECTION_XF, JESU_XF = 2.5, 3.0


def captions(lang: str) -> dict:
    out = {}
    for raw in (DOCS / f"{lang}-draft.md").read_text().splitlines():
        if m := CAPTION.match(raw):
            out[m[1]] = m[2]
    return out


def direction() -> list:
    """Line order, pauses and question flags from the English direction (narrate.py)."""
    sys.argv = ["narrate.py", "--lang", "en"]
    sys.path.insert(0, str(ROOT / "scripts/ai-animal-mind"))
    import narrate  # noqa: E402
    return narrate.load()


def estimate(lang: str, text: str) -> float:
    if lang == "zh":
        return len(re.sub(r"[，。、；：？！「」“”《》…\s]", "", text)) / RATE["zh"]
    return len(re.sub(r"[^A-Za-z]", "", text)) / RATE["en"]


def take(lang: str, lid: str):
    path = TAKES[lang] / f"{lid}.wav"
    return mit.decode(path, trim=True) if path.exists() else None


def at_fn(slots: dict, special: dict):
    def at(a: str) -> float:
        if a in special:
            return special[a]
        if (m := re.match(r"^(title|jesu)\+([\d.]+)$", a)):
            return special[m[1]] + float(m[2])
        m = re.match(r"^(am\d\d-\d\d)(?:@([\d.]+)|\+([\d.]+)|-([\d.]+))?$", a)
        s, e = slots[m[1]]
        if m[2]:
            return s + float(m[2]) * (e - s)
        if m[3]:
            return e + float(m[3])
        if m[4]:
            return s - float(m[4])
        return s
    return at


def min_rate(fps: str, muse: bool = False) -> float:
    a, _, b = fps.partition("/")
    return 0.45 if float(a) / float(b or 1) >= 49 else 0.55 if muse else 0.7


def sound_clip(e: dict) -> np.ndarray:
    """One recording: e["src"] from e["in"] for e["dur"] s (the whole file without "dur"), through e["af"] (an ffmpeg
    filter: high-pass against DC offset and rumble, a bass lift for the elephants), levelled to the voices (+ e["db"])
    but never peaking above SND_PEAK, with short fades. A call shorter than a second is measured repeated, since
    loudness needs 400 ms blocks."""
    cmd = ["ffmpeg", "-v", "error", "-ss", f"{e.get('in', 0.0)}", "-i", str(SOUNDS / e["src"])]
    if e.get("dur"):
        cmd += ["-t", f"{e['dur']}"]
    if e.get("af"):
        cmd += ["-af", e["af"]]
    raw = subprocess.run(cmd + ["-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True).stdout
    y = np.frombuffer(raw, np.float32).copy()
    probe = np.tile(y, int(np.ceil(1.5 * SR / len(y)))) if len(y) < SR else y
    gain = 10 ** ((music_ducking.LINE_LUFS + e.get("db", 0.0) - mit.lufs(probe)) / 20)
    y *= min(gain, SND_PEAK / max(1e-6, float(np.abs(y).max())))
    a, b = int(SND_FADE[0] * SR), int(min(SND_FADE[1], len(y) / SR / 4) * SR)
    y[:a] *= np.linspace(0, 1, a)
    y[-b:] *= np.linspace(1, 0, b)
    return y


def music_bed(total: float, sections: list, jesu_at: float) -> np.ndarray:
    """K. 265 section by section (each piece levelled on its own), then the Bach from jesu_at to its end."""
    src = mit.ffread(K265_SOURCE)
    seg = lambda n: src[int(K265[n][0] * SR):int(K265[n][1] * SR)].copy()
    bed = np.zeros(int(total * SR) + SR, np.float32)
    f = int(SECTION_XF * SR)
    body = [s for s in sections if s["id"] in EDIT["music"] and s["start"] < jesu_at]
    for i, sec in enumerate(body):
        a = 0.0 if i == 0 else sec["start"] - 1.2
        b = (body[i + 1]["start"] - 1.2 + SECTION_XF) if i + 1 < len(body) else jesu_at + JESU_XF
        names = list(EDIT["music"][sec["id"]])
        order = list(K265)
        while sum(K265[x][1] - K265[x][0] for x in names) < b - a:  # too short: go on with the next variations
            names.append(order[(order.index(names[-1]) + 1) % len(order)])
        piece = np.concatenate([seg(x) for x in names])
        piece *= 10 ** ((mit.BED_LUFS - mit.lufs(piece)) / 20)
        n = min(int((b - a) * SR), len(piece))
        piece = piece[:n].copy()
        if i > 0:
            piece[:f] *= np.linspace(0, 1, f)
        tail = int((JESU_XF if i + 1 == len(body) else SECTION_XF) * SR)
        piece[-min(tail, n):] *= np.linspace(1, 0, min(tail, n))
        k = int(a * SR)
        bed[k:k + n] += piece[:len(bed) - k]
    jesu = mit.ffread(JESU_SOURCE)[int(EDIT["jesu"]["in"] * SR):int(JESU_END * SR)].copy()
    jesu *= 10 ** ((mit.BED_LUFS - mit.lufs(jesu)) / 20)
    g = int(JESU_XF * SR)
    jesu[:g] *= np.linspace(0, 1, g)
    k = int(jesu_at * SR)
    bed[k:k + len(jesu)] += jesu[:len(bed) - k]
    # if the last lines run past the Bach, the K. 265 theme from the opening comes back softly to end the film
    bach_end = jesu_at + JESU_END - EDIT["jesu"]["in"]
    if total - bach_end > 2.0:
        theme = seg("theme")
        theme *= 10 ** ((mit.BED_LUFS - 3.0 - mit.lufs(theme)) / 20)
        a = bach_end - 1.0
        n = min(len(theme), int((total - a) * SR))
        theme = theme[:n].copy()
        theme[:g] *= np.linspace(0, 1, g)
        k = int(a * SR)
        bed[k:k + n] += theme[:len(bed) - k]
    return bed[: int(total * SR)]


def boosts(env: np.ndarray, slots: dict) -> np.ndarray:
    """Lift the music between two lines by db (edit.json boost), easing in and out over a second."""
    for a, b, db in EDIT["boost"]:
        lo, hi = slots[a][1] + music_ducking.RELEASE, slots[b][0] - music_ducking.ATTACK
        if hi - lo < 1.0:
            continue
        t = np.arange(len(env)) / SR
        ramp = np.clip(np.minimum((t - lo) / 1.0, (hi - t) / 1.0), 0, 1)
        env *= 10 ** (db * ramp / 20)
    return env


def main():
    lines_cfg = direction()
    cap = {"en": captions("en"), "zh": captions("zh")}
    takes = {l["id"]: {lang: take(lang, l["id"]) for lang in ("en", "zh")} for l in lines_cfg}
    missing = [l["id"] for l in lines_cfg if takes[l["id"]][LANG] is None]
    if missing and not DRAFT:
        raise SystemExit(f"{len(missing)} {LANG} takes missing ({missing[:4]}...); voice them or use --draft")

    after = {}
    for e in EDIT.get("sounds", []):
        after.setdefault(e["after"], []).append(e)
    sounds = []  # (start, clip, entry)
    t, prev, slots, sections, voice, pads = LEAD, None, {}, [], {}, {}
    for l in lines_cfg:
        sec = l["id"][:4].upper()
        if prev is not None:
            gap = l["pause"] if l["pause"] is not None else (SECTION_GAP if sec != prev[0] else GAP)
            if prev[1]:
                gap = max(gap, QUESTION_GAP)
            if prev[2] in after:
                u = t + SND_LEAD
                for e in after[prev[2]]:
                    y = sound_clip(e)
                    sounds.append((u, y, e))
                    u += len(y) / SR + e.get("gap", SND_BETWEEN)
                gap = max(gap, u - after[prev[2]][-1].get("gap", SND_BETWEEN) + SND_TAIL - t)
            t += gap
        if not sections or sections[-1]["id"] != sec:
            sections.append({"id": sec, "start": round(t, 3)})
        lens, real = [], []
        for lang in ("en", "zh"):
            y = takes[l["id"]][lang]
            lens.append(len(y) / SR if y is not None else estimate(lang, cap[lang][l["id"]]))
            if y is not None:
                real.append(len(y) / SR)
        slot = max(lens) if len(real) != 1 else min(max(lens), real[0] + PAD_CAP)
        slot = max([slot, *real])
        pads[l["id"]] = slot - (len(takes[l["id"]][LANG]) / SR if takes[l["id"]][LANG] is not None else slot)
        slots[l["id"]] = (round(t, 3), round(t + slot, 3))
        y = takes[l["id"]][LANG]
        voice[l["id"]] = (t, y if y is not None else np.zeros(int(estimate(LANG, cap[LANG][l["id"]]) * SR), np.float32))
        t += slot
        prev = (sec, l["question"], l["id"])
    padded = sorted(((round(v, 2), k) for k, v in pads.items() if v > 0.05), reverse=True)
    print(f"slot padding in the {LANG} track: {sum(pads.values()):.1f} s over {len(padded)} lines; longest: "
          + ", ".join(f"{k} {v}s" for v, k in padded[:6]))

    jesu_at = slots[EDIT["jesu"]["anchor"]][0] - EDIT["jesu"]["lead"]
    last_end = max(e for _, e in slots.values())
    total = round(max(last_end + 7.0, jesu_at + (JESU_END - EDIT["jesu"]["in"]) + 1.5), 3)

    narration = np.zeros(int(total * SR) + SR, np.float32)
    for lid, (start, y) in voice.items():
        k = int(start * SR)
        narration[k:k + len(y)] += y
    narration = narration[: int(total * SR)]
    sfx = np.zeros_like(narration)
    for start, y, _ in sounds:
        k = int(start * SR)
        sfx[k:k + len(y)] += y[:len(sfx) - k]
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "delivery").mkdir(exist_ok=True)
    sf.write(OUT / f"narration.{LANG}.wav", narration, SR)

    # the picture
    clips = json.loads((PUB / "clips.json").read_text())
    at = at_fn(slots, {"title": 0.0, "jesu": jesu_at})
    edit = EDIT["shots"]
    shots, problems = [], []
    for i, s in enumerate(edit):
        start = at(s["at"])
        end = at(edit[i + 1]["at"]) if i + 1 < len(edit) else total
        shot = {k: v for k, v in s.items() if k != "at"}
        shot.update(start=round(start, 3), end=round(end, 3))
        if s["k"] == "muse":
            c = clips.get(f"muse-{s['g']}")
            short = c and c["probe"]["duration"] / (end - start + FADE) < 0.55
            if short:
                print(f"note: Muse {s['g']} lasts {c['probe']['duration']:.1f} s but its shot needs {end - start + FADE:.1f} s;"
                      " showing its first frame instead (ask for a longer clip, or split the shot)")
            if c and not short:
                shot.update(k="clip", clip=f"muse-{s['g']}")
            else:
                ref = sorted((DATA / "ai-animal-mind/references").glob(f"{s['g']}-*.png"))
                shot.update(k="still", img=ref[0].name)
        if s["k"] == "jesu":
            shot.update(k="clip", clip="jesu", rate=1.0, plain=True)
        if shot["k"] == "clip":
            c = clips.get(shot["clip"])
            if c is None:
                problems.append(f"{shot['clip']} not staged")
                continue
            avail = c["probe"]["duration"] - shot.get("in", 0.0) - 0.1
            need = end - start + FADE
            rate = shot.get("rate") or min(1.0, avail / need)
            shot["rate"] = round(max(rate, 0.3), 3)
            if rate < min_rate(c["probe"]["fps"], shot["clip"].startswith("muse-")):
                problems.append(f"{shot['clip']} at {start:.1f}s: needs {need:.1f}s, has {avail:.1f}s (rate {rate:.2f})")
        shots.append(shot)
    if end <= start:
        problems.append("shots out of order")
    for a, b in zip(shots, shots[1:]):
        if b["start"] <= a["start"]:
            problems.append(f"shot at {b['start']} does not come after {a['start']} ({b.get('clip') or b.get('img')})")
    if problems:
        print("picture problems (fix edit.json):\n  " + "\n  ".join(problems))
        if not DRAFT:
            raise SystemExit(1)

    # the music, ducked under this track's voice
    bed = music_bed(total, sections, jesu_at)
    cues = [{"speech": {"start": voice[k][0], "end": voice[k][0] + len(voice[k][1]) / SR}} for k in voice]
    spans = [(a, a + len(y) / SR) for a, y, _ in sounds]
    cues += [{"speech": {"start": a, "end": b}} for a, b in spans]
    first = {}
    for a, _, e in sounds:
        first.setdefault(e["after"], a)
    cues += [{"speech": {"start": voice[k][0] + len(voice[k][1]) / SR, "end": a}} for k, a in first.items()]
    quiet = [(a, a + len(y) / SR) for a, y, e in sounds if not e.get("bed")]
    music_ducking.envelope(cues, total, mit.BED_LUFS, OUT / f"env.{LANG}.wav", quiet=quiet)
    env = boosts(mit.ffread(OUT / f"env.{LANG}.wav"), slots)
    n = min(len(env), len(bed), len(narration))
    mix = narration[:n] + sfx[:n] + bed[:n] * env[:n]
    mix *= 10 ** ((mit.FINAL_LUFS - mit.lufs(mix)) / 20)
    sf.write(OUT / f"mix.{LANG}.raw.wav", mix, SR, subtype="FLOAT")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(OUT / f"mix.{LANG}.raw.wav"), "-af",
                    f"alimiter=limit={10 ** (mit.FINAL_TP / 20):.4f}:attack=5:release=60:level=false",
                    "-c:a", "pcm_s24le", str(OUT / f"mix.{LANG}.wav")], check=True)

    timeline = {"fps": 30, "durationSeconds": total, "shots": shots, "draft": bool(missing),
                "lines": {k: {"start": s, "end": e} for k, (s, e) in slots.items()}, "jesuAt": round(jesu_at, 3),
                "sounds": [{"name": e.get("name", e["src"]), "start": round(a, 3), "end": round(a + len(y) / SR, 3)}
                           for a, y, e in sounds]}
    PUB.mkdir(parents=True, exist_ok=True)
    (PUB / "timeline.json").write_text(json.dumps(timeline, ensure_ascii=False, indent=1))

    # captions: this track's own speech times, both languages
    spans = {k: (voice[k][0], voice[k][0] + len(voice[k][1]) / SR) for k in voice}
    for cl in ("en", "zh"):
        srt, n = [], 0
        for lid, (s, e) in sorted(spans.items(), key=lambda kv: kv[1][0]):
            text = cap[cl][lid]
            if cl == "zh":
                parts = list(mit.srt_pieces(text, s, e))
            else:
                ps = fi4captions.pieces(text)
                tot, t0, parts = sum(len(p) for p in ps), s, []
                for p in ps:
                    t1 = t0 + (e - s) * len(p) / tot
                    parts.append((t0, t1, fi4captions.two_lines(p)))
                    t0 = t1
            for a, b, piece in parts:
                n += 1
                srt.append(f"{n}\n{mit.stamp(a)} --> {mit.stamp(b)}\n{piece}\n")
        tag = "zh-Hans" if cl == "zh" else "en"
        (OUT / f"delivery/ai-animal-mind.{LANG}.{tag}.srt").write_text("\n".join(srt))
    print(f"{len(slots)} lines, {len(shots)} shots, {total / 60:.2f} min ({total:.1f} s); Bach from {jesu_at:.1f} s"
          + (f"; {len(missing)} {LANG} lines not voiced yet" if missing else ""))
    for s in sections:
        print(f"  {mit.stamp(s['start'])[:8]}  {s['id']}")
    for a, y, e in sounds:
        print(f"  sound {mit.stamp(a)[:8]} {len(y) / SR:.1f} s  {e.get('name', e['src'])} (after {e['after']})")


if __name__ == "__main__":
    main()
