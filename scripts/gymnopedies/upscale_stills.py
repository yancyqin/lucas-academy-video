#!/usr/bin/env python3
"""Real-ESRGAN x4 on the Codex reconstructions (they come out ~900x1750), then a Lanczos downscale to LONG px on the
long side — supersampled, cleaner than a direct 2x. The 4K stills are what Muse gets as first frames and what the
film dissolves from. Same model and tiling as scripts/upscale/esrgan.py.

usage: .venv-align/bin/python scripts/gymnopedies/upscale_stills.py IMG.png [...]   -> <name>-4k.png next to each
"""
import os, pathlib, sys
import numpy as np, torch
from PIL import Image
from spandrel import ModelLoader

REPO = pathlib.Path(__file__).resolve().parents[2]
MODEL = REPO / "t2v/models/esrgan/RealESRGAN_x4plus.pth"
if not MODEL.exists(): MODEL = pathlib.Path("/Users/yqin/repo/playground/lucas-academy-video/t2v/models/esrgan/RealESRGAN_x4plus.pth")
DEV = "mps" if torch.backends.mps.is_available() else "cpu"
TILE, OVERLAP, LONG = 256, 16, 3840

model = ModelLoader().load_from_file(str(MODEL)).eval().to(DEV)

def upscale(img):
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

for arg in sys.argv[1:]:
    im = Image.open(arg).convert("RGB")
    big = upscale(np.asarray(im, np.float32) / 255.0)
    out = Image.fromarray((big * 255 + 0.5).astype(np.uint8))
    k = LONG / max(out.size)
    if k < 1: out = out.resize((round(out.width * k), round(out.height * k)), Image.LANCZOS)
    dst = os.path.splitext(arg)[0] + "-4k.png"
    out.save(dst)
    print(f"{os.path.basename(arg)} {im.size} -> {out.size} {dst}")
