"""Stage the pictures 「怎么骗过 AI：面包还是狗？」 shows into public/bread-or-dog/ (JPEG, at most 1920 px wide).

  python3 scripts/bread-or-dog/assets.py      (system python is fine: it only calls sips)

Every picture is one the models actually saw (or the cake's cut-open edit and the noise picture made for the film), from
lucas-academy-video-data/bread-or-dog/. The noise picture is shown ×25 (adv_viz); the attacked picture itself is copied
as PNG so the noise survives.
"""
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = next(p / "lucas-academy-video-data" for p in ROOT.parents if (p / "lucas-academy-video-data").is_dir()) / "bread-or-dog"
PUB = ROOT / "public/bread-or-dog"

PICS = {
    # intro: dogs and breads that look alike (round 1, Pexels)
    "dog-shiba.jpg": "test/img02.jpg", "bread-boule.jpg": "test/img01.jpg", "dog-dachshund.jpg": "test/img06.jpg",
    "bread-sourdough.jpg": "test/img05.jpg", "dog-fluffy.jpg": "test/img10.jpg", "bread-brioche.jpg": "test/img04.jpg",
    "dog-corgi.jpg": "test/img03.jpg", "bread-rolls.jpg": "test/img09.jpg",
    # trick 2: the puppy on the baking tray (Codex) shown to LLaVA
    "tray-puppy.jpg": "test/img19.jpg",
    # trick 3: noise against ResNet-50 (448 px crops)
    "noise-clean.png": "round2/test/adv0a.png", "noise-x25.png": "round2/adv_viz/adv1_noise.png", "noise-attacked.png": "round2/test/adv1.png",
    # trick 4: the BREAD note
    "note-bread.jpg": "test/img16.jpg",
    # v0.4 opening: it used to be hard (our own look-alike grid and photos; the CC BY 4.0 cat with elephant skin from
    # Geirhos et al.'s texture-vs-shape repo, which our own ResNet-50 calls "Indian elephant")
    "lookalike-grid.jpg": "round2/test/g5.jpg", "muffins.jpg": "test/img08.jpg", "chihuahua.jpg": "test/img07.jpg",
    "cat-elephant.png": "history/geirhos-stimuli/cat2-elephant1.png",
    "texture-fur.jpg": "film-pics/texture-fur.jpg", "texture-crust.jpg": "film-pics/texture-crust.jpg",
    # v0.4 trick 1: the Muse first frame (16:9 redraw of k1, tested again) and the end reference (stand-in until the clip)
    "cake-dog-16x9.jpg": "muse/frames/M01_first.png", "cake-end.jpg": "muse/frames/M01_end_a.png",
    # v0.4 ending: a wall of pictures for "hundreds of millions of pictures with captions"
    "data-wall.jpg": "film-pics/data-wall.jpg",
}


def main():
    PUB.mkdir(parents=True, exist_ok=True)
    for name, src in PICS.items():
        dst = PUB / name
        if name.endswith(".png"):
            shutil.copy(DATA / src, dst)
        else:
            subprocess.run(["sips", "-s", "format", "jpeg", "-s", "formatOptions", "92", "-Z", "1920", str(DATA / src),
                            "--out", str(dst)], check=True, capture_output=True)
        print(name, "<-", src)


if __name__ == "__main__":
    main()
