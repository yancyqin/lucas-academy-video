# Perceptron and optogenetics story shorts

Two independent 1080×1920, 30 fps films. English is the default audio; Chinese is a second audio track and a separate uploadable M4A. English and Simplified Chinese SRTs remain external. The common picture uses brief English teaching text, with no chapter/source/series badges or caption strip.

The owner requested condensed story versions of Family AI Lab 01 and Fun Informatics 4, prioritizing existing moving footage. Nine owner-made Muse clips cover every frame. Source audio is muted. Portrait crops keep the subject centered; near-square video inserts preserve the hand, notebook, goggles and camera details. Each shot plays forward once, without looping or a held poster. Newly arranged diagrams and the training-picture flow sit over the moving sources. See [source record](sources.md), [assets](assets.json) and both timelines for provenance, source windows and playback rates.

The revised perceptron story takes 74.2667 seconds with eleven cues: time travel → real-time race → measured speed → reveal → sum points → learn from examples → specialized-task caveat → family experiment → matrix multiplication → Lucas Academy learning invitation. The closing weighted sum is written as a row matrix times an input column. The QR and on-picture URL are removed at the owner's request. The race clock advances in real elapsed seconds even when the laboratory footage is slowed. All figures come from the preserved original full round: JavaScript median 0.3735265625 microseconds, rounded to 0.37 on screen, 10/10 correct; Claude 1.146 seconds, Astra 4.0476772495 seconds. No rerun, training experiment or contender API call was made. The copy keeps the owner's 3 million / 10 million headlines and the scope explanation.

The revised optogenetics story takes 74.7667 seconds with eleven cues: reaching for a notebook → algae → light-sensitive door → surviving relay cells → amber switch → encoding → decoding → training → limits → how brains process signals → a Lucas Academy invitation to explore how brains think and AI learns. It retains one patient, partial recovery, glasses still needed and normal vision not restored. Illustrative clips never claim to show the patient's actual visual experience. The general blue-light diagram and the patient's different amber-sensitive switch are distinguished in the narration.

Louise narrates both languages locally at 1.1 speed. The two introductory/headline cues in each language are exact checked full-film WAVs. Forty-four selected WAVs are checked against Whisper transcripts by SHA256. The first nine cues of each film retain the approved narration. Eight revised closing takes replace the old final questions and add the two learning invitations. A Chinese matrix line is retaken with two shorter sentences so the mathematical wording stays clear. The closing Chinese speech reads Lucas Academy as 卢卡斯学院 and AI as 人工智能, while the displayed copy keeps the concise English names. Medium-model rechecks resolve the selected retakes and key recognition ambiguities. ASR homophones, particularly 微秒/为秒 and 绿藻/绿枣, are recorded as transcription differences. The records do not claim a separate human listening review. Both audio mixes target −16 LUFS and −1 dBTP; delivered AAC levels are measured again. No music or Suno media is used.

Standalone entry `src/science-shorts.tsx` avoids modifying the shared main composition registry or package scripts. No worktree was created and the shared checkout's branch was not switched. Only the shorts' files are selected into the delivery commit based on fetched `origin/main`.

To rebuild using staged inputs and selected takes:

```sh
python3 scripts/science-shorts/prepare.py
.venv-align/bin/python scripts/science-shorts/mix.py
node scripts/science-shorts/render.cjs --movie
python3 scripts/science-shorts/verify.py
python3 scripts/science-shorts/package.py
python3 scripts/science-shorts/backup.py
```

Use `--film perceptron` or `--film optogenetics` for Python commands that accept it, and `--film=perceptron` / `--film=optogenetics` for the renderer. `node scripts/science-shorts/render.cjs --stills` creates layout frames without producing a movie.

Finished files are in `out/science-shorts/{perceptron,optogenetics}/`: bilingual MP4, independent EN/ZH M4As and EN/ZH SRTs. The revised desktop upload package is `/Users/yqin/Desktop/感知机与光遗传学-竖屏短片-v2/`. The original package remains untouched; v1 output files are also preserved under `out/science-shorts/archive/v1/`. Neither movie has embedded or burned subtitles. Nothing has been published to a video platform.

Revised inputs are backed up under `../lucas-academy-video-data/science-shorts-20261106-v2/` with SHA256SUMS and a refusal-to-overwrite restore script. The v1 backup remains separate. After restoring, use `python3 scripts/science-shorts/prepare.py --restored` to rebuild captions and timing directly from the preserved selected voices. This produces the same cue intervals and shot rates without requiring the old full-film public directories or regenerating narration.

Validation results are in [verification.json](verification.json): source/result hashes, selected voice hashes, frame counts and duration, both audio languages/default flags, zero subtitle tracks, matching external cues, exact standalone AAC payloads, final loudness, black-frame detection and absence of QR codes in both revised perceptron closing beats. Final-picture samples are in each output folder's `final-frames/`; production samples also check the start and end of the hand/product shots. `--stills --cues=p10,p11,o10,o11` previews only the new ending layouts.
