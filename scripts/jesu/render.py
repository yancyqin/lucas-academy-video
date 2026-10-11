"""Render 《耶稣，世人仰望的喜悦》 from edit.json.

  render.py                      render shots (cached), composite the picture, add the music
  render.py --force              re-render every shot
  render.py --mux-only [MUSIC]   keep picture.mp4, only (re)lay the music — edit.json's or MUSIC
                                 (same timing: another mix or master of the same recording)

A different recording of the piece moves every cut: run retime.py NEW_MUSIC first, then a
full render.

Each shot runs from its `at` to the next shot's `at`; neighbouring shots overlap
by DISSOLVE seconds centred on that point and cross-fade there. Subtitles are
drawn in Python, so one pass writes both the clean picture (for the .srt) and
the burned-in one.

Outputs (DATA/build/):
  picture.mp4     the picture alone (no audio) — what --mux-only reuses
  jesu-clean.mp4  picture + music, no text      jesu.srt  the subtitles as soft subs
  jesu-subs.mp4   picture + music + burned-in subtitles (only when edit.json
                  has "burn_subtitles": true)
"""
import json
import pathlib
import re
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import shots as RS  # noqa: E402

HERE = pathlib.Path(__file__).parent
EDIT = json.loads((HERE / "edit.json").read_text())
DATA = pathlib.Path(EDIT["data"])
JOURNEY = pathlib.Path(EDIT["journey"])
W, H, FPS = RS.W, RS.H, RS.FPS
D = EDIT["dissolve"]
FONT = DATA / "fonts/NotoSerifSC-Regular.otf"
FONT_REF = DATA / "fonts/NotoSerifSC-Light.otf"


def src_path(s):
    root, rel = s.split(":", 1)        # "jesu:C/C1-x.mp4" or "journey:N/04-x.webm"
    return str((DATA / "footage" if root == "jesu" else JOURNEY / "footage") / rel)


def shot_spans(total):
    shots = EDIT["shots"]
    out = []
    for i, s in enumerate(shots):
        start = s["at"]
        end = shots[i + 1]["at"] if i + 1 < len(shots) else total
        a = max(0.0, start - (D / 2 if i else 0))
        b = min(total, end + (D / 2 if i + 1 < len(shots) else 0))
        out.append((s, start, end, a, b))
    return out


def render_shot(i, s, a, b, force):
    out = DATA / f"build/shots/{i:02d}-{s['id']}.mp4"
    out.parent.mkdir(parents=True, exist_ok=True)
    key = json.dumps({**s, "len": round(b - a, 3)}, sort_keys=True)
    stamp = out.with_suffix(".json")
    if out.exists() and not force and stamp.exists() and stamp.read_text() == key:
        return out
    rec = {"path": src_path(s["src"]), **{k: v for k, v in s.items() if k not in ("src", "id", "at")}}
    if pathlib.Path(rec["path"]).suffix.lower() in RS.STILL_EXT:
        RS.render_still(rec, b - a, out)
    else:
        RS.render_video(rec, b - a, out)
    stamp.write_text(key)
    print(f"  shot {i:02d} {s['id']:<10} {b - a:5.1f}s  {pathlib.Path(rec['path']).name}", flush=True)
    return out


class Reader:
    def __init__(self, path):
        self.p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", str(path), "-f", "rawvideo",
                                   "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
        self.last = None

    def next(self):
        buf = self.p.stdout.read(W * H * 3)
        if len(buf) == W * H * 3:
            self.last = np.frombuffer(buf, np.uint8).reshape(H, W, 3)
        return self.last          # past the end: hold the last frame

    def close(self):
        self.p.stdout.close()
        self.p.kill()


def wrap(text, font, width):
    """Greedy wrap at clause punctuation, falling back to characters."""
    clauses, cur = [], ""
    for ch in text:
        cur += ch
        if ch in "，；。！？：、」":
            clauses.append(cur)
            cur = ""
    if cur:
        clauses.append(cur)
    lines, line = [], ""
    for c in clauses:
        if font.getlength(line + c) <= width:
            line += c
        else:
            if line:
                lines.append(line)
            line = ""
            for ch in c:          # a clause longer than a line
                if font.getlength(line + ch) > width:
                    lines.append(line)
                    line = ""
                line += ch
    if line:
        lines.append(line)
    return lines


def subtitle_layer(sub):
    st = EDIT["subtitle_style"]
    f = ImageFont.truetype(str(FONT), st["size"])
    fr = ImageFont.truetype(str(FONT_REF), st["ref_size"])
    lines = wrap(sub["text"], f, W * st["max_width"])
    lh = int(st["size"] * st["line_height"])
    block = lh * len(lines) + (st["ref_gap"] + st["ref_size"] if sub.get("ref") else 0)
    y0 = int(H * st["bottom"]) - block
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for k, ln in enumerate(lines):
        d.text((W / 2, y0 + k * lh), ln, font=f, fill=(255, 255, 255, 255), anchor="ma")
    if sub.get("ref"):
        d.text((W / 2, y0 + lh * len(lines) + st["ref_gap"]), sub["ref"], font=fr,
               fill=(225, 225, 225, 255), anchor="ma")
    # soft shadow so white text reads on bright skies
    halo = layer.getchannel("A").filter(ImageFilter.MaxFilter(5)).filter(
        ImageFilter.GaussianBlur(st["shadow_blur"]))
    halo = halo.point(lambda v: min(255, int(v * st["shadow_strength"])))
    shadow = Image.merge("RGBA", (*Image.new("RGB", (W, H), (0, 0, 0)).split(), halo))
    out = Image.alpha_composite(shadow, layer)
    a = np.asarray(out).astype(np.float32) / 255.0
    return a[..., :3], a[..., 3:]


def smooth(u):
    u = min(max(u, 0.0), 1.0)
    return u * u * (3 - 2 * u)


def music_track(src=None):
    """The music, loudness-normalised and padded with the silent tail -> (path, length)."""
    src = pathlib.Path(src) if src else DATA / EDIT["music"]
    out = DATA / "build/music.wav"
    # two-pass loudnorm to -16 LUFS, -1.5 dBTP
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(src), "-af",
                        "loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True)
    m = json.loads(re.findall(r"\{[^{}]*\}", r.stderr)[-1])
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(src), "-af",
                    f"loudnorm=I=-16:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
                    f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:"
                    f"offset={m['target_offset']}:linear=true,aresample=48000,"
                    f"apad=pad_dur={EDIT.get('tail', 0)}",
                    "-c:a", "pcm_s24le", str(out)], check=True)
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                "-of", "csv=p=0", str(out)], capture_output=True, text=True).stdout)
    return out, dur


def srt(subs, path):
    def ts(t):
        ms = int(round(t * 1000))
        return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"
    lines = []
    for k, s in enumerate(subs, 1):
        body = s["text"] + (f"\n—— {s['ref']}" if s.get("ref") else "")
        lines.append(f"{k}\n{ts(s['start'])} --> {ts(s['end'])}\n{body}\n")
    path.write_text("\n".join(lines))


def mux(picture, music, out):
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(picture), "-i", str(music),
                    "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "256k",
                    "-shortest", "-movflags", "+faststart", str(out)], check=True)


def main():
    force = "--force" in sys.argv
    (DATA / "build").mkdir(exist_ok=True)
    if "--mux-only" in sys.argv:
        rest = [a for a in sys.argv[sys.argv.index("--mux-only") + 1:] if not a.startswith("--")]
        music, total = music_track(rest[0] if rest else None)
        mux(DATA / "build/picture.mp4", music, DATA / "build/jesu-clean.mp4")
        print(f"wrote jesu-clean.mp4 with {rest[0] if rest else EDIT['music']} ({total:.1f} s)")
        return
    music, total = music_track()
    spans = shot_spans(total)
    print(f"music {total:.2f} s, {len(spans)} shots")
    files = [render_shot(i, s, a, b, force) for i, (s, start, end, a, b) in enumerate(spans)]

    subs = EDIT.get("subtitles") or EDIT.get("verses") or []
    if EDIT.get("write_srt", True):
        srt(subs, DATA / "build/jesu.srt")
    burn = EDIT.get("burn_subtitles", True)
    layers = [subtitle_layer(s) for s in subs] if burn else []
    fade = EDIT["subtitle_style"]["fade"]

    enc = lambda path: subprocess.Popen(  # noqa: E731
        ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
         "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "17",
         "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(path)],
        stdin=subprocess.PIPE)
    clean = enc(DATA / "build/picture.mp4")
    burned = enc(DATA / "build/picture-subs.mp4") if burn else None
    readers = {}
    n = int(round(total * FPS))
    fade_in, fade_out = EDIT["fade_in"], EDIT["fade_out"]
    for fi in range(n):
        t = fi / FPS
        frame = np.zeros((H, W, 3), np.float32)
        for i, (s, start, end, a, b) in enumerate(spans):
            if not (a <= t < b):
                if i in readers and t >= b:
                    readers.pop(i).close()
                continue
            if i not in readers:
                readers[i] = Reader(files[i])
            img = readers[i].next().astype(np.float32)
            w = 1.0
            if i > 0:                          # fading in over the previous shot
                w *= smooth((t - (start - D / 2)) / D)
            if i + 1 < len(spans):             # fading out under the next shot
                w *= 1 - smooth((t - (end - D / 2)) / D)
            frame += img * w
        g = smooth(t / fade_in) * smooth((total - t) / fade_out)
        frame *= g
        clean.stdin.write(np.clip(frame, 0, 255).astype(np.uint8).tobytes())
        if not burn:
            if fi % (FPS * 20) == 0:
                print(f"  {t:6.1f} s", flush=True)
            continue
        for (rgb, alpha), s in zip(layers, subs):
            if s["start"] <= t < s["end"]:
                k = smooth((t - s["start"]) / fade) * smooth((s["end"] - t) / fade)
                al = alpha * k
                frame = frame * (1 - al) + rgb * 255 * al
        burned.stdin.write(np.clip(frame, 0, 255).astype(np.uint8).tobytes())
        if fi % (FPS * 20) == 0:
            print(f"  {t:6.1f} s", flush=True)
    for r in readers.values():
        r.close()
    for p in (clean, burned):
        if p:
            p.stdin.close()
            p.wait()
    mux(DATA / "build/picture.mp4", music, DATA / "build/jesu-clean.mp4")
    if burn:
        mux(DATA / "build/picture-subs.mp4", music, DATA / "build/jesu-subs.mp4")
    print("wrote picture.mp4, jesu-clean.mp4" + (", jesu-subs.mp4" if burn else "")
          + (", jesu.srt" if EDIT.get("write_srt", True) else ""))


if __name__ == "__main__":
    main()
