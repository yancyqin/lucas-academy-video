#!/usr/bin/env python3
"""Round 5 (Yancy 2026-11-11: "Soften and retest"): match each AI picture to its real partner.

  soften.py      ai/raw/tNN.png -> ai/uNN.png, log in ai/soften.json

Round 4 (macro, vivid) lost 8/10 and 9/10 because the AI pictures were crisper and more saturated than the real frames
next to them (median sharpness 134 vs 98, saturation 175 vs 139), which is exactly what both models said. Round 5
keeps round 4's pictures and pairing and only takes that away, per pair:
  - saturation: scale the HSV saturation down to the real partner's mean (never up);
  - sharpness: Gaussian blur, smallest radius whose result is no sharper than the real partner (never sharpen);
  - then the same medium as before: 1920x1080 H.264 at ~5 Mbps, frame back out.
Both are measured the way the models see the pictures: cut to 16:9, 1600x900 (blind_test.norm).
Partners come from round 4's pairs/answers.json (kept in _retired/round4-macro-2026-11-11/ once round 5 runs).
"""
import json, os, subprocess, sys, tempfile

import numpy as np
from PIL import Image, ImageFilter

sys.path.insert(0, os.path.dirname(__file__))
import blind_test as bt  # noqa: E402

DATA = bt.DATA
RADII = [0, 0.4, 0.7, 1.0, 1.3, 1.6, 2.0, 2.5, 3.0, 3.6, 4.3, 5.0]


def sharp(img):
    a = np.asarray(img.convert("L"), dtype=np.float32)
    lap = a[1:-1, 1:-1] * 4 - a[:-2, 1:-1] - a[2:, 1:-1] - a[1:-1, :-2] - a[1:-1, 2:]
    return float(lap.var())


def sat(img):
    return float(np.asarray(img.convert("HSV"), dtype=np.float32)[..., 1].mean())


def scale_sat(img, f):
    if f >= 1:
        return img
    h, s, v = img.convert("HSV").split()
    s = s.point(lambda x: int(round(x * f)))
    return Image.merge("HSV", (h, s, v)).convert("RGB")


def through_video(img, tmp):
    """Same medium as the real frames: 1920x1080 H.264 ~5 Mbps, frame back out (as codex_realistic.video)."""
    src, mp4, out = f"{tmp}/in.png", f"{tmp}/v.mp4", f"{tmp}/out.png"
    img.save(src)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-i", src, "-t", "1", "-r", "30",
                    "-vf", "format=yuv420p", "-c:v", "libx264", "-preset", "medium",
                    "-b:v", "5M", "-maxrate", "5M", "-bufsize", "10M", "-g", "30", mp4], check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "0.5", "-i", mp4, "-frames:v", "1", out], check=True)
    return Image.open(out).convert("RGB")


def seen(img, tmp):
    """What the models see: blind_test.norm (16:9 crop, 1600x900, JPEG q90)."""
    a, b = f"{tmp}/seen-in.png", f"{tmp}/seen.jpg"
    img.save(a); bt.norm(a, b)
    return Image.open(b).convert("RGB")


def main():
    answers = json.load(open(sys.argv[1] if len(sys.argv) > 1 else f"{DATA}/pairs/answers.json"))
    pairs_dir = os.path.dirname(sys.argv[1]) if len(sys.argv) > 1 else f"{DATA}/pairs"
    log = []
    for a in answers:
        t = a["ai"]; u = "u" + t[1:]
        real = Image.open(f"{pairs_dir}/{a['n']:02d}-{a['real']}.jpg").convert("RGB")
        fake_side = "B" if a["real"] == "A" else "A"
        before = Image.open(f"{pairs_dir}/{a['n']:02d}-{fake_side}.jpg").convert("RGB")
        target_sharp, target_sat = sharp(real), sat(real)
        f = min(1.0, target_sat / sat(before))
        base = Image.open(f"{DATA}/ai/raw/{t}.png").convert("RGB").resize((1920, 1080), Image.BICUBIC)
        base = scale_sat(base, f)
        with tempfile.TemporaryDirectory() as tmp:
            for r in RADII:
                cand = base.filter(ImageFilter.GaussianBlur(r)) if r else base
                frame = through_video(cand, tmp)
                s = seen(frame, tmp)
                if sharp(s) <= target_sharp or r == RADII[-1]:
                    break
            frame.save(f"{DATA}/ai/{u}.png")
        row = dict(n=a["n"], real=a["key"], ai=t, out=u, blur_radius=r, sat_factor=round(f, 3),
                   real_sharp=round(target_sharp), ai_sharp_before=round(sharp(before)), ai_sharp_after=round(sharp(s)),
                   real_sat=round(target_sat), ai_sat_before=round(sat(before)), ai_sat_after=round(sat(s)))
        log.append(row)
        print(row, flush=True)
    json.dump(log, open(f"{DATA}/ai/soften.json", "w"), indent=1)


if __name__ == "__main__":
    main()
