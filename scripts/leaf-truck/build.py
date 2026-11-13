"""一片落叶，为什么让卡车急刹车？ — rough-cut builder.

  build.py assets        clips → out/leaf-truck/public (1920x1080, 24 fps), stills
  build.py plan          line timing from the takes, shots, tags → out/leaf-truck/build/timeline.json
  build.py render [s]    Remotion picture at scale s (default 0.5 for drafts)
  build.py mix           both voice tracks + K.265 ducked under the voice, captions, mux

Both languages share one picture: every line gets a slot as long as its longer take (Louise zh/en 1.1).
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "out/leaf-truck"
PUB, BUILD = OUT / "public", OUT / "build"
BASE = Path("/Users/yqin/repo/playground/lucas-academy-video/out/autonomous-driving-seven-ways/source")
MUSE = Path("/Users/yqin/repo/playground/lucas-academy-video-data/leaf-truck/muse")   # Yancy's Muse clips G1–G8 (SOURCES.json)
# Yancy 11-12: 「不要用小星星了」, then 「可以用 降D大调前奏曲 升C小调夜曲」. All from Musopen "Set Chopin Free" (CC0;
# lucas-academy-video-data/leaf-truck/music/SOURCES.md). One picture serves every version: `mix <name>`.
#   name: (file, [(film s, source s), ...]) — the source plays on from each point; 3 s equal-power crossfades.
MUSIC_DIR = Path("/Users/yqin/repo/playground/lucas-academy-video-data/leaf-truck/music/raw")
MUSICS = {
    # Waltz in C-sharp minor, Op. 64 No. 2 (Olga Gurevich), complete: più mosso under the 47 stops and the chain reaction
    "waltz": ("chopin-waltz-op64-2-musopen.flac", [(0.0, 0.0)]),
    # Nocturne in C-sharp minor, B. 49 (Frank Lévy), complete: 225 s, ends in C-sharp major as the end card fades
    "nocturne": ("chopin-nocturne-b49-musopen.flac", [(0.0, 0.0)]),
    # Prelude in D-flat major, Op. 28 No. 15 (Jeannette Fang): straight to the voice gap before lf06-04, where the
    # C-sharp minor middle (first climax under the chain reaction) gives way to the D-flat return (source 4:17, just after the last climax)
    "prelude": ("chopin-prelude-op28-15-musopen.flac", [(0.0, 0.0), (165.5, 257.0)]),
}
MUSIC_PICK = "waltz"
MUSIC_END = 226.0   # s: film time by which every version's last chord has died away
FPS, RATE = 24, 48000
LANGS = ("en", "zh")
TARGET = "I=-16:TP=-1.5:LRA=9"
UNDER_DB, GAP_DB, MIN_GAP, ATTACK, RELEASE = -20.0, -9.0, .8, .35, .8   # scripts/music_ducking.py defaults

CLIPS = {  # name: (source, start, seconds)
    "truck": (BASE / "v6/truck.mp4", 0, 10), "headon": (BASE / "v6/truck-headon.mp4", 0, 10),
    "crossing": (BASE / "v6/crossing-moving.mp4", 0, 10), "plane_alt": (BASE / "v5/plane_alt.mp4", 3.0, 12),
    "plane": (BASE / "v5/plane.mp4", 0, 9.6), "keys": (BASE / "v5/keys.mp4", 0, 5.6),
    **{g: (MUSE / f"{g}.mp4", 0, 10) for g in ("G1", "G2", "G3", "G4", "G5", "G6", "G7", "G8")},
}


def run(*a, **k):
    return subprocess.run([str(x) for x in a], check=True, **k)


def assets():
    (PUB / "clips").mkdir(parents=True, exist_ok=True)
    (PUB / "stills").mkdir(parents=True, exist_ok=True)
    for name, (src, start, secs) in CLIPS.items():
        run("ffmpeg", "-v", "error", "-y", "-ss", start, "-t", secs, "-i", src, "-an", "-vf",
            "fps=24,scale=1920:1080:force_original_aspect_ratio=increase:flags=lanczos,crop=1920:1080,setsar=1",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", 16, "-pix_fmt", "yuv420p", "-g", 24, PUB / f"clips/{name}.mp4")
    run("ffmpeg", "-v", "error", "-y", "-i", BASE / "v6/truck-headon.mp4", "-frames:v", 1,
        "-vf", "scale=1920:1080:flags=lanczos", "-q:v", 2, PUB / "stills/headon-start.jpg")
    run("ffmpeg", "-v", "error", "-y", "-sseof", "-0.2", "-i", BASE / "v6/truck-headon.mp4", "-frames:v", 1,
        "-vf", "scale=1920:1080:flags=lanczos", "-q:v", 2, PUB / "stills/headon-end.jpg")
    # leaves in front of the truck after the gust (truck.mp4, 8 s): the lower right of the frame
    run("ffmpeg", "-v", "error", "-y", "-ss", 8, "-i", BASE / "v6/truck.mp4", "-frames:v", 1,
        "-vf", "crop=iw*0.5:ih*0.5:iw*0.5:ih*0.5,scale=1920:1080:flags=lanczos", "-q:v", 2, PUB / "stills/leaves.jpg")
    for g in ("G2", "G4"):   # first frames for the title card and the split screen
        run("ffmpeg", "-v", "error", "-y", "-i", MUSE / f"{g}.mp4", "-frames:v", 1,
            "-vf", "scale=1920:1080:flags=lanczos", "-q:v", 2, PUB / f"stills/{g.lower()}-start.jpg")
    run("ffmpeg", "-v", "error", "-y", "-ss", 8, "-i", BASE / "v6/crossing-moving.mp4", "-frames:v", 1,
        "-vf", "scale=1920:1080:flags=lanczos", "-q:v", 2, PUB / "stills/crossing-8s.jpg")
    print("assets ok")


# ---------------------------------------------------------------- takes
def take(lang, key):
    pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", str(OUT / f"takes/{lang}/{key}.wav"), "-ac", "1", "-ar", str(RATE),
                          "-f", "f32le", "-"], capture_output=True, check=True).stdout
    x = np.frombuffer(pcm, np.float32)
    hop = RATE // 100
    rms = np.sqrt((x[:len(x) // hop * hop].reshape(-1, hop) ** 2).mean(axis=1))
    loud = np.flatnonzero(rms > 10 ** (-40 / 20))
    run_ok = [i for i in loud if all(j in set(loud) for j in range(i, i + 10))]
    start = (run_ok[0] if run_ok else loud[0]) * hop
    return x[max(0, start - hop * 5):min(len(x), (loud[-1] + 1) * hop + hop * 15)].copy()


def lines(lang):
    return json.loads((OUT / f"takes/{lang}.json").read_text())


# ---------------------------------------------------------------- plan
QUESTION_PAUSE = {"lf04-04": 3.0}
SECTION_GAP = .9
EDIT = [  # first line id → shot; a shot lasts until the next one starts
    # Muse clips wobble for their first ~8 frames (Yancy 11-12: 「前半秒晃一下」), so none starts before 0.5 s
    ("lf01-01", {"kind": "clip", "src": "clips/G1.mp4", "start": .5, "rate": .8, "badge": "recon"}),
    ("lf01-03", {"kind": "clip", "src": "clips/truck.mp4", "start": 1.2, "badge": "recon"}),
    ("lf01-04", {"kind": "clip", "src": "clips/G8.mp4", "start": .5, "rate": .8, "badge": "recon"}),
    ("lf01-05", {"kind": "clip", "src": "clips/G2.mp4", "start": .5, "rate": .75, "badge": "recon"}),
    ("title", {"kind": "title"}),
    ("lf02-01", {"kind": "counter"}),
    ("lf02-02", {"kind": "clip", "src": "clips/G3.mp4", "start": .5, "jolt": 2.0, "badge": "recon"}),
    ("lf02-03", {"kind": "clip", "src": "clips/G4.mp4", "start": .5, "rate": .5, "badge": "recon",
                 "labels": [{"en": "14.4 cm", "zh": "只有一掌高 · a hand's height", "x": 1440, "y": 430, "at": 3.2, "arrow": True}]}),
    ("lf02-04", {"kind": "split"}),
    ("lf03-01", {"kind": "clip", "src": "clips/G5.mp4", "start": 5.0, "badge": "recon"}),
    ("lf03-02", {"kind": "sensor"}),
    ("lf03-03", {"kind": "stops"}),
    ("lf04-01", {"kind": "clip", "src": "clips/crossing.mp4", "start": 0, "badge": "idea"}),
    ("lf04-03", {"kind": "clip", "still": "stills/crossing-8s.jpg", "badge": "idea", "marks": [
        {"x": 1080, "y": 360, "w": 210, "h": 260, "en": "Person?", "zh": "人？", "color": "#ffcf8d", "at": .3},
        {"x": 1330, "y": 520, "w": 420, "h": 150, "en": "Leaves?", "zh": "落叶？", "color": "#ffcf8d", "dashed": True, "at": 1.4}]}),
    ("lf04-04", {"kind": "ab", "reveal": False}),
    ("lf04-05", {"kind": "ab", "reveal": True}),
    ("lf04-06", {"kind": "lidar"}),
    ("lf05-01", {"kind": "clip", "src": "clips/G6.mp4", "start": .5, "badge": "recon"}),
    ("lf05-02", {"kind": "ripple"}),
    ("lf06-01", {"kind": "dial"}),
    ("lf06-03", {"kind": "goal"}),
    ("lf06-04", {"kind": "fixes"}),
    ("lf07-01", {"kind": "clip", "src": "clips/plane_alt.mp4", "start": 0}),
    ("lf07-03", {"kind": "clip", "src": "clips/plane.mp4", "start": 1.4}),
    ("lf07-04", {"kind": "clip", "src": "clips/keys.mp4", "start": 0}),
    ("lf07-05", {"kind": "together"}),
    ("lf07-06", {"kind": "clip", "src": "clips/G7.mp4", "start": .5, "badge": "recon"}),
    ("end", {"kind": "end"}),
]
TAGS = {"lf03-04": ("Divergent → Critical", "发散 → 批判"), "lf04-04": ("Critical thinking", "批判性思维"),
        "lf05-01": ("Systems thinking", "系统思维"), "lf06-03": ("Backward thinking", "逆向思维"),
        "lf06-04": ("Integrative thinking", "综合思维")}


def plan():
    rows = {l: {r["id"]: r for r in lines(l)} for l in LANGS}
    ids = [r["id"] for r in lines("zh")]
    assert ids == [r["id"] for r in lines("en")]
    length = {i: max(len(take(l, i)) for l in LANGS) / RATE for i in ids}
    t, starts, out_lines, sections = .8, {}, [], {}
    for n, i in enumerate(ids):
        sec = i[:4].upper()
        if n and sec != ids[n - 1][:4].upper():
            t += SECTION_GAP
            if sec == "LF02":           # title card after the cold open
                starts["title"] = t
                t += 3.6
        sections.setdefault(sec, t)
        starts[i] = t
        text = rows["zh"][i]["text"]
        q = text.rstrip("」”").endswith("？")
        out_lines.append({"id": i, "at": round(t, 3), "len": round(length[i], 3),
                          "text": {l: rows[l][i]["text"] for l in LANGS}})
        t += length[i] + (QUESTION_PAUSE.get(i, 1.3) if q else .4)
    starts["end"] = t + 2.3            # the sunset shot runs on a little before the end card
    total = max(starts["end"] + 4.5, MUSIC_END + 2.5)
    frames = int(np.ceil(total * FPS))
    shots = []
    for k, (key, spec) in enumerate(EDIT):
        a = round(starts[key] * FPS)
        b = round(starts[EDIT[k + 1][0]] * FPS) if k + 1 < len(EDIT) else frames
        shot = {**spec, "from": a, "dur": b - a}
        if "src" in spec:   # never run past the end of a clip: slow it down a little instead (not below 0.75x)
            name = Path(spec["src"]).stem
            room = CLIPS[name][2] - spec.get("start", 0) - .05
            rate = spec.get("rate", 1)
            if (b - a) / FPS * rate > room:
                rate = room / ((b - a) / FPS)
                assert rate >= .75, (name, rate)
                shot["rate"] = round(rate, 4)
                print(f"  {name}: {rate:.2f}x to fill {(b - a) / FPS:.1f}s")
        shots.append(shot)
    shots[0]["dur"] += shots[0]["from"]   # the first picture is up from frame 0, before the first line starts
    shots[0]["from"] = 0
    tags = []
    for key, (en, zh) in TAGS.items():
        a = round(starts[key] * FPS)
        tags.append({"from": a, "dur": round(4.5 * FPS), "en": en, "zh": zh})
    sections["END"] = starts["end"]
    timeline = {"frames": frames, "shots": shots, "tags": tags, "lines": out_lines, "sections": sections}
    BUILD.mkdir(parents=True, exist_ok=True)
    (BUILD / "timeline.json").write_text(json.dumps(timeline, ensure_ascii=False, indent=1) + "\n")
    print(f"{frames} frames = {frames / FPS:.1f} s, {len(shots)} shots")


# ---------------------------------------------------------------- render
def render(scale="0.5"):
    tl = json.loads((BUILD / "timeline.json").read_text())
    props = BUILD / "props.json"
    props.write_text(json.dumps({k: tl[k] for k in ("frames", "shots", "tags")}, ensure_ascii=False))
    run("node", REPO / "scripts/leaf-truck/render.cjs", props, BUILD / "picture.mp4", scale)


# ---------------------------------------------------------------- sound
def music_bed(tl, name):
    """The chosen piece laid on the film by its (film, source) points; ducking and edge fades come from duck()."""
    path, segs = MUSICS[name]
    n = int(tl["frames"] / FPS * RATE)
    pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", str(MUSIC_DIR / path), "-ac", "1", "-ar", str(RATE), "-f", "f32le",
                          "-"], capture_output=True, check=True).stdout
    x = np.frombuffer(pcm, np.float32)
    bed = np.zeros(n, np.float32)
    xf = int(3.0 * RATE)
    for k, (film, src) in enumerate(segs):
        a = int(film * RATE) - (xf // 2 if k else 0)
        b = int(segs[k + 1][0] * RATE) + xf // 2 if k + 1 < len(segs) else n
        s0 = int(src * RATE) - (int(film * RATE) - a)
        seg = np.pad(x[s0:s0 + (b - a)], (0, max(0, (b - a) - len(x[s0:s0 + (b - a)]))))
        env = np.ones(b - a, np.float32)
        ramp = np.linspace(0, np.pi / 2, xf)
        if k:
            env[:xf] = np.sin(ramp)
        if k + 1 < len(segs):
            env[-xf:] = np.cos(ramp)
        bed[a:b] += seg * env
    return bed


def duck(bed, spans, voice_rms, bed_rms):
    t = np.arange(len(bed)) / RATE
    merged = []
    for a, b in sorted(spans):
        if merged and a - merged[-1][1] < MIN_GAP:
            merged[-1][1] = max(merged[-1][1], b)
        else:
            merged.append([a, b])
    d = np.zeros(len(bed), np.float32)
    for a, b in merged:
        lo, hi = int(max(0, a - ATTACK) * RATE), int(min(len(bed) / RATE, b + RELEASE) * RATE)
        x = t[lo:hi]
        pre = np.clip((x - (a - ATTACK)) / ATTACK, 0, 1)
        post = np.clip(1 - (x - b) / RELEASE, 0, 1)
        v = np.where(x < a, pre * pre * (3 - 2 * pre), np.where(x > b, post * post * (3 - 2 * post), 1.0))
        d[lo:hi] = np.maximum(d[lo:hi], v)
    gain = 10 ** ((GAP_DB + (UNDER_DB - GAP_DB) * d) / 20) * voice_rms / bed_rms
    edge = np.minimum(1, np.minimum(t / 2.0, (t[-1] - t) / 3.0))
    return bed * gain * edge


# road sound under the footage: each clip's own generated audio (Whisper heard no speech in these; G1 and the
# crossing clip are left out because it heard something word-like), level-matched, quiet, fading at the cuts
FX_CLIPS = {"truck", "G2", "G3", "G4", "G5", "G6", "G7", "G8"}
FX_DB = -18.0   # below the voice


def fx_bed(tl, n):
    bed = np.zeros(n, np.float32)
    fade = int(.3 * RATE)
    for sh in tl["shots"]:
        name = Path(sh.get("src", "")).stem
        if sh["kind"] != "clip" or name not in FX_CLIPS:
            continue
        src, start, _ = CLIPS[name]
        pcm = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(start + sh.get("start", 0)), "-t", str(sh["dur"] / FPS),
                              "-i", str(src), "-map", "0:a:0", "-ac", "1", "-ar", str(RATE), "-f", "f32le", "-"],
                             capture_output=True, check=True).stdout
        x = np.frombuffer(pcm, np.float32).copy()
        x /= float(np.sqrt((x ** 2).mean())) + 1e-9
        k = min(fade, len(x) // 2)
        x[:k] *= np.linspace(0, 1, k)
        x[-k:] *= np.linspace(1, 0, k)
        a = int(sh["from"] / FPS * RATE)
        x = x[:n - a]
        bed[a:a + len(x)] += x
    return bed


LINE = {"zh": 22, "en": 42}


def wrap_long(clause, lang):
    """A clause longer than one caption line, cut into nearly equal pieces (at spaces in English)."""
    if len(clause) <= LINE[lang]:
        return [clause]
    k = -(-len(clause) // LINE[lang])
    while True:
        if lang == "zh":
            step = -(-len(clause) // k)
            out = [clause[i:i + step] for i in range(0, len(clause), step)]
        else:
            words, out, cur = clause.split(), [], ""
            target = len(clause) / k
            for w in words:
                if cur and len(cur) + 1 + len(w) > target + 6:
                    out.append(cur)
                    cur = w
                else:
                    cur = f"{cur} {w}" if cur else w
            out.append(cur)
        if all(len(x) <= LINE[lang] for x in out):
            return out
        k += 1


def cues_for(text, lang):
    pat = r"[^。？！；：，、]+[。？！；：，、]?" if lang == "zh" else r"[^.?!;:,]+[.?!;:,]?"
    parts = [x.strip() for x in re.findall(pat, text) if x.strip()]
    sep = "" if lang == "zh" else " "
    parts = [q for x in parts for q in wrap_long(x, lang)]
    join = lambda xs: sep.join(xs)

    def as_lines(xs):
        if len(join(xs)) <= LINE[lang]:
            return [join(xs)]
        fits = [k for k in range(1, len(xs)) if len(join(xs[:k])) <= LINE[lang] and len(join(xs[k:])) <= LINE[lang]]
        if not fits:
            return None
        k = min(fits, key=lambda k: abs(len(join(xs[:k])) - len(join(xs[k:]))))
        return [join(xs[:k]), join(xs[k:])]

    best = {0: (0, 0, [])}
    for i in range(1, len(parts) + 1):
        opts = [(best[j][0] + 1, max(best[j][1], len(join(parts[j:i]))), best[j][2] + [ls])
                for j in range(i) if j in best and (ls := as_lines(parts[j:i]))]
        if opts:
            best[i] = min(opts, key=lambda o: o[:2])
    return best[len(parts)][2] if len(parts) in best else [[text]]


def stamp(x):
    ms = round(x * 1000)
    return f"{ms // 3600000:02}:{ms // 60000 % 60:02}:{ms // 1000 % 60:02},{ms % 1000:03}"


def mix(music=MUSIC_PICK):
    tl = json.loads((BUILD / "timeline.json").read_text())
    n = int(tl["frames"] / FPS * RATE)
    bed = music_bed(tl, music)[:n]
    bed = np.pad(bed, (0, n - len(bed)))
    fx = fx_bed(tl, n)
    tracks = {}
    for lang in LANGS:
        voice = np.zeros(n, np.float32)
        spans, cues = [], []
        for ln in tl["lines"]:
            clip = take(lang, ln["id"])
            s = int(ln["at"] * RATE)
            voice[s:s + len(clip)] += clip[:n - s]
            spans.append((ln["at"], ln["at"] + len(clip) / RATE))
            groups = cues_for(ln["text"][lang], lang)
            w = [sum(map(len, g)) for g in groups]
            acc = 0
            for g, wi in zip(groups, w):
                a = ln["at"] + len(clip) / RATE * acc / sum(w)
                acc += wi
                cues.append([a, ln["at"] + len(clip) / RATE * acc / sum(w) + (.3 if acc == sum(w) else 0), "\n".join(g)])
        voiced = np.concatenate([voice[int(a * RATE):int(b * RATE)] for a, b in spans])
        v_rms = float(np.sqrt((voiced ** 2).mean()))
        b_rms = float(np.sqrt((bed[np.abs(bed) > 1e-4] ** 2).mean()))
        mixdown = voice + duck(bed, spans, v_rms, b_rms) + fx * v_rms * 10 ** (FX_DB / 20)
        path = BUILD / f"mix-{lang}.{music}.wav"
        run("ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", RATE, "-ac", 1, "-i", "-", "-c:a", "pcm_s16le", path,
            input=np.clip(mixdown, -1, 1).astype(np.float32).tobytes())
        tracks[lang] = path
        for i in range(len(cues) - 1):
            cues[i][1] = min(cues[i][1], cues[i + 1][0] - .02)
        name = "captions.en.srt" if lang == "en" else "captions.zh-Hans.srt"
        (BUILD / name).write_text("\n".join(f"{i}\n{stamp(a)} --> {stamp(b)}\n{t}\n" for i, (a, b, t) in enumerate(cues, 1)))
    norm = {}
    for lang in LANGS:
        err = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(tracks[lang]), "-af",
                              f"loudnorm={TARGET}:print_format=json", "-f", "null", "-"], capture_output=True, text=True).stderr
        st = json.loads(err[err.rfind("{"):err.rfind("}") + 1])
        norm[lang] = (f"loudnorm={TARGET}:measured_I={st['input_i']}:measured_TP={st['input_tp']}:measured_LRA={st['input_lra']}:"
                      f"measured_thresh={st['input_thresh']}:offset={st['target_offset']}:linear=true")
    out = BUILD / f"leaf-truck.{music}.mp4"
    run("ffmpeg", "-v", "error", "-y", "-i", BUILD / "picture.mp4", "-i", tracks["en"], "-i", tracks["zh"],
        "-map", "0:v:0", "-map", "1:a:0", "-map", "2:a:0", "-c:v", "copy", "-filter:a:0", norm["en"], "-filter:a:1", norm["zh"],
        "-c:a", "aac", "-b:a", "160k", "-ac", 1, "-ar", 48000, "-shortest",
        "-metadata:s:a:0", "language=eng", "-metadata:s:a:0", "handler_name=English",
        "-metadata:s:a:1", "language=zho", "-metadata:s:a:1", "handler_name=简体中文",
        "-disposition:a:0", "default", "-disposition:a:1", 0, "-movflags", "+faststart", out)
    for lang, idx in (("en", 0), ("zh", 1)):
        s = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(out), "-map", f"0:a:{idx}", "-af",
                            "loudnorm=print_format=json", "-f", "null", "-"], capture_output=True, text=True).stderr
        st = json.loads(s[s.rfind("{"):s.rfind("}") + 1])
        print(lang, "LUFS", st["input_i"], "TP", st["input_tp"])
    print(out)


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "mix":
        mix(*sys.argv[2:3])
    else:
        {"assets": assets, "plan": plan}.get(cmd, lambda: render(*sys.argv[2:]))()
