"""Audition versions of Matthew's English readings of the two Stevenson poems (owner, 2026-10-27: his voice is a
bit quiet — make it louder, take the noise out, give a few versions to compare before it goes into the films).

    .venv-align/bin/python scripts/zhong-ying/matthew_voice.py          # the audition versions
    .venv-align/bin/python scripts/zhong-ying/matthew_voice.py clips    # the chosen one, cut into the films' stanzas

The memos (iPhone, 2026-10-27) sit about 16 dB under the other lines (−37 / −35 LUFS) with a room hum under them,
mostly below 300 Hz, about 27 dB under his voice; levelled up to the other lines, that hum comes up with him. The
denoiser is spectral gating (learn the noise from the pauses, turn each frequency down where it is no louder than
that noise), which kept quiet children's voices better than DeepFilterNet or Demucs in the kids-toon film.
  0-plain        only made louder (and the rumble under 90 Hz cut) — to hear what the others take away
  A-clean        light gating (−12 dB), then the studio chain the other recorded voices use (sunny_voice.py STUDIO)
  B-cleaner      strong gating (−24 dB), then the same studio chain
  C-fuller       strong gating, then a fuller sound for a child's voice: a little warmth and presence, firmer
                 compression, a touch more room
Each enters its chain at the other recordings' level (−29 LUFS) so the studio chain treats it the same way.
Writes DATA/narration/matthew/versions/<version>/<poem>.wav and, on the Desktop, one audition mp3 per version (both
poems, all at −16 LUFS, so loudness is not what tells them apart) plus one stanza in all four versions back to back.
The owner chose C (2026-10-27). `clips` cuts it into one clip per stanza, DATA/narration/matthew/en/<film>-vNN.wav,
which films.clip() prefers over Louise's takes; DATA/narration/matthew/cuts.json says where each was cut.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.ndimage import uniform_filter
from scipy.signal import istft, stft

sys.path.insert(0, str(Path(__file__).resolve().parent))
from films import DATA  # noqa: E402
from sunny_voice import STUDIO  # noqa: E402

HERE = DATA / "narration" / "matthew"
OUT = HERE / "versions"
DESKTOP = Path.home() / "Desktop" / "中英阅读-语音试听" / "Matthew"
SR = 48000
# memo on the Desktop → the poem it reads
RECORDINGS = {"New Recording.m4a": "foreign-lands", "New Recording 2.m4a": "where-go-the-boats"}
CHAIN_LUFS = -29.0               # where Windchime 18 / 19 entered the studio chain
FULLER = ("highpass=f=80,equalizer=f=220:t=q:w=1.0:g=1.5,equalizer=f=3000:t=q:w=1.2:g=3.5,highshelf=f=9000:g=2,"
          "deesser=i=0.4,acompressor=threshold=-28dB:ratio=4:attack=6:release=120:makeup=4,"
          "aecho=0.85:0.55:23|41|67:0.09|0.06|0.04")
CHOSEN = "C-fuller"              # the owner's pick, 2026-10-27
FILM_OF = {"foreign-lands": "climb-higher", "where-go-the-boats": "little-boats"}
PRE, POST = 0.22, 0.35           # kept before a stanza's first sound and after its last (as sunny_voice.py)
VERSIONS = {
    "0-plain": ("0-原样放大", None, None),
    "A-clean": ("A-降噪+录音室", 12, STUDIO),
    "B-cleaner": ("B-强降噪+录音室", 24, STUDIO),
    "C-fuller": ("C-强降噪+更饱满", 24, FULLER),
}


def ff(*args, **kw):
    return subprocess.run(["ffmpeg", "-v", "error", "-y", *map(str, args)], check=True, **kw)


def lufs(path) -> float:
    meter = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(path), "-af", "ebur128", "-f", "null", "-"],
                           capture_output=True, text=True).stderr
    return float(re.findall(r"I:\s+(-?[\d.]+) LUFS", meter)[-1])


def spectral_gate(x: np.ndarray, reduce_db: float, n_std: float = 1.5) -> np.ndarray:
    """Learn the noise from the quietest 15 % of frames (the pauses); keep a frequency where it rises n_std above
    that noise, turn it down by reduce_db where it doesn't. The mask is smoothed over ±2 bins and ±3 frames so the
    gating doesn't leave the chirping 'musical noise' a hard mask does."""
    _, _, z = stft(x, SR, nperseg=2048, noverlap=1536)
    mag = np.abs(z)
    db = 20 * np.log10(mag + 1e-10)
    power = (mag ** 2).sum(0)
    quiet = power <= np.percentile(power, 15)
    thresh = db[:, quiet].mean(1) + n_std * db[:, quiet].std(1)
    mask = uniform_filter((db > thresh[:, None]).astype(float), size=(5, 7))
    floor = 10 ** (-reduce_db / 20)
    _, y = istft(z * (floor + (1 - floor) * mask), SR, nperseg=2048, noverlap=1536)
    return y[:len(x)]


def snr(path) -> float:
    """Voice over what is left in the pauses: the 95th percentile of 20 ms frames over the 10th, in dB."""
    a, _ = sf.read(path)
    a = a if a.ndim == 1 else a.mean(1)
    h = SR // 50
    env = 20 * np.log10(np.array([np.sqrt(np.mean(a[i:i + h] ** 2)) for i in range(0, len(a) - h, h)]) + 1e-10)
    return float(np.percentile(env, 95) - np.percentile(env, 10))


def main():
    DESKTOP.mkdir(parents=True, exist_ok=True)
    report = {}
    for name, poem in RECORDINGS.items():
        raw = HERE / "raw" / (Path(name).stem.replace(" ", "-").lower() + ".wav")
        ff("-i", HERE / "raw" / name, "-ac", "1", "-ar", SR, raw)
        x, _ = sf.read(raw)
        cut = HERE / "work" / f"{poem}-hp.wav"
        cut.parent.mkdir(parents=True, exist_ok=True)
        ff("-i", raw, "-af", "highpass=f=90:poles=2", cut)
        hp, _ = sf.read(cut)
        for v, (_, reduce_db, chain) in VERSIONS.items():
            (OUT / v).mkdir(parents=True, exist_ok=True)
            y = hp if reduce_db is None else spectral_gate(hp, reduce_db)
            pre = HERE / "work" / f"{poem}-{v}.wav"
            sf.write(pre, y, SR)
            gain = CHAIN_LUFS - lufs(pre)
            out = OUT / v / f"{poem}.wav"
            ff("-i", pre, "-af", f"volume={gain:.2f}dB" + (f",{chain}" if chain else ""), out)
            report[f"{v}/{poem}"] = {"snr_db": round(snr(out), 1), "gain_db": round(gain, 1)}
            print(f"{v:10s} {poem:20s} +{gain:.1f} dB  voice over pauses {snr(out):.1f} dB")

    for v, (label, _, _) in VERSIONS.items():
        parts = [OUT / v / f"{p}.wav" for p in RECORDINGS.values()]
        audition(parts, DESKTOP / f"{label}.mp3")
    # one stanza in every version, back to back: "Dark brown is the river … on either hand." (0.3–9.2 s)
    stanza = []
    for v in VERSIONS:
        piece = HERE / "work" / f"stanza-{v}.wav"
        ff("-ss", "0.30", "-to", "9.20", "-i", OUT / v / "where-go-the-boats.wav", "-af",
           "afade=t=in:d=0.02,areverse,afade=t=in:d=0.08,areverse", piece)
        stanza.append(piece)
    audition(stanza, DESKTOP / "对比-同一段-0ABC.mp3", each=True)
    (OUT / "README.json").write_text(json.dumps({"recordings": RECORDINGS, "chain_lufs": CHAIN_LUFS,
                                                 "versions": {k: [l, r, c] for k, (l, r, c) in VERSIONS.items()},
                                                 "measured": report}, ensure_ascii=False, indent=1))


def clips():
    """One clip per stanza of the chosen version, cut the way sunny_voice.py cuts Sunny's: the known text is aligned
    to find which stanza is where, then each is cut in the real pause around it (the aligner's word times can start
    a line late), from the end of the pause before it to the start of the pause after."""
    import stable_whisper

    from films import FILMS, texts

    model = stable_whisper.load_model("medium", device="cpu")
    (HERE / "en").mkdir(parents=True, exist_ok=True)
    cuts = {}
    for poem, film in FILM_OF.items():
        units = next(w["units"] for w in FILMS[film]["works"] if w["id"] == poem)
        spoken = {u["n"]: u["spoken_en"] for u in texts(film)}
        src = OUT / CHOSEN / f"{poem}.wav"
        audio, _ = sf.read(src)
        words = model.align(str(src), " ".join(spoken[n] for n in units), language="en").all_words()
        spans, at = [], 0
        for n in units:
            k = len(spoken[n].split())
            spans.append((words[at].start, words[at + k - 1].end))
            at += k
        assert at == len(words), f"{poem}: aligned {len(words)} words, expected {at}"
        hop = SR // 100
        env = np.sqrt(np.convolve(audio ** 2, np.ones(hop) / hop, "same")[::hop])
        loud = env > env.max() * 10 ** (-35 / 20)      # the gated pauses sit about 45 dB under him
        edges = []
        for a, b in spans:
            i, j = int(a * 100), min(len(loud) - 1, int(b * 100))
            while i > 0 and loud[max(0, i - 25):i].any():   # back to the last 250 ms pause
                i -= 1
            while j < len(loud) - 1 and loud[j:j + 25].any():
                j += 1
            edges.append((i / 100, j / 100))
        for i, (n, (a, b)) in enumerate(zip(units, edges)):
            lo = max(0.0, a - PRE) if i == 0 else max(a - PRE, (edges[i - 1][1] + a) / 2)
            hi = min(len(audio) / SR, b + POST) if i == len(edges) - 1 else min(b + POST, (b + edges[i + 1][0]) / 2)
            name = f"{film}-v{n:02d}"
            ff("-ss", f"{lo:.3f}", "-to", f"{hi:.3f}", "-i", src, "-af",
               "afade=t=in:d=0.015,areverse,afade=t=in:d=0.015,areverse", HERE / "en" / f"{name}.wav")
            cuts[name] = {"version": CHOSEN, "from": round(lo, 3), "to": round(hi, 3), "sound": [round(a, 3), round(b, 3)],
                          "text": spoken[n]}
            print(f"{name} {lo:6.2f}–{hi:6.2f}s (sound {a:.2f}–{b:.2f})  {spoken[n]}")
    (HERE / "cuts.json").write_text(json.dumps(cuts, ensure_ascii=False, indent=1))


def audition(parts, dest, each=False):
    """Pieces with a pause between, at −16 LUFS. each=True levels every piece on its own first, so a comparison
    of versions is not a comparison of loudness."""
    pre = "loudnorm=I=-16:TP=-3:LRA=11," if each else ""
    graph = "".join(f"[{i}]aresample={SR},aformat=channel_layouts=mono,{pre}apad=pad_dur=1.2[a{i}];"
                    for i in range(len(parts)))
    graph += "".join(f"[a{i}]" for i in range(len(parts))) + f"concat=n={len(parts)}:v=0:a=1,loudnorm=I=-16:TP=-3:LRA=11"
    wav = HERE / "work" / (dest.stem + ".wav")     # through a wav: loudnorm's frame timing upsets the mp3 muxer
    ff(*sum((["-i", p] for p in parts), []), "-filter_complex", graph, "-ar", SR, wav)
    ff("-i", wav, "-codec:a", "libmp3lame", "-b:a", "192k", dest)


if __name__ == "__main__":
    clips() if sys.argv[1:] == ["clips"] else main()
