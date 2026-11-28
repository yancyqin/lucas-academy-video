# We Build A BlackHole with AI — English narration (v0.1 · 2026-11-26)

By Lucas Academy Team. Plan: [BLACK-HOLE-AI.md](../../BLACK-HOLE-AI.md). Chinese track: [zh-edit.md](zh-edit.md),
same cue ids. Voice: Louise (`louise/en`, direct CosyVoice), natural speed. Outline approved by Yancy 2026-11-26:
fly around the black hole in third person, then how it was made (the debug page, the NASA references), then the
fall — the camera still until the event horizon, first person after it with occasional smooth looks.

Every factual line is checked against inception-space-ui: `docs/KERR-BLACK-HOLE-OPTICS.md` §10 (references),
`src/inception/world/blackHole/palette.js` (the SVS 13326 colour table), `docs/KERR-PLUNGE-MULTIIMAGE-PLAN.zh.md`
(SVS 14576), the shadow-edge acceptance (`criticalImpactParameter` to 1e-9) and
`src/inception/world/model/blackHoleApproach.js` (the 90-second fall, real time inside for Sgr A*).

Spoken forms (the voice reads these; captions keep the written form):
- bh04-01: "is.lucasacademy.org" → "is dot lucas academy dot org"
- bh03-05: "Sagittarius A*" → "Sagittarius A star"

## BH00 Flying around a black hole

- bh00-01 | This black hole is not a movie effect. Every pixel you see is a ray of light, traced backwards through Einstein's equations.
- bh00-02 | We built it with AI, and you can fly around it yourself in our online museum.
- bh00-03 | First, how we made it. Then, we fall in.

## BH01 What a real black hole looks like

- bh01-01 | Near a black hole, light does not travel in straight lines. Gravity bends it so much that you can see the back of the glowing disk, wrapped over the top and under the bottom.
- bh01-02 | Scientists at NASA's Goddard Space Flight Center have made beautiful films of this. We measured the colours in one of them to paint our gas.
- bh01-03 | For the bending itself, we followed a 2015 paper by Kip Thorne and the visual effects team behind the movie Interstellar.
- bh01-04 | And for falling in, NASA's 2024 film of a plunge into a black hole showed us what the view should do.

## BH02 How we built it with AI

- bh02-01 | We started with a plan in plain words: what a real, spinning black hole does to light.
- bh02-02 | Then the AI wrote the physics. The Kerr metric describes the shape of space around a spinning black hole, and a careful step-by-step solver follows each ray of light through it.
- bh02-03 | One ray for every pixel, all running on the graphics card, again and again every second.
- bh02-04 | This is our debug page. Here is the picture.
- bh02-05 | Here is what each ray did. Blue rays flew out to the sky, black ones fell into the hole, and the warm colours stopped in the glowing gas.
- bh02-06 | Here is how hard each pixel had to work. And here is how much the light was shifted: bluer where the gas rushes toward us, redder where it races away.
- bh02-07 | To check the graphics card, we compared it with a slow, exact version that runs on the main processor.
- bh02-08 | And we tested it against the math. The edge of the black shadow lands exactly where theory says, to one part in a billion.

## BH03 Falling in

- bh03-01 | Now let's fall in. Close to the hole, it grabs our ship and throws it into orbit.
- bh03-02 | Three times around, faster and faster, closer and closer.
- bh03-03 | That thin bright ring is light that has gone all the way around the hole.
- bh03-04 | Here is the edge, the event horizon. Past it, every path leads inward.
- bh03-05 | If this were Sagittarius A*, the black hole at the centre of our galaxy, these last fifteen seconds would really take fifteen seconds for the one falling in. So we play them in real time.

## BH04 Fly it yourself

- bh04-01 | Fly in yourself at is.lucasacademy.org. Open the Teleport Orb in The Manifold and choose Black Hole Journey. Have fun, and stay curious.
