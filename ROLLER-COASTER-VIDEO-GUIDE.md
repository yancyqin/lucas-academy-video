# From a Sketch to a Roller Coaster

## Final video production guide

This document is the editorial source of truth for the Lucas Academy Golden
Funnel video. It explains what the film is trying to say, what each milestone
does, how to record the game, and what the narrator should say.

All on-screen copy and narration are in English. The language should be easy
for a child around age ten to twelve to understand. The mathematics can look
advanced on screen, but the voice-over always explains the simple idea behind
it.

## The one-sentence story

A child who does not yet know the words “golden spiral” begins with real
questions and a rough pencil sketch; an adult then supports guided discovery
through comparisons and mathematical constraints until the idea is precise
enough to become a Surface and a rideable world.

## The central idea

The film is about inquiry, not answer generation. If the final object were the
only goal, the first prompt could request a golden spiral and skip directly to
the result. The preserved conversation is valuable because the child's goal
does not arrive fully formed. In Milestone 1, the child asks and draws. In
Milestone 2, an adult participates substantially, helping compare outputs,
introduce useful vocabulary, and formulate constraints. This is guided
discovery, not a claim that every technical prompt came from the child.

The AI makes possibilities visible quickly. The child supplies the initiating
idea, questions, sketch, and desired experience. The adult guides the middle
stage through comparison and mathematical framing. The narration must preserve
all three roles accurately. The source prompts and both versions of the
uploaded drawing are recorded in
[`roller-coaster-final/README.md`](./roller-coaster-final/README.md).

## What the audience should feel

1. **Curiosity:** “Could my drawing become something real?”
2. **Progress:** Questions and guided comparisons make the idea clearer.
3. **Wonder:** A mathematical rule can make a visible 3D shape.
4. **Momentum:** Code, tests, and deployment turn the shape into a ride.
5. **Payoff:** The audience rides the exact idea they watched being created.

The answer text is not the hero. The child's changing idea is the hero. Long
answers may move at 8x to 20x, while important questions, the uploaded sketch,
the final Surface, `READY TO RIDE`, and the real ride receive time to breathe.

## Current source and deliverables

| Part | Source | Current duration | Status |
| --- | --- | ---: | --- |
| Milestone 1 | `RollerCoasterMilestone1` | 36.05 s | Approved |
| Milestone 2 | `RollerCoasterMilestone2` | 22.55 s | Approved |
| Milestone 3 build | `RollerCoasterMilestone3Build` | 17.05 s | Approved |
| Final long | `roller-coaster-final/final-long.mp4` | 94.05 s | Complete |
| Final vertical short | `roller-coaster-final/final-short-vertical.mp4` | 59.78 s | Complete; native portrait M3 build |

The ride source is `/Users/yqin/repo/playground/inception-space-ui`. The
approved continuous-speed black-hole continuation is on `main` at commit
`43fae31` and is live
at `https://is.lucasacademy.org`.

## Film structure

### Milestone 1 — A question becomes a sketch

Purpose: establish that these are a child's actual questions and that the
project begins with ordinary curiosity, not with a perfect technical plan.

- Start with the exact first question.
- Type the first question most slowly.
- Let later questions type a little faster.
- Show the uploaded hand-drawn spiral with only mild cleanup.
- Keep the pencil texture and imperfect line. It is evidence of the real
  thinking process.
- Accelerate answers to 8x, 12x, and 20x.
- End on the first useful spiral function.
- Never replace the opening with a polished retrospective question. The
  imprecise original wording is essential evidence of the learning process.

### Milestone 2 — A sketch becomes one Surface

Purpose: show guided discovery. An adult helps turn the child's visual idea
into choices that can be compared: 3D rather than 2D, a Surface rather than a
line, a useful contraction rate, and an exact endpoint.

- Begin with the exact question:
  “3d xyz plane like a funal shape spiraling down”
- Enlarge the question.
- Compress the middle conversation to three meaningful visual steps:
  1. a descending funnel centerline;
  2. a ribbon-like surface with spiral contraction;
  3. one continuous Surface ending at `(0, 0, 0)`.
- Show equations and GeoGebra images, but do not pause for every sentence.
- At about 19 seconds, isolate the final 3D surface.
- Remove axes and interface chrome.
- Stand the surface upright so it already resembles a coaster.
- Push it toward the viewer and softly blur for about 3.5 seconds.
- Make the funnel-versus-golden comparison legible. The desired model emerges
  from noticing that one contracts too slowly and the other too quickly.

### Milestone 3 — A Surface becomes a ride

Purpose: make the invisible engineering feel fast, complex, and exciting,
then prove it works with real gameplay.

- Begin with the exact request:
  “Go ahead make it a roller coaster”
- Show the request typing naturally.
- Race through orientation, mathematical modeling, ride controls, rendering,
  Reader content, tests, Git, and deployment.
- Let dense technical words and formula fragments burst outward for five to
  six seconds.
- Pull every fragment back into one clear phrase:
  `READY TO RIDE`
- Use the smaller line:
  `GOLDEN FUNNEL · BUILD COMPLETE`
- Fade into real local gameplay.
- Open `R / READ`, scroll all the way to the bottom, then ride the full track.
- End only after the camera spirals completely into the black hole and the
  frame becomes black.

## Technical word-cloud direction

The word cloud is not a lesson. It is a visual burst of real engineering work.
It should look difficult to a general audience without turning into fake
“hacker” decoration.

Use fragments from these groups:

**Mathematics**

- `Surface(u, v)`
- `u ∈ [−4π, 10π]`
- `φ = (1 + √5) / 2`
- `taper(u) = 1 − u / 10π`
- `golden(u) = φ^(−u / 2π)`
- `r(u) = 8 · taper(u) · golden(u)`
- `∂S/∂u × ∂S/∂v`
- `C¹ continuity`
- `arc-length parameterization`

**3D graphics and ride runtime**

- `goldenFunnelProfile(u)`
- `goldenFunnelCutsceneFrame(t)`
- `manifoldBlackHoleFrame(t)`
- `normalize(cross(tangent, localUp))`
- `Quaternion.slerp()`
- `CatmullRomCurve3`
- `TBN frame`
- `camera.matrixWorld`
- `projectionMatrixInverse`
- `requestAnimationFrame()`
- `WebGLRenderer`
- `BufferGeometry`
- `Float32Array`
- `fixed timestep`
- `frame interpolation`
- `procedural surface sampling`
- `event horizon`
- `first-person camera lock`

**Verification and deployment**

- `npm run check`
- `tsc --noEmit`
- `vite build`
- `1,153 tests passed`
- `git diff --check`
- `commit 0b62ae3`
- `origin/main`
- `CI pipeline`
- `artifact SHA-256`
- `content-addressed asset`
- `cache-control: immutable`
- `Render deploy`
- `healthcheck: HTTP 200`
- `is.lucasacademy.org`

Give these fragments several depth layers. Let some drift along spiral paths.
Use small timing offsets, restrained blur, parallax, and brief terminal status
lines. The motion should progress from formula, to geometry, to runtime, to
testing, to deployment. Do not use random green characters or fake security
warnings.

## Complete child-friendly English voice-over

The lines below are the recommended full narration. Exact timecodes may move a
little when the final gameplay length is known. Read with warmth and curiosity,
not like a commercial. Leave short spaces between ideas so the pictures can do
some of the work.

### Opening and Milestone 1

**Visual:** The first question types slowly.

> These are questions a child really asked. He did not begin by saying “golden
> spiral.” He began with a fuzzy idea: a roller coaster made from formulas.

**Visual:** Early formula suggestions appear quickly.

> A finished spiral could have been made at once, but that would skip the
> valuable part.

**Visual:** The loop question appears.

> He tried hills, then asked for a loop.

**Visual:** The original uploaded sketch fills the screen.

> When words were not enough, he drew this.

**Visual:** The first spiral function and graph appear.

> The rough sketch made the next question possible.

### Milestone 2

**Visual:** “3d xyz plane like a funal shape spiraling down” types on screen.

> Next, an adult helped guide the search. Together, they moved the idea into
> three dimensions: like a funnel, spiraling down.

**Visual:** Funnel centerline becomes a ribbon.

> Each answer gave them something real to compare. A line was not a track, so
> they tried one Surface.

**Visual:** `u` and `v` are visible in the Surface expression.

> A funnel tightened too slowly; a golden spiral too quickly.

**Visual:** Final Surface ending at the origin.

> Comparing them helped the idea become one smooth path between the two, ending
> at zero.

**Visual:** The isolated 3D Surface stands upright and moves closer.

> The important result was not only the formula. Guided discovery had turned a
> visual idea into a shape the team could describe and test.

### Milestone 3 build

**Visual:** “Go ahead make it a roller coaster” types on screen.

> Only after the guided discovery did the instruction become clear: “Go ahead,
> make it a roller coaster.”

**Visual:** Agent build steps and technical word cloud accelerate.

> Code added rails, motion, a camera, tests, and a place in the museum.

**Visual:** Tests, Git, and deployment fragments appear.

> The computer moved quickly, but its direction came from the questions that
> had just become clear.

### Reader and gameplay

**Visual:** Open `R / READ` and begin scrolling.

> This is the same mathematical Surface.

**Visual:** Scroll to the formula near the bottom.

> It is not a picture placed on the ride. It is the ride.

**Visual:** First wide rotations.

> Its wide turns become smaller as the path falls toward its final point.

**Visual:** Turns become tighter. Keep narration sparse here.

> We can ride the result—but remember, the discovery happened before the ride.

**Visual:** Enter the black hole. Let the last second become fully black.

> A fuzzy question became a sketch, then a better question, then a world.

### Optional closing line

Use this only if the video continues after black. Otherwise, let black and
silence be the ending.

> The important result was not only the spiral. It was learning how to turn an
> unclear idea into a question clear enough to build.

## Narration performance notes

- Target a calm pace of about 125 to 140 words per minute.
- Say `phi` like “fye.”
- Say `Surface of U and V`, not every symbol in the full equation.
- Do not try to read the word cloud aloud.
- Do not talk continuously over the ride. The movement needs space.
- Keep sentences short. Prefer one idea per sentence.
- Sound curious and pleased, not amazed by every small action.
- Avoid words such as “obviously,” “simply,” or “easy.” They can make a child
  feel that a hard idea should already be familiar.
- Keep attribution accurate: the child began with the real questions, sketch,
  and desired experience; the adult contributed substantial mathematical
  guidance in Milestone 2; the AI made options visible and implemented them.

## Gameplay recording plan

1. Record the current local `main` build, not an old MP4.
2. Use the local route:
   `http://127.0.0.1:8095/?debug&hud=0&fullscreen=0&inspect=the-manifold&launch=goldenFunnel`
3. Wait until all models and shaders are loaded.
4. Enter fullscreen and establish pointer lock.
5. Open Reader with `R`.
6. Scroll smoothly to the absolute bottom and pause on the last content.
7. Close Reader.
8. Start the ride at `1.5×` speed and `0.5×/s` acceleration.
9. Make one very small, smooth look toward the black hole at the beginning.
10. Release the view and allow the camera to recover.
11. Record the entire ride without gameplay speed ramps or missing sections.
12. Allow the forced camera to continue through the final 2.25 tight turns.
13. Stop only after the picture has become fully black.

## Capture and export specification

- Master frame: `1920 × 1080`.
- Preferred gameplay capture: constant 60 fps.
- Fallback: constant 30 fps when 60 cannot remain stable.
- Stable 30 fps is better than unstable 60 fps.
- Use real-time hardware-accelerated window or display capture.
- Never make gameplay from an automated screenshot sequence.
- Do not synthesize missing frames.
- Final codec: H.264 video and AAC audio.
- Hide the cursor, browser chrome, desktop, recording controls, and debug UI.
- Verify width, height, codec, duration, `r_frame_rate`, and `avg_frame_rate`
  with `ffprobe`.
- Watch the final capture at normal speed before editing it into the master.

## Audio direction

- Milestone 1: light, curious pulse with room for the typing sounds.
- Milestone 2: add a soft rising pattern as the drawing becomes a Surface.
- Milestone 3 build: faster clockwork or percussive texture, never an aggressive
  “hacker” soundtrack.
- `READY TO RIDE`: briefly simplify the music so the phrase lands clearly.
- Gameplay: let wind, movement, and the room carry more of the sound.
- Black-hole ending: reduce music and low frequencies smoothly into silence.

## Cleanup and source-of-truth rules

- `src/` and `public/` contain reproducible source material.
- `out/` contains rendered deliverables and may be regenerated.
- Keep approved milestone masters and the current build reference.
- Remove review screenshots after a visual decision is approved.
- Replace an old gameplay file instead of keeping numbered near-duplicates.
- Never treat an old combined cut as current after its gameplay source changes.
- Do not delete Monkey Society assets while cleaning the roller-coaster film;
  it is a separate video project in the same repository.

## Final acceptance checklist

- The first question is exact and types slowest.
- The uploaded sketch is shown and still feels handmade.
- Milestone 2 uses only the three meaningful function iterations.
- The final 3D Surface is isolated, axis-free, upright, and visible long enough.
- Milestone 3 begins with the exact request.
- The word cloud uses credible engineering and mathematical language.
- The cloud converges clearly into `READY TO RIDE`.
- Reader is scrolled all the way to the bottom.
- Gameplay has stable frame cadence.
- The entire ride is present at natural speed.
- The final tight rotations continue into the black hole.
- The final frame reaches complete black.
- All visible text and narration are English.
- A child can explain the main idea after watching: ask, draw, make a rule,
  test it, and ride it.
- An adult can explain why the process matters: a direct golden-spiral answer
  would be faster, but it would hide the child's developing thought and agency.
- The audience can identify Milestone 2 as guided discovery, not as a sequence
  of technical questions authored entirely by the child.
