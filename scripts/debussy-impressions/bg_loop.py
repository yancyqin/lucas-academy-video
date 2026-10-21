#!/usr/bin/env python3
"""bg_loop.py — a MiniMax background clip → the frame sequence a faune section plays behind the easel.

    python bg_loop.py ID RUNDIR [--slow 4] [--intro 0] [--until S] [--fade 3] [--freeze x0,y0,x1,y1|e:cx,cy,ax,ay|p:x,y,... ...] [--freeze-tone]
                     [--stabilize [TOP[:BOTTOM]]] [--curve t:speed,t:speed,... [--dense 10]] [--set]

The whole clip, slowed `slow`× with ffmpeg minterpolate, plays once; from `--intro` seconds (clip time) on, it
then loops with a `fade`-second end→start crossfade (Seine 10-17: the peach→violet start played once, the settled
part looped — 「peach-to-violet 挺好的…后面可以用 looping」). `--until` drops a bad clip end; `--freeze` holds a
box, oval or polygon (clip pixels, soft edge) at the first frame — figures that walk although the prompt said
不动, the Footbridge's willow that sways wrongly (owner 10-20) — `--freeze-tone` lets the held part follow the clip's
overall brightening. Writes DATA/faune/film/ID/bg-seq-mm with enough frames for the section, so scene_compose
never wraps; prints the frame step at every join next to a typical step; `--set` points the section's scene.json
background_loop at it.

`--stabilize` locks the camera to the first frame (similarity transform from ORB features in the row band
TOP:BOTTOM × height, so drifting clouds or water don't steer it). `--curve` replaces slow + loop with a speed curve
in section seconds, smoothstep between keys (Meadow 10-19: 「中间拉一下慢放曲线，速度降低很多近乎定格，再恢复到原速」); the clip is first
interpolated `dense`× so near-freeze speeds stay smooth, and holds its last frame if it runs out. The background is
only seen until the camera has pushed into the canvas (~15 s), so the curve has to happen inside that window.
"""
import argparse, glob, json, os, shutil, subprocess, sys
import cv2, numpy as np

FILM = "/Users/yqin/repo/playground/lucas-academy-video-data/debussy-impressions/faune/film"
FPS = 30


def step(a, b): return float(np.abs(cv2.imread(a).astype(np.float32) - cv2.imread(b).astype(np.float32)).mean())


def stabilize(src, dst, band):
    cap = cv2.VideoCapture(src); fps = cap.get(cv2.CAP_PROP_FPS); fr = []
    while True:
        ok, f = cap.read()
        if not ok: break
        fr.append(f)
    H, W = fr[0].shape[:2]; top, bot = (list(map(float, band.split(":"))) + [1.0])[:2]; y0, y1 = int(top * H), int(bot * H); orb = cv2.ORB_create(4000); bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    def feats(f): k, d = orb.detectAndCompute(cv2.cvtColor(f[y0:y1], cv2.COLOR_BGR2GRAY), None); return [(p.pt[0], p.pt[1] + y0) for p in k], d
    k0, d0 = feats(fr[0])
    enc = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(fps), "-i", "-",
                            "-c:v", "libx264", "-crf", "10", "-pix_fmt", "yuv420p", dst], stdin=subprocess.PIPE)
    worst = 0.0
    for f in fr:
        k1, d1 = feats(f); m = sorted(bf.match(d0, d1), key=lambda x: x.distance)[:1000]
        A, _ = cv2.estimateAffinePartial2D(np.float32([k1[x.trainIdx] for x in m]), np.float32([k0[x.queryIdx] for x in m]), method=cv2.RANSAC, ransacReprojThreshold=2)
        worst = max(worst, float(np.hypot(A[0, 2], A[1, 2])))
        enc.stdin.write(cv2.warpAffine(f, A, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT).tobytes())
    enc.stdin.close(); enc.wait()
    print(f"  stabilised: camera held to frame 0 (largest correction {worst:.1f} px)")


def curve_seq(fs, keys, dense, need, out):
    keys = sorted(keys)
    def speed(t):
        if t <= keys[0][0]: return keys[0][1]
        for (t0, s0), (t1, s1) in zip(keys, keys[1:]):
            if t <= t1: u = (t - t0) / (t1 - t0); return s0 + (s1 - s0) * u * u * (3 - 2 * u)
        return keys[-1][1]
    per = dense * FPS; c = 0.0; end = None
    for k in range(need):
        x = min(c * per, len(fs) - 1.0); i = int(x); w = x - i
        if x >= len(fs) - 1 and end is None: end = k / FPS
        if w < 0.02 or i + 1 >= len(fs): shutil.copyfile(fs[i], f"{out}/{k:04d}.jpg")
        else:
            img = cv2.imread(fs[i]).astype(np.float32) * (1 - w) + cv2.imread(fs[i + 1]).astype(np.float32) * w
            cv2.imwrite(f"{out}/{k:04d}.jpg", np.clip(img, 0, 255).astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 94])
        c += speed((k + 0.5) / FPS) / FPS
    print(f"  curve: clip {len(fs) / per:.2f} s; " + (f"runs out at {end:.1f} s (then holds)" if end else f"{c:.2f} s of it used by {need / FPS:.1f} s"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("id"); ap.add_argument("run")
    ap.add_argument("--slow", type=float, default=4.0); ap.add_argument("--intro", type=float, default=0.0)
    ap.add_argument("--until", type=float); ap.add_argument("--fade", type=float, default=3.0)
    ap.add_argument("--freeze", nargs="*", default=[]); ap.add_argument("--freeze-tone", action="store_true"); ap.add_argument("--set", action="store_true")
    ap.add_argument("--stabilize", nargs="?", const="0"); ap.add_argument("--curve"); ap.add_argument("--dense", type=float, default=10.0)
    a = ap.parse_args()
    scene = f"{FILM}/{a.id}/scene.json"; C = json.load(open(scene))
    need = int(round((C["range"][1] - C["range"][0]) * FPS)) + 5
    src = os.path.join(a.run, "original.mp4")
    if not os.path.exists(src): sys.exit(f"no {src}")
    out = f"{FILM}/{a.id}/bg-seq-mm"; raw = out + ".raw"; lp = out + ".loop"
    for d in (out, raw, lp):
        if os.path.isdir(d): shutil.rmtree(d)
        os.makedirs(d)
    if a.stabilize is not None:
        stab = out + ".stab.mp4"; stabilize(src, stab, a.stabilize); src = stab
    if a.curve: a.slow = a.dense
    vf = f"setpts={a.slow}*PTS,minterpolate=fps={FPS}:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1"
    cmd = ["ffmpeg", "-loglevel", "error", "-y"] + (["-t", str(a.until)] if a.until else []) + ["-i", src, "-vf", vf, "-q:v", "2", f"{raw}/%04d.jpg"]
    subprocess.run(cmd, check=True)
    fs = sorted(glob.glob(raw + "/*.jpg"))
    if a.freeze:                                                  # walking figures → back to their first-frame pose
        f0 = cv2.imread(fs[0]).astype(np.float32); m = np.zeros(f0.shape[:2], np.float32)
        for b in a.freeze:
            if b.startswith("e:"):                               # e:cx,cy,ax,ay — an oval round one figure
                cx, cy, ax, ay = map(int, b[2:].split(",")); cv2.ellipse(m, (cx, cy), (ax, ay), 0, 0, 360, 1.0, -1)
            elif b.startswith("p:"):                             # p:x,y,x,y,... — a polygon (trees behind a bridge)
                v = np.int32(list(map(int, b[2:].split(",")))).reshape(-1, 2); cv2.fillPoly(m, [v], 1.0)
            else:
                x0, y0, x1, y1 = map(int, b.split(",")); m[y0:y1, x0:x1] = 1
        hard = m > 0.5; m = cv2.GaussianBlur(m, (0, 0), 8)[..., None]; m0 = f0[hard].mean(0)
        for f in fs[1:]:
            cur = cv2.imread(f).astype(np.float32)
            held = f0 * (cur[hard].mean(0) / m0) if a.freeze_tone else f0   # the held part brightens with the clip
            img = cur * (1 - m) + held * m
            cv2.imwrite(f, np.clip(img, 0, 255).astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 95])
    if a.curve:
        curve_seq(fs, [tuple(map(float, k.split(":"))) for k in a.curve.split(",")], a.dense, need, out)
        shutil.rmtree(raw); shutil.rmtree(lp)
        if a.stabilize is not None: os.remove(src)
        print(f"{a.id}: {need} frames = {need / FPS:.1f} s on a speed curve")
        if a.set: C["background_loop"] = out; json.dump(C, open(scene, "w"), indent=1); print("  scene.json background_loop set")
        return
    I = int(round(a.intro * a.slow * FPS)); K = int(round(a.fade * FPS))
    body = fs[I:]; n = len(body)
    if n - K < 2 * K: sys.exit(f"loop part too short: {n} frames for a {K}-frame fade")
    for i in range(n - K):                                        # loop frame i; its first K frames melt in the end
        if i < K:
            w = (i + 0.5) / K; w = w * w * (3 - 2 * w)
            img = cv2.imread(body[n - K + i]).astype(np.float32) * (1 - w) + cv2.imread(body[i]).astype(np.float32) * w
            cv2.imwrite(f"{lp}/{i:04d}.jpg", np.clip(img, 0, 255).astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 94])
        else: shutil.copyfile(body[i], f"{lp}/{i:04d}.jpg")
    loop = sorted(glob.glob(lp + "/*.jpg"))
    seq = fs[:I] + body[:n - K]                                   # intro, then straight on: the first pass
    k = 0
    while len(seq) < need: seq.append(loop[k % len(loop)]); k += 1
    seq = seq[:max(need, I + n - K)]
    for j, f in enumerate(seq): shutil.copyfile(f, f"{out}/{j:04d}.jpg")
    shutil.rmtree(raw); shutil.rmtree(lp)
    if a.stabilize is not None: os.remove(src)
    S = sorted(glob.glob(out + "/*.jpg"))
    joins = {"intro→pass": I - 1} if I else {}
    joins["pass→loop"] = I + n - K - 1
    if len(S) > I + 2 * (n - K): joins["loop wrap"] = I + 2 * (n - K) - 1
    typ = np.median([step(S[j], S[j + 1]) for j in range(5, min(len(S) - 1, I + n - K - 5), 37)])
    print(f"{a.id}: {len(S)} frames = {len(S) / FPS:.1f} s (section needs {need}); intro {I}, loop {n - K} = {(n - K) / FPS:.1f} s")
    print("  typical step %.2f; " % typ + "; ".join(f"{k} {step(S[j], S[j + 1]):.2f}" for k, j in joins.items() if j + 1 < len(S)))
    if a.set:
        C["background_loop"] = out; json.dump(C, open(scene, "w"), indent=1); print("  scene.json background_loop set")


if __name__ == "__main__":
    main()
