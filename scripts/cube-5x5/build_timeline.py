"""The timeline for "How Do You Solve a 5×5 Cube?" / 「五阶魔方怎么还原？」 (CUBE-5X5.md §4).

The 2×2 film's builder (scripts/cube-2x2/build_timeline.py) does the work, one picture and two soundtracks: every
line gets the longer of its two takes, each track its own mix and captions, the shots named by the takes' events
and held to their speed limits, one music bed under both. This gives it the 5×5 film's own folder, takes, shots,
holds, letter timings and music, then runs it.

Writes public/cube-5x5/timeline.json, public/cube-5x5/audio/{en,zh}{,.mix}.wav and
out/cube-5x5/delivery/cube-5x5.{en,zh-Hans}.srt.

  python3 scripts/cube-5x5/build_timeline.py [--captions-only]
"""
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("cube2x2_timeline", ROOT / "scripts/cube-2x2/build_timeline.py")
c2 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c2)

c2.PUB = c2.shared.PUB = ROOT / "public/cube-5x5"
c2.FILM_NAME = "cube-5x5"
c2.DELIVERY = ROOT / "out/cube-5x5/delivery"
c2.VOICES = {lang: c2.shared.MEDIA / f"outputs/louise/{lang}/cube-5x5-v1" for lang in ("zh", "en")}
c2.TITLE = {"zh": "五阶魔方怎么还原？", "en": "How Do You Solve a 5×5 Cube?"}
c2.TAKES = ("hero", "meet", "anatomy", "letters", "page", "solve")
c2.MUSIC_SOURCE = c2.PUB / "music/mozart-k265-renzi.mp3"
c2.wp.MUSIC = c2.PUB / "music/none"

# Extra seconds after a line, for a card to read or a result to look at (shots may add more).
c2.HOLD = {
    "cf00-01": 0.2, "cf00-02": 0.6, "cf00-03": 0.6, "cf00-04": 1.2,
    "cf01-04": 0.8, "cf02-02": 0.6,
    "cf03-04": 1.0, "cf04-03": 0.8, "cf05-03": 1.0, "cf06-02": 1.0, "cf07-03": 1.2, "cf08-03": 1.0, "cf09-02": 1.5,
    "cf10-02": 1.5, "cf10-05": 1.5, "cf10-06": 1.0,
    "cf11-02": 1.0, "cf11-04": 2.0,
    "cf12-02": 1.0, "cf12-03": 2.5,
}

# Shots: (first cue, last cue, take, source from, source to, fastest playback), as the 2×2 film's SHOTS. The solve
# take's stages: 0 cross, 1 corners, 2 middle, 3 yellow cross, 4 yellow face, 5 yellow corners, 6 yellow edges,
# 7 parity, 8 edges, 9–13 the centres (yellow on top, white below, red in front, green on the right, orange at
# the back). The take lights a stage's pieces as the stage begins, before its camera move: a shot that shows a
# change of light ends 1.4 s before the stage's event (the camera move takes 1.33 s). A shot that ends on a stage
# rests 0.1 s before its event, so the stage tag and step strip stay with the stage just finished.
c2.SHOTS = [
    # The payoff first (the whole solve, fast), the real page and its guide, the title and the skip hint.
    ("cf00-01", "cf00-01", "solve", ("start",), ("mark", "solved", 0.5), 40.0),
    ("cf00-02", "cf00-02", "page", ("start",), ("end",), 1.6),
    ("cf00-03", "cf00-04", "hero", ("end", -0.1), ("end",), 1.0),
    # The idea: the frame, the wings, the centres, the whole cube.
    ("cf01-01", "cf01-01", "anatomy", ("mark", "frame"), ("mark", "wings"), 1.5),
    ("cf01-02", "cf01-02", "anatomy", ("mark", "wings"), ("mark", "centres"), 1.5),
    ("cf01-03", "cf01-03", "anatomy", ("mark", "centres"), ("mark", "whole"), 1.5),
    ("cf01-04", "cf01-04", "anatomy", ("mark", "whole"), ("end",), 1.5),
    ("cf02-01", "cf02-02", "letters", ("start",), ("end",), 1.4),
    # Part 1, the frame, from below for the white cross and corners. One example at about 1×, the rest faster.
    ("cf03-01", "cf03-01", "solve", ("start",), ("stage", 0, -0.1), 1.2),
    ("cf03-02", "cf03-02", "solve", ("stage", 0), ("step", 0, 1), 1.2),
    ("cf03-03", "cf03-03", "solve", ("step", 0, 1), ("step", 0, 3), 1.5),
    ("cf03-04", "cf03-04", "solve", ("step", 0, 3), ("stage", 1, -0.1), 1.5),
    ("cf04-01", "cf04-02", "solve", ("stage", 1), ("step", 1, 1), 1.3),
    ("cf04-03", "cf04-03", "solve", ("step", 1, 1), ("stage", 2, -0.1), 5.0),
    ("cf05-01", "cf05-01", "solve", ("stage", 2), ("move", 2, 0, 1, "end"), 1.5),
    ("cf05-02", "cf05-02", "solve", ("move", 2, 0, 1, "end"), ("step", 2, 1), 1.3),
    ("cf05-03", "cf05-03", "solve", ("step", 2, 1), ("stage", 3, -0.1), 3.0),
    ("cf06-01", "cf06-01", "solve", ("stage", 3), ("step", 3, 0), 1.0),
    ("cf06-02", "cf06-02", "solve", ("step", 3, 0), ("stage", 4, -0.1), 1.6),
    ("cf07-01", "cf07-02", "solve", ("stage", 4), ("step", 4, 0), 1.0),
    ("cf07-03", "cf07-03", "solve", ("step", 4, 0), ("stage", 5, -0.1), 2.4),
    ("cf08-01", "cf08-01", "solve", ("stage", 5), ("step", 5, 0), 1.0),
    ("cf08-02", "cf08-02", "solve", ("step", 5, 0), ("step", 5, 1), 1.3),
    ("cf08-03", "cf08-03", "solve", ("step", 5, 1), ("stage", 6, -0.1), 2.0),
    ("cf09-01", "cf09-01", "solve", ("stage", 6), ("move", 6, 0, 11, "end", 0.3), 1.4),
    ("cf09-02", "cf09-02", "solve", ("move", 6, 0, 11, "end", 0.3), ("move", 6, 0, 11, "end", 0.31), 1.0),
    # Part 2, the edges: the wings come back into the light, the parity turn, one commutator slowly, the rest fast.
    # (Parity keeps the camera where it is, so its light changes on its event's own frame.)
    ("cf10-01", "cf10-01", "solve", ("move", 6, 0, 11, "end", 0.31), ("stage", 7, 0.1), 1.0),
    ("cf10-02", "cf10-02", "solve", ("stage", 7, 0.1), ("stage", 7, 0.11), 1.0),
    ("cf10-03", "cf10-03", "solve", ("stage", 7, 0.11), ("stage", 8, -0.1), 1.2),
    ("cf10-04", "cf10-04", "solve", ("stage", 8), ("move", 8, 0, 7, "end", 0.3), 1.0),
    ("cf10-05", "cf10-05", "solve", ("move", 8, 0, 7, "end", 0.3), ("move", 8, 0, 7, "end", 0.31), 1.0),
    ("cf10-06", "cf10-06", "solve", ("move", 8, 0, 7, "end", 0.31), ("stage", 9, -1.4), 12.0),
    # Part 3, the centres: the camera rises to the top, one block commutator slowly, the faces fast, solved.
    ("cf11-01", "cf11-01", "solve", ("stage", 9, -1.4), ("step", 9, 0), 1.0),
    ("cf11-02", "cf11-02", "solve", ("step", 9, 0), ("move", 9, 0, 7, "end", 0.3), 1.0),
    ("cf11-03", "cf11-03", "solve", ("move", 9, 0, 7, "end", 0.3), ("mark", "solved"), 14.0),
    ("cf11-04", "cf11-04", "solve", ("mark", "solved"), ("end",), 1.3),
    # Once more, the whole solve; the page again (from its first "Next move"); the question over a solved cube.
    ("cf12-01", "cf12-01", "solve", ("start",), ("mark", "solved", 0.7), 35.0),
    ("cf12-02", "cf12-02", "page", ("mark", "press #guide-move"), ("end",), 1.8),
    ("cf12-03", "cf12-03", "meet", ("start",), ("end",), 1.2),
]

# The letters lines: each move of the letters take turns as its word is said. Seconds into each raw English take,
# from Whisper's word times (scripts/cube-5x5/letter_words.py prints them).
c2.LETTER_WORDS = json.loads((ROOT / "scripts/cube-5x5/letter_words.json").read_text())

# Music: the theme under the opening, then the variations in this order, each section taking as many as it needs
# (a section is cut to its length and crossfaded into the next); the end is the theme's last bars. v11, the slow
# one, is left out.
VARIATIONS = ["v1", "v2", "v5", "v3", "v4", "v6", "v7", "v10", "v8", "v9", "v12"]
plain_bed = c2.music_bed


def music_bed(lang, cues, total):
    prefixes = list(dict.fromkeys(c["id"][:4] for c in cues))
    starts = [0.0] + [next(c["start"] for c in cues if c["id"].startswith(p)) for p in prefixes[1:]]
    plan, queue = {prefixes[0]: ["theme"]}, []
    for i, prefix in enumerate(prefixes[1:-1], 1):
        length, have, plan[prefix] = starts[i + 1] - starts[i] + c2.SECTION_XF, 0.0, []
        while have < length:
            queue = queue or list(VARIATIONS)
            name = queue.pop(0)
            plan[prefix].append(name)
            have += c2.K265[name][1] - c2.K265[name][0]
    plan[prefixes[-1]] = []
    c2.MUSIC_PLAN = plan
    return plain_bed(lang, cues, total)


c2.music_bed = music_bed

if __name__ == "__main__":
    if "--captions-only" in sys.argv:
        c2.write_captions(json.loads((c2.PUB / "timeline.json").read_text())["cues"])
    else:
        c2.build()
