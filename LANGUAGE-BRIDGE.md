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

## Pipeline

The concept images, the product screens (they show NIV text) and the narration
audio are not committed (this repo is public; see `.gitignore`). The image
prompts are in `docs/RECIPROCAL-DOORS-IMAGE-PROMPTS.md`; re-capture the product
screens with `node scripts/reciprocal-doors-capture-product.mjs` (Remotion's
headless Chrome over the DevTools protocol, 1440×900 at 2×, Chinese and English
interface; it also rewrites `product/regions.json`, the rects the film points at).

```bash
# 1. direction → film script → narration scripts (stale takes are deleted)
python3 scripts/reciprocal-doors-direction.py apply
python3 scripts/reciprocal-doors-voice.py narration
# 2. narration, each take Whisper-checked as the film plays it (after tightening)
cd ../lucas-academy-media
PYTHONPATH=src .conda/bin/python ../lucas-academy-video/scripts/reciprocal-doors-retake.py zh
PYTHONPATH=src .conda/bin/python ../lucas-academy-video/scripts/reciprocal-doors-retake.py en
PYTHONPATH=src .conda/bin/python ../lucas-academy-video/scripts/reciprocal-doors-pace.py   # Chinese pace
cd ../lucas-academy-video
# 3. tighten (edges, pauses capped at 0.55 s) and check everything once more
../lucas-academy-media/.conda/bin/python scripts/reciprocal-doors-tighten.py
(cd ../lucas-academy-media && PYTHONPATH=src .conda/bin/python ../lucas-academy-video/scripts/reciprocal-doors-check.py zh)
# 4. one timeline per film + captions, then one -16 LUFS track per film
node scripts/reciprocal-doors-prep.mjs
../lucas-academy-media/.conda/bin/python scripts/reciprocal-doors-tracks.py
# 5. render the pictures (clean + subtitled), mux, describe
npx remotion render src/index.ts LanguageBridgeZhClean out/reciprocal-doors/video/picture.zh.clean.mp4 --muted
npx remotion render src/index.ts LanguageBridgeZhSubtitled out/reciprocal-doors/video/picture.zh.subtitled.mp4 --muted
#    (same for En)
scripts/reciprocal-doors-deliver.sh
python3 scripts/reciprocal-doors-youtube.py
```

`reciprocal-doors-fit.py` fits Chinese line lengths to the English for a single
picture carrying both tracks; it is not used now that the films are separate.

## Delivery (YouTube)

In `out/reciprocal-doors/delivery/`, per film (`zh`, `en`):

- `language-bridge.<film>.mp4` — clean picture; upload this with the captions.
- `language-bridge.<film>.zh-Hans.srt` / `.en.srt` — captions in both languages
  on that film's time codes (the film's own language is the main one).
- `language-bridge.<film>.subtitled.mp4` — subtitles burned in (Chinese film:
  Chinese + small English; English film: English only), for elsewhere.
- `youtube-description.<film>.txt` — title, description with chapters, tags.

## Checks that caught real slips

Whisper (medium, simplified-Chinese prompt, a whole-line match ≥0.94 zh / ≥0.9 en,
must / must-not words per line) on the *tightened* takes: dropped words (有些),
tone slips (练→脸, 倒 dǎo→dào, 讲→扬), erhua (事→事儿), extra syllables
("we can say tat", "答，"), a stressed "can" heard as "can't", a line read twice.
Two readings are forced with CosyVoice pinyin tokens in the spoken text only
(`杯子[d][ǎo]了`, `一起[j][iǎng]`).
