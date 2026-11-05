# Family AI Lab 01 — review delivery

The owner's latest decisions override the earlier two-film plan: **one picture, English labels, English default, separate Chinese audio and subtitles**. At this review stage narration is deferred. The single MP4 has two selectable subtitle tracks, with English selected by default. Subtitles are not burned into the picture. The two caption-preview compositions are inspection tools for the same common timeline, not separate film deliveries.

## Delivery

- Review: `out/family-ai-lab-01/review/family-ai-lab-01.review.mp4`, 1920×1080, 30 fps, approximately 7:15, no audio.
- External captions: `out/family-ai-lab-01/review/en.srt`, `out/family-ai-lab-01/review/zh-Hans.srt`.
- Covers: `out/family-ai-lab-01/cover/design-{1,2,3}.{en,zh}.png`, 1280×720. `all-designs.png` is the six-cover contact sheet.
- Scripts: [English](en-script.md), [Chinese](zh-script.md), common sentence IDs `fa01-NN-MM`.
- Verification: `out/family-ai-lab-01/review/verification.json` and [committed check result](verification.json).
- QuickTime Player: View → Subtitles → English / Chinese selects the independent caption track. Both languages were checked visibly in the native player.

Cover directions: 1 — brass photocell array; 2 — paper card and circuits; 3 — green CRT. Generated backgrounds contain no text. Every title, model name and number is typeset by code. Bilingual cover questions and the surrounding comparison copy follow the film-specific owner plan, which overrides the general repository cover rules. No series ribbon or diagonal band.

## Experiment selection

The owner explicitly retained the original complete round after seeing the later Claude timing change. No benchmarks or model calls were made during production. `reruns/` is not read by the build or compositions. [Selected-data hashes](selected-data.json) freeze the four original JSON inputs. The native terminal clip shows the saved original files, clearly labelled as records; it is not presented as a new model run.

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

From the existing checkout, without a worktree:

```sh
npm run fal01:prepare
npm run fal01:cover
node scripts/family-ai-lab-01/render.cjs --stills
npm run fal01:render
npm run fal01:check
npm run fal01:backup
```

Restore the local media backup first on another checkout: `python3 ../lucas-academy-video-data/family-ai-lab-01/restore.py "$PWD"`. It verifies SHA256SUMS before copying and refuses differing destination files. Backup includes the three Muse originals, three generated backgrounds, curriculum snapshots, native recordings and capture derivatives. Media and finished video are ignored in Git.

To recapture the browser rather than restore it, serve the sibling curriculum with `python3 -m http.server 8149 --bind 127.0.0.1 --directory ../lucas-academy-ai`, then run `npm run fal01:capture`. The capture script uses installed Chrome and the bundled Playwright runtime; `PLAYWRIGHT_DIR` can supply another runtime. A missing Playwright FFmpeg binary can be installed through its `playwright install ffmpeg` command. `python3 scripts/family-ai-lab-01/record_terminal.py` recaptures the saved-result viewer in macOS Terminal, without rerunning an experiment. Cover rendering uses Pillow in `.venv-align`.

## Still for the owner to decide

1. Cover direction 1, 2 or 3.
2. Website address; review says “Website coming soon”.
3. The title currently uses grammatical **A 1957**, as in the plan.
4. Qwen is currently retained; its small incorrect race result remains unspoken in S1.
5. After picture/script approval, try Louise's pace and tone for each language, then align the two independent audio tracks to the common picture. English will be the default audio track. No voice has been generated yet.
