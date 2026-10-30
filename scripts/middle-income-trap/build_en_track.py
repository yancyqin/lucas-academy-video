"""English audio track for 「跨越中等收入陷阱」: Yancy's English takes laid on the finished film's timeline.

  /Users/yqin/repo/playground/lucas-academy-video/.venv-align/bin/python scripts/middle-income-trap/build_en_track.py [--srt-only]

Yancy, 2026-10-27: 做英文配音m4a吧. The picture and the Chinese track are finished (build_timeline.py), so nothing on
them moves. Every English line (narrate_en.py) starts when its Chinese line starts, or GAP after the English line
before it if that one ran long; the drift is reported. Li Lu's two clips stay where they are, with his own English.
A take that would run DRIFT past the next Chinese line, or into the next clip or the end card, is sped up (at most
MAX_TEMPO); if that is not enough the build stops and names the line to shorten in en-edit.md. Takes are trimmed,
faded and levelled like the Chinese ones, and the music, its ducking and the final loudness are the Chinese mix's.

Writes out/middle-income-trap/mix.en.wav, delivery/middle-income-trap.en.m4a (exactly the film's length, the extra
audio track YouTube takes) and delivery/middle-income-trap.en.srt. The English captions follow the Chinese lines'
times (an English line starts with its Chinese line), so one English caption file serves both audio tracks; a line
whose English runs longer keeps its caption up until the English ends. Li Lu's words come from the official CBS
transcript. --srt-only writes the captions without any takes (Yancy, 2026-10-27: 也需要英文字幕，先给我).
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
from build_timeline import DATA, MEDIA, ROOT, SR, decode, music_mix, stamp  # noqa: E402

TAKES = MEDIA / "outputs/yancy/en/middle-income-trap-v2"
GAP, DRIFT, MAX_TEMPO = 0.3, 3.0, 1.15
SRT_MAX = 64
# Li Lu's words as Columbia Business School's English transcript has them (education repo sources/talks/
# CBS_2026-10-05_GrahamDodd_LiLu_transcript_en.pdf); the Chinese captions use CBS's Chinese translation.
CLIP_EN = {
    "clipA": "So many countries have reached that level and stagnated there, so much so that there is a term to describe "
             "it: the middle-income trap. Dozens of countries achieved that and stayed there 40 or 50 years later. China "
             "is a large economy, so the question naturally is: What keeps a middle-income country stagnant and prevents "
             "it from breaking through the ceiling? You manufacture, you industrialize, you go with mid- to low-end "
             "manufacturing, but never break away from it.",
    "clipB": "With the zero-sum game, the trouble is that a lot of human nature goes to zero-sum, to the short term. "
             "Whatever you learn today is useless tomorrow. You don't accumulate. You rely more and more on the "
             "impersonal. You get a bigger computer, and now you use AI. You'll be replaced at some point, so what is "
             "the value of that as a human? Of course, I like the human in the loop. I advocate learning, having an "
             "engaged and improved life over time, and compounding your knowledge as well as the capital of the people "
             "in the trusting way.",
}
LINE = re.compile(r"^- (sc\d\d-\d\d) \| (.+)$")


def tempo(y: np.ndarray, factor: float) -> np.ndarray:
    with tempfile.TemporaryDirectory() as d:
        sf.write(f"{d}/a.wav", y, SR, subtype="FLOAT")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{d}/a.wav", "-af", f"atempo={factor:.4f}", f"{d}/b.wav"], check=True)
        out, _ = sf.read(f"{d}/b.wav", dtype="float32")
    return out


def balanced(part: str) -> list:
    """A clause longer than SRT_MAX, cut between words into the fewest, most even pieces."""
    n = -(-len(part) // SRT_MAX)
    words, out, cur = part.split(), [], ""
    for w in words:
        if cur and len(cur) + 1 + len(w) > len(part) / n + 6:
            out.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    return out + [cur]


def pieces(text: str, start: float, end: float):
    """Caption pieces of at most about SRT_MAX characters, split after punctuation (or between words), timed by length."""
    parts = [q for p in re.split(r"(?<=[,.;:?!])\s+", text) if p.strip() for q in (balanced(p.strip()) if len(p.strip()) > SRT_MAX else [p.strip()])]
    merged = []
    for p in parts:
        if merged and len(merged[-1]) + 1 + len(p) <= SRT_MAX:
            merged[-1] += " " + p
        else:
            merged.append(p)
    total, t = sum(len(p) for p in merged), start
    for p in merged:
        d = (end - start) * len(p) / total
        yield t, t + d, p
        t += d


def write_srt(tl: dict, en: dict, spoken_end: dict) -> Path:
    """Each English line on its Chinese line's span (longer if the English runs past it), Li Lu on his clips."""
    cues = [(c["start"], c["end"], CLIP_EN[c["id"]]) for c in tl["clips"]]
    for cid, v in tl["lines"].items():
        cues.append((v["start"], max(v["end"], spoken_end.get(cid, 0.0)), en[cid]))
    cues.sort()
    srt, n = [], 0
    for k, (start, end, text) in enumerate(cues):
        if k + 1 < len(cues):
            end = min(end, cues[k + 1][0] - 0.04)  # never over the next caption
        for a, b, p in pieces(text, start, end):
            n += 1
            srt.append(f"{n}\n{stamp(a)} --> {stamp(b)}\n{p}\n")
    path = ROOT / "out/middle-income-trap/delivery/middle-income-trap.en.srt"
    path.write_text("\n".join(srt))
    print(f"{path.name}: {n} captions")
    return path


def main():
    tl = json.loads((ROOT / "public/middle-income-trap/timeline.json").read_text())
    total = tl["durationSeconds"]
    en = {m[1]: m[2].strip() for raw in (ROOT / "docs/middle-income-trap/en-edit.md").read_text().splitlines()
          if (m := LINE.match(raw))}
    if "--srt-only" in sys.argv:
        write_srt(tl, en, {})
        return
    seq = sorted([(v["start"], "line", k) for k, v in tl["lines"].items()] + [(c["start"], "clip", c["id"]) for c in tl["clips"]])
    end_card = max(v["end"] for v in tl["lines"].values()) + 1.0
    audio = np.zeros(int(total * SR) + SR, np.float32)
    slots, drifts, sped = {}, [], []
    prev_end = 0.0
    for i, (zh_start, kind, cid) in enumerate(seq):
        if kind == "clip":
            clip = next(c for c in tl["clips"] if c["id"] == cid)
            y = decode(DATA / "clips" / clip["src"], trim=False)
            a = int(clip["start"] * SR)
            audio[a:a + len(y)] += y
            prev_end = clip["start"] + len(y) / SR
            continue
        wav = TAKES / f"{cid}.wav"
        if not wav.exists():
            raise SystemExit(f"missing take {wav}")
        y = decode(wav, trim=True)
        start = max(zh_start, prev_end + GAP)
        nxt = seq[i + 1] if i + 1 < len(seq) else (total, "end", "end")
        hard = nxt[0] - 0.5 if nxt[1] == "clip" else end_card + 3.0 if nxt[1] == "end" else float("inf")
        soft = nxt[0] + DRIFT if nxt[1] == "line" else hard
        limit = min(hard, soft)
        if start + len(y) / SR > limit:
            need = (len(y) / SR) / max(limit - start, 0.1)
            if need > MAX_TEMPO:
                raise SystemExit(f"{cid}: {len(y) / SR:.1f}s does not fit in {limit - start:.1f}s even at {MAX_TEMPO}x; shorten it in en-edit.md")
            y = tempo(y, need)
            sped.append((cid, round(need, 3)))
        a = int(start * SR)
        audio[a:a + len(y)] += y
        prev_end = start + len(y) / SR
        slots[cid] = (start, prev_end)
        drifts.append((cid, round(start - zh_start, 2)))
    audio = audio[:int(total * SR)]
    peak = float(np.max(np.abs(audio)))
    if peak > 0.89:
        audio *= 0.89 / peak

    out = ROOT / "out/middle-income-trap"
    firsts = {}
    for _, kind, cid in seq:
        if kind == "line":
            firsts.setdefault("SC" + cid[2:4], cid)
    clips = [{"start": c["start"], "end": c["end"]} for c in tl["clips"]]
    music_mix(audio, slots | {c["id"]: (c["start"], c["end"]) for c in tl["clips"]}, firsts, clips, total, out, lang="en")
    m4a = out / "delivery/middle-income-trap.en.m4a"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(out / "mix.en.wav"), "-af", f"apad=whole_dur={total:.3f}",
                    "-t", f"{total:.3f}", "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-metadata:s:a:0", "language=eng",
                    "-movflags", "+faststart", str(m4a)], check=True)
    write_srt(tl, en, {cid: e for cid, (_, e) in slots.items()})

    late = [d for d in drifts if d[1] > 0.05]
    print(f"{len(slots)} lines, {len(clips)} clips, {total / 60:.1f} min; {len(late)} lines start late "
          f"(most {max([d[1] for d in late], default=0):.1f}s), {len(sped)} sped up")
    for cid, d in late:
        print(f"  late {cid} +{d}s")
    for cid, f in sped:
        print(f"  tempo {cid} x{f}")
    print(m4a)


if __name__ == "__main__":
    main()
