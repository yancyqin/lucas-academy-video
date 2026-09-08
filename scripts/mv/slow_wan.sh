#!/bin/bash
# Stretch a Wan clip to the length its shot needs, forward only.
#
# setpts multiplies presentation timestamps, so the clip plays once, slowly. There
# is no reverse leg and no wrap: the plan forbids boomerangs because a shot about
# light filling the world cannot have the light drain back out, and a loop seam in
# a single-pass clip is visible anyway.
#
# minterpolate uses `blend`, not `mci`: motion compensation invents vectors on
# cloth, cloud and water and warps them. The raw file is never overwritten.
#
#   slow_wan.sh <raw.mp4> <out.mp4> <target-seconds>
set -euo pipefail
RAW=$1; OUT=$2; TARGET=$3
[ -f "$RAW" ] || { echo "missing raw: $RAW" >&2; exit 1; }
SRC=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$RAW")
# Overshoot proportionally: interpolation drops the tail, and at 6.5x a flat +0.4s
# margin still landed 0.4s short of the target.
FACTOR=$(python3 -c "print(f'{($TARGET*1.07+0.6)/$SRC:.6f}')")
echo "$(basename "$RAW"): ${SRC}s -> ${TARGET}s  (setpts ${FACTOR}x, single pass)"
ffmpeg -v error -y -i "$RAW" \
  -vf "setpts=${FACTOR}*PTS,minterpolate=fps=30:mi_mode=blend,scale=1920:1080:force_original_aspect_ratio=increase:flags=lanczos,crop=1920:1080" \
  -t "$TARGET" -r 30 -c:v libx264 -crf 17 -preset medium -pix_fmt yuv420p -an "$OUT"
GOT=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT")
echo "  wrote $(basename "$OUT")  ${GOT}s"
