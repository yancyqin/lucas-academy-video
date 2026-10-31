"""English audio track for 「你爱听 AI 说「是的」吗？」: Yancy's English takes laid on the finished film's timeline.

  /Users/yqin/repo/playground/lucas-academy-video/.venv-align/bin/python scripts/ai-sycophancy/build_en_track.py [--srt-only]

The same way as 「跨越中等收入陷阱」 (scripts/middle-income-trap/build_en_track.py; Yancy, 2026-10-31: 英文配音也可以做了).
The picture and the Chinese track are finished (build_timeline.py), so nothing on them moves. Every English line
(narrate_en.py) starts when its Chinese line starts, or GAP after the English line before it if that one ran long.
A take that would run DRIFT past the next Chinese line, or into the end card, is sped up (at most MAX_TEMPO); if that
is not enough the build stops and names the line to shorten in en-edit.md. Takes are trimmed, faded and levelled like
the Chinese ones; the music beds, their ducking and the final loudness are the Chinese mix's.

Writes out/ai-sycophancy/mix.en.wav, delivery/ai-sycophancy.en.m4a (exactly the film's length, the extra audio track
YouTube takes) and delivery/ai-sycophancy.en.srt (each English line on its Chinese line's span, longer if the English
runs past it, so one English caption file serves both audio tracks).
"""
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]


def module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


mit = module("mit_timeline", ROOT / "scripts/middle-income-trap/build_timeline.py")
mit_en = module("mit_en_track", ROOT / "scripts/middle-income-trap/build_en_track.py")
ours = module("as_timeline", ROOT / "scripts/ai-sycophancy/build_timeline.py")

TAKES = mit.MEDIA / "outputs/yancy/en/ai-sycophancy-v1"
SR = mit.SR
GAP, DRIFT, MAX_TEMPO = 0.3, 3.0, 1.15
LINE = re.compile(r"^- (sc\d\d-\d\d) \| (.+)$")
OUT = ROOT / "out/ai-sycophancy"


def write_srt(tl: dict, en: dict, spoken_end: dict) -> Path:
    cues = sorted((v["start"], max(v["end"], spoken_end.get(cid, 0.0)), en[cid]) for cid, v in tl["lines"].items())
    srt, n = [], 0
    for k, (start, end, text) in enumerate(cues):
        if k + 1 < len(cues):
            end = min(end, cues[k + 1][0] - 0.04)  # never over the next caption
        for a, b, p in mit_en.pieces(text, start, end):
            n += 1
            srt.append(f"{n}\n{mit.stamp(a)} --> {mit.stamp(b)}\n{p}\n")
    path = OUT / "delivery/ai-sycophancy.en.srt"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(srt))
    print(f"{path.name}: {n} captions")
    return path


def main():
    tl = json.loads((ROOT / "public/ai-sycophancy/timeline.json").read_text())
    total = tl["durationSeconds"]
    en = {m[1]: m[2].strip() for raw in (ROOT / "docs/ai-sycophancy/en-edit.md").read_text().splitlines() if (m := LINE.match(raw))}
    if "--srt-only" in sys.argv:
        write_srt(tl, en, {})
        return
    seq = sorted((v["start"], k) for k, v in tl["lines"].items())
    end_card = max(v["end"] for v in tl["lines"].values()) + ours.END_CARD
    audio = np.zeros(int(total * SR) + SR, np.float32)
    slots, drifts, sped, prev_end = {}, [], [], 0.0
    for i, (zh_start, cid) in enumerate(seq):
        wav = TAKES / f"{cid}.wav"
        if not wav.exists():
            raise SystemExit(f"missing take {wav}")
        y = mit.decode(wav, trim=True)
        start = max(zh_start, prev_end + GAP)
        limit = seq[i + 1][0] + DRIFT if i + 1 < len(seq) else end_card + 3.0
        if start + len(y) / SR > limit:
            need = (len(y) / SR) / max(limit - start, 0.1)
            if need > MAX_TEMPO:
                raise SystemExit(f"{cid}: {len(y) / SR:.1f}s does not fit in {limit - start:.1f}s even at {MAX_TEMPO}x; shorten it in en-edit.md")
            y = mit_en.tempo(y, need)
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

    mit.DATA = ours.DATA / "ai-sycophancy"
    mit.BEDS = ours.BEDS
    mit.music_mix(audio, slots, {cid: cid for cid, _ in ours.BEDS}, [], total, OUT, lang="en")
    m4a = OUT / "delivery/ai-sycophancy.en.m4a"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(OUT / "mix.en.wav"), "-af", f"apad=whole_dur={total:.3f}",
                    "-t", f"{total:.3f}", "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-metadata:s:a:0", "language=eng",
                    "-movflags", "+faststart", str(m4a)], check=True)
    write_srt(tl, en, {cid: e for cid, (_, e) in slots.items()})

    late = [d for d in drifts if d[1] > 0.05]
    print(f"{len(slots)} lines, {total / 60:.1f} min; {len(late)} lines start late "
          f"(most {max([d[1] for d in late], default=0):.1f}s), {len(sped)} sped up")
    for cid, d in late:
        print(f"  late {cid} +{d}s")
    for cid, f in sped:
        print(f"  tempo {cid} x{f}")
    print(m4a)


if __name__ == "__main__":
    main()
