# 语言的桥：你教我，我教你 / Language Bridge: You Teach Me, I Teach You

Two videos for [yancyqin/lucas-academy-media#4](https://github.com/yancyqin/lucas-academy-media/issues/4)
(first titled 互惠的门 / Reciprocal Doors — the pipeline files keep that name):
a **Chinese film** and an **English film**, each on its own timeline, about the
product at [lang.lucasacademy.org](https://lang.lucasacademy.org). Two fictional
children, Mary (more at ease in English) and Jacob (more at ease in Chinese),
teach each other; RD07, RD08 and RD10 show the real product.

- **Copy:** `src/scripts/reciprocal-doors.json` — the approved zh / en text of
  every line (subtitles come from here, word for word).
- **Voice direction:** `scripts/reciprocal-doors-direction.py` — what is *spoken*:
  the same words plus `<strong>` emphasis and punctuation, and the pause before
  each line. Review copy: `docs/RECIPROCAL-DOORS-VOICE-SCRIPT.md`
  (`reciprocal-doors-voice.py md` / `apply-md` round-trips it).
- **One reading per film** (the Van Gogh film's style, `zero-shot-instruct`,
  speed 1.0): 「请用活泼、亲切的语气，像给孩子讲故事一样说。」 (fangfang/zh) and
  "Please speak in a lively, warm voice, like telling a story to children."
  (louise/en). Per-line speeds or tones made the Chinese 忽快忽慢; the Chinese
  lines are instead paced to the film's median speaking rate
  (`src/scripts/reciprocal-doors.pace.zh.json`, spread ±6%). The taught
  phrases (我来帮你 / Let me help you) are read slowly and plainly.
- **The Chinese film plays at 1.3×** (owner, 2026-10-02; viewers found 1.5×
  about right): `reciprocal-doors-prep.mjs` time-stretches the takes with
  ffmpeg `atempo` (pitch kept, the stretch a player's speed setting uses) and
  shrinks the film's pauses with them; the taught phrases keep their slow
  reading. Three lines read wrong once stretched (图画→读话, 练认字→恋爱认字, a
  breath → 呵呵): `reciprocal-doors-fast.py` voices those at the fast pace
  instead (1.3× the median rate, Whisper-checked; 练 forced with `[l][iàn]`),
  and the film plays them as they are. The English film is unchanged.
- **Background music:** "Canon in D Major", Kevin MacLeod (incompetech.com),
  CC BY 3.0, so the credit goes with every upload (it is in both YouTube
  descriptions). The bed sits at −24 LUFS under −16 LUFS narration, as in the
  Van Gogh film; it dips about 6 dB under the voice and fades in over 2 s. The
  Chinese film fades it out over its last 4 s; the English film stretches it
  ×1.039 so the piece ends with the film. The Commons file first suggested,
  "Canon and Gigue in D", is CC BY-SA 3.0: set to picture, it would put the
  whole video under ShareAlike, which the NIV text on the product screens
  cannot be.

## Pipeline

The concept images, the product screens (they show NIV text) and the narration
audio are not committed (this repo is public; see `.gitignore`). The image
prompts are in `docs/RECIPROCAL-DOORS-IMAGE-PROMPTS.md`; re-capture the product
screens with `node scripts/reciprocal-doors-capture-product.mjs` (Remotion's
headless Chrome over the DevTools protocol, 1440×900 at 2×, Chinese and English
interface; it also rewrites `product/regions.json`, the rects the film points at).
The music is not committed either; fetch Kevin MacLeod's recording from Wikimedia
Commons:

```bash
mkdir -p public/audio/reciprocal-doors/music
curl -L -A lucas-academy-video/1.0 -o public/audio/reciprocal-doors/music/canon-in-d-major-kevin-macleod.mp3 \
  'https://upload.wikimedia.org/wikipedia/commons/c/c6/Canon_in_D_Major_%28ISRC_USUAN1100301%29.mp3'
```

```bash
# 1. direction → film script → narration scripts (stale takes are deleted)
python3 scripts/reciprocal-doors-direction.py apply
python3 scripts/reciprocal-doors-voice.py narration
# 2. narration, each take Whisper-checked as the film plays it (after tightening)
cd ../lucas-academy-media
PYTHONPATH=src .conda/bin/python ../lucas-academy-video/scripts/reciprocal-doors-retake.py zh
PYTHONPATH=src .conda/bin/python ../lucas-academy-video/scripts/reciprocal-doors-retake.py en
PYTHONPATH=src .conda/bin/python ../lucas-academy-video/scripts/reciprocal-doors-pace.py   # Chinese pace
PYTHONPATH=src .conda/bin/python ../lucas-academy-video/scripts/reciprocal-doors-fast.py rd03-05 rd07-03 rd07-06   # 1.3× takes
cd ../lucas-academy-video
# 3. tighten (edges, pauses capped at 0.55 s) and check everything once more
../lucas-academy-media/.conda/bin/python scripts/reciprocal-doors-tighten.py
(cd ../lucas-academy-media && PYTHONPATH=src .conda/bin/python ../lucas-academy-video/scripts/reciprocal-doors-check.py zh)
# 4. one timeline per film (the Chinese at 1.3×) + captions; check the Chinese as it plays
node scripts/reciprocal-doors-prep.mjs
(cd ../lucas-academy-media && PYTHONPATH=src .conda/bin/python ../lucas-academy-video/scripts/reciprocal-doors-check.py zh --played)
# 5. one -16 LUFS mix per film: the narration over the music
../lucas-academy-media/.conda/bin/python scripts/reciprocal-doors-tracks.py
# 6. render the pictures (clean + subtitled), mux, describe
npx remotion render src/index.ts LanguageBridgeZhClean out/reciprocal-doors/video/picture.zh.clean.mp4 --muted
npx remotion render src/index.ts LanguageBridgeZhSubtitled out/reciprocal-doors/video/picture.zh.subtitled.mp4 --muted
#    (same for En)
scripts/reciprocal-doors-deliver.sh
python3 scripts/reciprocal-doors-youtube.py
```

## Delivery (YouTube)

In `out/reciprocal-doors/delivery/`, per film (`zh`, `en`):

- `language-bridge.<film>.mp4` — clean picture; upload this with the captions.
- `language-bridge.<film>.zh-Hans.srt` / `.en.srt` — captions in both languages
  on that film's time codes (the film's own language is the main one).
- `language-bridge.<film>.subtitled.mp4` — subtitles burned in (Chinese film:
  Chinese + small English; English film: English only), for elsewhere.
- `youtube-description.<film>.txt` — title, description with chapters, the
  music credit, tags.
- `youtube-cover.<film>.jpg` — the cover (2026-10-06): only the question, on the title card's picture
  and veil — 「学了英文 / 会忘了中文吗？」 with "Learning English — Will They Forget Chinese?" small
  (zh film); the English film the other way round, in three lines so it clears the children. 英文 /
  English in Mary's coral, 中文 / Chinese in Jacob's teal. Render `LanguageBridgeCoverZh` / `...En`
  (`npx remotion still src/index.ts LanguageBridgeCoverZh cover.zh.png`), then scale to 1280×720.

## Checks that caught real slips

Whisper (medium, simplified-Chinese prompt, a whole-line match ≥0.94 zh / ≥0.9 en,
must / must-not words per line) on the *tightened* takes: dropped words (有些),
tone slips (练→脸, 倒 dǎo→dào, 讲→扬), erhua (事→事儿), extra syllables
("we can say tat", "答，"), a stressed "can" heard as "can't", a line read twice.
Two readings are forced with CosyVoice pinyin tokens in the spoken text only
(`杯子[d][ǎo]了`, `一起[j][iǎng]`). At 1.3× the check runs on the stretched
copies the film plays (`--played`), where 图画→读话, 练→恋爱 and a breath heard as
呵呵 showed up; native fast takes fixed all three.
