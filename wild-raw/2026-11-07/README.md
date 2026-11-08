# The Wild — approved raw recording, 2026-11-07

The owner approved this recording and requested that its source footage,
recording scripts and English prompt reconstruction be committed together.
This package is tracked in Git, following the repository's standalone
`roller-coaster-final/` package convention.

## Review and source files

- [1080p/30 fps master](the-wild-raw-1080p30.mp4): 51 seconds, 1,530 frames.
- [720p review copy](the-wild-raw-preview-720p.mp4).
- [Eight independent takes](takes/), in the order below.
- [Original real-time touch recording](source/page@37fb68941802b55514f24054e2f06b2e.webm),
  including setup before the selected four-second take.
- [Frame stills](stills/) and [review contact sheet](review-contact-sheet.jpg).
- [Capture manifest](capture-manifest.json), [verification](verification.json)
  and [file checksums](SHA256SUMS).
- [English prompt reconstruction](reconstructed-prompt.en.txt).

The videos have no added captions, prompt animation, narration, music or
closing copy. The game's stamina, quality and touch controls remain visible.
The first take preserves walking, sprinting, jumping and gliding as one
continuous sequence. The assembly cuts between the separately recorded takes.

| Take | Content | Seconds | Assembly span |
| --- | --- | ---: | --- |
| 01 | Walk, sprint, jump and glide over the meadow | 14 | 00:00–00:14 |
| 02 | Climb, lunge and mantle onto the plateau | 8 | 00:14–00:22 |
| 03 | Swim along the coast | 5 | 00:22–00:27 |
| 04 | Whispering Forest | 5 | 00:27–00:32 |
| 05 | Frost Peaks | 5 | 00:32–00:37 |
| 06 | Sunset Dunes | 5 | 00:37–00:42 |
| 07 | Low, Medium and High quality controls | 5 | 00:42–00:47 |
| 08 | Touch movement, jump and glide | 4 | 00:47–00:51 |

## Capture provenance

The real browser page is `https://is.lucasacademy.org/wild/`. The captured UI
build is `80031829439353e2fc6824ddfc442fd1e8d55944`, released by
[inception-space-ui PR #135](https://github.com/yancyqin/inception-space-ui/pull/135).
Later changes to the live page can produce different footage.

The action and region takes use the page's existing debug/manual clock to
advance its real physics and renderer by exactly 1/30 second per output frame.
Debug positioning sets up each separate take; it is not shown as visitor travel.
The touch take runs in real time with actual Chrome multitouch events and an
emulated touch viewport. It is not a recording of a physical iPad.

Capture-only CSS hides the loading overlay, temporary controls hint, transient
region heading and debug statistics. No game code, physics, scenery, lighting,
models or production data was changed. The assembly normalizes encoding to
H.264, limited-range Rec.709; the original takes retain their recorded bytes.

The original English prompt was deleted. The separate prompt file is an
approximation based on the owner's recollection: an open world, climbing,
gliding and *The Legend of Zelda: Breath of the Wild*. It is not a recovered
quotation and is not burned into these videos.

## Verify this approved package

From the repository root, with Node.js, Python 3, FFmpeg and FFprobe installed:

```bash
cd wild-raw/2026-11-07
shasum -a 256 -c SHA256SUMS
python3 finish-wild.py --verify-only
node --check record-wild.mjs
```

The verifier checks the eight clip hashes, dimensions, frame counts, captured
states/events and master checksum, then fully decodes the master. The original
review also checked for black frames and visually inspected the contact sheet.

## Rebuild an assembly or record another take

Work in the ignored `out/` directory so approved source files stay intact:

```bash
mkdir -p out/wild
cp -R wild-raw/2026-11-07 out/wild/rebuild
python3 wild-raw/2026-11-07/finish-wild.py --dir out/wild/rebuild
```

Recording also requires Google Chrome and Playwright. By default, the script
uses the same bundled Codex Playwright runtime as the existing cube capture
pipeline. Set `PLAYWRIGHT_DIR` to a directory containing `package.json` and a
resolvable `playwright` package when using another installation. Playwright's
FFmpeg component must be installed for the real-time touch take.

```bash
node wild-raw/2026-11-07/record-wild.mjs --out out/wild/recapture
python3 wild-raw/2026-11-07/finish-wild.py --dir out/wild/recapture
```

`--only 05-frost-peaks,08-touch-controls` resumes selected takes in an existing
working directory. `--url` selects a local or published Wild page, `--date`
sets the recorded date, and `--commit` records a source revision you have
verified for that URL. Without `--commit`, a new recording records its source
revision as `unknown`. The script requires an explicit `--out` directory.

The files in this approved package were copied from the reviewed Movies
delivery and checked by SHA-256. They were not re-recorded during repository
import. Script portability changes replace the temporary Playwright path,
require a working directory and add verification without rebuilding.
