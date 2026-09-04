#!/usr/bin/env python
"""Lay evenly spaced frames from a video out in a grid, to eyeball a clip without playing it.

  ./.venv/bin/python contact_sheet.py outputs/clip.mp4 [count] [cols]

Streams the file rather than decoding it whole, so pointing this at a finished
film instead of a short generated clip is safe.
"""

import os
import sys

import av
import numpy as np
from PIL import Image, ImageDraw


def frame_count(path):
    with av.open(path) as container:
        stream = container.streams.video[0]
        if stream.frames:
            return stream.frames
        # Some containers do not carry a count; demuxing packets is still cheap
        # because it never decodes.
        return sum(1 for _ in container.demux(stream))


def grab(path, wanted):
    """Decode once, keeping only the frames whose index is in `wanted`."""
    keep, remaining = {}, set(wanted)
    with av.open(path) as container:
        stream = container.streams.video[0]
        stream.thread_type = "AUTO"
        for i, frame in enumerate(container.decode(stream)):
            if i in remaining:
                keep[i] = frame.to_ndarray(format="rgb24")
                remaining.discard(i)
                if not remaining:
                    break
    return [keep[i] for i in wanted if i in keep]


def contact_sheet(path, count=8, cols=4, scale=0.5):
    total = frame_count(path)
    picks = sorted(set(np.linspace(0, total - 1, count).round().astype(int).tolist()))
    frames = grab(path, picks)

    h, w = frames[0].shape[:2]
    tw, th = int(w * scale), int(h * scale)
    rows = (len(frames) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * tw, rows * th), "black")

    for slot, (index, frame) in enumerate(zip(picks, frames)):
        tile = Image.fromarray(frame).resize((tw, th), Image.LANCZOS)
        draw = ImageDraw.Draw(tile)
        draw.text((7, 5), f"{index}", fill="black")
        draw.text((6, 4), f"{index}", fill="yellow")
        sheet.paste(tile, ((slot % cols) * tw, (slot // cols) * th))

    out = os.path.splitext(path)[0] + "-sheet.png"
    sheet.save(out)

    # A dead or collapsed clip shows up in these two numbers before it does to the eye.
    stack = np.stack(frames).astype(np.int16)
    motion = np.abs(np.diff(stack, axis=0)).mean() if len(frames) > 1 else 0.0
    print(f"{total} frames  {w}x{h}")
    print(f"mean pixel value {stack.mean():6.1f}   (0 or 255 = blank clip)")
    print(f"change between sampled frames {motion:6.2f}   (near 0 = nothing moves)")
    print(out)
    return out


if __name__ == "__main__":
    args = sys.argv[1:]
    contact_sheet(args[0], *(int(a) for a in args[1:3]))
