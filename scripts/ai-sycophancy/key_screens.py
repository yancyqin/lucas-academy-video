"""Darken the green phone and laptop screens in the staged clips, frame by frame (run after assets.py).

  /Users/yqin/repo/playground/lucas-academy-video/.venv-reframe/bin/python scripts/ai-sycophancy/key_screens.py [G1 G3 ...]

For each green-screen clip in public/ai-sycophancy/clips/: the screen is the biggest patch of the clip's own green
(HSV, around the colour sampled from it), plus any patch at least a third that size (a finger can split a screen in
two); smaller green things in the room, such as a globe's sea, stay as they are. The screen's edge is softened, green
spill is taken out of whatever touches it (fingers), and the screen becomes SCREEN. A clip is done once: the original
is kept beside it as <clip>.plain.mp4, and running again starts from that. The masks are the start of the real
composite (the chat drawn into the screen), which still needs the screen's corners tracked.
"""
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
CLIPS = ROOT / "public/ai-sycophancy/clips"
# hue (OpenCV, 0-180) of each clip's screen and the darkest value it reaches (G5 is filmed in a dim room)
GREEN = {"G1": (64, 120), "G3": (77, 120), "G4": (78, 90), "G5": (65, 70)}
SCREEN = np.array([46, 37, 28], np.float32)  # BGR of #1c252e
# how far from the screen green spill is taken out; G3's thumb glows green well past the edge (a warm room, nothing
# else green in it), so there it is the whole picture
SPILL = {"G3": 0}
W, H = 1920, 1080


def screen_mask(bgr: np.ndarray, hue: int, vmin: int) -> np.ndarray:
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    m = cv2.inRange(hsv, (hue - 14, 90, vmin), (hue + 14, 255, 255))
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    n, labels, stats, _ = cv2.connectedComponentsWithStats(m)
    if n <= 1:
        return np.zeros(m.shape, np.float32)
    areas = stats[1:, cv2.CC_STAT_AREA]
    keep = [i + 1 for i, a in enumerate(areas) if a >= max(areas.max() / 3, 2000)]
    m = np.isin(labels, keep).astype(np.uint8) * 255
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
    return cv2.GaussianBlur(m, (5, 5), 0).astype(np.float32) / 255.0


def key(clip: str) -> None:
    plain = CLIPS / f"{clip}.plain.mp4"
    out = CLIPS / f"{clip}.mp4"
    if not plain.exists():
        out.rename(plain)
    fps = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=r_frame_rate", "-of", "csv=p=0",
                          str(plain)], capture_output=True, text=True).stdout.strip()
    dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", str(plain), "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], stdout=subprocess.PIPE)
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", fps, "-i", "-",
                            "-an", "-c:v", "libx264", "-crf", "19", "-preset", "medium", "-pix_fmt", "yuv420p", "-g", "15",
                            "-movflags", "+faststart", str(out)], stdin=subprocess.PIPE)
    hue, vmin = GREEN[clip]
    n, cover = 0, []
    while raw := dec.stdout.read(W * H * 3):
        f = np.frombuffer(raw, np.uint8).reshape(H, W, 3).astype(np.float32)
        a = screen_mask(f.astype(np.uint8), hue, vmin)
        # spill: in a band around the screen, green may not exceed the brighter of red and blue
        reach = SPILL.get(clip, 25)
        band = (cv2.dilate((a > 0.02).astype(np.uint8), np.ones((reach, reach), np.uint8)).astype(bool) if reach
                else np.ones(a.shape, bool))
        g = f[..., 1]
        if reach:
            g[band] = np.minimum(g[band], np.maximum(f[..., 0], f[..., 2])[band] + 8)
        else:  # whole picture: only greenish pixels, and skin keeps its warmth (green under 0.9 of red)
            greenish = (g > f[..., 2]) & (g > f[..., 0])
            g[greenish] = np.minimum(g[greenish], np.maximum(f[..., 0], 0.9 * f[..., 2])[greenish] + 2)
        f = f * (1 - a[..., None]) + SCREEN * a[..., None]
        enc.stdin.write(np.clip(f, 0, 255).astype(np.uint8).tobytes())
        cover.append(a.mean())
        n += 1
    enc.stdin.close()
    enc.wait()
    dec.wait()
    print(f"{clip}: {n} frames, screen {100 * min(cover):.1f}–{100 * max(cover):.1f}% of the picture", flush=True)


if __name__ == "__main__":
    for c in sys.argv[1:] or list(GREEN):
        key(c)
