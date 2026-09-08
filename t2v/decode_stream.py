#!/usr/bin/env python
"""Decode a latent checkpoint one latent frame at a time, offloading as it goes.

`decode.py` calls `vae.decode()`, and that path -- although it already walks the
clip one latent frame at a time -- keeps every decoded pixel frame on the GPU and
grows it with `torch.cat`. That accumulation, not the decode itself, is what puts
33 frames at 35.9 GiB and makes anything longer impossible on a 36 GB machine.

This reproduces the same loop (same weights, same conv cache, same order, so the
pixels are identical) but moves each decoded chunk to the CPU as uint8 the moment
it exists. Peak memory then stops depending on clip length, which is what lets a
five-second raw clip exist at all.

  ./.venv/bin/python decode_stream.py outputs/clip.latents.pt --fps 16
"""

import argparse
import os
import time

HERE = os.path.dirname(os.path.abspath(__file__))
os.environ.setdefault("HF_HOME", os.path.join(HERE, "models"))
os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")

import imageio  # noqa: E402
import numpy as np  # noqa: E402
import torch  # noqa: E402
from diffusers import AutoencoderKLWan  # noqa: E402

BASE_REPO = "Wan-AI/Wan2.1-T2V-1.3B-Diffusers"


def write_video(video: np.ndarray, out: str, fps: int) -> None:
    """Write uint8 RGB frames.

    NOT diffusers' export_to_video: given a numpy array it runs
    `(frame * 255).astype(np.uint8)` unconditionally, because it assumes float
    frames in [0, 1]. Handing it uint8 multiplies by 255 in uint8, and since
    255 = -1 (mod 256) every value v comes back as 256 - v -- a near-perfect
    inversion. It is a quiet failure: the clip plays, the motion is right, and the
    only symptom is that gold reads as blue and a bright sun reads as a black hole.
    """
    with imageio.get_writer(out, fps=fps, quality=8, macro_block_size=16) as w:
        for frame in video:
            w.append_data(frame)


def to_uint8(chunk: torch.Tensor) -> np.ndarray:
    """(1, C, f, H, W) in [-1, 1] on any device -> (f, H, W, C) uint8 on the host."""
    x = chunk.clamp(-1.0, 1.0).float().add(1.0).mul(127.5).round()
    x = x.squeeze(0).permute(1, 2, 3, 0)  # C,f,H,W -> f,H,W,C
    return x.to("cpu", torch.uint8).numpy()


def decode_stream(latents_path, device="mps", fps=16, out=None, vae=None, latents=None):
    if vae is None:
        vae = AutoencoderKLWan.from_pretrained(BASE_REPO, subfolder="vae", torch_dtype=torch.float32)
        vae.to(device).eval()

    if latents is None:
        latents = torch.load(latents_path, map_location="cpu")
    latents = latents.to(torch.float32)
    mean = torch.tensor(vae.config.latents_mean).view(1, vae.config.z_dim, 1, 1, 1)
    std = torch.tensor(vae.config.latents_std).view(1, vae.config.z_dim, 1, 1, 1)
    latents = latents * std + mean

    num_frame = latents.shape[2]
    print(f"latents {tuple(latents.shape)} -> {num_frame} latent frames on {device}", flush=True)

    frames, t0 = [], time.time()
    with torch.no_grad():
        vae.clear_cache()
        # post_quant_conv is a 1x1x1 conv, so it is safe to apply per frame; doing
        # it per frame keeps the whole normalised latent off the GPU.
        for i in range(num_frame):
            vae._conv_idx = [0]
            z_i = latents[:, :, i : i + 1].to(device)
            x_i = vae.post_quant_conv(z_i)
            out_i = vae.decoder(
                x_i, feat_cache=vae._feat_map, feat_idx=vae._conv_idx, first_chunk=(i == 0)
            )
            frames.append(to_uint8(out_i))
            del z_i, x_i, out_i
            if device == "mps":
                torch.mps.empty_cache()
            print(
                f"  latent frame {i + 1}/{num_frame} -> {frames[-1].shape[0]} px frames"
                f"  ({time.time() - t0:.0f}s"
                + (f", {torch.mps.driver_allocated_memory() / 2**30:.1f} GiB)" if device == "mps" else ")"),
                flush=True,
            )
        vae.clear_cache()

    video = np.concatenate(frames, axis=0)
    if device == "mps":
        print(f"  peak {torch.mps.driver_allocated_memory() / 2**30:.1f} GiB", flush=True)
    print(f"  decode {time.time() - t0:.0f}s -> {video.shape}", flush=True)

    out = out or (latents_path or "out").replace(".latents.pt", ".mp4")
    write_video(video, out, fps)
    print(f"{out}  ({len(video)} frames)", flush=True)
    return out


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("latents")
    p.add_argument("--device", default="mps", choices=["mps", "cpu"])
    p.add_argument("--fps", type=int, default=16)
    p.add_argument("--out", default=None)
    a = p.parse_args()
    decode_stream(a.latents, device=a.device, fps=a.fps, out=a.out)
