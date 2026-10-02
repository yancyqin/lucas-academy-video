"""Mix the narration of each Language Bridge film into one full-length track.

Two films (owner, 2026-10-01): the Chinese video and the English video, each on
its own timeline (scripts/reciprocal-doors-prep.mjs). For each film this writes
out/reciprocal-doors/<lang>/:
  language-bridge.<lang>.wav         narration over the background music, 48 kHz 16-bit
                                     stereo, -16 LUFS (linear gain only) -- what the film plays
  language-bridge.<lang>.voice.wav   the narration alone (mono, -16 LUFS), for later edits
  language-bridge.<lang>.mp3         the mix, for listening
  language-bridge.<lang>.timing.csv   line id, start, end, texts
(the film's captions in both languages are written there by the prep step).

    ../lucas-academy-media/.conda/bin/python scripts/reciprocal-doors-tracks.py [zh|en]
"""
from __future__ import annotations

import csv
import json
import re
import sys
import subprocess
import tempfile
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "public"
OUT = ROOT / "out/reciprocal-doors"
RATE = 48000
LOUDNESS = -16.0  # integrated LUFS for both languages (YouTube plays speech at about -14)

# Background music (owner's choice, 2026-10-02): Pachelbel's Canon, Kevin MacLeod's
# recording, CC BY 3.0 -- the credit below must go with every upload. Not committed;
# fetch it with the command in LANGUAGE-BRIDGE.md.
MUSIC = PUBLIC / "audio/reciprocal-doors/music/canon-in-d-major-kevin-macleod.mp3"
MUSIC_CREDIT = (
    "Canon in D Major Kevin MacLeod (incompetech.com) "
    "Licensed under Creative Commons: By Attribution 3.0 License https://creativecommons.org/licenses/by/3.0/"
)
# The bed sits where it does in the delivered Van Gogh film -- its music-only pauses
# measure -23 to -26 LUFS against -16 LUFS narration -- whatever the file's own
# level; it dips ~6 dB under the voice and comes back over 0.7 s.
BED_LUFS = -24.0
DUCK = "sidechaincompress=threshold=0.03:ratio=6:attack=20:release=700:makeup=1"
FADE_IN, FADE_OUT = 2.0, 4.0
LOOP_CROSSFADE = 8.0
FIT = 0.05  # within 5% of the film: stretch the piece (pitch kept) so it ends with the film


def read_mono(path: Path) -> np.ndarray:
    with tempfile.NamedTemporaryFile(suffix=".wav") as tmp:
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(path), "-ac", "1", "-ar", str(RATE), tmp.name], check=True)
        audio, _ = sf.read(tmp.name, dtype="float32")
    return audio


def loudness_match(source: Path, target: Path) -> None:
    """Two-pass loudnorm with linear gain only: the performance's dynamics stay as they are."""
    probe = subprocess.run(
        ["ffmpeg", "-hide_banner", "-i", str(source), "-af", f"loudnorm=I={LOUDNESS}:TP=-1.5:LRA=20:print_format=json", "-f", "null", "-"],
        capture_output=True, text=True, check=True,
    ).stderr
    # ffmpeg prints the measurement as the last {...} block, followed by its summary line.
    measured = json.loads(re.findall(r"\{[^{}]*\}", probe)[-1])
    chain = (
        f"loudnorm=I={LOUDNESS}:TP=-1.5:LRA=20:linear=true:"
        f"measured_I={measured['input_i']}:measured_TP={measured['input_tp']}:"
        f"measured_LRA={measured['input_lra']}:measured_thresh={measured['input_thresh']}:offset={measured['target_offset']}"
    )
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(source), "-af", chain, "-ar", str(RATE), "-c:a", "pcm_s16le", str(target)], check=True)


def seconds(path: Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)], capture_output=True, text=True, check=True).stdout
    return float(out)


def integrated(path: Path) -> float:
    log = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(path), "-af", "loudnorm=print_format=json", "-f", "null", "-"], capture_output=True, text=True, check=True).stderr
    return float(json.loads(re.findall(r"\{[^{}]*\}", log)[-1])["input_i"])


def with_music(voice: Path, length: float, out: Path) -> str:
    """Narration over the music bed, exactly `length` seconds; returns how the piece was fitted."""
    music = seconds(MUSIC)
    gain = BED_LUFS - integrated(MUSIC)
    ratio = music / length
    inputs = ["-i", str(voice), "-i", str(MUSIC)]
    fade_out = FADE_OUT
    if abs(ratio - 1) <= FIT:
        # Close enough to stretch: the piece's own ending lands on the film's last frame.
        bed, how = f"[1:a]atempo={ratio:.5f},atrim=0:{length:.3f}", f"stretched x{1 / ratio:.3f} to end with the film"
        fade_out = 1.5
    elif music > length:
        bed, how = f"[1:a]atrim=0:{length:.3f}", f"faded out at {length:.1f} s of {music:.1f} s"
    else:
        inputs += ["-i", str(MUSIC)]
        bed, how = f"[1:a][2:a]acrossfade=d={LOOP_CROSSFADE}:c1=tri:c2=tri,atrim=0:{length:.3f}", "looped once with a crossfade"
    graph = (
        f"{bed},aresample={RATE},aformat=channel_layouts=stereo,"
        f"afade=t=in:d={FADE_IN},afade=t=out:st={length - fade_out:.3f}:d={fade_out},volume={gain:.2f}dB[bed];"
        f"[0:a]aresample={RATE},aformat=channel_layouts=stereo,apad,atrim=0:{length:.3f},asplit[voice][key];"
        f"[bed][key]{DUCK}[ducked];"
        "[voice][ducked]amix=inputs=2:normalize=0:duration=first"
    )
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex", graph, "-ar", str(RATE), "-c:a", "pcm_f32le", str(out)], check=True)
    return f"{how}, bed {gain:+.1f} dB"


def film(lang: str) -> None:
    timeline = json.loads((ROOT / f"src/scripts/reciprocal-doors.timeline.{lang}.json").read_text(encoding="utf-8"))
    if timeline.get("missing"):
        raise SystemExit(f"{lang}: narration missing for {len(timeline['missing'])} parts; run the narration first")
    out = OUT / lang
    out.mkdir(parents=True, exist_ok=True)
    total = int(round(timeline["durationSeconds"] * RATE))
    mix = np.zeros(total, dtype="float32")
    for segment in timeline["segments"]:
        for chunk in segment["chunks"]:
            for part in chunk["tracks"][lang]:
                audio = read_mono(PUBLIC / part["file"])
                at = int(round((chunk["start"] + part["offset"]) * RATE))
                mix[at:at + len(audio)] += audio[: total - at]
    voice = out / f"language-bridge.{lang}.voice.wav"
    wav = out / f"language-bridge.{lang}.wav"
    with tempfile.NamedTemporaryFile(suffix=".wav") as raw:
        sf.write(raw.name, mix, RATE, subtype="FLOAT")
        loudness_match(Path(raw.name), voice)
    with tempfile.NamedTemporaryFile(suffix=".wav") as raw:
        music = with_music(voice, total / RATE, Path(raw.name))
        loudness_match(Path(raw.name), wav)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(wav), "-c:a", "libmp3lame", "-b:a", "192k", str(wav.with_suffix(".mp3"))], check=True)
    with (out / f"language-bridge.{lang}.timing.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.writer(handle)
        writer.writerow(["segment", "line", "start_s", "end_s", "zh", "en"])
        for segment in timeline["segments"]:
            for chunk in segment["chunks"]:
                writer.writerow([segment["id"], chunk["id"], f"{chunk['start']:.3f}", f"{chunk['start'] + chunk['slot']:.3f}", chunk["zh"], chunk["en"]])
    print(f"{lang}: {wav.name} {sf.info(wav).duration:.2f}s (music {music}), timing + captions in {out}")


def main() -> None:
    for lang in sys.argv[1:] or ["zh", "en"]:
        film(lang)


if __name__ == "__main__":
    main()
