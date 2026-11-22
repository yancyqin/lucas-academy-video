# Cleanup preparation · 2026-11-21

No media or working data has been removed. The read-only inventory identifies
reproducible assembly files while keeping the approved outputs and source
dependencies. The video PR should be merged and verified before code copies are
removed from local production data.

The inventory contains **229 candidate files, about 3.73 GB of logical file
sizes**. These are assembly intermediates in `parts/`, `stages/`, `chapters/`,
the v2/v3/v4 `parts/` folders, the six shorts' `parts/` folders, and Python
bytecode caches. APFS clones can share storage, so this is not a promise of
physical disk space recovered. The complete local file list is retained as
`romanticism-music-gallery/checks/cleanup-inventory-20261121.json` outside Git.

| Keep | Why |
| --- | --- |
| `v4/exports/` and the Desktop short upload package | Approved master, parts and six uploaded shorts; subtitles, upload copy and private receipts remain useful for publication. |
| `v3/exports/` | The current v4 finisher copies its exact approved AAC streams from these files. Its name alone does not make it disposable. |
| `audio/`, `music/`, `art/`, `footage/` and `v4/assets/` | Approved program, exact source recordings, original paintings, reused clips and the owner's cover frame. |
| Native room capture folders | Matching room source is not yet fully committed in `inception-space-ui`; retain the captures until that separate archive is secure. |
| Timelines, scripts, source credits, subtitles and verification records | Rebuild and attribution evidence; text copies are now in this PR. |
| Local private YouTube receipts and the installed upload skill | Private links and account screenshots remain local; the portable skill is also committed under `.agents/skills/`. |
| The separate narrated-film project and shared salon data | Another production's active work and the reused monastery/Paris inserts are outside this cleanup's scope. |

Generate a fresh inventory immediately before a later cleanup:

```bash
python3 scripts/romanticism-music-gallery/archive.py inventory \
  --data-root ../lucas-academy-video-data/romanticism-music-gallery \
  --output ../lucas-academy-video-data/romanticism-music-gallery/checks/cleanup-inventory-latest.json
```

The command lists individual candidates and their exact containing folders. It
has no delete mode. Do not delete a parent directory merely because some child
files are candidates, and do not remove `v3` or `v4` wholesale. Reconfirm current
dependencies if the production changes after this inventory.
