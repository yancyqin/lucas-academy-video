#!/usr/bin/env python3
"""The whole film: Gymnopédies 1–3 rendered by walk.py from film/no1–3.json, joined with GAP s of black and silence.
Every part is encoded the same way (x264 yuv420p 30 fps, AAC 48 kHz stereo), so the join is a stream copy.

usage: .venv-reframe/bin/python scripts/gymnopedies/film.py [--draft] [--muse sharp|soft] [--skip-render]
       -> film/听得见的舞[-draft].mp4 and film/film.json (each piece's start, for the chapters)
"""
import argparse, json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import walk

GAP = 2.0
PARTS = ["no1", "no2", "no3"]

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--draft", action="store_true")
    ap.add_argument("--muse", choices=["sharp", "soft"], default="sharp"); ap.add_argument("--skip-render", action="store_true")
    a = ap.parse_args(); walk.MUSE = a.muse
    specs = [json.load(open(f"{HERE}/film/{p}.json")) for p in PARTS]
    out_dir = f"{walk.DATA}/film"; sfx = "-draft" if a.draft else ""
    if not a.skip_render:
        for s in specs: walk.render(s, a.draft)
    w, h = (walk.W // 2, walk.H // 2) if a.draft else (walk.W, walk.H)
    gap = f"{out_dir}/gap{sfx}.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"color=black:s={w}x{h}:r={walk.FPS}", "-f", "lavfi",
                    "-i", "anullsrc=r=48000:cl=stereo", "-t", str(GAP), "-c:v", "libx264", "-crf", "22" if a.draft else "16",
                    "-preset", "medium", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-ac", "2", gap], check=True)
    files, starts, t = [], [], 0.0
    for i, s in enumerate(specs):
        if i: files.append(gap); t += GAP
        starts.append(round(t, 2)); files.append(f"{out_dir}/{s['name']}{sfx}.mp4"); t += s["end"] - s["start"]
    lst = f"{out_dir}/concat{sfx}.txt"
    open(lst, "w").write("".join(f"file '{f}'\n" for f in files))
    final = f"{out_dir}/听得见的舞{sfx}.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", "-movflags", "+faststart", final], check=True)
    os.remove(lst); os.remove(gap)
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", final],
                               capture_output=True, text=True).stdout)
    json.dump({"starts": starts, "duration": round(dur, 2), "parts": PARTS, "gap": GAP}, open(f"{out_dir}/film.json", "w"), indent=1)
    print(f"-> {final}  {dur:.1f}s, pieces start at {starts}")

if __name__ == "__main__":
    main()
