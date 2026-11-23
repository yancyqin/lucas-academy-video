# Video production conventions

## YouTube description order — owner confirmed 2026-11-22

- For every new or revised long-form upload, start each language's description with the complete timestamped chapter list. The first line is the first chapter (`0:00` / `00:00`); introductions, links, source credits, bylines and hashtags follow it.
- Use `scripts/youtube_text.py` when generating upload copy, and inspect the actual local upload text before handoff. Do not put an introduction or a chapter heading before the first timestamp. Do not invent chapters for Shorts or videos without chapters.
- After the owner edits a published description, read and archive their current wording verbatim. Published records document what the owner published; do not rewrite those historical records to make them pass a new-upload formatting check.
- Follow `docs/PRODUCTION-CHECKLIST.md` for native voice timing, Chinese spoken years, music fades, actual decoded motion cadence, and separate audio/subtitle delivery.

## Finished film archives

- Keep original recordings, approved voice performances, model weights and personal voice profiles out of Git.
- Keep final masters, reusable source media and shared museum assets outside Git. Preserve cross-project dependencies before removing intermediates. Record exact cleanup candidates and verify their hashes before deletion.
- Do not include unrelated work from another film or the shared museum UI in a production archive PR. Keep the museum's source and deployment in its own repository.
