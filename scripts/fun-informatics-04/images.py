"""Generate the reference frames for the Muse clips with Codex image generation (FUN-INFORMATICS-04.md §5).

    python3 scripts/fun-informatics-04/images.py [name ...] [--force]

Yancy generates the short videos in Muse (2026-11-01); these photographs are the first frames to start them from,
so the dish in G1 and G2 is the same dish. Nothing in them carries text, labels or logos.

Writes public/fun-informatics-04/references/<name>.png (gitignored) and records each one in
docs/fun-informatics-04/generated-assets.json (tool, intent, size, sha256, label "AI 生成"), like episode 3.
A picture that names another as its reference runs after it and gets it attached with -i. Three run at once.
"""
import hashlib
import json
import struct
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "public/fun-informatics-04/references"
RECORD = ROOT / "docs/fun-informatics-04/generated-assets.json"

TAIL = (" Realistic photograph, not an illustration. No people, no hands, no text, letters, numbers, labels or logos "
        "anywhere. Landscape 16:9, the largest native size, no software upscale.")

# name: (where it is used, reference picture or None, subject)
IMAGES = {
    "dish-green": ("S01 / G1 首帧", None,
                   "Top-down view of a shallow round clear glass dish, like a petri dish about ten centimetres wide, "
                   "filled with water that has a faint, even, pale-green tint from microscopic algae. It sits in the "
                   "middle of a plain matte white table, with plenty of empty table around it. Soft, even daylight and "
                   "a gentle soft shadow under the dish; clean and calm."),
    "dish-beam": ("S03 / S47 / G2 首帧", "dish-green",
                  "The same glass dish of pale-green water as in the attached reference picture, from the same "
                  "top-down camera, but the room is now dim. A small black flashlight lies on the table at the left "
                  "edge of the frame, pointing at the dish; its narrow warm-white beam lights the left side of the "
                  "dish. The green tint is still even across the whole dish: the algae have not moved yet."),
    "goggles": ("S36 / G3 首帧", None,
                "A pair of research goggles resting on a clean white table, three-quarter view. The front frame is "
                "matte dark grey with one small round camera lens in the centre, between the eyes; a faint amber glow "
                "shows from inside the lenses. Soft studio light, shallow depth of field, a quiet product shot of a "
                "medical research device."),
    "notebook-table": ("S39 / G5 首帧", None,
                       "A plain closed notebook with a dark blue cover and a small white cardboard box, side by side "
                       "with a gap between them, on a plain white table, seen from about 45 degrees above. Soft "
                       "daylight from the left. Empty table space on the right side of the frame, where a hand could "
                       "later reach in."),
    "camera-cable": ("S31 / G6 首帧（相机的比方）", None,
                     "A mirrorless camera body with its lens removed, seen from the front so the rectangular image "
                     "sensor inside the mount is clearly visible, standing on a clean wooden desk. A black cable runs "
                     "from the side of the camera to an open laptop beside it. Soft window light; no brand names."),
    "chlamydomonas": ("S02 / S04 / G7 首帧（可选）", None,
                      "Bright-field microscope image of a single Chlamydomonas reinhardtii cell: an oval green cell "
                      "about ten micrometres long, with two thin flagella of equal length coming out of its front end, "
                      "a cup-shaped green chloroplast filling most of the cell, and one small bright orange-red eyespot "
                      "on the side of the cell near its middle. Pale background, sharp focus, the cell in the centre "
                      "with space around it. No scale bar."),
}


def png_size(path: Path) -> list[int]:
    with path.open("rb") as f:
        head = f.read(24)
    return list(struct.unpack(">II", head[16:24]))


def generate(name: str) -> str:
    use, ref, subject = IMAGES[name]
    prompt = (f"This is an automated run and nobody can answer questions. Use your image generation tool to make ONE "
              f"image{', using the attached picture as the reference so the dish, camera angle and framing match' if ref else ''}"
              f", then copy the generated file into the current directory as {name}.png and reply with its absolute "
              f"path and pixel size.\n\n{subject}{TAIL}")
    cmd = ["codex", "exec", "--skip-git-repo-check", "-s", "workspace-write", "-C", str(OUT),
           "--enable", "image_generation", "-c", 'model_reasoning_effort="medium"',
           "-o", str(OUT / f"{name}.last.md")]
    if ref:
        cmd += ["-i", str(OUT / f"{ref}.png")]
    run = subprocess.run(cmd + ["-"], input=prompt, capture_output=True, text=True)
    if not (OUT / f"{name}.png").is_file():
        return f"{name}: FAILED\n{run.stdout[-800:]}\n{run.stderr[-800:]}"
    return f"{name}: ok {png_size(OUT / f'{name}.png')}"


def record() -> None:
    old = {a["path"]: a for a in json.loads(RECORD.read_text())["assets"]} if RECORD.exists() else {}
    assets = []
    for name, (use, ref, subject) in IMAGES.items():
        path = OUT / f"{name}.png"
        if not path.is_file():
            continue
        data = path.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        prev = old.get(f"references/{name}.png", {})
        assets.append({
            "path": f"references/{name}.png", "tool": "codex exec · image_generation",
            "created": prev.get("created") if prev.get("sha256") == digest else date.today().isoformat(),
            "use": use, "reference": f"references/{ref}.png" if ref else None, "intent": subject + TAIL,
            "dimensions": png_size(path), "sha256": digest, "bytes": len(data), "label": "AI 生成"})
    RECORD.write_text(json.dumps({"assets": assets}, ensure_ascii=False, indent=2) + "\n")
    print(f"{len(assets)} images recorded -> {RECORD.relative_to(ROOT)}")


def main() -> None:
    args = sys.argv[1:]
    force = "--force" in args
    names = [a for a in args if a != "--force"] or list(IMAGES)
    unknown = set(names) - set(IMAGES)
    assert not unknown, f"unknown images: {unknown}"
    OUT.mkdir(parents=True, exist_ok=True)
    todo = [n for n in names if force or not (OUT / f"{n}.png").is_file()]
    for n in todo:
        (OUT / f"{n}.png").unlink(missing_ok=True)
    first = [n for n in todo if not IMAGES[n][1] or IMAGES[n][1] not in todo]
    later = [n for n in todo if n not in first]
    with ThreadPoolExecutor(3) as pool:
        for batch in (first, later):
            for line in pool.map(generate, batch):
                print(line, flush=True)
    record()


if __name__ == "__main__":
    main()
