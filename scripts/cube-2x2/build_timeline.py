"""Timelines for 「二阶魔方怎么还原？」 / "How Do You Solve a 2×2 Cube?" (CUBE-2X2.md §4).

Episode 1 of Fun Informatics does the voice work (scripts/fun-informatics-01/build_timeline.py): it trims and
levels each Louise take and writes the narration track and the SRT captions; Fun Informatics 3's builder adds
the caption splitting this film reuses. On top of that this film needs:

  - SHOTS: which stretch of which footage take plays under which lines. The takes are recorded by capture.mjs
    from the cube page, one continuous solve plus three short takes, and each one's .json says where every
    move, step and stage starts. A shot's source window is named by those events, so a re-recorded take
    moves the shots with it.
  - holds that keep every shot under its speed limit: a line that is shorter than its footage would need
    gets the difference as extra time after its speech, instead of the footage racing (README "Continuous
    footage and speed curves": slow at the moments the narration names, never jumpy).
  - the music: Mozart's Twinkle Variations, K. 265 (Simone Renzi, CC BY 3.0), the recording Fun Informatics 3
    uses, one variation per section, ending on the theme's own final cadence.

Writes, for each language:
  public/cube-2x2/timeline.LANG.json   cues, shots and the takes' events, which Remotion loads before rendering
  public/cube-2x2/audio/LANG.wav       narration
  public/cube-2x2/audio/LANG.mix.wav   narration over the music, ducked (scripts/music_ducking.py)
  out/cube-2x2/delivery/cube-2x2.LANG.{zh-Hans,en}.srt

  python3 scripts/cube-2x2/build_timeline.py [zh|en] [--captions-only]
"""
import array
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


shared = load("fi01_timeline", "scripts/fun-informatics-01/build_timeline.py")
fi03 = load("fi03_timeline", "scripts/fun-informatics-03/build_timeline.py")
wp = shared.wp
PUB = shared.PUB = ROOT / "public/cube-2x2"
FILM_NAME = "cube-2x2"
DELIVERY = ROOT / "out/cube-2x2/delivery"
VOICES = {lang: shared.MEDIA / f"outputs/louise/{lang}/cube-2x2-v1" for lang in ("zh", "en")}
TITLE = {"zh": "二阶魔方怎么还原？", "en": "How Do You Solve a 2×2 Cube?"}
FPS, RATE = shared.FPS, wp.RATE
LEAD_IN, ONSET, GAP, SECTION_GAP, END_CARD = 1.2, 0.15, 0.4, 0.9, 8.0
TRANSLATIONS = json.loads((ROOT / "docs/cube-2x2/translations.json").read_text())

# Extra seconds after a line, for a card to read or a result to look at (shots may add more: see SHOTS).
HOLD = {
    "cb00-02": 0.6, "cb00-03": 3.0,
    "cb01-02": 1.2, "cb01-05": 0.6,
    "cb02-03": 1.0, "cb02-06": 1.0, "cb02-08": 1.2, "cb02-09": 1.5,
    "cb03-02": 1.5, "cb03-04": 1.0, "cb03-06": 1.5,
    "cb04-02": 1.0, "cb04-03": 0.5, "cb04-05": 2.0,
    "cb05-02": 1.5,
    "cb06-01": 2.5,
}

# Shots: (first cue, last cue, take, source from, source to, fastest playback). Source points are events of the
# take's .json: ("start",), ("end",), ("mark", name), ("stage", i), ("step", stage, step), and ("move", stage,
# step, index, "start" | "end"); a number adds seconds. A shot spans its cues' whole time; the composition runs
# the footage over it on an eased curve, so the picture settles between shots instead of jumping.
SHOTS = [
    ("cb00-01", "cb00-02", "hero", ("start",), ("end",), 1.5),
    ("cb00-03", "cb00-03", "hero", ("end", -0.1), ("end",), 1.0),
    ("cb01-01", "cb01-02", "meet", ("start",), ("end",), 1.5),
    ("cb01-03", "cb01-03", "notation", ("start",), ("mark", "R'"), 1.2),
    ("cb01-04", "cb01-04", "notation", ("mark", "R'"), ("mark", "R2"), 1.2),
    ("cb01-05", "cb01-05", "notation", ("mark", "R2"), ("end",), 1.4),
    # The solve, one take. The first layer is filmed from below.
    ("cb02-01", "cb02-01", "solve", ("start",), ("step", 0, 0), 1.5),
    ("cb02-02", "cb02-02", "solve", ("step", 0, 0), ("step", 0, 1), 1.0),
    ("cb02-03", "cb02-03", "solve", ("step", 0, 1), ("step", 0, 1, 0.01), 1.0),
    ("cb02-04", "cb02-04", "solve", ("step", 0, 1), ("move", 0, 1, 0, "end"), 1.0),
    ("cb02-05", "cb02-05", "solve", ("move", 0, 1, 0, "end"), ("move", 0, 1, 8, "end"), 1.6),
    ("cb02-06", "cb02-06", "solve", ("move", 0, 1, 8, "end"), ("step", 0, 2), 1.2),
    ("cb02-07", "cb02-07", "solve", ("step", 0, 2), ("step", 0, 3), 2.2),
    # The finished white layer stays in view (from below) through "the first layer is done" and the tip...
    ("cb02-08", "cb02-08", "solve", ("step", 0, 3), ("move", 0, 3, 4, "end", 0.5), 1.5),
    ("cb02-09", "cb02-09", "solve", ("move", 0, 3, 4, "end", 0.5), ("move", 0, 3, 4, "end", 0.51), 1.0),
    # ...and the camera rises to the yellow top on "white is on the bottom, so yellow is on top".
    ("cb03-01", "cb03-01", "solve", ("move", 0, 3, 4, "end", 0.51), ("step", 1, 0), 1.0),
    ("cb03-02", "cb03-04", "solve", ("step", 1, 0), ("step", 1, 0, 0.01), 1.0),
    ("cb03-05", "cb03-05", "solve", ("step", 1, 0), ("step", 1, 1), 1.5),
    ("cb03-06", "cb03-06", "solve", ("step", 1, 1), ("stage", 2), 1.5),
    ("cb04-01", "cb04-02", "solve", ("stage", 2), ("step", 2, 0), 1.0),
    ("cb04-03", "cb04-03", "solve", ("step", 2, 0), ("step", 2, 1), 1.6),
    ("cb04-04", "cb04-04", "solve", ("step", 2, 1), ("step", 2, 1, 0.01), 1.0),
    ("cb04-05", "cb04-05", "solve", ("step", 2, 1), ("end",), 2.5),
    # Once more, the whole solve, quickly.
    ("cb05-01", "cb05-02", "solve", ("step", 0, 0), ("mark", "solved", 0.7), 7.0),
    ("cb06-01", "cb06-01", "meet", ("start",), ("end",), 1.2),
]

# Music: K. 265 in Simone Renzi's recording (public/cube-2x2/music/SOURCES.txt), the variations as cut for
# Fun Informatics 3. Each section starts its own; the ending is the last stretch of the theme, so the film
# finishes on the tune's final cadence.
MUSIC_SOURCE = PUB / "music/mozart-k265-renzi.mp3"
wp.MUSIC = PUB / "music/none"  # set to the bed per language in build(), once the music is in
K265 = fi03.K265
MUSIC_PLAN = {
    "cb00": ["theme"],          # the tune everyone knows, under the opening question
    "cb01": ["v1"],             # light, for meeting the cube
    "cb02": ["v2", "v5"],       # the first layer, the longest stretch
    "cb03": ["v4"],
    "cb04": ["v3"],
    "cb05": ["v12"],            # quick, for the fast replay
    "cb06": [],                 # the theme's last bars: see music_bed
}
SECTION_XF = 2.0
wp.PEAK_DB = -2.0
sys.path.insert(0, str(ROOT / "scripts"))
import music_ducking  # noqa: E402  (README "Music under narration")

assert music_ducking.LINE_LUFS == wp.LINE_LUFS
wp.music_envelope = lambda cues, total, bed_lufs, path: music_ducking.envelope(cues, total, bed_lufs, path)


def take(name):
    return json.loads((PUB / f"footage/{name}.json").read_text())


def point(record, spec):
    """A source time in seconds for an event spec (see SHOTS)."""
    kind, rest = spec[0], list(spec[1:])
    extra = rest.pop() if rest and isinstance(rest[-1], float) else 0.0
    fps = record["fps"]
    if kind == "start":
        frame = 0
    elif kind == "end":
        frame = record["frames"] - 1
    elif kind == "mark":
        frame = next(m["frame"] for m in record["marks"] if m["name"] == rest[0])
    elif kind == "stage":
        frame = next(s["frame"] for s in record["stages"] if s["stage"] == rest[0])
    elif kind == "step":
        frame = next(s["frame"] for s in record["steps"] if s["stage"] == rest[0] and s["step"] == rest[1])
    elif kind == "move":
        stage, step, index, edge = rest
        frame = next(m[edge] for m in record["moves"] if m["stage"] == stage and m["step"] == step and m["index"] == index)
    else:
        raise ValueError(spec)
    return round(frame / fps + extra, 3)


def music_bed(lang, cues, total) -> Path:
    """Each section's variations, cut to the section and crossfaded into the next; the last section gets the
    theme's closing bars, timed to end with the film."""
    prefixes = list(MUSIC_PLAN)
    starts = [0.0 if p == "cb00" else next(c["start"] for c in cues if c["id"].startswith(p)) for p in prefixes]
    graph, k, sections = [], 0, []
    names = [n for plan in MUSIC_PLAN.values() for n in plan] + ["theme"]
    graph.append(f"[0:a]aresample=48000,aformat=sample_fmts=flt:channel_layouts=stereo,asplit={len(names)}"
                 + "".join(f"[in{i}]" for i in range(len(names))))

    def seg(a, b):
        nonlocal k
        graph.append(f"[in{k}]atrim={a}:{b},asetpts=PTS-STARTPTS[g{k}]")
        k += 1
        return f"[g{k - 1}]"

    for i, prefix in enumerate(prefixes):
        last = i == len(prefixes) - 1
        length = (total - starts[i]) if last else starts[i + 1] - starts[i] + SECTION_XF
        if last:
            a, b = K265["theme"]
            parts = seg(max(a, b - length), b)
            graph.append(f"{parts}apad=whole_dur={length:.3f},atrim=0:{length:.3f},asetpts=PTS-STARTPTS[sec{i}]")
        else:
            parts = "".join(seg(*K265[n]) for n in MUSIC_PLAN[prefix])
            count = len(MUSIC_PLAN[prefix])
            graph.append(f"{parts}concat=n={count}:v=0:a=1,apad=whole_dur={length:.3f},atrim=0:{length:.3f},"
                         f"afade=t=out:st={max(0, length - SECTION_XF - 1.0):.3f}:d={SECTION_XF + 1.0:.3f},asetpts=PTS-STARTPTS[sec{i}]")
        sections.append(f"[sec{i}]")
    chain = sections[0]
    for i, nxt in enumerate(sections[1:], 1):
        graph.append(f"{chain}{nxt}acrossfade=d={SECTION_XF}:c1=tri:c2=tri[x{i}]")
        chain = f"[x{i}]"
    graph.append(f"{chain}apad=whole_dur={total:.3f},atrim=0:{total:.3f}[bed]")
    # Unused splits must still be consumed.
    used = k
    for extra in range(used, len(names)):
        graph.append(f"[in{extra}]anullsink")
    out = PUB / f"audio/music-bed.{lang}.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(MUSIC_SOURCE), "-filter_complex", ";".join(graph),
                    "-map", "[bed]", "-c:a", "pcm_f32le", str(out)], check=True)
    got = shared.seconds(out)
    assert abs(got - total) < 0.05, f"{lang}: music bed is {got:.2f}s, film {total:.2f}s"
    return out


def build(langs):
    cue_text = json.loads((PUB / "narration/cues.json").read_text())
    ids = [c["id"] for c in cue_text]
    takes = {name: take(name) for name in ("hero", "meet", "notation", "solve")}
    footage = shared.listing("footage", (".mp4",))
    # Each shot's source window, and what it asks of its cues' time.
    windows = []
    for first, last, name, a, b, fastest in SHOTS:
        s0, s1 = point(takes[name], a), point(takes[name], b)
        assert s1 >= s0, (first, s0, s1)
        windows.append({"first": first, "last": last, "take": name, "from": s0, "to": s1, "fastest": fastest})
    covered = {cid for w in windows for cid in ids[ids.index(w["first"]):ids.index(w["last"]) + 1]}
    assert covered == set(ids), f"cues without a shot: {sorted(set(ids) - covered)}"

    for lang in langs:
        missing, clips = [], {}
        for c in cue_text:
            path = VOICES[lang] / f"{c['id']}.wav"
            if path.is_file():
                clips[c["id"]] = wp.level(wp.trim(wp.read_wav(path)))
            else:
                missing.append(c["id"])
                clips[c["id"]] = wp.estimate(lang, c[lang])
        # A shot's cues need at least (source length / fastest) seconds; the shortfall goes on its last cue.
        slot = {}
        for n, c in enumerate(cue_text):
            last_in_section = n + 1 == len(ids) or ids[n + 1][:4] != c["id"][:4]
            speech = len(clips[c["id"]]) / RATE
            slot[c["id"]] = ONSET + speech + GAP + HOLD.get(c["id"], 0) + (SECTION_GAP if last_in_section else 0)
        extra = {}
        for w in windows:
            span = ids[ids.index(w["first"]):ids.index(w["last"]) + 1]
            need = (w["to"] - w["from"]) / w["fastest"]
            have = sum(slot[cid] for cid in span)
            if need > have:
                extra[w["last"]] = round(need - have + 0.2, 3)
        t, cues, sounds = LEAD_IN, [], []
        for c in cue_text:
            speech = len(clips[c["id"]]) / RATE
            end = t + slot[c["id"]] + extra.get(c["id"], 0)
            cues.append({"id": c["id"], "section": c["section"], "zh": c["zh"], "en": c["en"],
                         "start": round(t, 3), "end": round(end, 3),
                         "speech": {"start": round(t + ONSET, 3), "end": round(t + ONSET + speech, 3)}})
            sounds.append((t + ONSET, clips[c["id"]]))
            t = end
        total = t + END_CARD
        by_id = {c["id"]: c for c in cues}
        shots = [{"take": w["take"], "cues": [w["first"], w["last"]], "start": by_id[w["first"]]["start"],
                  "end": by_id[w["last"]]["end"], "from": w["from"], "to": w["to"]} for w in windows]
        audio = PUB / "audio"
        audio.mkdir(parents=True, exist_ok=True)
        track = array.array("h", bytes(2 * round(total * RATE)))
        for start, clip in sounds:
            k = round(start * RATE)
            track[k:k + len(clip)] = clip
        wp.write_wav(audio / f"{lang}.wav", track, RATE)
        if MUSIC_SOURCE.is_file():
            wp.MUSIC = music_bed(lang, cues, total)
        wp.mix_with_music(audio / f"{lang}.wav", audio / f"{lang}.mix.wav", cues, total)
        finish(audio / f"{lang}.mix.wav")
        write_captions(lang, cues)
        data = {"fps": FPS, "leadIn": LEAD_IN, "title": TITLE, "footage": footage,
                "footageSeconds": {name: shared.seconds(PUB / "footage" / name) for name in footage},
                "lang": lang, "durationSeconds": round(total, 3), "endCardStart": round(t, 3),
                "cues": cues, "shots": shots,
                "takes": {name: {k: v for k, v in record.items() if k != "plan"} for name, record in takes.items()},
                "plan": takes["solve"].get("plan"),
                "draft": bool(missing)}
        (PUB / f"timeline.{lang}.json").write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n")
        added = ", ".join(f"{cid} +{s:.1f}s" for cid, s in extra.items())
        print(f"{lang}: {len(cues)} cues, {len(shots)} shots, {total:.1f}s ({total / 60:.1f} min)"
              + (f"; held for footage: {added}" if added else ""))
        if missing:
            print(f"  ESTIMATED (no take yet): {', '.join(missing)}")


def finish(mix: Path) -> None:
    """Without a music bed wp.mix_with_music only resamples: give the film the same -16 LUFS and ceiling anyway
    (Fun Informatics 3's finish, on this film's own mixer)."""
    if wp.MUSIC.is_file():
        return
    raw = mix.with_suffix(".raw.wav")
    mix.rename(raw)
    gain = wp.FILM_LUFS - wp.loudness("-i", str(raw))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(raw), "-af",
                    f"volume={gain:.2f}dB,alimiter=limit={10 ** (wp.PEAK_DB / 20):.4f}:attack=5:release=50:level=false:latency=true",
                    "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le", str(mix)], check=True)
    raw.unlink()


def write_captions(lang, cues):
    fi03.DELIVERY, fi03.FILM_NAME, fi03.TRANSLATIONS = DELIVERY, FILM_NAME, TRANSLATIONS
    fi03.write_captions(lang, cues)


if __name__ == "__main__":
    langs = [a for a in sys.argv[1:] if a in ("zh", "en")] or ["zh", "en"]
    if "--captions-only" in sys.argv:
        for lang in langs:
            write_captions(lang, json.loads((PUB / f"timeline.{lang}.json").read_text())["cues"])
    else:
        build(langs)
