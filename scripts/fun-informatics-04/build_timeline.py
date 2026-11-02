"""Timeline, Chinese narration mix and captions for 「诺贝尔奖：光遗传学是什么？从信息学的角度看」 (FUN-INFORMATICS-04.md).

  /Users/yqin/repo/playground/lucas-academy-video/.venv-align/bin/python scripts/fun-informatics-04/build_timeline.py --voice louise --speed 1.1 [--lang en] [--no-music] [--draft]

Built the way 「你爱听 AI 说「是的」吗？」 is (scripts/ai-sycophancy/build_timeline.py), with the helpers of
「跨越中等收入陷阱」: every line's settings come from narrate.py's lines.json (lucas-academy-media
outputs/<voice>/zh/fun-informatics-04-v1/), a take is trimmed, faded and levelled to -23 LUFS, lines are GAP apart,
SECTION_GAP at a new chapter, or the direction's 停顿, and after a question at least QUESTION_GAP. --draft stands in
silence (as long as the caption would take to read) for takes not voiced yet, to look at the picture early.

Shots come from scripts/fun-informatics-04/edit.json; a clip plays from `in` at the rate that fits its shot, never
below MIN_RATE for its frame rate. Each shot gets the label for where its picture comes from (clips.json and
docs/fun-informatics-04/footage-sources.json): Pexels, a Commons credit, episode 1, or 「AI 生成 · 示意」.

Music: Mozart's Twinkle Variations, K. 265, Simone Renzi (CC BY 3.0), as in episode 3; each chapter its own variations,
cut at the recording's pauses (K265, from scripts/fun-informatics-03/build_timeline.py), ducked under the voice by
music_ducking.py. Writes public/fun-informatics-04/timeline.<lang>.json, out/fun-informatics-04/narration.<lang>.wav,
out/fun-informatics-04/mix.<lang>.wav and the film's own captions in out/fun-informatics-04/delivery/.

--lang en builds the English film from the same shot list: its lines have the same ids, so every anchor holds; each
shot's `…En` text replaces the Chinese, the Nobel figures go back to their English labels (no `.zh`), and episode 1's
picture comes from its English film (clips fi1en-*).
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
ARGS = sys.argv[1:]
sys.argv = sys.argv[:1]  # the shared module reads its own flags at import
import build_timeline as mit  # noqa: E402
import music_ducking  # noqa: E402

LANG = ARGS[ARGS.index("--lang") + 1] if "--lang" in ARGS else "zh"
VOICE = ARGS[ARGS.index("--voice") + 1] if "--voice" in ARGS else "louise"
SPEED = float(ARGS[ARGS.index("--speed") + 1]) if "--speed" in ARGS else 1.1
MEDIA = mit.MEDIA
DATA = next(p / "lucas-academy-video-data" for p in ROOT.parents if (p / "lucas-academy-video-data").is_dir())
TAKES = MEDIA / f"outputs/{VOICE}/{LANG}/fun-informatics-04-v1"
PUB = ROOT / "public/fun-informatics-04"
OUT = ROOT / "out/fun-informatics-04"
SR = mit.SR
LEAD, GAP, SECTION_GAP, END_HOLD, QUESTION_GAP = 1.2, 0.45, 1.5, 10.0, 1.2
END_CARD = 0.6
DRAFT_RATE = 4.0 if LANG == "zh" else 14.0  # 字/s, or letters/s in English, for a line not voiced yet (--draft only)
SECTION = re.compile(r"^## (OG\d\d) · (.+)$")
CAPTION = re.compile(r"^- (og\d\d-\d\d) \| (.+)$")
QUESTION = re.compile(r"[？?][」”\"]?$")

MUSIC_SOURCE = DATA / "fun-informatics-03/public/music/mozart-k265-renzi.mp3"
K265 = {  # seconds in the recording (scripts/fun-informatics-03/build_timeline.py)
    "theme": (3.85, 47.85), "v1": (49.0, 89.8), "v2": (91.15, 132.5), "v3": (134.1, 176.15), "v4": (178.45, 218.55),
    "v5": (220.85, 260.4), "v6": (261.35, 303.0), "v7": (303.95, 345.7), "v8": (349.45, 397.85), "v9": (401.55, 452.9),
    "v10": (456.25, 496.0), "v11": (498.25, 651.1), "v12": (652.45, 724.25),
}
MUSIC_PLAN = {
    "OG00": ["theme", "v5"],        # the tune everyone knows, under the green water
    "OG01": ["v2"],
    "OG02": ["v1", "v3", "v4"],     # the discovery, lively
    "OG03": ["v6"],
    "OG04": ["v8"],                 # the eye, quieter
    "OG05": ["v10", "v12"],
    "OG06": ["v11"],                # the slow variation under the verses, the theme comes back to end the film
}
SECTION_XF, THEME_TAIL = 2.5, 1.0
WORDS = {
    "zh": {"pexels": "实拍 · Pexels", "ai": "AI 生成 · 示意", "fi1": "画面 · 趣味信息学 1",
           "nobel": "图 · 诺贝尔生理学或医学奖委员会，Mattias Karlén 绘", "lab": "真实实验录像 · {who} 等 · Wikimedia Commons · {lic}"},
    "en": {"pexels": "Footage · Pexels", "ai": "AI-generated · illustrative", "fi1": "Picture · Fun Informatics 1",
           "nobel": "Illustration · The Nobel Committee for Physiology or Medicine, Ill. Mattias Karlén",
           "lab": "Lab recording · {who} et al. · Wikimedia Commons · {lic}"},
}[LANG]
AI = WORDS["ai"]
TEXT_KEYS = ("lower", "big", "lines", "verse", "ref", "ask", "ringText", "label")


def min_rate(fps: str) -> float:
    a, _, b = fps.partition("/")
    return 0.45 if float(a) / float(b or 1) >= 49 else 0.75


def label(shot: dict, clips: dict, sources: dict) -> str:
    if shot["k"] in ("still",):
        return AI
    if shot["k"] == "nobel":
        return WORDS["nobel"]
    if "clip" not in shot:
        return ""
    src = clips[shot["clip"]]["source"]
    if src.startswith("pexels:"):
        return f"{WORDS['pexels']} · {sources['pexels'][src[7:]]['by']}"
    if src.startswith("commons:"):
        c = sources["commons"][src[8:]]
        return WORDS["lab"].format(who=c["by"].split(",")[0].rsplit(" ", 1)[0], lic=c["license"])
    return {"muse": AI, "fi1": WORDS["fi1"]}[src]


def localize(shot: dict) -> dict:
    """The English film's version of a shot: its …En words, the Nobel figures' own English labels, episode 1's
    English picture. The Chinese film keeps the shot as it is, minus the English."""
    out = {}
    for k, v in shot.items():
        if k.endswith("En"):
            continue
        out[k] = v
    if LANG == "en":
        for k in TEXT_KEYS:
            if f"{k}En" in shot:
                out[k] = shot[f"{k}En"]
        if out.get("img", "").endswith(".zh.jpg"):
            out["img"] = out["img"].replace(".zh.jpg", ".jpg")
        if out.get("clip", "").startswith("fi1-"):
            out["clip"] = "fi1en-" + out["clip"][4:]
    return out


def footage_plan(shots: list, clips: dict) -> list:
    problems = []
    for s in shots:
        if "clip" not in s:
            continue
        c = clips[s["clip"]]["probe"]
        avail = c["duration"] - s.get("in", 0.0) - 0.1
        need = s["end"] - s["start"] + 0.8  # the cross-fade into the next shot plays this clip too
        rate = min(1.0, avail / need) if need > 0 else 1.0
        s["rate"] = round(max(rate, 0.3), 3)
        if rate < min_rate(c["fps"]):
            problems.append(f"{s['clip']} at {s['start']:.1f}s: needs {need:.1f}s, has {avail:.1f}s (rate {rate:.2f})")
    return problems


def music(total: float, chapters: list) -> np.ndarray:
    """Each chapter's variations in order, trimmed to the chapter and crossfaded into the next; the last chapter's
    slow variation hands over to the theme, which ends THEME_TAIL before the film does."""
    src = mit.ffread(MUSIC_SOURCE)
    seg = lambda n: src[int(K265[n][0] * SR):int(K265[n][1] * SR)].copy()
    bed = np.zeros(int(total * SR) + SR, np.float32)
    f = int(SECTION_XF * SR)
    for i, ch in enumerate(chapters):
        a = 0.0 if i == 0 else ch["start"] - 1.2
        b = chapters[i + 1]["start"] - 1.2 + SECTION_XF if i + 1 < len(chapters) else total - THEME_TAIL
        piece = np.concatenate([seg(n) for n in MUSIC_PLAN[ch["id"]]])
        if i + 1 == len(chapters):  # the closing theme takes the end of the film
            theme = seg("theme")
            room = int((b - a) * SR) - len(theme) + f
            body = piece[:max(room, f * 2)].copy()
            body[-f:] *= np.linspace(1, 0, f)
            theme[:f] *= np.linspace(0, 1, f)
            out = np.zeros(len(body) + len(theme) - f, np.float32)
            out[:len(body)] += body
            out[len(body) - f:] += theme
            piece = out
        n = min(int((b - a) * SR), len(piece))
        piece = piece[:n].copy()
        if i > 0:
            piece[:f] *= np.linspace(0, 1, f)
        if i + 1 < len(chapters) and n == int((b - a) * SR):
            piece[-f:] *= np.linspace(1, 0, f)
        k = int(a * SR)
        bed[k:k + n] += piece[:len(bed) - k]
    return bed[: int(total * SR)]


def main():
    draft = "--draft" in ARGS
    lines_cfg = json.loads((TAKES / "lines.json").read_text()) if (TAKES / "lines.json").exists() else None
    names, captions = {}, {}
    for raw in (ROOT / f"docs/fun-informatics-04/{LANG}-draft.md").read_text().splitlines():
        if m := SECTION.match(raw):
            names[m[1]] = m[2].strip()
        elif m := CAPTION.match(raw):
            captions[m[1]] = m[2]
    if lines_cfg is None:
        if not draft:
            raise SystemExit(f"no takes in {TAKES}; run narrate.py first, or --draft")
        sys.path.insert(0, str(ROOT / "scripts/fun-informatics-04"))
        sys.argv = ["narrate.py", "--lang", LANG, "--voice", VOICE, "--speed", str(SPEED)]
        import narrate  # noqa: E402
        lines_cfg = narrate.load()
    hold = LEAD + (lines_cfg[0]["pause"] or 0.0)
    audio, t, prev = [np.zeros(int(hold * SR), np.float32)], hold, None
    lines, chapters, missing = {}, [], []
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
            chapters.append({"id": sec, "name": names[sec].split(" ｜")[0], "start": 0.0 if not chapters else round(t, 3)})
        take = TAKES / f"s{l['speed']:.2f}" / f"{l['id']}.wav"
        if take.exists():
            y = mit.decode(take, trim=True)
        elif draft:
            missing.append(l["id"])
            y = np.zeros(int(len(re.sub(r"[，。、；：？！「」“”\s]", "", l["caption"])) / DRAFT_RATE * SR), np.float32)
        else:
            raise SystemExit(f"missing take {take}")
        lines[l["id"]] = {"start": round(t, 3), "end": round(t + len(y) / SR, 3), "text": captions[l["id"]]}
        audio.append(y)
        t += len(y) / SR
        prev = (sec, bool(QUESTION.search(captions[l["id"]])))
    audio.append(np.zeros(int(END_HOLD * SR), np.float32))
    t += END_HOLD
    chapters[-1]["end"] = round(t, 3)
    narration = np.concatenate(audio)
    peak = float(np.max(np.abs(narration)))
    if peak > 0.89:
        narration *= 0.89 / peak

    (OUT / "delivery").mkdir(parents=True, exist_ok=True)
    sf.write(OUT / f"narration.{LANG}.wav", narration, SR)
    slots = {k: (v["start"], v["end"]) for k, v in lines.items()}
    end_card = max(v["end"] for v in lines.values()) + END_CARD

    edit = json.loads((ROOT / "scripts/fun-informatics-04/edit.json").read_text())
    clips = json.loads((PUB / "clips.json").read_text())
    sources = json.loads((ROOT / "docs/fun-informatics-04/footage-sources.json").read_text())
    shots = [localize(s) for s in mit_resolve(edit["shots"], slots, end_card, t)]
    for s in shots:
        s["label"] = label(s, clips, sources)
        if "clip" in s:
            s["shape"] = clips[s["clip"]]["shape"]
    problems = footage_plan(shots, clips)
    if problems:
        print("clips too short for their shots (fix edit.json):\n  " + "\n  ".join(problems))
        if not draft:
            raise SystemExit(1)
    if "--no-music" not in ARGS:
        bed = music(t, chapters)
        bed *= 10 ** ((mit.BED_LUFS - mit.lufs(bed)) / 20)
        cues = [{"speech": {"start": a, "end": b}} for a, b in slots.values()]
        music_ducking.envelope(cues, t, mit.BED_LUFS, OUT / f"env.{LANG}.wav")
        env = mit.ffread(OUT / f"env.{LANG}.wav")
        n = min(len(env), len(bed), len(narration))
        mix = narration[:n] + bed[:n] * env[:n]
        mix *= 10 ** ((mit.FINAL_LUFS - mit.lufs(mix)) / 20)
        sf.write(OUT / f"mix.{LANG}.raw.wav", mix, SR, subtype="FLOAT")
        import subprocess
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(OUT / f"mix.{LANG}.raw.wav"), "-af",
                        f"alimiter=limit={10 ** (mit.FINAL_TP / 20):.4f}:attack=5:release=60:level=false",
                        "-c:a", "pcm_s24le", str(OUT / f"mix.{LANG}.wav")], check=True)
    for c in chapters:
        c["en"], c["enShort"] = edit["chapters"][c["id"]]
        if LANG == "en":
            c["name"] = c["en"]
    timeline = {"fps": 30, "durationSeconds": round(t, 3), "lines": lines, "chapters": chapters, "shots": shots,
                "draft": bool(missing)}
    PUB.mkdir(parents=True, exist_ok=True)
    (PUB / f"timeline.{LANG}.json").write_text(json.dumps(timeline, ensure_ascii=False, indent=1))

    srt, n = [], 0
    if LANG == "zh":
        for start, end, text in sorted((v["start"], v["end"], v["text"]) for v in lines.values()):
            for a, b, piece in mit.srt_pieces(re.sub(r"【[^】]*】", "", text), start, end):
                n += 1
                srt.append(f"{n}\n{mit.stamp(a)} --> {mit.stamp(b)}\n{piece}\n")
        (OUT / "delivery/fun-informatics-04.zh.zh-Hans.srt").write_text("\n".join(srt))
    else:  # English captions: two lines of at most 42 letters (captions.py)
        sys.path.insert(0, str(ROOT / "scripts/fun-informatics-04"))
        import captions  # noqa: E402
        for start, end, text in sorted((v["start"], v["end"], v["text"]) for v in lines.values()):
            parts = captions.pieces(text)
            total, t0 = sum(len(p) for p in parts), start
            for part in parts:
                t1 = t0 + (end - start) * len(part) / total
                n += 1
                srt.append(f"{n}\n{mit.stamp(t0)} --> {mit.stamp(t1)}\n{captions.two_lines(part)}\n")
                t0 = t1
        (OUT / "delivery/fun-informatics-04.en.en.srt").write_text("\n".join(srt))
    print(f"{len(lines)} lines, {len(shots)} shots, {t / 60:.1f} min" + (f", {len(missing)} not voiced yet" if missing else ""))
    for c in chapters:
        print(f"  {mit.stamp(c['start'])[:8]}  {c['name']}")


def mit_resolve(edit: list, slots: dict, end_card: float, total: float) -> list:
    """edit.json with every anchor resolved: "og01-02" is that line's start, "og01-02@0.5" halfway through it."""
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
