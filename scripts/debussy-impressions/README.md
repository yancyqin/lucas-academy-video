# Debussy × Impressionism films

The four Debussy films share these scripts. Their data (paintings, AI reconstructions, MiniMax clips, frames,
renders) lives in `lucas-academy-video-data/debussy-impressions`, not in git. MiniMax rules and lessons:
`MINIMAX-VIDEO-EXPERIENCE.md`.

- **大海 (La mer), 月光 (Clair de lune)** — an edit list per piece in `edits/`, rendered with the music by
  `render_piece.py`: each AI photo turns into its painting, cuts land on accents (`accents.py`, `snap_cuts.py`), MiniMax
  motion comes from `minimax_job.py` + `prep_anim.py`, and 月光 breathes with the melody (`breath_curve.py`,
  `plan_breaths.py`). 沉没的教堂 (`edits/02-cathedrale.json`) is parked.
- **牧神午后 (Prélude à l'après-midi d'un faune)** — 12 living paintings from the art lab, pipeline below.
- Shared: `commons_art.py` (public-domain paintings), `codex_prompts.py` + `align.py` (Codex reconstructions),
  `audio_report.py` / `normalize.py` / `listen_points.py` (recordings), `youtube.py` (title, description, cover).

## 牧神午后

1. `film_plan.py sections` — section starts and, per painting, the timings of painting, push-in, wand and look.
2. Per painting: `film_plan.py score ID` (strokes on the notes) → `lazy_painter.py plan` (strokes.json) →
   `film_plan.py live ID` (live.json, scene.json; needs the art lab's `snap.json`).
3. Living frames: `film_hook.py` makes the film copy of the art lab (`filmSnap`, `filmShow`, `filmCapture`); serve it
   on localhost:8741, run `frame_sink.py`, call `__living.filmCapture` in the browser, move the frames to
   `film/<id>/frames-live`.
4. Moving backgrounds: `minimax_job.py prepare/submit/poll` (3 renders a day; the quota resets at 09:00 PDT and extra
   submits are accepted, then fail) → `bg_loop.py` (slow down + seamless loop, or a speed `--curve`; `--stabilize`,
   `--freeze`) → scene.json `background_loop`. The background is only seen until the push-in ends.
5. `film_plan.py layout` — the easel stands in the scene at a painter's distance (horizon rule, `LAYOUT`, `GRASS`);
   the wide shot holds, the push-in starts halfway to the living painting.
6. `film_build.sh ID…` → `film/<id>/section.mp4` (oil frames from `lazy_painter.py render`, scene by `scene_compose.py`);
   `film_assemble.py OUT.mp4` joins the 12 sections with the music.
7. `youtube.py edits/04-faune.json OUTDIR` — separate Chinese and English titles and descriptions, tags, cover.
