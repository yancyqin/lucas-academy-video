"""Real-ESRGAN 4x on the raw generated clips, before they are slowed down.

Order matters: the clips are 17 frames each, so upscaling first costs 221 frames
across the whole set. Upscaling after the 21x slowdown would be ~9000 frames, and
the upscaler would be working on blend-interpolated mush instead of real output.

4x then a lanczos downscale to 1080p supersamples, which is cleaner than 2x direct.
"""
import sys, pathlib, subprocess, time
import numpy as np, torch
from PIL import Image
from spandrel import ModelLoader

REPO = pathlib.Path(__file__).resolve().parents[2]
MODEL = REPO / 't2v/models/esrgan/RealESRGAN_x4plus.pth'
DEV = 'mps' if torch.backends.mps.is_available() else 'cpu'
TILE, OVERLAP = 256, 16

model = ModelLoader().load_from_file(str(MODEL)).eval().to(DEV)

def upscale(img: np.ndarray) -> np.ndarray:
    """Tiled 4x. Tiling keeps peak memory flat regardless of frame size."""
    h, w, _ = img.shape
    out = np.zeros((h*4, w*4, 3), np.float32)
    with torch.no_grad():
        for y in range(0, h, TILE):
            for x in range(0, w, TILE):
                y0, x0 = max(0, y-OVERLAP), max(0, x-OVERLAP)
                y1, x1 = min(h, y+TILE+OVERLAP), min(w, x+TILE+OVERLAP)
                t = torch.from_numpy(img[y0:y1, x0:x1]).permute(2,0,1)[None].to(DEV)
                r = model(t)[0].permute(1,2,0).clamp(0,1).cpu().numpy()
                # drop the overlap margin so tiles butt together without a seam
                ty, tx = (y-y0)*4, (x-x0)*4
                hh, ww = (min(h, y+TILE)-y)*4, (min(w, x+TILE)-x)*4
                out[y*4:y*4+hh, x*4:x*4+ww] = r[ty:ty+hh, tx:tx+ww]
    return out

for name in sys.argv[1:]:
    src = REPO / f't2v/outputs/{name}.mp4'
    work = REPO / f'tmp/upscale/{name}'
    work.mkdir(parents=True, exist_ok=True)
    subprocess.run(['ffmpeg','-v','error','-i',str(src),str(work/'in_%03d.png')], check=True)
    frames = sorted(work.glob('in_*.png'))
    t0 = time.time()
    for i, f in enumerate(frames):
        a = np.asarray(Image.open(f).convert('RGB'), np.float32)/255.0
        Image.fromarray((upscale(a)*255).round().astype(np.uint8)).save(work/f'up_{i+1:03d}.png')
    dst = REPO / f'tmp/upscale/{name}-4x.mp4'
    subprocess.run(['ffmpeg','-v','error','-framerate','16','-i',str(work/'up_%03d.png'),
                    '-vf','scale=1920:1080:flags=lanczos','-c:v','libx264','-crf','14',
                    '-pix_fmt','yuv420p','-y',str(dst)], check=True)
    print(f'{name}: {len(frames)} frames in {time.time()-t0:.0f}s -> {dst.name}', flush=True)
