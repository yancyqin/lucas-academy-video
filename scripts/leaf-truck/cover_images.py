"""Cover thumbnails for 「一片落叶，为什么让卡车急刹车？」, drawn whole by Codex image generation, title included.

    python3 scripts/leaf-truck/cover_images.py [name ...] [--force]

Same method as scripts/ai-animal-mind/cover_images.py (Yancy 11-11: Codex designs the whole thumbnail; HTML type over
a frame was 「太丑」). The zh covers come first; each en cover is the zh picture with the English title.
Writes lucas-academy-video-data/leaf-truck/covers/gen/<name>.png (Codex's size) and covers/<name>.jpg (1280×720).
"""
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PIL import Image

REPO = Path(__file__).resolve().parents[2]
DATA = Path("/Users/yqin/repo/playground/lucas-academy-video-data/leaf-truck")
GEN, OUT = DATA / "covers/gen", DATA / "covers"
REFS = REPO / "out/leaf-truck/muse-refs"

ZH = "第一行「一片落叶」，第二行「为什么让卡车急刹？」"
EN = 'line one "Why Did a Leaf", line two "Stop a Truck?"'
TYPE = ("The title is part of the design: huge, bold, clean modern sans-serif lettering that is easy to read on a phone, "
        "white with a soft shadow, the word for leaf (落叶 / Leaf) picked out in one warm autumn-orange accent colour; set "
        "in the open part of the picture so it never covers the truck or the leaves. Exactly two lines of text and "
        "nothing else: no logo, no small print, no watermark, no other letters, numbers or signs anywhere (the truck "
        "has no logo and a blank number plate). Spell the title exactly as given, every character correct. ")
STYLE = ("A YouTube thumbnail for an educational video for parents and curious kids about how a driverless truck "
         "thinks, 16:9 landscape, the largest native size. Photorealistic, natural colours, cinematic light, one strong "
         "subject, uncluttered; not a cartoon, not an illustration. The truck must look like the attached reference: an "
         "unbranded white box truck (a van cab with a square white cargo box), nobody in the cab. ")

COVERS = {  # name: (language, subject, zh cover it is edited from, truck reference)
    "cover-a-leaves.zh": ("zh", "Camera low at road level on a wet autumn road, overcast: three or four bright orange "
                          "fallen leaves lie sharp in the lower foreground; a few metres behind them the white truck "
                          "has stopped, facing us, headlights on, slightly soft in focus. Autumn trees and a calm grey "
                          "sky fill the upper part of the picture, where the title goes.", None, REFS / "G2.png"),
    "cover-b-brake.zh": ("zh", "A quiet autumn street in a small town, three-quarter side view: the white truck has just "
                         "stopped hard, its front a short gap before a swirl of orange leaves blowing across its lane; "
                         "leaves in the air, wet asphalt, soft overcast light. Open sky and trees above the truck for the "
                         "title.", None, REFS / "input/truck.jpg"),
    "cover-a-leaves.en": ("en", None, "cover-a-leaves.zh", None),
    "cover-b-brake.en": ("en", None, "cover-b-brake.zh", None),
}


def prompt(name):
    lang, subject, ref, _ = COVERS[name]
    title = ZH if lang == "zh" else EN
    if ref:
        return (f"Edit the attached thumbnail: keep the picture exactly as it is (same subject, composition, light and "
                f"colours) and replace its title with the English title, {title}, in the same style, size and place. "
                + TYPE + "16:9 landscape, the largest native size.")
    return STYLE + subject + f" Title text: {title}. " + TYPE


def generate(name):
    _, _, ref, look = COVERS[name]
    how = ", editing the attached image as described" if ref else ", using the attached truck picture as the look reference"
    task = (f"This is an automated run and nobody can answer questions. Use your image generation tool to make ONE "
            f"image{how}, then copy the generated file into the current directory as {name}.png and reply with its "
            f"absolute path and pixel size.\n\n{prompt(name)}")
    cmd = ["codex", "exec", "--skip-git-repo-check", "-s", "workspace-write", "-C", str(GEN), "--enable",
           "image_generation", "-c", 'model_reasoning_effort="medium"', "-o", str(GEN / f"{name}.last.md"),
           "-i", str(GEN / f"{ref}.png" if ref else look), "-"]
    run = subprocess.run(cmd, input=task, capture_output=True, text=True)
    png = GEN / f"{name}.png"
    if not png.is_file():
        return f"{name}: FAILED\n{run.stdout[-600:]}\n{run.stderr[-600:]}"
    with Image.open(png) as im:
        w, h = im.size
        ch = round(w * 9 / 16)
        box = (0, (h - ch) // 2, w, (h - ch) // 2 + ch) if ch <= h else ((w - round(h * 16 / 9)) // 2, 0,
                                                                         (w + round(h * 16 / 9)) // 2, h)
        im.convert("RGB").crop(box).resize((1280, 720), Image.LANCZOS).save(OUT / f"{name}.jpg", quality=92)
    return f"{name}: ok {w}x{h}"


def main():
    args = sys.argv[1:]
    names = [a for a in args if a != "--force"] or list(COVERS)
    GEN.mkdir(parents=True, exist_ok=True)
    todo = [n for n in names if "--force" in args or not (GEN / f"{n}.png").is_file()]
    for n in todo:
        (GEN / f"{n}.png").unlink(missing_ok=True)
    zh = [n for n in todo if COVERS[n][0] == "zh"]
    en = [n for n in todo if COVERS[n][0] == "en"]
    with ThreadPoolExecutor(3) as pool:
        for batch in (zh, en):   # an en cover is edited from its zh cover, so zh first
            for line in pool.map(generate, batch):
                print(line, flush=True)


if __name__ == "__main__":
    main()
