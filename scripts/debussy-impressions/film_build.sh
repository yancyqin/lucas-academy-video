#!/bin/zsh
# film_build.sh ID... — for each painting: the oil painting frames, then the section video (picture only).
PY=/Users/yqin/repo/playground/lucas-academy-video/.venv-reframe/bin/python
S=/Users/yqin/repo/playground/lucas-academy-video/.claude/worktrees/information-theory-video-plan-d0f6c2/scripts/debussy-impressions
F=/Users/yqin/repo/playground/lucas-academy-video-data/debussy-impressions/faune/film
for id in "$@"; do
  read t0 p0 p1 < <($PY -c "import json;c=json.load(open('$F/$id/scene.json'));print(c['live_start'],c['camera'][0],c['camera'][1])")
  if [ ! -d "$F/$id/frames-paint" ] || [ "$(ls $F/$id/frames-paint | wc -l)" -lt 10 ]; then
    $PY $S/lazy_painter.py oil $F/$id/target.png $F/$id/strokes.json $F/$id/frames-paint --to $t0 --relief $p0 $p1 > /dev/null || { echo "$id oil FAILED"; continue; }
  fi
  $PY $S/scene_compose.py $F/$id/scene.json $F/$id/section.mp4 > /dev/null && echo "$id done $(ffprobe -v error -show_entries format=duration -of csv=p=0 $F/$id/section.mp4)s" || echo "$id compose FAILED"
done
