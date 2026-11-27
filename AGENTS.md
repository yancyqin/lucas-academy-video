# Video production conventions

## Mandatory global QA — owner confirmed 2026-11-26

- Every video, preview and revision must pass `scripts/qa/qa.py check` and `gate` before delivery, packaging or upload. Film-specific checks supplement the shared gate; they do not replace it. Read `docs/PRODUCTION-CHECKLIST.md` first.
- Check the video's own audio and every additional language track separately. Gates apply to the actual final media bytes, spec, subtitles and voice source. Re-run after changes; do not reuse a green report from an older export.
- Record genuine final-audio human review with `qa.py final-review`, or the owner's explicit approval of that exact version. ASR, successful decoding, quiet tails and sample preservation are not evidence that a final syllable was fully spoken or connected speech sounds natural. Do not claim ear-listening when tools cannot hear.
- An existing explicit owner approval is valid review evidence: record it, do not ask the owner to approve the same version again. It cannot waive hard technical failures. Preserve unresolved findings and state concrete limitations.
- Add new narration slips to `scripts/qa/pitfalls.json` and preserve the lesson in the shared checklist. See `docs/qa-lessons/memory-audio-2026-11-26.md` for the clipped 色 and unnatural predict connection.

## YouTube description order — owner confirmed 2026-11-22

- For every new or revised long-form upload, start each language's description with the complete timestamped chapter list. The first line is the first chapter (`0:00` / `00:00`); introductions, links, source credits, bylines and hashtags follow it.
- Use `scripts/youtube_text.py` when generating upload copy, and inspect the actual local upload text before handoff. Do not put an introduction or a chapter heading before the first timestamp. Do not invent chapters for Shorts or videos without chapters.
- After the owner edits a published description, read and archive their current wording verbatim. Published records document what the owner published; do not rewrite those historical records to make them pass a new-upload formatting check.
- Follow `docs/PRODUCTION-CHECKLIST.md` for native voice timing, Chinese spoken years, music fades, actual decoded motion cadence, and separate audio/subtitle delivery.

## Finished film archives

- Keep original recordings, approved voice performances, model weights and personal voice profiles out of Git.
- Keep final masters, reusable source media and shared museum assets outside Git. Preserve cross-project dependencies before removing intermediates. Record exact cleanup candidates and verify their hashes before deletion.
- Do not include unrelated work from another film or the shared museum UI in a production archive PR. Keep the museum's source and deployment in its own repository.
