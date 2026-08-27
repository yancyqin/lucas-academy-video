# Lucas Academy Video Lab

This repo is a small video lab for Lucas Academy lessons.

## Golden Funnel roller coaster

The completed roller-coaster film, its vertical short cut, the three approved
milestone masters, and the child-friendly English voice-over are packaged in
[`roller-coaster-final/`](./roller-coaster-final/README.md).

This is not primarily a demonstration of how quickly AI can output a golden
spiral. It preserves a real child's inquiry: an initially fuzzy idea becomes
clearer through questions, a hand-drawn image, rejected answers, comparisons,
and new constraints. A finished spiral could be generated in one step; the
educational value is in watching the child discover what to ask for.

The delivery README records the original wording of the questions and links
both the untouched uploaded sketch and the mildly enhanced copy used on
screen.

## The real inquiry

The wording below is intentionally unpolished. These are not retrospective
prompts written after the answer was known:

> I'm making a roller coaster from formula in xy coordinate plane, any
> interesting formula suggestions?

> can we have something make a loop?

> something like this

![Original pencil spiral uploaded with “something like this”](public/images/roller-coaster/original-sketch-source.png)

The idea then moved from 2D into 3D:

> 3d xyz plane like a funal shape spiraling down

The child used later results to discover more exact requirements: it should be
one ribbon-like `Surface`, descend along the Y-axis, end at `(0, 0, 0)`, and
contract faster than a funnel but slower than a golden spiral. Only after that
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
