"""Cover pictures for 「Challenge: Which Butterflies Are Real?」 made whole by Codex image generation, title included.

    /Users/yqin/repo/playground/lucas-academy-video/.venv-align/bin/python scripts/butterfly-challenge/cover_images.py [name ...] [--force]

As for 「动物想什么？AI 知道吗？」 (scripts/ai-animal-mind/cover_images.py; Yancy 2026-11-11: HTML type over a frame was
「太丑」, Codex thumbnails with the lettering in were picked): Codex designs the whole thumbnail, every result is
checked letter by letter before it is shown. English first, because English is the film's default track (Yancy
2026-11-12); a zh version of the chosen one is the same picture with the Chinese title, made with the en cover attached.
README "YouTube covers": a question, huge, two lines, one or two accent words, one strong realistic picture, no other text.

Writes lucas-academy-video-data/butterfly-challenge/covers/gen/<name>.png and covers/<name>.jpg (1280x720).
"""
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
DATA = next(p / "lucas-academy-video-data" for p in ROOT.parents if (p / "lucas-academy-video-data").is_dir())
GEN = DATA / "butterfly-challenge/covers/gen"
OUT = DATA / "butterfly-challenge/covers"

TYPE = ("The title is part of the design: huge, bold, clean modern sans-serif lettering that is easy to read on a phone, "
        "white with a soft shadow, the accent word in the colour given; set in the open part of the picture so it never "
        "covers a butterfly. Exactly the title and nothing else: no logo, no small print, no watermark, no labels, no "
        "other letters, numbers or signs anywhere. Spell the title exactly as given, every letter correct. ")
STYLE = ("A YouTube thumbnail for an educational nature video for parents and curious kids, 16:9 landscape, the largest "
         "native size. Photorealistic macro photography, natural vivid colours, soft natural light, uncluttered; not a "
         "cartoon, not an illustration. ")

COVERS = {  # name: (title, subject)
    "cover-a-two-butterflies.en": (
        'two lines: "Which One" and "Is Real?", with the word Real in fresh leaf green',
        "Two European peacock butterflies, wings open, one on the left and its near twin on the right, each "
        "resting on its own flower, facing each other across the frame, both sharp and beautiful, so the viewer cannot "
        "tell which is the real one; dark green softly blurred background; the title across the upper middle."),
    "cover-b-glasswing.en": (
        'two lines: "Real" and "or AI?", with the letters AI in warm amber orange',
        "A glasswing butterfly with clear, see-through wings resting on a bright red zinnia, extreme macro, the flower "
        "showing through its transparent wings; dark green softly blurred background on the right for the title."),
    "cover-c-magnifier.en": (
        'two lines: "Which Butterfly" and "Is Real?", with the word Real in fresh leaf green',
        "A hand-held magnifying glass, seen from the side, hovering over a bright orange and black butterfly on a leaf; "
        "inside the lens the butterfly's wing scales look like tiny tiles, crisp and real; no hand visible, only the "
        "glass and its handle; dark green softly blurred background with room for the title."),
}


# Chinese versions (README "YouTube covers": one language per cover, same accent colour for the same word): the same
# picture with the title replaced, made by editing the English cover. Yancy 11-12: 「封面都放包里我看看」.
ZH = {
    "cover-a-two-butterflies.zh": ("cover-a-two-butterflies.en", "第一行「哪一只」，第二行「是真的？」，「真的」两个字用和原图 Real 一样的嫩绿色"),
    "cover-b-glasswing.zh": ("cover-b-glasswing.en", "第一行「真的」，第二行「还是AI？」，「AI」用和原图一样的暖琥珀橙色"),
    "cover-c-magnifier.zh": ("cover-c-magnifier.en", "第一行「哪只蝴蝶」，第二行「是真的？」，「真的」两个字用和原图 Real 一样的嫩绿色"),
}


def prompt(name: str) -> str:
    if name in ZH:
        return ("Edit the attached thumbnail: keep the picture exactly as it is (same butterflies, composition, light and "
                f"colours) and replace its English title with a Chinese title, {ZH[name][1]}, in the same place, the same "
                "huge bold clean sans-serif style (a heavy Chinese sans like PingFang Heavy), white with a soft shadow. "
                "Exactly that title and nothing else: no English, no other characters, no logo, no watermark. Every "
                "Chinese character must be correct. 16:9 landscape, the largest native size.")
    title, subject = COVERS[name]
    return STYLE + subject + f" Title text, {title}. " + TYPE


def generate(name: str) -> str:
    task = (f"This is an automated run and nobody can answer questions. Use your image generation tool to make ONE "
            f"image, then copy the generated file into the current directory as {name}.png and reply with its absolute "
            f"path and pixel size.\n\n{prompt(name)}")
    cmd = ["codex", "exec", "--skip-git-repo-check", "-s", "workspace-write", "-C", str(GEN), "--enable",
           "image_generation", "-c", 'model_reasoning_effort="medium"', "-o", str(GEN / f"{name}.last.md")]
    if name in ZH:  # the English cover to edit
        cmd += ["-i", str(GEN / f"{ZH[name][0]}.png")]
        task = task.replace("make ONE image,", "make ONE image by editing the attached image as described,")
    cmd += ["-"]
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


def main() -> None:
    args = sys.argv[1:]
    names = [a for a in args if a != "--force"] or list(COVERS) + list(ZH)
    GEN.mkdir(parents=True, exist_ok=True)
    todo = [n for n in names if "--force" in args or not (GEN / f"{n}.png").is_file()]
    with ThreadPoolExecutor(3) as pool:
        for line in pool.map(generate, todo):
            print(line, flush=True)


if __name__ == "__main__":
    main()
