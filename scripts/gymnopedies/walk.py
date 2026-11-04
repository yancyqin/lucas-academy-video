#!/usr/bin/env python3
"""听得见的舞 test cuts: footage that walks with the music, Degas pictures that breathe with it.

Owner 2026-11-02: 「节奏曲线拉到听听走走」 — the footage moves on the music's notes and nearly stops between them.
Every onset in the recording (music/analysis/<piece>.accents.json) adds a pulse to the shot's speed: it rises over
ATT s and decays over DEC s, weighted by the onset's accent score, on top of a small FLOOR. The pulse train is scaled so
the shot's mean speed is `mean` (fraction of real time) and capped at SMAX, so the dancers step on each note, rest in
the gaps, and never run faster than they really moved.

Footage is cropped to 16:9, scaled to 1920x1080 and motion-interpolated to 100 fps once (footage/cache, regenerable);
output frames blend the two nearest interpolated frames at the curve's source time. Pictures (art/<id>.jpg, or a
MiniMax clip) get a slow eased push-in and a gentle brightness breath from music/analysis/<piece>.breath.json.
Shots overlap by `xfade` seconds, centred on the shot's `at` time (put `at` on an accent).

spec (JSON): {"name", "piece", "start", "end", "fade_in", "fade_out", "afade_in", "afade_out" (audio; default = the video
              fades), "afade_curve" (ffmpeg afade curve, e.g. "qua" so a loop's tail dies away), "out_dir" (default tests/),
              "size": [w, h] (default 1920x1080; crops take this aspect — the vertical shorts' picture), "breath": false
              (pictures keep a constant brightness, so a loop's last frame equals its first),
              "shots": [{"at", "src": "pexels:<id>" | "art:<id>" | "img:<path>" | "video:<path>" | "muse:<segment>" (an aligned Muse
                         segment, footage/muse/aligned-<--muse>/) | "gen:<name>" (footage/impressionism-secret/), "in", "mean", "crop": [x0, y0, w]
                         (fractions of the source; w = 16:9 window width), "zoom": [z0, z1], "xfade", "hold" (s of standstill
                         easing into motion — set it to the xfade when a clip dissolves in from its painting),
                         "fit": true (footage: mean = whatever plays the source from `in` to its last frame — owner 11-03, use
                         the whole Muse clip), "crop_to": [x0, y0, w] (the window eases from crop to crop_to — a slow tilt/pan;
                         footage keeps w; a picture may also change w — e.g. a tilt that shows each hand whole in turn when
                         no 16:9 window holds them all), "out" (footage: play exactly in..out over the shot — one stretch of a
                         clip), "floor" (footage: the speed curve's floor; raise it and the clip never nearly stops — owner
                         11-03 on the shorts: 「实景的不要有静态」)}]}
usage: .venv-reframe/bin/python scripts/gymnopedies/walk.py SPEC.json [--draft] [--muse sharp|soft]
"""
import argparse, glob, hashlib, json, os, subprocess, sys
import cv2
import numpy as np

DATA = "/Users/yqin/repo/playground/lucas-academy-video-data/satie-gymnopedies"
MUSE = "sharp"                     # which aligned Muse set `muse:` sources read (--muse)
W, H, FPS, IFPS = 1920, 1080, 30, 100
ATT, DEC, FLOOR, SMAX = 0.10, 0.55, 0.12, 1.0

def onsets(piece):
    return [(o["t"], o["score"]) for o in json.load(open(f"{DATA}/music/analysis/{piece}.accents.json"))["onsets"]]

def speed_curve(ons, t0, t1, mean, hold=0.0, floor=FLOOR):
    """Speed (fraction of real time) at each output frame of [t0, t1). `hold` s at the start ease up from standstill, so
    a clip that dissolves in from its painting stays on its first (aligned) frame while the dissolve runs."""
    t = t0 + np.arange(int(round((t1 - t0) * FPS))) / FPS
    p = np.full_like(t, floor)
    for ot, sc in ons:
        x = t - ot
        p += sc * np.where(x < 0, 0, np.where(x < ATT, x / ATT, np.exp(-(x - ATT) / DEC)))
    k = np.exp(-0.5 * (np.arange(-4, 5) / 2.0) ** 2); p = np.convolve(p, k / k.sum(), mode="same")
    if hold > 0: p = p * ease(np.clip((t - t0) / hold, 0, 1)) ** 2
    s = p * mean / p.mean()
    for _ in range(20):                                   # cap at SMAX, give the excess back to the slow parts
        s = np.minimum(s, SMAX); s *= mean / s.mean()
    return np.minimum(s, SMAX)

def src_path(src):
    kind, ref = src.split(":", 1)
    if kind == "pexels": return glob.glob(f"{DATA}/footage/pexels/{ref}-*.mp4")[0]
    if kind == "art": return f"{DATA}/art/{ref}.jpg"
    if kind == "muse": return f"{DATA}/footage/muse/aligned-{MUSE}/{ref}.mp4"
    if kind == "gen":                  # the 印象派的秘密 clips, sharpened with the Muse ones when the film reads the sharp set
        sharp = f"{DATA}/footage/muse/sharp/{ref}.mp4"
        return sharp if MUSE == "sharp" and os.path.exists(sharp) else f"{DATA}/footage/impressionism-secret/{ref}.mp4"
    return ref

def probe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height:format=duration",
                          "-of", "json", path], capture_output=True, text=True, check=True).stdout
    j = json.loads(out); return j["streams"][0]["width"], j["streams"][0]["height"], float(j["format"]["duration"])

def crop_box(sw, sh, crop):
    """crop = [x0, y0, w] as fractions; the window is 16:9 in source pixels."""
    x0, y0, cw = crop if crop else (None, None, None)
    if cw is None:
        cw_px = min(sw, sh * W / H)
    else:
        cw_px = cw * sw
    ch_px = cw_px * H / W                           # the output's aspect (16:9 unless the spec sets "size")
    x = (sw - cw_px) / 2 if x0 is None else x0 * sw
    y = (sh - ch_px) / 2 if y0 is None else y0 * sh
    x = max(0, min(sw - cw_px, x)); y = max(0, min(sh - ch_px, y))
    return int(round(x)) & ~1, int(round(y)) & ~1, int(round(cw_px)) & ~1, int(round(ch_px)) & ~1

def interpolated(path, a, length, crop, draft, crop_to=None):
    """Source window [a, a + length] cropped, scaled and interpolated to IFPS; cached by its parameters. With crop_to the
    cache holds the union of both windows at the output scale, and the shot moves its window across it."""
    sw, sh, dur = probe(path)
    a = max(0.0, a); length = min(length, dur - a)
    x, y, cw, ch = crop_box(sw, sh, crop)
    w, h = (W // 2, H // 2) if draft else (W, H)
    if crop_to:
        x2, y2, cw2, _ = crop_box(sw, sh, crop_to); assert abs(cw2 - cw) <= 2, "crop_to must keep the window width"
        k = w / cw                                  # output px per source px, the same scale the shot pans with
        ux, uy = min(x, x2), min(y, y2); cw, ch = max(x, x2) + cw - ux, max(y, y2) + ch - uy; x, y = ux, uy
        w, h = int(round(cw * k)) & ~1, int(round(ch * k)) & ~1
    # mtime in the key: a re-aligned clip written to the same path must not reuse the old clip's interpolation
    key = hashlib.sha1(json.dumps([path, os.path.getmtime(path), round(a, 3), round(length, 3), [x, y, cw, ch], w, h]).encode()).hexdigest()[:12]
    os.makedirs(f"{DATA}/footage/cache", exist_ok=True)
    out = f"{DATA}/footage/cache/{os.path.basename(path)[:-4]}-{key}.mp4"
    if not os.path.exists(out):
        vf = f"crop={cw}:{ch}:{x}:{y},scale={w}:{h}:flags=lanczos,minterpolate=fps={IFPS}:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{a:.3f}", "-t", f"{length:.3f}", "-i", path, "-vf", vf, "-an",
                        "-c:v", "libx264", "-crf", "12", "-preset", "fast", "-pix_fmt", "yuv420p", out + ".part.mp4"], check=True)
        os.rename(out + ".part.mp4", out)
    return out, length, (w, h)

class Reader:
    """Sequential frame reader with random-ish forward access (frames are only ever requested in order)."""
    def __init__(self, path, w, h):
        self.p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", path, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE,
                                  stderr=subprocess.DEVNULL)        # closed early once the shot is over: no broken-pipe noise
        self.w, self.h, self.i, self.cur, self.nxt = w, h, -1, None, None
        self._advance(); self._advance()
    def _read(self):
        b = self.p.stdout.read(self.w * self.h * 3)
        return None if len(b) < self.w * self.h * 3 else np.frombuffer(b, np.uint8).reshape(self.h, self.w, 3)
    def _advance(self):
        f = self._read()
        if f is not None or self.nxt is not None:
            self.cur, self.nxt = self.nxt, f if f is not None else self.nxt
            self.i += 1
    def frame(self, pos):
        """Blend of frames floor(pos) and floor(pos)+1."""
        k = int(pos)
        while self.i < k and self.nxt is not None: self._advance()
        a = pos - k
        if self.cur is None: return self.nxt
        if a < 1e-3: return self.cur
        return cv2.addWeighted(self.cur, 1 - a, self.nxt, a, 0)
    def close(self):
        self.p.stdout.close(); self.p.terminate(); self.p.wait()

def ease(u): return u * u * (3 - 2 * u)

class Shot:
    def __init__(self, spec, piece_ons, breath, t0, t1, draft):
        self.spec, self.t0, self.t1 = spec, t0, t1
        self.w, self.h = (W // 2, H // 2) if draft else (W, H)
        kind = spec["src"].split(":", 1)[0]
        path = src_path(spec["src"])
        n = int(round((t1 - t0) * FPS))
        if kind in ("art", "img"):           # img:<path> = any still, e.g. a reconstruction aligned to its painting
            img = cv2.cvtColor(cv2.imread(path), cv2.COLOR_BGR2RGB)
            x, y, cw, ch = crop_box(img.shape[1], img.shape[0], spec.get("crop"))
            self.img, self.box = img, (x, y, cw, ch)
            self.box_to = crop_box(img.shape[1], img.shape[0], spec["crop_to"]) if spec.get("crop_to") else self.box
            self.zoom = spec.get("zoom", [1.0, 1.06])
            fps_b = breath["fps"]; tt = t0 + np.arange(n) / FPS
            b = np.interp(tt * fps_b, np.arange(len(breath["b"])), breath["b"])
            self.light = 0.97 + 0.06 * b if spec.get("breath", True) else np.ones_like(b)   # gentle: brightens as the melody rises
            self.kind = "art"
        else:
            mean = spec.get("mean", 0.4)
            if spec.get("fit"): mean = (probe(path)[2] - spec.get("in", 0.0) - 0.08) / (t1 - t0)
            if "out" in spec: mean = (spec["out"] - spec.get("in", 0.0)) / (t1 - t0)
            s = speed_curve(piece_ons, t0, t1, mean, spec.get("hold", 0.0), spec.get("floor", FLOOR))
            tau = np.concatenate([[0], np.cumsum(s[:-1])]) / FPS     # source seconds from `in`
            need = tau[-1] + 0.2
            self.path, length, cache_wh = interpolated(path, spec.get("in", 0.0), need, spec.get("crop"), draft, spec.get("crop_to"))
            if length < need - 0.05 and not spec.get("fit"): print(f"  ! {spec['src']} has only {length:.1f}s from {spec.get('in', 0)}, needs {need:.1f}s")
            self.pos = np.minimum(tau * IFPS, length * IFPS - 2)
            self.pan = None
            if spec.get("crop_to"):                # window offsets inside the cached union, eased over the shot
                sw, sh, _ = probe(path); k = self.w / crop_box(sw, sh, spec["crop"])[2]
                (x1, y1, _, _), (x2, y2, _, _) = crop_box(sw, sh, spec["crop"]), crop_box(sw, sh, spec["crop_to"])
                ux, uy = min(x1, x2), min(y1, y2); u = ease(np.linspace(0, 1, n))
                self.pan = np.stack([(x1 - ux) * k + (x2 - x1) * k * u, (y1 - uy) * k + (y2 - y1) * k * u], 1)
            self.reader = Reader(self.path, *cache_wh)
            self.kind = "footage"
            print(f"  {spec['src']}: {t1 - t0:.1f}s on screen, {tau[-1]:.1f}s of footage from {spec.get('in', 0)}s, speed {s.min():.2f}-{s.max():.2f}")
    def frame(self, k):
        if self.kind == "footage":
            f = self.reader.frame(self.pos[min(k, len(self.pos) - 1)])
            if self.pan is None: return f
            dx, dy = self.pan[min(k, len(self.pan) - 1)]           # sub-pixel, so a slow tilt never steps
            return cv2.warpAffine(f, np.float32([[1, 0, -dx], [0, 1, -dy]]), (self.w, self.h), flags=cv2.INTER_LINEAR)
        n = int(round((self.t1 - self.t0) * FPS)); u = ease(min(1.0, k / max(n - 1, 1)))
        z = self.zoom[0] + (self.zoom[1] - self.zoom[0]) * u
        x, y, cw, ch = (a + (b - a) * u for a, b in zip(self.box, self.box_to))
        zw, zh = cw / z, ch / z
        cx, cy = x + cw / 2, y + ch / 2
        M = np.float32([[self.w / zw, 0, -(cx - zw / 2) * self.w / zw], [0, self.h / zh, -(cy - zh / 2) * self.h / zh]])
        f = cv2.warpAffine(self.img, M, (self.w, self.h), flags=cv2.INTER_AREA if z < 1.5 else cv2.INTER_LINEAR)
        return np.clip(f.astype(np.float32) * self.light[min(k, len(self.light) - 1)], 0, 255).astype(np.uint8)

def render(spec, draft):
    global W, H
    W, H = spec.get("size", [1920, 1080])
    piece, start, end = spec["piece"], spec["start"], spec["end"]
    ons = onsets(piece); breath = json.load(open(f"{DATA}/music/analysis/{piece}.breath.json"))
    shots = spec["shots"]
    total = end - start
    windows = []
    for i, sh in enumerate(shots):
        xin = shots[i]["xfade"] if i > 0 and "xfade" in shots[i] else 0.0
        xout = shots[i + 1].get("xfade", 0.0) if i + 1 < len(shots) else 0.0
        a = max(start, sh["at"] - xin / 2); b = min(end, shots[i + 1]["at"] + xout / 2) if i + 1 < len(shots) else end
        windows.append((a, b, xin, xout))
    out_dir = f"{DATA}/{spec.get('out_dir', 'tests')}"; os.makedirs(out_dir, exist_ok=True)
    name = spec["name"] + ("-draft" if draft else "")
    w, h = (W // 2, H // 2) if draft else (W, H)
    video = f"{out_dir}/{name}.video.mp4"
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}", "-r", str(FPS), "-i", "-",
                            "-c:v", "libx264", "-crf", "16" if not draft else "22", "-preset", "medium", "-pix_fmt", "yuv420p", video], stdin=subprocess.PIPE)
    live = {}
    n = int(round(total * FPS))
    fin, fout = spec.get("fade_in", 0.0), spec.get("fade_out", 0.0)
    for k in range(n):
        t = start + k / FPS
        frames = []
        for i, (a, b, xin, xout) in enumerate(windows):
            if a <= t < b:
                if i not in live:
                    print(f"shot {i + 1} at {a - start:.1f}s"); live[i] = Shot(shots[i], ons, breath, a, b, draft)
                f = live[i].frame(int(round((t - a) * FPS)))
                wgt = 1.0
                if xin > 0 and t < a + xin: wgt = ease((t - a) / xin)
                frames.append((f, wgt))
            elif i in live and t >= b:
                if live[i].kind == "footage": live[i].reader.close()
                del live[i]
        if len(frames) == 1: img = frames[0][0]
        else:
            (f0, _), (f1, w1) = frames[0], frames[-1]
            img = cv2.addWeighted(f0, 1 - w1, f1, w1, 0)
        g = 1.0
        if fin and t - start < fin: g = ease((t - start) / fin)
        if fout and end - t < fout: g = min(g, ease((end - t) / fout))
        if g < 1: img = (img.astype(np.float32) * g).astype(np.uint8)
        enc.stdin.write(img.tobytes())
    enc.stdin.close(); enc.wait()
    audio = f"{DATA}/music/normalized/{piece}.wav"
    final = f"{out_dir}/{name}.mp4"
    ain, aout = spec.get("afade_in", fin), spec.get("afade_out", fout)
    cv = f":curve={spec['afade_curve']}" if spec.get("afade_curve") else ""
    af = f"afade=t=in:st=0:d={max(ain, 0.01)},afade=t=out:st={total - max(aout, 0.01):.3f}:d={max(aout, 0.01)}{cv}"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", video, "-ss", f"{start:.3f}", "-t", f"{total:.3f}", "-i", audio,
                    "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-af", af, "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-ac", "2",
                    "-shortest", final], check=True)
    os.remove(video)
    print("->", final)

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("spec"); ap.add_argument("--draft", action="store_true")
    ap.add_argument("--muse", choices=["sharp", "soft"], default="sharp")
    a = ap.parse_args(); MUSE = a.muse
    render(json.load(open(a.spec)), a.draft)
