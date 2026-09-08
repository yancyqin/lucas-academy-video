"""Render every Rejoice shot to its own 1920x1080 file at exactly its screen length.

Doing the trims, the slowdowns and the fog here rather than in Remotion is what
makes the no-loop rule checkable: each file is as long as the span it has to fill,
so nothing can wrap around to its own first frame. verify_shots.py re-measures the
written files and fails if any of them came out short.

Slowdowns are forward-only -- setpts stretches the presentation timestamps, it does
not reverse or ping-pong. Interpolation is `blend` rather than `mci`, because
motion compensation invents vectors on water, cloud and bubble footage and warps it.

  .venv-align/bin/python scripts/mv/build_shots.py            # all
  .venv-align/bin/python scripts/mv/build_shots.py S13 S29     # some
"""
import pathlib, subprocess, sys, json

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from shots import SHOTS, W, H, FPS

REPO = pathlib.Path(__file__).resolve().parents[2]
SRC = REPO / "public/footage"
OUT = REPO / "public/footage/rejoice"
OUT.mkdir(parents=True, exist_ok=True)
WAN = REPO / "tmp/rejoice/wan"

FILL = f"scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,crop={W}:{H}"


def probe(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", str(path)], capture_output=True, text=True)
    return float(r.stdout.strip())


def edge_mask(path, w, h, hold=0.66, feather=0.34):
    """A white centre fading to black at the frame edge, written once and reused.

    Used to hide what de-watermarking leaves behind around the border: the sharp
    picture is kept only inside `hold`, and past that it crossfades into a blurred
    copy of itself, so the edges go soft instead of showing the retouching.
    """
    from PIL import Image
    import numpy as np
    if pathlib.Path(path).exists():
        return path
    ys, xs = np.mgrid[0:h, 0:w]
    dx = np.abs(xs / (w - 1) * 2 - 1)
    dy = np.abs(ys / (h - 1) * 2 - 1)
    d = np.maximum(dx, dy)
    a = np.clip((1.0 - d) / max(feather, 1e-6), 0.0, 1.0)
    a = a * a * (3 - 2 * a)                      # smoothstep, so the seam is invisible
    Image.fromarray((a * 255).astype("uint8"), "L").save(path)
    return path


def fog_filter(strength):
    """Veil the picture rather than brighten it.

    Screening a lifted blur over a 4K close-up just blows it out -- the first pass
    turned the woman's face bright pink and left every feature perfectly readable,
    which is the opposite of "we could not understand". So the bulk of the strength
    now mixes in a blurred copy, which reads as fog and shallow depth of field and
    actually takes detail away; only a little goes to a screened haze for glow.
    """
    veil = round(strength, 3)
    haze = round(min(0.16, strength * 0.26), 3)
    return (f"split[fa][fb];[fb]gblur=sigma=26[fbl];"
            f"[fa][fbl]blend=all_mode=average:all_opacity={veil}[fm];"
            f"[fm]split[ga][gb];[gb]boxblur=30:2,eq=brightness=0.04[gbl];"
            f"[ga][gbl]blend=all_mode=screen:all_opacity={haze}")


def resolve(src):
    p = SRC / src
    if p.exists():
        return p
    p2 = WAN / src
    if p2.exists():
        return p2
    return None


def build(sid, src, src_in, start, end, move, tr):
    span = round(end - start, 3)
    dst = OUT / f"{sid}.mp4"
    path = resolve(src)
    if path is None:
        print(f"{sid}: SOURCE MISSING {src}  (skipped)")
        return False

    seg_pre, seg_src = "", None
    if tr.get("segments"):
        # Different speeds either side of a moment that has to stay put. Joined
        # inside one file so the seam is a straight cut, not a dissolve -- a
        # dissolve across a flash would smear the very frame it is built around.
        legs = []
        for k, (s0, s1, want) in enumerate(tr["segments"]):
            f = want / (s1 - s0)
            legs.append(f"[0:v]trim=start={s0}:end={s1},setpts=(PTS-STARTPTS)*{f:.6f}[sg{k}]")
            print(f"{sid}:   seg{k} src {s0}-{s1}s -> {want}s on screen  ({f:.3f}x)", flush=True)
        n = len(tr["segments"])
        seg_pre = ";".join(legs) + ";" + "".join(f"[sg{k}]" for k in range(n)) + \
                  f"concat=n={n}:v=1:a=0[cat]"
        seg_src = "[cat]"

    chain = []
    if tr.get("still"):
        z0, z1 = tr.get("zoom", (1.04, 1.16))
        # A still needs the movement supplied. zoompan drives the zoom per frame;
        # the source is pre-scaled so the pan has real pixels to work with.
        frames = int(round(span * FPS))
        big_w, big_h = W * 2, H * 2
        zexpr = f"{z0}+({z1}-{z0})*on/{max(frames - 1, 1)}"
        chain.append(f"scale={big_w}:{big_h}:force_original_aspect_ratio=increase:flags=lanczos,"
                     f"crop={big_w}:{big_h},"
                     f"zoompan=z='{zexpr}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
                     f":d=1:s={big_w}x{big_h}:fps={FPS},"
                     f"scale={W}:{H}:flags=lanczos")
        # -framerate matters: an image input defaults to 25 fps, so a 3.6s still
        # yielded 90 frames and zoompan emitted a 3.0s clip with the zoom cut short.
        inp = ["-loop", "1", "-framerate", str(FPS), "-t", f"{span}", "-i", str(path)]
    else:
        # srcEnd caps how much source the shot may draw on, which is what forces a
        # slowdown when the clip is long enough to cover the span at 1x. The face is
        # split this way: the first half stretched over 17s, the second over 12.2s.
        hold = tr.get("holdLast", 0.0)
        move_span = span - hold          # the moving part ends this early
        avail = (tr["srcEnd"] if tr.get("srcEnd") is not None else probe(path)) - src_in
        # Stretch slightly past the span: interpolation rounds frames off the end
        # and the clip is cut to length anyway, so overshooting costs nothing while
        # coming up 0.1s short would leave a gap the dissolve cannot cover.
        if tr.get("fit"):
            # Compress the whole source into the span. Used where the point is to
            # see the entire move, not a piece of it at natural speed.
            factor = span / avail
        else:
            # Overshoot proportionally: interpolation trims the tail, and the
            # heavier the stretch the more it trims -- a flat margin left a 4.9x
            # shot 0.14s short of its span.
            if hold:
                # Fit the source exactly into the moving part. The usual margin
                # overshoots and then gets trimmed, and trimming here would cut off
                # the very last frames -- the ones this shot exists to hold on.
                factor = move_span / avail
            else:
                factor = (move_span * 1.03 + 0.3) / avail if avail < move_span else 1.0
        chain.append(FILL)
        if tr.get("reverse"):
            # Played backwards on purpose: this clip pulls focus the wrong way for
            # the section, and running it in reverse turns its own defocus into a
            # focus pull. Scaled before reversing so the whole segment does not have
            # to be buffered at source resolution.
            chain.append("reverse")
        if tr.get("segments"):
            factor = 1.0                  # each leg already carries its own rate
        if factor != 1.0:
            chain.append(f"setpts={factor:.6f}*PTS")
            # Interpolation is only for stretching; speeding up just drops frames.
            if factor >= 1.5:
                chain.append(f"minterpolate=fps={FPS}:mi_mode=blend")
            else:
                chain.append(f"fps={FPS}")
        else:
            chain.append(f"fps={FPS}")
        if hold:
            # Clone the final frame outward. No trim: the source was fitted exactly
            # to the moving part, so its real last frame is the one that holds.
            chain.append(f"tpad=stop_mode=clone:stop_duration={hold + 0.5}")
        elif tr.get("segments") or tr.get("fit"):
            # Resampling an exact fit between frame rates can land a few frames
            # short. Pad the tail rather than nudge the rate; the cut to `span`
            # removes the surplus.
            chain.append("tpad=stop_mode=clone:stop_duration=0.6")
        inp = ["-ss", f"{src_in}", "-i", str(path)]
        if tr.get("srcEnd") is not None:
            inp = ["-ss", f"{src_in}", "-t", f"{tr['srcEnd'] - src_in}", "-i", str(path)]
        if tr.get("segments"):
            inp = ["-i", str(path)]           # segments trim from the whole file
        print(f"{sid}: {src} @{src_in}s  avail {avail:.2f}s -> span {span:.2f}s  "
              f"slow {factor:.3f}x", flush=True)

    if tr.get("exposure") is not None or tr.get("saturation") is not None:
        e = tr.get("exposure", 0.0)
        sat = tr.get("saturation", 1.0)
        chain.append(f"eq=brightness={e}:saturation={sat}")
    if tr.get("fog"):
        chain.append(fog_filter(tr["fog"]))

    extra_inputs, post = [], []
    if tr.get("edgeSoften"):
        mask = edge_mask(str(REPO / "tmp/rejoice/edge-mask.png"), W, H)
        extra_inputs = ["-i", mask]
        post = [f"gblur=sigma={tr['edgeSoften']}"]

    vf = ",".join(chain)
    head = seg_src or "[0:v]"
    graph = (seg_pre + ";" if seg_pre else "") + f"{head}{vf}[v]"
    if post:
        graph = ((seg_pre + ";" if seg_pre else "")
                 + f"{head}{vf},split[ea][eb];"
                 f"[eb]{post[0]}[eblur];"
                 f"[1:v]format=gray,scale={W}:{H}[emask];"
                 f"[ea][emask]alphamerge[esharp];"
                 f"[eblur][esharp]overlay=format=auto[v]")
    cmd = ["ffmpeg", "-v", "error", "-y", *inp, *extra_inputs,
           "-filter_complex", graph, "-map", "[v]",
           "-t", f"{span}", "-r", str(FPS),
           "-c:v", "libx264", "-crf", "18", "-preset", "medium",
           "-pix_fmt", "yuv420p", "-an", str(dst)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        print(f"{sid}: FFMPEG FAILED\n{r.stderr[-900:]}")
        return False
    got = probe(dst)
    ok = got >= span - 0.05
    print(f"{sid}: wrote {dst.name}  {got:.2f}s (need {span:.2f}s) {'ok' if ok else 'SHORT'}",
          flush=True)
    return ok


if __name__ == "__main__":
    want = set(sys.argv[1:])
    rows = [s for s in SHOTS if not want or s[0] in want]
    results = {}
    for sid, src, src_in, start, end, move, tr in rows:
        results[sid] = build(sid, src, src_in, start, end, move, tr)
    bad = [k for k, v in results.items() if not v]
    print(f"\n{len(results) - len(bad)}/{len(results)} shots built")
    if bad:
        print("failed/missing:", " ".join(bad))
