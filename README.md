# Lucas Academy Video Lab

This repo is a small video lab for Lucas Academy lessons.

Two ways to make a video live here, and they are different in kind. The Remotion
compositions below are **deterministic** -- the code draws exactly what it says.
`t2v/` and `comfyui/` are **generative** -- a diffusion model samples pixels from
a sentence. Both run locally on this Mac.

- [`comfyui/`](./comfyui/README.md) -- Wan 2.1 in ComfyUI: the graph, the weights
  it expects, and measured speed/memory on this machine.
- [`t2v/`](./t2v/README.md) -- the same model from the command line, so a clip can
  be scripted or batched. Shares ComfyUI's weights rather than downloading its own.
- [`voice-cover/`](./voice-cover/README.md) -- sing a Suno song in your own voice.
  [SETUP.md](./voice-cover/SETUP.md) builds the two environments and lists the patches
  that Apple Silicon needs; [WORKFLOW.md](./voice-cover/WORKFLOW.md) is the pipeline;
  [VOICE-GUIDE.md](./voice-cover/VOICE-GUIDE.md) covers recording and training a voice.
  Code lives in `rvc/` (Applio, the default) and `svc/` (Seed-VC), tools in `scripts/`.
- [`LYRIC-VIDEO.md`](./LYRIC-VIDEO.md) -- the lyric-video pipeline: forced
  alignment of the lyrics, generated and stock footage through one grade, and the
  failures worth knowing about before repeating any of it.

## Golden Funnel roller coaster

The completed roller-coaster film, its vertical short cut, the three approved
milestone masters, and the child-friendly English voice-over are packaged in
[`roller-coaster-final/`](./roller-coaster-final/README.md).

This is not primarily a demonstration of how quickly AI can output a golden
spiral. It begins with a real child's inquiry: an initially fuzzy idea becomes
clearer through questions and a hand-drawn image. Milestone 2 then becomes
**guided discovery**: an adult participates more actively, using comparisons,
technical vocabulary, and new constraints to help develop the child's idea. A
finished spiral could be generated in one step; the educational value is in
watching the idea become clear through inquiry and guidance.

The delivery README records the original wording of the questions and links
both the untouched uploaded sketch and the mildly enhanced copy used on
screen.

## The real inquiry

The Milestone 1 wording below is intentionally unpolished. These are the
child's questions, not retrospective prompts written after the answer was
known:

> I'm making a roller coaster from formula in xy coordinate plane, any
> interesting formula suggestions?

> can we have something make a loop?

> something like this

![Original pencil spiral uploaded with “something like this”](public/images/roller-coaster/original-sketch-source.png)

The idea then moved from 2D into 3D:

> 3d xyz plane like a funal shape spiraling down

Milestone 2 is collaborative guided discovery. An adult participated heavily,
using later results to introduce and compare more exact requirements: one
ribbon-like `Surface`, descending along the Y-axis, ending at `(0, 0, 0)`, and
contracting faster than a funnel but slower than a golden spiral. These
technical prompts should not all be attributed to the child. Only after that
exploration came the implementation request:

> Go ahead make it a roller coaster

The [complete source record](./roller-coaster-final/README.md#original-questions-and-source-image)
preserves the intermediate questions, the Möbius reference formula, the
funnel-versus-golden comparison, and links to both versions of the drawing.

- `final-long.mp4` — complete 16:9 film.
- `final-short-vertical.mp4` — complete 9:16 short.
- `clips/` — the three long-form milestone sources.

Generated review files belong in the ignored `out/` directory and are not
part of the final package.

The first prototype turns the Monkey Republic society simulation into a short
data-backed video. The goal is not to replace coding. It gives students another
way to see the same idea: rules shape society, and beliefs become behavior when
the world rewards them.

## Prototype

- `MonkeySociety`: a short Remotion video showing the same monkeys in two
  worlds: Win-Win Jungle and Dark Forest.
- Data comes from the sibling `snake-lab` repo, using the real Monkey Republic
  `Society` engine and current personality/world settings.
- The visual focuses on the society simulation because that is the part that
  benefits most from video.

## Run

```bash
npm install
npm run data
npm start
```

Render an MP4:

```bash
npm run render
```

The rendered file will be written to `out/monkey-society.mp4`.

## Data Source

`scripts/generate-monkey-data.mjs` imports:

- `../snake-lab/v3-coder/games/monkey-republic/society.js`
- `../snake-lab/v3-coder/public/games/monkey-republic/constants.js`
- `../snake-lab/v3-coder/public/games/monkey-republic/personalities.js`

That keeps the video aligned with the game instead of duplicating a separate
simulation.
