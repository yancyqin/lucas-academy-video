"""画面检查: jumps, start wobble, shake, back-and-forth drift, frozen footage, black frames and flashes in the
rendered film — the problems Yancy has caught by eye (README "Automatic checks").

Two different defects hide under "画面抖动":
- a jump or wobble is fast: the frame-to-frame shift spikes (a Muse clip's first ~8 frames — leaf-truck,
  「muse 这些视频接入前半秒晃一下」; a single wrong frame);
- a drift is slow: a MiniMax background swaying ±4–5 px behind a fixed easel (faune, 「画板一直晃」) barely changes
  one frame from the next, so it only shows in the trajectory over seconds.
So the film is decoded once at 960 px wide (4 px at 1920 is still 2 px here), and per frame we keep its luma, its
block difference from the last few frames, and its global shift against the previous frame by phase correlation
(sub-pixel). Everything after that works on those numbers.

Shots, dissolves and planned black come from the spec (spec.py). Without shots the checks still run, split at the
cuts they find; freeze is only judged inside shots the spec calls "footage" (paintings are meant to be still).
Pixel figures in findings are at 1920 wide. Thresholds in T are starting values; tests/test_picture.py holds the
synthetic defects each one must catch.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import numpy as np

from common import FAIL, UNSURE, ffprobe, item, short_hash

LONG = 960  # analysis size of the long side
T = {
    "conf_min": 0.12,          # phase-correlation peak (0–1) below which a frame's shift is not trusted
    "cut_mad": 12.0,           # block-mean difference (0–255) of a hard cut
    "glitch_mad": 5.0,         # a frame this different from both neighbours …
    "glitch_back": 0.35,       # … while the neighbours match each other (ratio) …
    "glitch_conf": 0.3,        # … and it is not the same picture shifted (that is a jump or a wobble)
    "jump_px": 3.0,            # frame-to-frame shift spike, px @960, above the local baseline …
    "jump_k": 6.0,             # … and this many robust sigmas
    "wobble_frames": 18,       # a shot's first 0.6 s
    "wobble_px": 1.2,          # RMS of the shift spikes in those frames, px @960 …
    "wobble_ratio": 3.0,       # … and this many times the next two seconds
    "shake_unsure": 0.8,       # RMS of the trajectory around its 0.5-s average, any 1-s window, px @960
    "shake_fail": 2.0,
    "drift_px": 1.5,           # a swing of the smoothed trajectory, px @960 (3 px @1920) …
    "drift_reversals": 2,      # … turning back at least this many times
    "static_px": 0.5,          # a shot marked static may not move more than this, px @960 (1 px @1920)
    "freeze_fine": 0.06,       # mean pixel change (0–255, at 960 px): repeated frames decode to ≤ 0.03, a quiet
                               # night scene still moves at 0.1–0.4 …
    "freeze_s": 0.5,           # … for this long, inside footage
    "black_luma": 24.0,        # mean luma (video range: black is 16) …
    "black_std": 4.0,          # … and flat
    "black_frames": 2,         # ≥ 0.07 s at 30 fps
    "flash_luma": 12.0,        # a frame's luma off the median of its ±4 neighbours
    "edge_start": 0.5, "edge_end": 1.0,   # black at the very start/end of the film is a fade
}
KMAX = 4  # block differences kept against the last KMAX frames


# --------------------------------------------------------------------------------------------- measuring


class Correlator:
    """Phase correlation with a Gaussian-weighted spectrum (a smooth peak → accurate sub-pixel fit)."""

    def __init__(self, h: int, w: int):
        self.shape = (h, w)
        self.window = np.outer(np.hanning(h), np.hanning(w)).astype(np.float32)
        fy = np.fft.fftfreq(h)[:, None]
        fx = np.fft.rfftfreq(w)[None, :]
        self.weight = np.exp(-(fx ** 2 + fy ** 2) / (2 * 0.12 ** 2)).astype(np.float32)
        self.ref = float(np.fft.irfft2(self.weight.astype(np.complex64), s=self.shape)[0, 0])

    def spectrum(self, img: np.ndarray) -> np.ndarray:
        a = img.astype(np.float32)
        return np.fft.rfft2((a - a.mean()) * self.window)

    def shift(self, cur: np.ndarray, prev: np.ndarray) -> tuple[float, float, float]:
        """How far the content moved from prev to cur (+x right, +y down), and the peak's strength."""
        r = cur * np.conj(prev)
        r = r / (np.abs(r) + 1e-6) * self.weight
        c = np.fft.irfft2(r, s=self.shape)
        h, w = self.shape
        k = int(np.argmax(c))
        py, px = divmod(k, w)
        peak = c[py, px]

        def sub(m, z, p):
            if m > 0 and z > 0 and p > 0:
                lm, lz, lp = np.log(m), np.log(z), np.log(p)
                d = lm - 2 * lz + lp
                return 0.0 if d >= 0 else 0.5 * (lm - lp) / d
            d = m - 2 * z + p
            return 0.0 if d >= 0 else 0.5 * (m - p) / d

        y = py + sub(c[(py - 1) % h, px], peak, c[(py + 1) % h, px])
        x = px + sub(c[py, (px - 1) % w], peak, c[py, (px + 1) % w])
        if y > h / 2:
            y -= h
        if x > w / 2:
            x -= w
        return float(x), float(y), float(peak / self.ref)


def _regions(spec: dict, fps: float, scale: float, size: tuple[int, int]) -> list[dict]:
    """Shots the spec marks static: the whole frame (static: true) or [[x, y, w, h]] boxes in the film's pixels."""
    out = []
    H, W = size
    for s in spec.get("shots") or []:
        st = s.get("static")
        if not st:
            continue
        boxes = [[0, 0, W / scale, H / scale]] if st is True else st
        for b in boxes:
            x, y, w, h = (int(round(v * scale)) for v in b)
            x, y = max(0, x), max(0, y)
            w, h = min(W - x, w), min(H - y, h)
            if w >= 32 and h >= 32:
                out.append({"shot": s.get("id"), "a": int(round(s["start"] * fps)), "b": int(round(s["end"] * fps)),
                            "box": [x, y, w, h], "box1920": b})
    return out


def measure(video: Path, spec: dict, out: Path | None = None) -> dict:
    p = ffprobe(video)
    v = next(s for s in p["streams"] if s["codec_type"] == "video")
    num, den = (int(x) for x in v["r_frame_rate"].split("/"))
    fps = num / den
    W0, H0 = int(v["width"]), int(v["height"])
    scale = LONG / max(W0, H0)
    W, H = int(round(W0 * scale / 10)) * 10, int(round(H0 * scale / 10)) * 10
    regions = _regions(spec, fps, W / W0, (H, W))          # static boxes are in the film's own pixels
    in_trans = set()
    for a, b in spec.get("transitions") or []:
        in_trans.update(range(int(np.floor(a * fps)) - 2, int(np.ceil(b * fps)) + 3))
    st = video.stat()
    key = hashlib.sha1(json.dumps([str(video), st.st_size, st.st_mtime, W, H, [r["box"] + [r["a"], r["b"]] for r in regions],
                                   sorted(in_trans) if regions else [], 3]).encode()).hexdigest()[:16]
    cache = out / "picture-stats.npz" if out else None
    if cache and cache.exists():
        z = np.load(cache, allow_pickle=True)
        if str(z["key"]) == key:
            return json.loads(str(z["meta"])) | {k: z[k] for k in z.files if k not in ("key", "meta")}
    corr = Correlator(H, W)
    rcorr = {i: Correlator(r["box"][3], r["box"][2]) for i, r in enumerate(regions)}
    rref, rpos = {}, {i: [] for i in range(len(regions))}
    proc = subprocess.Popen(["ffmpeg", "-v", "error", "-i", str(video), "-map", "0:v:0",
                             "-vf", f"scale={W}:{H}:flags=area,format=gray", "-f", "rawvideo", "-pix_fmt", "gray", "-"],
                            stdout=subprocess.PIPE)
    size = W * H
    luma, lstd, mads, shifts, conf, fine = [], [], [], [], [], []
    prevf = None
    blocks: list[np.ndarray] = []
    prev_spec = None
    i = 0
    while True:
        buf = proc.stdout.read(size)
        if len(buf) < size:
            break
        f = np.frombuffer(buf, np.uint8).reshape(H, W)
        ff = f.astype(np.float32)
        luma.append(float(ff.mean()))
        lstd.append(float(ff.std()))
        fine.append(float(np.abs(ff - prevf).mean()) if prevf is not None else 0.0)
        prevf = ff
        b = ff.reshape(H // 10, 10, W // 10, 10).mean(axis=(1, 3))
        mads.append([float(np.abs(b - blocks[-k]).mean()) if len(blocks) >= k else 0.0 for k in range(1, KMAX + 1)])
        blocks.append(b)
        if len(blocks) > KMAX:
            blocks.pop(0)
        spec_f = corr.spectrum(ff)
        if prev_spec is None:
            shifts.append((0.0, 0.0))
            conf.append(1.0)
        else:
            x, y, c = corr.shift(spec_f, prev_spec)
            shifts.append((x, y))
            conf.append(c)
        prev_spec = spec_f
        for k, r in enumerate(regions):
            if r["a"] <= i < r["b"] and i not in in_trans:   # a dissolve is not the shot moving
                x0, y0, w, h = r["box"]
                s = rcorr[k].spectrum(ff[y0:y0 + h, x0:x0 + w])
                if k not in rref:
                    rref[k] = s
                    rpos[k].append((i, 0.0, 0.0))
                else:
                    x, y, _ = rcorr[k].shift(s, rref[k])
                    rpos[k].append((i, x, y))
        i += 1
    proc.wait()
    stats = {"fps": fps, "size": [W, H], "src": [W0, H0], "px1920": 1920 / LONG,
             "regions": [{**{k: r[k] for k in ("shot", "box1920")}, "pos": rpos[k]} for k, r in enumerate(regions)],
             "luma": np.array(luma), "lstd": np.array(lstd), "mad": np.array(mads).reshape(-1, KMAX),
             "shift": np.array(shifts).reshape(-1, 2), "conf": np.array(conf), "fine": np.array(fine)}
    if cache:
        meta = {k: stats[k] for k in ("fps", "size", "src", "px1920", "regions")}
        np.savez_compressed(cache, key=key, meta=json.dumps(meta), **{k: stats[k] for k in ("luma", "lstd", "mad", "shift", "conf", "fine")})
    return stats


# --------------------------------------------------------------------------------------------- judging


def _movavg(x: np.ndarray, n: int) -> np.ndarray:
    """Centred moving average that shrinks its window at the ends (no zero padding)."""
    if len(x) == 0:
        return x
    c = np.concatenate([[0.0], np.cumsum(x)])
    i = np.arange(len(x))
    lo = np.maximum(0, i - n // 2)
    hi = np.minimum(len(x), i + n // 2 + 1)
    return (c[hi] - c[lo]) / (hi - lo)


def _zigzag(x: np.ndarray, p: float) -> list[int]:
    """Turning points of x, keeping only swings of at least p: [first extreme, …, last extreme] (indices)."""
    piv: list[int] = []
    if len(x) < 3:
        return piv
    hi = lo = 0
    direction = 0
    for i in range(1, len(x)):
        if direction >= 0 and x[i] > x[hi]:
            hi = i
        if direction <= 0 and x[i] < x[lo]:
            lo = i
        if direction == 0:
            if x[hi] - x[lo] >= p:
                piv.append(min(hi, lo))
                direction = 1 if hi > lo else -1
        elif direction == 1 and x[hi] - x[i] >= p:
            piv.append(hi)
            direction, lo = -1, i
        elif direction == -1 and x[i] - x[lo] >= p:
            piv.append(lo)
            direction, hi = 1, i
    if direction:
        piv.append(hi if direction == 1 else lo)
    return piv


def _spans_to_mask(spans, n: int, fps: float, pad: int = 0) -> np.ndarray:
    m = np.zeros(n, bool)
    for a, b in spans or []:
        m[max(0, int(np.floor(a * fps)) - pad): min(n, int(np.ceil(b * fps)) + pad + 1)] = True
    return m


def check(video: Path, spec: dict, out: Path | None = None) -> tuple[dict, list]:
    video = Path(video)
    s = measure(video, spec, out)
    fps, px = s["fps"], s["px1920"]
    n = len(s["luma"])
    mad, sh, conf, luma, lstd = s["mad"], s["shift"], s["conf"], s["luma"], s["lstd"]
    m1 = mad[:, 0]
    findings, info = [], {"frames": n, "fps": fps, "analysed_at": s["size"], "skipped": []}
    t = lambda i: i / fps  # noqa: E731

    def add(verdict, code, title, detail, i0, i1, extra_key=""):
        findings.append(item("picture", verdict, code, title, detail, t0=t(i0), t1=t(i1),
                             key=short_hash("picture", code, round(t(i0), 1), extra_key)))

    trans = _spans_to_mask(spec.get("transitions"), n, fps, pad=2)
    planned = _spans_to_mask(spec.get("planned_black"), n, fps, pad=1) | trans
    edge = np.zeros(n, bool)   # a fade at the very start/end — never more than a slice of a short film
    edge[: min(int(T["edge_start"] * fps), n // 10)] = True
    edge[n - min(int(T["edge_end"] * fps), n // 7):] = True

    # Black frames. Only the frames inside a planned black, a transition or the film's edges are excused: a black
    # run that reaches past them is judged on the part that sticks out (a film that is black from start to finish
    # must not pass because its first frames are an "opening fade").
    black = (luma <= T["black_luma"]) & (lstd <= T["black_std"])
    unplanned = black & ~(planned | edge)
    black_runs = []
    i = 0
    while i < n:
        if unplanned[i]:
            j = i
            while j < n and unplanned[j]:
                j += 1
            if j - i >= T["black_frames"]:
                a, b = i, j   # the whole black stretch this run belongs to, for the message
                while a > 0 and black[a - 1]:
                    a -= 1
                while b < n and black[b]:
                    b += 1
                black_runs.append((i, j))
                add(FAIL, "picture.black", "黑帧", f"{j - i} 帧全黑（{(j - i) / fps:.2f} 秒）" + (
                    f"；这一段一共黑了 {(b - a) / fps:.2f} 秒，只有其中一部分是计划内的（planned_black / 转场 / 片头片尾）"
                    if (a, b) != (i, j) else ""), i, j)
            i = j
        else:
            i += 1
    in_black = np.zeros(n, bool)
    for a, b in black_runs:
        in_black[max(0, a - 1): b + 1] = True

    # Single wrong frames (1–3 frames that differ from both sides while the sides match), then hard cuts.
    bad = np.zeros(n, bool)
    cuts = []
    i = 1
    while i < n - 1:
        if m1[i] > T["glitch_mad"] and not trans[i]:
            hit = None
            for k in range(1, 4):
                j = i + k  # first frame after the suspect run
                if j >= n or k + 1 > KMAX:
                    break
                if m1[j] > T["glitch_mad"] and mad[j, k] < T["glitch_back"] * min(m1[i], m1[j]) \
                        and min(conf[i], conf[j]) < T["glitch_conf"]:
                    hit = k
                    break
            if hit:
                bad[i:i + hit] = True
                if not in_black[i]:
                    add(FAIL, "picture.glitch", "画面跳了一下",
                        f"{hit} 帧和前后都不一样（前后两帧却一样），像是插进了一张错的画面", i, i + hit)
                i += hit
                continue
            if m1[i] > T["cut_mad"] and m1[i] > 3 * max(np.median(m1[max(1, i - 6):i]) if i > 1 else 0, 0.5) \
                    and m1[i + 1] < 0.5 * m1[i]:
                cuts.append(i)
        i += 1
    info["cuts_found"] = [round(t(c), 2) for c in cuts]

    # Segments: between shot edges, found cuts and dissolves, without the bad frames.
    edges = set(cuts)
    for shot in spec.get("shots") or []:
        edges.add(int(round(shot["start"] * fps)))
        edges.add(int(round(shot["end"] * fps)))
    skip = trans | bad | in_black
    segs, a = [], None
    for i in range(n + 1):
        if i == n or skip[i] or i in edges:
            if a is not None and i - a >= 6:
                segs.append((a, i))
            a = None if (i == n or skip[i]) else i
        elif a is None:
            a = i

    trusted = conf >= T["conf_min"]
    d = np.where(trusted[:, None], sh, 0.0)
    seg_info = []
    for a, b in segs:
        dd = d[a + 1:b].copy()            # shifts inside the segment (the first one crosses its edge)
        row = {"t": [round(t(a), 2), round(t(b), 2)], "frames": b - a}
        if len(dd) < 4:
            seg_info.append(row)
            continue
        traj = np.vstack([[0, 0], np.cumsum(dd, axis=0)])
        # Jumps: a frame-to-frame shift far off its neighbourhood.
        base = np.vstack([_movavg(dd[:, 0], 31), _movavg(dd[:, 1], 31)]).T
        dev = np.linalg.norm(dd - np.median(dd, axis=0) if len(dd) < 31 else dd - base, axis=1)
        sigma = 1.4826 * np.median(np.abs(dev - np.median(dev))) + 0.05
        wob_n = min(T["wobble_frames"], len(dd) // 3)
        spikes = np.where((dev > T["jump_px"]) & (dev > T["jump_k"] * sigma))[0]
        # The first 0.6 s on its own: a Muse/MiniMax clip that wobbles before it settles.
        if b - a >= 2 * fps and wob_n >= 6:
            head = dev[:wob_n]
            rest = dev[wob_n: wob_n + int(2 * fps)]
            h_rms = float(np.sqrt(np.mean(head ** 2)))
            r_rms = float(np.sqrt(np.mean(rest ** 2))) if len(rest) else 0.0
            row["head_rms"] = round(h_rms * px, 2)
            if h_rms > T["wobble_px"] and h_rms > T["wobble_ratio"] * max(r_rms, 0.1):
                add(FAIL, "picture.start_wobble", "开头晃",
                    f"镜头开始的 {wob_n / fps:.1f} 秒里画面在晃（平均 {h_rms * px:.1f} 像素/帧），之后才稳住；"
                    "Muse/MiniMax 片段从 0.5 秒以后开始用", a, a + wob_n + 1)
                spikes = spikes[spikes >= wob_n]
        if len(spikes):
            groups = []
            for k in spikes:
                if groups and k - groups[-1][-1] <= 3:
                    groups[-1].append(k)
                else:
                    groups.append([k])
            for g in groups[:5]:
                k = g[0]
                mag = float(max(dev[g]))
                add(FAIL, "picture.jump", "画面跳了一下", f"整幅画面突然移动了 {mag * px:.0f} 像素", a + 1 + k, a + 2 + g[-1])
        # Shake: the trajectory around its own 0.5-s average.
        res = traj - np.vstack([_movavg(traj[:, 0], int(fps / 2) | 1), _movavg(traj[:, 1], int(fps / 2) | 1)]).T
        r = np.linalg.norm(res, axis=1)
        if wob_n and b - a >= 2 * fps:
            r = r[wob_n:]
        win = int(fps)
        if len(r) >= win:
            c = np.concatenate([[0.0], np.cumsum(r ** 2)])
            rms = np.sqrt((c[win:] - c[:-win]) / win)
            k = int(np.argmax(rms))
            worst = float(rms[k])
            row["shake"] = round(worst * px, 2)
            if worst > T["shake_unsure"]:
                off = a + (wob_n if b - a >= 2 * fps else 0)
                add(FAIL if worst > T["shake_fail"] else UNSURE, "picture.shake", "画面在抖",
                    f"1 秒内画面位置来回抖动约 {worst * px:.1f} 像素", off + k, off + k + win)
        # Drift: the smoothed trajectory swinging back and forth.
        smooth = np.vstack([_movavg(traj[:, 0], int(fps / 2) | 1), _movavg(traj[:, 1], int(fps / 2) | 1)]).T
        for axis, name in ((0, "左右"), (1, "上下")):
            piv = _zigzag(smooth[:, axis], T["drift_px"])
            if len(piv) - 2 >= T["drift_reversals"]:
                amp = float(np.max(np.abs(np.diff(smooth[piv, axis]))))
                row[f"drift_{'xy'[axis]}"] = {"turns": len(piv) - 1, "swing": round(amp * px, 1)}
                add(UNSURE, "picture.drift", "画面来回漂移",
                    f"画面{name}来回移动了 {len(piv) - 1} 次，每次约 {amp * px:.0f} 像素（1920 宽）；"
                    "固定的东西（画架、画框、字）背后背景在晃会很明显", a + piv[0], a + piv[-1], name)
                break
        seg_info.append(row)
    info["segments"] = seg_info

    # Static shots and regions: measured against the shot's first frame.
    for r in s["regions"]:
        pos = np.array(r["pos"]).reshape(-1, 3)
        if len(pos) < 3:
            continue
        rng = float(max(np.ptp(pos[:, 1]), np.ptp(pos[:, 2])))
        if rng > T["static_px"]:
            k = int(np.argmax(np.abs(pos[:, 1:]).max(axis=1)))
            add(FAIL, "picture.static_moved", "应该不动的画面在动",
                f"镜头 {r['shot']} 标成静止的区域 {r['box1920']} 移动了 {rng * px:.1f} 像素（1920 宽）",
                int(pos[0, 0]), int(pos[-1, 0]), str(r["box1920"]))

    # Frozen footage.
    footage = [sh_ for sh_ in spec.get("shots") or [] if sh_.get("kind") == "footage"]
    if not footage:
        info["skipped"].append("实拍停住（spec 里没有 kind=footage 的镜头）")
    still = s["fine"] < T["freeze_fine"]
    need = int(round(T["freeze_s"] * fps))
    for shot in footage:
        a, b = int(round(shot["start"] * fps)), min(n, int(round(shot["end"] * fps)))
        i = a + 1
        while i < b:
            if still[i] and not trans[i]:
                j = i
                while j < b and still[j]:
                    j += 1
                if j - i + 1 >= need:
                    add(FAIL, "picture.freeze", "实拍画面停住了",
                        f"镜头 {shot.get('id', '')} 有 {(j - i + 1) / fps:.1f} 秒完全没有变化（实拍画面不能停）", i - 1, j)
                i = j
            i += 1

    # Flashes: a frame much brighter or darker than its neighbours (not a cut, not a dissolve).
    med = np.array([np.median(luma[max(0, i - 4): i + 5]) for i in range(n)])
    flash = np.where((np.abs(luma - med) > T["flash_luma"]) & ~trans & ~bad & ~in_black)[0]
    last = -10
    for i in flash:
        if i - last > 3:
            add(UNSURE, "picture.flash", "闪了一下", f"这一帧比前后亮度差了 {abs(luma[i] - med[i]):.0f}（0–255）", i, i + 1)
        last = i
    info["thresholds"] = T
    return info, findings
