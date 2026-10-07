"""Timelines for 「计算机怎么算 1+1=？ / How Does a Computer Add 1 + 1=?」 (FUN-INFORMATICS-01.md).

Two films, one per language, each paced by its own narration (Louise, zh and en). Reads the cues
written by narration.py and the per-line WAVs from lucas-academy-media, then writes for each LANG:
  public/fun-informatics-01/timeline.LANG.json   cue timeline Remotion loads before rendering
  public/fun-informatics-01/audio/LANG.wav       narration track
  public/fun-informatics-01/audio/LANG.mix.wav   narration over "Echoes in the Void", -16 LUFS
  out/fun-informatics-01/delivery/fun-informatics-01.LANG.{zh-Hans,en}.srt

The trimming, levelling and music mix are whole-person-01's (scripts/whole-person-01/build_timeline.py),
imported rather than copied. A missing WAV is stood in for by silence of an estimated length.

  python3 scripts/fun-informatics-01/build_timeline.py [zh|en]
"""
import array
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _media() -> Path:
    if os.environ.get("LUCAS_MEDIA"):
        return Path(os.environ["LUCAS_MEDIA"])
    for parent in ROOT.parents:  # works from a worktree too
        if (parent / "lucas-academy-media").is_dir():
            return parent / "lucas-academy-media"
    raise SystemExit("set LUCAS_MEDIA to a lucas-academy-media checkout")


MEDIA = _media()
_spec = importlib.util.spec_from_file_location("wp01", ROOT / "scripts/whole-person-01/build_timeline.py")
wp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(wp)
PUB = ROOT / "public/fun-informatics-01"
wp.MUSIC = PUB / "music/echoes-in-the-void.m4a"

VOICES = {lang: MEDIA / f"outputs/louise/{lang}/fun-informatics-01-v2" for lang in ("zh", "en")}  # v2 (2026-10-07); v1 takes stay in fun-informatics-01
TITLE = {"zh": "计算机怎么算 1+1=？", "en": "How Does a Computer Add 1 + 1=?"}
FPS, RATE = 30, wp.RATE
LEAD_IN = 6.0      # loading screen (2 s) + the title on the transit chamber
ONSET, GAP, SECTION_GAP, END_CARD = 0.15, 0.4, 0.9, 10.0
# Extra seconds after a line, for the picture: a zoom to watch, a card to read, a painting to finish.
HOLD = {
    "it00-01": 1.0, "it00-03": 4.0, "it00-04": 2.0, "it00-05": 2.0,
    "it01-01": 1.0, "it01-02": 0.8, "it01-04": 1.5, "it01-05": 0.8, "it01-06": 2.0, "it01-07": 2.5,
    "it02-01": 1.0, "it02-04": 0.8, "it02-05": 0.8, "it02-06": 0.8,
    "it03-02": 1.0, "it03-03": 1.5, "it03-04": 0.5, "it03-05": 0.5, "it03-06": 0.5, "it03-07": 0.5, "it03-08": 1.5,
    "it04-01": 0.5, "it04-02": 1.0, "it04-05": 1.2, "it04-06": 1.2, "it04-07": 2.0, "it04-08": 1.5, "it04-09": 1.5,
    "it05-01": 1.0, "it05-03": 1.5, "it05-05": 2.0,
    "it06-02": 2.0, "it06-03": 1.5, "it06-04": 2.0, "it06-05": 1.0, "it06-06": 1.0, "it06-07": 1.5, "it06-08": 2.0,
    "it06-09": 2.5, "it06-10": 3.0, "it06-11": 1.5,
    "it07-02": 2.0, "it07-03": 1.0, "it07-04": 1.0, "it07-05": 1.5, "it07-06": 1.5, "it07-07": 1.0, "it07-08": 1.5,
    "it07-09": 2.0, "it07-10": 1.5,
    "it08-01": 1.5, "it08-02": 2.0, "it08-04": 1.5, "it08-06": 2.0,
    "it09-01": 1.0, "it09-02": 1.0, "it09-04": 2.5, "it09-05": 2.5, "it09-06": 1.0, "it09-07": 2.0, "it09-08": 2.0, "it09-09": 1.5,
    "it10-01": 1.0, "it10-03": 1.5, "it10-04": 1.5, "it10-05": 1.5, "it10-06": 1.0, "it10-07": 1.0, "it10-08": 2.0,
    "it10-09": 1.5, "it10-10": 2.0, "it10-11": 3.0,
    "it11-02": 1.5, "it11-03": 2.0, "it11-05": 3.0, "it11-06": 1.5, "it11-07": 1.0, "it11-08": 1.5,
}


# One film's own exceptions to HOLD. 「当然是二呀！」 (2026-10-07) made the Chinese it01-02 take 0.335 s shorter,
# so its hold grew by as much and the rest of the Chinese film kept its timing; the English film is unchanged.
HOLD_BY_LANG = {"zh": {"it01-02": 1.135}}


def listing(sub: str, exts: tuple) -> list:
    d = PUB / sub
    return sorted(str(f.relative_to(d)) for f in d.rglob("*") if f.suffix.lower() in exts) if d.is_dir() else []


def seconds(path: Path) -> float:
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                                capture_output=True, text=True, check=True).stdout.strip())


def build(langs: list) -> None:
    cue_text = json.loads((PUB / "narration/cues.json").read_text())
    ids = [c["id"] for c in cue_text]
    footage = listing("footage", (".mp4",))
    shared = {
        "fps": FPS, "leadIn": LEAD_IN, "title": TITLE,
        "footage": footage, "images": listing("images", (".png", ".jpg", ".svg")),
        "footageSeconds": {name: seconds(PUB / "footage" / name) for name in footage},
    }
    for lang in langs:
        missing, clips = [], {}
        for c in cue_text:
            path = VOICES[lang] / f"{c['id']}.wav"
            if path.is_file():
                clips[c["id"]] = wp.level(wp.trim(wp.read_wav(path)))
            else:
                missing.append(c["id"])
                clips[c["id"]] = wp.estimate(lang, c[lang])
        t, cues = LEAD_IN, []
        for n, c in enumerate(cue_text):
            speech = len(clips[c["id"]]) / RATE
            last_in_section = n + 1 == len(ids) or ids[n + 1][:4] != c["id"][:4]
            hold = HOLD_BY_LANG.get(lang, {}).get(c["id"], HOLD.get(c["id"], 0))
            slot = ONSET + speech + GAP + hold + (SECTION_GAP if last_in_section else 0)
            cues.append({"id": c["id"], "section": c["section"], "zh": c["zh"], "en": c["en"],
                         "start": round(t, 3), "end": round(t + slot, 3),
                         "speech": {"start": round(t + ONSET, 3), "end": round(t + ONSET + speech, 3)}})
            t += slot
        total = t + END_CARD
        audio = PUB / "audio"
        audio.mkdir(parents=True, exist_ok=True)
        track = array.array("h", bytes(2 * round(total * RATE)))
        for cue in cues:
            at = round(cue["speech"]["start"] * RATE)
            clip = clips[cue["id"]]
            track[at:at + len(clip)] = clip
        wp.write_wav(audio / f"{lang}.wav", track, RATE)
        wp.mix_with_music(audio / f"{lang}.wav", audio / f"{lang}.mix.wav", cues, total)
        out = ROOT / "out/fun-informatics-01/delivery"
        out.mkdir(parents=True, exist_ok=True)
        for name, key in (("zh-Hans", "zh"), ("en", "en")):
            blocks = [f"{n}\n{wp.srt_time(c['speech']['start'])} --> {wp.srt_time(c['end'] - 0.1)}\n{c[key]}\n"
                      for n, c in enumerate(cues, 1)]
            (out / f"fun-informatics-01.{lang}.{name}.srt").write_text("\n".join(blocks), encoding="utf-8")
        data = {**shared, "lang": lang, "durationSeconds": round(total, 3), "endCardStart": round(t, 3), "cues": cues}
        (PUB / f"timeline.{lang}.json").write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n")
        print(f"{lang}: {len(cues)} cues, {total:.1f}s ({total / 60:.1f} min)")
        if missing:
            print(f"  ESTIMATED (no wav yet): {len(missing)} lines, e.g. {', '.join(missing[:6])}")


if __name__ == "__main__":
    build(sys.argv[1:] or ["zh", "en"])  # e.g. `build_timeline.py zh` rebuilds only the Chinese film
