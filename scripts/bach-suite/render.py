"""Render the five-piece Bach film from edit.json onto the suite's music.

  render.py            render shots (cached), composite the picture, mux suite.wav
  render.py --force    re-render every shot
  render.py --only air one piece's picture alone (quick check), no mux

The music and where each piece sits come from assemble.py (DATA/build/suite.wav,
timings.json); every shot's `at` is relative to its piece, so re-assembling the audio
(another gap, another recording) only needs a re-render, not new numbers. Inside a piece,
neighbouring shots cross-dissolve over the piece's `dissolve` seconds (0 = hard cut);
each piece fades in from and out to black, and the gaps between pieces stay black.
Jesu is the finished film's own picture.mp4, laid in unchanged.

Outputs (DATA/build/): shots/*.mp4, picture.mp4, bach-suite.mp4
"""
import json
import pathlib
import subprocess
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "jesu"))
import shots as RS  # noqa: E402  (the Jesu film's shot renderer: trim, slow, crop, Ken Burns)

HERE = pathlib.Path(__file__).parent
EDIT = json.loads((HERE / "edit.json").read_text())
DATA = pathlib.Path(EDIT["data"])
W, H, FPS = RS.W, RS.H, RS.FPS


def smooth(u):
    u = min(max(u, 0.0), 1.0)
    return u * u * (3 - 2 * u)


class Reader:
    def __init__(self, path):
        self.p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", str(path), "-f", "rawvideo",
                                   "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
        self.last = np.zeros((H, W, 3), np.uint8)

    def next(self):
        buf = self.p.stdout.read(W * H * 3)
        if len(buf) == W * H * 3:
            self.last = np.frombuffer(buf, np.uint8).reshape(H, W, 3)
        return self.last          # past the end: hold the last frame

    def close(self):
        self.p.stdout.close()
        self.p.kill()


def spans(timings):
    """-> per piece: (timing, dissolve, [(shot, start, end, a, b)]) in film time."""
    out = {}
    for t in timings:
        p = EDIT["pieces"][t["id"]]
        # a piece may fade in/out more slowly than the film default (the Air sinks into the dark)
        t = {**t, "fade_in": p.get("fade_in", EDIT["fade_in"]), "fade_out": p.get("fade_out", EDIT["fade_out"]),
             # `black_at`: seconds from the piece's start where the fade-out reaches black (default: its end)
             "black_at": t["start"] + p["black_at"] if "black_at" in p else t["end"]}
        if "picture" in p:
            out[t["id"]] = (t, 0.0, [])
            continue
        D, shots, rows = p["dissolve"], p["shots"], []
        for i, s in enumerate(shots):
            start = t["start"] + s["at"]
            end = t["start"] + shots[i + 1]["at"] if i + 1 < len(shots) else t["end"]
            a = start - (D / 2 if i else 0)
            b = end + (D / 2 if i + 1 < len(shots) else 0)
            rows.append((s, start, end, a, b))
        out[t["id"]] = (t, D, rows)
    return out


def render_curve(rec, dur, out):
    """Video played on a speed curve: rec["speed"] = [[u, speed], ...], u in 0..1 of the shot,
    linear between points (曲线变速). Source time is the integral of the speed; output frames
    blend the two nearest source frames, so slowed time-lapses stay smooth."""
    path = rec["path"]
    fps_src = eval(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                                   "stream=r_frame_rate", "-of", "csv=p=0", path],
                                  capture_output=True, text=True).stdout.strip())
    total = RS.probe(path)[2]
    t0 = float(rec.get("best_in_s") or 0)
    pts = sorted(rec["speed"])
    n = round(dur * FPS)

    def speed(u):
        if u <= pts[0][0]:
            return pts[0][1]
        for (u0, s0), (u1, s1) in zip(pts, pts[1:]):
            if u <= u1:
                return s0 + (s1 - s0) * (u - u0) / (u1 - u0)
        return pts[-1][1]
    src = np.cumsum([0.0] + [speed((k + 0.5) / n) / FPS for k in range(n - 1)])
    if t0 + src[-1] > total - 0.1:                    # not enough clip: slow the whole curve to fit
        src *= (total - 0.1 - t0) / src[-1]
        print(f"    {pathlib.Path(path).name}: curve scaled to fit the clip", flush=True)
    grade = rec["grade"] + "," if rec.get("grade") else ""
    rd = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", f"{t0:.3f}", "-t", f"{src[-1] + 1:.3f}", "-i", path,
                           "-vf", f"scale={round(W * 1.02)}:{round(H * 1.02)}:force_original_aspect_ratio=increase"
                                  f":flags=lanczos,crop={W}:{H},{grade}format=rgb24",
                           "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    frames, have = {}, -1

    def frame(k):
        nonlocal have
        while have < k:
            buf = rd.stdout.read(W * H * 3)
            if len(buf) < W * H * 3:
                break
            have += 1
            frames[have] = np.frombuffer(buf, np.uint8).reshape(H, W, 3)
            frames.pop(have - 3, None)
        return frames.get(min(k, have))
    enc = RS._encoder(out)
    for i in range(n):
        f = src[i] * fps_src
        k = int(f)
        a, b = frame(k), frame(k + 1)
        w = f - k
        img = a if w < 0.02 or b is None else (a * (1 - w) + b * w).astype(np.uint8)
        enc.stdin.write(img.tobytes())
    enc.stdin.close()
    enc.wait()
    rd.stdout.close()
    rd.kill()


def render_popwall(rec, dur, out):
    """Paintings on black, one per accent: each fades in just before its accent and is full-screen
    on it (the hit), holds a beat, then shrinks on the music's next beat into its place on a wall.

    rec["pops"] = [{"src": "art:pop/x.jpg", "at": accent (s from shot start), "x": cx, "y": cy,
    "h": height, "rot": deg, ["hold": s, "shrink": s]}, ...] - cx, cy, h are fractions of the frame.
    rec["lead"] (default 0.3) is the fade-in before each accent; by default a picture holds half the
    gap to the next accent and shrinks over the rest of it, minus the next picture's lead. While a
    picture is full-screen the wall behind it dims."""
    from PIL import Image, ImageFilter
    Image.MAX_IMAGE_PIXELS = None
    lead = float(rec.get("lead", 0.3))
    pops = rec["pops"]
    items = []
    for k, pp in enumerate(pops):
        im = Image.open(DATA / "art" / pp["src"][4:]).convert("RGB")
        gap = (pops[k + 1]["at"] - pp["at"]) if k + 1 < len(pops) else 2.0
        hold = float(pp.get("hold", gap * 0.5))
        shrink = float(pp.get("shrink", max(gap - hold - lead - 0.05, 0.3)))
        full_h = min(H * 0.96, (W * 0.96) * im.height / im.width)          # fits the frame
        items.append({"im": im, "at": pp["at"], "hold": hold, "shrink": shrink, "full_h": full_h,
                      "slot_h": pp["h"] * H, "x": pp["x"] * W, "y": pp["y"] * H, "rot": pp.get("rot", 0)})

    def card(it, h, angle, mount):
        """The painting at height h (px), with a white mount fading in as it becomes a wall piece."""
        im = it["im"]
        hh = max(2, round(h)); ww = max(2, round(im.width * hh / im.height))
        pic = im.resize((ww, hh), Image.LANCZOS if hh > 300 else Image.BILINEAR).convert("RGBA")
        m = round(max(3, hh / 90) * mount)
        c = Image.new("RGBA", (ww + 2 * m, hh + 2 * m), (245, 242, 235, round(255 * mount)))
        c.alpha_composite(pic, (m, m))
        if mount > 0.05:
            pad = 24
            sh = Image.new("RGBA", (c.width + 2 * pad, c.height + 2 * pad), (0, 0, 0, 0))
            sh.paste(Image.new("RGBA", c.size, (0, 0, 0, round(150 * mount))), (pad, pad + 8))
            sh = sh.filter(ImageFilter.GaussianBlur(12))
            sh.alpha_composite(c, (pad, pad))
            c = sh
        if abs(angle) > 0.05:
            c = c.rotate(angle, resample=Image.BICUBIC, expand=True)
        return c

    def state(it, t):
        """-> (alpha, height, cx, cy, angle, mount, fullness) or None before it appears."""
        t0 = it["at"] - lead
        if t < t0:
            return None
        if t < it["at"]:                                       # fade in, settling from 1.05x
            u = (t - t0) / lead
            e = u * u * (3 - 2 * u)
            return e, it["full_h"] * (1.05 - 0.05 * e), W / 2, H / 2, 0.0, 0.0, e
        if t < it["at"] + it["hold"]:                          # full screen: the hit
            return 1.0, it["full_h"], W / 2, H / 2, 0.0, 0.0, 1.0
        u = min(1.0, (t - it["at"] - it["hold"]) / it["shrink"])
        e = u * u * (3 - 2 * u)                                # shrink into place on the beat
        return (1.0, it["full_h"] + (it["slot_h"] - it["full_h"]) * e, W / 2 + (it["x"] - W / 2) * e,
                H / 2 + (it["y"] - H / 2) * e, it["rot"] * e, e, 1.0 - e)

    cache = {}
    enc = RS._encoder(out)
    for i in range(round(dur * FPS)):
        t = i / FPS
        states = [(it, state(it, t)) for it in items]
        states = [(it, st) for it, st in states if st]
        settled = [(it, st) for it, st in states if st[6] == 0.0]
        moving = [(it, st) for it, st in states if st[6] > 0.0]
        wall = Image.new("RGBA", (W, H), (0, 0, 0, 255))
        for it, st in settled:
            key = id(it)
            if key not in cache:
                cache[key] = card(it, it["slot_h"], it["rot"], 1.0)
            c = cache[key]
            wall.alpha_composite(c, (round(it["x"] - c.width / 2), round(it["y"] - c.height / 2)))
        if moving:
            dim = max(st[6] for _, st in moving)               # the wall recedes behind a full painting
            wall = Image.blend(Image.new("RGBA", (W, H), (0, 0, 0, 255)), wall, 1 - 0.75 * dim)
        for it, (al, h, cx, cy, ang, mount, _) in moving:
            c = card(it, h, ang, mount)
            if al < 0.999:
                c.putalpha(c.getchannel("A").point(lambda v, a=al: round(v * a)))
            x0, y0 = round(cx - c.width / 2), round(cy - c.height / 2)
            if x0 < 0 or y0 < 0 or x0 + c.width > W or y0 + c.height > H:
                cl = c.crop((max(0, -x0), max(0, -y0), min(c.width, W - x0), min(c.height, H - y0)))
                wall.alpha_composite(cl, (max(0, x0), max(0, y0)))
            else:
                wall.alpha_composite(c, (x0, y0))
        enc.stdin.write(wall.convert("RGB").tobytes())
    enc.stdin.close()
    enc.wait()


def render_shot(piece, i, s, length, force):
    out = DATA / f"build/shots/{piece}-{i:02d}-{s['id']}.mp4"
    out.parent.mkdir(parents=True, exist_ok=True)
    key = json.dumps({**s, "len": round(length, 3)}, sort_keys=True)
    stamp = out.with_suffix(".json")
    if out.exists() and not force and stamp.exists() and stamp.read_text() == key:
        return out
    if s.get("popwall"):
        render_popwall(s, length, out)
        stamp.write_text(key)
        print(f"  shot {piece}-{i:02d} {s['id']:<18} {length:5.1f}s  (pop wall)", flush=True)
        return out
    # "art:<file>" is a still from DATA/art (paintings, moved over with kenburns); else footage
    path = DATA / "art" / s["src"][4:] if s["src"].startswith("art:") else DATA / "footage" / s["src"]
    rec = {"path": str(path), **{k: v for k, v in s.items() if k not in ("src", "id", "at", "desc")}}
    if path.suffix.lower() in RS.STILL_EXT:
        RS.render_still(rec, length, out)
    elif "speed" in s:
        render_curve(rec, length, out)
    else:
        RS.render_video(rec, length, out)
    stamp.write_text(key)
    print(f"  shot {piece}-{i:02d} {s['id']:<18} {length:5.1f}s", flush=True)
    return out


def main():
    force = "--force" in sys.argv
    only = sys.argv[sys.argv.index("--only") + 1] if "--only" in sys.argv else None
    timings = json.loads((DATA / "build/timings.json").read_text())["pieces"]
    if only:
        timings = [t for t in timings if t["id"] == only]
    plan = spans(timings)
    files = {pid: [render_shot(pid, i, s, b - a, force) for i, (s, _, _, a, b) in enumerate(rows)]
             for pid, (_, _, rows) in plan.items()}

    t_from = timings[0]["start"]
    total = timings[-1]["end"] - t_from
    name = f"picture-{only}.mp4" if only else "picture.mp4"
    enc = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                            "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264",
                            "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p",
                            "-movflags", "+faststart", str(DATA / "build" / name)], stdin=subprocess.PIPE)
    black = bytes(W * H * 3)
    readers, jesu = {}, None
    for fi in range(int(round(total * FPS))):
        t = t_from + fi / FPS
        cur = next((pid for pid, (tm, _, _) in plan.items() if tm["start"] <= t < tm["end"]), None)
        if cur is None:                                   # the silence between pieces
            enc.stdin.write(black)
            continue
        tm, D, rows = plan[cur]
        if not rows:                                      # Jesu: the finished picture
            jesu = jesu or Reader(EDIT["pieces"][cur]["picture"])
            enc.stdin.write(jesu.next().tobytes())
            continue
        g = smooth((t - tm["start"]) / tm["fade_in"]) * smooth((tm["black_at"] - t) / tm["fade_out"])
        layers = []
        for i, (s, start, end, a, b) in enumerate(rows):
            key = (cur, i)
            if not (a <= t < b):
                if key in readers and t >= b:
                    readers.pop(key).close()
                continue
            if key not in readers:
                readers[key] = Reader(files[cur][i])
            w = 1.0
            if D and i > 0:                               # fading in over the previous shot
                w *= smooth((t - (start - D / 2)) / D)
            if D and i + 1 < len(rows):                   # fading out under the next shot
                w *= 1 - smooth((t - (end - D / 2)) / D)
            layers.append((readers[key].next(), w))
        if len(layers) == 1 and layers[0][1] == 1.0 and g == 1.0:
            enc.stdin.write(layers[0][0].tobytes())       # the common case: no maths
        else:
            frame = sum(img.astype(np.float32) * w for img, w in layers) * g
            enc.stdin.write(np.clip(frame, 0, 255).astype(np.uint8).tobytes())
        if fi % (FPS * 30) == 0:
            print(f"  {t // 60:.0f}:{t % 60:04.1f}  {cur}", flush=True)
    for r in readers.values():
        r.close()
    if jesu:
        jesu.close()
    enc.stdin.close()
    enc.wait()
    if only:
        print(f"wrote {name}")
        return
    out = DATA / "build/bach-suite.mp4"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(DATA / "build/picture.mp4"),
                    "-i", str(DATA / "build/suite.wav"), "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "256k", "-shortest", "-movflags", "+faststart", str(out)],
                   check=True)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
