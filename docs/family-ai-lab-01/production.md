# Family AI Lab 01 — bilingual film

**Next revision — cover/copy review only (2026-11-05):** [Owner review brief](revision-2026-11-05.md); complete narration drafts: [Chinese](full-review-v2.zh.md) / [English](full-review-v2.en.md) and [new cover candidate](cover-v2.json). The next MP4 will have no subtitle tracks or reserved subtitle strip; SRT files remain separate. The current delivered film below is the previous version. No new video, Muse shot or narration is generated in this step.

One common picture uses short English labels. Louise narrates both languages at speed 1.1 with a warm, curious, conversational instruction. The MP4 contains two independent audio tracks and two independent subtitle tracks; English is selected by default for both. Captions are not burned into the picture. `FamilyAiLab01En` / `Zh` are inspection compositions for the same timeline, not separate film deliveries.

## Delivery

- Film: `out/family-ai-lab-01/delivery/family-ai-lab-01.bilingual.mp4`, 1920×1080, 30 fps. The exact duration and measured loudness are in [verification.json](verification.json).
- External captions: `out/family-ai-lab-01/delivery/en.srt`, `out/family-ai-lab-01/delivery/zh-Hans.srt`.
- Separate audio: `out/family-ai-lab-01/audio/en.m4a`, `out/family-ai-lab-01/audio/zh.m4a`.
- Covers: `out/family-ai-lab-01/cover/design-{1,2,3}.{en,zh}.png`, 1280×720. `all-designs.png` is the six-cover contact sheet.
- Scripts: [English](en-script.md), [Chinese](zh-script.md), common sentence IDs `fa01-NN-MM`.
- Verification: `out/family-ai-lab-01/delivery/verification.json` and [committed check result](verification.json).
- QuickTime Player: View → Languages selects English / Chinese audio; View → Subtitles selects either independent caption track. The earlier silent review remains under `out/family-ai-lab-01/review/` as a previous revision.

The opening animates all 419 actual training sprites: 228 sevens and 191 ones, in amber and cyan. They fall as pixel rain and gather into the actual race input. The native terminal shot retains the saved result rows while cropping out the shell username, host and cursor. The browser-lab scenes and final invitation show a QR code for https://ai.lucasacademy.org/ . The old website placeholder is removed. QR recognition is checked on a rendered 1280×720 film frame, not just on the source image.

## Narration and timing

152 selected sentence WAVs are preserved under the ignored `public/family-ai-lab-01/narration/` input directory and in the local data backup. Each take has a SHA256, actual duration, original synthesis settings and source. English/Chinese plans are in [voice.en.json](voice.en.json) and [voice.zh.json](voice.zh.json). [voice-overrides.json](voice-overrides.json) records pronunciation-specific respellings and unambiguous paraphrases. These do not change experimental numbers; captions retain ordinary spelling. [voice-choices.json](voice-choices.json) records the inspected take chosen for each sentence.

Whisper small transcribes every selected sentence independently. Uncertain lines receive a second medium-model pass; transcripts and hashes remain in the local data backup. Scores only identify review candidates: number units and Mandarin homophones require separate inspection. Rephrased retakes clarify “our race”, “through layers”, the row pronunciation of 行, and the 亿 units in the brain/model counts.

Each sentence starts 0.1 seconds into its picture interval. The common interval uses the longer actual English/Chinese take plus a 0.4-second gap; no speech is stretched or clipped. The race interval also preserves real elapsed finish times. The final invitation adds five seconds to scan the code. Two-pass loudness normalization targets −16 LUFS and −1 dBTP. Final AAC audio is measured again after muxing. All Muse and browser footage is muted so only the selected narration enters the two audio tracks.

Cover directions: 1 — brass photocell array; 2 — paper card and circuits; 3 — green CRT. Generated backgrounds contain no text. Every title, model name and number is typeset by code. Bilingual cover questions and the surrounding comparison copy follow the film-specific owner plan, which overrides the general repository cover rules. No series ribbon or diagonal band.

## Experiment selection

The owner explicitly retained the original complete round after seeing the later Claude timing change. No benchmarks or calls to the race contenders were made during production. `reruns/` is not read by the build or compositions. [Selected-data hashes](selected-data.json) freeze the four original JSON inputs. The native terminal clip shows the saved original files, clearly labelled as records; it is not presented as a new model run.

The race runs at 1:1 elapsed seconds. JavaScript completes before the next 30 fps frame. Each model's displayed finishing time comes directly from its original JSON median. The illustrative input is the actual `seven-a` grid. A single small methodological line stays in the race corner. X's name is withheld until S6. The earlier twelve-example experiment is never used in the film.

The browser footage uses the owner's actual Perceptron Lab. Its 3×3 activity is operated through the real controls. A capture-only adapter imports the already-trained 419-picture model at 20×20; it leaves Python `predict` and `train` unchanged. This restoration has no timing loop, writes no benchmark result, and calls no language model. Enlarged point grids and lists are synchronized crops of that same recording. [Capture provenance](capture.json) and [curriculum input hashes](curriculum-sources.json) record the source. The sibling curriculum checkout is not modified.

## Picture sources

Every shot carries a lower-right credit. [Muse prompts and selection](muse.md) describe the three owner-supplied originals. [ImageGen prompts](image-prompts.json) describe all three cover backgrounds, produced with the built-in image tool. AI material is labelled as illustration. Mark I is a deliberately simplified authored schematic, not archival footage or a wiring plan. No Commons photographs are used.

The 400-point and approximately eight-billion-parameter comparison uses area, not an invented parameter count for GPT or Claude. A 400-point square would be about 0.136 pixels wide beside a 610-pixel square representing eight billion; the visible 20×20 grid is explicitly an enlarged inset. Qwen's published full count is 8.2 billion, rounded to approximately eight billion for this family explanation.

## Sources for educational facts

| Used in film | Primary source |
|---|---|
| 1957 report title and date | [Frank Rosenblatt, *The Perceptron: A Perceiving and Recognizing Automaton*, Cornell Aeronautical Laboratory, Report 85-460-1, January 1957 (scan)](https://perceptrondemo.com/assets/rosenblatt-perceptron-perceiving-1957-1ea0ab61.pdf) |
| Mark I optical array and motor-adjusted potentiometers | [*Mark I Perceptron Operators' Manual*, Cornell Aeronautical Laboratory, February 15, 1960 (DTIC)](https://apps.dtic.mil/sti/pdfs/AD0236965.pdf); [Smithsonian collection record](https://www.si.edu/object/electronic-neural-network-mark-i-perceptron%3Anmah_334414) |
| 1958 headline, text only | [*The New York Times*, July 8, 1958](https://www.nytimes.com/1958/07/08/archives/new-navy-device-learns-by-doing-psychologist-shows-embryo-of.html) |
| Common approximate human neuron estimate | [Azevedo et al., 2009, original study abstract](https://pubmed.ncbi.nlm.nih.gov/19226510/) — the estimate is approximate, not a precise count for every person |
| Hebb's 1949 strengthening proposal | [*The Organization of Behavior*, original book scan](https://pure.mpg.de/pubman/item/item_2346268_3/component/file_2346267/Hebb_1949_The_Organization_of_Behavior.pdf) |
| 1969 mathematical limits | [Minsky and Papert, *Perceptrons*, original publisher record](https://mitpress.mit.edu/9780262630221/perceptrons/) |
| Later cooling of interest, expressed briefly without assigning it to one cause | [Olazaran's historical research, 1991](https://era.ed.ac.uk/server/api/core/bitstreams/dc0fad18-9a98-4b3a-acf1-9610af9592c6/content); [UCSD Institute for Neural Computation, *Perceptrons*, 2004](https://tdlc.ucsd.edu/documents/Perceptrons%20Monograph.pdf) |
| Backpropagation milestone | [Rumelhart, Hinton and Williams, *Nature*, 1986](https://www.nature.com/articles/323533a0) |
| ImageNet milestone | [Krizhevsky, Sutskever and Hinton, NeurIPS 2012](https://proceedings.neurips.cc/paper_files/paper/2012/hash/c399862d3b9d6b76c8436e924a68c45b-Abstract.html) |
| Transformer milestone | [Vaswani et al., 2017](https://arxiv.org/abs/1706.03762) |
| Qwen3-8B parameter count | [Official Qwen model card](https://huggingface.co/Qwen/Qwen3-8B) |
| Heart and cat bytes, classroom activity | Owner's `lucas-academy-ai` curriculum, exact revision and asset hashes in [curriculum-sources.json](curriculum-sources.json) |

## Rebuild

From the existing checkout, without a worktree, first restore the local media backup if inputs are absent:

```sh
python3 ../lucas-academy-video-data/family-ai-lab-01/restore.py "$PWD"
npm run fal01:timeline:voiced
npm run fal01:voice:mix
npm run fal01:cover
node scripts/family-ai-lab-01/render.cjs --stills
npm run fal01:final
npm run fal01:check:final
npm run fal01:backup
```

Restore verifies SHA256SUMS before copying and refuses differing destination files. The backup includes Muse originals, generated backgrounds, curriculum snapshots, native recordings, capture derivatives, QR/training sprite inputs, all 152 selected narration WAVs, transcripts and loudness measurements. Media and finished video are ignored in Git. Rebuilding from the selected WAVs requires no model download or voice-profile access.

The project uses `.venv-align` for Pillow, qrcode, NumPy, soundfile, Whisper and OpenCC. The sibling media repository's `.conda` runtime, CosyVoice3 weights and private Louise profiles are needed only to generate new takes (`fal01:voice:en` / `zh`). Synthesis uses at most two CPU processes with three Torch threads each. Cached English/Chinese text-normalizer FSTs are required; synthesis does not fetch unrelated language packs. Changed lines require a new `--take` and explicit selection before `fal01:voice:select` copies them into portable inputs.

`fal01:prepare` rebuilds curriculum inputs, QR/training sprites and the estimated silent-review timeline. Follow it with `fal01:timeline:voiced` before rebuilding the narrated delivery. `fal01:visuals` alone refreshes the QR, crop and sprites. To recapture the browser, serve the sibling curriculum with `python3 -m http.server 8149 --bind 127.0.0.1 --directory ../lucas-academy-ai`, then run `npm run fal01:capture`. Capture uses installed Chrome and the bundled Playwright runtime; `PLAYWRIGHT_DIR` can supply another runtime. `npm run fal01:terminal` records only the saved-result viewer in macOS Terminal; it makes no experiment call.

## Still for the owner to decide

1. Cover direction 1, 2 or 3.
2. The title currently uses grammatical **A 1957**, as in the plan.
3. Qwen is currently retained; its small incorrect race result remains unspoken in S1.

The website is confirmed and full narration is authorized. Pace or tone can be adjusted after listening to this version.
