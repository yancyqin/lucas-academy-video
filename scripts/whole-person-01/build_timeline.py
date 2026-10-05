"""Build the timelines for "全人教育的五个理念 / Five Principles of Whole-Person Education".

lucas-academy-media#5. Two films, one per language, each paced by its own
narration (no shared timeline). Reads the confirmed line scripts and per-line
narration WAVs from lucas-academy-media, then writes for each LANG in zh, en:
  src/data/whole-person-01.LANG.json             cue timeline for Remotion
  public/whole-person-01/audio/LANG.wav          full-length narration track
  public/whole-person-01/audio/LANG.mix.wav      narration + ducked music bed, -16 LUFS
  out/whole-person-01/LANG/zh-Hans.srt, en.srt   captions for that film; both
                                                 languages share its cue times

Nothing is burned in: YouTube gets the clean film plus both SRTs.
A missing WAV is stood in for by silence of an estimated length (and reported).
"""
import array
import json
import math
import subprocess
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MEDIA = ROOT.parent / "lucas-academy-media"
SCRIPTS = {
    "zh": MEDIA / "data/scripts/whole-person-five-ideas-zh.json",
    "en": MEDIA / "data/scripts/whole-person-five-ideas-en.json",
}
VOICES = {
    "zh": MEDIA / "outputs/yancy/zh/whole-person-five-ideas-v8",  # Yancy, zero-shot-instruct teaching tone, 1.0
    "en": MEDIA / "outputs/louise/en/whole-person-five-ideas-v8",
}
FPS = 30
RATE = 24000
LEAD_IN = 6.0      # loading screen (2 s) + title on the chamber before the question
ONSET = 0.15       # breath at the start of every cue
GAP = 0.4          # after every cue
SECTION_GAP = 0.9  # extra at the end of a section
END_CARD = 9.0
SILENCE = 300      # |sample| below this (about -40 dBFS) counts as silence when trimming
KEEP = round(0.05 * RATE)
# Extra time to read a card or watch a demo after a line.
HOLD = {
    "wp00-01": 1.5, "wp00-03": 0.6, "wp00-06": 1.0, "wp00-08": 1.5, "wp01-19": 1.0, "wp01-07": 1.0, "wp01-09": 0.8, "wp01-10": 0.8, "wp01-11": 0.8,
    "wp01-14": 3.2, "wp01-16": 3.5, "wp02-03": 1.0, "wp02-07": 3.0, "wp02-09": 3.0,
    "wp03-03": 1.0, "wp03-05": 4.0, "wp04-03": 1.0, "wp04-04": 1.0, "wp04-07": 4.0,
    "wp05-04": 1.0, "wp05-06": 4.0, "wp06-02": 1.5,
}
# Background music: "Echoes in the Void" (owner's track for the Journey of Art
# room), looped with crossfades, ducked under the narration, mix at -16 LUFS.
MUSIC = ROOT / "public/whole-person-01/music/echoes-in-the-void.m4a"
MUSIC_XFADE = 6.0   # seconds of crossfade between loops
MUSIC_BED_DB = -13  # bed level before ducking


def read_wav(path: Path) -> array.array:
    with wave.open(str(path)) as w:
        assert w.getframerate() == RATE and w.getnchannels() == 1 and w.getsampwidth() == 2, path
        return array.array("h", w.readframes(w.getnframes()))


def trim(clip: array.array) -> array.array:
    """Drop room tone before the first and after the last word, keeping a few ms."""
    loud = [i for i in range(0, len(clip), 120) if abs(clip[i]) > SILENCE]
    if not loud:
        return clip
    return clip[max(0, loud[0] - KEEP):min(len(clip), loud[-1] + KEEP)]


def estimate(lang: str, text: str) -> array.array:
    seconds = len(text) / 4.6 if lang == "zh" else len(text.split()) / 2.6
    return array.array("h", bytes(2 * round(seconds * RATE)))


def mix_with_music(voice: Path, out: Path, total: float) -> None:
    """Narration over the looped, ducked music bed, loudness-normalised (48 kHz stereo)."""
    if not MUSIC.is_file():
        print(f"  no music at {MUSIC}; narration only")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(voice), "-ar", "48000", "-ac", "2", str(out)], check=True)
        return
    length = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(MUSIC)],
                                  capture_output=True, text=True, check=True).stdout)
    loops = max(1, math.ceil((total - MUSIC_XFADE) / (length - MUSIC_XFADE)))
    inputs = sum((["-i", str(MUSIC)] for _ in range(loops)), [])
    chain, last = [], "[0:a]"
    for k in range(1, loops):
        chain.append(f"{last}[{k}:a]acrossfade=d={MUSIC_XFADE}:c1=tri:c2=tri[m{k}]")
        last = f"[m{k}]"
    v = loops  # index of the narration input
    graph = ";".join(chain + [
        f"{last}atrim=0:{total:.3f},asetpts=PTS-STARTPTS,afade=t=in:d=2,afade=t=out:st={total - 5:.3f}:d=5,"
        f"volume={MUSIC_BED_DB}dB,aresample=48000[bed]",
        f"[{v}:a]aresample=48000,aformat=channel_layouts=stereo,asplit=2[vo][sc]",
        "[bed][sc]sidechaincompress=threshold=0.02:ratio=6:attack=60:release=900[duck]",
        "[duck][vo]amix=inputs=2:normalize=0,loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000[mix]",
    ])
    subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-i", str(voice), "-filter_complex", graph,
                    "-map", "[mix]", "-ac", "2", "-ar", "48000", "-t", f"{total:.3f}", str(out)], check=True)


def srt_time(t: float) -> str:
    ms = round(t * 1000)
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def present(sub: str, exts: tuple[str, ...]) -> list[str]:
    d = ROOT / "public/whole-person-01" / sub
    return sorted(f.name for f in d.iterdir() if f.suffix.lower() in exts) if d.is_dir() else []


def main() -> None:
    scripts = {lang: json.loads(p.read_text()) for lang, p in SCRIPTS.items()}
    text = {lang: {l["id"]: l["text"] for l in s["lines"]} for lang, s in scripts.items()}
    ids = list(text["zh"])
    assert ids == list(text["en"]), "zh and en scripts must have the same line ids"

    footage = present("footage", (".mp4", ".mov", ".webm"))
    shared = {
        "fps": FPS, "leadIn": LEAD_IN,
        "title": {lang: s["title"] for lang, s in scripts.items()},
        "footage": footage, "images": present("images", (".png", ".jpg")),
        # Clip lengths let Remotion loop a recording exactly (OffthreadVideo has no loop).
        "footageSeconds": {
            name: float(subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                 str(ROOT / "public/whole-person-01/footage" / name)],
                capture_output=True, text=True, check=True).stdout.strip())
            for name in footage
        },
    }

    for lang in ("zh", "en"):
        missing, clips = [], {}
        for i in ids:
            path = VOICES[lang] / f"{i}.wav"
            if path.is_file():
                clips[i] = trim(read_wav(path))
            else:
                missing.append(i)
                clips[i] = estimate(lang, text[lang][i])

        t = LEAD_IN
        cues = []
        for n, i in enumerate(ids):
            speech = len(clips[i]) / RATE
            last_in_section = n + 1 == len(ids) or ids[n + 1][:4] != i[:4]
            slot = ONSET + speech + GAP + HOLD.get(i, 0) + (SECTION_GAP if last_in_section else 0)
            cues.append({
                "id": i, "section": i[:4], "zh": text["zh"][i], "en": text["en"][i],
                "start": round(t, 3), "end": round(t + slot, 3),
                "speech": {"start": round(t + ONSET, 3), "end": round(t + ONSET + speech, 3)},
            })
            t += slot
        total = t + END_CARD

        audio_dir = ROOT / "public/whole-person-01/audio"
        audio_dir.mkdir(parents=True, exist_ok=True)
        track = array.array("h", bytes(2 * round(total * RATE)))
        for cue in cues:
            at = round(cue["speech"]["start"] * RATE)
            clip = clips[cue["id"]]
            track[at:at + len(clip)] = clip
        with wave.open(str(audio_dir / f"{lang}.wav"), "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(RATE)
            w.writeframes(track.tobytes())
        mix_with_music(audio_dir / f"{lang}.wav", audio_dir / f"{lang}.mix.wav", total)

        out = ROOT / "out/whole-person-01" / lang
        out.mkdir(parents=True, exist_ok=True)
        for name, key in (("zh-Hans.srt", "zh"), ("en.srt", "en")):
            blocks = [
                f"{n}\n{srt_time(c['speech']['start'])} --> {srt_time(c['end'] - 0.1)}\n{c[key]}\n"
                for n, c in enumerate(cues, 1)
            ]
            (out / name).write_text("\n".join(blocks), encoding="utf-8")

        data = {**shared, "lang": lang, "durationSeconds": round(total, 3), "endCardStart": round(t, 3), "cues": cues}
        (ROOT / f"src/data/whole-person-01.{lang}.json").write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n")
        speech = sum(len(c) for c in clips.values()) / RATE
        print(f"{lang}: {len(cues)} cues, {total:.1f}s ({total/60:.1f} min), speech {speech:.1f}s")
        if missing:
            print(f"  ESTIMATED (no wav yet): {len(missing)} lines, e.g. {', '.join(missing[:6])}")


if __name__ == "__main__":
    main()
