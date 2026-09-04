# Voice cover workflow — Suno song, your voice

Everything below was learned the hard way on this Mac (M3 Pro, 36 GB, MPS, no CUDA)
while covering *One Breath*. Read "Traps" before changing anything: most of the
failures in this project were **silent** — a step printed "completed" and produced
zero files.

---

## The workflow

```
1  Suno            download the song AND its stems (7 tracks)
2  source          use "0 Lead Vocals.mp3" as the conversion source
3  convert         RVC (trained) or Seed-VC (zero-shot)  ->  your timbre
4  gate            silence anything the original singer did not sing
5  match           spectrum + LUFS matched to the original lead
6  mix             bed = the other 6 stems, unchanged, one continuous file
```

No splicing anywhere. Convert the whole 313 s vocal in one pass and lay it over one
untouched instrumental —句间静音转出来还是静音, so per-line cutting buys nothing and
costs seams.

### 1. Suno

Download both:
- the song (`One Breath (Remastered).mp3`)
- **Stems** — a zip with `0 Lead Vocals`, `1 Backing Vocals`, `2 Drums`, `3 Bass`,
  `4 Guitar`, `5 Synth`, `6 Other`, all 48 kHz stereo, all the full length.

The stems beat demucs on both ends: a cleaner conversion source, and a bed with no
separation residue. Suno's "Without Lead Vocal" export also works as a bed but is
**2 dB quieter** than the full mix — compensate with `volume=2dB`.

### 2. Prepare the source

```bash
ffmpeg -i "stems/0 Lead Vocals.mp3" -ac 1 -ar 44100 -c:a pcm_s16le -y source.wav
```

### 3. Convert

**RVC (Applio) — the default choice.**

```bash
cd rvc/applio
export PYTORCH_ENABLE_MPS_FALLBACK=1
.venv/bin/python core.py infer \
  --input-path  ../../source.wav \
  --output-path ../out/converted.wav \
  --pth-path logs/yancy48k/yancy48k_200e_7800s.pth \
  --index-path "" --index-rate 0 \
  --pitch 0 --protect 0.33 --f0-method rmvpe \
  --volume-envelope 1 --export-format WAV
```

**Seed-VC — no training, useful for a second opinion or a single section.**

```bash
cd svc/seed-vc
export PYTORCH_ENABLE_MPS_FALLBACK=1
.venv/bin/python inference.py \
  --source ../voice/wav/source.wav --target ../voice/wav/ref-y37.wav \
  --output ../out/seedvc --diffusion-steps 40 --inference-cfg-rate 0.7 \
  --f0-condition True --auto-f0-adjust False --semi-tone-shift 0
```

### 4–5. Gate, then match

```bash
python scripts/gate.py     converted.wav "stems/0 Lead Vocals.mp3" gated.wav
python scripts/matcheq.py  gated.wav processed.wav 0 -1 -19.5
```

Gate first: matching the spectrum of a track full of hallucinated noise matches the
noise too.

### 6. Mix

```
bed   = stems 1..6 summed, untouched
lead  = processed vocal + convolution reverb (~32 % wet)
```

---

## RVC vs Seed-VC

| | RVC (Applio) | Seed-VC |
|---|---|---|
| Training | 12 min of audio, **5 h** on this Mac | none, zero-shot |
| Full song (313 s) | **134 s** | ~37 min |
| Speed | 0.43× realtime | 7× realtime |
| 9–10 kHz vs original | −8.6 dB | −12.7 dB |
| LRA out of the box | 1.4 | 2.1 (原唱 1.9) |
| Silence hallucination | −53 dB | −43 dB (worse) |

**Use RVC.** It is ~16× faster, which is the difference between iterating and
waiting. Quality is close enough that the mix decisions matter more than the model.
Keep Seed-VC installed for one thing: when a specific passage sounds wrong, the
other model often renders it differently — a per-section swap costs minutes.

Neither model gets close to the original's air. At 9–10 kHz both sit well below the
Suno vocal, and **more diffusion steps make it worse, not better** (80 steps
measured 1.3 dB below 40). That ceiling is the vocoder's; no EQ recovers detail
that was never generated.

---

## Recording the voice samples

Full version, including the guide tones and the voiceprint check: **[VOICE-GUIDE.md](VOICE-GUIDE.md)**.

Measure the song first — the reference has to cover the range the song actually
demands, or the model extrapolates and the top sounds fake.

*One Breath* needed **E3–G4, median D4**, with F#4 alone accounting for 15.7 % of
the sung frames.

Target: **≥10 seconds of phonation per semitone** the song uses.

**Sing against a sustained guide tone, not against the song.** Following the song
drifts. But there is a trap:

> A guide tone above the comfortable range gets sung an **octave down**, and it
> feels correct because the pitch class matches. One take here came back a perfect
> octave low across the whole run. Build the guide so it *walks up* from a
> comfortable note in small steps, and check the result before recording more.

Real voice, not breathy falsetto — a breathy top has no resonance and the model
learns nothing from it.

Recording: quiet room, no reverb, phone noise-suppression **off**, no post-processing.
Bandwidth is rarely the problem — phone recordings here reached 14–15 kHz.

---

## Traps

**Silent failures. Count the output files.** Three separate steps in this project
reported success and produced nothing:

- Applio `extract.py:236` resolves the device as cpu-or-cuda only. On a Mac,
  `--gpu 0` becomes `cuda:0`, the workers die inside `ProcessPoolExecutor`, and the
  step prints "extracted successfully" with an empty folder. Patched to fall back.
- `rvc/lib/utils.py:149` downloads the embedder with `wget.download()`, which does
  not verify length or retry. It stopped 55 MB short of 378 MB and the truncated
  zip only failed much later, deep inside `from_pretrained`. Use `curl -C -`.
- Applio's final model export did not run at the end of training. Only `G_*/D_*`
  training checkpoints existed; the deployable 55 MB model had to be produced by
  calling `extract_model` manually. It also needs `assets/config.json`, which the
  repo ships only as `config_template.json`.

**Seed-VC on Apple Silicon needs two patches** (both only on the singing path, which
is why upstream's Mac support did not cover them):

- `inference.py:329-330` — the F0 extractor returns float64; MPS has no float64.
  Add `.float()` before `.to(device)`.
- `inference.py:408` — torchaudio 2.11 routes `save()` through TorchCodec. Write
  with `soundfile` instead.

**RVC's faiss index segfaults here** (exit 139) on load. Running with
`--index-path "" --index-rate 0` works; timbre fidelity is slightly lower.

**Both models hallucinate through silence.** The source is digital silence for the
first 26 s; RVC emits −53 dB there, Seed-VC −43 dB. Convolution reverb then turns
that bed into a drifting echo. Always gate the conversion against the source.

**demucs stems come out 23.02 ms late** relative to the mp3 they were separated
from — constant across the whole file. Every measurement comparing a stem-derived
file to the original is wrong by that amount until it is corrected, and it produces
convincing but fake "dips" at transients.

**Match LUFS, not RMS.** RMS matching left the vocal sounding quiet through three
rounds of the user saying so while the meter said it was fine.

**Watch your own processing.** The raw RVC vocal had LRA 1.4 — tighter than the
original's 1.9. After the spectrum-matching chain it was **3.6**: +12 dB boosts
landing on intermittent sibilance blew the loudness range open, and the compressor
sat *before* the EQ so nothing controlled what the EQ lifted. Cap corrections at
±6 dB and put a compressor after the EQ as well.

**Waveform correlation cannot tell you whether two files are the same take.** A
remaster is the same performance with a different waveform; correlation reads
≈ −0.4. Compare **onset envelopes** instead — same take scores > 0.9 at 0 ms lag.
This is also how to check a downloaded instrumental lines up.

**Suno's stems do not sum to the mix bit-exactly** (corr ≈ 0.9) — they are lossy
re-encodes. Sample-aligned, not phase-identical, so subtracting the instrumental
from the mix does **not** isolate the vocal (best-fit gain came out negative,
rejection 0.2 dB).

**Intelligibility survives heavy low-pass.** 800 Hz is nowhere near enough to make a
vocal unintelligible — telephone bandwidth is 300–3400 Hz. The first formant sits at
300–800 Hz. To remove words while keeping body you have to reach ~450 Hz, and the
floor is the singer's own fundamental (E3 = 165 Hz to G4 = 390 Hz here).

---

## Where things are

```
stems/                          Suno's 7 stems
svc/seed-vc/                    Seed-VC (patched); inference.py.orig is upstream
svc/voice/raw/Yancy/            voice samples
svc/voice/wav/ref-y37.wav       Seed-VC reference (samples 3 + 7)
rvc/applio/                     Applio (patched); extract.py.orig is upstream
rvc/dataset/yancy/              12 min training set, silence stripped
rvc/applio/logs/yancy48k/
  yancy48k_200e_7800s.pth       the trained model (55 MB)
  G_2809.pth                    lowest generator loss was at epoch 73
```

Training ran 200 epochs but the loss bottomed at **epoch 73** and never improved —
100 epochs would have been enough, and ~2.5 h instead of 5.
