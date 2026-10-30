# How Do You Solve a 5×5 Cube? — narration (v0.1 · 2026-10-25 · outline v2 approved by Yancy)

Cube series, episode 2. By Lucas Academy Team. Plan: [CUBE-5X5.md](../../CUBE-5X5.md).

**One film, English first, with a Chinese audio track**, like the 2×2 film. This file is the English narration;
[zh-edit.md](zh-edit.md) is the Chinese track, with the same cue ids, the same examples and the same pictures.
Each line's time on screen fits the longer of the two takes.

One line: **a 75-digit number of scrambles, and a 3×3 hiding inside: the frame, then the edges, then the centres.**

Outline v2 (Yancy 2026-10-25, "1b 但是下面可以快速跳步骤"): the 3×3's seven steps are taught in full inside this
film (Part 1), and the bottom chapter bar has a segment for each of them, so a viewer who knows the 3×3 jumps
straight to Part 2. The method is the cage method the web cube's "Step by step" uses: the 3×3 frame first,
then the edges with commutators, then the centres; no parity algorithms to learn.

Every example is this film's own scramble (CUBE-5X5.md §3), solved by the web cube's guide: the white–orange edge
is already home; the white–green–orange corner takes three goes; two middle edges go left; the Sune cases come in
the order two, none, one; there are no headlights at first; the wings have the odd order (one 2R′); the first
edge commutator is [2L, F′ R′ F]; the first centre commutator moves two yellow pieces at once.

Reading vs captions (the voice's spellings go in narration.py SPOKEN and notation()):
- Notation: R′ is read "R prime", U2 "U two"; a number in front picks a layer, 2L is read "two L".
- The lines that read a whole algorithm are voiced a little slower (narration.py ALGORITHM).
- v0.1 takes (Whisper small and medium agreed): cf04-03's "four white corners" came out "four wide corners"
  (re-voiced); cf07-03's "Here, two" came out "Ear, two" (now "We start with two"); cf08-02's first R after
  "anywhere:" ran into it ("bar prime": the voice reads a full stop there); cf09-02's "solved: it looks" came out
  "soft, but looks" (read with a full stop); cf10-03's "the guide checks" was "the guy checks" (now "the web cube
  checks this"); cf11-02's "A turns" was heard "It turns" (now "Move A … move B").

Tone: as the 2×2 film (narration.py TONE), about 1.25×: a lively hook, brisk teaching, the algorithms clear,
a warmer closing question.

## CF00 · Opening: the challenge

- cf00-01 | A seventy-five-digit number: that's how many ways this cube can be scrambled. Most people never solve one. By the end of this video, <strong>you will</strong>.
  Picture: the scrambled 5×5 solves itself at high speed; the 75-digit number writes itself out
- cf00-02 | And you can try it right now, online. Scan the code: our free web cube has a step-by-step guide that walks you through every move.
  Picture: the real page on a 5×5, "Step by step" and "Next move" pressed; the link and QR code beside it
- cf00-03 | So, let's go: <strong>how do you solve a five-by-five cube?</strong>
  Picture: title card
- cf00-04 | Already know the three-by-three? Skip straight to Part 2 with the bar below.
  Picture: an arrow down to the Part 2 segment of the chapter bar

## CF01 · The idea

- cf01-01 | Here's the secret: inside every five-by-five hides a three-by-three. The corners, the middle piece of each edge, and the centre of each face: that's the <strong>frame</strong>, and it turns just like a three-by-three.
  Picture: the anatomy take, the frame lit
- cf01-02 | Beside each middle edge piece sit two <strong>edge wings</strong>: twenty-four in all.
- cf01-03 | And around each face's centre, eight <strong>centre pieces</strong>: forty-eight in all.
- cf01-04 | So we solve it in three parts: the frame, like a three-by-three; then the edges; then the centres.

## CF02 · The letters

- cf02-01 | Moves have letters: R is the right face, U the top, F the front. Turn it clockwise as you look at it; a little mark means the other way, and a 2 after it means twice.
  Picture: R, U, F, R′, U2, each with its card
- cf02-02 | A big cube has inner layers, too. A number in front picks the layer: 2R is the second layer from the right, and M is the middle one. No need to memorise: a card shows up every time.
  Picture: 2R, M, each with its card

## CF03 · Part one: the frame — the white cross

- cf03-01 | Part one: the frame. Turn only the outside faces, and the frame moves just like a three-by-three. The wings and centres step back for now; we'll come back for them.
  Picture: chapter card "Part 1 · The Frame"; the wings and centres dimmed
- cf03-02 | Step one: a white cross. Hold the cube with the white centre on the bottom.
- cf03-03 | Bring each white edge down beside its own centre: white and green goes next to green. No algorithm here, just a few turns, and the guide shows every one.
- cf03-04 | One was home already. Four white edges: a white cross!

## CF04 · The white corners

- cf04-01 | Step two: the white corners. Turn the top to put a white corner right above its spot, then do one little move: <strong>R U R′ U′</strong>. Repeat it until the corner drops in, white facing down.
- cf04-02 | This one, white, green and orange, takes three times.
- cf04-03 | The rest work the same way: turn the cube so the spot is at the front right, and repeat. Three times, five times, once. Four white corners!

## CF05 · The middle layer

- cf05-01 | Step three: the middle layer. Find a top edge with no yellow, and turn the top until its front colour stands over its own centre.
- cf05-02 | Its top colour shows which way it goes. To the right: <strong>U R U′ R′ U′ F′ U F</strong>.
- cf05-03 | To the left, the mirror image: <strong>U′ L′ U L U F U′ F′</strong>. Two go left, and the middle layer is done.

## CF06 · The yellow cross

- cf06-01 | Step four: a yellow cross on top, with one algorithm: <strong>F R U R′ U′ F′</strong>. Just a yellow dot? Do it once, and an L appears.
- cf06-02 | A yellow L: turn the top so its arms point to the back and the left, and do it. Now it's a line: hold it left to right, and once more. A yellow cross!

## CF07 · The yellow face

- cf07-01 | Step five: the whole top yellow, with <strong>Sune</strong>: R U R′ U R U2 R′.
- cf07-02 | If exactly one corner shows yellow on top, turn it to the front left. If none do, or two do, turn the top until the front-left corner's yellow faces left. Then Sune.
- cf07-03 | We start with two: Sune. Now none: Sune again. Now just one: turn it to the front left, and one last Sune… the top is all yellow!

## CF08 · The yellow corners

- cf08-01 | Step six: the yellow corners. Look for <strong>headlights</strong>: two top corners on one side that match.
- cf08-02 | None yet? Do the corner algorithm once, from anywhere: <strong>R′ F R′ B2 R F′ R′ B2 R2</strong>.
- cf08-03 | Now there are headlights. Hold them at the back, and do it again. Turn the top to line it up… and the corners are done.

## CF09 · The yellow edges

- cf09-01 | The frame's last step: the yellow edges. Hold a finished side at the back, and do the edge algorithm: <strong>R U′ R U R U R U′ R′ U′ R2</strong>. No finished side? Do it once from anywhere first.
- cf09-02 | The frame is solved: it looks just like a three-by-three! Only the wings and the centres are left.

## CF10 · Part two: the edges

- cf10-01 | Part two: the edges. The wings come back into the light, and here's the big new idea: the <strong>commutator</strong>.
  Picture: chapter card "Part 2 · The Edges"
- cf10-02 | Do a move A, then a move B. Undo A, then undo B. Almost everything goes back where it was, and only three pieces trade places.
  Picture: the commutator card, A B A′ B′
- cf10-03 | But first, one check. Three-way swaps can never fix two pieces that are simply swapped. So if the wings are in an odd order, one quarter turn of an inner layer, 2R′, makes it even. The web cube checks this for you.
- cf10-04 | Now a commutator, slowly. A is 2L, an inner layer. B is F′ R′ F. Then undo A, and undo B.
- cf10-05 | Watch the glowing pieces: three wings traded places, and the yellow and red edge piece is home. Everything else is back where it was.
- cf10-06 | Sometimes a set-up turn lines the pieces up first, and is undone at the end. Twenty-four wings, one commutator at a time… and all the edges are done!

## CF11 · Part three: the centres

- cf11-01 | Part three: the centres. The same idea, but now a commutator can move a whole row of centre pieces at once.
  Picture: chapter card "Part 3 · The Centres"
- cf11-02 | Here, two yellow pieces go from the bottom to the top in one go. Move A turns two inner layers to bring them up; move B, U 2L U′, takes them in. Then undo A, and undo B.
- cf11-03 | Yellow first, then white on the bottom, then red, green and orange. The last face, blue, finishes all by itself.
- cf11-04 | And that's it: a solved five-by-five!

## CF12 · Once more, and the online cube

- cf12-01 | Once more, all the way through: the frame, like a three-by-three; then the edges; then the centres.
- cf12-02 | No cube yet? Scan the code, press "Step by step", and the web cube walks you through every move.
  Picture: the page and its QR code again
- cf12-03 | A seventy-five-digit number of scrambles, and one plan solves every one: find the small cube hiding inside the big one. So: is there something around you that looks huge and hard, with a smaller, easier puzzle hiding inside? That's what we learn and think about together at Lucas Academy.
