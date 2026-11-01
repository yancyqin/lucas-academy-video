"""piece.py — one piece of the Mozart sketchbook as its own film segment (MOZART-SKETCHBOOK-PLAN.md).

    python piece.py KEY prepare     analyse every picture, write beats + plans + the film config
    python piece.py KEY render      render DATA/segments/KEY.mp4 (starts and ends on the empty desk)

Each piece: its pictures (pictures/m<KEY>-NN.png), its sections (sections/KEY.json from sections.py), one medium with
its tools, a desk lit for its time of day, a 2 s lead-in (the sheet arrives, the tool comes in), and after the music a
hold on the last picture and a dissolve back to the empty desk — so segments join seamlessly and also stand alone.
Twinkle (17) reuses the two approved crayon plans for the theme and Variation 1.
"""
import json, pathlib, subprocess, sys

DATA = pathlib.Path("/Users/yqin/repo/playground/lucas-academy-video-data/mozart-sketchbook")
TW = pathlib.Path("/Users/yqin/repo/playground/lucas-academy-video-data/twinkle-stars")
PY = "/Users/yqin/repo/playground/lucas-academy-video/.venv-reframe/bin/python"
HERE = pathlib.Path(__file__).parent
T = DATA / "tools"

def tool(name, length, tint): return {"png": str(T / f"{name}.png"), "len": length, "tint": tint}
CRAYON = {"png": str(TW / "pictures/crayon.png"), "len": 330, "tint": "body"}
PENCIL = tool("pencil", 330, "body")
GRAPHITE, SEPIA = [96, 96, 104], [118, 82, 52]

# medium: (analysis, film medium, crayon width ×, sketch colour, sketch tool, paint tool)
MEDIA = {
    "crayon":      ("outline", "crayon", 1.0, None, None, CRAYON),
    "marker":      ("outline", "crayon", 1.0, None, None, tool("marker", 330, "body")),
    "oilpastel":   ("outline", "crayon", 1.2, None, None, CRAYON),
    "pencil":      ("picture", "pencil", 1.0, None, None, PENCIL),
    "ink":         ("picture", "ink", 1.4, None, None, tool("brush-chinese", 430, "tip")),
    "penwash":     ("picture", "watercolour", 1.4, None, tool("pen", 330, "none"), tool("brush-round", 430, "tip")),
    "watercolour": ("sketch", "watercolour", 1.4, GRAPHITE, PENCIL, tool("brush-round", 430, "tip")),
    "gouache":     ("sketch", "gouache", 1.6, GRAPHITE, PENCIL, tool("brush-flat", 430, "tip")),
    "oil":         ("sketch", "oil", 1.9, SEPIA, None, tool("brush-flat", 430, "tip")),
    "pastel":      ("sketch", "pastel", 1.5, [140, 130, 120], None, tool("pastel", 300, "body")),
}
# key: (medium, desk, gain dB, marks gap s)
PIECES = {
    "05": ("marker", "desk-morning", -2.5, 0.3), "20": ("watercolour", "desk-morning", 6.0, 0.3),
    "06": ("gouache", "desk-day", -4.4, 0.3), "10": ("oilpastel", "desk-day", -0.3, 0.3),
    "16": ("pencil", "desk-day", 2.3, 0.3), "01": ("oil", "desk-evening", -1.7, 0.3),
    "27": ("penwash", "desk-evening", 1.8, 0.3), "17": ("crayon", "desk", 2.5, 0.3),
    "15": ("pastel", "desk", 0.0, 0.6), "07": ("ink", "desk", 4.3, 0.6),
}
LEAD, OUTRO = 2.0, (1.5, 0.8)


def desk_path(name):
    p = T / f"{name}.png"
    return str(p if p.exists() else TW / "pictures/desk.png")


def pictures(key):
    if key == "17":
        return [TW / "pictures/p00-theme.png", TW / "pictures/p01-v1.png"] + [DATA / f"pictures/m17-{n:02d}.png" for n in range(2, 13)]
    return sorted(DATA.glob(f"pictures/m{key}-[0-9][0-9].png"))


def prepare(key):
    medium, desk, gain, gap = PIECES[key]
    kind, film_medium, wmul, sketch, sketch_tool, paint_tool = MEDIA[medium]
    sec = json.load(open(DATA / f"sections/{key}.json"))["sections"]
    pics = pictures(key)
    assert len(pics) == len(sec), f"{key}: {len(pics)} pictures for {len(sec)} sections"
    out = DATA / f"pieces/{key}"; out.mkdir(parents=True, exist_ok=True)
    sections = []
    for n, (pic, s) in enumerate(zip(pics, sec), 1):
        npz = DATA / f"analysis/{pic.stem}.npz"
        if not npz.exists():
            if kind == "outline":
                subprocess.run([PY, str(HERE / "crayon.py"), "analyze", str(pic), str(npz)], check=True)
            else:
                subprocess.run([PY, str(HERE / "paint.py"), str(pic), str(npz), "--lines", kind], check=True)
        if key == "17" and n <= 2:                                   # the approved theme and Variation 1
            plan = TW / f"sample/plan-{'theme' if n == 1 else 'v1'}.json"
            npz = TW / f"analysis/{pic.stem}.npz"
        else:
            beats = out / f"beats-{n:02d}.json"; plan = out / f"plan-{n:02d}.json"
            json.dump({"beats": s["beats"], "cadence": s["cadence"]}, open(beats, "w"))
            def try_plan(split, w):
                r = subprocess.run([PY, str(HERE / "crayon.py"), "plan", str(npz), str(beats), str(plan), "--start", str(s["start"]),
                                    "--end", str(s["end"]), "--wmul", f"{w:.2f}", "--split", str(split)], check=True, capture_output=True, text=True)
                sp = [l for l in r.stdout.splitlines() if l.startswith("speeds:")][0].split()
                return float(sp[3]), float(sp[6])                    # line p95, fill p95
            # the outline/colour split whose faster half is slowest, measured on the real paths; then widen if still fast
            best = min(range(1, 5), key=lambda k: max(try_plan(k, wmul)))
            w = wmul
            for attempt in range(6):
                line_v, fill_v = try_plan(best, w)
                if fill_v <= 2600 or attempt == 5: break
                w *= 1.3
            rush, speed = line_v / 2600, max(line_v, fill_v)
            print(f"  {key}-{n:02d}: outlines to phrase {best}/6, brush ×{w:.2f}, fastest strokes {line_v:.0f} (lines) / {fill_v:.0f} (colour) px/s")
        sec_cfg = {"id": f"{key}-{n:02d}", "picture": str(pic), "npz": str(npz), "plan": str(plan), "medium": film_medium,
                   "tool": paint_tool}
        if sketch: sec_cfg["sketch_color"] = sketch
        if sketch_tool: sec_cfg["tool_lines"] = sketch_tool
        sections.append(sec_cfg)
    music = TW / "music/k265-renzi.wav" if key == "17" else DATA / f"music/{key}.wav"
    cfg = {"desk": desk_path(desk), "crayon": CRAYON["png"], "music": str(music), "lead_in": LEAD, "approach": 2.2, "slide": 0.9,
           "outro": list(OUTRO), "fade_out": 0.6,
           "audio_filter": f"volume={gain}dB,alimiter=limit=0.84:attack=5:release=60:level=disabled", "sections": sections}
    json.dump(cfg, open(out / "config.json", "w"), indent=1)
    end = sec[-1]["end"] + LEAD + OUTRO[0] + OUTRO[1] + 0.3
    json.dump({"to": round(end, 2)}, open(out / "render.json", "w"))
    print(f"{key}: {len(sections)} pictures, {medium}, render to {end:.1f} s")


def render(key):
    out = DATA / f"pieces/{key}"; seg = DATA / "segments"; seg.mkdir(exist_ok=True)
    to = json.load(open(out / "render.json"))["to"]
    cfg = json.load(open(out / "config.json"))                   # the desk for its time of day, if it exists by now
    cfg["desk"] = desk_path(PIECES[key][1]); json.dump(cfg, open(out / "config.json", "w"), indent=1)
    subprocess.run([PY, str(HERE / "film.py"), str(out / "config.json"), str(seg / f"{key}.mp4"), "--from", "0", "--to", str(to),
                    "--preview", "15"], check=True)


if __name__ == "__main__":
    key, what = sys.argv[1], sys.argv[2]
    prepare(key) if what == "prepare" else render(key)
