#!/usr/bin/env python
"""Decode a saved latent checkpoint into an mp4.

Denoising is the expensive half of a run and `generate.py` parks its result in
`<name>.latents.pt`. This turns that file into video without redoing any of it,
which also makes the decode itself cheap to experiment on.

  ./.venv/bin/python decode.py outputs/clip.latents.pt --device cpu
"""

import argparse
import os
import time

HERE = os.path.dirname(os.path.abspath(__file__))
os.environ.setdefault("HF_HOME", os.path.join(HERE, "models"))
os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")

import torch  # noqa: E402
from diffusers import AutoencoderKLWan  # noqa: E402
from diffusers.utils import export_to_video  # noqa: E402
from diffusers.video_processor import VideoProcessor  # noqa: E402

BASE_REPO = "Wan-AI/Wan2.1-T2V-1.3B-Diffusers"


def decode(latents_path, device="mps", fps=16, tile=None, out=None):
    vae = AutoencoderKLWan.from_pretrained(BASE_REPO, subfolder="vae", torch_dtype=torch.float32)
    vae.to(device).eval()
    if tile:
        vae.enable_tiling(tile_sample_min_height=tile, tile_sample_min_width=tile,
                          tile_sample_stride_height=tile * 3 // 4, tile_sample_stride_width=tile * 3 // 4)

    latents = torch.load(latents_path, map_location=device).to(vae.dtype)
    mean = torch.tensor(vae.config.latents_mean).view(1, vae.config.z_dim, 1, 1, 1).to(latents)
    std = torch.tensor(vae.config.latents_std).view(1, vae.config.z_dim, 1, 1, 1).to(latents)
    latents = latents * std + mean
    print(f"latents {tuple(latents.shape)} on {device}, tiling={'off' if not tile else tile}", flush=True)

    t = time.time()
    with torch.no_grad():
        video = vae.decode(latents, return_dict=False)[0]
    if device == "mps":
        torch.mps.synchronize()
        print(f"  driver allocated {torch.mps.driver_allocated_memory() / 2**30:.1f} GiB", flush=True)
    print(f"  decode {time.time() - t:.0f}s -> {tuple(video.shape)}", flush=True)

    frames = VideoProcessor(vae_scale_factor=8).postprocess_video(video, output_type="np")[0]
    out = out or latents_path.replace(".latents.pt", ".mp4")
    export_to_video(frames, out, fps=fps)
    print(f"{out}  ({len(frames)} frames)", flush=True)
    return out


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("latents")
    p.add_argument("--device", default="mps", choices=["mps", "cpu"])
    p.add_argument("--tile", type=int, default=None, help="tile size in pixels; omit for no tiling")
    p.add_argument("--fps", type=int, default=16)
    p.add_argument("--out", default=None)
    a = p.parse_args()
    decode(a.latents, device=a.device, fps=a.fps, tile=a.tile, out=a.out)
