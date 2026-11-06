#!/usr/bin/env python3
"""Normalize the approved Lévy FLAC and run the shared accent/breath analysis.

Copied and adapted from scripts/gymnopedies/music.py. Uses only plain gain until
true peaks would exceed -1 dBTP; then applies the existing oversampled limiter.
Writes 48-kHz / 24-bit PCM WAV and the measured before/after report.
"""
import json, os, subprocess, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "debussy-impressions"))
from normalize import ebur128, render

DATA = os.environ.get("BLUE_WAVE_DATA", "/Users/yqin/repo/playground/lucas-academy-video-data/blue-wave")
DEBUSSY = "/Users/yqin/repo/playground/lucas-academy-video-data/debussy-impressions"   # accents.py / breath_curve.py read relative to it
TARGET, CEIL = -18.0, -1.0

PIECES = {"levy": {"src": "music/raw/levy-musopen.flac", "performer": "Lévy", "licence": "Musopen CC0 (owner-supplied)"}}

def main():
    os.makedirs(f"{DATA}/music/normalized", exist_ok=True); os.makedirs(f"{DATA}/music/analysis", exist_ok=True)
    py = sys.executable; here = os.path.dirname(os.path.abspath(__file__))
    report = {}
    for pid, p in PIECES.items():
        src, dst = f"{DATA}/{p['src']}", f"{DATA}/music/normalized/{pid}.wav"
        i, lra, peak = ebur128(src)
        gain = TARGET - i
        limit = CEIL - 0.3 if peak + gain > CEIL else None
        render(src, dst, gain, limit)
        i2, lra2, peak2 = ebur128(dst)
        for _ in range(3):
            if abs(i2 - TARGET) <= 0.2 and peak2 <= CEIL: break
            gain += TARGET - i2
            if peak2 > CEIL: limit = (limit if limit is not None else CEIL) - (peak2 - CEIL) - 0.1
            render(src, dst, gain, limit)
            i2, lra2, peak2 = ebur128(dst)
        report[pid] = {**p, "in_lufs": i, "lra": lra, "in_peak": peak, "gain_db": round(gain, 2), "limited": limit is not None,
                       "out_lufs": i2, "out_peak": peak2}
        rel = os.path.relpath(dst, DEBUSSY)
        subprocess.run([py, f"{here}/../debussy-impressions/accents.py", rel, f"{DATA}/music/analysis/{pid}.accents.json"], check=True)
        subprocess.run([py, f"{here}/../debussy-impressions/breath_curve.py", rel, f"{DATA}/music/analysis/{pid}.breath.json"], check=True)
        print(f"{pid}: {i:.1f} -> {i2:.1f} LUFS, peak {peak2:.1f}, gain {gain:+.1f} dB{' (limited)' if limit else ''}")
    json.dump(report, open(f"{DATA}/music/normalized/report.json", "w"), ensure_ascii=False, indent=1)

if __name__ == "__main__":
    main()
