# We Build A BlackHole with AI

Owner: Yancy. Branch `claude/black-hole-ai-film`. By Lucas Academy Team.
Media (outside Git): `../lucas-academy-video-data/black-hole-ai-20261126/v01/`.

## Decisions (owner, 2026-11-26)

- Title exactly **"We Build A BlackHole with AI"**.
- Order: fly around the black hole in **third person** → how it was made (the **debug page**, how the
  **NASA references** were used) → **fall in**. During the fall the view does not move; after the event horizon,
  first person, with occasional smooth up/down/left/right looks — never constant motion, never jittery.
- Voice "per the project's conventions": Louise, natural speed; English picture with a Chinese audio track and
  separate en/zh SRTs, not burned in (`../lucas-academy-media/AGENTS.md`, `docs/PRODUCTION-CHECKLIST.md`).
- Outline approved 2026-11-26 (before any capture), as the cube films' rule asks.
- Music: Chopin, Nocturne in C-sharp minor, B. 49, Frank Lévy (Musopen, public domain — the same recording the
  museum's Sky room now plays). Continuous under the whole film, ducked from voice activity
  (`scripts/music_ducking.py`), natural fade at the end.
- The footage is the museum itself after inception-space-ui's 2026-11-26 Journey upgrade (the Odyssey ship,
  third/first person on V with the pull-in at the horizon, the 90-second fall with the inside in real time for
  Sgr A*) and its study page `kerr-black-hole.html` (with that day's fix: the page never set the capture radius,
  so its shadow had been magenta since 2026-09-09).

## Script

[docs/black-hole-ai/en-edit.md](docs/black-hole-ai/en-edit.md) and
[docs/black-hole-ai/zh-edit.md](docs/black-hole-ai/zh-edit.md) — 21 lines each, same ids, sections BH00–BH04.
Voice takes: `../lucas-academy-video-data/black-hole-ai-20261126/v01/audio/{en,zh}/<id>.wav` +
`audio/manifest.json` (made by `scripts/black-hole-ai/voice.py`).

## Footage (all 1920×1080, 30 fps, rendered frame by frame on a manual clock)

`../lucas-academy-video-data/black-hole-ai-20261126/v01/public/footage/` (frames and per-frame logs in
`../footage/<take>/`).

| file | length | what |
|---|---|---|
| `f1-orbit.mp4` | 50.0 s | The Odyssey circling the hole at ~32 r_g, ~4 r_g above the disk, chase camera behind it; the lensed hole on the right third of the frame the whole time. Continuous. |
| `f3-fall.mp4` | 93.4 s | One continuous take of the Black Hole Journey, opened from the Teleport Orb. Straight in at full thrust, **no look input until after the horizon**. Events (clip seconds): capture **7.83**; whirl r≈3.5–4 r_g ~15–55; event horizon **79.9**; camera pull-in 79.9→82.9 (ship hidden 80.4); looks inside: left 81.4–84.0, up 85.8–88.0, back to centre 89.4–92.0; fade 92.63→93.37, black after. |
| `d1-picture.mp4` | 7.0 s | Study page, "The picture", marked-grid sky (the lensing of the grid is the point), museum settings a* 0.382 clockwise, slow orbit drift. |
| `d2-outcome.mp4` | 6.0 s | "What each ray did": blue = escaped to the sky, black = fell into the horizon, gold/orange-red = stopped in the gas (magenta = out of budget: none). Same drift, continues d1. |
| `d3-cost.mp4` | 4.0 s | "What each ray cost": steps per ray as a ramp. |
| `d4-shift.mp4` | 5.0 s | "Frequency shift": blue where the gas comes toward the camera, red where it goes away. |
| `d5-landmark.mp4` | 7.0 s | One landmark in an empty sky, no gas: its lensed images around the shadow. B-roll for the checks. |
| `stills/panel-*.png` | — | The study page with its control panel (picture / outcome / cost / shift), 1920×1080 — the "this is our debug page" shot. `panel-compare.png` has the panel scrolled; use the real numbers below instead. |

The CPU check, as the page printed it (2026-11-26, a* 0.382, 48×48): *"outcome agrees on 100.00% of 2304 rays —
sky, horizon or gas"; "frequency shift: mean Δ 4.31e-4"; "no GPU ray ran out of budget"*. (The page's
gas-colour line differs by design — the gas noise hash is float64 vs float32 — and is not shown.)
The shadow test: the ray-traced shadow edge equals the critical impact parameter to 1e-9
(inception-space-ui `docs/KERR-BLACK-HOLE-OPTICS.md`).

## Picture plan

| section | narration | picture |
|---|---|---|
| BH00 Flying around a black hole | bh00-01..03 | `f1-orbit` from 0 s. Title card "We Build A BlackHole with AI" + "By Lucas Academy Team" after bh00-02, ~3.5 s, over the orbit. |
| BH01 What a real black hole looks like | bh01-01..04 | `f1-orbit` continues. Side/lower cards: bh01-02 "NASA Goddard Scientific Visualization Studio — SVS 13326 (J. Schnittman): the colours of our gas"; bh01-03 "O. James, E. von Tunzelmann, P. Franklin, K. S. Thorne (2015), *Gravitational lensing by spinning black holes in astrophysics, and in the movie Interstellar*, Class. Quantum Grav. 32, 065001"; bh01-04 "NASA Goddard visualization, 2024 — a plunge into a black hole (SVS 14576)". Text cards only: no NASA or paper imagery is reproduced. |
| BH02 How we built it with AI | bh02-01..08 | 01 a "plan" card (plain words: metric → integrator → camera → gas & colour → GPU → checks); 02 a code card with the real `kerrSchild` snippet from inception-space-ui `src/inception/world/blackHole/kerr.js` + "Kerr metric · adaptive Dormand–Prince solver"; 03 `d1-picture`; 04 `stills/panel-picture.png` then back to `d1`; 05 `d2-outcome` + a small legend; 06 `d3-cost` then `d4-shift`; 07 `d5-landmark` + the CPU-check card; 08 `d5-landmark` + the shadow-edge card. EN label big, ZH small. |
| BH03 Falling in | bh03-01..05 | `f3-fall` from ~4.5 s to its end, uncut. bh03-01 at the capture (7.83), bh03-02 ~+12 s, bh03-03 around the whirl (~25–30 s), bh03-04 ending before 79 s, bh03-05 starting just after 80.5 (inside), ending before the fade at 92.6. |
| BH04 Fly it yourself | bh04-01 | End card: link **is.lucasacademy.org** + QR (decode-verified), "The Manifold → Teleport Orb → Black Hole Journey", byline. |

Bottom chapter bar segmented exactly like the YouTube chapters (cube-film convention), ▼ playhead.

## Assembly notes (2026-11-27)

- `d3-cost` is shown **8× brighter** than the study page draws it (its ramp peaks at RGB 24, 5, 9, which reads as
  black on screen); the picture carries no label saying so. A re-capture with a brighter ramp would remove the need.
- The fall plays uncut from clip **5.5 s** (after the hole's seizure at 5.23–5.33 s) to its end; bh03-05 starts at
  clip **80.10 s**, just inside the horizon, so the English take ends before the fade at 92.63.
- f1-orbit (the 80-s take of 2026-11-27) plays straight under BH00–BH01, and its last seconds, dimmed, under the end
  card; the study page's panel stills fill where the debug clips are shorter than their lines.
- Built by `scripts/black-hole-ai/build_timeline.py`, `render.py`, `cadence.py`, `package.py` (npm `bh:*`).

## Delivery and QA

`out/black-hole-ai/delivery/`: the MP4 (English default + Chinese second audio track), the Chinese track as
M4A (`aac_at`, not WAV), `black-hole-ai.en.srt`, `black-hole-ai.zh-Hans.srt`, upload text with chapters first
(`scripts/youtube_text.py`). Mandatory: `scripts/qa/qa.py check` then `gate`, for the film and the Chinese track
separately; `final-review` only with real listening or the owner's approval of the exact version.

## Release review — 2026-11-27

UI PR #142 merged as `77a76a5307a72f1ad9a5959823326bac86d2b00e`; the
production site serves the upgraded Journey and the byte-exact R2 manifest.
Global QA PR #69 merged as `5e9b8a40c5d6a0e0ec2d5345f3a1ed593be468a4`;
this branch includes that current shared implementation.

The owner selected YouTube **Unlisted**, retained both short shadow-only
passages (film 183.400–184.000 and 204.900–206.267 s), and explicitly said
that the English and Chinese final audio still need listening review.
Only those two passages are declared intentional still views in the QA
spec, with a static-region check above the chapter bar and the owner's
actual wording. The intent is bound to the source take's SHA-256; a new take
does not inherit it. All other fall frames retain footage-freeze checks.
The original failed reports are retained outside Git with release evidence.

Lensing changes image shape while the ship and view direction remain fixed,
so the fall's global camera-motion estimate is retained as `review`.
Full-resolution decoded cadence, source-frame continuity and the actual
frames supplement the global checks. Neither ASR nor this picture review
constitutes final-audio listening approval. No audio or film bytes were
changed during this review.

The repository's existing `findLastIndex` calls need ES2023 type definitions.
The explicit TypeScript libraries now include ES2023 and the browser DOM;
the ES2022 output target is unchanged.

Production helpers now use this checkout's merged shared QA and mixer instead
of silently finding a sibling feature checkout. `bh:package` returns a failing
exit code while any gate or delivery requirement remains unmet.
