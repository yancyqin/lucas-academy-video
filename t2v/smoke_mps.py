#!/usr/bin/env python
"""Check that the transformer and VAE actually run on Metal, before the 22 GB
text encoder finishes downloading.

Feeds the denoiser one dummy latent and one dummy text embedding, then decodes
through the VAE. Output is noise -- the point is that no kernel is missing.
"""

import os
import time

HERE = os.path.dirname(os.path.abspath(__file__))
os.environ.setdefault("HF_HOME", os.path.join(HERE, "models"))
os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")

import torch
from diffusers import AutoencoderKLWan, WanTransformer3DModel

REPO = "Wan-AI/Wan2.1-T2V-1.3B-Diffusers"
DEV = "mps"

print("torch", torch.__version__, "| mps available:", torch.backends.mps.is_available())

t = time.time()
tr = WanTransformer3DModel.from_pretrained(REPO, subfolder="transformer", torch_dtype=torch.bfloat16)
tr.to(DEV).eval()
print(f"transformer loaded in {time.time() - t:.0f}s "
      f"({sum(p.numel() for p in tr.parameters()) / 1e9:.2f}B params)")

# 480x832, 5 frames -> latents are 8x smaller in space, 4x in time (+1 anchor).
frames, h, w = 5, 480, 832
lat = torch.randn(1, 16, (frames - 1) // 4 + 1, h // 8, w // 8, dtype=torch.bfloat16, device=DEV)
emb = torch.randn(1, 226, 4096, dtype=torch.bfloat16, device=DEV)
ts = torch.tensor([1000.0], device=DEV)

t = time.time()
with torch.no_grad():
    out = tr(hidden_states=lat, timestep=ts, encoder_hidden_states=emb).sample
torch.mps.synchronize()
print(f"transformer forward OK  {tuple(out.shape)}  {time.time() - t:.1f}s (first call includes warmup)")

t = time.time()
with torch.no_grad():
    out = tr(hidden_states=lat, timestep=ts, encoder_hidden_states=emb).sample
torch.mps.synchronize()
print(f"transformer forward (warm) {time.time() - t:.2f}s")

vae = AutoencoderKLWan.from_pretrained(REPO, subfolder="vae", torch_dtype=torch.float32).to(DEV).eval()
vae.enable_tiling()
t = time.time()
with torch.no_grad():
    video = vae.decode(lat.float() / 1.0, return_dict=False)[0]
torch.mps.synchronize()
print(f"vae decode OK  {tuple(video.shape)}  {time.time() - t:.1f}s")
print(f"peak MPS memory: {torch.mps.driver_allocated_memory() / 2**30:.1f} GiB")
print("\nMPS PATH OK")
