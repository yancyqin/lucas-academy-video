#!/usr/bin/env python3
"""Widen a portrait painting to 16:9 for the film (owner 11-05: 「旅人基于原画扩充为横屏」): Codex paints only the sides, in
the painter's own style; the middle stays the real scan.

  extend_painting.py canvas ID     art/<ID>.jpg centred at full height on a 2048×1152 grey canvas -> codex/refs/<ID>-canvas.png
                                   (Codex's layout reference; `codex_real.py <tag> <ID>-16x9` then paints codex/real-<ID>-16x9.png)
  extend_painting.py compose ID    finds the painting inside Codex's picture (template match over scales), lifts Codex's picture
                                   to 3840×2160, matches its colour to the scan around the painting, and puts the 4K scan back in
                                   with a feathered seam -> codex/extended-<ID>.png, plus codex/extended-<ID>-seams.jpg to check
"""
import os, sys
import cv2
import numpy as np
from PIL import Image

DATA = os.environ.get("BLUE_WAVE_DATA", "/Users/yqin/repo/playground/lucas-academy-video-data/blue-wave")
W, H = 3840, 2160
GREY = (128, 128, 128)
FEATHER = 0.04          # seam width, as a fraction of the painting's width on each side

def canvas(pid):
    art = Image.open(f"{DATA}/art/{pid}.jpg").convert("RGB")
    cw, ch = 2048, 1152
    pw = round(ch * art.width / art.height)
    c = Image.new("RGB", (cw, ch), GREY)
    c.paste(art.resize((pw, ch), Image.LANCZOS), ((cw - pw) // 2, 0))
    dst = f"{DATA}/codex/refs/{pid}-canvas.png"; c.save(dst)
    print(dst, (cw, ch), "painting", pw, "px wide at", (cw - pw) // 2)

def locate(gen, art):
    """Best (x, y, w, h) of the painting inside Codex's picture, both as grey arrays."""
    g = cv2.cvtColor(gen, cv2.COLOR_RGB2GRAY).astype(np.float32)
    best = (-2, None)
    for s in np.linspace(0.80, 1.0, 41):                       # painting height as a fraction of the picture's
        th = int(round(g.shape[0] * s)); tw = int(round(th * art.shape[1] / art.shape[0]))
        if tw >= g.shape[1] or th > g.shape[0]: continue
        t = cv2.cvtColor(cv2.resize(art, (tw, th), interpolation=cv2.INTER_AREA), cv2.COLOR_RGB2GRAY).astype(np.float32)
        r = cv2.matchTemplate(g, t, cv2.TM_CCOEFF_NORMED); _, v, _, (x, y) = cv2.minMaxLoc(r)
        if v > best[0]: best = (v, (x, y, tw, th))
    return best

def compose(pid):
    gen = np.asarray(Image.open(f"{DATA}/codex/real-{pid}-16x9.png").convert("RGB"))
    art_img = Image.open(f"{DATA}/art/{pid}.jpg").convert("RGB")
    score, (x, y, w, h) = locate(gen, np.asarray(art_img))
    print(f"Codex picture {gen.shape[1]}×{gen.shape[0]}, painting found at x={x} y={y} {w}×{h}, NCC {score:.3f}")
    # crop Codex's picture to 16:9 around the painting (it should already be 16:9), then lift it to 3840×2160
    gh, gw = gen.shape[:2]
    cw = min(gw, round(gh * 16 / 9)); ch = round(cw * 9 / 16)
    cx = int(np.clip(x + w / 2 - cw / 2, 0, gw - cw)); cy = int(np.clip(y + h / 2 - ch / 2, 0, gh - ch))
    k = W / cw
    base = cv2.resize(gen[cy:cy + ch, cx:cx + cw], (W, H), interpolation=cv2.INTER_LANCZOS4).astype(np.float32)
    px, py, pw, ph = round((x - cx) * k), round((y - cy) * k), round(w * k), round(h * k)
    art = np.asarray(art_img.resize((pw, ph), Image.LANCZOS), dtype=np.float32)
    # clip the painting to the frame (it may touch or pass an edge by a pixel or two)
    x0, y0, x1, y1 = max(px, 0), max(py, 0), min(px + pw, W), min(py + ph, H)
    art = art[y0 - py:y1 - py, x0 - px:x1 - px]
    # colour: Codex's re-painted middle vs the scan, per channel (mean and spread) — applied to the whole Codex picture
    ref = base[y0:y1, x0:x1]
    mu_g, sd_g = ref.reshape(-1, 3).mean(0), ref.reshape(-1, 3).std(0) + 1e-3
    mu_a, sd_a = art.reshape(-1, 3).mean(0), art.reshape(-1, 3).std(0) + 1e-3
    base = (base - mu_g) / sd_g * sd_a + mu_a
    # feathered paste: full scan inside, fading into Codex's sides over FEATHER of the painting width at left and right
    f = max(8, round((x1 - x0) * FEATHER))
    ramp = np.ones(x1 - x0, np.float32)
    ramp[:f] = np.linspace(0, 1, f); ramp[-f:] = np.linspace(1, 0, f)
    a = ramp[None, :, None]
    out = base.copy()
    out[y0:y1, x0:x1] = a * art + (1 - a) * base[y0:y1, x0:x1]
    out = Image.fromarray(np.clip(out + 0.5, 0, 255).astype(np.uint8))
    dst = f"{DATA}/codex/extended-{pid}.png"; out.save(dst)
    # seam check: the two seams at full resolution, side by side
    sx = [x0, x1 - 1]; band = 360
    crops = [out.crop((max(0, s - band), H // 2 - band, min(W, s + band), H // 2 + band)) for s in sx]
    sheet = Image.new("RGB", (sum(c.width for c in crops) + 20, 2 * band), (255, 255, 255))
    sheet.paste(crops[0], (0, 0)); sheet.paste(crops[1], (crops[0].width + 20, 0))
    sheet.save(f"{DATA}/codex/extended-{pid}-seams.jpg", quality=88)
    print(dst, out.size, f"painting at x={x0}..{x1} y={y0}..{y1}, seam {f} px")

if __name__ == "__main__":
    {"canvas": canvas, "compose": compose}[sys.argv[1]](sys.argv[2])
