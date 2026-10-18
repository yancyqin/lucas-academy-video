# 焰火 · Fireworks | Light Up the Paintings

Debussy, *Feux d'artifice* (Préludes II/12), Stefano Ligoratti (live, CC BY 3.0, via IMSLP), 4:36. Seven dusk and
night paintings: each starts as a realistic scene, the light falls and we step into the painting; a flame carried
in lights it and the fuse, and every firework bursts on an accent of the music (owner 2026-10-18: 「焰火绽开要卡
节奏点上」). The fireworks are the art lab's living paintings (`lucas-visual-art-lab`, series `feux`,
`assets/living-fireworks.js`); this folder plans, captures and composes the film.

| # | Painting | From | Lit by |
|---|---|---|---|
| 1 | Monet, *San Giorgio Maggiore at Dusk* | 0:00 | match |
| 2 | Monet, *The Houses of Parliament, Sunset* | 1:01 | lamplighter's pole |
| 3 | Pissarro, *The Boulevard Montmartre at Night* | 1:45 | taper |
| 4 | Van Gogh, *Starry Night Over the Rhône* | 2:17 | sparkler |
| 5 | 北京城的夜 (our photo, AI-painted, from 月光) | 2:40 | incense stick |
| 6 | Whistler, *Nocturne in Black and Gold – The Falling Rocket* (the climax) | 3:06 | portfire |
| 7 | Monet, *The Rue Montorgueil, 30 June 1878* (the coda's distant Marseillaise) | 3:47 | torch |

Data: `lucas-academy-video-data/debussy-impressions/feux/` (`film/<id>/plan.json`, `frames-live/`, `section.mp4`;
`real/` before-photos; `tools/` painted tools). The 1.5 s of silence at 3:47 is a gated rest at the end of the
climax's fade: the Rocket fades to black there and Montorgueil fades in.

## Rebuild

All with `.venv-reframe/bin/python` from the repo root, scripts in `scripts/debussy-feux/`.

1. `accents.py music/normalized/feux-ligoratti-ccby3.wav feux/film/accents.json` (paths relative to the data
   folder): every onset with a local-salience accent score.
2. `feux_codex_run.py real | redo | tools`: Codex images — the scene before the light dims (round 2 = edits that
   keep the painting's composition), and the seven unlit tools on #FF00FF. `align_before.py` puts each photo on its
   painting as cropped for the art lab; `key_tools.py` keys the tools and finds where the flame goes.
3. `film_plan.py`: sections, light curve, tool path, camera and the shells (each `at` an accent: strongest first,
   ≥ 0.42 s apart, a loudness cap per 1.5 s) → `feux/film/<id>/plan.json`.
4. Capture: serve the art-lab worktree (`python3 -m http.server 8745`), run `film_sink.py <film dir> 8746`, open
   `living.html?w=feux-<id>` and for every plan frame call `__living.fireworks(show, {night, lamps})`,
   `__living.drawAt(t)` and POST `canvas.toDataURL('image/jpeg', 0.92)` to `/frame?name=<id>&i=<k>` (toBlob stalls in
   a hidden pane). About 40 fps.
5. `film_compose.py <id>`: photo dims and dissolves, camera on a glowing surround, the tool with its flickering flame
   (match / wick / taper / sparkler / incense / portfire / torch), the fuse sputter → `section.mp4`.
6. `film_assemble.py v1`: 1.5 s crossfades, music → `feux/film/feux-film-v1.mp4` + 720p review.
7. `youtube.py <upload dir>`: description (zh + en, chapters, credits, AI disclosure) and cover.

Checked on v1: every one of the 110 shells flashes within 2 frames of its accent in the final film; −18 LUFS.
