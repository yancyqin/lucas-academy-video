# Voice cover — sing a Suno song in your own voice

Singing voice conversion: keep the melody, rhythm and phrasing of a Suno track, swap
the timbre for yours. The tooling spans two directories — `rvc/` and `svc/` — so the
docs live here rather than inside either one.

| | |
|---|---|
| **[SETUP.md](SETUP.md)** | Build both environments from scratch. Every patch here fixes a **silent** failure on Apple Silicon. Start here. |
| **[WORKFLOW.md](WORKFLOW.md)** | The six-step pipeline, the RVC vs Seed-VC comparison, and the traps. |
| **[VOICE-GUIDE.md](VOICE-GUIDE.md)** | Recording requirements, guide tones, training, and voiceprint verification. |

## Which tool

**RVC (Applio)** is the default. On this Mac it converts a 5-minute song in
**134 seconds**; Seed-VC takes ~37 minutes for the same job. Quality is close enough
that mix decisions matter more than the model. RVC needs a trained model
(12 min of audio, ~2.5 h at 100 epochs); Seed-VC is zero-shot.

Keep both installed. When one passage sounds wrong, the other model often renders it
cleanly — the finished lead vocal here is three segments spliced from the original
singer, Seed-VC, and RVC.

## Layout

```
rvc/applio/                     Applio, patched for MPS
rvc/applio/logs/NAME/           trained model (the 55 MB *_NNNe_NNNNs.pth)
rvc/dataset/NAME/               training audio, silence stripped
svc/seed-vc/                    Seed-VC, patched
svc/voice/raw/NAME/             voice recordings   <- not reproducible, keep
svc/voice/wav/                  converted wav + reference sets
stems/                          Suno's 7 stems     <- not reproducible, keep
scripts/                        range_check, guide_tone, voiceprint, gate, matcheq
out/                            deliverables
```

## The one rule

Several upstream steps **report success and write zero files** — feature extraction
picking a CUDA device that is not there, a model download stopping 55 MB short, the
final model export never running. Count the output files after every step; an exit
code of 0 proves nothing.
