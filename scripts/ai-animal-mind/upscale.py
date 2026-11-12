"""Sharpen the film's stills for a 1080p render with Real-ESRGAN.

    /Users/yqin/repo/playground/lucas-academy-video/.venv-align/bin/python scripts/ai-animal-mind/upscale.py [--force]

The Codex first frames come out 1672x941 and the 1904 Clever Hans photo is 730x490, both short of 1080p before any slow
zoom (Yancy 2026-11-11: 「视频整个是高清的吗？」). Runs RealESRGAN_x4plus (tiled, on MPS) on
lucas-academy-video-data/ai-animal-mind/references/G*.png and stills/clever-hans-1904.jpg, then downsamples the 4x
result with lanczos to at most 3840 px wide (sharper than a direct 2x, room for the zoom). The 1904 photo is not run
through the model, which melts its small faces into oil-paint smears; it gets a 4x lanczos resize and a slight blur
that hides its JPEG blocks (sharpening makes them worse), so it stays a soft old photograph. Writes hd/<same name>;
assets.py takes a still from hd/ first. Existing files are kept unless --force. Yancy's own photos are no longer used
(11-11: 「不用我的照片了」).
"""
import sys
from pathlib import Path

import numpy as np
import torch
from PIL import Image, ImageFilter
from spandrel import ModelLoader

ROOT = Path(__file__).resolve().parents[2]
DATA = next(p / "lucas-academy-video-data" for p in ROOT.parents if (p / "lucas-academy-video-data").is_dir())
FILM = DATA / "ai-animal-mind"
DST = FILM / "hd"
SOURCES = sorted((FILM / "references").glob("G*.png")) + [FILM / "stills/clever-hans-1904.jpg"]
MODEL = next(p / "t2v/models/esrgan/RealESRGAN_x4plus.pth" for p in [ROOT, *ROOT.parents]
             if (p / "t2v/models/esrgan/RealESRGAN_x4plus.pth").is_file())
DEV = "mps" if torch.backends.mps.is_available() else "cpu"
TILE, OVERLAP, WIDTH = 256, 16, 3840
GENTLE = {"clever-hans-1904.jpg"}  # old photographs: resize + slight blur, no model

model = ModelLoader().load_from_file(str(MODEL)).eval().to(DEV)


def upscale(img: np.ndarray) -> np.ndarray:
    h, w, _ = img.shape
    out = np.zeros((h * 4, w * 4, 3), np.float32)
    with torch.no_grad():
        for y in range(0, h, TILE):
            for x in range(0, w, TILE):
                y0, x0 = max(0, y - OVERLAP), max(0, x - OVERLAP)
                y1, x1 = min(h, y + TILE + OVERLAP), min(w, x + TILE + OVERLAP)
                t = torch.from_numpy(img[y0:y1, x0:x1]).permute(2, 0, 1)[None].to(DEV)
                r = model(t)[0].permute(1, 2, 0).clamp(0, 1).cpu().numpy()
                ty, tx = (y - y0) * 4, (x - x0) * 4
                hh, ww = (min(h, y + TILE) - y) * 4, (min(w, x + TILE) - x) * 4
                out[y * 4:y * 4 + hh, x * 4:x * 4 + ww] = r[ty:ty + hh, tx:tx + ww]
    return out


DST.mkdir(parents=True, exist_ok=True)
for src in SOURCES:
    dst = DST / src.name
    if dst.is_file() and "--force" not in sys.argv:
        print("keep", dst.name)
        continue
    im = Image.open(src).convert("RGB")
    if im.width >= 1920 and im.height >= 1080:
        print("already HD", src.name)
        continue
    if src.name in GENTLE:
        big = im.resize((im.width * 4, im.height * 4), Image.LANCZOS).filter(ImageFilter.GaussianBlur(1.6))
    else:
        a = np.asarray(im, np.float32) / 255.0
        big = Image.fromarray((upscale(a) * 255).round().astype(np.uint8))
    if big.width > WIDTH:
        big = big.resize((WIDTH, round(big.height * WIDTH / big.width)), Image.LANCZOS)
    big.save(dst, quality=95) if dst.suffix == ".jpg" else big.save(dst)
    print(f"{src.name} {im.width}x{im.height} -> {big.width}x{big.height}", flush=True)
