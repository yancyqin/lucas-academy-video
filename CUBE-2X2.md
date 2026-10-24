# 二阶魔方怎么还原？ / How Do You Solve a 2×2 Cube?

The first film of a cube series (owner, 2026-10-23: "create videos to teach how to solve 2×2, 3×3, 5×5 … let's
create 2×2 to begin with", Chinese and English). A how-to about five minutes long: what the cube is, how to read
moves, then the beginner's method in three steps, shown on one real solve. Every picture comes from Lucas
Academy's own web cube (inception-space-ui `/cube/`, its new "Solve it for me" guide), so the film and the page
teach the same method with the same words, and a viewer can go and do it on the page.

Narration scripts: [docs/cube-2x2/zh-edit.md](docs/cube-2x2/zh-edit.md) ·
[docs/cube-2x2/en-edit.md](docs/cube-2x2/en-edit.md) (31 lines each, same ids, same examples).

## 1. Decided

- **Languages:** two films, Chinese and English, Louise's voices with the README defaults (owner, 2026-10-23).
- **Method:** the beginner's layer-by-layer method, exactly as the cube page's guide plays it
  (inception-space-ui `cube/src/solver/beginner.js`):
  1. **The white layer.** A 2×2 has no centres, so the first white corner, held bottom-front-right white side
     down, decides every face's colour; each other corner is held below its spot and the little move
     **R U R′ U′** is repeated until it drops in (one, three or five times).
  2. **A yellow top.** Sune (**R U R′ U R U2 R′**, called 小鱼公式 in Chinese), held by the rule: one yellow up →
     front-left; none or two → the front-left corner's yellow faces left.
  3. **The last corners.** Headlights (two matching top corners on a side) to the back, then
     **R′ F R′ B2 R F′ R′ B2 R2**; no headlights → do it once from anywhere. Then turn the top.
  These are also the 3×3 beginner's corner steps, which is why the series starts here.
- **Opening and ending** follow the README: the opening asks the film's question with the title card and byline;
  the last line is an open question that takes "break a messy problem into small steps" into the viewer's life
  and ends on Lucas Academy.
- **Music:** Mozart's Twinkle Variations, K. 265, in the Simone Renzi recording (CC BY 3.0) that Fun
  Informatics 3 already uses — same file, same licence, credited in the description. One variation per section,
  ducked under every line (`scripts/music_ducking.py`), ending on the theme's last bars.

## 2. Footage

`scripts/cube-2x2/capture.mjs` drives the cube page in headless Chrome (Playwright from Codex's runtime, or
`PLAYWRIGHT_DIR`) on its `?debug` manual clock, so every frame is exactly 1/30 s and nothing depends on the
machine's speed. It needs the inception-space-ui branch with "Solve it for me" served locally (Vite on
`127.0.0.1:8133`, or pass `--url`). Takes, in `public/cube-2x2/footage/` with a `.json` of their events:

| Take | What | Length |
|---|---|---|
| `hero` | the film's scramble, one slow turn round | 20 s |
| `meet` | a solved cube, turned to show its bottom and top | 20 s |
| `notation` | R, R′, U, U′, R2 (and back), y, y′ on a solved cube | 13 s |
| `solve` | the whole guided solve of `F′ U′ B′ R D F R2 F D R2 B2 L`, one take | 66 s, 67 moves |

The scramble was picked (by searching the solver's plans) so the one solve shows every rule once, with no detour:
the first layer's corners take R U R′ U′ three, five and one times; the yellow top needs two Sunes, the first
from "no yellow up", the second from "one yellow up"; the last corners have headlights. The first layer is
filmed from below (pitch −0.72) so the white layer is in view while it is built, with one extra light from
underneath added by the capture only (the page lights from above, so a white bottom reads grey).

## 3. Narration

`scripts/cube-2x2/narration.py` turns the edit files into lucas-narrate scripts. Notation is spelled out for the
voice (R′ → R撇 / R prime, U2 → U二 / U two, each move separated so every letter is heard); captions keep the
notation. `narrate.py` voices them into `lucas-academy-media/outputs/louise/{zh,en}/cube-2x2-v1/`, and
`check.py` runs Whisper over every take (`out/cube-2x2/narration-check[.en].json`).

## 4. The film

- `scripts/cube-2x2/build_timeline.py` places the lines, decides which stretch of which take plays under each
  (SHOTS, named by the takes' events, so a re-recorded take moves the shots with it), lengthens a line wherever
  its footage would otherwise have to run faster than its limit, builds the music bed and the two SRTs per film.
- `src/videos/cube-2x2/Cube2x2Video.tsx` (`Cube2x2Zh`, `Cube2x2En`): each shot plays at the footage's own
  speed with a short start and stop, then rests on the result while the line finishes (a shot longer than its
  lines is sped up smoothly instead; the replay runs at about 2.5×). Over the picture: the three stages, the
  step's moves with the turning one lit, the algorithm's name, which time round the little move is on, the
  notation letters, the colour pairs, the first corner's colours, the Sune rule as two top views, headlights,
  the page's address, and the closing question. The cube sits left so all of that has a column of its own.
- `scripts/cube-2x2/render.py zh|en` renders in chunks at concurrency 2 and muxes the mix
  (`out/cube-2x2/delivery/cube-2x2.LANG.mp4`); `frames.cjs` renders review stills;
  `package.py` checks the films (length, black frames, −16 LUFS, true peak), renders the covers
  (`Cube2x2CoverZh/En`, one language each) and writes the upload texts. Nothing is uploaded or moved.

```
npm run c2:capture                     # footage (dev server with the guide on :8133)
npm run c2:narration                   # narration scripts + cues + translations
../lucas-academy-media/.conda/bin/python scripts/cube-2x2/narrate.py zh   # then en
../lucas-academy-media/.conda/bin/python scripts/cube-2x2/check.py --lang zh  # then --lang en
npm run c2:timeline                    # timelines, mixes, SRTs
python3 scripts/cube-2x2/render.py zh  # then en
python3 scripts/cube-2x2/package.py
```

## 5. For the owner to decide

- **The cover question.** Working title 「二阶魔方怎么还原？」 / "How Do You Solve a 2×2 Cube?". Other options:
  「只用两个公式，能还原二阶魔方吗？」 / "Can Two Algorithms Solve a 2×2 Cube?";
  「三百六十七万种打乱，怎么都能还原？」 / "3.6 Million Scrambles: Can You Solve Them All?".
- **Byline and series.** The cards say "By Lucas Academy Team" (README default); the series has no name yet.
- **When to publish.** The film sends viewers to is.lucasacademy.org/cube and its "Solve it for me" button, which
  goes live when the inception-space-ui cube PR is merged and deployed.

## 6. v0.1 (2026-10-23): rendered, waiting for the owner's review

- `out/cube-2x2/delivery/`: `cube-2x2.zh.mp4` (5:54) and `cube-2x2.en.mp4` (5:30), 1920×1080, 30 fps,
  −16.0 LUFS, true peak −2.0 / −1.5 dBTP, no black frames (`delivery-check.{zh,en}.json`); two SRTs per film;
  `cover.{zh,en}.jpg` (1280×720); `upload.{zh,en}.txt` (title, description with chapters and the music credit,
  tags, upload settings).
- Narration: every take Whisper-checked. Retakes, with the old takes kept in `…/cube-2x2-v1/replaced/`:
  zh cb01-04 (反着 → 反过来), cb02-05, cb03-02 and cb04-03 (R2 read 「R 两下」, at 0.85×); en cb02-05,
  cb03-02 and cb04-03 (0.85×), cb02-09 ("lift it out"), cb04-04 (a pause), cb05-02 ("teach you" heard as
  "tissue" → "show you how"). What Whisper still flags is its own spelling (centerpieces, corner's, "Sune"
  heard as "soon", which is how it is said; R heard as 二).
- Working files (`public/cube-2x2/`, the takes, `out/`) are local and gitignored, as for the other films.
