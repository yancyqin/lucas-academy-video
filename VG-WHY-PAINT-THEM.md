# 梵高为什么画他们？ / Why Did Van Gogh Paint Them?

Video ① of [yancyqin/lucas-academy-media#3](https://github.com/yancyqin/lucas-academy-media/issues/3).
Script source of truth: `lucas-academy-media/data/scripts/vg-why-paint-them/`
`zh-edit.md` (fangfang/zh) and `en-edit.md` (louise/en) — one line per cue,
`<strong>` emphasis and ONE film-wide style (`整体语气` / `Overall tone`, a
lively storytelling instruction voiced in `zero-shot-instruct` mode; speed 1.3
zh / 1.1 en). Per-section tones were tried and dropped: switching sounded
unnatural.

## Pipeline

The paintings, the music and the narration audio are not committed (this repo
is public). Restore the pictures and the music first:
`python3 scripts/vg-why/fetch_assets.py` (needs Pillow).

```bash
# 1. scripts → cues.json + zh.json + en.json (lucas-academy-media)
python3 data/scripts/vg-why-paint-them/build.py
# 2. narration (CPU, ~40 s a line); --only redoes just the lines that changed
.conda/bin/lucas-narrate data/scripts/vg-why-paint-them/zh.json --profile fangfang/zh --language zh --speed 0.9 --output-dir outputs/fangfang/zh/vg-why-paint-them
.conda/bin/lucas-narrate data/scripts/vg-why-paint-them/en.json --profile louise/en --language en --speed 0.9 --output-dir outputs/louise/en/vg-why-paint-them
# 3. Whisper check: flags dropped / garbled words (not tone or accent)
.conda/bin/python scripts/check_narration.py data/scripts/vg-why-paint-them/en.json outputs/louise/en/vg-why-paint-them --language en
# 4. timeline + full audio tracks + SRTs (this repo)
python3 scripts/vg-why/build_timeline.py
# 5. render the picture once; mix the music under each track, loudness-match, mux
npm run vgwhy:render          # deliver.py --sample START SECONDS: a mix excerpt only
```

One picture timeline carries both languages: every cue lasts
`max(zh, en) + pause`, so the same picture takes either audio track and both
SRTs share identical time codes.

## Delivery (YouTube)

No burned-in captions: YouTube carries them. In `out/vg-why-paint-them/`:

- `vg-why-paint-them.zh.mp4` — upload this; Chinese is the default audio track.
- `vg-why-paint-them.en.m4a` — Studio → Languages → add the English dub (same
  length as the video).
- `zh-Hans.srt`, `en.srt` — captions; either language lines up with either track.
- `vg-why-paint-them.en.mp4` — the English cut, for checking only.

Both tracks carry the Van Gogh House music under the narration (Human Horizon A,
the owner's Suno song — `public/vg-why-paint-them/music/SOURCE.md`): looped
with an 8 s crossfade, about 8 dB under the voice in the pauses and ducked a
further ~6 dB while anyone speaks. Both are loudness-matched to −16 LUFS /
−1.5 dBTP. The English lines are shorter (22%), so on the shared timeline the
English track has ~1.2 s more pause per line — chosen over slowing Louise or
cutting two separate videos.

## Pictures

Every picture is a real work: Van Gogh's paintings, drawings and letter
sketches, plus Giotto's *Lamentation* (c. 1305) for the halo. No generated
images (Yancy, 2026-09-30: "完全废除用codex的图"; the earlier Codex set is in
`archive/vg-why-codex-concepts/`, unused).

- The picture plan is `src/videos/vg-why/shots.ts`: each shot covers a run of
  cues. Kinds: `art` (one work with a camera move), `pair`, `row` (a few works
  appearing one by one, labelled), `wall` (many works, justified rows),
  `dissolve` (one work into another), `quote` / `letter` cards, lesson cards.
- The Roulin family (VG03): his wife and three children one by one, then a
  wall of 13 of the family portraits — captioned "some of", never a count.
- VG02: stars / fields / flowers / people, then the letter-705 bedroom sketch
  next to the painting. VG04: the Arles hospital ward → the Yellow House →
  the letter card over *The Bedroom*. VG06: *The Bedroom* dissolving into
  *Starry Night over the Rhône* ("a world larger than a room", labelled as the
  letter's idea). VG07: *La Berceuse* (a lullaby), Giotto's halos, then
  *La Berceuse*'s glowing colour. VG10: one work per lesson. VG11: a wall of
  the people he painted.
- Files: `public/vg-why-paint-them/art/<id>.jpg` (≤3840 px) and `tiles/<id>.jpg`
  (≤800 px, for rows and walls). Credits for the YouTube description:
  `python3 scripts/vg-why/credits.py` → `out/vg-why-paint-them/description-credits.txt`.

## Sources

Paintings: public-domain (or CC0 museum) photographs from Wikimedia Commons,
downloaded 2026-09-29/30 into `public/vg-why-paint-them/art/` — `SOURCES.txt`
there has each file's Commons page, sha256, size, licence and collection
(photo borders trimmed on a few; the dark paintings kept whole). The Roulin portrait is the Detroit Institute of Arts version
(1996.25) — the course library's provenance entry names the MFA Boston
collection for the same file, which is wrong and should be corrected there.
