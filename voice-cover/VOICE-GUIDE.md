# Recording a voice for conversion

How to get samples a voice-conversion model can actually use, and how to prove the
result is the right person. Written from what worked and what did not on *One
Breath* — seven takes before the coverage was right.

Companion to [WORKFLOW.md](WORKFLOW.md), which covers the conversion itself.

---

## Measure the song before you record anything

The reference has to cover the range the song demands. Where it does not, the model
extrapolates, and extrapolated high notes are exactly the "fake" sound people hear.

```bash
python scripts/range_check.py song "stems/one-breath/0 Lead Vocals.mp3"
```

*One Breath* comes back **E3–A4, median E4** — D4 25.2 %, F#4 18.1 %, E4 14.8 %,
G4 12.4 %, A4 5.8 %. The top four notes are most of the song, and the early takes
had almost none of them, which is why the choruses sounded synthetic.

> **These numbers replace the ones this file used to quote** (E3–G4, median D4,
> F#4 15.7 %, G4 3.8 %). The old figures came out of a detector that octave-halved;
> see *The tool that lied* below. The correction matters: the song reaches **A4**,
> not G4, and the yancy takes contain **0.0 s** of A4 against the song's 5.8 %. That
> gap sat unnoticed through a whole model because the measurement hid the note.

**Target: ≥10 seconds of phonation per semitone the song uses.** Check before
training, not after:

```bash
python scripts/range_check.py cover "stems/one-breath/0 Lead Vocals.mp3" svc/voice/wav/yancy/y*.wav
```

---

### The tool that lied

`range_check.py` originally took its pitch from `torchaudio.detect_pitch_frequency`,
which is autocorrelation-based and **octave-halves on sung high notes**. On the Shawn
takes it reported 8.7 s of F#4 and 42.2 s of F#3; the truth is 47.8 s and 14.0 s. The
two totals are nearly conserved, which is the signature — the energy did not vanish,
it moved down an octave.

Settled by a direct test rather than a second opinion: on the frames the good detector
calls F#4, the energy at f0/2 is 50–60 dB below f0 and **no frame carries a
sub-harmonic**. The singer really was at F#4.

It now uses `librosa.pyin` at 16 kHz — nothing sung reaches 900 Hz, and the shorter lag
search keeps a whole song under a minute.

Why it mattered: the bad numbers said a singer was missing the exact note he had the
most of, which would have sent him back to re-record a range he already covered. At
the same time it hid the note he genuinely lacked (A4). **A measurement that is wrong
in both directions is worse than no measurement**, because it gets acted on.

## Record against a guide tone, not against the song

Singing along to the record drifts — the singer follows the arrangement instead of
the pitch. A sustained tone is far easier to lock onto.

```bash
python scripts/guide_tone.py                             # the two song-specific runs
python scripts/guide_tone.py chromatic G2 C5 3.5 3 svc/voice/guide-chromatic.mp3
```

The first form writes two song-specific runs. The second walks the whole range one
semitone at a time, for covers that are not chosen yet: **G2–C5, three passes, 6.6 min,
10.5 s per semitone**, which clears the target below. Sing **ah** on the first pass,
**ee** on the second, **oo** on the third, and stay silent where the range runs out —
silence costs nothing, a strained squeak teaches a voice the singer does not have.

A short high pip marks every C, so a singer ten minutes into a featureless chromatic
run still knows where they are.

Pick the top by what the songs demand, not by the singer. *One Breath* reaches A4;
*Rejoice* puts **21.7 % of the song at A4 or above**. C5 covers both with headroom.

A pure sine is hard to tune to; these carry harmonics, which is why an organ note or
a hummed pitch is easy to match.

### The octave trap

> A guide tone above the comfortable range gets sung an **octave down**, and it
> feels correct because the pitch class is right.

This happened here. Take 5 followed the C4→E4→F#4→G4 guide perfectly — at E3, F#3,
G3. 64 seconds of phonation, zero of it in the range that was missing. The
distribution was an exact mirror of the guide, one octave low.

Two defences:

- Build the run so it **walks up in small steps** from a comfortable note, rather
  than jumping to the target.
- **Check the take before recording more.** `range_check.py cover` takes seconds and
  would have caught it immediately.

The take that finally worked (7) covered D3–G4 in one pass and brought the set to
12.8 s of G4. (The "0.5 s before" figure came from the broken detector; the shape of
the story holds, the exact before-number does not.)

### Chest or mixed voice, not breath

Breathy falsetto has almost no resonance, so the model learns nothing from it and
the top of the range still sounds hollow. A strained, cracking, ugly note in real
voice is worth more than a pretty airy one. Say so before recording — it is
counter-intuitive.

---

## Recording conditions

- Quiet room, **no reverb** — a closet, or under a blanket, genuinely helps
- Phone voice memo is fine; turn **noise suppression / voice isolation off**
- No post-processing: no EQ, no normalisation, no cleanup — hand over the raw file
- Same mic and same distance across every take

Bandwidth is rarely the limit. The phone takes here reached 14–15 kHz, well past
what the conversion models reproduce.

**Beware the 99.5 % rolloff metric.** It measures where the energy sits, so a take
with strong low end reads as "band-limited" when it is merely dark. Look at the
spectrum shape for a cliff instead; a real codec cut is a 40 dB drop inside one band.

---

## Training data

Ten to fifteen minutes of clean phonation is plenty for RVC. Strip silence first —
it only wastes epochs:

```bash
ffmpeg -i take.m4a -af "highpass=f=60,silenceremove=start_periods=1:start_silence=0.15:\
start_threshold=-45dB:detection=rms,areverse,silenceremove=start_periods=1:\
start_silence=0.15:start_threshold=-45dB:detection=rms,areverse" \
  -ac 1 -ar 44100 -c:a pcm_s16le -y dataset/name/take.wav
```

Then, in `rvc/applio`:

```bash
python core.py preprocess --model-name NAME --dataset-path ../dataset/NAME \
  --sample-rate 48000 --cpu-cores 8 --cut-preprocess Automatic \
  --chunk-len 3.0 --overlap-len 0.3 --normalization-mode post

python core.py extract --model-name NAME --f0-method rmvpe --cpu-cores 8 --gpu 0 \
  --sample-rate 48000 --embedder-model contentvec --include-mutes 2

python core.py train --model-name NAME --sample-rate 48000 --vocoder HiFi-GAN \
  --total-epoch 100 --batch-size 8 --gpu 0 --pretrained \
  --save-every-epoch 25 --index-algorithm Auto
```

**Do not pass `--save-every-weights`.** It is declared `is_flag=True, default=True`,
and Click sets a flag's value to `not default` when there is no `--no-` twin — so
passing it sets it to **False** and silently disables the per-epoch export it appears
to request. Omitting it leaves the default True. Verified against Click 8.1.8:

```
--save-every-weights   ->  False        (what the flag does)
omitted                ->  True         (what you want)
```

The shawn48k run passed the flag as this file used to document it and got no
deployable model at epochs 25, 50 or 75 — only the 1.3 GB `G_*/D_*` pairs. The final
export at the last epoch is unconditional in `train.py`, so it still appeared at
epoch 100. This is the real mechanism behind the third silent failure below.

**Count the output files after every step.** All three have failed silently here —
see the Traps section of WORKFLOW.md.

Timing on an M3 Pro with 12 minutes of audio: preprocess 26 s, extract 56 s, train
**1.5 min/epoch**. The generator loss bottomed at **epoch 73** and never improved,
so 200 epochs cost 5 hours for nothing beyond epoch ~75. **Use 100.**

Training saves `G_*/D_*` checkpoints at 431 MB / 817 MB each — a 200-epoch run left
12 GB behind. Only the exported 55 MB model is needed for inference; keep one `G_`
near the loss minimum if you might re-export.

---

## Proving it is the right voice

People judge a converted vocal by **delivery**, not timbre — pitch, breath and
phrasing all come from the source singer, so a listener who knows you may say "that
isn't you" while the timbre is in fact yours. Measure it.

```bash
python scripts/voiceprint.py
```

ECAPA-TDNN (VoxCeleb) embeddings, cosine similarity over hundreds of 3-second
segments. **Establish baselines on the same material** — a single number means
nothing:

| | similarity |
|---|---|
| different people | +0.162 |
| same person, different takes | +0.271 |
| **converted vocal vs the singer** | **+0.291** |
| converted vocal vs a control speaker | +0.180 |

The control matters: run the same comparison against someone else's voice and it
should fall back into the different-people band. Here it did (0.180), which is what
makes the 0.291 meaningful rather than an artefact of the metric being generous.

Two honest caveats: ECAPA is trained on speech, so singing is out of distribution
and the absolute values do not map onto published thresholds; and conversion keeps
the source's prosody, which inflates similarity toward the source singer too
(+0.268 here). The comparison is only meaningful **relative to the baselines
measured on the same audio**.

Resemblyzer, which ships with Applio, was not usable here — its same-speaker and
different-speaker ranges overlapped (0.831 vs 0.856).

### Blind test

Level-match, strip reverb, use the same length, and do not say which is which:

```bash
ffmpeg -ss 100 -t 30 -i converted.wav -af loudnorm=I=-20:TP=-1.5:LRA=11 A.mp3
ffmpeg -ss 0   -t 30 -i take.wav      -af loudnorm=I=-20:TP=-1.5:LRA=11 B.mp3
```

Ask "is this the same person", not "does this sound like X" — the second question
invites the delivery to answer instead of the timbre.

---

## Scripts

| | |
|---|---|
| `scripts/range_check.py` | what the song needs / what the takes cover |
| `scripts/guide_tone.py` | sustained guide tones to sing against |
| `scripts/voiceprint.py` | ECAPA speaker verification with baselines |
| `scripts/gate.py` | silence what the source singer did not sing |
| `scripts/matcheq.py` | spectrum + LUFS match to the original vocal (`LEAD_REF` selects the song) |
| `scripts/audio/wet-lead.sh` | convolution reverb blended by ear-percentage |
| `scripts/make_recording_pdf.py` | the printable session sheet, `en` or `zh` |

The handout for the singer is [RECORDING-GUIDE.pdf](RECORDING-GUIDE.pdf)
([中文](RECORDING-GUIDE-zh.pdf)) — room, mic, settings, and how to use the guide
track, on two printable pages.
