"""Mix and mux the delivered files of "Why Did Van Gogh Paint Them?" (media#3).

Run after `remotion render ... VgWhyPicture out/vg-why-paint-them/picture.mp4`.
The picture is rendered once without audio. Each narration track is laid over
the Van Gogh House music (Human Horizon A, the owner's Suno song — provenance in
inception-space-ui/content/inception/assets/PROVENANCE.md): the song loops with
a crossfade, fades in and out, and ducks whenever someone speaks. The mix is
loudness-matched (two-pass EBU R128, -16 LUFS, -1.5 dBTP) so switching the
YouTube audio language does not jump in volume, made exactly as long as the
picture (YouTube requires a dub to match the video), and muxed in:

  vg-why-paint-them.zh.mp4   upload this: picture + Chinese (default track)
  vg-why-paint-them.en.m4a   add in Studio → Languages as the English dub
  vg-why-paint-them.en.mp4   the same picture with English, for checking
  zh-Hans.srt, en.srt        captions (written by build_timeline.py)

`deliver.py --sample START SECONDS` writes mix-sample.{zh,en}.m4a instead: an
excerpt of the same mix, for judging the music level before a render.
"""
import argparse
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "out/vg-why-paint-them"
AUDIO = ROOT / "public/vg-why-paint-them/audio"
MUSIC = ROOT / "public/vg-why-paint-them/music/van-gogh-human-horizon-a-v1.mp3"
PICTURE = OUT / "picture.mp4"
TIMELINE = ROOT / "src/data/vg-why-paint-them.json"
LOUDNORM = "loudnorm=I=-16:TP=-1.5:LRA=11"

MUSIC_GAIN_DB = -13   # the bed in the pauses, against narration that ends up at -16 LUFS
LOOP_CROSSFADE = 8    # seconds where the song's end overlaps its next start
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


def mix(narration: Path, length: float, out: Path) -> None:
    """Narration over the room music, exactly `length` seconds, 48 kHz stereo WAV."""
    graph = (
        f"[1:a][2:a]acrossfade=d={LOOP_CROSSFADE}:c1=tri:c2=tri,atrim=0:{length:.3f},"
        f"afade=t=in:d={FADE_IN},afade=t=out:st={length - FADE_OUT:.3f}:d={FADE_OUT},"
        f"volume={MUSIC_GAIN_DB}dB[bed];"
        f"[0:a]aresample=48000,aformat=channel_layouts=stereo,apad,atrim=0:{length:.3f},asplit[voice][key];"
        f"[bed][key]{DUCK}[ducked];"
        "[voice][ducked]amix=inputs=2:normalize=0:duration=first"
    )
    run("ffmpeg", "-hide_banner", "-y", "-i", str(narration), "-i", str(MUSIC), "-i", str(MUSIC),
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
    args = parser.parse_args()
    length = (json.loads(TIMELINE.read_text())["durationSeconds"] if args.sample else duration(PICTURE))
    for lang in ("zh", "en"):
        mixed = OUT / f"mix.{lang}.wav"
        mix(AUDIO / f"{lang}.wav", length, mixed)
        if args.sample:
            sample = OUT / f"mix-sample.{lang}.m4a"
            normalized(mixed, sample, tuple(args.sample))
            print(f"{lang}: {sample.relative_to(ROOT)}")
        else:
            track = OUT / f"vg-why-paint-them.{lang}.m4a"
            m = normalized(mixed, track)
            video = OUT / f"vg-why-paint-them.{lang}.mp4"
            run("ffmpeg", "-hide_banner", "-y", "-i", str(PICTURE), "-i", str(track),
                "-map", "0:v:0", "-map", "1:a:0", "-c", "copy",
                "-metadata:s:a:0", f"language={'zho' if lang == 'zh' else 'eng'}",
                "-movflags", "+faststart", str(video))
            check = measure(track, "loudnorm")
            print(f"{lang}: {m['input_i']} → {check['input_i']} LUFS, "
                  f"peak {check['input_tp']} dBTP, {duration(track):.2f}s (picture {length:.2f}s)")
        mixed.unlink()
    if not args.sample:
        (OUT / "vg-why-paint-them.zh.m4a").unlink()  # already inside the zh video


if __name__ == "__main__":
    main()
