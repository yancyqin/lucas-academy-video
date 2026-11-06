# The tiny pipe — bilingual animated review

The owner requested a story adaptation of the zero-and-one lesson and selected full bilingual narrated animation on 2026-11-05. The original opening is in `lucas-academy-ai/L1-beginner/course.md`; curriculum revision and frozen asset hashes are in [sources.json](sources.json). [Story and shot plan](../../FAMILY-AI-LAB-02.md), [Chinese](zh-script.md), [English](en-script.md).

## Delivery

- Opening preview: `out/family-ai-lab-02/delivery/opening-preview.mp4`, 30 seconds, both audio tracks.
- Movie: `out/family-ai-lab-02/delivery/family-ai-lab-02.bilingual.mp4`, 4:23.1, 7,893 frames.
- Default English audio and independent Chinese audio; separate tracks also in `out/family-ai-lab-02/audio/en.m4a` and `zh.m4a`.
- External subtitles: `out/family-ai-lab-02/delivery/en.srt` and `zh-Hans.srt`.
- Final script/voice selection hashes: [script-revision.json](script-revision.json). Delivery verification is recorded in `verification.json` beside this document.

## Picture

One shared 1920×1080 picture at 30 fps. Labels are short English phrases. The MP4 has no subtitle tracks, burned captions or reserved subtitle band. SRT files are delivered separately.

Mia and Leo, the treehouses, paper note, pipe, beads, codebooks, branching trees, boxes and picnic are original code-drawn animation. The received counter and letters use the actual bead arrival times. `prepare.py` derives codes from character values and verifies the complete message and four-question box path. It also verifies the worst-case depth of the ten-box question tree. Existing fruit images retain their original MIT credit; worksheets are owner originals.

The online lab is an unmodified snapshot, operated using its real All off / Weight controls. [Capture receipt](capture.json) records the actions, result and media hash. Both source and local live-page snapshot are retained; the public site was retrieved with curl after the web reader could not open it.

## Voice and sound

Louise narrates both languages at 1.1 speed. Each take is immutable once generated; changed wording gets a new numbered take. Whisper small checks every selected take; ambiguous readings get medium checks or replacement takes. The selected WAV SHA256 values, caption text and actual duration bind audio to the common picture intervals. New scripts live in [voice.en.json](voice.en.json) and [voice.zh.json](voice.zh.json); final selection and transcription evidence are recorded beside them.

All 72 selected takes have inspected small-model transcripts; uncertain terminology and figures retain the medium-model evidence. Eighteen selected takes are replacements, including three edits with source hashes and retained intervals. English uses little ball rather than bead, and explicitly says the letter A and the word play. The Chinese fruit question uses 种子. Caption spelling is not replaced with ASR errors: raw numeral formats, script variants, names and homophone/tonal deviations remain visible in [narration-qa.json](narration-qa.json).

The Chinese fruit-explanation take omits a generated final 哦 after the complete sentence; the scope take omits unrelated generated speech after 够. The light explanation retains the complete off/on clause and omits its ambiguous opening. Original and edited WAVs and the exact edit receipts are preserved. `trim_take.py` creates a new immutable edited take with a ten-millisecond fade; it never changes the original.

Each line starts 0.1 seconds after its cue begins. Cue duration fits the longer language, the demonstrated action and a 0.4-second gap; the final question holds five more seconds. No speech is stretched or cut to fit. The PLAY sequence deliberately leaves room for all 32 beads to arrive. English and Chinese external captions follow their own speech duration within the shared cue boundaries.

Original procedural celesta music and bead/answer sounds use the reproducible score and synthesis recipe in `soundtrack.py`. There are no acquired music tracks or samples. Each voice line is leveled to −23 LUFS before mixing; music uses the repository's per-language ducking envelope, −20 dB under speech / −9 dB in gaps of at least 0.8 seconds, 0.35-second advance and 0.8-second recovery. The final mixed tracks are normalized to −16 LUFS / −1 dBTP and measured after AAC encoding. Browser source footage is muted.

## Rebuild

```sh
npm run fal02:prepare
npm run fal02:capture
npm run fal02:voice:en
npm run fal02:voice:zh
npm run fal02:voice:check
# Inspect transcripts and commit explicit voice-choices.json decisions.
npm run fal02:voice:select
npm run fal02:timeline:voiced
npm run fal02:voice:mix
npm run fal02:stills
npm run fal02:final
npm run fal02:check
npm run fal02:backup
```

The private sibling media runtime and Louise profile are required for new synthesis only. At most two TTS processes run, with three Torch threads each. Existing cached normalizer files are used; unrelated language packs are not fetched. `.venv-align` supplies audio, image, QR and Whisper dependencies. Browser capture uses the bundled Playwright runtime and installed Chrome. No Suno downloads, Cloudflare writes or curriculum changes are needed.

The renderer uses 2,400-frame ranges, two workers and bounded media caches, with a fresh Chromium process per range. Completed chunks have exact frame-count checks and content hashes under a source/props fingerprint; the picture is concatenated before the two full-length audio tracks are muxed. SRTs are copied beside the MP4 and never muxed.

Media stays ignored in Git. Restore the data backup into an empty target, verify SHA256SUMS, then rebuild from the selected WAVs; no voice profile is needed for that route. The backup's restore script refuses differing destination files.

## Final validation

Final MP4: 7,893 video frames, default English plus Chinese AAC, no subtitle tracks, no detected black segments. Both final AAC tracks measure −16.03 LUFS, true peaks −0.97 / −0.98 dBTP. The course QR decoded from the actual lab and end frames at 1080p and 720p. All 13 frozen source hashes, 72 selected voice hashes/settings and 36 cue pairs per external SRT passed. TypeScript and diff checks passed. The data backup restored 95 public inputs into an empty folder and compared every file byte for byte. See [verification.json](verification.json).
