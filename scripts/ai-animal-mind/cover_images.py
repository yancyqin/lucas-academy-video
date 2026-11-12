"""Cover pictures for 「动物想什么？AI 知道吗？」 made whole by Codex image generation, title included.

    /Users/yqin/repo/playground/lucas-academy-video/.venv-align/bin/python scripts/ai-animal-mind/cover_images.py [name ...] [--force]

Yancy 2026-11-11: 「标题改为：动物想什么？AI知道吗」 and 「封面不太好，你可以换封面，让codex image gen 生成一下，给我3个」
(after an HTML title over the G10 frame was 「太丑」). So Codex designs the whole thumbnail, picture and lettering
together; every result is checked character by character before it is shown. The zh covers come first; an en version
is the same picture with the English title (made with the zh cover attached as the reference).

Writes lucas-academy-video-data/ai-animal-mind/covers/gen/<name>.png (Codex's size) and covers/<name>.jpg (1280×720),
and records each in docs/ai-animal-mind/generated-assets.json under "covers".
"""
import hashlib
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
DATA = next(p / "lucas-academy-video-data" for p in ROOT.parents if (p / "lucas-academy-video-data").is_dir())
GEN = DATA / "ai-animal-mind/covers/gen"
OUT = DATA / "ai-animal-mind/covers"
RECORD = ROOT / "docs/ai-animal-mind/generated-assets.json"

ZH = "第一行「动物想什么？」，第二行「AI 知道吗？」"
EN = 'line one "What Are Animals Thinking?", line two "Does AI Know?"'
TYPE = ("The title is part of the design: huge, bold, clean modern lettering that is easy to read on a phone, white with "
        "a soft shadow, the word AI picked out in one tasteful accent colour that suits the picture; set in the open "
        "part of the picture so it never covers the animal's face. Exactly two lines of text and nothing else: no logo, "
        "no small print, no watermark, no other letters, numbers or signs anywhere. Spell the title exactly as given, "
        "every character correct. ")
STYLE = ("A YouTube thumbnail for an educational science video for parents and curious kids, 16:9 landscape, the "
         "largest native size. Photorealistic, natural colours, cinematic light, one strong subject, uncluttered; not a "
         "cartoon, not an illustration. ")

COVERS = {  # name: (language, subject, reference cover or None)
    "cover-a-sunset-monkey.zh": ("zh", "A wild monkey sits on a rock on a hilltop, seen from behind and a little to the "
                                 "side, quietly watching a huge glowing orange sun setting over a calm lake; warm rim "
                                 "light on its fur; a wide, calm sky.", None),
    "cover-b-monkey-face.zh": ("zh", "A close portrait of a thoughtful macaque monkey in warm evening light, its eyes "
                               "looking off into the distance, as if wondering; beside its head, very faint thin glowing "
                               "lines like sound waves drift in the air, subtle and elegant, hinting at AI listening; a "
                               "dark, softly blurred background.", None),
    "cover-c-dolphin.zh": ("zh", "Underwater in clear blue sea with sunbeams: an Atlantic spotted dolphin swims toward "
                           "the camera, curious and close, its spotted skin sharp; faint thin rings of light ripple out "
                           "from its head like sound waves, subtle and realistic; deep blue open water above.", None),
    # Yancy 11-11, after picking B: 「再做另外一版，用G10那个女人，上半身 在水里 做一个惊讶的表情，旁边有海豚，用C的配色」
    "cover-d-surprised-swimmer.zh": ("zh", "Use the two attached images as references. Image 1 shows the woman: keep her "
                                     "the same person (face, long dark hair, red bikini). Image 2 shows the colour scheme "
                                     "and title style to match: deep blue sea with sunbeams from above, a bold white title "
                                     "with the word AI in the same bright cyan. The new picture: underwater, the same "
                                     "young woman seen from the waist up, turned toward the camera, with a surprised, "
                                     "delighted expression (eyebrows raised, eyes wide, mouth a little open), as if the "
                                     "dolphin had just told her something; her hair floating; no mask, no goggles, no "
                                     "snorkel. An Atlantic spotted dolphin is right beside her face, looking at her "
                                     "curiously, its spotted skin sharp. Deep blue open water above for the title.", None),
    "cover-a-sunset-monkey.en": ("en", None, "cover-a-sunset-monkey.zh"),
    "cover-b-monkey-face.en": ("en", None, "cover-b-monkey-face.zh"),
    "cover-c-dolphin.en": ("en", None, "cover-c-dolphin.zh"),
    "cover-d-surprised-swimmer.en": ("en", None, "cover-d-surprised-swimmer.zh"),
}
REFS = {  # name: pictures attached as references for a new design (not edited)
    "cover-d-surprised-swimmer.zh": [DATA / "ai-animal-mind/references/G10-dolphin-scarf.png", GEN / "cover-c-dolphin.zh.png"],
}


def png_size(path: Path) -> list[int]:
    with Image.open(path) as im:
        return list(im.size)


def prompt(name: str) -> str:
    lang, subject, ref = COVERS[name]
    title = ZH if lang == "zh" else EN
    if ref:
        return (f"Edit the attached thumbnail: keep the picture exactly as it is (same subject, composition, light and "
                f"colours) and replace its title with the English title, {title}, in the same style, size and place. "
                + TYPE + "16:9 landscape, the largest native size.")
    return STYLE + subject + f" Title text: {title}. " + TYPE


def generate(name: str) -> str:
    ref, looks = COVERS[name][2], REFS.get(name, [])
    how = ", editing the attached image as described" if ref else ", using the attached images as described" if looks else ""
    task = (f"This is an automated run and nobody can answer questions. Use your image generation tool to make ONE "
            f"image{how}, then copy the generated file into the current directory as {name}.png and reply with its "
            f"absolute path and pixel size.\n\n{prompt(name)}")
    cmd = ["codex", "exec", "--skip-git-repo-check", "-s", "workspace-write", "-C", str(GEN), "--enable",
           "image_generation", "-c", 'model_reasoning_effort="medium"', "-o", str(GEN / f"{name}.last.md")]
    if ref:
        cmd += ["-i", str(GEN / f"{ref}.png")]
    for look in looks:
        cmd += ["-i", str(look)]
    run = subprocess.run(cmd + ["-"], input=task, capture_output=True, text=True)
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


def record() -> None:
    data = json.loads(RECORD.read_text()) if RECORD.exists() else {"assets": []}
    old = {a["path"]: a for a in data.get("covers", [])}
    covers = []
    for name in COVERS:
        path = GEN / f"{name}.png"
        if not path.is_file():
            continue
        raw = path.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        prev = old.get(f"covers/gen/{name}.png", {})
        covers.append({"path": f"covers/gen/{name}.png", "tool": "codex exec · image_generation",
                       "created": prev.get("created") if prev.get("sha256") == digest else date.today().isoformat(),
                       "intent": prompt(name), "dimensions": png_size(path), "sha256": digest, "bytes": len(raw)})
    data["covers"] = covers
    RECORD.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def main() -> None:
    args = sys.argv[1:]
    names = [a for a in args if a != "--force"] or list(COVERS)
    assert not set(names) - set(COVERS), f"unknown covers: {set(names) - set(COVERS)}"
    GEN.mkdir(parents=True, exist_ok=True)
    todo = [n for n in names if "--force" in args or not (GEN / f"{n}.png").is_file()]
    for n in todo:
        (GEN / f"{n}.png").unlink(missing_ok=True)
    with ThreadPoolExecutor(3) as pool:
        for line in pool.map(generate, todo):
            print(line, flush=True)
    record()


if __name__ == "__main__":
    main()
