"""Mix and mux the delivered files of 你知道印象派的秘密吗？ / Do You Know the Secret of Impressionism?

Run after `remotion render ... ImpressionismPicture out/impressionism-secret/picture.mp4`.
The picture is rendered once without audio. Each narration track is laid over a
bed of Satie and Fauré (public-domain and CC BY recordings, sources in
public/impressionism-secret/music/SOURCES.txt): the pieces follow one another
with crossfades, fade in and out, and duck whenever someone speaks. The mix is
loudness-matched (two-pass EBU R128, -16 LUFS, -1.5 dBTP) so switching the
YouTube audio language does not jump in volume, made exactly as long as the
picture (YouTube requires a dub to match the video), and muxed in:

  impressionism-secret.en.mp4   upload this: picture + English (default track; v6, owner 2026-11-02)
  impressionism-secret.zh.m4a   add in Studio → Languages as the Chinese dub
  impressionism-secret.zh.mp4   the same picture with Chinese, for checking
  impressionism-secret.{zh,en}.srt  captions (written by build_timeline.py)

`deliver.py --sample START SECONDS` writes mix-sample.{zh,en}.m4a instead: an
excerpt of the same mix, for judging the music level before a render.
"""
import argparse
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "out/impressionism-secret"
AUDIO = ROOT / "public/impressionism-secret/audio"
MUSIC_DIR = ROOT / "public/impressionism-secret/music/src"
# The bed, in order; repeated from the top if the film is longer.
PLAYLIST = ["satie-gymnopedie-1-laucke.flac", "faure-violin-sonata-1-andante.ogg",
            "satie-gymnopedie-2-laucke.flac", "satie-gymnopedie-1-alciatore.ogg"]
PICTURE = OUT / "picture.mp4"
TIMELINE = ROOT / "src/data/impressionism-secret.json"
LOUDNORM = "loudnorm=I=-16:TP=-1.5:LRA=11"

MUSIC_GAIN_DB = -14   # the bed in the pauses, against narration that ends up at -16 LUFS
LOOP_CROSSFADE = 6    # seconds where one piece hands over to the next
FADE_IN, FADE_OUT = 2.0, 4.0
# Ducking: the voice is the key; the bed dips ~6 dB while anyone speaks and
# comes back over 0.7 s, slow enough not to pump between words.
DUCK = "sidechaincompress=threshold=0.03:ratio=6:attack=20:release=700:makeup=1"


def run(*args: str) -> str:
    result = subprocess.run(args, capture_output=True, text=True, check=True)
    return result.stderr


def duration(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
        capture_output=True, text=True, check=True,
    ).stdout
    return float(out)


def measure(path: Path, filters: str = LOUDNORM) -> dict:
    options = f"{filters}{':' if '=' in filters else '='}print_format=json"
    log = run("ffmpeg", "-hide_banner", "-nostats", "-i", str(path),
              "-af", options, "-f", "null", "-")
    return json.loads(re.findall(r"\{[^{}]*\}", log)[-1])


def bed(length: float, out: Path) -> None:
    """The playlist, crossfaded piece to piece and repeated, as one stereo WAV at least `length` long."""
    files, total = [], 0.0
    while total < length + LOOP_CROSSFADE:
        for name in PLAYLIST:
            files.append(MUSIC_DIR / name)
            total += duration(MUSIC_DIR / name) - LOOP_CROSSFADE
    inputs = [arg for f in files for arg in ("-i", str(f))]
    norm = "".join(f"[{i}:a]aresample=48000,aformat=channel_layouts=stereo[m{i}];" for i in range(len(files)))
    chain, last = "", "m0"
    for i in range(1, len(files)):
        chain += f"[{last}][m{i}]acrossfade=d={LOOP_CROSSFADE}:c1=tri:c2=tri[x{i}];"
        last = f"x{i}"
    run("ffmpeg", "-hide_banner", "-y", *inputs, "-filter_complex", norm + chain.rstrip(";"),
        "-map", f"[{last}]", "-ar", "48000", "-c:a", "pcm_s16le", str(out))


def mix(narration: Path, music: Path, length: float, out: Path) -> None:
    """Narration over the music bed, exactly `length` seconds, 48 kHz stereo WAV."""
    graph = (
        f"[1:a]atrim=0:{length:.3f},"
        f"afade=t=in:d={FADE_IN},afade=t=out:st={length - FADE_OUT:.3f}:d={FADE_OUT},"
        f"volume={MUSIC_GAIN_DB}dB[bed];"
        f"[0:a]aresample=48000,aformat=channel_layouts=stereo,apad,atrim=0:{length:.3f},asplit[voice][key];"
        f"[bed][key]{DUCK}[ducked];"
        "[voice][ducked]amix=inputs=2:normalize=0:duration=first"
    )
    run("ffmpeg", "-hide_banner", "-y", "-i", str(narration), "-i", str(music),
        "-filter_complex", graph, "-ar", "48000", "-c:a", "pcm_s16le", str(out))


def normalized(source: Path, out: Path, trim: tuple[float, float] | None = None) -> dict:
    m = measure(source)
    second_pass = (
        f"{LOUDNORM}:measured_I={m['input_i']}:measured_TP={m['input_tp']}"
        f":measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}"
        f":offset={m['target_offset']}:linear=true"
    )
    cut = ["-ss", f"{trim[0]:.3f}", "-t", f"{trim[1]:.3f}"] if trim else []
    run("ffmpeg", "-hide_banner", "-y", "-i", str(source), *cut, "-af", second_pass,
        "-ar", "48000", "-ac", "2", "-c:a", "aac", "-b:a", "192k", str(out))
    return m


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample", nargs=2, type=float, metavar=("START", "SECONDS"))
    parser.add_argument("--language", choices=("zh", "en", "all"), default="all",
                        help="Remix only the selected language after a narration correction")
    args = parser.parse_args()
    length = (json.loads(TIMELINE.read_text())["durationSeconds"] if args.sample else duration(PICTURE))
    music = OUT / "bed.wav"
    bed(length, music)
    languages = ("zh", "en") if args.language == "all" else (args.language,)
    for lang in languages:
        mixed = OUT / f"mix.{lang}.wav"
        mix(AUDIO / f"{lang}.wav", music, length, mixed)
        if args.sample:
            sample = OUT / f"mix-sample.{lang}.m4a"
            normalized(mixed, sample, tuple(args.sample))
            print(f"{lang}: {sample.relative_to(ROOT)}")
        else:
            track = OUT / f"impressionism-secret.{lang}.m4a"
            m = normalized(mixed, track)
            video = OUT / f"impressionism-secret.{lang}.mp4"
            run("ffmpeg", "-hide_banner", "-y", "-i", str(PICTURE), "-i", str(track),
                "-map", "0:v:0", "-map", "1:a:0", "-c", "copy",
                "-metadata:s:a:0", f"language={'zho' if lang == 'zh' else 'eng'}",
                "-movflags", "+faststart", str(video))
            check = measure(track, "loudnorm")
            print(f"{lang}: {m['input_i']} → {check['input_i']} LUFS, "
                  f"peak {check['input_tp']} dBTP, {duration(track):.2f}s (picture {length:.2f}s)")
        mixed.unlink()
    if not args.sample and "en" in languages:
        (OUT / "impressionism-secret.en.m4a").unlink()  # already inside the en video
    music.unlink()


if __name__ == "__main__":
    main()
