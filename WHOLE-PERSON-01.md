# 我们怎样陪孩子成长：全人教育的五个理念 / How We Grow Alongside Our Kids: Five Principles of Whole-Person Education

Videos for [yancyqin/lucas-academy-media#5](https://github.com/yancyqin/lucas-academy-media/issues/5).
Two films, one per language, told to parents. No captions are burned in: each film ships with
`zh-Hans.srt` and `en.srt` timed to its own narration.

| | narration | length |
| --- | --- | --- |
| `WholePersonZh` | Yancy's own voice (`yancy/zh`), zero-shot-instruct teaching tone, speed 1.0 | ≈ 8:08 |
| `WholePersonEn` | Louise (`louise/en`) | ≈ 7:34 |

Deliverables (local, `out/` is ignored): `out/whole-person-01/{zh,en}/whole-person-five-principles.{zh,en}.mp4`
plus `zh-Hans.srt` and `en.srt` in the same folder. Loudness −16 LUFS.

## Script

Source of truth: lucas-academy-media `data/scripts/whole-person-five-ideas.md` (v0.8, approved),
`whole-person-five-ideas-zh.json`, `whole-person-five-ideas-en.json` — 56 lines, one line = one voice
take = one caption. It follows the parents deck (lucasacademy.org/presentation/?deck=parents, slides
7–18) with Yancy's edits, and the essay page `/research/whole-person-education` was aligned with it.

## Pipeline

```bash
# 1. Voice (from lucas-academy-media, with its .conda env; CPU, ~1 min a line)
V=../lucas-academy-video/scripts/whole-person-01
.conda/bin/python $V/narrate.py zh && .conda/bin/python $V/narrate.py en     # reuse unchanged lines by text
.conda/bin/python $V/retake.py zh 'wp01-19=authoritative&authoritarian'     # re-voice until Whisper hears the words
.conda/bin/python $V/pace.py zh && .conda/bin/python $V/pace.py en           # every line within ±10% of the median pace
.conda/bin/python $V/check_lines.py data/scripts/whole-person-five-ideas-zh.json outputs/yancy/zh/whole-person-five-ideas-v8 zh
# 2. Timelines, narration + music mixes, SRTs (this repo)
npm run wp01:timeline
# 3. Render both films at 1080p
npm run wp01:render
```

- `narrate.py` — one WAV per line into `OUT`; lines whose text is unchanged since `PREVIOUS` are copied,
  not re-synthesized. `SPOKEN` holds what the voice reads where it differs from the caption: the zh voice
  reads the English terms (critical literacy, problematizing, authoritative, authoritarian), 梵高 is
  spoken 凡高 (fán gāo), 119 is spoken 一百一十九.
- `retake.py ID=REGEX&REGEX …` — fresh takes until Whisper's transcript matches. The zh voice garbles
  English names (Lucas Academy, Art Lab, Matthew): check those lines.
- `pace.py` — speaking rate = syllables per second of sound (pauses excluded); a line more than 10% off the
  film median is re-voiced with closed-loop speed correction and kept only if Whisper still reads it right.
  `EXEMPT` keeps the opening question 「谁是教育者？」 slow on purpose. Speeds land in `src/data/whole-person-01.pace.json`.
- `check_lines.py` — Whisper every line, flag below 0.9. Known zh false alarms: homophones (权柄→全柄,
  勉励→免利, 作主→做主). Final run: all 56 English lines pass; zh only those homophones.
- `build_timeline.py` — per film: cue timeline (`src/data/whole-person-01.{zh,en}.json`), trimmed narration
  track, music mix and SRTs. Music: "Echoes in the Void" (Yancy's track for the Inception Space Journey of
  Art room), looped with 6 s crossfades, −13 dB bed, sidechain-ducked under the voice, mix normalised to −16 LUFS.

## Picture

- **Opening:** Inception Space's own loading screen (rebuilt from `inception-space-ui/index.html`
  `#entry-loading` at 1.5×, English text kept) → the transit chamber with the avatar hidden; the title card
  and 「谁是教育者？」 sit on the footage; the question is asked, ~2 s pause, then the answer.
- **Sections:** each principle plays its app recording dimmed under frosted-glass cards (cyan hairline,
  mono kickers); a demo line brings the recording up full. Cards that state a belief carry
  「Lucas Academy 的团队相信」 even though the narration says 我们相信.
- **Lucas & Matthew:** original pencil sketch → prepared drawing → finished artwork (the museum versions).
  They are Yancy's children; names and drawings are shared with their parent's permission.

### Local assets (`public/whole-person-01/`, ignored) and where they come from

| path | source |
| --- | --- |
| `footage/journey-of-art.mp4`, `language-bridge.mp4`, `van-gogh-room.mp4`, `snake-ranking.mp4` | lucasgame-academy `presentation/assets/`, re-encoded with a keyframe every 0.5 s (see Gotchas) |
| `footage/live-painting.mp4` | the Art Lab recording `live-painting (1).mp4`, made constant 30 fps, same keyframe rule |
| `footage/transit-chamber.mp4` | `scripts/whole-person-01/record-chamber.cjs` (below) |
| `images/{lucas,matthew}-sketch-original.jpg`, `*-preparation-final.jpg`, `logo.png`, `live-painting.png` | lucasgame-academy `presentation/assets/` |
| `images/{lucas,matthew}-final-artwork.jpg` | inception-space-ui `output/imagegen/lesson03-matthew-lucas/<kid>/<kid>-completed-full-bleed-final.jpg` (same bytes as the R2 museum objects) |
| `music/echoes-in-the-void.m4a` | Yancy's original `Echoes in the Void.m4a`; provenance in inception-space-ui `PROVENANCE.md` |
| `audio/` | written by `npm run wp01:timeline` |
| `concept/` | Codex concept images from an early version — not used, kept local |

Re-encode a recording: `ffmpeg -i IN.mp4 -an -c:v libx264 -crf 18 -pix_fmt yuv420p -r 30 -g 15 -keyint_min 15 -sc_threshold 0 -movflags +faststart OUT.mp4`.

Record the transit chamber: start the Inception Space dev server on :8110 (`npx vite --port 8110` in
inception-space-ui), then `PLAYWRIGHT_DIR=<dir with node_modules/playwright> node scripts/whole-person-01/record-chamber.cjs <frames> 20`
and encode the frames as above. It opens the cylinder room `room-b` directly, takes the floor console's
Space Travel ride (which holds in the chamber indefinitely), and captures one frame per 1/30 s of world
time with the avatar hidden.

## Gotchas

- Use `OffthreadVideo` + `Loop`: the HTML5 `<Video>` repeated and jumped back frames when rendering.
- The deck recordings had a keyframe every 6–8 s; with several clips on screen OffthreadVideo timed out.
  Re-encode with `-g 15` and render with `--timeout=240000 --offthreadvideo-cache-size-in-bytes=2000000000`.
- `npx remotion render --help` starts a render instead of printing help.
- Instruct-only CosyVoice (`instruct2`) loses the speaker's voice; the free-form "chat" tone sounded wrong.
  One film-wide `zero-shot-instruct` teaching tone keeps Yancy's voice.
