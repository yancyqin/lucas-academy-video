"""Build one test picture per medium for the Mozart sketchbook: beats from sections.py, plan, film config.

    python sample_media.py KEY      (20 watercolour, 01 oil, 07 ink, 16 pencil) -> DATA/samples/KEY/{beats,plan,config}.json
"""
import json, pathlib, subprocess, sys

DATA = pathlib.Path("/Users/yqin/repo/playground/lucas-academy-video-data/mozart-sketchbook")
TW = pathlib.Path("/Users/yqin/repo/playground/lucas-academy-video-data/twinkle-stars")
PY = "/Users/yqin/repo/playground/lucas-academy-video/.venv-reframe/bin/python"
HERE = pathlib.Path(__file__).parent
SAMPLES = {   # picture, medium, tool (png, length, tint), sketch colour, crayon width ×, gain (dB)
    "20": ("m20-1-watercolour", "watercolour", ("brush-round", 430, "tip"), [96, 96, 104], 1.4, 4.8),
    "01": ("m01-1-oil", "oil", ("brush-flat", 430, "tip"), [118, 82, 52], 1.9, -1.0),
    "07": ("m07-1-inkcolour", "ink", ("brush-chinese", 430, "tip"), [40, 38, 42], 1.4, 5.2),
    "16": ("m16-1-colourpencil", "pencil", ("pencil", 330, "body"), [60, 50, 45], 1.0, 2.8),
}


def main():
    k = sys.argv[1]; pic, medium, (tool, tlen, tint), sketch, wmul, gain = SAMPLES[k]
    sec = json.load(open(DATA / f"sections/{k}.json"))["sections"][0]
    out = DATA / f"samples/{k}"; out.mkdir(parents=True, exist_ok=True)
    json.dump({"beats": sec["beats"], "cadence": sec["cadence"]}, open(out / "beats.json", "w"))
    subprocess.run([PY, str(HERE / "crayon.py"), "plan", str(DATA / f"analysis/{pic}.npz"), str(out / "beats.json"), str(out / "plan.json"),
                    "--start", str(sec["start"]), "--end", str(sec["end"]), "--wmul", str(wmul)], check=True)
    cfg = {"desk": str(TW / "pictures/desk.png"), "crayon": str(TW / "pictures/crayon.png"), "music": str(DATA / f"music/{k}.wav"),
           "audio_filter": f"volume={gain}dB,alimiter=limit=0.84:attack=5:release=60:level=disabled", "fade_out": 1.2, "lead_in": 3.0,
           "sections": [{"id": k, "picture": str(DATA / f"pictures/{pic}.png"), "npz": str(DATA / f"analysis/{pic}.npz"),
                         "plan": str(out / "plan.json"), "medium": medium, "sketch_color": sketch,
                         "tool": {"png": str(DATA / f"tools/{tool}.png"), "len": tlen, "tint": tint}}]}
    json.dump(cfg, open(out / "config.json", "w"), indent=1)
    print(k, medium, "section", sec["start"], "→", sec["end"], "; render to", round(sec["end"] + 3.0 + 0.6, 1))


if __name__ == "__main__":
    main()
