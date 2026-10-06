# 孩子说“不”，你怎么办？｜全人教育的五个理念 / Your Child Says “No.” Now What? | Five Principles of Whole-Person Education

(The film's name, on its opening card: 我们怎样陪孩子成长：全人教育的五个理念 / How We Grow Alongside Our Kids.)

Videos for [yancyqin/lucas-academy-media#5](https://github.com/yancyqin/lucas-academy-media/issues/5).
Two films, one per language, told to parents. Published without captions (owner's call, 2026-10-05);
nothing is burned in, and the pipeline still writes `zh-Hans.srt` and `en.srt` timed to each film's
narration in case they are wanted later.

| | narration | length |
| --- | --- | --- |
| `WholePersonZh` | Yancy's own voice (`yancy/zh`, v10), zero-shot-instruct teaching tone, speed 1.0 | ≈ 8:26 |
| `WholePersonEn` | Louise (`louise/en`, v9) | ≈ 7:52 |

History: first uploads 2026-10-05 (zh v8). An audio-only zh remix followed with v9, which is v8 with the
off-pitch lines re-voiced plus the steady mix. Louise's Chinese voice was tried and dropped; the owner kept
Yancy's. The en film was re-uploaded with the byline (ZaKR2wA7dFk).

2026-10-06 re-make (owner: 「这个视频很重要」, script v0.9): the films open on 「孩子说“不”，你怎么办？」.
They answer 「谁是教育者？」 first, then come back to the question at principle 1, and the YouTube title
is the question. Four new lines per language: zh v10 / en v9, every other take reused. The picture is
re-rendered for both.

Delivery (local, `out/` is ignored), all in `out/whole-person-01/delivery/`:

- `whole-person-five-principles.<film>.mp4` — 1080p, −16 LUFS, clean picture.
- `whole-person-five-principles.<film>.zh-Hans.srt` / `.en.srt` — both captions on that film's own times (not uploaded).
- `youtube-description.<film>.txt` — title, paste-ready description with chapters, credits and Bible
  notices, tags, upload settings (not made for kids; altered/synthetic content = yes, synthesized voice).
- `youtube-thumbnail.<film>.jpg` — the cover, 1280×720: only the question, 「孩子说“不”你怎么办？」 /
  "Your Child Says “No.” Now What?", big on the title frame's background (the README cover rule;
  composition `WholePersonCoverZh` / `WholePersonCoverEn`, copy in `QUESTION`).

Only sources are committed: the line scripts (lucas-academy-media), the code and this file. Everything
the pipeline writes — voice takes, timelines, mixes, recordings, renders — is a local working copy:
rebuild it with the steps below when the film changes, and delete it once the film is published.

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
.conda/bin/python $V/pitch.py zh && .conda/bin/python $V/pitch.py en         # every line within ±2 semitones of the median pitch
.conda/bin/python $V/check_lines.py data/scripts/whole-person-five-ideas-zh.json outputs/yancy/zh/whole-person-five-ideas-v9 zh
# 2. Timelines, narration + music mixes, SRTs (this repo)
npm run wp01:timeline
# 3. Render both films at 1080p
npm run wp01:render
# 4. YouTube title, description (chapter times from the timelines), tags, thumbnails
npm run wp01:youtube
```

`LUCAS_MEDIA=<path>` points `build_timeline.py` at a lucas-academy-media checkout that is not this
repo's sibling.

Fix the sound of a film that is already rendered (re-voiced lines, a new mix) without touching the
picture: `npm run wp01:timeline -- --keep-timeline zh --remux` keeps `timeline.zh.json`, rebuilds only
the zh audio and writes `whole-person-five-principles.zh.remix.mp4` (video stream copied). Every take
must still fit its line's slot; `pitch.py` only keeps takes that do.

- `narrate.py` — one WAV per line into `OUT`; lines whose text is unchanged since `PREVIOUS` are copied,
  not re-synthesized. `SPOKEN` holds what the voice reads where it differs from the caption: the zh voice
  reads the English terms (critical literacy, problematizing, authoritative, authoritarian), 梵高 is
  spoken 凡高 (fán gāo), 119 is spoken 一百一十九.
- `retake.py ID=REGEX&REGEX …` — fresh takes until Whisper's transcript matches. The zh voice garbles
  English names (Lucas Academy, Art Lab, Matthew): check those lines.
- `pace.py` — speaking rate = syllables per second of sound (pauses excluded); a line more than 10% off the
  film median is re-voiced with closed-loop speed correction and kept only if Whisper still reads it right.
  `EXEMPT` keeps the questions (wp00-00, wp00-01) and the hanging wp01-00a as read. Speeds are kept in lucas-academy-media
  `outputs/whole-person-five-ideas.pace.json` (ignored) as the next run's starting point.
- `pitch.py` — median pitch of each trimmed take (pyin, voiced frames) against the film median; a line more
  than 2 semitones off is re-voiced at its paced speed until a take lands within 1 semitone, Whisper still
  reads it right, and it keeps its length (±10%) inside its timeline slot. Added after a listener heard the
  first zh film go up and down: 「第三个理念」 sat about 6 semitones above the other four section openers.
  `EXEMPT` keeps the opening question. zh v9 (Yancy) = v8 with seven lines re-voiced this way.
- `check_lines.py` — Whisper every line, flag below 0.9. Known zh false alarms: homophones (权柄→全柄,
  勉励→免利, 作主→做主, 陡峭→抖窍). Final run: all 56 English lines pass; zh only those homophones.
  Re-check zh flags with Whisper medium before re-voicing: small also mishears tones (互教→虎交), while
  medium caught real slips in the Louise trial (权柄 read bìng, 命题 read míng, 「孩子也是」 slurred,
  和 read kě, 赐 read zì), each fixed with a fresh take. `pace.py` and `pitch.py` compare with the spoken text and
  apply the homophone map, so a homophone no longer blocks a good take.
- `build_timeline.py` — per film: cue timeline (`public/whole-person-01/timeline.{zh,en}.json`; the
  compositions load it before rendering, so it sets each film's length), trimmed narration track, music
  mix and SRTs. Every line is levelled to −23 LUFS first (the takes came out up to 5 dB apart). Music:
  "Echoes in the Void", made by Yancy with Suno for the Inception Space Journey of Art room, looped with
  6 s crossfades; it sits 17 dB under the voice and rises to 10 dB under only in pauses of 2.5 s or more
  (fades of 0.5 s down, 1.5 s up), driven by the timeline. The first films used a sidechain compressor,
  which let the music swell 12 dB in every card hold, and one-pass `loudnorm`, which rides the gain; the
  mix now gets one fixed gain to −16 LUFS and a −1.5 dBFS peak limiter.
- `youtube.py` — the YouTube text lives here; chapter times and film lengths are read from the timelines.

## Picture

- **Opening (2026-10-06):** the first frame is the cover: 「孩子说“不”，你怎么办？」 big, plus what the
  cover leaves out (LUCAS ACADEMY, the film's name, "By Lucas Academy Team"), on the transit chamber with
  the avatar hidden. The question is asked after 2 s and followed by ~2 s of pause. The card stays through
  「在回答这个问题之前……」 and gives way to 「谁是教育者？」 in the same big type; that is asked slowly,
  held, then answered. The first upload opened on Inception Space's loading screen; it was dropped so the
  film starts on its cover.
- **Back to the question (wp01-00/00a):** after the five principles are listed, the question comes back big
  over the principle-1 recording: 「现在我们回答最开始的问题……它关乎……」, a 1.5 s pause, then
  「第一个理念，是权柄」 on its card. `pace.py`/`pitch.py` leave the two questions and the hanging line alone.
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
| `music/echoes-in-the-void.m4a` | Yancy's original `Echoes in the Void.m4a` (made with Suno); provenance in inception-space-ui `PROVENANCE.md` |
| `timeline.{zh,en}.json`, `audio/` | written by `npm run wp01:timeline` |

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
