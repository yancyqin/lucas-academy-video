# Roller Coaster Conversation Video Milestones

The shared ChatGPT conversation is the source timeline for both the game work
and the accompanying video.

The complete editorial plan, recording specification, and child-friendly
English voice-over are in [`ROLLER-COASTER-VIDEO-GUIDE.md`](./ROLLER-COASTER-VIDEO-GUIDE.md).

## Milestone 1 — complete

- Composition: `RollerCoasterMilestone1`
- Output: `roller-coaster-final/clips/01-milestone-1.mp4`
- Boundary: the original formula question, the loop question, the uploaded
  spiral sketch, and the first spiral-function answer.
- Rhythm: first question is slowest; later questions get faster; answers
  accelerate through 8x, 12x, and 20x.

## Milestone 2 — complete

- Composition: `RollerCoasterMilestone2`
- Output: `roller-coaster-final/clips/02-milestone-2.mp4`
- Boundary: starts with the exact question “3d xyz plane like a funal shape
  spiraling down” and ends at the final single GeoGebra `Surface` formula.
- Process: three key iterations — 3D funnel centerline, Möbius ribbon with
  Fibonacci/golden-spiral decay, and the final Y-down surface ending at
  `(0,0,0)`.
- Rhythm: the question is enlarged and slow; answers visibly type into the
  ChatGPT thread while accelerating through 8x, 10x, 12x, 16x, 18x, and 20x.
- Language: all on-screen copy is English.
- Transition: from 19 seconds, the isolated upright 3D Surface—without UI or
  axes—pushes forward and blurs for 3.5 seconds into the Milestone 3 build.

## Milestone 3 — complete and deployed

- Composition: `RollerCoasterMilestone3Build`
- Output: `roller-coaster-final/clips/03-milestone-3-build.mp4`
- Exact request: “Go ahead make it a roller coaster”.
- Duration: 17 seconds; the final second fades directly to black for the game
  scene.
- Build answer: rapidly condenses the work into six real stages — orientation,
  mathematical model, ride wiring, visible Surface, Reader, and verification.
- Current verified facts: 1,154 passing tests; a continuous Surface; and a
  first-person camera that follows the final 2.25 tight turns into the origin.
- Build-complete beat: the code concepts burst into a dynamic word cloud,
  converge, and resolve to `READY TO RIDE` before the one-second fade.
- Production ride: the continuous-speed black-hole handoff is on `main` at
  commit `43fae31` and deployed to `is.lucasacademy.org`.
- Handoff: the approved in-game footage begins immediately after the fade and
  continues through the black-hole ending.

The completed recording follows this approved plan:

1. Record entering The Manifold and approaching Golden Funnel.
2. Press `R`, scroll the Reader all the way to the bottom, and close it.
3. Start the automatic ride and capture one complete coaster run as smooth,
   continuous real-time footage.
4. Record at stable 60 fps when possible, or stable 30 fps if the machine
   cannot hold 60. Never build gameplay from a screenshot loop.
5. Continue through the forced first-person black-hole cutscene until the
   image is fully black.

## Final cuts

- Final 16:9 master:
  `roller-coaster-final/final-long.mp4`.
- Final 9:16 short:
  `roller-coaster-final/final-short-vertical.mp4`.
- Each milestone boundary is a deliberate deceleration point; the work after
  it accelerates until the next milestone begins.

## Short vertical cut

- Composition: `RollerCoasterMilestonesShort`
- Output: `roller-coaster-final/final-short-vertical.mp4`
- Format: `1080 × 1920`, 60 fps, 59.78 seconds.
- Edit: preserves the exact first Milestone 1 and Milestone 2 questions, keeps
  the uploaded sketch, removes repeated intermediate explanation, and pushes
  answer playback to 12x, 16x, and 20x.
- Milestone 3 uses the separate native `RollerCoasterMilestone3BuildVertical`
  composition; only the real horizontal gameplay is carried in a portrait
  overlay so none of the ride is cropped.
- Current model: one continuous five-turn tapered logarithmic Surface with
  contraction `k = 0.25`; it shrinks faster than a plain funnel but far more
  slowly than a standard golden spiral, and closes at `(0,0,0)`.
