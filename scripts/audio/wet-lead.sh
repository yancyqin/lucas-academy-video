#!/usr/bin/env bash
# Convolution reverb on a lead vocal, blended by ear-percentage rather than by
# raw filter gain.
#
#   wet-lead.sh <lead.wav> <ir.wav> <wet-percent> <out.wav>
#
# Two things about afir that cost an hour here:
#
#  - `dry` is an INPUT gain, not a dry/wet mix control. `dry=0:wet=1` does not
#    give you the wet signal, it zeroes the input and returns digital silence.
#    Leave both at 1: afir's output is already the convolution alone.
#  - the output level follows the energy of the impulse response, and `gtype`
#    made no difference at all here (peak/none/rms/dc all measured -55.2 LUFS).
#    This plate lands 36 dB below the dry lead, so the tail has to be measured
#    and matched rather than assumed.
#
# Because that match is a +36 dB lift, the whole chain runs in one float graph;
# writing a -44 dBFS intermediate to 16-bit first would lift its quantisation
# noise right along with the reverb.
set -euo pipefail

lead=${1:?lead file}; ir=${2:?impulse response}; pct=${3:?wet percent}; out=${4:?out file}

WET_GRAPH="[0:a]aformat=channel_layouts=stereo[d];[d][1:a]afir=dry=1:wet=1:length=1[w]"

lufs_of() {  # read integrated loudness off an ebur128 summary on stdin
  sed -n '/Summary:/,$p' | awk '/^    I:/{print $2}'
}

dl=$(ffmpeg -hide_banner -nostats -i "$lead" -af ebur128=framelog=quiet -f null - 2>&1 | lufs_of)
wl=$(ffmpeg -hide_banner -nostats -i "$lead" -i "$ir" \
       -filter_complex "${WET_GRAPH};[w]ebur128=framelog=quiet" -f null - 2>&1 | lufs_of)

# Bring the tail to the dry lead's loudness, then scale to the requested blend.
match=$(awk -v d="$dl" -v w="$wl" 'BEGIN{printf "%.2f", d-w}')
wg=$(awk -v p="$pct" 'BEGIN{printf "%.4f", p/100}')
dg=$(awk -v p="$pct" 'BEGIN{printf "%.4f", 1-p/100}')

ffmpeg -v error -i "$lead" -i "$ir" -filter_complex \
  "${WET_GRAPH};\
   [w]volume=${match}dB,volume=${wg}[wv];\
   [0:a]aformat=channel_layouts=stereo,volume=${dg}[dv];\
   [dv][wv]amix=inputs=2:normalize=0[m]" \
  -map '[m]' -c:a pcm_f32le -y "$out"

printf '  %-24s dry %s / tail %s LUFS -> matched %s dB, %s%% wet\n' \
  "$(basename "$out")" "$dl" "$wl" "$match" "$pct"
