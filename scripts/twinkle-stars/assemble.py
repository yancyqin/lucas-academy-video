"""assemble.py — join the Mozart sketchbook segments into one film, with a short quiet gap between pieces.

    python assemble.py OUT.mp4 [--gap 1.0]

Order (morning → night): 05 20 06 10 16 01 27 17 15 07. Every segment starts and ends on its own empty desk; between two
pieces a silent clip crossfades one desk's light into the next (one dissolve clip per boundary, then one concat — chained
xfade filters corrupt timestamps). Writes OUT.chapters.json with each piece's start time in the film.
"""
import argparse, json, pathlib, subprocess, tempfile

DATA = pathlib.Path("/Users/yqin/repo/playground/lucas-academy-video-data/mozart-sketchbook")
ORDER = ["05", "20", "06", "10", "16", "01", "27", "17", "15", "07"]
NAMES = {"05": ("《费加罗的婚礼》序曲", "The Marriage of Figaro, Overture"), "20": ("嬉游曲 K.138 · 第一乐章", "Divertimento K. 138, I"),
         "06": ("《魔笛》序曲", "The Magic Flute, Overture"), "10": ("《大组曲》· 终曲", "Gran Partita, VII. Finale"),
         "16": ("单簧管协奏曲 · 回旋曲", "Clarinet Concerto, III. Rondo"), "01": ("第40号交响曲 · 第一乐章", "Symphony No. 40, I"),
         "27": ("《弦乐小夜曲》（手风琴版）", "Eine kleine Nachtmusik (accordions)"), "17": ("《小星星变奏曲》", "Twinkle Variations, K. 265"),
         "15": ("单簧管协奏曲 · 柔板", "Clarinet Concerto, II. Adagio"), "07": ("《大组曲》· 柔板", "Gran Partita, III. Adagio")}


def probe(p):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
                                capture_output=True, text=True).stdout)


def first_frame(p, out):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(p), "-frames:v", "1", str(out)], check=True)


def last_frame(p, out):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-sseof", "-1", "-i", str(p), "-update", "1", str(out)], check=True)


def piece_files(key):
    """A piece's segment, plus its ending (hold, then the empty desk) when that was made separately."""
    seg = DATA / f"segments/{key}.mp4"; tail = DATA / f"segments/{key}.tail.mp4"
    return [seg, tail] if tail.exists() else [seg]


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("out"); ap.add_argument("--gap", type=float, default=1.0)
    a = ap.parse_args()
    pieces = [piece_files(k) for k in ORDER]
    missing = [f.name for fs in pieces for f in fs if not f.exists()]; assert not missing, f"missing segments: {missing}"
    enc = ["-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p", "-r", "30",
           "-c:a", "aac", "-b:a", "256k", "-ar", "44100", "-ac", "2"]
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp); parts = []; chapters = []; t = 0.0
        for i, fs in enumerate(pieces):
            chapters.append({"key": ORDER[i], "t": round(t, 2), "zh": NAMES[ORDER[i]][0], "en": NAMES[ORDER[i]][1]})
            for f in fs: parts.append(f); t += probe(f)
            if i + 1 < len(pieces):                              # the desk's light changes, quietly
                a_png, b_png, clip = tmp / f"a{i}.png", tmp / f"b{i}.png", tmp / f"gap{i}.mp4"
                last_frame(fs[-1], a_png); first_frame(pieces[i + 1][0], b_png)
                subprocess.run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-t", str(a.gap), "-i", str(a_png), "-loop", "1", "-t", str(a.gap),
                                "-i", str(b_png), "-f", "lavfi", "-t", str(a.gap), "-i", "anullsrc=r=44100:cl=stereo",
                                "-filter_complex", f"[0:v][1:v]blend=all_expr='A*(1-T/{a.gap})+B*(T/{a.gap})',format=yuv420p[v]",
                                "-map", "[v]", "-map", "2:a", *enc, "-shortest", str(clip)], check=True)
                parts.append(clip); t += a.gap
        inputs = [x for p in parts for x in ("-i", str(p))]      # the concat filter decodes every part (safe across encoders)
        graph = "".join(f"[{i}:v:0]setsar=1,fps=30,format=yuv420p[v{i}];[{i}:a:0]aresample=44100,aformat=channel_layouts=stereo[a{i}];"
                        for i in range(len(parts)))
        graph += "".join(f"[v{i}][a{i}]" for i in range(len(parts))) + f"concat=n={len(parts)}:v=1:a=1[v][a]"
        subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", graph, "-map", "[v]", "-map", "[a]", *enc,
                        "-movflags", "+faststart", a.out], check=True)
    json.dump(chapters, open(a.out.replace(".mp4", ".chapters.json"), "w"), ensure_ascii=False, indent=1)
    d = probe(a.out)
    print(f"wrote {a.out}: {int(d // 60)}:{d % 60:04.1f}")
    for c in chapters: print(f"  {int(c['t'] // 60)}:{int(c['t'] % 60):02d} {c['zh']}")


if __name__ == "__main__":
    main()
