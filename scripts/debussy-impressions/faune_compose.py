"""faune_compose.py — put the painter's frames and the living page's frames on one primed canvas, add the music.

The picture sits centred on a 16:9 field of the same primed linen the painter starts from (~6 % margin), so the blank
state is one surface; a faint canvas weave lies over everything (ground, paint and living frames alike), which hides
the join between the Python-painted phase and the browser-rendered living phase. Arriving glints get a short twinkle.

    python faune_compose.py PAINT_DIR LIVE_DIR LIVE_START OUT.mp4 --wav W --music A B [--glints glints.json] [--fade S]
"""
import argparse, glob, json, math, os, subprocess
import numpy as np, cv2

GROUND = np.array([236, 228, 212], np.float32) / 255
FW, FH, FPS = 1920, 1080, 30

ap = argparse.ArgumentParser()
ap.add_argument("paint"); ap.add_argument("live"); ap.add_argument("live_start", type=float); ap.add_argument("out")
ap.add_argument("--wav", required=True); ap.add_argument("--music", nargs=2, type=float, required=True)
ap.add_argument("--glints"); ap.add_argument("--fade", type=float, default=3.0); ap.add_argument("--margin", type=float, default=0.06)
a = ap.parse_args()

paint = sorted(glob.glob(os.path.join(a.paint, "*.jpg"))); live = sorted(glob.glob(os.path.join(a.live, "*.jpg")))
first = cv2.imread(paint[0]); ph, pw = first.shape[:2]
s = min(FW * (1 - 2 * a.margin) / pw, FH * (1 - 2 * a.margin) / ph)
nw, nh = int(round(pw * s)), int(round(ph * s)); ox, oy = (FW - nw) // 2, (FH - nh) // 2

rng = np.random.default_rng(5)                                   # canvas weave: fine threads both ways, a little slub
wx = np.sin(np.arange(FW) * 2 * math.pi / 3.1)[None, :] * 0.5 + rng.normal(0, 0.35, (1, FW))
wy = np.sin(np.arange(FH) * 2 * math.pi / 3.3)[:, None] * 0.5 + rng.normal(0, 0.35, (FH, 1))
weave = (1 + 0.012 * (wx + wy) + 0.008 * cv2.GaussianBlur(rng.normal(0, 1, (FH, FW)).astype(np.float32), (0, 0), 1.2)).astype(np.float32)[..., None]

glints = json.load(open(a.glints)) if a.glints else []           # [{x, y (picture px), t}]
T = a.music[1] - a.music[0]; N = int(round(T * FPS))
cmd = ["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{FW}x{FH}", "-r", str(FPS), "-i", "-",
       "-ss", str(a.music[0]), "-t", str(T), "-i", a.wav,
       "-filter:a", f"afade=t=out:st={T - a.fade}:d={a.fade}", "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p",
       "-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart", "-shortest", a.out]
enc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
yy, xx = np.mgrid[-24:25, -24:25].astype(np.float32)
star = (np.exp(-(xx ** 2 + yy ** 2) / 40) + 0.55 * np.exp(-(yy ** 2) / 1.6 - np.abs(xx) / 7) + 0.55 * np.exp(-(xx ** 2) / 1.6 - np.abs(yy) / 7))
star = (star / star.max())[..., None]
for n in range(N):
    t = a.music[0] + n / FPS
    if t < a.live_start: src = paint[min(n, len(paint) - 1)]
    else: src = live[min(int(round((t - a.live_start) * FPS)), len(live) - 1)]
    pic = cv2.cvtColor(cv2.imread(src), cv2.COLOR_BGR2RGB)
    pic = cv2.resize(pic, (nw, nh), interpolation=cv2.INTER_AREA).astype(np.float32) / 255
    frame = np.empty((FH, FW, 3), np.float32); frame[:] = GROUND
    frame[oy:oy + nh, ox:ox + nw] = pic
    for g in glints:                                               # a glint arriving: a short soft twinkle
        age = t - g["t"]
        if 0 <= age < 0.7:
            k = math.sin(math.pi * age / 0.7) * 0.85
            cx, cy = int(ox + g["x"] * s), int(oy + g["y"] * s)
            y0, x0 = cy - 24, cx - 24
            if 0 <= y0 and y0 + 49 <= FH and 0 <= x0 and x0 + 49 <= FW:
                reg = frame[y0:y0 + 49, x0:x0 + 49]
                reg[:] = reg + (1 - reg) * star * k
    frame = np.clip(frame * weave, 0, 1)
    enc.stdin.write((frame * 255 + .5).astype(np.uint8).tobytes())
enc.stdin.close(); enc.wait()
print(a.out, N, "frames", f"picture {nw}x{nh} at {ox},{oy}")
