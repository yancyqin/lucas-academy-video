"""Delivery checks for 「一根冰棍，要花多少钱？」: complete narration, captions, codec, black frames and loudness.

Checks the film's own captions and the other-language ones. Writes out/fun-economics-01/delivery-check.<lang>.json.
Run after render.py.
  python3 scripts/fun-economics-01/quality.py [--lang en]
"""
import hashlib
import json
import math
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PUB = ROOT / "public/fun-economics-01"
OUT = ROOT / "out/fun-economics-01"
DELIVERY = OUT / "delivery"
LANG = sys.argv[sys.argv.index("--lang") + 1] if "--lang" in sys.argv else "zh"
SRT_TAG = {"zh": "zh-Hans", "en": "en"}
FILM_NAME = "fun-economics-01"
LAST_CUE = "oc07-01"
FOOTAGE = ["hands.{lang}.mp4", "roads.{lang}.mp4", "homework.mp4"]  # placeholders stand in until these exist


def width(text: str) -> float:
    return sum(0.5 if ord(ch) < 0x2E80 else 1 for ch in text)


def main() -> None:
    tl = json.loads((PUB / f"timeline.{LANG}.json").read_text())
    if tl["draft"]:
        raise SystemExit("A draft timeline is not deliverable")
    cues = len(json.loads((PUB / f"narration/cues.{LANG}.json").read_text()))
    assert len(tl["cues"]) == cues and tl["cues"][-1]["id"] == LAST_CUE
    check = json.loads((OUT / f"narration-check.{LANG}.json").read_text())
    assert check["checked"] == check["expected"] == cues, "every take must be checked"
    film = DELIVERY / f"{FILM_NAME}.{LANG}.mp4"
    probe = json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(film)]))
    video = next(s for s in probe["streams"] if s["codec_type"] == "video")
    audio = next(s for s in probe["streams"] if s["codec_type"] == "audio")
    assert (video["width"], video["height"], video["r_frame_rate"], video["codec_name"]) == (1920, 1080, "30/1", "h264")
    expected = math.ceil(tl["durationSeconds"] * tl["fps"])
    assert int(video["nb_frames"]) == expected, (video["nb_frames"], expected)
    assert audio["codec_name"] == "aac" and audio["channels"] == 2
    duration = float(probe["format"]["duration"])
    assert abs(duration - tl["durationSeconds"]) < 0.15, (duration, tl["durationSeconds"])
    counts = {}
    for caption_lang in ("zh", "en"):
        blocks = (DELIVERY / f"{FILM_NAME}.{LANG}.{SRT_TAG[caption_lang]}.srt").read_text().strip().split("\n\n")
        previous = -1.0
        for number, block in enumerate(blocks, 1):
            lines = block.splitlines()
            assert int(lines[0]) == number
            times = re.findall(r"(\d+):(\d+):(\d+),(\d+)", lines[1])
            a, b = [int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000 for h, m, s, ms in times]
            assert 0 <= a < b <= tl["endCardStart"] and a >= previous - 0.002, (number, a, b)
            assert 1 <= len(lines[2:]) <= 2 and max(width(x) for x in lines[2:]) <= 22, (number, lines[2:])
            assert "<strong>" not in block and "Mary：" not in block and "Mary:" not in block
            assert (caption_lang == "zh") == bool(re.search(r"[一-鿿]", block)), (caption_lang, number, lines[2:])
            previous = b
        counts[caption_lang] = len(blocks)
    print(f"Codec, duration and caption blocks passed: {counts}", flush=True)
    stats = OUT / "blackframe-statistics.txt"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(film), "-an", "-vf", f"signalstats,metadata=print:file={stats}", "-f", "null", "-"], check=True)
    maxima = [float(line.split("=", 1)[1]) for line in stats.read_text().splitlines() if line.startswith("lavfi.signalstats.YMAX=")]
    assert len(maxima) == expected, (len(maxima), expected)
    black = sum(v <= 18 for v in maxima)
    assert black == 0, f"{black} black frames"
    print(f"Black-frame scan: {len(maxima)} frames, {black} black", flush=True)
    loud = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(film), "-vn", "-af", "ebur128=peak=sample+true:framelog=quiet", "-f", "null", "-"],
                          capture_output=True, text=True, check=True).stderr
    (OUT / "loudness.txt").write_text(loud)
    lufs = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", loud)[-1])
    peak = float(re.findall(r"Peak:\s+(-?[\d.]+) dBFS", loud)[-1])
    assert abs(lufs + 16) <= 0.5 and peak <= -1.5, (lufs, peak)
    placeholders = [name.format(lang=LANG) for name in FOOTAGE if name.format(lang=LANG) not in tl["footage"]]
    report = {"language": LANG, "voices": {"narrator": f"louise/{LANG}", "mary": "eunice/en (instruct, prompt D)"}, "cues": cues,
              "duration": duration, "resolution": [1920, 1080], "fps": 30, "captionBlocks": counts, "blackFrames": black,
              "scannedFrames": len(maxima), "integratedLUFS": lufs, "truePeakDBTP": peak, "missingFootage": placeholders,
              "narrationFlagged": check["flagged"], "sha256": hashlib.sha256(film.read_bytes()).hexdigest(), "bytes": film.stat().st_size}
    (OUT / f"delivery-check.{LANG}.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(f"Final film: {lufs} LUFS, {peak} dBTP" + (f"; placeholders still in: {', '.join(placeholders)}" if placeholders else "; passed"), flush=True)


if __name__ == "__main__":
    main()
