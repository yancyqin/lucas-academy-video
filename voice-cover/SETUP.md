# Setup — from a clean machine

Two separate environments, both patched. Nothing here is optional: every patch below
fixes a failure that is **silent** on Apple Silicon — the step prints success and
writes nothing.

Verified on macOS 15 / M3 Pro / 36 GB, no CUDA. Needs `uv`, `ffmpeg`, `git`.

```bash
brew install uv ffmpeg
```

---

## RVC (Applio) — the default converter

```bash
cd lucas-academy-video/rvc
git clone --depth 1 https://github.com/IAHispano/Applio.git applio
cd applio
uv venv --python 3.12 .venv                 # 3.12, not 3.10
VIRTUAL_ENV=.venv uv pip install -r requirements.txt
.venv/bin/python -c "import torch; print(torch.backends.mps.is_available())"   # must print True
```

Do **not** use the official `RVC-Project/Retrieval-based-Voice-Conversion-WebUI`.
Its `configs/config.py` resolves the device as CUDA-or-CPU with no MPS branch, so
training silently falls back to CPU — hours instead of minutes. Applio has the MPS
path (`rvc/train/train.py:198`).

### Patch 1 — device fallback in feature extraction

`rvc/train/extract/extract.py:236` reads:

```python
devices = ["cpu"] if gpus == "-" else [f"cuda:{idx}" for idx in gpus.split("-")]
```

On a Mac `--gpu 0` becomes `cuda:0`, the workers die inside `ProcessPoolExecutor`,
and the step reports "extracted successfully" with an empty folder. Replace with:

```python
if gpus == "-":
    devices = ["cpu"]
elif torch.cuda.is_available():
    devices = [f"cuda:{idx}" for idx in gpus.split("-")]
else:
    devices = ["cpu"]
    print("No CUDA device present; extracting on CPU.")
```

Add `import torch` near the top if it is not already imported. Upstream copy is kept
as `extract.py.orig`.

### Pretrained weights

```bash
.venv/bin/python core.py prerequisites --pretraineds-hifigan --models --no-exe
```

Click uses dashes, not underscores — `--pretraineds_hifigan` errors out.

### Patch 2 — the embedder download truncates

`rvc/lib/utils.py:149` fetches contentvec with `wget.download()`, which verifies
nothing and does not retry. It stopped 55 MB short of 378 MB here, and the truncated
zip only failed much later inside `from_pretrained` with a miniz error that names
nothing useful. Fetch it with curl instead:

```bash
curl -L --retry 8 --retry-delay 3 -C - \
  -o rvc/models/embedders/contentvec/pytorch_model.bin \
  https://huggingface.co/IAHispano/Applio/resolve/main/Resources/embedders/contentvec/pytorch_model.bin

python -c "import zipfile; print(zipfile.is_zipfile('rvc/models/embedders/contentvec/pytorch_model.bin'))"
```

Must print `True` and the file must be **378,342,945 bytes**.

### Patch 3 — the trained model is not exported

Training writes only `G_*/D_*` checkpoints; the final export step did not run at the
end of a 200-epoch run here. `assets/config.json` is also missing (the repo ships
`config_template.json`). To produce the deployable model by hand:

```bash
echo '{"model_author": "you"}' > assets/config.json
```

```python
import json, torch, types, sys; sys.path.insert(0, '.')
from rvc.train.process.extract_model import extract_model
ns = lambda d: types.SimpleNamespace(**{k: ns(v) if isinstance(v, dict) else v
                                        for k, v in d.items()})
hps  = ns(json.load(open('logs/NAME/config.json')))
ckpt = torch.load('logs/NAME/G_7800.pth', map_location='cpu', weights_only=False)
extract_model(ckpt=ckpt.get('model', ckpt), sr=48000, name='NAME',
              model_path='logs/NAME/NAME_200e_7800s.pth',
              epoch=200, step=7800, hps=hps, vocoder='HiFi-GAN')
```

### Known issue — faiss index segfaults

Passing `--index-path` to inference crashes with SIGSEGV (exit 139) after the weights
load. Run with `--index-path "" --index-rate 0`; timbre fidelity is slightly lower.

---

## Seed-VC — zero-shot, keep it for second opinions

```bash
cd lucas-academy-video/svc
git clone --depth 1 https://github.com/Plachtaa/seed-vc.git seed-vc
cd seed-vc
uv venv --python 3.10 .venv                 # 3.10, not 3.12
```

`requirements-mac.txt` carries pip-only inline flags (`--pre`) and a CUDA index that
`uv pip` rejects and a Mac does not need. Install torch separately:

```bash
grep -vE '^(--extra-index-url|torch |torchvision |torchaudio )' requirements-mac.txt > /tmp/req.txt
VIRTUAL_ENV=.venv uv pip install torch torchvision torchaudio
VIRTUAL_ENV=.venv uv pip install -r /tmp/req.txt
```

The singing checkpoint (`seed-uvit-whisper-base`, 783 MB, 44.1 kHz, F0-conditioned)
downloads to `checkpoints/` on first run — allow ~20 minutes. The RMVPE pitch model
downloads on the first `--f0-condition True` run, another ~1.4 GB.

### Patch 1 — float64 on MPS

`inference.py:329-330`. The F0 extractor returns float64; Metal has no float64.

```python
F0_ori = torch.from_numpy(F0_ori).float().to(device)[None]
F0_alt = torch.from_numpy(F0_alt).float().to(device)[None]
```

### Patch 2 — torchaudio 2.11 save

`inference.py:408` calls `torchaudio.save`, which now routes through TorchCodec.
`soundfile` is already a dependency and needs no native libs:

```python
import soundfile as _sf
_sf.write(
    os.path.join(args.output,
                 f"vc_{source_name}_{target_name}_{length_adjust}_{diffusion_steps}_{inference_cfg_rate}.wav"),
    vc_wave.cpu().numpy().T, sr)
```

Both patches only affect the **singing** path (`--f0-condition True`), which is why
upstream's Apple Silicon support does not cover them. Upstream copy is
`inference.py.orig`.

Always run Seed-VC with `PYTORCH_ENABLE_MPS_FALLBACK=1`.

---

## Shared tools

```bash
VIRTUAL_ENV=.venv-align uv pip install torch torchaudio numpy scipy soundfile speechbrain demucs stable-ts
```

`scripts/` expects this environment for `range_check.py`, `matcheq.py` and
`voiceprint.py`; `gate.py` and `guide_tone.py` only need numpy + soundfile and run
under either venv.

---

## Verify the install

```bash
# RVC: convert 13 seconds, should take ~6 s and write a file
cd rvc/applio && PYTORCH_ENABLE_MPS_FALLBACK=1 .venv/bin/python core.py infer \
  --input-path ../../svc/voice/wav/source-chorus-remaster.wav \
  --output-path /tmp/t.wav --pth-path logs/NAME/NAME_200e_7800s.pth \
  --index-path "" --index-rate 0 --pitch 0 --protect 0.33 --f0-method rmvpe \
  --volume-envelope 1 --export-format WAV
ls -l /tmp/t.wav
```

**Check the file exists.** An exit code of 0 means nothing here — several of these
steps return 0 having written nothing.

---

## Disk

| | |
|---|---|
| `rvc/applio` venv + pretrained | ~2 GB |
| `svc/seed-vc` venv + checkpoints | ~10 GB |
| training checkpoints, per 25-epoch save | 431 MB (G) + 817 MB (D) |
| exported model | **55 MB** — the only thing inference needs |

A 200-epoch run leaves 12 GB of `G_*/D_*` behind. Keep the export and one `G_` near
the loss minimum; delete the rest.
