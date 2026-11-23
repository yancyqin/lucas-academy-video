# Published film: production and recovery

## Final delivery

`v11-smooth60` is the owner-published 60 fps film. The local production folder is
`lucas-academy-video-data/raindrop-romanticism/production/v12`; the Desktop upload
package was moved into its `published-release/` directory after publication.
`production/latest.json` and current delivery records point there. The package
includes the English movie, Chinese WAV/M4A, both SRTs, both warm-gallery covers,
Word scripts and a local bilingual preview. Earlier Desktop Word revisions are
kept under `published-release/文案修订/`.

The production path `v12/delivery/01-English-full.mp4` is a relative symlink to the
archived package's canonical master. The final picture has 59,128 actual frames
at 60 fps and runs 985.4667 seconds. The approved audio mixes and subtitle files
are unchanged from the preceding approved delivery. Chinese speech retains its
natural speed; language timing differences use silence rather than stretching.
The scene includes the Chopin/Sand portrait reconstruction. The guide character
was cancelled by the owner.

## Motion correction and validation

Tagging repeated frames as 60 fps did not fix the older recording's cadence.
The final museum walk was rendered frame by frame at its final timeline using a
continuous monotone Hermite camera curve and the current salon layout. It retains
56 paintings and nine plinths, including Dragon. Camera tests found no boundary
collisions; maximum travel speed was 3.741 m/s and maximum turn rate 25.197°/s.
Arrival timing was adjusted for the Raft, Vesuvius, Wanderer, Temeraire and Rain,
Steam and Speed. Painting appreciation intentionally holds still.

Validation decoded all 59,128 frames with FFmpeg's error gate, checked 1080p60,
separate subtitles, master duration and retained audio/caption hashes. The former
302–312 second walking interval's near-duplicate fraction fell from 49.37% to
zero. The nature arrival sample contains an intentional slow approach/hold; its
near-identical frames are reported rather than concealed. Museum frames are
native captures; motion interpolation is restricted to slowed prerecorded inserts.
No new cloud generation was needed for the smooth revision or archive cleanup.

## Descriptions and publishing

The owner published the film. The current English/Chinese descriptions were read
from Studio and saved verbatim before cleanup. Their chapter headings are part
of that historical record and are preserved. Future generated descriptions must
start directly with the first `0:00` / `00:00` chapter, followed by the complete
chapter list; introductions, credits, links and hashtags come afterwards.
The owner's current wording must never be overwritten by an older local draft.

## Rebuilding

```bash
python3 scripts/raindrop-romanticism/archive.py verify
python3 scripts/raindrop-romanticism/archive.py restore \
  --data-root /path/to/playground/lucas-academy-video-data/raindrop-romanticism
# Add --apply only for a new, empty destination after reviewing the dry run.
```

The text snapshot replaces machine paths with documented tokens. Restore expands
them for the selected sibling workspace and refuses to overwrite differing files.
It does not recover media, fetch models, generate voices or publish anything.
The versioned scripts are a historical production record, not a one-command build.

Retain native `v12/raw/walk-*.mp4` captures, approved narration fragments and the
MiniMax performance sources, Muse/stock footage, original paintings/photos,
portrait assets and music. `v12/compose.py` also reads the six approved audio/
subtitle files in `v11/delivery`; those inputs remain protected. The archived
capture plan records the shared UI commit and working-file hashes. A fresh 3D
capture additionally requires the private `inception-space-ui` repository and its
exact salon assets; a Git commit alone does not reproduce its uncommitted layout.
No private UI implementation is copied into this public archive.

Use the production Python environment with NumPy and Pillow, FFmpeg/FFprobe, and
Node for capture. Native browser capture requires the current museum server.
The retained MP4 captures support recomposition without rerendering the room.
A missing `parts/` directory after cleanup is expected; the validator checks
intermediate freshness only while such intermediates exist.

## Reusable production lessons

- Keep the owner's approved words and retake only the requested sentences.
- Chinese spoken years use individual digits (for example, 1838 → 一八三八).
- Start the opening voice without music; restart Raindrop at the listening cue.
- Fade music in and out at joins; check the complete final audio for clicks.
- Preserve natural voice timing in both languages; pad silence to align scenes.
- Inspect actual decoded motion, especially slow approaches, rather than trusting
  frame-rate metadata or silently duplicating screen recordings.
- Keep subtitles external and exhibition labels in English for this film.
- Save the owner's live descriptions before cleaning an upload package.
