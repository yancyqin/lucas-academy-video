# How Do You Solve a 2×2 Cube? / 二阶魔方怎么还原？

The first film of a cube series (owner, 2026-10-23: "create videos to teach how to solve 2×2, 3×3, 5×5 … let's
create 2×2 to begin with"). A how-to of 4:39: what the cube is and how to read moves,
then the beginner's method in two big parts, shown on one real solve. Every picture comes from Lucas Academy's own
web cube (inception-space-ui `/cube/`, its "Solve it for me" guide), so the film and the page teach the same method
with the same words, and a viewer without a cube can go and do it on the page.

Narration: [docs/cube-2x2/en-edit.md](docs/cube-2x2/en-edit.md) (English, the film's language) ·
[docs/cube-2x2/zh-edit.md](docs/cube-2x2/zh-edit.md) (the Chinese audio track). 28 lines each, same ids.

## 1. Decided

- **v0.3 (owner, 2026-10-25, after v0.2: "前面节奏太慢 太啰嗦，前 1 分钟钩子不够"; the new opening approved first):**
  - **Open on the payoff and a challenge**: the scrambled cube solves itself at about 9×, the count runs to
    3,674,160, "Most people never solve one. By the end of this video, you will."
  - **"You can try it right now, online"**: the real page in a browser window, a cursor pressing "Step by step"
    and "Next move" (the page went live with yancyqin/inception-space-ui#131 on 2026-10-24), and its QR code.
  - The letters in **one line** (R, U, F, a mark, a 2), each move turning as its letter is said; "meet the
    cube" and the colour pairs are gone. **Part 1 starts at 0:42** (was 1:47); the film is 4:39 (was 6:38).
  - **Narration at about 1.25×** ("以前所有视频的经验": 1.0 has been too slow), with the tone set per section:
    a lively hook, brisk teaching, the algorithm lines at 1.05×, the closing question warmer at 1.1×.
  - The ending says "Step by step" (the page's button) instead of "Solve it for me".
- **v0.2 (owner, 2026-10-25, after v0.1; the outline below was approved before the film was made):**
  - **One film, English first, with a Chinese audio track** (the channel has YouTube's multi-language audio).
  - **Labels in English, Chinese smaller underneath.** The cover too: the question in English, the Chinese small.
  - **A card for every move, every time it is used**: the letter, what it means in both languages, and a little
    cube with the turning layer lit and an arrow for the direction.
  - **A smaller cube**, on the left; the cards have a column of their own on the right.
  - **Two big parts**: Part 1, the first layer; Part 2, the top layer, in two steps (a yellow top, then the
    corners). Each part opens with a full-screen chapter card; a bar at the top shows where you are.
  - **The cube page's link and QR code at the start and at the end**: no cube? practise online.
- **Method:** the beginner's layer-by-layer method, exactly as the cube page's guide plays it
  (inception-space-ui `cube/src/solver/beginner.js`):
  1. **The first layer.** A 2×2 has no centres, so the first white corner, held bottom-front-right white side
     down, decides every face's colour; each other corner is held below its spot and the little move
     **R U R′ U′** is repeated until it drops in (one, three or five times).
  2. **The top layer.** A yellow top with Sune (**R U R′ U R U2 R′**, 小鱼公式), held by the rule: one yellow up
     → front-left; none or two → the front-left corner's yellow faces left. Then the corners: headlights (two
     matching top corners on a side) to the back, **R′ F R′ B2 R F′ R′ B2 R2**; no headlights → do it once from
     anywhere; then turn the top.
  These are also the 3×3 beginner's corner steps, which is why the series starts here.
- **Opening and ending** follow the README: the opening asks the film's question with the title card and byline
  ("By Lucas Academy Team"); the last line is an open question that takes "break a messy problem into small steps"
  into the viewer's life and ends on Lucas Academy.
- **Music:** Mozart's Twinkle Variations, K. 265, in the Simone Renzi recording (CC BY 3.0) that Fun Informatics 3
  already uses — same file, same licence, credited in the description. One variation per section, ducked under
  every line (`scripts/music_ducking.py`), ending on the theme's last bars; the same bed under both tracks.

## 2. Outline (approved 2026-10-25)

| Section | What | On screen |
|---|---|---|
| CB00 Opening (0:00) | the cube solves itself; 3.6 million scrambles, "most people never solve one, by the end of this video you will"; try it online now, step by step; the title | 9× solve with the count; **the real page + QR**; title card |
| CB01 The letters (0:27) | R, U, F, a mark, a 2, in one line; "a card shows up every time" | each move turning as it is said, with its card |
| CB02 Part 1 · The first layer | the first corner decides the colours; R U R′ U′ three, five and one times; the stuck-corner tip | chapter card; seen from below; move cards; the step's moves; × count |
| CB03 Part 2 · step 1 · A yellow top | Sune and how to hold the cube; two Sunes | chapter card; Sune card; two top-view rule cards |
| CB04 Part 2 · step 2 · The corners | headlights; the corner algorithm; no headlights; turn the top | headlights card; move cards |
| CB05 Once more | the whole solve at about 3×; the three algorithms | chapter bar; cheat sheet |
| CB06 Ending | no cube yet? scan the code, "Step by step"; the closing question; end card | **the page + QR**; the question; end card with QR |

## 3. Footage

`scripts/cube-2x2/capture.mjs` drives the cube page in headless Chrome (Playwright from Codex's runtime, or
`PLAYWRIGHT_DIR`) on its `?debug` manual clock, so every frame is exactly 1/30 s and nothing depends on the
machine's speed. It needs the inception-space-ui branch with "Solve it for me" served locally (Vite on
`127.0.0.1:8133`, or pass `--url`). Takes, in `public/cube-2x2/footage/` with a `.json` of their events:

| Take | What | Length |
|---|---|---|
| `hero` | the film's scramble, one slow turn round | 20 s |
| `meet` | a solved cube, turned to show its bottom and top | 20 s |
| `letters` | R, U, F, R′, U2 on a solved cube, each pinned to its word in the film (LETTER_WORDS) | 5 s |
| `page` | the real page, panel and all, a drawn cursor pressing "Step by step", "Next move" ×4, "Next step", "Play" | 13 s |
| `notation` | R, R′, U, U′, F, F′, B, B′, U2 (and back), y, y′ (v0.2; no longer in the film) | 18 s |
| `solve` | the whole guided solve of `F′ U′ B′ R D F R2 F D R2 B2 L`, one take | 66 s, 67 moves |

The scramble was picked (by searching the solver's plans) so the one solve shows every rule once, with no detour.
The first layer is filmed from below (pitch −0.72) so the white layer is in view while it is built, with one
extra light from underneath added by the capture only (the page lights from above, so a white bottom reads grey).

## 4. Narration, timeline, film

- `narration.py` turns the edit files into lucas-narrate scripts. Notation is spelled out for the voice (R′ → R撇 /
  R prime; R2 → 「R 两下」 / R two, because 「R 二」 sounds like "R, R"), and sets each line's speed and tone (TONE:
  1.25× and a lively or brisk instruction; 1.05× for the algorithm lines; 1.1× and warmer for the closing question).
  `narrate.py` voices them into `lucas-academy-media/outputs/louise/{en,zh}/cube-2x2-v3/` (v0.3 re-voiced every
  line at the new speed; v1 and v2 takes are kept). `check.py` runs Whisper over every take (`out/cube-2x2/narration-check[.en].json`).
- `build_timeline.py` gives every line the time of the LONGER of its two takes, so both tracks match one picture;
  places the shots (SHOTS, named by the takes' events); lengthens a line wherever its footage would otherwise run
  faster than its limit; builds the music bed, each track's mix and each language's SRT (timed to its own track).
- `src/videos/cube-2x2/Cube2x2Video.tsx` (`Cube2x2`; `Cube2x2ZhTrack` previews the Chinese track): each shot
  plays the footage at its own speed with a short start and stop, then rests on the result while the line
  finishes (a shot longer than its lines is sped up smoothly instead). The QR code (`qr.ts`) is data, made once
  with the `qrcode` npm package and checked by decoding rendered frames at 1080p and 720p with macOS's CoreImage.
- `render.py` renders the picture muted in chunks (concurrency 2) and muxes **both tracks** into
  `out/cube-2x2/delivery/cube-2x2.mp4` (English first and default, Chinese second, language-tagged), plus
  `cube-2x2.zh-track.wav` for YouTube Studio's "Add audio track". `frames.cjs` renders review stills;
  `package.py` checks the film and the Chinese track (length, black frames, −16 LUFS, true peak), renders the
  cover and writes `upload.txt`. Nothing is uploaded or moved.

```
npm run c2:capture                     # footage (dev server with the guide on :8133)
npm run c2:narration                   # narration scripts + cues
../lucas-academy-media/.conda/bin/python scripts/cube-2x2/narrate.py en   # then zh
../lucas-academy-media/.conda/bin/python scripts/cube-2x2/check.py --lang en  # then --lang zh; --model medium to confirm
npm run c2:timeline                    # the timeline, both mixes, both SRTs
python3 scripts/cube-2x2/render.py     # the film with both tracks
python3 scripts/cube-2x2/package.py    # checks, cover, upload text
```

## 5. Publishing

The film sends viewers to is.lucasacademy.org/cube and its "Solve it for me" button, which goes live when
inception-space-ui #131 is merged and deployed: publish after that.

## 6. Narration checks

Every take is Whisper-checked (small, and medium where small was unsure). Retakes, the old takes kept in
`…/replaced/`: zh 反着 → 反过来 (cb01-04, v0.1); R2 read 「R 两下」 and the algorithm lines at 0.85× (v0.1);
en "let it teach you" heard as "tissue" (v0.1, line since replaced); a pause in cb04-04 and a comma in cb02-09
(v0.1); v0.2: en cb01-06 "its card" heard as "cart" → "its card appears"; zh cb01-05 「跟一个二」 heard as
「跟一个 R」 → 「跟一个数字 2」; zh cb03-01 had inserted words, re-voiced. What Whisper still flags is its own
spelling (centerpieces, corner's, "Sune" heard as "soon", which is how it is said; R heard as 二; y heard as 外,
which is how Chinese reads the letter). v0.3 (all lines re-voiced at 1.25×): Whisper small misheard 「数字二」,
「全都朝下」, 「两两」, 「二维码」 and "turn the top"; Whisper medium heard all of them as written. The Chinese voice adds a
natural 「嘿」 before 「顶面全黄了！」 (cb03-06), kept as it fits the line.
