# Smooth museum revision (delivery v11)

The old v10 MP4 had regular 24 fps timestamps but repeated decoded frames:
49.37% of adjacent frame pairs in the history walking sample (302–312 s) were
nearly identical. Repeated `setpts` / `fps` passes over the old 24 fps capture
caused the visible cadence problem. See `old-cadence-audit.json`.

This revision renders the current native museum at 1920 × 1080, sampling the
camera at every **final** 1/60-second timestamp. A component-wise monotone
Hermite curve joins position, unwrapped yaw, pitch and field of view. It avoids
paragraph-by-paragraph speed changes and camera shake. The camera route is
checked against current pedestal obstacles. `camera-validation.json` records
the full route bounds. Named-work arrivals are aligned to the approved narration,
including the Raft, Vesuvius, Wanderer, Temeraire and Rain, Steam and Speed.
Museum readiness must confirm all 56 artworks, eight
sculptures, and Moose the Dragon loaded, with no failures.

The local `capture-server.mjs` production tool proxies the existing museum dev
server, which remains on port 8095. Its own recording controls are at
`http://127.0.0.1:8078/film-capture/`. Use its visible controls through the in-app
browser. It binds to localhost and does not deploy or modify the museum UI.
`capture.html` renders each frame, synchronizes WebGL completion, and applies
WebCodecs encoder backpressure. Interrupted recording resumes completed chunks.

`prepare.py` records the source UI commit and the actual dirty source-file
hashes. Re-run it before capture if the room layout changes. Delete or archive
affected **derived** capture chunks before resuming a changed camera plan.
Do not mix chunks from different routes. Source recordings and reference art
must remain untouched.

`compose.py` restores the approved portraits, full paintings, English artwork
labels, real footage and Muse inserts. Motion compensation is used only for
slow prerecorded inserts; museum frames are native new renders. The final
video has 59,128 frames at 60 fps (985.466667 s). This adds only 8.333 ms of
silent tail relative to the approved 985.458333 s audio timeline. It does not
move a sentence or stretch either voice.

The approved v10 English mix, Chinese independent audio, and both SRT files
are preserved byte for byte in `delivery/`. No cloud generation is requested.
`validate.py` fully decodes the export, measures actual moving frames, checks
60 fps / frame count, and verifies the audio and caption hashes. Static art
appreciation is intentional and must not be classified as a capture failure.

Run `install.py` only after checks pass. It atomically refreshes the existing
Desktop package, saves a prior-version archive here, retains both covers,
descriptions and Word scripts, and prepares the private YouTube upload manifest.
It never deletes or changes the visibility of an existing YouTube video.
