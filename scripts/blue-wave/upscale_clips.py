#!/usr/bin/env python3
"""Real-ESRGAN x4 on the owner's Muse clips (640–1072 px, soft next to the 4K paintings; owner 11-03: 「yes you can
sharpen them」), every frame, then a Lanczos resize to OUT x the clip size. Runs before align_video.py.

Speed (M3 Pro, MPS, 768x1120 frame): fp32 256-px tiles 11 s, fp16 512-px tiles 8.4 s, fp16 on a 0.75x input 4.3 s —
the 0.75x input looked the same as the full one (lace and tree texture side by side), so 1680 frames take ~2 h, not ~7.
Muse already renders below its pixel size, so the 0.75x step loses little; x4 of it is 3x, about what the 16:9 crops need.

usage: .venv-align/bin/python scripts/gymnopedies/upscale_clips.py ID|CLIP.mp4 [...]   -> footage/muse/sharp/<id>.mp4
       (an ID is footage/muse/<id>.mp4; a path is any clip, e.g. the 印象派的秘密 clips gen-moulin / gen-opera)
"""
import json, os, pathlib, subprocess, sys, time
import numpy as np, torch
from PIL import Image
from spandrel import ModelLoader

DATA = os.environ.get("BLUE_WAVE_DATA", "/Users/yqin/repo/playground/lucas-academy-video-data/blue-wave")
MODEL = pathlib.Path(__file__).resolve().parents[2] / "t2v/models/esrgan/RealESRGAN_x4plus.pth"
if not MODEL.exists(): MODEL = pathlib.Path("/Users/yqin/repo/playground/lucas-academy-video/t2v/models/esrgan/RealESRGAN_x4plus.pth")
DEV = "mps" if torch.backends.mps.is_available() else "cpu"
DT = torch.float16 if DEV == "mps" else torch.float32
torch.set_num_threads(2)
if DEV == "mps": torch.mps.set_per_process_memory_fraction(0.42)
TILE, OVERLAP, IN_SCALE, OUT = 512, 16, 0.75, 3.0

model = ModelLoader().load_from_file(str(MODEL)).model.to(DT).eval().to(DEV)

def upscale(img):
    """Tiled x4 of a float32 HxWx3 image in [0, 1]."""
    h, w, _ = img.shape
    out = np.zeros((h * 4, w * 4, 3), np.float32)
    with torch.no_grad():
        for y in range(0, h, TILE):
            for x in range(0, w, TILE):
                y0, x0 = max(0, y - OVERLAP), max(0, x - OVERLAP)
                y1, x1 = min(h, y + TILE + OVERLAP), min(w, x + TILE + OVERLAP)
                t = torch.from_numpy(img[y0:y1, x0:x1]).permute(2, 0, 1)[None].to(DEV, DT)
                r = model(t)[0].permute(1, 2, 0).float().clamp(0, 1).cpu().numpy()
                ty, tx = (y - y0) * 4, (x - x0) * 4
                hh, ww = (min(h, y + TILE) - y) * 4, (min(w, x + TILE) - x) * 4
                out[y * 4:y * 4 + hh, x * 4:x * 4 + ww] = r[ty:ty + hh, tx:tx + ww]
    return out

def probe(clip):
    s = json.loads(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                                   "stream=width,height,r_frame_rate,nb_frames", "-of", "json", clip],
                                  capture_output=True, text=True, check=True).stdout)["streams"][0]
    return s["width"], s["height"], s["r_frame_rate"], int(s["nb_frames"])

def frames(clip, w, h):
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", clip, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    while True:
        b = p.stdout.read(w * h * 3)
        if len(b) < w * h * 3: break
        yield np.frombuffer(b, np.uint8).reshape(h, w, 3)
    p.wait()

for cid in sys.argv[1:]:
    clip = cid if cid.endswith(".mp4") else f"{DATA}/footage/muse/{cid}.mp4"; cid = os.path.basename(clip)[:-4]
    w, h, fps, n = probe(clip)
    sw, sh = round(w * IN_SCALE), round(h * IN_SCALE)
    ow, oh = round(w * OUT) & ~1, round(h * OUT) & ~1
    dst = f"{DATA}/footage/muse/sharp/{cid}.mp4"; os.makedirs(os.path.dirname(dst), exist_ok=True)
    marker = pathlib.Path(dst + ".done.json")
    if marker.exists() and os.path.exists(dst):
        if probe(dst)[3] == n:
            print(f"{cid}: verified {n} existing frames, skipping", flush=True)
            continue
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{ow}x{oh}", "-r", fps,
                            "-i", "-", "-c:v", "libx264", "-crf", "12", "-preset", "medium", "-pix_fmt", "yuv420p", dst + ".part.mp4"],
                           stdin=subprocess.PIPE)
    t0 = time.time(); k = 0
    for f in frames(clip, w, h):
        small = np.asarray(Image.fromarray(f).resize((sw, sh), Image.LANCZOS), np.float32) / 255.0
        big = Image.fromarray((upscale(small) * 255 + 0.5).astype(np.uint8)).resize((ow, oh), Image.LANCZOS)
        enc.stdin.write(np.asarray(big).tobytes()); k += 1
        if k % 24 == 0: print(f"  {cid} {k}/{n} {time.time() - t0:.0f}s", flush=True)
    enc.stdin.close()
    if enc.wait() != 0: raise RuntimeError(f"Encoder failed for {cid}")
    if k != n or probe(dst + ".part.mp4")[3] != n:
        raise RuntimeError(f"Frame mismatch for {cid}: {k}, expected {n}")
    os.replace(dst + ".part.mp4", dst)
    marker.write_text(json.dumps({"source": clip, "frames": k, "size": [ow, oh], "seconds": time.time()-t0}, indent=2))
    if DEV == "mps": torch.mps.empty_cache()
    print(f"{cid}: {k} frames {w}x{h} -> {ow}x{oh} in {time.time() - t0:.0f}s -> {dst}", flush=True)
