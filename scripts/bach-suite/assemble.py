"""Lay the five Bach pieces end to end, with a silence between each, as one listening track.

  assemble.py            -> DATA/build/suite.wav (+ suite.mp3, timings.json)
  assemble.py --gap 5    seconds of silence between pieces (default 4)

Each of the first four is trimmed of its leading/trailing silence and loudness-matched to
the Jesu film (-16 LUFS, -1.5 dBTP, one plain gain). Jesu is the finished film's own
music.wav, untouched, so that film's picture still lines up with it.

The Gavotte is a dry mono recording with almost no dynamics (LRA 2): at the same LUFS it
sounded smaller and quieter than its wide, reverberant neighbours (owner, 2026-10-11). It
gets a light synthetic hall (`room`: wet level in LU below the dry signal) for stereo width
and is set louder (`lufs`) so its loud passages meet the Air's.
"""
import argparse
import json
import pathlib
import re
import subprocess

DATA = pathlib.Path("/Users/yqin/repo/playground/lucas-academy-video-data/bach-suite")
JOURNEY = pathlib.Path("/Users/yqin/repo/playground/lucas-academy-video-data/journey/music")
JESU = pathlib.Path("/Users/yqin/repo/playground/lucas-academy-video-data/jesu/build/music.wav")

PIECES = [
    {"id": "prelude", "title": "C 大调前奏曲 BWV 846", "src": JOURNEY / "prelude-c-ishizaka.flac"},
    # the picture holds 2 s after the cello dies away, then only 2 s of black (owner, 2026-10-14)
    {"id": "cello", "title": "第一大提琴组曲 · 前奏曲 BWV 1007", "src": JOURNEY / "cello-chris-cc0.ogg",
     "tail": 2.0, "gap_after": 2.0},
    {"id": "gavotte", "title": "加沃特回旋曲 BWV 1006", "src": DATA / "music/gavotte-bwv1006-vicond-ccby.ogg",
     "room": 8, "lufs": -14},
    {"id": "air", "title": "G 弦上的咏叹调 BWV 1068", "src": JOURNEY / "candidates/air-bwv1068-usaf-strings.mp3"},
    {"id": "jesu", "title": "耶稣，世人仰望的喜悦 BWV 147", "src": JESU, "as_is": True},
]
FMT = ["-ar", "48000", "-ac", "2", "-c:a", "pcm_s24le"]
F32 = ["-ar", "48000", "-ac", "2", "-c:a", "pcm_f32le"]
# keep 0.3 s before the first note; keep the decay down to -60 dB, then 0.5 s more
TRIM = ("silenceremove=start_periods=1:start_threshold=-55dB:start_silence=0.3,"
        "areverse,silenceremove=start_periods=1:start_threshold=-60dB:start_silence=0.5,areverse")


def ffmpeg(*args):
    return subprocess.run(["ffmpeg", "-hide_banner", "-y", *args], capture_output=True, text=True, check=True)


def duration(path):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                 "-of", "csv=p=0", str(path)], capture_output=True, text=True).stdout)


def measure(path):
    """-> (integrated LUFS, true peak dBTP)"""
    r = ffmpeg("-i", str(path), "-af", "loudnorm=I=-16:TP=-1.5:print_format=json", "-f", "null", "-")
    m = json.loads(re.findall(r"\{[^{}]*\}", r.stderr)[-1])
    return float(m["input_i"]), float(m["input_tp"])


def room_ir(path):
    """A 2.4 s synthetic hall: decorrelated noise per channel, exponential decay (RT60 ~1.4 s),
    dark (5 kHz low-pass), 18 ms pre-delay."""
    if not path.exists():
        ffmpeg("-f", "lavfi", "-i", "anoisesrc=d=2.4:c=white:seed=11:a=0.5",
               "-f", "lavfi", "-i", "anoisesrc=d=2.4:c=white:seed=29:a=0.5", "-filter_complex",
               "[0][1]amerge=inputs=2,afade=t=out:st=0:d=2.4:curve=exp,lowpass=f=5000,highpass=f=150,"
               "adelay=18|18", *F32, str(path))
    return path


def prepare(p, out):
    """Trimmed, loudness-matched 48 kHz stereo wav of piece p -> what was done to its level.

    One plain gain, never compression: up to p's `lufs` (default -16), but no further than a
    -1.5 dBTP peak allows. The solo piano and cello stop ~2 dB short; loudnorm's dynamic mode
    would get them there only by squashing them."""
    if p.get("as_is"):
        ffmpeg("-i", str(p["src"]), *FMT, str(out))
        return "as is"
    tmp = out.with_suffix(".tmp.wav")
    if "room" in p:
        dry, wet = out.with_suffix(".dry.wav"), out.with_suffix(".wet.wav")
        ffmpeg("-i", str(p["src"]), "-af", f"{TRIM},apad=pad_dur=1.5", *F32, str(dry))
        ffmpeg("-i", str(dry), "-i", str(room_ir(out.parent / "room-ir.wav")), "-filter_complex",
               "[0:a][1:a]afir", *F32, str(wet))
        k = 10 ** ((measure(dry)[0] - measure(wet)[0] - p["room"]) / 20)
        ffmpeg("-i", str(dry), "-i", str(wet), "-filter_complex",
               f"amix=inputs=2:weights=1 {k:.4f}:normalize=0", *F32, str(tmp))
        dry.unlink(), wet.unlink()
    else:
        ffmpeg("-i", str(p["src"]), "-af", TRIM, *F32, str(tmp))
    i, tp = measure(tmp)
    gain = min(p.get("lufs", -16) - i, -1.5 - tp)
    ffmpeg("-i", str(tmp), "-af", f"volume={gain:.2f}dB", *FMT, str(out))
    tmp.unlink()
    return f"{gain:+.1f} dB -> {i + gain:.1f} LUFS" + (f", hall {p['room']} LU under" if "room" in p else "")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gap", type=float, default=4.0)
    gap = ap.parse_args().gap
    build = DATA / "build"
    (build / "pieces").mkdir(parents=True, exist_ok=True)

    def silence(sec):
        path = build / f"pieces/silence-{sec:g}.wav"
        if not path.exists():
            ffmpeg("-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-t", str(sec), *FMT, str(path))
        return path

    parts, timings, t = [], [], 0.0
    for i, p in enumerate(PIECES):
        out = build / f"pieces/{i + 1}-{p['id']}.wav"
        kind = prepare(p, out)
        if p.get("tail"):                      # silence inside the piece: the picture holds on it
            held = out.with_suffix(".held.wav")
            ffmpeg("-i", str(out), "-af", f"apad=pad_dur={p['tail']}", *FMT, str(held))
            held.replace(out)
        d = duration(out)
        timings.append({"id": p["id"], "title": p["title"], "start": round(t, 2), "end": round(t + d, 2)})
        print(f"{i + 1} {p['title']:<32} {t // 60:.0f}:{t % 60:04.1f}  {d:6.1f} s  ({kind})")
        parts.append(out)
        t += d
        if i + 1 < len(PIECES):
            g = p.get("gap_after", gap)
            parts.append(silence(g))
            t += g

    listing = build / "pieces/concat.txt"
    listing.write_text("".join(f"file '{p}'\n" for p in parts))
    ffmpeg("-f", "concat", "-safe", "0", "-i", str(listing), "-c", "copy", str(build / "suite.wav"))
    ffmpeg("-i", str(build / "suite.wav"), "-c:a", "libmp3lame", "-b:a", "256k", str(build / "suite.mp3"))
    (build / "timings.json").write_text(json.dumps({"gap": gap, "pieces": timings}, ensure_ascii=False, indent=1))
    print(f"suite {t // 60:.0f}:{t % 60:04.1f} -> {build / 'suite.mp3'}")


if __name__ == "__main__":
    main()
