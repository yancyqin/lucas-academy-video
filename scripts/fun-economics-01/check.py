"""Check every voice take with Whisper and find the word times the arithmetic page is cut to.

Run with lucas-academy-media's Python (it has Whisper). For each cue: transcribe the take (small model, word
timestamps), compare it with what the voice was given to read, flag it below SIMILAR, and keep its words with
times. Then place the page's step anchors (ANCHORS) on the film's clock and write, for <lang> zh or en,
  out/fun-economics-01/narration-check.<lang>.json   per-cue transcript, similarity, words, sha256
  public/fun-economics-01/markers.<lang>.json        "s3.2": seconds, read by build_timeline.py and record-roads.cjs

  ../lucas-academy-media/.conda/bin/python scripts/fun-economics-01/check.py [--lang en]
  python3 scripts/fun-economics-01/build_timeline.py [--lang en]    # picks the markers up
"""
import difflib
import hashlib
import json
import re
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[2]
PUB = ROOT / "public/fun-economics-01"
LANG = sys.argv[sys.argv.index("--lang") + 1] if "--lang" in sys.argv else "zh"
OUT = ROOT / f"out/fun-economics-01/narration-check.{LANG}.json"
sys.path.insert(0, str(ROOT / "scripts/fun-economics-01"))
from build_timeline import VOICES  # noqa: E402
from narration import cn_number, en_number  # noqa: E402

SIMILAR = 0.85
# Page steps: scene.step -> (cue, phrase in what is spoken, or None for the start of the cue).
ANCHORS_ZH = {
    "s0.0": ("oc04-05", None), "s0.1": ("oc04-05", "同一张点子图"),
    "s1.0": ("oc04-06", None), "s1.1": ("oc04-06", "加起来"), "s1.2": ("oc04-06", "它练的是"),
    "s2.0": ("oc04-07", None), "s2.1": ("oc04-07", "竖着切一刀"), "s2.2": ("oc04-07", "合起来"), "s2.3": ("oc04-07", "它练的是"),
    "s4.0": ("oc04-16", None), "s4.1": ("oc04-16", "去掉余数"), "s4.2": ("oc04-16", "左边是单数"), "s4.3": ("oc04-17", None),
    "s4.4": ("oc04-18", None), "s4.5": ("oc04-18", "剩下"), "s4.6": ("oc04-19", None), "s4.7": ("oc04-19", "剩下"),
    "s4.8": ("oc04-20", None), "s4.9": ("oc04-21", None),
    "s5.0": ("oc04-22", None), "s5.1": ("oc04-23", "背下了"), "s5.2": ("oc04-24", None), "s5.3": ("oc05-02", "走一走"),
}
ANCHORS_EN = {
    "s0.0": ("oc04-05", None), "s0.1": ("oc04-05", "same dot picture"),
    "s1.0": ("oc04-06", None), "s1.1": ("oc04-06", "row by row"), "s1.2": ("oc04-06", "what it trains"),
    "s2.0": ("oc04-07", None), "s2.1": ("oc04-07", "cut it"), "s2.2": ("oc04-07", "together"), "s2.3": ("oc04-07", "what it trains"),
    "s4.0": ("oc04-16", None), "s4.1": ("oc04-16", "dropping"), "s4.2": ("oc04-16", "wherever"), "s4.3": ("oc04-17", None),
    "s4.4": ("oc04-18", None), "s4.5": ("oc04-18", "rows left"), "s4.6": ("oc04-19", None), "s4.7": ("oc04-19", "groups left"),
    "s4.8": ("oc04-20", None), "s4.9": ("oc04-21", None),
    "s5.0": ("oc04-22", None), "s5.1": ("oc04-23", "memorized"), "s5.2": ("oc04-24", None), "s5.3": ("oc05-02", "walk these"),
}
# The finger scene (s3) is not in this film since v0.8: its path is one line over the hand footage.
ANCHORS = ANCHORS_ZH if LANG == "zh" else ANCHORS_EN
assert list(ANCHORS_ZH) == list(ANCHORS_EN)


def norm(text: str) -> str:
    """Compare what was read with what was heard: no punctuation or spaces, numbers in words; in Chinese, 航 (the row
    respelling) as 行."""
    if LANG == "en":
        text = re.sub(r"\$(\d+)", lambda m: m[1] + (" dollar" if m[1] == "1" else " dollars"), text)
        text = re.sub(r"\d+", lambda m: en_number(int(m[0])) if int(m[0]) <= 100 else m[0], text)
        return re.sub(r"[^a-z]", "", text.lower())
    text = re.sub(r"\d+", lambda m: cn_number(int(m[0])) if int(m[0]) <= 100 else m[0], text)
    text = text.replace("航", "行").replace("两", "二")
    return re.sub(r"[^\w]|_", "", text).lower()


def main() -> None:
    import whisper  # lucas-academy-media's environment
    model = whisper.load_model("small")
    cues = json.loads((PUB / f"narration/cues.{LANG}.json").read_text())
    old = json.loads(OUT.read_text())["cues"] if OUT.exists() else {}
    report = {}
    for c in cues:
        wav = VOICES[LANG][c["speaker"]] / f"{c['id']}.wav"
        if not wav.is_file():
            continue
        digest = hashlib.sha256(wav.read_bytes()).hexdigest()
        if old.get(c["id"], {}).get("sha256") == digest and old[c["id"]].get("spoken") == c["spoken"]:
            report[c["id"]] = old[c["id"]]
            continue
        result = model.transcribe(str(wav), language=LANG, initial_prompt="以下是普通话的句子。" if LANG == "zh" else None,
                                  word_timestamps=True, condition_on_previous_text=False)
        heard = "".join(seg["text"] for seg in result["segments"]).strip()
        words = [{"w": w["word"].strip(), "start": round(w["start"], 2), "end": round(w["end"], 2)}
                 for seg in result["segments"] for w in seg.get("words", [])]
        ratio = difflib.SequenceMatcher(None, norm(c["spoken"]), norm(heard)).ratio()
        report[c["id"]] = {"sha256": digest, "spoken": c["spoken"], "heard": heard, "ratio": round(ratio, 3),
                           "flagged": ratio < SIMILAR, "words": words}
        print(f"{c['id']} {ratio:.2f} {'FLAG ' if ratio < SIMILAR else ''}{heard}", flush=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    flagged = [cid for cid, r in report.items() if r["flagged"]]
    OUT.write_text(json.dumps({"expected": len(cues), "checked": len(report), "flagged": flagged, "cues": report},
                              ensure_ascii=False, indent=1) + "\n")
    print(f"checked {len(report)}/{len(cues)}, flagged {len(flagged)}: {', '.join(flagged)}")
    write_markers(report)


def write_markers(report: dict) -> None:
    tl_path = PUB / f"timeline.{LANG}.json"
    if not tl_path.exists():
        return
    cues = {c["id"]: c for c in json.loads(tl_path.read_text())["cues"]}
    marks, missing = {}, []
    for label, (cid, phrase) in ANCHORS.items():
        cue = cues[cid]
        if phrase is None:
            # A scene's first step goes up before the page fades in over the picture before it (0.3 s ahead of the
            # cue), so the old scene never flashes; a later step that opens a cue waits for its first word.
            marks[label] = round(cue["start"] - 0.5 if label.endswith(".0") else cue["speech"]["start"], 3)
            continue
        words = report.get(cid, {}).get("words", [])
        chars, owner = "", []
        for i, w in enumerate(words):
            piece = norm(w["w"])
            chars += piece
            owner += [i] * len(piece)
        at = chars.find(norm(phrase))
        if at < 0:
            missing.append(f"{label} ({cid} 「{phrase}」)")
            continue
        word = words[owner[at]]
        marks[label] = round(cue["speech"]["start"] + word["start"] - cue.get("trim", 0.0), 3)
    (PUB / f"markers.{LANG}.json").write_text(json.dumps(marks, indent=1) + "\n")
    print(f"markers: {len(marks)}/{len(ANCHORS)}" + (f"; not found: {', '.join(missing)}" if missing else ""))


if __name__ == "__main__":
    main()
