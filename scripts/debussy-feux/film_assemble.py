#!/usr/bin/env python3
"""Join the seven 焰火 sections (each overlaps the next by 1.5 s, laid at its absolute music time) with crossfades and
lay the Ligoratti recording under them. Writes feux/film/feux-film-<tag>.mp4 (1080p30) and a 720p review copy.

    python film_assemble.py v1
"""
import json, subprocess, sys

DATA = "/Users/yqin/repo/playground/lucas-academy-video-data/debussy-impressions"
FILM = f"{DATA}/feux/film"
MUSIC = f"{DATA}/music/normalized/feux-ligoratti-ccby3.wav"
ORDER = ["venice", "parliament", "montmartre", "rhone", "beijing", "rocket", "montorgueil"]

def main(tag):
    spans = []
    for s in ORDER:                                  # start from the plan, end from the file actually rendered
        t0 = json.load(open(f"{FILM}/{s}/plan.json"))["span"][0]
        n = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                  f"{FILM}/{s}/section.mp4"], capture_output=True, text=True, check=True).stdout)
        spans.append((t0, t0 + n - 0.034))
    assert abs(spans[0][0]) < 1e-6
    cmd = ["ffmpeg", "-v", "error", "-y"]
    for s in ORDER: cmd += ["-i", f"{FILM}/{s}/section.mp4"]
    cmd += ["-i", MUSIC]
    parts, last = [], "[0:v]"
    for i in range(1, len(ORDER)):
        start, prev_end = spans[i][0], spans[i - 1][1]
        d = round(prev_end - start, 3); assert d > 0, (ORDER[i], d)
        out = f"[x{i}]"
        parts.append(f"{last}[{i}:v]xfade=transition=fade:duration={d}:offset={start:.3f}{out}")
        last = out
    end = spans[-1][1]
    parts.append(f"[{len(ORDER)}:a]atrim=0:{end:.3f},afade=t=out:st={end - 2.5:.3f}:d=2.5[a]")
    out = f"{FILM}/feux-film-{tag}.mp4"
    cmd += ["-filter_complex", ";".join(parts), "-map", last, "-map", "[a]", "-c:v", "libx264", "-crf", "17", "-preset", "medium",
            "-pix_fmt", "yuv420p", "-r", "30", "-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart", out]
    subprocess.run(cmd, check=True)
    rev = f"{FILM}/feux-film-{tag}-review-720p.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", out, "-vf", "scale=1280:720", "-c:v", "libx264", "-crf", "22", "-preset", "medium",
                    "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", rev], check=True)
    print(out); print(rev)

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "v1")
