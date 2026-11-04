#!/usr/bin/env python3
"""Every Muse segment the film uses, aligned into its painting's frame with align_video.py — one command per clip set.

Owner 11-03: use each Muse clip whole; the dance-class clip in two parts with the painting faded in between
(「第一段 0 到 1 秒，第二段从 1.3 秒到结束，删除 1.0–1.3 秒」). Changes found frame by frame:
  dance-class  0–10 still (= the reconstruction) | 10→11 the front dancer changes | 22–30 a morph (music stand fades in,
               figures ghost) — the owner's 1.0–1.3 s | 31– steady to the end
  etoile       0–34 nearly still | 34→35 backdrop and dancer change, the room stays put (ECC onto frame 0 holds)
Segments after a change register onto frame 0 of the same clip (--ref 0), so the room never moves at a join.

usage: .venv-reframe/bin/python scripts/gymnopedies/align_segments.py soft|sharp [ID ...]
       soft  = footage/muse/<id>.mp4        -> footage/muse/aligned-soft/   (drafts)
       sharp = footage/muse/sharp/<id>.mp4  -> footage/muse/aligned-sharp/  (the film; upscale_clips.py first)
"""
import os, subprocess, sys

DATA = "/Users/yqin/repo/playground/lucas-academy-video-data/satie-gymnopedies"
HERE = os.path.dirname(os.path.abspath(__file__))
SEGMENTS = [   # (clip id, segment name, start, end (exclusive) or None, ref frame or None)
    ("etoile", "etoile-a", 0, 35, None),
    ("etoile", "etoile-b", 35, None, 0),
    ("dance-class", "dance-class-a", 0, 11, None),
    ("dance-class", "dance-class-b", 11, 22, 0),        # 21→22 the morph begins (the owner's 1.0–1.3 s, cut)
    ("dance-class", "dance-class-c", 31, None, 0),
    ("waiting", "waiting", 0, None, None),
    ("barre", "barre", 0, None, None),
    ("bougival", "bougival", 0, None, None),
    ("dance-city", "dance-city", 0, None, None),
    ("rehearsal-stage", "rehearsal-stage", 0, None, None),
]
REPORT_ID = {"barre": "barre-met"}

def main():
    kind, only = sys.argv[1], set(sys.argv[2:])
    src = f"{DATA}/footage/muse" + ("/sharp" if kind == "sharp" else "")
    out = f"{DATA}/footage/muse/aligned-{kind}"
    for cid, name, start, end, ref in SEGMENTS:
        if only and cid not in only: continue
        cmd = [sys.executable, f"{HERE}/align_video.py", REPORT_ID.get(cid, cid), f"{src}/{cid}.mp4", "--start", str(start), "--out", f"{out}/{name}.mp4"]
        if end is not None: cmd += ["--end", str(end)]
        if ref is not None: cmd += ["--ref", str(ref)]
        subprocess.run(cmd, check=True)

if __name__ == "__main__":
    main()
