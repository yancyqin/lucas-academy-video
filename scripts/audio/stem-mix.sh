#!/usr/bin/env bash
# Mix a subset of stems (Demucs or Suno) back into one file.
#
#   stem-mix.sh [--peak DBFS] [--lufs TARGET] <stem-dir> <out-file> <stem[:gainDB]> ...
#
# Stems sum back to the original mix, so picking a subset is how you drop an
# instrument, and a negative gain is how you just push one down instead:
#
#   stem-mix.sh "$dir" out.mp3 vocals bass drums           # minus guitar/keys/synth
#   stem-mix.sh "$dir" out.mp3 vocals drums bass synth:-9  # keeps synth, 9 dB down
#
# The stems of a mastered song sum back to the pre-limiter peaks, which overshoot
# full scale, so the mix is measured and trimmed to --peak (default -1 dBFS true
# peak) before encoding. Trimming is transparent; a limiter would not be.
#
# --lufs also matches integrated loudness across a set of alternate mixes, so
# they can be compared by ear fairly. The peak ceiling still wins over it.
set -euo pipefail

ceiling=-1.0; target=""
while true; do
  case "${1:-}" in
    --peak) ceiling=$2; shift 2;;
    --lufs) target=$2; shift 2;;
    *) break;;
  esac
done
dir=${1:?stem dir}; out=${2:?out file}; shift 2
[ $# -gt 0 ] || { echo "pick at least one stem" >&2; exit 1; }

args=(); pre=""; mixin=""; n=0
for spec in "$@"; do
  s=${spec%%:*}
  gain=${spec#"$s"}; gain=${gain#:}   # empty when no :gain was given
  f="$dir/$s.wav"
  [ -f "$f" ] || { echo "no such stem: $f" >&2; exit 1; }
  args+=(-i "$f")
  pre+="[$n:a]volume=${gain:-0}dB[a$n];"
  mixin+="[a$n]"
  n=$((n+1))
done

if [ "$n" -eq 1 ]; then mix="${pre}${mixin}anull"
else mix="${pre}${mixin}amix=inputs=$n:normalize=0"; fi

# Pass 1: measure the raw sum. Pass 2: encode with just enough trim.
sum=$(ffmpeg -v info "${args[@]}" -filter_complex "${mix}[m];[m]ebur128=peak=true" \
        -f null - 2>&1 | sed -n '/Summary:/,$p')
peak=$(awk '/Peak:/{print $2}' <<<"$sum")
lufs=$(awk '/^    I:/{print $2}' <<<"$sum")
trim=$(awk -v p="$peak" -v c="$ceiling" -v i="$lufs" -v t="$target" 'BEGIN{
  room = c - p;                       # headroom to the peak ceiling
  d = (t == "") ? ((room < 0) ? room : 0) : ((t - i < room) ? t - i : room);
  printf "%.2f", d }')

ffmpeg -y -v error "${args[@]}" -filter_complex "${mix},volume=${trim}dB[out]" -map '[out]' \
  -c:a libmp3lame -b:a 256k "$out"
printf '%-38s <-  %s   (peak %s, %s LUFS, trim %s dB)\n' \
  "$(basename "$out")" "$*" "$peak" "$lufs" "$trim"
