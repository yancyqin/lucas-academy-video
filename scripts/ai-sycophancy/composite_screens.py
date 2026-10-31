"""Put the chat into the phone and laptop screens of the green-screen shots (G1–G5), frame by frame.

  /Users/yqin/repo/playground/lucas-academy-video/.venv-reframe/bin/python scripts/ai-sycophancy/composite_screens.py [G1 G5 ...]

Run after build_timeline.py and assets.py. For each shot:
1. What the screen shows is rendered from the AsScreen composition (src/videos/ai-sycophancy/Screen.tsx) at the
   screen's shape, as long as the clip; the shot's cues (edit.json, seconds into the shot) become seconds into the
   clip by the rate the clip plays at.
2. The screen is found in every frame of the plain clip (clips/<G>.plain.mp4): the green, as key_screens.py finds it,
   or for G2's white laptop the bright patch. Its four corners come from the convex hull (a finger cutting in leaves
   the hull alone), top edge first; handheld phones are smoothed over a few frames, the laptops (static) take one
   median quad.
3. The rendered screen is warped onto those corners and shown only where the screen is, so fingers stay in front;
   green spill is taken out of the fingers as in key_screens.py.
Writes clips/<G>.mp4 and, for a look, out/ai-sycophancy/screens/<G>-check.jpg (one frame, the quad drawn on it).
"""
import json
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from key_screens import GREEN, SCREEN, SPILL, screen_mask  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
CLIPS = ROOT / "public/ai-sycophancy/clips"
OUT = ROOT / "out/ai-sycophancy/screens"
W, H = 1920, 1080
PHONE, LAPTOP = (720, 1560), (1600, 1000)
SIZE = {"G1": PHONE, "G3": PHONE, "G5": PHONE, "G2": LAPTOP, "G4": LAPTOP}
STATIC = {"G2", "G4"}


def run(cmd, **kw):
    return subprocess.run(cmd, check=True, **kw)


def fps_of(path: Path) -> float:
    a, b = run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=r_frame_rate", "-of", "csv=p=0", str(path)],
               capture_output=True, text=True).stdout.strip().split("/")
    return float(a) / float(b or 1)


def frames(path: Path, w=W, h=H):
    dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", str(path), "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], stdout=subprocess.PIPE)
    while raw := dec.stdout.read(w * h * 3):
        yield np.frombuffer(raw, np.uint8).reshape(h, w, 3)
    dec.wait()


def mask_of(clip: str, bgr: np.ndarray) -> np.ndarray:
    if clip == "G2":  # a white laptop screen in a dark room: the biggest bright, colourless patch
        hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
        m = cv2.inRange(hsv, (0, 0, 170), (180, 50, 255))
        n, labels, stats, _ = cv2.connectedComponentsWithStats(m)
        return (labels == 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])).astype(np.float32)
    hue, vmin = GREEN[clip]
    return screen_mask(bgr, hue, vmin)


def corners(mask: np.ndarray, portrait: bool) -> np.ndarray:
    cs, _ = cv2.findContours((mask > 0.5).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    hull = cv2.convexHull(max(cs, key=cv2.contourArea))
    ap = cv2.approxPolyDP(hull, 0.02 * cv2.arcLength(hull, True), True).reshape(-1, 2)
    pts = ap.astype(np.float32) if len(ap) == 4 else cv2.boxPoints(cv2.minAreaRect(hull)).astype(np.float32)
    c = pts.mean(0)
    pts = pts[np.argsort(np.arctan2(pts[:, 1] - c[1], pts[:, 0] - c[0]))]  # clockwise on screen (y points down)
    length = [np.linalg.norm(pts[(i + 1) % 4] - pts[i]) for i in range(4)]
    pick = sorted(range(4), key=lambda i: length[i])[:2] if portrait else sorted(range(4), key=lambda i: -length[i])[:2]
    top = min(pick, key=lambda i: (pts[i][1] + pts[(i + 1) % 4][1]) / 2)
    return np.roll(pts, -top, axis=0)  # TL, TR, BR, BL


def smooth(q: np.ndarray, static: bool) -> np.ndarray:
    if static:
        return np.repeat(np.median(q, 0)[None], len(q), 0)
    pad = np.pad(q, ((2, 2), (0, 0), (0, 0)), mode="edge")
    med = np.stack([np.median(pad[i:i + 5], 0) for i in range(len(q))])
    pad = np.pad(med, ((2, 2), (0, 0), (0, 0)), mode="edge")
    return np.stack([pad[i:i + 5].mean(0) for i in range(len(q))])


def screen_props(clip: str, shot: dict, edit: dict) -> dict:
    rate = shot["rate"]
    w, h = SIZE[clip]
    props = {"kind": clip, "width": w, "height": h, "cues": [], "lines": []}
    if clip == "G1":
        props["cues"] = [a * rate for a in shot["msgsAt"]]
        props["lines"] = [m["zh"] for m in shot["msgs"]]
    elif clip == "G3":
        props["cues"] = [1.0]
    elif clip == "G5":
        at = shot["lineAt"] * rate
        props["cues"] = [at - 0.6, at + 2.0, at + 2.6]
        props["lines"] = ["我觉得孩子这篇作文写得挺好，对吧？", "如果不是，请诚实回答我。"]
    elif clip == "G4":
        props["cues"] = [a * rate for a in shot["itemsAt"]]
        first = next(s for s in edit["shots"] if s.get("head", "").startswith("我们照着她的处境"))["msgs"][0]["zh"]
        props["lines"] = [first]
    return props


def composite(clip: str, shot: dict, edit: dict) -> None:
    plain = CLIPS / f"{clip}.plain.mp4"
    if not plain.exists():
        (CLIPS / f"{clip}.mp4").rename(plain)
    fps = fps_of(plain)
    portrait = SIZE[clip] == PHONE
    OUT.mkdir(parents=True, exist_ok=True)

    quads = np.array([corners(mask_of(clip, f), portrait) for f in frames(plain)])
    quads = smooth(quads, clip in STATIC)
    seconds = len(quads) / fps + 0.5

    props = screen_props(clip, shot, edit) | {"seconds": seconds}
    (OUT / f"{clip}.props.json").write_text(json.dumps(props, ensure_ascii=False))
    ui_path = OUT / f"{clip}.mp4"
    run(["npx", "remotion", "render", "src/index.ts", "AsScreen", str(ui_path), f"--props={OUT / f'{clip}.props.json'}",
         "--crf=16", "--log=error"], cwd=ROOT)

    uw, uh = SIZE[clip]
    src = np.float32([[0, 0], [uw, 0], [uw, uh], [0, uh]])
    ui = frames(ui_path, uw, uh)
    cur, cur_i = next(ui), 0
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", f"{fps:.5f}", "-i", "-",
                            "-an", "-c:v", "libx264", "-crf", "19", "-preset", "medium", "-pix_fmt", "yuv420p", "-g", "15",
                            "-movflags", "+faststart", str(CLIPS / f"{clip}.mp4")], stdin=subprocess.PIPE)
    reach = SPILL.get(clip, 25)
    for i, f in enumerate(frames(plain)):
        want = min(round(i / fps * 30), round(seconds * 30) - 1)
        while cur_i < want:
            nxt = next(ui, None)
            if nxt is None:
                break
            cur, cur_i = nxt, cur_i + 1
        q = quads[i]
        warped = cv2.warpPerspective(cur, cv2.getPerspectiveTransform(src, q), (W, H), flags=cv2.INTER_LINEAR,
                                     borderMode=cv2.BORDER_CONSTANT, borderValue=tuple(int(v) for v in SCREEN))
        warped = cv2.GaussianBlur(warped, (3, 3), 0).astype(np.float32)
        g = f.astype(np.float32)
        if clip == "G2":
            a = np.zeros((H, W), np.float32)
            cv2.fillConvexPoly(a, q.astype(np.int32), 1.0)
            a = cv2.GaussianBlur(a, (5, 5), 0)
        else:
            a = mask_of(clip, f)
            gg = g[..., 1]
            if reach:
                band = cv2.dilate((a > 0.02).astype(np.uint8), np.ones((reach, reach), np.uint8)).astype(bool)
                gg[band] = np.minimum(gg[band], np.maximum(g[..., 0], g[..., 2])[band] + 8)
            else:
                greenish = (gg > g[..., 2]) & (gg > g[..., 0])
                gg[greenish] = np.minimum(gg[greenish], np.maximum(g[..., 0], 0.9 * g[..., 2])[greenish] + 2)
        out = g * (1 - a[..., None]) + warped * a[..., None]
        out = np.clip(out, 0, 255).astype(np.uint8)
        enc.stdin.write(out.tobytes())
        if i == len(quads) * 2 // 3:
            look = out.copy()
            cv2.polylines(look, [q.astype(np.int32)], True, (0, 200, 255), 2)
            cv2.circle(look, tuple(int(v) for v in q[0]), 8, (0, 0, 255), -1)  # top-left
            cv2.imwrite(str(OUT / f"{clip}-check.jpg"), cv2.resize(look, (960, 540)))
    enc.stdin.close()
    enc.wait()
    print(f"{clip}: {len(quads)} frames at {fps:.2f} fps, screen {SIZE[clip]}", flush=True)


if __name__ == "__main__":
    tl = json.loads((ROOT / "public/ai-sycophancy/timeline.json").read_text())
    edit = json.loads((ROOT / "scripts/ai-sycophancy/edit.json").read_text())
    shots = {s["clip"]: s for s in tl["shots"] if s.get("green")}
    for c in sys.argv[1:] or ["G1", "G2", "G3", "G4", "G5"]:
        composite(c, shots[c], edit)
