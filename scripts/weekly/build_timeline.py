"""好奇新世界: lay an episode out on one shared timeline (WEEKLY-DEMO-PLAN.md: one Chinese film + an English dub track).

A block lasts its lines plus a pad, or "min" seconds if its footage needs longer; "hold" {line: s} lets the
picture run on after a line, so the next line meets its moment in the recording. Every line gets one slot, as long as the longer of its two takes plus a short pause, so both tracks start each line at
the same moment and one picture and one pair of SRTs serve both. The picture follows scripts/weekly/<ep>/shots.py.
Until a line is voiced its length is estimated from its text, and the timeline is marked draft.

  python3 scripts/weekly/build_timeline.py 001 [zh|en]      (both when no language is given)
writes public/weekly/<ep>/timeline.<lang>.json (read by the WeeklyEpisode composition) and prints the chapters.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from assets import ROOT, load_shots  # noqa: E402

FPS = 30
GAP = 0.45   # between two lines in a block
LEAD = 0.6   # from a block's first frame to its first line
PAD = 0.8    # after a block's last line
LINE = re.compile(r"^- ([a-z]{2}\d\d-\d\d) \| (.+)$")
TRANSLATION = re.compile(r"^\s+> (.+)$")
SECTION = re.compile(r"^## ([A-Z]{2}\d\d) · (.+?)(?:（.*）)?$")


def parse_script(ep: str) -> dict:
    cues, last, section = {}, None, None
    for raw in (ROOT / "docs/weekly" / ep / "zh-edit.md").read_text(encoding="utf-8").splitlines():
        if m := SECTION.match(raw):
            section = m[1].lower()
        elif m := LINE.match(raw):
            last = m[1]
            assert last.startswith(section), f"{last} is not under {section}"
            cues[last] = {"id": last, "section": section, "zh": re.sub(r"</?strong>", "", m[2].strip())}
        elif (m := TRANSLATION.match(raw)) and last:
            cues[last]["en"] = re.sub(r"</?strong>", "", m[1].strip())
            last = None
    missing = [c for c, v in cues.items() if "en" not in v]
    assert not missing, f"no > English line under {missing}"
    return cues


def duration(path: Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                         capture_output=True, text=True, check=True)
    return float(out.stdout.strip())


def estimate(lang: str, text: str) -> float:
    if lang == "zh":  # Fangfang at 1.15: about 5 characters a second
        return 0.35 + len(re.findall(r"[一-鿿]", text)) / 5.0 + 0.12 * len(re.findall(r"[，、；：]", text))
    return 0.35 + len(text.split()) / 2.5 + 0.1 * len(re.findall(r"[,;:]", text))


def pick(value, lang: str):
    """A {"zh": …, "en": …} value is the film's own; anything else is shared."""
    return value[lang] if isinstance(value, dict) and set(value) <= {"zh", "en"} else value


class Sources:
    """Where a film's pictures are and what a recording's marks are."""

    def __init__(self, pub: Path, lang: str):
        self.pub, self.lang, self.cache = pub, lang, {}

    def path(self, src: str) -> str:
        src = src.replace("{lang}", self.lang)
        for folder in ("captures", "stills"):  # captures/x.mp4 -> captures/<lang>/x.mp4, shared from zh if absent
            if src.startswith(folder + "/"):
                name = src[len(folder) + 1:]
                own = f"{folder}/{self.lang}/{name}"
                src = own if (self.pub / own).exists() else f"{folder}/zh/{name}"
        assert (self.pub / src).exists(), f"missing {src}"
        return src

    def info(self, src: str) -> dict:
        if src not in self.cache:
            meta = self.pub / src.replace(".mp4", ".json")
            if src.startswith("captures/") and meta.exists():
                self.cache[src] = json.loads(meta.read_text())
            else:
                self.cache[src] = {"duration": duration(self.pub / src), "marks": {}}
        return self.cache[src]

    def time(self, src: str, value) -> float:
        """Seconds in a recording: a number, a mark, [mark, offset], or "end"."""
        value = pick(value, self.lang)
        if isinstance(value, (int, float)):
            return float(value)
        name, offset = (value, 0.0) if isinstance(value, str) else value
        info = self.info(src)
        at = info["duration"] - 0.05 if name == "end" else info["marks"][name]
        return round(at + offset, 3)


def main(ep: str, lang: str) -> None:
    pub = ROOT / "public/weekly" / ep
    src = Sources(pub, lang)
    cues = parse_script(ep)
    blocks = load_shots(ep).BLOCKS
    used = [c for b in blocks for c in b.get("cues", [])]
    assert sorted(used) == sorted(cues) and len(set(used)) == len(used), \
        f"shots.py must use every line once: missing {set(cues) - set(used)}, unknown {set(used) - set(cues)}"
    draft = False
    for cue in cues.values():
        take = pub / "narration" / lang / f"{cue['id']}.wav"
        if take.exists():
            cue["dur"], cue["audio"] = round(duration(take), 3), f"weekly/{ep}/narration/{lang}/{cue['id']}.wav"
        else:
            cue["dur"], draft = round(estimate(lang, cue[lang]), 3), True

    t, shots, timed, chapters = 0.0, [], [], []
    for block in blocks:
        start = t
        anchors = {}
        if block.get("cues"):
            t += block.get("lead", LEAD)
            for i, cid in enumerate(block["cues"]):
                cue = cues[cid]
                anchors[cid] = t
                timed.append({**cue, "start": round(t, 3), "end": round(t + cue["dur"], 3)})
                t += cue["dur"] + (GAP if i < len(block["cues"]) - 1 else 0) + pick(block.get("hold", {}).get(cid, 0), lang)
            t += pick(block.get("pad", PAD), lang)
            t = max(t, start + pick(block.get("min", 0), lang))  # footage that needs more time than its lines plays on under music
        else:
            t += pick(block["dur"], lang)
        end = t
        # Shots: an "at" shot starts with its line; shots between two fixed points share that time evenly.
        items = block["shots"]
        fixed = [start] + [None] * (len(items) - 1) + [end]
        for i, s in enumerate(items):
            if "at" in s:  # a line id, or [line id, seconds after its start]
                cid, after = (s["at"], 0.0) if isinstance(s["at"], str) else s["at"]
                fixed[i] = anchors[cid] + after - (0.25 if i and not after else 0)
        i = 0
        while i < len(items):
            j = i + 1
            while fixed[j] is None:
                j += 1
            for k in range(i, j):
                fixed[k] = fixed[i] + (fixed[j] - fixed[i]) * (k - i) / (j - i)
            i = j
        for k, s in enumerate(items):
            a, b = fixed[k], fixed[k + 1]
            shot = {key: v for key, v in s.items() if key not in ("at", "from", "to", "keys")}
            shot.update(start=round(a, 3), end=round(b, 3))
            if "src" in s:
                shot["src"] = src.path(s["src"])
            if s["kind"] in ("clip", "film"):
                # Source time along the shot: straight from "from" to "to", or through "keys" ([line id, source time]:
                # that moment of the recording arrives as the line starts) on one smooth monotone curve.
                path = shot["src"]
                points = ([(0.0, src.time(path, s["from"]))]
                          + [(anchors[cid] - a, src.time(path, v)) for cid, v in s.get("keys", [])]
                          + [(b - a, src.time(path, s["to"]))])
                shot["keys"] = [[round(x, 3), round(y, 3)] for x, y in points]
                for (x0, y0), (x1, y1) in zip(points, points[1:]):
                    speed = (y1 - y0) / (x1 - x0)
                    if not 0.6 <= speed <= 3.2:
                        print(f"  ! {path} {y0}–{y1} plays at {speed:.2f}× in {x1 - x0:.1f} s")
            if b - a < 1.5 and s["kind"] not in ("title", "end"):
                print(f"  ! a {b - a:.2f} s {s['kind']} shot ({s.get('src', s.get('zh', ''))}) at {a:.1f} s")
            for key in ("label", "tag", "film"):  # a (zh, en) pair: the film shows its own
                if key in shot:
                    shot[key] = shot[key][0 if lang == "zh" else 1]
            shots.append(shot)
            if s["kind"] == "chapter":
                chapters.append({"t": round(a, 3), "n": s["n"], "zh": s["zh"], "en": s["en"]})

    tl = {"episode": ep, "lang": lang, "fps": FPS, "durationSeconds": round(t, 3), "draft": draft,
          "series": {"zh": "好奇新世界", "en": "Curious Worlds"},
          "shots": shots, "cues": timed, "chapters": chapters}
    (pub / f"timeline.{lang}.json").write_text(json.dumps(tl, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    m, s = divmod(t, 60)
    print(f"{ep} {lang}: {len(timed)} lines, {len(shots)} shots, {int(m)}:{s:04.1f}{' (DRAFT: estimated lengths)' if draft else ''}")
    for c in [{"t": 0, "zh": "开场", "en": "Opening"}] + chapters:
        mm, ss = divmod(int(c["t"]), 60)
        print(f"  {mm}:{ss:02d} {c[lang]}")


if __name__ == "__main__":
    for language in sys.argv[2:] or ["zh", "en"]:
        main(sys.argv[1], language)
