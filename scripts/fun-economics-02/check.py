"""Check every voice take with Whisper (episode 1's check.py) and find when the picture's marked words are said.

Run with lucas-academy-media's Python (it has Whisper), once per language. Writes
  out/fun-economics-02/narration-check.<lang>.json   per-cue transcript, similarity, words, sha256
  public/fun-economics-02/word-times.json            {marker: {lang: seconds into the trimmed take}}, read by
                                                     build_timeline.py in place of its estimate

  ../lucas-academy-media/.conda/bin/python scripts/fun-economics-02/check.py [--lang en]
  python3 scripts/fun-economics-02/build_timeline.py [--lang en]
"""
import json

from common import FILM, OUT, PUB, VOICES, base

c = base("check")
c.PUB, c.OUT, c.VOICES = PUB, OUT / f"narration-check.{c.LANG}.json", VOICES
bt = base("build_timeline", "fun-economics-02")
WORD_TIMES = PUB / "word-times.json"


def write_markers(report: dict) -> None:
    """Each marked word's start, in seconds into its take after the leading silence is trimmed."""
    trims = {}
    tl_path = PUB / f"timeline.{c.LANG}.json"
    if tl_path.exists():
        trims = {cue["id"]: cue["trim"] for cue in json.loads(tl_path.read_text())["cues"]}
    times = json.loads(WORD_TIMES.read_text()) if WORD_TIMES.exists() else {}
    missing = []
    for key, (cid, zh, en) in bt.ANCHORS.items():
        words = report.get(cid, {}).get("words", [])
        chars, owner = "", []
        for i, w in enumerate(words):
            piece = c.norm(w["w"])
            chars += piece
            owner += [i] * len(piece)
        at = chars.find(c.norm(zh if c.LANG == "zh" else en))
        if at < 0 or cid not in trims:
            missing.append(f"{key} ({cid})")
            continue
        times.setdefault(key, {})[c.LANG] = round(words[owner[at]]["start"] - trims[cid], 3)
    WORD_TIMES.write_text(json.dumps(times, indent=1) + "\n")
    print(f"{FILM} word times ({c.LANG}): {len(bt.ANCHORS) - len(missing)}/{len(bt.ANCHORS)}" + (f"; not found: {', '.join(missing)}" if missing else ""))


c.write_markers = write_markers
if __name__ == "__main__":
    c.main()
