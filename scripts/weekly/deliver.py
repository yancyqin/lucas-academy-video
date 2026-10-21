"""好奇新世界 / Curious Worlds: the mix, the captions and the upload folder of each film of an episode.

Two films (owner, 2026-10-20): the Chinese film and the English film, each on its own timeline, each -16 LUFS, each
with both caption files timed to its own voice (README: no burned-in captions). The music bed is the episode's own
(shots.py MUSIC); it sits under the voice and rises in the gaps, driven by the timeline rather than a sidechain
(a ducker swells in every long hold).

Run with lucas-academy-media's Python (numpy, soundfile):
  python scripts/weekly/deliver.py 001 mix [zh|en]        # out/weekly/<ep>/mix.<lang>.wav
  npx remotion render Weekly001 out/weekly/001/picture.zh.mp4 --muted --props='{"episode":"001","lang":"zh","voice":false}'
  npx remotion render Weekly001En out/weekly/001/picture.en.mp4 --muted --props='{"episode":"001","lang":"en","voice":false}'
  python scripts/weekly/deliver.py 001 package [zh|en]    # film, captions, cover, upload text -> the Desktop folder
"""
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import soundfile as sf

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from assets import PLAYGROUND, ROOT, load_shots  # noqa: E402

SR = 48000
TARGET_LUFS = -16.0
BED_LUFS = -24.0      # the bed alone, in the gaps
BED_DUCK_DB = -11.0   # under a voice
RAMP = 0.45           # seconds for the bed to dip or rise
FADE_IN, FADE_OUT = 1.5, 4.0


def ffmpeg(*args: str) -> None:
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", *args], check=True)


def loudness(path: Path) -> float:
    out = subprocess.run(["ffmpeg", "-nostats", "-i", str(path), "-af", "ebur128=peak=true:framelog=quiet", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    return float(re.findall(r"I:\s+(-?[\d.]+) LUFS", out)[-1])


def read(path: Path, channels: int = 2) -> np.ndarray:
    """Any audio file as float32 at SR with `channels` channels (decoded by ffmpeg)."""
    with tempfile.NamedTemporaryFile(suffix=".wav") as tmp:
        ffmpeg("-i", str(path), "-ac", str(channels), "-ar", str(SR), "-c:a", "pcm_f32le", tmp.name)
        data, _ = sf.read(tmp.name, dtype="float32", always_2d=True)
    return data


def bed(ep: str, tl: dict, n: int) -> np.ndarray:
    music = getattr(load_shots(ep), "MUSIC", None)
    if not music:
        return np.zeros((n, 2), np.float32)
    src = PLAYGROUND / music["src"]
    data = read(src)[int(music.get("start", 0) * SR):]
    with tempfile.NamedTemporaryFile(suffix=".wav") as tmp:  # level the music itself once, by measurement
        sf.write(tmp.name, data, SR)
        data *= 10 ** ((BED_LUFS - loudness(Path(tmp.name))) / 20)
    xf = int(4.0 * SR)  # loop with a crossfade when the episode is longer than the piece
    out = data.copy()
    while len(out) < n:
        ramp = np.linspace(0, 1, xf)[:, None]
        out[-xf:] = out[-xf:] * (1 - ramp) + data[:xf] * ramp
        out = np.concatenate([out, data[xf:]])
    out = out[:n]
    # Under the voices the bed dips; between them it comes back. Driven by the timeline, not by the signal.
    env = np.ones(n, np.float32)
    duck = 10 ** (BED_DUCK_DB / 20)
    t = np.arange(n) / SR
    for c in tl["cues"]:
        a, b = c["start"] - 0.2, c["end"] + 0.15
        down = np.clip((t - (a - RAMP)) / RAMP, 0, 1)
        up = np.clip(((b + RAMP) - t) / RAMP, 0, 1)
        env = np.minimum(env, 1 - (1 - duck) * np.minimum(down, up))
    env *= np.clip(t / FADE_IN, 0, 1) * np.clip((tl["durationSeconds"] - t) / FADE_OUT, 0, 1)
    return out * env[:, None]


def timeline(ep: str, lang: str) -> dict:
    return json.loads((ROOT / "public/weekly" / ep / f"timeline.{lang}.json").read_text())


def mix(ep: str, lang: str) -> None:
    pub = ROOT / "public/weekly" / ep
    out = ROOT / "out/weekly" / ep
    out.mkdir(parents=True, exist_ok=True)
    tl = timeline(ep, lang)
    if tl["draft"]:
        raise SystemExit("timeline is a draft (lines still estimated): voice every line, run takes.py and build_timeline.py")
    n = int(np.ceil(tl["durationSeconds"] * SR))
    music = bed(ep, tl, n)
    voice = np.zeros((n, 2), np.float32)
    for c in tl["cues"]:
        take = read(pub / "narration" / lang / f"{c['id']}.wav")
        a = int(round(c["start"] * SR))
        voice[a:a + len(take)] += take[: n - a]
    track = voice + music
    raw = out / f"mix.{lang}.raw.wav"
    sf.write(raw, track, SR, subtype="FLOAT")
    gain = TARGET_LUFS - loudness(raw)
    final = out / f"mix.{lang}.wav"
    # A fixed gain to the target, then a true-peak limiter for the few loudest syllables.
    ffmpeg("-i", str(raw), "-af", f"volume={gain:.2f}dB,alimiter=limit=0.84:level=false:attack=3:release=60", "-c:a", "pcm_s24le", str(final))
    raw.unlink()
    print(f"{lang}: {final.relative_to(ROOT)}  {loudness(final):.1f} LUFS")


def stamp(s: float) -> str:
    ms = int(round(s * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def pieces(text: str, lang: str) -> list[str]:
    """A long line becomes two or three captions at its own pauses."""
    limit = 26 if lang == "zh" else 84
    if len(text) <= limit:
        return [text]
    parts = re.split(r"(?<=[，。；：？！])" if lang == "zh" else r"(?<=[,.;:?!])\s+", text)
    out, cur = [], ""
    for p in parts:
        if cur and len(cur) + len(p) > limit:
            out.append(cur)
            cur = p
        else:
            cur += p if lang == "zh" else (" " + p if cur else p)
    return out + [cur] if cur else out


def srt(ep: str, film: str) -> dict:
    """Both caption files of one film, timed to that film's voice: its own words and their translation."""
    tl = timeline(ep, film)
    files = {}
    for lang, name in (("zh", "zh-Hans"), ("en", "en")):
        rows, i = [], 1
        for c in tl["cues"]:
            parts = pieces(c[lang], lang)
            weights = np.cumsum([0] + [len(p) for p in parts]) / sum(len(p) for p in parts)
            for k, p in enumerate(parts):
                a = c["start"] + (c["end"] - c["start"]) * weights[k]
                b = c["start"] + (c["end"] - c["start"]) * weights[k + 1]
                rows.append(f"{i}\n{stamp(a)} --> {stamp(b - 0.04)}\n{p}\n")
                i += 1
        path = ROOT / "out/weekly" / ep / f"weekly-{ep}.{film}.{name}.srt"
        path.write_text("\n".join(rows), encoding="utf-8")
        files[lang] = path
    return files


UPLOAD = {"zh": "好奇新世界-第{n}期-上传", "en": "好奇新世界-第{n}期-英文版-上传"}


def package(ep: str, lang: str) -> None:
    out = ROOT / "out/weekly" / ep
    picture = out / f"picture.{lang}.mp4"
    if not picture.exists():
        raise SystemExit(f"render the picture first: {picture.relative_to(ROOT)}")
    film = out / f"weekly-{ep}.{lang}.mp4"
    ffmpeg("-i", str(picture), "-i", str(out / f"mix.{lang}.wav"), "-map", "0:v", "-map", "1:a", "-c:v", "copy",
           "-c:a", "aac", "-b:a", "256k", "-metadata:s:a:0", f"language={'zho' if lang == 'zh' else 'eng'}",
           "-shortest", "-movflags", "+faststart", str(film))
    files = [film, *srt(ep, lang).values()]
    for extra in (f"cover.{lang}.jpg", f"youtube.{lang}.txt"):
        if (out / extra).exists():
            files.append(out / extra)
    folder = Path.home() / "Desktop" / UPLOAD[lang].format(n=int(ep))
    folder.mkdir(parents=True, exist_ok=True)
    for f in files:
        subprocess.run(["cp", str(f), str(folder / f.name)], check=True)
    print(f"{lang}: {folder}\n  " + "\n  ".join(f.name for f in files))


if __name__ == "__main__":
    ep, step, *langs = sys.argv[1:]
    for language in langs or ["zh", "en"]:
        {"mix": mix, "srt": srt, "package": package}[step](ep, language)
