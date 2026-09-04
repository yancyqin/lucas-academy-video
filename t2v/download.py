import os, time
os.environ.setdefault("HF_HOME", os.path.join(os.path.dirname(os.path.abspath(__file__)), "models"))
os.environ["HF_HUB_DISABLE_XET"] = "1"          # Xet chunk transfer stalls on this network
from huggingface_hub import snapshot_download

BASE = "Wan-AI/Wan2.1-T2V-1.3B-Diffusers"
FAST = "FastVideo/FastWan2.1-T2V-1.3B-Diffusers"
stages = [
    ("core: transformer + vae + tokenizer", BASE,
     ["*.json", "*.txt", "*.model", "transformer/*", "vae/*", "scheduler/*", "tokenizer/*"]),
    ("text encoder: umt5-xxl (~22 GB)", BASE, ["text_encoder/*"]),
    ("distilled transformer (FastWan)", FAST, ["*.json", "transformer/*", "scheduler/*"]),
]
for name, repo, patterns in stages:
    t = time.time()
    print(f"\n>>> {name}", flush=True)
    snapshot_download(repo, allow_patterns=patterns, max_workers=4)
    print(f"<<< done in {time.time()-t:.0f}s", flush=True)
print("\nALL WEIGHTS READY", flush=True)
