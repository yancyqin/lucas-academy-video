# Publication cleanup

The owner authorized cleanup after publishing, including the Desktop upload
package. The package and three Word revisions were moved into the project rather
than discarded. Current delivery pointers were updated and the owner's live
English/Chinese descriptions were archived verbatim before any deletion.

The local cleanup plan lists each disposable binary with its size, SHA-256 and
reason. A separate protection manifest covers retained media and approved voice
fragments. All candidate hashes and every protected hash are checked before the
first deletion; protected hashes are checked again afterwards. Only those exact
listed files are deleted. Source code is kept locally as well as in the PR.

Removed categories are superseded exports, assembly chunks, delivery backups,
duplicate Annex-B capture streams, obsolete camera takes and short check renders.
The current master, native 60 fps museum MP4 captures, original/reusable footage,
art, approved audio, personal voice inputs and the shared salon are retained.
In particular, `production/v5/parts/walk-00.mp4` is protected because the separate
instrumental film references it. That film and unrelated Desktop files are
outside the cleanup scope.

The machine-local exact plans and digests remain in `production/v12/cleanup-*.json`.
The public [summary](cleanup-summary.json) records counts without personal paths.
Logical bytes removed may differ from physical free space on APFS because clones,
hard links and other processes share the volume. No deletion or publishing occurs
when verifying or restoring the text archive.
