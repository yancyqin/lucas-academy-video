# How Do You Solve a 2×2 Cube? — narration (v0.3 · 2026-10-25 · new opening approved by Yancy)

Cube series, episode 1. By Lucas Academy Team. Plan: [CUBE-2X2.md](../../CUBE-2X2.md).

**One film, English first, with a Chinese audio track** (Yancy, 2026-10-25). This file is the English narration;
[zh-edit.md](zh-edit.md) is the Chinese track, with the same cue ids, the same examples and the same pictures. Each
line's time on screen fits the longer of the two takes, so both tracks match the picture.

One line: **3.6 million scrambles, one little move and two algorithms, two layers.**

v0.2 (Yancy 2026-10-25): English first with a Chinese track; English labels with small Chinese under them; a card
for every move each time it is used; a smaller cube; two big parts (the first layer, then the top layer in two
steps); the cube page's link and QR code at the start and at the end ("no cube? practise online").
v0.3 (Yancy 2026-10-25): the opening was too slow and wordy and its hook too weak. It now opens on the payoff and a
challenge ("Most people never solve one. By the end of this video, you will."), says it can be tried online right now
with the page's "Step by step" guide, and gets the letters into one line: Part 1 starts at about 0:45, not 1:47.
The voice runs at about 1.25× (1.0 has been too slow in every film), with the tone set per section (narration.py
TONE): a lively hook, brisk teaching, the algorithm lines a little slower, a warmer closing question.

Reading vs captions (the voice's spellings go in SPOKEN):
- Notation: R′ is read "R prime", U2 "U two", B2 "B two", R2 "R two".
- The three lines that read a whole algorithm (cb02-05, cb03-02, cb04-03) are voiced at 0.85× so every letter is heard.
- v0.1 takes: cb04-04's "do the algorithm once" ran together ("duty algorithm wants"), so the voice reads it with
  a pause; cb02-09's "lift it out" lost its "it" until it got a comma.
- v0.2 takes: cb01-06's "its card shows up" was heard as "its cart" (both Whisper models): now "its card appears".

Overall tone: curious, unhurried, discovering together with a child (README default, louise/en).

## CB00 · Opening: the challenge

- cb00-01 | Three and a half million ways to scramble this cube. Most people never solve one. By the end of this video, <strong>you will</strong>.
  Picture: the scrambled cube solves itself at high speed; the count runs up to 3,674,160
- cb00-02 | And you can try it right now, online. Scan the code: our free web cube has a step-by-step guide that walks you through every move.
  Picture: the real page, "Step by step" and "Next move" pressed; the link and QR code beside it
- cb00-03 | So, let's go: <strong>how do you solve a two-by-two cube?</strong>
  Picture: title card

## CB01 · The letters

- cb01-01 | Moves have letters: R is the right face, U the top, F the front. Turn it clockwise as you look at it; a little mark means the other way, and a 2 means twice. No need to memorise: a card shows up every time.
  Picture: R, U, F, R′, U2, each with its card

## CB02 · Part one: the first layer

- cb02-01 | Part one: the first layer. All the white faces down, and the side colours of the four corners matching.
  Picture: chapter card "Layer 1 · The White Layer"; the camera looks from below
- cb02-02 | A two-by-two has no centres, so we choose the first corner ourselves. Pick a white corner and hold it at the bottom front right, white facing down.
- cb02-03 | Ours is white, green and orange. From now on, the front is green and the right is orange: this one corner decides the colour of every side.
- cb02-04 | The next corner is white, green and red. First, turn the whole cube so that its spot comes to the bottom front right.
- cb02-05 | Now, just one little move: <strong>R U R′ U′</strong>. If once isn't enough, do it again.
- cb02-06 | On the third time, it drops right in, white facing down!
- cb02-07 | The next one, white, red and blue, is up on top. Turn the top to put it right above its spot, then R U R′ U′ again. This one takes five times.
- cb02-08 | The last one, white, blue and orange, needs only one. The first layer is done!
- cb02-09 | A tip: if a white corner is stuck in the bottom in the wrong spot, turn it to the front right and do R U R′ once to lift it out first.

## CB03 · Part two: the top layer — step one, a yellow top

- cb03-01 | Part two: the top layer. White is on the bottom, so yellow is on top. This part has two steps. Step one: make the whole top yellow.
  Picture: chapter card "Layer 2 · The Top Layer"; the camera rises above
- cb03-02 | This step uses our first algorithm. It's called <strong>Sune</strong>: R U R′ U R U2 R′.
- cb03-03 | How do you hold the cube? If exactly one top corner shows yellow, turn the top so it sits at the front left.
- cb03-04 | If none do, or two do, turn the top until the front-left corner's yellow faces left. Then do Sune.
- cb03-05 | Here, none of the top is yellow. Turn the top so the front-left corner's yellow faces left, and do Sune once.
- cb03-06 | Now exactly one corner shows yellow, and it's already at the front left. One more Sune… and the whole top is yellow!

## CB04 · Part two: the top layer — step two, the corners

- cb04-01 | Step two: swap the four top corners into their right places.
- cb04-02 | Look at the sides. Is there a side whose two top corners are the same colour? They look like a pair of <strong>headlights</strong>.
- cb04-03 | Turn the headlights to the back, and do the second algorithm: R′ F R′ B2 R F′ R′ B2 R2.
- cb04-04 | If no side has headlights, do the algorithm once from anywhere, and they'll appear.
- cb04-05 | Finally, turn the top to line it up with the bottom… and it's solved!

## CB05 · Once more

- cb05-01 | Once more, all the way through. Part one, the first layer. Part two, the top layer: a yellow top, then the corners.
- cb05-02 | One little move and two algorithms: that's all it takes.

## CB06 · Ending

- cb06-01 | No cube yet? Scan the code, press "Step by step", and the online cube walks you through every move.
  Picture: the page and its QR code again
- cb06-02 | More than three and a half million scrambles, and the same three steps solve every one. So: is there something around you that looks messy and hard, that you could break into small steps and do one at a time? That's what we learn and think about together at Lucas Academy.
