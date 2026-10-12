"""Move every cut to a different recording of the same piece (e.g. a piano Jesu, Joy).

  retime.py NEW_MUSIC            rewrite edit.json: music, shot times, verse times
  retime.py NEW_MUSIC --dry      only print old -> new times

The cuts were placed on this film's current recording (edit.json "music"): phrase
starts and bar downbeats. A different performance has its own tempo and rubato, so
the same musical moment falls at a different second. This aligns the two recordings
by their harmony (chroma, dynamic time warping), maps each cut to the same musical
moment in the new one, and snaps it to the nearest beat there. Then run render.py.

It assumes the same music in the same order (repeats included). For a different
arrangement — a shortened version, an added intro — check the printed mapping; a cut
whose new spacing differs wildly from the old one points at where the versions part.
Undo with `git checkout scripts/jesu/edit.json`.
"""
import argparse
import json
import pathlib
import sys

import librosa
import numpy as np

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
import beats as B  # noqa: E402

SR, HOP = 22050, 2048          # ~93 ms frames: fine enough for cuts, small enough for DTW
LEAD = 0.25                    # a dissolve is centred this long before its beat (as in the cut)


def chroma(path):
    y, _ = librosa.load(str(path), sr=SR, mono=True)
    c = librosa.feature.chroma_cqt(y=y, sr=SR, hop_length=HOP)
    return c, len(y) / SR


def warp(old_path, new_path):
    """-> f(t_old) = t_new, monotonic, from a DTW path over chroma."""
    a, _ = chroma(old_path)
    b, _ = chroma(new_path)
    _, wp = librosa.sequence.dtw(X=a, Y=b, metric="cosine")
    wp = wp[::-1]
    ta = librosa.frames_to_time(wp[:, 0], sr=SR, hop_length=HOP)
    tb = librosa.frames_to_time(wp[:, 1], sr=SR, hop_length=HOP)
    # collapse repeated x so np.interp sees a strictly increasing x
    xs, ys = [], []
    for x, y in zip(ta, tb):
        if xs and x <= xs[-1]:
            ys[-1] = max(ys[-1], y)
        else:
            xs.append(x)
            ys.append(y)
    return lambda t: float(np.interp(t, xs, ys))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("music", help="the new recording (any format ffmpeg/librosa reads)")
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()
    edit_path = HERE / "edit.json"
    edit = json.loads(edit_path.read_text())
    data = pathlib.Path(edit["data"])
    old = data / edit["music"]
    new = pathlib.Path(a.music).resolve()
    f = warp(old, new)
    grid = B.analyze(new)
    print(f"new recording: {grid['tempo']:.1f} bpm, {grid['duration']:.1f} s (was {B.analyze(old)['duration']:.1f} s)")
    prev_old = prev_new = None
    warnings = []
    for s in edit["shots"]:
        if "beat" not in s:                      # the opening shot starts at 0
            continue
        nb = B.snap(f(s["beat"]), grid["beats"])
        gap = flag = ""
        if prev_old is not None:
            was, now = s["beat"] - prev_old, nb - prev_new
            gap = f"   spacing {was:5.1f} -> {now:5.1f} s"
            if not 0.6 <= now / was <= 1.6:
                flag = "   <- check: the recordings differ here"
                warnings.append(s["id"])
        print(f"{s['id']:16s} {s['beat']:7.2f} -> {nb:7.2f}{gap}{flag}")
        prev_old, prev_new = s["beat"], nb
        s["beat"], s["at"] = round(nb, 2), round(nb - LEAD, 2)
    for v in edit.get("verses") or []:
        v["start"], v["end"] = round(f(v["start"]), 2), round(f(v["end"]), 2)
    if warnings:
        print(f"{len(warnings)} cut(s) moved oddly: {', '.join(warnings)} — "
              "set their 'beat'/'at' by hand in edit.json after retiming")
    if a.dry:
        return
    try:
        edit["music"] = str(new.relative_to(data))
    except ValueError:
        edit["music"] = str(new)
    edit_path.write_text(json.dumps(edit, ensure_ascii=False, indent=1))
    print(f"edit.json now uses {edit['music']}; run render.py")


if __name__ == "__main__":
    main()
