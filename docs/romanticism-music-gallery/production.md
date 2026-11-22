# Approved production

The final master is **山、海、人间 / Mountains, Seas, and Mortals**: 1740.417
seconds, 1920 × 1080, 24 fps, instrumental music with English picture labels.
Separate English and Simplified Chinese SRTs are retained for the master and its
nature/human-life parts. The owner's selected Sierra frame is the unlettered
cover; its composition is preserved.

The opening label appears at 0.5 seconds: **From Gallery to Space**. The title
follows, then **Hear and see / how the Romantics saw the world**. The native IS
salon uses English signs; the final export verification found 43 overlays, 70
native signs and no Chinese picture labels.

The master retains five complete recordings: Chopin's Raindrop Prelude,
Nocturne Op. 9 No. 2 and C-sharp-minor Nocturne; Beethoven's Pathétique second
movement and Egmont Overture. The approved AAC payloads were copied without
re-encoding from v3. The master and both parts passed full decode and audio
payload comparisons. The preserved provenance distinguishes the composition
from the particular recording. Daniel Veesey's historical MP3 license tag and
FMA listing conflict is recorded rather than relabelled as confirmed CC0.

## Six portrait shorts

All six are 58 seconds, 1080 × 1920, 24 fps. Each approaches two complete
paintings in the current salon, zooms to selected details, and returns to the
gallery. English titles and artist names are in the picture; four timed Chinese
translations per film are in separate `.zh-Hans.srt` files. The music is a
continuous excerpt with short entrance/ending fades. There is no narration or
source-footage audio.

| Film | Paintings | Recording excerpt |
| --- | --- | --- |
| Facing the Vastness / 面对辽阔 | Wanderer above the Sea of Fog; Chalk Cliffs on Rügen | Chopin, Raindrop Prelude, 0:00–0:58 |
| Silence and Time / 寂静与时间 | Monk by the Sea; Abbey in the Oakwood | Chopin, Nocturne Op. 9 No. 2, 0:00–0:58 |
| Mountains and Light / 山峦与光 | The Heart of the Andes; Among the Sierra Nevada | Chopin, C-sharp-minor Nocturne, 0:14–1:12 |
| Two Faces of War / 战争的两张面孔 | The Wounded Cuirassier; The Charging Chasseur | Beethoven, Egmont Overture, 2:28–3:26 |
| Youth and Old Age / 青年与暮年 | The Voyage of Life: Youth; The Voyage of Life: Old Age | Beethoven, Egmont Overture, 0:40–1:38 |
| Hope and Freedom / 希望与自由 | The Raft of the Medusa; Liberty Leading the People | Beethoven, Egmont Overture, 8:02–9:00 |

The approved first sample is retained byte-for-byte. The latest *Mountains and
Light* closes in on the two waterfalls, at normalized image points
`(0.61, 0.73)` and `(0.46, 0.67)`, instead of the earlier valley/peak details.
*Hope and Freedom* connects a rescue signal with a raised flag. Those two
paintings remain original still images in the deterministic room; there is no
generative animation of the figures.

The final package passed browser playback, seeking and all 24 Chinese-caption
checks. Each export also passed full audio/video decode. All six were uploaded
through the Codex in-app browser and verified **Private**, with Chinese SRT
tracks and localized Chinese title/description. The receipt's last two platform
checks were still running at handoff; that historical state is preserved in
`delivery-summary.json`, not presented as copyright clearance.

## Archive and runtime layout

`scripts/romanticism-music-gallery/snapshot/` is a restorable text payload. It
mirrors the external production directory: base and v3 preparation history,
current v4 scripts/metadata, the approved first short, and the later batch.
`archive-manifest.json` records every payload hash and the original source hash.
The root credits payload deliberately comes from the corrected v4 provenance.
The final v4 credits are authoritative for recording attribution.

Absolute workstation paths are replaced with `@DATA_ROOT@`, `@UI_ROOT@`,
`@VIDEO_REPO@`, `@RUNTIME_DEPS@`, `@PLAYGROUND@` and `@USER_HOME@`. Restore expands
them for a selected external data directory. Keep the original sibling layout:
the workspace contains `inception-space-ui`, `lucas-academy-video` and
`lucas-academy-video-data/<production-folder>`. The helper rejects UI/workspace
overrides that conflict with relative paths in the original scripts.
Scripts still require the recorded
macOS tools/fonts, ffmpeg/ffprobe, Python with Pillow, and the bundled Node
Playwright runtime. This is a code/metadata archive, not a backup of the media.

From the video repository:

```bash
python3 scripts/romanticism-music-gallery/archive.py verify

# Dry-run first. Choose a new external folder if existing files differ.
python3 scripts/romanticism-music-gallery/archive.py restore \
  --data-root ../lucas-academy-video-data/romanticism-music-gallery-restored \
  --ui-root ../inception-space-ui

# Writes missing text/scripts only; never overwrites a differing file.
python3 scripts/romanticism-music-gallery/archive.py restore \
  --data-root ../lucas-academy-video-data/romanticism-music-gallery-restored \
  --ui-root ../inception-space-ui --apply
```

Restore the protected media separately before rendering. For v4, run
`v4/scripts/prepare_assets.py`, the native `v4/scripts/film.mjs` capture, then
`finish.py`, `verify.py` and `package_youtube.py` from the restored runtime.
The final finisher explicitly reads the three approved `v3/exports/*.mp4`
audio streams; those exports must remain available. The root's original PCM
program, five source recordings and source artwork files must also remain.

For shorts, the runtime batch's `prepare.py` accepts selected job IDs. Its
`capture.mjs` uses `ROMANTIC_SHORT_JOB` and supports `--plan`, `--qa` and
`--recapture`. **Use `--recapture` after changing camera/detail settings**:
otherwise existing chunk files are intentionally reused. Follow capture with
`finish.py`, inspect the final contact sheet, then package and verify the
Desktop player. `prepare.py` reads the canonical room catalog, so record a new
layout snapshot when deliberately adopting a different gallery layout.

Packaging is a local production operation. YouTube upload is separate and
requires an owner request; the reusable skill does not grant blanket permission
to upload or publish future files. Complete private links and screenshots are
kept in the local Desktop package's `资料/YouTube上传凭据/` folder.

## Shared native room and retained dependencies

`inception-space-ui` remains the sole implementation of the gallery. The video
archive references its catalogs, layout and renderer; it does not copy them.
`native-room.json` records the nine captured source hashes and the observed UI
HEAD. The matching room files were not all committed at archive time. Preserve
the native room captures until those source files have their own UI commit.

The long film also reads two existing Muse clips from the separate narrated
project, `raindrop-romanticism/production/v2/footage/O02-monastery.mp4` and
`O03-paris.mp4`. Its gallery-entry, Wanderer insert and owner cover frame are
in `v4/assets`. Keep those originals; this PR neither modifies the narrated
project nor requests new Muse/Suno generation, downloads or R2 writes.
