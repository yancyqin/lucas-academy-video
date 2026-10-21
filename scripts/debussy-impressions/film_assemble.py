"""film_assemble.py — join the 12 sections into the faune film: each finished living painting dissolves (2.5 s)
into the next plein-air scene, the dissolve ending on that section's first note; the whole recording runs under it.

    python film_assemble.py OUT.mp4 [--only id,id,...]
"""
import argparse, json, subprocess
FILM = "/Users/yqin/repo/playground/lucas-academy-video-data/debussy-impressions/faune/film"
WAV = "/Users/yqin/repo/playground/lucas-academy-video-data/debussy-impressions/music/normalized/faune-columbia-univ-orch-pd.wav"

ap = argparse.ArgumentParser(); ap.add_argument("out"); ap.add_argument("--only"); a = ap.parse_args()
plan = json.load(open(f"{FILM}/plan.json"))
if a.only: keep = a.only.split(","); plan = [s for s in plan if s["id"] in keep]
inputs, chain = [], []
for k, s in enumerate(plan):
    inputs += ["-i", f"{FILM}/{s['id']}/section.mp4"]
t_start = plan[0]["s0"] - plan[0]["pre"]
cur = "[0:v]"; dur = plan[0]["s1"] - t_start
for k in range(1, len(plan)):
    s = plan[k]; x = s["pre"]
    off = (s["s0"] - x) - t_start                                   # where this section's dissolve begins in the film
    tag = f"[v{k}]"
    chain.append(f"{cur}[{k}:v]xfade=transition=fade:duration={x}:offset={off:.3f}{tag}")
    cur = tag; dur = s["s1"] - t_start
T = dur
chain.append(f"{cur}fade=t=out:st={T - 2.0:.3f}:d=2.0,format=yuv420p[v]")
cmd = ["ffmpeg", "-loglevel", "error", "-y"] + inputs + ["-ss", str(t_start), "-t", f"{T:.3f}", "-i", WAV,
       "-filter_complex", ";".join(chain), "-map", "[v]", "-map", f"{len(plan)}:a",
       "-filter:a", f"afade=t=out:st={T - 3:.3f}:d=3", "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-r", "30",
       "-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart", "-shortest", a.out]
subprocess.run(cmd, check=True)
print(a.out, f"{T:.1f} s, {len(plan)} sections")
