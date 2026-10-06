"""Build the timelines for "全人教育的五个理念 / Five Principles of Whole-Person Education".

lucas-academy-media#5. Two films, one per language, each paced by its own
narration (no shared timeline). Reads the confirmed line scripts and per-line
narration WAVs from lucas-academy-media, then writes for each LANG in zh, en:
  public/whole-person-01/timeline.LANG.json      cue timeline Remotion loads before rendering
  public/whole-person-01/audio/LANG.wav          full-length narration track
  public/whole-person-01/audio/LANG.mix.wav      narration + music bed, -16 LUFS
  out/whole-person-01/delivery/whole-person-five-principles.LANG.{zh-Hans,en}.srt
                                                 captions for that film; both languages
                                                 share its cue times

Nothing is burned in: YouTube gets the clean film plus both SRTs.
A missing WAV is stood in for by silence of an estimated length (and reported).

The mix keeps the sound steady; a listener heard the first zh film go 「忽高忽低」.
Every line is levelled to LINE_LUFS (CosyVoice takes come out a few dB apart).
The music sits MUSIC_UNDER dB below the voice and rises to MUSIC_PAUSE only in
pauses of PAUSE s or more; a sidechain compressor had let it swell 12 dB in every
card hold. The result gets one fixed gain to FILM_LUFS plus a peak limiter
(one-pass loudnorm rides the gain).

  --keep-timeline LANG [--remux]
      The picture is already rendered: keep public/whole-person-01/timeline.LANG.json
      and rebuild only that film's audio, e.g. after pitch.py re-voiced lines (every
      take must still fit its slot). --remux then puts the new mix on
      out/whole-person-01/delivery/whole-person-five-principles.LANG.mp4 as
      whole-person-five-principles.LANG.remix.mp4, picture untouched.
"""
import array
import json
import math
import os
import re
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MEDIA = Path(os.environ.get("LUCAS_MEDIA", ROOT.parent / "lucas-academy-media"))
SCRIPTS = {
    "zh": MEDIA / "data/scripts/whole-person-five-ideas-zh.json",
    "en": MEDIA / "data/scripts/whole-person-five-ideas-en.json",
}
VOICES = {
    "zh": MEDIA / "outputs/louise/zh/whole-person-five-ideas-v10",  # Louise's Chinese voice, zero-shot-instruct teaching tone
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
# Background music: "Echoes in the Void" (Yancy's Suno track for the Journey of
# Art room), looped with crossfades under the narration.
MUSIC = ROOT / "public/whole-person-01/music/echoes-in-the-void.m4a"
MUSIC_XFADE = 6.0   # seconds of crossfade between loops
LINE_LUFS = -23.0   # every line is levelled to this before the mix
MUSIC_UNDER = -17   # music level while someone speaks, dB re the voice
MUSIC_PAUSE = -10   # music level in a pause of PAUSE s or more (a card on screen)
PAUSE = 2.5
FADE_DOWN, FADE_UP = 0.5, 1.5   # seconds for the music to make room, and to come back
FILM_LUFS, PEAK_DB = -16.0, -1.5
ENV_RATE = 1000     # music-envelope samples per second


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


def write_wav(path: Path, samples: array.array, rate: int) -> None:
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate)
        w.writeframes(samples.tobytes())


def loudness(*source: str, data=None) -> float:
    """Integrated loudness (EBU R128, LUFS) of one ffmpeg input."""
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", *source, "-af", "ebur128=framelog=quiet", "-f", "null", "-"],
                       input=data, capture_output=True, check=True)
    return float(re.findall(r"I:\s+(-?[\d.]+) LUFS", r.stderr.decode())[-1])


def level(clip: array.array) -> array.array:
    """The clip at LINE_LUFS."""
    lufs = loudness("-f", "s16le", "-ar", str(RATE), "-ac", "1", "-i", "-", data=clip.tobytes())
    if lufs < -60:  # a silent stand-in for a missing take
        return clip
    gain = 10 ** ((LINE_LUFS - lufs) / 20)
    return array.array("h", [max(-32768, min(32767, round(s * gain))) for s in clip])


def music_envelope(cues: list, total: float, bed_lufs: float, path: Path) -> None:
    """The music bed's gain over time, as a 16-bit WAV at ENV_RATE (full scale = unity)."""
    under = 10 ** ((LINE_LUFS + MUSIC_UNDER - bed_lufs) / 20)
    pause = 10 ** ((LINE_LUFS + MUSIC_PAUSE - bed_lufs) / 20)
    spans = []  # speech, merged across pauses shorter than PAUSE
    for c in cues:
        a, b = c["speech"]["start"], c["speech"]["end"]
        if spans and a - spans[-1][1] < PAUSE:
            spans[-1][1] = b
        else:
            spans.append([a, b])
    n = math.ceil(total * ENV_RATE)
    duck = [0.0] * n  # 1 = under the voice, 0 = in a pause
    for a, b in spans:
        a0, a1, b1, b2 = (round(x * ENV_RATE) for x in (a - FADE_DOWN, a, b, b + FADE_UP))
        for k in range(max(0, a0), min(n, b2)):
            d = 1.0 if a1 <= k < b1 else (k - a0) / (a1 - a0) if k < a1 else 1 - (k - b1) / (b2 - b1)
            duck[k] = max(duck[k], d)
    fade_in, fade_out = 2 * ENV_RATE, 5 * ENV_RATE
    env = array.array("h", [
        round(min(1.0, pause * (under / pause) ** duck[k] * min(1.0, k / fade_in, (n - k) / fade_out)) * 32767)
        for k in range(n)
    ])  # the level moves in dB, not in amplitude
    write_wav(path, env, ENV_RATE)


def mix_with_music(voice: Path, out: Path, cues: list, total: float) -> None:
    """Narration over the looped music bed, one fixed gain to FILM_LUFS, peaks limited (48 kHz stereo)."""
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
    stereo = "aresample=48000,pan=stereo|c0=c0|c1=c0,aformat=sample_fmts=flt"
    with tempfile.TemporaryDirectory() as tmp:
        bed, env, premix = Path(tmp, "bed.wav"), Path(tmp, "envelope.wav"), Path(tmp, "premix.wav")
        graph = ";".join(chain + [f"{last}atrim=0:{total:.3f},asetpts=PTS-STARTPTS,aresample=48000,aformat=sample_fmts=flt:channel_layouts=stereo[bed]"])
        subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", graph, "-map", "[bed]", "-c:a", "pcm_f32le", str(bed)], check=True)
        music_envelope(cues, total, loudness("-i", str(bed)), env)
        graph = f"[1:a]{stereo}[env];[0:a][env]amultiply[music];[2:a]{stereo}[vo];[music][vo]amix=inputs=2:normalize=0[mix]"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(bed), "-i", str(env), "-i", str(voice), "-filter_complex", graph,
                        "-map", "[mix]", "-c:a", "pcm_f32le", str(premix)], check=True)
        gain = FILM_LUFS - loudness("-i", str(premix))
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(premix), "-af",
                        f"volume={gain:.2f}dB,alimiter=limit={10 ** (PEAK_DB / 20):.4f}:attack=5:release=50:level=false:latency=true",
                        "-ar", "48000", "-c:a", "pcm_s16le", str(out)], check=True)
    print(f"  mix {loudness('-i', str(out)):.1f} LUFS (gain {gain:+.1f} dB)")


def keep_timeline(lang: str, remux: bool) -> None:
    """Rebuild only LANG's audio on its existing timeline, so the rendered picture still fits."""
    timeline = json.loads((ROOT / f"public/whole-person-01/timeline.{lang}.json").read_text())
    total = timeline["durationSeconds"]
    track = array.array("h", bytes(2 * round(total * RATE)))
    cues = []
    for cue in timeline["cues"]:
        clip = level(trim(read_wav(VOICES[lang] / f"{cue['id']}.wav")))
        start, room = cue["speech"]["start"], cue["end"] - cue["speech"]["start"] - 0.1
        if len(clip) / RATE > room:
            sys.exit(f"{cue['id']}: the take runs {len(clip) / RATE:.2f}s but its slot holds {room:.2f}s; "
                     "re-voice it shorter, or rebuild the timeline and re-render")
        at = round(start * RATE)
        track[at:at + len(clip)] = clip
        cues.append({**cue, "speech": {"start": start, "end": start + len(clip) / RATE}})
    audio_dir = ROOT / "public/whole-person-01/audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    write_wav(audio_dir / f"{lang}.wav", track, RATE)
    mix_with_music(audio_dir / f"{lang}.wav", audio_dir / f"{lang}.mix.wav", cues, total)
    print(f"{lang}: audio rebuilt on the existing timeline ({total:.1f}s)")
    if remux:
        film = ROOT / f"out/whole-person-01/delivery/whole-person-five-principles.{lang}.mp4"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(film), "-i", str(audio_dir / f"{lang}.mix.wav"),
                        "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac", "-b:a", "320k",
                        "-movflags", "+faststart", str(film.with_suffix(".remix.mp4"))], check=True)
        print(f"  -> {film.with_suffix('.remix.mp4').name}")


def srt_time(t: float) -> str:
    ms = round(t * 1000)
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def present(sub: str, exts: tuple[str, ...]) -> list[str]:
    d = ROOT / "public/whole-person-01" / sub
    return sorted(f.name for f in d.iterdir() if f.suffix.lower() in exts) if d.is_dir() else []


def build() -> None:
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
                clips[i] = level(trim(read_wav(path)))
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
        write_wav(audio_dir / f"{lang}.wav", track, RATE)
        mix_with_music(audio_dir / f"{lang}.wav", audio_dir / f"{lang}.mix.wav", cues, total)

        out = ROOT / "out/whole-person-01/delivery"
        out.mkdir(parents=True, exist_ok=True)
        for name, key in (("zh-Hans", "zh"), ("en", "en")):
            blocks = [
                f"{n}\n{srt_time(c['speech']['start'])} --> {srt_time(c['end'] - 0.1)}\n{c[key]}\n"
                for n, c in enumerate(cues, 1)
            ]
            (out / f"whole-person-five-principles.{lang}.{name}.srt").write_text("\n".join(blocks), encoding="utf-8")

        data = {**shared, "lang": lang, "durationSeconds": round(total, 3), "endCardStart": round(t, 3), "cues": cues}
        (ROOT / f"public/whole-person-01/timeline.{lang}.json").write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n")
        speech = sum(len(c) for c in clips.values()) / RATE
        print(f"{lang}: {len(cues)} cues, {total:.1f}s ({total/60:.1f} min), speech {speech:.1f}s")
        if missing:
            print(f"  ESTIMATED (no wav yet): {len(missing)} lines, e.g. {', '.join(missing[:6])}")


if __name__ == "__main__":
    if "--keep-timeline" in sys.argv:
        keep_timeline(sys.argv[sys.argv.index("--keep-timeline") + 1], "--remux" in sys.argv)
    else:
        build()
