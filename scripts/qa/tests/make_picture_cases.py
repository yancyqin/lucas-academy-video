"""Make the synthetic picture defects picture.py must catch (and the clean shots it must leave alone).

    .venv-align/bin/python scripts/qa/tests/make_picture_cases.py [--out out/qa/_picture_cases] [--a IMG] [--b IMG]

Every clip is 1920×1080 at 30 fps, rendered with sub-pixel affine sampling (a smooth Ken Burns push-in is the clean
base, never ffmpeg zoompan, which itself jitters). Each case gets <case>.mp4 and <case>.spec.json; the defects are
modelled on what Yancy caught: a Muse clip's wobbling first 8 frames, a wrong frame, a background swaying ±4 px with
a ~3 s period (faune 「画板一直晃」), a frozen stretch of real footage, black frames, and a hard cut that is fine.
"""
from __future__ import annotations

import argparse
import json
import math
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parents[3]
W, H, FPS = 1920, 1080, 30
ZY = Path("/Users/yqin/repo/playground/lucas-academy-video/.claude/worktrees/video-animals-children-footage-dc629f/public/zhong-ying")


def source(path: Path | None, seed: int) -> Image.Image:
    if path and path.exists():
        return Image.open(path).convert("RGB")
    rng = np.random.default_rng(seed)  # a textured stand-in when the pictures are not on this machine
    noise = (rng.random((540, 960, 3)) * 255).astype(np.uint8)
    return Image.fromarray(noise).filter(ImageFilter.GaussianBlur(3)).resize((1920, 1080))


def frame(img: Image.Image, zoom: float = 1.0, ox: float = 0.0, oy: float = 0.0, cx: float = 0.5, cy: float = 0.5) -> Image.Image:
    """Output pixel (x, y) shows source point centre + (x − W/2 − ox, y − H/2 − oy) / scale."""
    sw, sh = img.size
    s = max(W / sw, H / sh) * 1.12 * zoom          # 12 % margin so offsets never reveal an edge
    c0 = cx * sw - (W / 2 + ox) / s
    f0 = cy * sh - (H / 2 + oy) / s
    return img.transform((W, H), Image.AFFINE, (1 / s, 0, c0, 0, 1 / s, f0), resample=Image.BICUBIC)


def ease(x: float) -> float:
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def push(t: float, dur: float) -> float:
    """A painting's push-in: eases in and out (it may rest at the ends)."""
    return 1.0 + 0.06 * ease(t / dur)


def roll(t: float, dur: float) -> float:
    """Footage-like motion: a steady push that never comes to rest (real/Muse footage always moves)."""
    return 1.0 + 0.08 * t / dur


def write(path: Path, frames) -> None:
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "18", "-preset", "veryfast",
                          "-pix_fmt", "yuv420p", str(path)], stdin=subprocess.PIPE)
    for f in frames:
        p.stdin.write(np.asarray(f, np.uint8).tobytes())
    p.stdin.close()
    if p.wait():
        raise SystemExit(f"ffmpeg failed for {path}")


def cases(a: Image.Image, b: Image.Image):
    """(name, make frames, spec) — frames are only rendered for the cases asked for."""
    rng = np.random.default_rng(7)

    def clean(dur=8.0, img=a):
        return [frame(img, roll(i / FPS, dur)) for i in range(int(dur * FPS))]

    yield "clean", clean, {"shots": [{"id": "s1", "start": 0, "end": 8, "kind": "footage"}]}

    shake = rng.uniform(-11, 11, (8, 2)) * np.array([[1, 0.7]])
    shake[np.abs(shake) < 6] = np.sign(shake[np.abs(shake) < 6] + 1e-9) * 7   # ±6–11 px, never near zero

    def wobble():
        out = [frame(a, push(i / FPS, 3.0)) for i in range(3 * FPS)]
        for i in range(6 * FPS):
            ox, oy = shake[i] if i < 8 else (0.0, 0.0)
            out.append(frame(b, roll(i / FPS, 6.0), ox, oy))
        return out

    yield "start_wobble", wobble, {"shots": [{"id": "painting", "start": 0, "end": 3, "kind": "painting"},
                                             {"id": "muse", "start": 3, "end": 9, "kind": "footage"}]}

    def glitch():
        g = clean()
        g[120] = frame(b, 1.03)
        return g

    yield "glitch", glitch, {"shots": [{"id": "s1", "start": 0, "end": 8, "kind": "footage"}]}

    dur = 9.0
    yield "drift", lambda: [frame(a, roll(i / FPS, dur), 4 * math.sin(2 * math.pi * i / FPS / 3))
                            for i in range(int(dur * FPS))], \
        {"shots": [{"id": "s1", "start": 0, "end": 9, "kind": "footage"}]}

    def drift_region():
        box = frame(b, 1.0).crop((700, 200, 1260, 880))     # the "easel": fixed in place
        out = []
        for i in range(int(dur * FPS)):
            f = frame(a, 1.0, 4 * math.sin(2 * math.pi * i / FPS / 3))
            f.paste(box, (220, 200))
            out.append(f)
        return out

    yield "drift_region", drift_region, {"shots": [{"id": "easel", "start": 0, "end": 9, "kind": "painting",
                                                    "static": [[900, 120, 900, 820]]}]}

    def freeze():
        out = []
        for i in range(8 * FPS):
            t = i / FPS
            te = t if t < 3 else (3.0 if t < 4 else t - 1.0)
            out.append(frame(a, roll(te, 7.0)))
        return out

    yield "freeze", freeze, {"shots": [{"id": "muse", "start": 0, "end": 8, "kind": "footage"}]}

    def black():
        bl = clean()
        for k in (120, 121, 122):
            bl[k] = Image.new("RGB", (W, H))
        return bl

    yield "black", black, {"shots": [{"id": "s1", "start": 0, "end": 8, "kind": "footage"}]}

    yield "hard_cut", lambda: [frame(a, push(i / FPS, 4.0)) for i in range(4 * FPS)] + \
        [frame(b, push(i / FPS, 4.0)) for i in range(4 * FPS)], {}


REAL = ZY.parents[1] / "out/zhong-ying/moon-shines-on/moon-shines-on.mp4"   # a rendered film with MiniMax clips
REAL_AT, REAL_DUR = 161.5, 12.0                                              # inside its the-moon clip
REAL_CASES = ("real_clean", "real_wobble", "real_drift", "real_glitch", "real_freeze")


def real_cases(video: Path, at: float, dur: float, other: Image.Image, out: Path) -> None:
    """The same defects injected into real (MiniMax) footage, so texture and motion are real too."""
    enc = {}
    for name in REAL_CASES:
        enc[name] = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                                      "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "18", "-preset", "veryfast",
                                      "-pix_fmt", "yuv420p", str(out / f"{name}.mp4")], stdin=subprocess.PIPE)
    dec = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", f"{at}", "-t", f"{dur}", "-i", str(video), "-map", "0:v:0",
                            "-vf", f"scale={W}:{H}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    rng = np.random.default_rng(11)
    shake = rng.uniform(6, 11, (8, 2)) * rng.choice([-1, 1], (8, 2))
    wrong = frame(other, 1.0)
    hold = None
    i = 0
    while True:
        buf = dec.stdout.read(W * H * 3)
        if len(buf) < W * H * 3:
            break
        img = Image.frombuffer("RGB", (W, H), buf)
        base = frame(img, 1.0)
        out_frames = {
            "real_clean": base,
            "real_wobble": frame(img, 1.0, *shake[i]) if i < 8 else base,
            "real_drift": frame(img, 1.0, 4 * math.sin(2 * math.pi * i / FPS / 3)),
            "real_glitch": wrong if i == 180 else base,
            "real_freeze": (hold := base if i == 120 else hold) if 120 <= i < 150 else base,
        }
        for name, f in out_frames.items():
            enc[name].stdin.write(np.asarray(f, np.uint8).tobytes())
        i += 1
    dec.wait()
    for name, p in enc.items():
        p.stdin.close()
        p.wait()
        spec = {"film": f"case-{name}", "kind": "narrated", "lines": [],
                "shots": [{"id": "minimax", "start": 0, "end": round(i / FPS, 3), "kind": "footage"}]}
        (out / f"{name}.spec.json").write_text(json.dumps(spec, indent=1) + "\n")
        print(name, i, "frames", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "out/qa/_picture_cases"))
    ap.add_argument("--a", default=str(ZY / "who-woke-you/cover-chun-xiao.jpg"))
    ap.add_argument("--b", default=str(ZY / "who-keeps-waiting/cover-jiang-xue.jpg"))
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--real", default=str(REAL), help="a rendered film with real footage at --real-at (skipped if missing)")
    ap.add_argument("--real-at", type=float, default=REAL_AT)
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    a, b = source(Path(args.a), 1), source(Path(args.b), 2)
    for name, make, spec in cases(a, b):
        if args.only and name not in args.only:
            continue
        frames = make()
        write(out / f"{name}.mp4", frames)
        spec = {"film": f"case-{name}", "kind": "narrated", "lines": [], **spec}
        (out / f"{name}.spec.json").write_text(json.dumps(spec, indent=1) + "\n")
        print(name, len(frames), "frames", flush=True)
    if Path(args.real).exists() and (not args.only or set(args.only) & set(REAL_CASES)):
        real_cases(Path(args.real), args.real_at, REAL_DUR, b, out)


if __name__ == "__main__":
    main()
