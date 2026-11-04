#!/usr/bin/env python3
"""The three piano recordings for 听得见的舞 (owner 2026-11-02: piano only — No. 1 Baiocchi, Nos. 2–3 MacLeod).

Brings each to -18 LUFS with plain gain (a limiter only where the true peak would pass -1 dBTP, as in the Debussy
films), writes music/normalized/<id>.wav (48 kHz / 24-bit), then runs the Debussy accent and breath analysis on it
(music/analysis/<id>.accents.json, <id>.breath.json).

usage: .venv-reframe/bin/python scripts/gymnopedies/music.py
"""
import json, os, subprocess, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "debussy-impressions"))
from normalize import ebur128, render

DATA = "/Users/yqin/repo/playground/lucas-academy-video-data/satie-gymnopedies"
DEBUSSY = "/Users/yqin/repo/playground/lucas-academy-video-data/debussy-impressions"   # accents.py / breath_curve.py read relative to it
TARGET, CEIL = -18.0, -1.0

PIECES = {
    "gymnopedie-1": {"src": "music/src/gymnopedie-1-baiocchi.wav", "performer": "Daria Baiocchi", "licence": "CC0 1.0",
                     "page": "https://commons.wikimedia.org/wiki/File:Satie_Gymnop%C3%A8die_n.1_DariaBaiocchi.wav",
                     "licence_proof": "https://web.archive.org/web/20261025004947/https://imslp.org/wiki/3_Gymnop%C3%A9dies_(Satie,_Erik) (IMSLP #724979, Creative Commons Zero 1.0)"},
    "gymnopedie-2": {"src": "music/src/gymnopedie-2-macleod.mp3", "performer": "Kevin MacLeod (incompetech.com)", "licence": "CC BY 3.0",
                     "page": "https://commons.wikimedia.org/wiki/File:Gymnopedie_No._2_(ISRC_USUAN1100786).mp3"},
    "gymnopedie-3": {"src": "music/src/gymnopedie-3-macleod.mp3", "performer": "Kevin MacLeod (incompetech.com)", "licence": "CC BY 3.0",
                     "page": "https://commons.wikimedia.org/wiki/File:Gymnopedie_No._3_(ISRC_USUAN1100785).mp3"},
}

def main():
    os.makedirs(f"{DATA}/music/normalized", exist_ok=True); os.makedirs(f"{DATA}/music/analysis", exist_ok=True)
    py = sys.executable; here = os.path.dirname(os.path.abspath(__file__))
    report = {}
    for pid, p in PIECES.items():
        src, dst = f"{DATA}/{p['src']}", f"{DATA}/music/normalized/{pid}.wav"
        i, lra, peak = ebur128(src)
        gain = TARGET - i
        limit = CEIL if peak + gain > CEIL else None
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
