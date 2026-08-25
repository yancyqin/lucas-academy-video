# Lucas Academy Video Lab

This repo is a small video lab for Lucas Academy lessons.

## Golden Funnel roller coaster

The completed roller-coaster film, its vertical short cut, the three approved
milestone masters, and the child-friendly English voice-over are packaged in
[`roller-coaster-final/`](./roller-coaster-final/README.md).

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
