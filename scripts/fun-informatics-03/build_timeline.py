"""Timelines for 「报数为什么说『幺』？」 / "Why Do Pilots Say 'Bravo'?" (FUN-INFORMATICS-03.md §5).

Episode 1's builder (scripts/fun-informatics-01/build_timeline.py) does the voice work: it trims and levels
each Louise take, and its helpers write the narration track and the SRT captions. This adds what episode 3
needs on top: *events*, sounds that play on their own after a line's speech, with the picture following them:

  - the two walkie-talkie listening tests (radio.py), after ns01-02 and ns01-06;
  - the family's own voices from the Pictionary footage at the moment a drawing is guessed (Lucas, Cashew,
    the moon, the star). Only those short stretches are used: the rest of the room talk, with other
    children's names in it, stays out.

Writes, for each language:
  public/fun-informatics-03/timeline.LANG.json   cues + events, which Remotion loads before rendering
  public/fun-informatics-03/audio/LANG.wav       narration and events
  public/fun-informatics-03/audio/LANG.mix.wav   the film's soundtrack (music joins once it is chosen)
  out/fun-informatics-03/delivery/fun-informatics-03.LANG.{zh-Hans,en}.srt

  python3 scripts/fun-informatics-03/build_timeline.py [zh|en]
"""
import array
import importlib.util
import json
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("fi01_timeline", ROOT / "scripts/fun-informatics-01/build_timeline.py")
shared = importlib.util.module_from_spec(spec)
spec.loader.exec_module(shared)
wp = shared.wp
PUB = shared.PUB = ROOT / "public/fun-informatics-03"
# Music (owner, 2026-10-16): Mozart's Twinkle Variations, K. 265, played by Simone Renzi (CC BY 3.0, music/SOURCES.txt).
# Each section gets its own variations, cut at the pauses between them in the recording (found from its quiet gaps):
MUSIC_SOURCE = PUB / "music/mozart-k265-renzi.mp3"
K265 = {  # seconds in the recording
    "theme": (3.85, 47.85), "v1": (49.0, 89.8), "v2": (91.15, 132.5), "v3": (134.1, 176.15), "v4": (178.45, 218.55),
    "v5": (220.85, 260.4), "v6": (261.35, 303.0), "v7": (303.95, 345.7), "v8": (349.45, 397.85), "v9": (401.55, 452.9),
    "v10": (456.25, 496.0), "v11": (498.25, 651.1), "v12": (652.45, 724.25),
}
MUSIC_PLAN = {
    "ns00": ["theme"],             # the tune as everyone knows it
    "ns01": ["v5", "v2", "v4"],    # light and sparse under the explaining
    "ns02": ["v1", "v3", "v12"],   # lively for the game
    "ns03": ["v11"],               # the slow variation, then the theme comes back to end the film
}
SECTION_XF = 2.5                   # crossfade between sections
THEME_TAIL = 1.5                   # the closing theme ends this long before the film does
QUIET = (1.2, 1.0)                 # no music from this long before a radio test until this long after it
wp.MUSIC = MUSIC_SOURCE            # replaced per film by its own bed (music_bed)
wp.PEAK_DB = -2.0  # AAC headroom for the final <= -1.5 dBTP ceiling, as in episode 2
TRANSLATIONS = json.loads((ROOT / "docs/fun-informatics-03/translations.json").read_text())
DELIVERY = ROOT / "out/fun-informatics-03/delivery"
FILM_NAME = "fun-informatics-03"
VOICES = {lang: shared.MEDIA / f"outputs/louise/{lang}/fun-informatics-03-v1" for lang in ("zh", "en")}
TITLE = {"zh": "报数为什么说「幺」？", "en": "Why Do Pilots Say “Bravo”?"}
FPS, RATE = shared.FPS, wp.RATE
LEAD_IN, ONSET, GAP, SECTION_GAP, END_CARD = 1.2, 0.15, 0.4, 0.9, 8.0
EVENT_GAP = 0.5    # silence between a line's speech and its event
EVENT_DB = -2.0    # the family's voices sit a little under the narration
# Extra seconds after a line (after its events, if any): a card to read, a title to land, a drawing to look at.
HOLD = {
    "ns00-01": 1.2, "ns00-02": 1.0, "ns00-03": 0.8, "ns00-04": 3.2,
    "ns01-01": 0.6, "ns01-02": 1.4, "ns01-03": 1.0, "ns01-04": 0.8, "ns01-05": 0.6, "ns01-06": 1.0,
    "ns01-07": 0.6, "ns01-08": 0.8, "ns01-09": 2.0,
    "ns02-01": 0.6, "ns02-02": 0.3, "ns02-03": 0.6, "ns02-04": 1.0, "ns02-05": 0.4, "ns02-06": 1.6,
    "ns02-07": 2.4, "ns02-08": 0.6, "ns02-09": 0.6, "ns02-10": 2.0,
    "ns03-01": 1.0, "ns03-02": 1.2, "ns03-03": 1.5, "ns03-04": 4.0,
}
# After a cue's speech: (name, source file under public/fun-informatics-03, from s, to s). Footage times are
# the clip's own (footage.py keeps the camera's sound and timing).
EVENTS = {
    "ns01-02": [("radio-test1", "audio/radio-{lang}-test1-120ms.wav", None, None)],
    "ns01-06": [("radio-test2", "audio/radio-{lang}-test2.wav", None, None)],
    "ns02-03": [("lucas", "footage/r1-lucas.mp4", 26.2, 31.0)],     # "Lucas?" "Yeah."
    "ns02-05": [("cachew", "footage/r1-cachew.mp4", 16.9, 24.2)],   # "A dog." "Cashew." "Okay, good job."
    "ns02-08": [("moon", "footage/r2-moon.mp4", 8.5, 12.0)],        # "Banana." "Okay, moon." "Yeah."
    "ns02-09": [("star", "footage/r2-star.mp4", 17.1, 20.1)],       # "Oh, this is star." "Yeah, star."
}


def decode(path: Path, start, end) -> array.array:
    """A stretch of any file's sound as 24 kHz mono 16-bit, levelled like a narration line."""
    cut = [] if start is None else ["-ss", f"{start}", "-to", f"{end}"]
    with tempfile.TemporaryDirectory() as tmp:
        wav = Path(tmp, "event.wav")
        subprocess.run(["ffmpeg", "-v", "error", "-y", *cut, "-i", str(path), "-ac", "1", "-ar", str(RATE),
                        "-af", "afade=t=in:d=0.04,areverse,afade=t=in:d=0.08,areverse", str(wav)], check=True)
        clip = wp.read_wav(wav)
    clip = wp.level(clip)
    gain = 10 ** (EVENT_DB / 20)
    return array.array("h", (max(-32768, min(32767, round(s * gain))) for s in clip))


def music_bed(lang, cues, total) -> Path:
    """The film's own music: each section's variations in order, trimmed to the section, crossfaded into the next.
    The last section's slow variation hands over to the theme, so the film ends on the tune's own final cadence."""
    starts = []
    for prefix in MUSIC_PLAN:
        starts.append(0.0 if prefix == "ns00" else next(c["start"] for c in cues if c["id"].startswith(prefix)))
    names = [n for plan in MUSIC_PLAN.values() for n in plan] + ["theme"]
    graph = [f"[0:a]aresample=48000,aformat=sample_fmts=flt:channel_layouts=stereo,asplit={len(names)}" + "".join(f"[in{k}]" for k in range(len(names)))]
    k = 0
    def seg(name):
        nonlocal k
        a, b = K265[name]
        graph.append(f"[in{k}]atrim={a}:{b},asetpts=PTS-STARTPTS[g{k}]")
        k += 1
        return f"[g{k - 1}]"
    sections = []
    for i, (prefix, plan) in enumerate(MUSIC_PLAN.items()):
        parts = "".join(seg(n) for n in plan)
        last = i == len(MUSIC_PLAN) - 1
        if not last:
            length = starts[i + 1] - starts[i] + SECTION_XF
        else:
            theme = K265["theme"][1] - K265["theme"][0]
            length = (total - THEME_TAIL - theme) - starts[i] + SECTION_XF  # the slow variation's share
            assert length > SECTION_XF * 2, f"{lang}: no room for the closing theme"
        # A section longer than its music (the opening outlasts the theme) rests in silence after the cadence.
        graph.append(f"{parts}concat=n={len(plan)}:v=0:a=1,apad=whole_dur={length:.3f},atrim=0:{length:.3f},asetpts=PTS-STARTPTS[sec{i}]")
        sections.append(f"[sec{i}]")
    tail = seg("theme")
    graph.append(f"{sections[-1]}{tail}acrossfade=d={SECTION_XF}:c1=tri:c2=tri,apad=whole_dur={total - starts[-1]:.3f}[sec{len(sections) - 1}x]")
    sections[-1] = f"[sec{len(sections) - 1}x]"
    chain = sections[0]
    for i, nxt in enumerate(sections[1:], 1):
        graph.append(f"{chain}{nxt}acrossfade=d={SECTION_XF}:c1=tri:c2=tri[x{i}]")
        chain = f"[x{i}]"
    graph.append(f"{chain}atrim=0:{total:.3f}[bed]")
    out = PUB / f"audio/music-bed.{lang}.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(MUSIC_SOURCE), "-filter_complex", ";".join(graph),
                    "-map", "[bed]", "-c:a", "pcm_f32le", str(out)], check=True)
    got = shared.seconds(out)
    assert abs(got - total) < 0.05, f"{lang}: music bed is {got:.2f}s, film {total:.2f}s"
    return out


_quiet = []  # (start, end) of the radio tests in the film being mixed
sys.path.insert(0, str(ROOT / "scripts"))
import music_ducking  # noqa: E402  (README "Music under narration": the music gives way in every gap, not only long pauses)

assert music_ducking.LINE_LUFS == wp.LINE_LUFS
# The project's ducking, with no music at all around the radio tests: the listener hears only the radio.
wp.music_envelope = lambda cues, total, bed_lufs, path: music_ducking.envelope(
    cues, total, bed_lufs, path, quiet=[(a - QUIET[0], b + QUIET[1]) for a, b in _quiet])


def finish(mix: Path) -> None:
    """Without a music bed, wp.mix_with_music only resamples; give the film the same -16 LUFS and peak ceiling."""
    if wp.MUSIC.is_file():
        return
    with tempfile.TemporaryDirectory() as tmp:
        raw = Path(tmp, "raw.wav")
        mix.rename(raw)
        gain = wp.FILM_LUFS - wp.loudness("-i", str(raw))
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(raw), "-af",
                        f"volume={gain:.2f}dB,alimiter=limit={10 ** (wp.PEAK_DB / 20):.4f}:attack=5:release=50:level=false:latency=true",
                        "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le", str(mix)], check=True)
    print(f"  mix {wp.loudness('-i', str(mix)):.1f} LUFS (no music; gain {gain:+.1f} dB)")


LIMIT = {"zh": 26, "en": 84}  # characters per caption, about two lines on YouTube


def split(text, marks):
    """Cut after each mark, but never inside a quotation, and an English mark only before a space."""
    parts, cur, depth = [], "", 0
    for k, ch in enumerate(text):
        cur += ch
        depth += (ch in "「“") - (ch in "」”")
        if ch == '"':
            depth = 1 - depth
        if depth <= 0 and ch in marks and (ch in "。？！；，：」" or k + 1 == len(text) or text[k + 1] == " "):
            parts.append(cur.strip())
            cur = ""
    if cur.strip():
        parts.append(cur.strip())
    return parts


def pieces(text, key):
    """A line split at sentence ends, and at commas where a sentence is still too long, short pieces merged,
    so each caption stays within about two lines."""
    ends, commas = ("。？！；", "，：") if key == "zh" else (".?!;", ",:")
    parts = []
    for sentence in split(text, ends):
        parts += split(sentence, commas) if len(sentence) > LIMIT[key] else [sentence]
    out = []
    for part in parts:
        if out and len(out[-1]) + len(part) + (0 if key == "zh" else 1) <= LIMIT[key]:
            out[-1] = out[-1] + ("" if key == "zh" else " ") + part
        else:
            out.append(part)
    return out


def write_captions(lang, cues):
    """Each film's own words, and a translation of them (never the other film's lines: its examples differ).
    A cue's speech time is shared among its pieces by length."""
    DELIVERY.mkdir(parents=True, exist_ok=True)
    other = "en" if lang == "zh" else "zh"
    captions = {lang: {c["id"]: c[lang] for c in cues}, other: TRANSLATIONS[f"{lang}-film-{other}"]}
    for name, key in (("zh-Hans", "zh"), ("en", "en")):
        blocks, n = [], 0
        for c in cues:
            parts = pieces(captions[key][c["id"]], key)
            a, b = c["speech"]["start"], c["speech"]["end"]
            total = sum(len(p) for p in parts)
            t = a
            for k, part in enumerate(parts):
                end = b + 0.6 if k == len(parts) - 1 else t + (b - a) * len(part) / total
                n += 1
                blocks.append(f"{n}\n{wp.srt_time(t)} --> {wp.srt_time(end)}\n{part}\n")
                t = end
        (DELIVERY / f"{FILM_NAME}.{lang}.{name}.srt").write_text("\n".join(blocks), encoding="utf-8")


def build(langs):
    cue_text = json.loads((PUB / "narration/cues.json").read_text())
    ids = [c["id"] for c in cue_text]
    footage = shared.listing("footage", (".mp4",))
    common = {"fps": FPS, "leadIn": LEAD_IN, "title": TITLE, "footage": footage,
              "images": shared.listing("images", (".png", ".jpg")),
              "footageSeconds": {name: shared.seconds(PUB / "footage" / name) for name in footage}}
    for lang in langs:
        missing, clips = [], {}
        for c in cue_text:
            path = VOICES[lang] / f"{c['id']}.wav"
            if path.is_file():
                clips[c["id"]] = wp.level(wp.trim(wp.read_wav(path)))
            else:
                missing.append(c["id"])
                clips[c["id"]] = wp.estimate(lang, c[lang])
        t, cues, events, sounds = LEAD_IN, [], [], []
        for n, c in enumerate(cue_text):
            speech = len(clips[c["id"]]) / RATE
            at = t + ONSET + speech + GAP
            for name, src, a, b in EVENTS.get(c["id"], []):
                at += EVENT_GAP - GAP if not events or events[-1]["cue"] != c["id"] else EVENT_GAP
                clip = decode(PUB / src.format(lang=lang), a, b)
                length = len(clip) / RATE
                events.append({"name": name, "cue": c["id"], "start": round(at, 3), "end": round(at + length, 3),
                               "src": src.format(lang=lang), "srcStart": a, "srcEnd": b})
                sounds.append((at, clip))
                at += length + GAP
            last_in_section = n + 1 == len(ids) or ids[n + 1][:4] != c["id"][:4]
            end = at + HOLD.get(c["id"], 0) + (SECTION_GAP if last_in_section else 0)
            cues.append({"id": c["id"], "section": c["section"], "zh": c["zh"], "en": c["en"],
                         "start": round(t, 3), "end": round(end, 3),
                         "speech": {"start": round(t + ONSET, 3), "end": round(t + ONSET + speech, 3)}})
            sounds.append((t + ONSET, clips[c["id"]]))
            t = end
        total = t + END_CARD
        audio = PUB / "audio"
        audio.mkdir(parents=True, exist_ok=True)
        track = array.array("h", bytes(2 * round(total * RATE)))
        for start, clip in sounds:
            k = round(start * RATE)
            track[k:k + len(clip)] = clip
        wp.write_wav(audio / f"{lang}.wav", track, RATE)
        # Events count as speech for the music's ducking.
        speaking = cues + [{"id": e["name"], "start": e["start"], "end": e["end"],
                            "speech": {"start": e["start"], "end": e["end"]}} for e in events]
        if MUSIC_SOURCE.is_file():
            wp.MUSIC = music_bed(lang, cues, total)
            _quiet[:] = [(e["start"], e["end"]) for e in events if e["name"].startswith("radio")]
        wp.mix_with_music(audio / f"{lang}.wav", audio / f"{lang}.mix.wav", sorted(speaking, key=lambda c: c["speech"]["start"]), total)
        finish(audio / f"{lang}.mix.wav")
        write_captions(lang, cues)
        data = {**common, "lang": lang, "durationSeconds": round(total, 3), "endCardStart": round(t, 3),
                "cues": cues, "events": events, "draft": bool(missing)}
        (PUB / f"timeline.{lang}.json").write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n")
        print(f"{lang}: {len(cues)} cues, {len(events)} events, {total:.1f}s ({total / 60:.1f} min)")
        if missing:
            print(f"  ESTIMATED (no take yet): {', '.join(missing)}")


if __name__ == "__main__":
    langs = [a for a in sys.argv[1:] if a in ("zh", "en")] or ["zh", "en"]
    if "--captions-only" in sys.argv:  # rewrite the SRTs from the existing timelines; the rendered films stay valid
        for lang in langs:
            write_captions(lang, json.loads((PUB / f"timeline.{lang}.json").read_text())["cues"])
    else:
        build(langs)
