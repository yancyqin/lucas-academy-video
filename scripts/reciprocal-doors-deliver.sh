#!/usr/bin/env bash
# Package the two Language Bridge (语言的桥) films for YouTube, one video per
# language. For each film:
#   language-bridge.<lang>.mp4             clean picture -- upload this with the SRT captions
#   language-bridge.<lang>.subtitled.mp4   the same with subtitles burned in (for sharing elsewhere)
#   language-bridge.<lang>.<caption lang>.srt   captions in both languages, on this film's time codes
# Inputs:
#   npx remotion render src/index.ts LanguageBridge{Zh,En}{Clean,Subtitled} out/reciprocal-doors/video/picture.<lang>.{clean,subtitled}.mp4 --muted
#   scripts/reciprocal-doors-tracks.py   (one -16 LUFS narration track per film + timing)
#   scripts/reciprocal-doors-prep.mjs    (captions)
#   scripts/reciprocal-doors-deliver.sh [zh|en ...]
set -euo pipefail
cd "$(dirname "$0")/.."

out=out/reciprocal-doors/delivery
mkdir -p "$out"
for lang in ${@:-zh en}; do
  iso=$([ "$lang" = zh ] && echo chi || echo eng)
  for cut in clean subtitled; do
    picture="out/reciprocal-doors/video/picture.$lang.$cut.mp4"
    [ -f "$picture" ] || { echo "skip $lang $cut: no $picture"; continue; }
    # (not $([ ... ] && echo ...): under set -e a false test there ends the script silently)
    if [ "$cut" = subtitled ]; then name="language-bridge.$lang.subtitled.mp4"; else name="language-bridge.$lang.mp4"; fi
    ffmpeg -y -loglevel error -i "$picture" -i "out/reciprocal-doors/$lang/language-bridge.$lang.wav" \
      -map 0:v:0 -map 1:a:0 -c:v copy -c:a aac -b:a 192k -ar 48000 \
      -metadata:s:a:0 language=$iso -disposition:a:0 default -movflags +faststart -shortest \
      "$out/$name"
    printf '%-40s %s s\n' "$name" "$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$out/$name")"
  done
  cp "out/reciprocal-doors/$lang/language-bridge.$lang.zh-Hans.srt" "out/reciprocal-doors/$lang/language-bridge.$lang.en.srt" \
     "out/reciprocal-doors/$lang/language-bridge.$lang.timing.csv" "$out/"
done
