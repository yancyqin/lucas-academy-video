#!/usr/bin/env python3
"""Bring every candidate recording to the same loudness so pieces don't jump in volume.

Plain gain to TARGET LUFS (integrated) keeps each piece's own dynamics. Only where that gain would push the
true peak above CEIL dBTP does a look-ahead limiter (run at 192 kHz so it also catches inter-sample peaks)
shave the loudest transients. Output: 48 kHz / 24-bit WAV in music/normalized/, 192 kbps MP3 listening copies
in preview/audio/, and music/normalized/report.json with the gain and limiting applied to each file.

usage: python3 normalize.py [--target -18] [--ceil -1]
"""
import argparse, json, os, re, subprocess

DATA = "/Users/yqin/repo/playground/lucas-academy-video-data/debussy-impressions"

def ebur128(path):
    err = subprocess.run(["ffmpeg", "-nostats", "-hide_banner", "-i", path, "-vn", "-af", "ebur128=peak=true", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    tail = err[err.rfind("Summary:"):]
    g = lambda pat: float(re.search(pat, tail).group(1))
    return g(r"I:\s+(-?[\d.]+) LUFS"), g(r"LRA:\s+([\d.]+) LU"), g(r"Peak:\s+(-?[\d.]+) dBFS")

def render(src, dst, gain, limit_db):
    chain = [f"volume={gain:.2f}dB"]
    if limit_db is not None:
        lin = 10 ** (limit_db / 20)
        chain = ["aresample=192000"] + chain + [f"alimiter=limit={lin:.4f}:attack=5:release=120:asc=1:level=0:latency=1", "aresample=48000:filter_size=64:cutoff=0.97"]
    else:
        chain = ["aresample=48000:filter_size=64:cutoff=0.97"] + chain
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-vn", "-ac", "2", "-af", ",".join(chain), "-c:a", "pcm_s24le", dst], check=True)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--target", type=float, default=-18.0); ap.add_argument("--ceil", type=float, default=-1.0)
    a = ap.parse_args()
    sources = json.load(open(f"{DATA}/music/sources.json"))
    os.makedirs(f"{DATA}/music/normalized", exist_ok=True); os.makedirs(f"{DATA}/preview/audio", exist_ok=True)
    report = []
    for s in sources:
        if not s.get("file"): continue
        src = f"{DATA}/music/{s['file']}"; base = os.path.basename(s["file"]).rsplit(".", 1)[0]
        dst = f"{DATA}/music/normalized/{base}.wav"
        I, LRA, TP = ebur128(src)
        gain = a.target - I
        over = TP + gain - a.ceil
        limit = (a.ceil - 0.3) if over > 0 else None          # limiter a little under the ceiling; resampling adds a few tenths
        for _ in range(3):
            render(src, dst, gain, limit)
            I2, LRA2, TP2 = ebur128(dst)
            if abs(I2 - a.target) <= 0.2 and TP2 <= a.ceil + 0.05: break
            gain += a.target - I2                               # limiting lowered the loudness a little: make it up
            if TP2 > a.ceil + 0.05: limit = (limit if limit is not None else a.ceil) - (TP2 - a.ceil) - 0.1
        mp3 = f"{DATA}/preview/audio/{base}.mp3"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", dst, "-c:a", "libmp3lame", "-b:a", "192k", mp3], check=True)
        I3, _, TP3 = ebur128(mp3)
        r = {"key": s["key"], "source": s["file"], "out": f"normalized/{base}.wav", "listen": f"preview/audio/{base}.mp3",
             "in_LUFS": I, "in_LRA": LRA, "in_TP": TP, "gain_dB": round(gain, 2),
             "peak_shaved_dB": round(max(0.0, TP + gain - a.ceil), 1), "out_LUFS": I2, "out_LRA": LRA2, "out_TP": TP2, "mp3_LUFS": I3, "mp3_TP": TP3}
        report.append(r)
        print(f"{s['key']:16s} in {I:6.1f} LUFS TP {TP:5.1f} | gain {gain:+6.2f} dB | shaved {r['peak_shaved_dB']:4.1f} dB | out {I2:6.1f} LUFS LRA {LRA2:4.1f} TP {TP2:5.1f} | mp3 {I3:6.1f}/{TP3:5.1f}")
    json.dump({"target_LUFS": a.target, "ceiling_dBTP": a.ceil, "files": report}, open(f"{DATA}/music/normalized/report.json", "w"), indent=1)

if __name__ == "__main__":
    main()
