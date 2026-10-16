"""Render one shot to a 1920x1080 / 30 fps H.264 clip of an exact length.

Stills get a slow Ken Burns move (subpixel-accurate, PIL); video is trimmed
from its marked window, slowed to fit when the window is short, cropped to
cover the frame. Optional per-shot fields:

  best_in_s, best_out_s   the clean window in the source
  crop      [x, y, w, h]  normalised crop of the source before scaling
  kenburns  {from, to}    normalised [x, y, w, h] rectangles for stills,
            or {path: [r1, r2, ...]} to move through several stops;
            with from/to, `ease` ("linear" default, "out" = glide to rest, "inout")
            and `hold` (seconds standing still on the last framing at the end)
  interp    true          motion-interpolate slowed footage instead of repeating frames
  grade     "<filters>"   ffmpeg filters applied after scaling (colour)
  fit       "contain"     show the whole source frame on black instead of filling
"""
import json
import pathlib
import re
import subprocess

import numpy as np
from PIL import Image

Image.MAX_IMAGE_PIXELS = None

W, H, FPS = 1920, 1080, 30
STILL_EXT = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp"}


def probe(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                        "stream=width,height:format=duration", "-of", "json", path],
                       capture_output=True, text=True)
    j = json.loads(r.stdout)
    st = j["streams"][0]
    return st["width"], st["height"], float(j["format"].get("duration") or 0)


def fit_rect(rect, iw, ih):
    """Normalised [x, y, w, h] -> pixel box with a 16:9 aspect, inside the image."""
    x, y, w, h = rect
    cx, cy = (x + w / 2) * iw, (y + h / 2) * ih
    bw = max(w * iw, h * ih * 16 / 9)
    bh = bw * 9 / 16
    if bw > iw:
        bw, bh = iw, iw * 9 / 16
    if bh > ih:
        bh, bw = ih, ih * 16 / 9
    x0 = min(max(cx - bw / 2, 0), iw - bw)
    y0 = min(max(cy - bh / 2, 0), ih - bh)
    return np.array([x0, y0, x0 + bw, y0 + bh], dtype=float)


def cover_box(iw, ih, scale=1.0):
    bw, bh = (iw, iw * 9 / 16) if iw / ih < 16 / 9 else (ih * 16 / 9, ih)
    bw, bh = bw * scale, bh * scale
    return np.array([(iw - bw) / 2, (ih - bh) / 2, (iw + bw) / 2, (ih + bh) / 2])


def _encoder(out):
    return subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                             "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264",
                             "-preset", "medium", "-crf", "16", "-pix_fmt", "yuv420p", str(out)],
                            stdin=subprocess.PIPE)


def render_still(rec, dur, out):
    im = Image.open(rec["path"]).convert("RGB")
    if max(im.size) > 6000:
        k = 6000 / max(im.size)
        im = im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS)
    iw, ih = im.size
    kb = rec.get("kenburns") or {}
    n = round(dur * FPS)
    if kb.get("path"):
        # several stops (e.g. whole -> Mary -> Jesus): eased moves between them,
        # so the camera settles briefly on each one
        stops = [fit_rect(r, iw, ih) for r in kb["path"]]
        segs = len(stops) - 1

        def at(u):
            k = min(int(u * segs), segs - 1)
            v = u * segs - k
            v = v * v * (3 - 2 * v)
            return stops[k] + (stops[k + 1] - stops[k]) * v
    else:
        if kb.get("from") and kb.get("to"):
            a, b = fit_rect(kb["from"], iw, ih), fit_rect(kb["to"], iw, ih)
        else:
            a, b = cover_box(iw, ih, 1.0), cover_box(iw, ih, 0.92)

        ease = kb.get("ease", "linear")

        def at(u):                     # linear: a long take should drift, not ease
            if ease == "out":          # glide in and come to rest (a pause in the music)
                u = 1 - (1 - u) ** 2
            elif ease == "inout":
                u = u * u * (3 - 2 * u)
            return a + (b - a) * u
    # `hold`: seconds at the end where the camera stands still on the last framing
    moving = max(n - round(float(kb.get("hold", 0)) * FPS), 1)
    p = _encoder(out)
    for i in range(n):
        box = at(min(i / max(moving - 1, 1), 1.0))
        p.stdin.write(im.resize((W, H), Image.BICUBIC, box=tuple(box)).tobytes())
    p.stdin.close()
    p.wait()


def bars(path, t0, length, iw, ih):
    """Crop black bars baked into archival transcodes (pillarboxed 4:3, film-gate edges)."""
    r = subprocess.run(["ffmpeg", "-hide_banner", "-ss", f"{t0:.3f}", "-t", f"{length:.3f}",
                        "-i", path, "-vf", "cropdetect=limit=0.1:round=2:reset=0", "-f", "null", "-"],
                       capture_output=True, text=True)
    found = re.findall(r"crop=(\d+):(\d+):(\d+):(\d+)", r.stderr)
    if not found:
        return ""
    w, h, x, y = map(int, found[-1])
    if w * h < 0.5 * iw * ih or (w > iw - 8 and h > ih - 8):
        return ""
    return f"crop={w}:{h}:{x}:{y},"


def render_video(rec, dur, out):
    iw, ih, total = probe(rec["path"])
    t0 = float(rec.get("best_in_s") or 0)
    t1 = float(rec.get("best_out_s") or total)
    window = max(t1 - t0, 0.5)
    speed = 1.0 if window >= dur else window / dur     # slow down rather than leave the window
    take = dur * speed
    if rec.get("crop"):
        x, y, w, h = rec["crop"]
        crop = f"crop=iw*{w}:ih*{h}:iw*{x}:ih*{y},"
    elif rec.get("bars"):
        crop = bars(rec["path"], t0, min(window, dur), iw, ih)
    else:
        crop = ""
    interp = (f"minterpolate=fps={FPS}:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1,"
              if rec.get("interp") and speed < 0.95 else "")
    grade = rec["grade"] + "," if rec.get("grade") else ""
    # 2% overscan hides thin black borders and edge junk in transcodes
    if rec.get("fit") == "contain":         # whole frame on black (e.g. the square Sun)
        frame = (f"scale={W}:{H}:force_original_aspect_ratio=decrease:flags=lanczos,"
                 f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:black,")
    else:                                   # 2% overscan hides thin borders and edge junk
        frame = (f"scale={round(W * 1.02)}:{round(H * 1.02)}:force_original_aspect_ratio=increase"
                 f":flags=lanczos,crop={W}:{H},")
    vf = f"setpts=(PTS-STARTPTS)/{speed},{interp}{crop}{frame}fps={FPS},{grade}format=yuv420p"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{t0:.3f}", "-t", f"{take + 0.3:.3f}",
                    "-i", rec["path"], "-vf", vf, "-t", f"{dur:.3f}", "-an", "-c:v", "libx264",
                    "-preset", "medium", "-crf", "16", str(out)], check=True)
