#!/usr/bin/env python3
"""Vertical loop shorts from 听得见的舞 (owner 11-03: 「再多做几段短视频，短一些，最好能循环」; a blurred, enlarged copy of the
video behind the picture: 「加个虚化背景试试（原视频放大虚化）」).

Second round (owner 11-03, with the Blue Dancers clip): 「做新的短视频，而且之前三个重新做。画和 muse 视频切换的频繁一些
2-3 次，实景的不要有静态，画一开始的静态帧也短一些 1 秒左右，后面的最多也就 2 秒吧」. So each short now runs
  painting (~1 s) → clip, part 1 → painting (2 s) → clip, part 2 → painting (2 s) → clip, part 3 → painting (~1 s, = frame 0)
(1 and 3 then dropped the painting before part 3 — 「第三次的切画取消，就是继续 muse 好了」 — so parts 2 and 3 are one run.)
plan() lays that out: 0.6 s dissolves, the clip's usable footage split into consecutive parts (each played once, never
repeated), screen time shared in proportion so every part moves at the same speed. "Usable" = no still frames: the
étoile clip's near-still first 1.4 s and the dance-class clip's still first 0.45 s and its morph (22–30) are left out, the
clips start moving the moment they appear (no hold on their first frame), and the 听听走走 speed curve gets a high floor
(FLOOR) so the dancers keep moving between the notes. Each short is a Gymnopédie excerpt cut just before a bar's downbeat
(all three openings have one at 21.0 s), about 21 s, so the clips play near half speed:
  s1-etoile        No. 1 0–20.85     L'Étoile, her clip after the change (frames 35–239) in 3 parts
  s2-dance-class   No. 3 0–20.85     The Dance Class: the skirt (frames 11–21), then the class (31–239) in 2 parts
  s3-rehearsal     No. 2 0–20.85     The Rehearsal on Stage, its whole clip in 3 parts
  s4-blue-dancers  No. 3 121.5–145   Blue Dancers on its vertical Codex scene (owner: 「蓝色舞者这幅画我挺喜欢的，生成一个
                                      codex 竖屏图，做一个 muse，单独出一个短视频」), the clip in 3 parts; blue_canvas() puts the
                                      painting where it sits in the clip's first frame, on a darkened blur of itself
They loop: the first and last frames are the same still (walk.py "breath": false), and the music dies away (afade qua).

usage: .venv-reframe/bin/python scripts/gymnopedies/shorts.py plan|render|vertical|check [NAME ...]
       -> shorts/NAME.json (plan), shorts/NAME.mp4 (picture), shorts/NAME-vertical.mp4 (the short, -18 LUFS)
       .venv-reframe/bin/python scripts/gymnopedies/shorts.py canvas      -> shorts/blue-dancers-canvas.png
       .venv-reframe/bin/python scripts/gymnopedies/shorts.py texts       -> package/youtube-description.shorts.txt
"""
import json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import walk
import youtube as YT
sys.path.insert(0, os.path.join(HERE, ".."))
from youtube_tags import hashtags, tags

NAMES = ["s1-etoile", "s2-dance-class", "s3-rehearsal", "s4-blue-dancers"]
VW, VH = 1080, 1920
LIFT = 0.42           # share of the spare height above the picture: a little high, clear of the Shorts captions below
XF, FIRST, GAP, LAST = 0.6, 1.2, 1.4, 0.9   # dissolve; first clip's `at`; painting `at` → next clip `at`; last painting before the end
FLOOR = 0.9           # speed-curve floor for the shorts (the film's is 0.12): the clips swell on the notes but never stall
BLUE = f"{walk.DATA}/footage/muse/sharp/blue-dancers-vertical.mp4"
PLANS = {   # picture (src, crop), output picture size, piece + excerpt, clip parts: (src, in, out, fixed window or None)
    # owner 11-03 on 1 and 3: 「第三次的切画取消，就是继续 muse 好了」 — no painting at ~14 s: the clip's last two thirds run on
    "s1-etoile": dict(pic=("art:etoile", [0.006, 0.008, 0.95]), size=[1080, 1560], piece="gymnopedie-1", start=0.0, end=20.85,
                      parts=[("muse:etoile-b", None, None, None)] * 2, weights=[1, 2]),
    "s2-dance-class": dict(pic=("art:dance-class", [0.03, 0.02, 0.86]), size=[1080, 1184], piece="gymnopedie-3", start=0.0, end=20.85,
                           parts=[("muse:dance-class-b", 0.0, None, 1.5), ("muse:dance-class-c", None, None, None),
                                  ("muse:dance-class-c", None, None, None)]),
    "s3-rehearsal": dict(pic=("art:rehearsal-stage", [0.008, 0.004, 0.985]), size=[1080, 834], piece="gymnopedie-2", start=0.0,
                         end=20.85, parts=[("muse:rehearsal-stage", None, None, None)] * 2, weights=[1, 2]),
    "s4-blue-dancers": dict(pic=(f"img:{walk.DATA}/shorts/blue-dancers-canvas.png", [0.0, 0.0, 1.0]), size=[1080, 1620],
                            piece="gymnopedie-3", start=121.5, end=145.0, afade_out=2.5, parts=[(f"video:{BLUE}", None, None, None)] * 3),
}

def plan(name):
    """The spec walk.py renders: paintings and clip parts alternating as the docstring says."""
    P = PLANS[name]; walk.MUSE = "sharp"
    n, total = len(P["parts"]), P["end"] - P["start"]
    # consecutive stretches: parts with the same src share its footage in order, split evenly
    parts, cursor, wts = [], {}, list(P.get("weights", []))
    for src, a, b, win in P["parts"]:
        dur = walk.probe(walk.src_path(src))[2] - 0.08
        same = [q for q in P["parts"] if q[0] == src and q[1] is None]
        k = cursor.get(src, 0.0 if a is None else a)
        if a is None:                                    # split evenly, or by "weights" (e.g. [1, 2]: a third, then the rest)
            share = wts.pop(0) / sum(P["weights"]) if P.get("weights") else 1 / len(same)
            a, b = k, k + dur * share; cursor[src] = b
        parts.append((src, a, b if b is not None else dur, win))
    ltot = total - FIRST - LAST - GAP * (n - 1) + 2 * XF / 2 * n            # every part's window, dissolves included
    fixed = sum(w for *_, w in parts if w); free = sum(b - a for _, a, b, w in parts if not w)
    wins = [w if w else (ltot - fixed) * (b - a) / free for _, a, b, w in parts]
    shots, t = [{"at": P["start"], "src": P["pic"][0], "crop": P["pic"][1], "zoom": [1.0, 1.0]}], P["start"] + FIRST
    for i, ((src, a, b, _), w) in enumerate(zip(parts, wins)):
        shots.append({"at": round(t, 3), "src": src, "in": round(a, 3), "out": round(b, 3), "crop": P["pic"][1], "floor": FLOOR, "xfade": XF})
        t = t + w - XF                                                          # the next painting's `at`
        if i < n - 1:
            shots.append({"at": round(t, 3), "src": P["pic"][0], "crop": P["pic"][1], "zoom": [1.0, 1.0], "xfade": XF}); t += GAP
    shots.append({"at": round(P["end"] - LAST, 3), "src": P["pic"][0], "crop": P["pic"][1], "zoom": [1.0, 1.0], "xfade": XF})
    spec = {"name": name, "piece": P["piece"], "start": P["start"], "end": P["end"], "size": P["size"], "fade_in": 0.0, "fade_out": 0.0,
            "afade_in": 0.03, "afade_out": P.get("afade_out", 1.5), "afade_curve": "qua", "breath": False, "out_dir": "shorts", "shots": shots}
    json.dump(spec, open(f"{HERE}/shorts/{name}.json", "w"), indent=1)
    print(f"{name}: {total:.2f}s, parts at {[round(s_['at'] - P['start'], 2) for s_ in shots if s_['src'] != P['pic'][0]]}, "
          f"speed {[round((b - a) / w, 2) for (_, a, b, _), w in zip(parts, wins)]} x real time")

def blue_canvas():
    """The Blue Dancers painting in the coordinates of the sharp clip's first frame (the Codex vertical scene Muse started
    from), on a darkened blur of itself: ECC (affine, structure images) from a first guess — the painting fills the scene's
    width at its own size, 305/1536 down (Codex kept it, template NCC 0.59)."""
    import cv2, numpy as np
    sys.path.insert(0, os.path.join(HERE, "..", "debussy-impressions")); os.environ.setdefault("ALIGN_DATA", walk.DATA)
    import align as AL
    cap = cv2.VideoCapture(BLUE); ok, frame = cap.read(); cap.release(); assert ok
    P0 = cv2.imread(f"{walk.DATA}/art/blue-dancers.jpg"); fh, fw = frame.shape[:2]; ph, pw = P0.shape[:2]
    kf, kp = AL.WORK / max(fh, fw), AL.WORK / max(ph, pw)
    size = (round(fw * kf), round(fh * kf))
    T = AL.structure(cv2.resize(frame, size, interpolation=cv2.INTER_AREA))
    R = AL.structure(cv2.resize(P0, (round(pw * kp), round(ph * kp)), interpolation=cv2.INTER_AREA))
    s0 = fw / pw; M0 = np.float32([[s0, 0, 0], [0, s0, 305 / 1536 * fh]])
    Mw = (np.diag([kf, kf, 1.0]) @ np.vstack([M0, [0, 0, 1]]) @ np.diag([1 / kp, 1 / kp, 1.0]))[:2].astype(np.float32)
    def ncc(M):
        W_ = cv2.warpAffine(R, M, size); m = cv2.warpAffine(np.ones_like(R), M, size) > 0.5
        a, b = T[m], W_[m]; return float(((a - a.mean()) * (b - b.mean())).mean() / (a.std() * b.std()))
    Me = AL.ecc(T, R, Mw, size)
    best = Me if ncc(Me) > ncc(Mw) else Mw
    print(f"blue canvas: guess NCC {ncc(Mw):.3f}, ECC {ncc(Me):.3f}")
    M = (np.diag([1 / kf, 1 / kf, 1.0]) @ np.vstack([best, [0, 0, 1]]) @ np.diag([kp, kp, 1.0]))[:2].astype(np.float32)
    paint = cv2.warpAffine(P0, M, (fw, fh), flags=cv2.INTER_AREA)
    mask = cv2.GaussianBlur(cv2.warpAffine(np.ones((ph, pw), np.float32), M, (fw, fh)), (0, 0), 1.5)[..., None]
    fill = cv2.GaussianBlur(cv2.resize(P0, (fw, fh)), (0, 0), fw / 40) * 0.55
    cv2.imwrite(f"{walk.DATA}/shorts/blue-dancers-canvas.png", (paint * mask + fill * (1 - mask)).astype(np.uint8))
    # dissolve check: the canvas half over the clip's first frame
    cv2.imwrite(f"{walk.DATA}/shorts/blue-dancers-canvas-check.jpg",
                cv2.resize(cv2.addWeighted(frame, 0.5, (paint * mask + frame * (1 - mask)).astype(np.uint8), 0.5, 0), None, fx=0.3, fy=0.3))

def out(name, suffix=""): return f"{walk.DATA}/shorts/{name}{suffix}.mp4"

def loudness(path):
    r = subprocess.run(["ffmpeg", "-v", "info", "-i", path, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
    return float(re.findall(r"I:\s+(-?[\d.]+) LUFS", r)[-1]), float(re.findall(r"Peak:\s+(-?[\d.]+) dBFS", r)[-1])

def vertical(name):
    src = out(name); w, h, _ = walk.probe(src)
    y = round((VH - h) * LIFT) & ~1
    lufs, peak = loudness(src); gain = -18.0 - lufs
    af = f"volume={gain:.2f}dB" + (",alimiter=limit=0.89:level=false" if peak + gain > -1.0 else "")
    vf = (f"[0:v]split[a][b];[a]scale={VW}:{VH}:force_original_aspect_ratio=increase,crop={VW}:{VH},gblur=sigma=34,"
          f"eq=brightness=-0.07:saturation=0.85[bg];[bg][b]overlay=0:{y}[v]")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-filter_complex", vf, "-map", "[v]", "-map", "0:a", "-af", af,
                    "-c:v", "libx264", "-crf", "17", "-preset", "medium", "-pix_fmt", "yuv420p", "-r", str(walk.FPS),
                    "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-movflags", "+faststart", out(name, "-vertical")], check=True)
    print(f"{name}: picture {w}x{h} at y {y}, {lufs:.1f} LUFS {gain:+.1f} dB -> {out(name, '-vertical')}")

def check(name):
    """How cleanly the loop closes (the last frame against the first, mean abs difference 0-255), the loudness, and the
    longest stretch where the picture stands still (the paintings' solos should be the only ones: ≤ ~1 s)."""
    path = out(name, "-vertical"); dur = walk.probe(path)[2]
    import numpy as np
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vf", "scale=270:480", "-f", "rawvideo", "-pix_fmt", "gray", "-"],
                         capture_output=True).stdout
    a = np.frombuffer(raw, np.uint8).reshape(-1, 480, 270).astype(np.float32); d = np.abs(np.diff(a, axis=0)).mean(axis=(1, 2))
    still = d < 0.12 * np.median(d); runs, k0 = [], None
    for k, v in enumerate(still):
        if v and k0 is None: k0 = k
        if not v and k0 is not None: runs.append((k - k0, k0)); k0 = None
    if k0 is not None: runs.append((len(still) - k0, k0))
    runs.sort(reverse=True)
    print(f"{name}: still stretches (s @ s): {[(round(n / walk.FPS, 2), round(k / walk.FPS, 1)) for n, k in runs[:5]]}")
    def grab(t):
        b = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", path, "-frames:v", "1", "-vf", "scale=270:480",
                            "-f", "rawvideo", "-pix_fmt", "gray", "-"], capture_output=True).stdout
        return [x for x in b]
    a, b = grab(0), grab(dur - 1.5 / walk.FPS)
    diff = sum(abs(x - y) for x, y in zip(a, b)) / len(a)
    lufs, peak = loudness(path)
    print(f"{name}: {dur:.1f}s, loop seam {diff:.2f}, {lufs:.1f} LUFS, peak {peak:.1f} dBFS")

MACLEOD = ("\"{t}\" Kevin MacLeod (incompetech.com)\nLicensed under Creative Commons: By Attribution 3.0 License\n"
           "http://creativecommons.org/licenses/by/3.0/")
TEXTS = {   # name: (file, title, zh line, en line, music zh, music en)
    "s1-etoile": ("1-明星-竖屏", "听得见的舞·德加《明星》活过来了 The Dance You Can Hear: Degas's “The Star” comes alive",
                  "德加的《明星》（约 1876–77，奥赛博物馆）从画里走出来，跟着萨蒂《裸体歌舞》第一首跳了一段。",
                  "Degas's “The Star” (c. 1876–77, Musée d'Orsay) steps out of the painting and dances to Satie's Gymnopédie No. 1.",
                  "音乐：萨蒂《裸体歌舞》第一首（开头 0:00–0:21），Daria Baiocchi 演奏，CC0，来自 IMSLP / Wikimedia Commons。",
                  "Music: Satie, Gymnopédie No. 1 (opening, 0:00–0:21), performed by Daria Baiocchi, CC0, via IMSLP / Wikimedia Commons."),
    "s2-dance-class": ("2-舞蹈课-竖屏", "听得见的舞·德加《舞蹈课》活过来了 The Dance You Can Hear: Degas's “The Dance Class” comes alive",
                       "德加的《舞蹈课》（1874，大都会艺术博物馆）活过来一会儿，又回到画里。音乐是萨蒂《裸体歌舞》第三首。",
                       "Degas's “The Dance Class” (1874, The Met) comes alive for a moment, then goes back into the painting. "
                       "Music: Satie's Gymnopédie No. 3.",
                       "音乐：萨蒂《裸体歌舞》第三首（开头 0:00–0:21）。" + MACLEOD.format(t="Gymnopedie No 3"),
                       "Music: Satie, Gymnopédie No. 3 (opening, 0:00–0:21). " + MACLEOD.format(t="Gymnopedie No 3")),
    "s3-rehearsal": ("3-舞台上的排练-竖屏",
                     "听得见的舞·德加《舞台上的排练》活过来了 The Dance You Can Hear: Degas's “The Rehearsal on Stage” comes alive",
                     "德加的《舞台上的排练》（约 1874，奥赛博物馆）活过来一会儿，又回到画里。音乐是萨蒂《裸体歌舞》第二首。",
                     "Degas's “The Rehearsal on Stage” (c. 1874, Musée d'Orsay) comes alive for a moment, then goes back into the "
                     "painting. Music: Satie's Gymnopédie No. 2.",
                     "音乐：萨蒂《裸体歌舞》第二首（开头 0:00–0:21）。" + MACLEOD.format(t="Gymnopedie No 2"),
                     "Music: Satie, Gymnopédie No. 2 (opening, 0:00–0:21). " + MACLEOD.format(t="Gymnopedie No 2")),
    "s4-blue-dancers": ("4-蓝色舞者-竖屏",
                        "听得见的舞·德加《蓝色舞者》活过来了 The Dance You Can Hear: Degas's “Blue Dancers” comes alive",
                        "德加的《蓝色舞者》（1898，普希金造型艺术博物馆）：上场之前，舞者们在后台整理肩带。音乐是萨蒂《裸体歌舞》第三首的结尾。",
                        "Degas's “Blue Dancers” (1898, Pushkin Museum): backstage, the dancers fix their straps before going on. "
                        "Music: the end of Satie's Gymnopédie No. 3.",
                        "音乐：萨蒂《裸体歌舞》第三首（结尾 2:01–2:25）。" + MACLEOD.format(t="Gymnopedie No 3"),
                        "Music: Satie, Gymnopédie No. 3 (ending, 2:01–2:25). " + MACLEOD.format(t="Gymnopedie No 3")),
}
AI_ZH = "画面：画里的场景和舞者的动作是 AI 依据原画想象生成的（Codex 图像生成 + Muse 视频），不是历史影像；画作本身是公有领域。"
AI_ZH_BLUE = AI_ZH.replace("（Codex 图像生成 + Muse 视频）", "（Codex 图像生成，原画上下的部分也是 Codex 补出来的 + Muse 视频）")
AI_EN = ("About the images: the real-looking scene and the dancers' movement are AI-generated from the painting (Codex image "
         "generation + Muse video), not historical footage; the painting itself is in the public domain.")
AI_EN_BLUE = AI_EN.replace("(Codex image generation + Muse video)", "(Codex image generation, which also extended the scene above "
                           "and below the painting, + Muse video)")

def texts():
    doc = []
    for n in NAMES:
        f, title, zh, en, mz, me = TEXTS[n]; assert len(title) <= 100, (n, len(title))
        az, ae = (AI_ZH_BLUE, AI_EN_BLUE) if n == "s4-blue-dancers" else (AI_ZH, AI_EN)
        desc = "\n".join([zh, en, "", "完整版 / Full film：《听得见的舞》The Dance You Can Hear", "", mz, me, "", az, ae, "",
                          hashtags(["shorts", "satie", "gymnopedie", "degas", "ballet"])])
        doc += [f"========== {f}.mp4 ==========", "【标题 / Title】", title, "", "【简介 / Description】", desc, "",
                "【标签 / Tags】", tags(YT.OWN_TAGS), ""]
    doc += ["【上传设置 / Upload settings】",
            "· 四个竖屏短视频（1080×1920，30 fps，约 21–24 秒，-18 LUFS），每个都能无缝循环：第一帧和最后一帧是同一张画，音乐在下一个小节前淡出",
            "· 完整版上传后，把简介里的「完整版」换成它的链接，也可以在 Shorts 的「相关视频」里关联完整版",
            "· Altered or synthetic content：是 —— 画里的写实场景和舞者动作是 AI 生成的", "· 类别：Education", ""]
    path = f"{walk.DATA}/package/youtube-description.shorts.txt"; os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w").write("\n".join(doc)); print(path)

def main():
    cmd, names = sys.argv[1], sys.argv[2:] or NAMES
    if cmd == "texts": texts(); return
    if cmd == "canvas": blue_canvas(); return
    for n in names:
        if cmd == "plan": plan(n)
        elif cmd == "render": walk.MUSE = "sharp"; walk.render(json.load(open(f"{HERE}/shorts/{n}.json")), False)
        elif cmd == "vertical": vertical(n)
        elif cmd == "check": check(n)

if __name__ == "__main__":
    main()
