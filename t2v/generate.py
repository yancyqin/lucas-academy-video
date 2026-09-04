#!/usr/bin/env python
"""Text-to-video on Apple Silicon, using open-source weights and the Metal (MPS) backend.

Backends -- the text encoder and VAE are shared, only the denoiser differs:

  wan      Wan2.1-T2V-1.3B, the official model. ~50 steps, classifier-free guidance.
  fastwan  FastWan2.1-T2V-1.3B, the same model distilled by FastVideo so that a
           handful of steps replaces the full schedule. No guidance pass, so a
           step is also half the work.

Pass --text-encoder to borrow ComfyUI's umt5 checkpoint rather than downloading
the 22 GB fp32 copy that ships with the diffusers repo; the key names match.

Example:
  ./.venv/bin/python generate.py --prompt "a paper boat drifting down a rain gutter" \
    --text-encoder ~/ComfyUI-Shared/models/text_encoders/umt5_xxl_fp16.safetensors
"""

import argparse
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
# Keep every downloaded byte inside this repo instead of ~/.cache.
os.environ.setdefault("HF_HOME", os.path.join(HERE, "models"))
# A few ops still have no Metal kernel; let them run on the CPU rather than crash.
os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")

import numpy as np  # noqa: E402
import torch  # noqa: E402
from diffusers import (  # noqa: E402
    AutoencoderKLWan,
    FlowMatchEulerDiscreteScheduler,
    UniPCMultistepScheduler,
    WanPipeline,
)
from diffusers.utils import export_to_video  # noqa: E402

BASE_REPO = "Wan-AI/Wan2.1-T2V-1.3B-Diffusers"
FAST_REPO = "FastVideo/FastWan2.1-T2V-1.3B-Diffusers"

# The negative prompt shipped by the Wan authors. It steers away from the failure
# modes the model is prone to (still frames, extra limbs, JPEG mush).
NEGATIVE = (
    "色调艳丽，过曝，静态，细节模糊不清，字幕，风格，作品，画作，画面，静止，整体发灰，"
    "最差质量，低质量，JPEG压缩残留，丑陋的，残缺的，多余的手指，画得不好的手部，"
    "画得不好的脸部，畸形的，毁容的，形态畸形的肢体，手指融合，静止不动的画面，"
    "杂乱的背景，三条腿，背景人很多，倒着走"
)

PRESETS = {
    #           steps  guidance  flow_shift
    "wan": dict(steps=50, guidance=5.0, shift=3.0),
    # Distillation collapses the schedule to three fixed points and drops guidance,
    # so a step costs half as much as well (no negative-prompt pass).
    "fastwan": dict(steps=3, guidance=1.0, shift=3.0),
}

# The denoising timesteps FastVideo distilled against. UniPC would otherwise place
# three steps on an even linspace, which is not where this model was trained.
DMD_TIMESTEPS = (1000.0, 757.0, 522.0)


def pin_dmd_timesteps(scheduler, wanted=DMD_TIMESTEPS):
    """Force the scheduler onto the distilled model's fixed schedule.

    UniPC accepts custom sigmas, but re-applies the flow shift to whatever it is
    given, so undo the shift first: sigma = y / (shift - y * (shift - 1)).
    """
    shift = scheduler.config.flow_shift
    sigmas = np.array([(y := t / 1000.0) / (shift - y * (shift - 1)) for t in wanted])
    original = scheduler.set_timesteps

    def set_timesteps(num_inference_steps=None, device=None, **kwargs):
        kwargs.pop("sigmas", None)
        original(num_inference_steps=None, device=device, sigmas=sigmas, **kwargs)

    scheduler.set_timesteps = set_timesteps


def parse_args():
    p = argparse.ArgumentParser(
        description="Generate a video from a text prompt on Apple Silicon.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--prompt", required=True)
    p.add_argument("--negative", default=NEGATIVE)
    p.add_argument("--backend", choices=sorted(PRESETS), default="fastwan")
    # 16 keeps the latent grid whole after the VAE's 8x downsample and the patchifier's 2x.
    p.add_argument("--width", type=int, default=832, help="multiple of 16")
    p.add_argument("--height", type=int, default=480, help="multiple of 16")
    # The VAE compresses time 4x around a single anchor frame, so 4k+1 frames.
    p.add_argument("--frames", type=int, default=33, help="4k+1; 81 frames = 5s at 16fps")
    p.add_argument("--fps", type=int, default=16)
    p.add_argument("--steps", type=int, default=None, help="default depends on backend")
    p.add_argument("--guidance", type=float, default=None, help="default depends on backend")
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--shift", type=float, default=None, help="flow shift; default depends on backend")
    p.add_argument(
        "--scheduler",
        choices=["euler", "unipc"],
        default="euler",
        help="euler is 1st-order and keeps no history between steps. unipc is the "
        "upstream default, but its 2nd-order history accumulates bf16 error on Metal "
        "and burns colour out past ~15 steps",
    )
    p.add_argument(
        "--text-encoder",
        default=None,
        help="single-file umt5 checkpoint (e.g. ComfyUI's umt5_xxl_fp16.safetensors) "
        "to load instead of the sharded diffusers copy",
    )
    p.add_argument("--out", default=None)
    return p.parse_args()


def check_geometry(args):
    problems = []
    for name, value in (("width", args.width), ("height", args.height)):
        if value % 16:
            problems.append(f"--{name} {value} is not a multiple of 16")
    if args.frames % 4 != 1:
        problems.append(f"--frames {args.frames} is not 4k+1 (try {args.frames // 4 * 4 + 1})")
    if problems:
        sys.exit("error: " + "; ".join(problems))


def load_single_file_encoder(path):
    """Reuse ComfyUI's umt5 checkpoint as the diffusers text encoder.

    Comfy-Org's repackaged encoders keep the HuggingFace key names, so this is a
    plain state-dict load into a model built from the config -- no remapping, and
    it saves re-downloading the 22 GB fp32 copy.
    """
    from safetensors.torch import load_file
    from transformers import UMT5Config, UMT5EncoderModel

    config = UMT5Config.from_pretrained(BASE_REPO, subfolder="text_encoder")
    # Build on meta so the 11 GB of random init is never actually allocated;
    # assign=True then hands the loaded tensors straight to the module.
    with torch.device("meta"):
        model = UMT5EncoderModel(config)

    state = load_file(path)
    state.pop("spiece_model", None)  # ComfyUI bundles the tokenizer in the same file
    _, unexpected = model.load_state_dict(state, strict=False, assign=True)
    # embed_tokens shares storage with shared.weight, so the checkpoint carries it
    # only once and the tie has to be redone by hand after an assign-load.
    model.encoder.embed_tokens.weight = model.shared.weight

    stranded = [n for n, t in (*model.named_parameters(), *model.named_buffers()) if t.is_meta]
    if stranded:
        raise SystemExit(f"text encoder left {len(stranded)} tensors unloaded: {stranded[:3]}")
    if unexpected:
        print(f"  ignored {len(unexpected)} unexpected tensors: {unexpected[:3]}", flush=True)
    return model.to(torch.bfloat16).eval()


def build_pipeline(backend, shift, text_encoder_path=None, scheduler="unipc"):
    """Load the shared encoder/VAE, then whichever transformer this backend wants."""
    dtype = torch.bfloat16

    # The Wan VAE is numerically fragile; the authors keep it in fp32 and so do we.
    vae = AutoencoderKLWan.from_pretrained(BASE_REPO, subfolder="vae", torch_dtype=torch.float32)

    extra = {}
    if text_encoder_path:
        extra["text_encoder"] = load_single_file_encoder(text_encoder_path)
    if backend == "fastwan":
        from diffusers import WanTransformer3DModel

        extra["transformer"] = WanTransformer3DModel.from_pretrained(
            FAST_REPO, subfolder="transformer", torch_dtype=dtype
        )

    pipe = WanPipeline.from_pretrained(BASE_REPO, vae=vae, torch_dtype=dtype, **extra)
    if scheduler == "unipc":
        pipe.scheduler = UniPCMultistepScheduler.from_config(
            pipe.scheduler.config,
            prediction_type="flow_prediction",
            use_flow_sigmas=True,
            num_train_timesteps=1000,
            flow_shift=shift,
        )
        if backend == "fastwan":
            pin_dmd_timesteps(pipe.scheduler)
    else:
        pipe.scheduler = FlowMatchEulerDiscreteScheduler(
            num_train_timesteps=1000, shift=shift
        )

    pipe.to("mps")
    # Deliberately NOT vae.enable_tiling(): on this VAE the tiled path holds every
    # tile plus its conv cache and peaks around 45 GiB, where the plain decode --
    # which already walks the clip one latent frame at a time -- peaks near 24 GiB.
    return pipe


def main():
    args = parse_args()
    check_geometry(args)

    if not torch.backends.mps.is_available():
        sys.exit("error: this machine has no Metal (MPS) backend")

    preset = PRESETS[args.backend]
    steps = args.steps if args.steps is not None else preset["steps"]
    guidance = args.guidance if args.guidance is not None else preset["guidance"]
    shift = args.shift if args.shift is not None else preset["shift"]
    out = args.out or os.path.join(
        HERE, "outputs", f"{args.backend}-{args.seed}-{int(time.time())}.mp4"
    )
    os.makedirs(os.path.dirname(out), exist_ok=True)

    seconds = (args.frames - 1) / args.fps
    print(
        f"backend={args.backend}  {args.width}x{args.height}  {args.frames} frames "
        f"({seconds:.1f}s @ {args.fps}fps)  steps={steps}  guidance={guidance}  shift={shift}  "
        f"scheduler={args.scheduler}",
        flush=True,
    )
    print(f"prompt: {args.prompt}", flush=True)

    t0 = time.time()
    pipe = build_pipeline(args.backend, shift, args.text_encoder, args.scheduler)
    print(f"[{time.time() - t0:6.1f}s] pipeline ready", flush=True)

    marks = []

    def on_step(pipe_, i, t, kwargs):
        marks.append(time.time())
        prev = marks[-2] if len(marks) > 1 else t1  # t1 is set just below
        print(f"  step {i + 1}/{steps}  {marks[-1] - prev:5.1f}s", flush=True)
        return kwargs

    # Encode first, then drop the 11 GB encoder. Otherwise the encoder, the
    # transformer and the VAE are all resident at once and 36 GB is not enough.
    with torch.no_grad():
        positive, negative = pipe.encode_prompt(
            prompt=args.prompt,
            negative_prompt=args.negative if guidance > 1.0 else None,
            do_classifier_free_guidance=guidance > 1.0,
            device="mps",
        )
    pipe.text_encoder = None
    torch.mps.empty_cache()
    print(f"[{time.time() - t0:6.1f}s] prompt encoded, text encoder released", flush=True)

    t1 = time.time()
    result = pipe(
        prompt_embeds=positive,
        negative_prompt_embeds=negative,
        width=args.width,
        height=args.height,
        num_frames=args.frames,
        num_inference_steps=steps,
        guidance_scale=guidance,
        generator=torch.Generator().manual_seed(args.seed),
        callback_on_step_end=on_step,
        output_type="latent",
    )
    gen = time.time() - t1

    # Denoising is the expensive half. Park it on disk first, so a failure in the
    # VAE decode costs a decode and not the whole run.
    latents = result.frames
    checkpoint = os.path.splitext(out)[0] + ".latents.pt"
    torch.save(latents.cpu(), checkpoint)
    print(
        f"[{time.time() - t0:6.1f}s] denoise done in {gen:.0f}s ({gen / steps:.1f}s/step)"
        f" -> {checkpoint}",
        flush=True,
    )

    # The 33-frame decode alone peaks at 36 GiB on this machine, so the transformer
    # has to go the same way the text encoder did before the VAE starts.
    pipe.transformer = None
    torch.mps.empty_cache()

    frames = decode_latents(pipe, latents, out, args.fps)
    total = time.time() - t0
    print(f"\n{out}  ({frames} frames)\ntotal {total / 60:.1f} min", flush=True)


def decode_latents(pipe, latents, out, fps):
    """Undo the VAE's per-channel normalisation, decode, and write the mp4."""
    t = time.time()
    torch.mps.empty_cache()
    vae = pipe.vae
    latents = latents.to(vae.dtype)
    mean = torch.tensor(vae.config.latents_mean).view(1, vae.config.z_dim, 1, 1, 1).to(latents)
    std = torch.tensor(vae.config.latents_std).view(1, vae.config.z_dim, 1, 1, 1).to(latents)
    latents = latents * std + mean

    with torch.no_grad():
        video = vae.decode(latents, return_dict=False)[0]
    frames = pipe.video_processor.postprocess_video(video, output_type="np")[0]
    print(
        f"  vae decode {time.time() - t:.0f}s, "
        f"peak {torch.mps.driver_allocated_memory() / 2**30:.1f} GiB",
        flush=True,
    )
    export_to_video(frames, out, fps=fps)
    return len(frames)


if __name__ == "__main__":
    main()
