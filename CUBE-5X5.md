# How Do You Solve a 5×5 Cube? / 五阶魔方怎么还原？

The cube series' second film (owner, 2026-10-25: "做一个5阶魔方的吧"), made like the 2×2 one
([CUBE-2X2.md](CUBE-2X2.md)): one picture, English first, with a Chinese audio track; every picture from Lucas
Academy's own web cube (inception-space-ui `/cube/`, its "Step by step" guide), so the film and the page teach the
same method with the same words. **v0.1, 8:11** (2026-10-26): `out/cube-5x5/delivery/` passes the delivery checks
(no black frames; English and Chinese both −16.0 LUFS, true peak −1.4 / −1.6 dBTP; streams eng + chi).

Narration: [docs/cube-5x5/en-edit.md](docs/cube-5x5/en-edit.md) (English, the film's language) ·
[docs/cube-5x5/zh-edit.md](docs/cube-5x5/zh-edit.md) (the Chinese audio track). 43 lines each, same ids.

## 1. Decided

- **Outline first** (the owner's rule since the 2×2 film): outline v1 offered (a) a 3×3 film first, (b) the 3×3
  taught inside this one, (c) "follow the page"; the owner chose **(b), "1b 但是下面可以快速跳步骤"**: the 3×3's
  seven steps are taught in full as Part 1, and the bottom chapter bar has a segment for each, so a viewer who
  knows the 3×3 jumps straight to Part 2. Outline v2 (below) was approved ("确认") before any footage.
- **Method: the cage method the page's guide uses** (inception-space-ui `cube/src/solver/big.js`), not reduction:
  1. **The frame** — corners, the middle piece of each edge and the fixed centres move like a 3×3 under outer
     turns, so the frame is solved with the 3×3 beginner's method (`beginner.js`): white cross, white corners
     (R U R′ U′), middle layer (U R U′ R′ U′ F′ U F / U′ L′ U L U F U′ F′), yellow cross (F R U R′ U′ F′),
     yellow face (Sune), yellow corners (headlights, R′ F R′ B2 R F′ R′ B2 R2), yellow edges
     (R U′ R U R U R U′ R′ U′ R2).
  2. **The edges** — an edge-parity check first (an odd order of the wings is evened out by one inner quarter
     turn, because three-way swaps cannot fix a single swap), then the 24 wings with commutators [A, B] =
     A B A′ B′, each with at most a few set-up turns.
  3. **The centres** — face by face with block commutators that move a row of centre pieces at once; the last
     face finishes by itself.
  No parity algorithms to learn, the commutator is an idea worth teaching for itself, and the page's "Step by step"
  plays exactly this.
- **Format, as the 2×2 film** (owner, 2026-10-25): English labels with small Chinese; a move card every time a move
  is used (now with inner layers: 2R, M, 2-3Rw, drawn on a little 5×5); the cube small on the left; big chapters;
  the link and QR code at the start and the end; a strong opening (the payoff and a dare); narration at about 1.25×
  with the tone set per section; the bottom chapter bar segmented like YouTube's; the series' hashtags (with #5x5
  for #2x2); the cover with the "Free online cube included" badge.
- **Showing the structure**: the solve take lights the cube by part. While the frame is built, the wings and
  centres step back (dark, still stickers); in Part 2 the centres stay back and each commutator's three wings
  glow; in Part 3 each commutator's centre pieces glow. On the commutator steps the step strip groups the moves
  as set-up · A · B · A′ · B′ · undo.

## 2. Outline v2 (approved 2026-10-25)

| # | Chapter (the bar's segment) | What |
|---|---|---|
| 0 | Challenge | the 5×5 solves itself; the 75-digit number written out; "most people never solve one, by the end of this video you will"; try it online now + QR; the title; "Already know the 3×3? Skip to Part 2" with an arrow to the bar |
| 1 | The idea | a 3×3 hides inside: the frame, the edge wings, the centre pieces, each lit in turn; three parts |
| 2 | Letters | R, U, F, a mark, a 2; a number in front picks an inner layer (2R); M |
| 3–9 | Part 1 · The frame | white cross, white corners, middle layer, yellow cross, yellow face, yellow corners, yellow edges: each rule and its algorithm, one example at about 1×, the rest faster |
| 10 | Part 2 · Edges | the commutator A B A′ B′; the parity check (2R′); one commutator slowly, its three wings glowing; the rest fast with a counter |
| 11 | Part 3 · Centres | the same idea, a row at a time; one slowly; the faces fast; blue finishes by itself |
| 12 | Replay & try online | the whole solve fast; the link and QR; the closing question |

## 3. Footage

`scripts/cube-2x2/capture.mjs --film cube-5x5` (the 2×2 film's capture, given a FILMS table: size, scramble,
letters, stages filmed from below). Takes in `public/cube-5x5/footage/`:

| Take | What |
|---|---|
| `hero` | the film's scramble, one slow turn round |
| `meet` | a solved cube, turned to show its bottom and top |
| `anatomy` | a solved cube turning, its kinds lit in turn (frame 26, wings 24, centres 48), the others dimmed |
| `letters` | R, U, F, R′, U2, 2R, M, each pinned to its word (LETTER_WORDS, from `letter_words.py`) |
| `page` | the real page on a 5×5: "Step by step", "Next move" ×4, "Next step", "Play" |
| `solve` | the whole guided solve, one take: 408 s, 471 moves |

The scramble (60 moves, in capture.mjs) was picked by searching the solver's plans for one solve that shows every
rule: one white edge already home; corners three, three, five and one times; middle edges right, left, left; a
yellow L then a line; Sune on two, none, one; no headlights, then headlights; one finished side; the wings in an odd
order (one 2R′); 18 edge commutators, some with set-ups; centres in five faces (yellow 4 steps, white 3, red 4,
green 3, orange 3), blue last by itself. The cross and white corners are filmed from below; each centre stage looks
at the face it fills (the top higher, the bottom from below, the back from behind). Dimming: the page's lighting and
tone mapping keep a sticker's colour readable down to about 0.3 of its colour, so "back" is 0.05 and "aside" 0.45.

## 4. Narration, timeline, film

The 2×2 film's tools, generalised by a film argument, with the 5×5's own settings in `scripts/cube-5x5/`:

- `scripts/cube-5x5/narration.py`: the 2×2's, plus the big cube's notation (2L read "two L" / 「第二层 L」, since
  「二」 next to a letter is heard as R); the hook lines lively, the eight algorithm lines at 1.05×, the closing
  question at 1.1×, the rest at 1.25×.
- `scripts/cube-2x2/narrate.py en|zh cube-5x5` → `lucas-academy-media/outputs/louise/{en,zh}/cube-5x5-v1/`;
  `scripts/cube-2x2/check.py --film cube-5x5 --lang en|zh` (Whisper).
- `scripts/cube-5x5/build_timeline.py`: the 2×2's builder with this film's shots (named by the solve take's
  stages, steps and moves), holds, letter timings and music (the K. 265 variations in order, as many per section
  as it needs).
- `src/videos/cube-5x5/Cube5x5Video.tsx` (`Cube5x5`, `Cube5x5Cover`), built on the 2×2 composition's exported
  pieces: the page's formatMove (wide and inner layers), a 5×5 move icon, the stage tag (part, step of 7, edge
  counter, fast-forward speed), the commutator step strip, the 75-digit number, the piece-kind face map, the
  three-part card, the 3×3 rule cards and the centres checklist.
- `scripts/cube-2x2/render.py --film cube-5x5`, `scripts/cube-2x2/frames.cjs en --film cube-5x5`,
  `scripts/cube-5x5/package.py`.

```
node scripts/cube-2x2/capture.mjs --film cube-5x5          # footage (dev server with the guide on :8133)
npm run c5:narration
../lucas-academy-media/.conda/bin/python scripts/cube-2x2/narrate.py en cube-5x5    # then zh
../lucas-academy-media/.conda/bin/python scripts/cube-2x2/check.py --film cube-5x5 --lang en   # then zh
npm run c5:timeline
npm run c5:render
python3 scripts/cube-5x5/package.py
```

## 5. Publishing

The page's guide is live (inception-space-ui #131, 2026-10-24). Nothing is uploaded from here.

## 6. Narration checks

All 86 takes Whisper-checked (small, then medium wherever small was unsure). Retakes, the old takes kept in
`…/cube-5x5-v1/replaced/`:

- **English:** cf04-03 "four white corners" heard as "four wide corners" (re-voiced); cf07-03 "Here, two" →
  "Ear, two" (now "We start with two"); cf08-02 "anywhere: R′" → "bar prime" (a full stop before the algorithm);
  cf09-02 "solved: it looks" → "soft, but looks" (a full stop); cf10-03 "the guide checks" → "the guy checks"
  (now "the web cube checks this"); cf11-02 "A turns" → "It turns" (now "Move A … move B").
- **Chinese:** cf01-02 「每条」 → 「哪条」 and cf01-03 「一共」 → 「提供」 (re-voiced); cf02-02 「R 前面写个数字二」
  → 「2 前面」 (R and 二 sound alike: the voice now says 「比如右边数过来的第二层」 while the card shows 2R); cf03-04
  ran on into invented words after the line (re-voiced, a little longer); cf09-01's eleven-move algorithm ran
  together (re-voiced at 0.95×); cf11-02 「从底面搬到顶面」 → 「底面…底面」 (now 「从下面搬到上面」).
- What Whisper still flags is its own spelling or homophones: "webcube", "memorize", "every one" as "everyone";
  「角」 as 「脚」, 「阶」 as 「接」, 「棱」 as 「轮」, 「一下」 as 「以下」; "Sune" as "soon" in small (medium hears Sune);
  and the slower pace of the algorithm lines, which is set on purpose.
