"""Generate the film's illustrations with Codex image generation (FUN-INFORMATICS-03.md §5).

    python3 scripts/fun-informatics-03/images.py [name ...] [--force]

Every image shares one style: marker doodles on warm paper, so the AI pictures sit next to the real
Pictionary drawings without a jump. No image carries text or digits; numbers, letters and signs are
drawn on top in Remotion, where they are exact and can animate.

Writes public/fun-informatics-03/images/<name>.png (gitignored) and records each one in
docs/fun-informatics-03/generated-assets.json (tool, intent, size, sha256, label "AI 生成"), the same
record episode 2 kept. Existing images are skipped unless named with --force. Three run at once.
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
OUT = ROOT / "public/fun-informatics-03/images"
RECORD = ROOT / "docs/fun-informatics-03/generated-assets.json"

STYLE = ("Children's picture-book illustration in a hand-drawn marker style: bold, slightly wobbly black marker "
         "outlines on warm off-white paper, flat colour fills in a small palette (teal, orange, warm yellow, soft sky "
         "blue), a little paper texture, generous empty space, friendly and simple. Absolutely no text, letters, "
         "numbers or logos anywhere in the image.")

# name: (where it is used, subject)
IMAGES = {
    "walkie-talkie": ("NS01 对讲机试听；片名卡；封面",
                      "a chunky yellow walkie-talkie standing upright with its antenna up; little zig-zag sound waves "
                      "and scribbly static sparks burst from its speaker. Centered. Landscape 16:9."),
    "pilot-radio": ("zh ns00-03；en ns00-01–ns00-03",
                    "a friendly pilot in a small cockpit, seen from the side, wearing a headset and speaking into its "
                    "little microphone; clouds and blue sky through the window; a few zig-zag radio waves leave the "
                    "headset. Landscape 16:9."),
    "noisy-classroom": ("ns01-01 教室里太吵",
                        "a lively classroom seen from the back of the room: children chatting, laughing and waving, a "
                        "paper plane in the air; at the front a teacher is talking, and the teacher's empty speech "
                        "bubble is half scribbled over by messy zig-zag lines. Landscape 16:9."),
    "crackly-phone": ("ns01-01 电话里沙沙响",
                      "a child holding an old-fashioned telephone receiver to one ear, looking puzzled; the curly cord "
                      "turns into scribbly zig-zag static lines as it runs off the side of the picture. Landscape 16:9."),
    "dice-one": ("zh ns01-08 骰子上的一个点叫「幺」",
                 "a single white six-sided die in a three-quarter view; its top face shows one large round red dot and "
                 "nothing else; a soft shadow. Centered, lots of empty paper. Landscape 16:9."),
    "cane-seven": ("zh ns01-08 七像根拐杖",
                   "an old wooden walking cane drawn alone, tilted so that its short handle runs straight across the "
                   "top and its long shaft slants down to the lower left, the whole cane making the shape of a seven "
                   "(but do not draw any digit). Centered, lots of empty paper. Landscape 16:9."),
    "hole-zero": ("zh ns01-08 零像个洞",
                  "a tall oval dark hole in a small patch of grass, seen from slightly above; a curious little mole "
                  "peeks out from the rim. Centered, lots of empty paper. Landscape 16:9."),
    "buildings-wrong-door": ("zh ns01-05 七号楼听成一号楼",
                             "two apartment buildings side by side, each with one big blank white square plaque on its "
                             "front wall near the top; a delivery courier on a little scooter, holding a parcel, has "
                             "stopped in front of the left building and scratches their head. The plaques are empty. "
                             "Landscape 16:9."),
    "taxiway-fork": ("en ns01-05 wrong road at the airport",
                     "a small friendly passenger plane rolling along an airport taxiway that splits into two at a fork; "
                     "at the fork stand two blank yellow signboards on short posts, one by each branch, both empty. "
                     "Seen from slightly above. Landscape 16:9."),
    "tin-can-phone": ("NS03 收尾和开放问题",
                      "two children in a sunny garden talking through a tin-can telephone, one speaking into a can and "
                      "the other listening with a big smile; the string between the cans has a few small scribbly "
                      "zig-zag kinks in the middle. Landscape 16:9."),
}


# Photographic pictures, with their own prompt instead of STYLE. The cover's: the owner wants it real-looking and
# educational for parents and educators (2026-10-16).
PHOTOS = {
    "cover-photo-desk": ("YouTube cover (cover.py desk)",
                         "A realistic photograph (not an illustration): a yellow-and-black handheld walkie-talkie lying on a light "
                         "wooden table, next to a sheet of white paper with a child's simple pencil drawing of a star, two pencils, a "
                         "coin and a small printed word card that is blank. Soft natural window light from the left, shallow depth of "
                         "field, calm and warm, the feel of a thoughtful home or classroom learning moment. The objects sit in the right "
                         "half of the frame; the left half is calm, softly blurred table and wall, good for a title. No people, no "
                         "hands, no text, no letters, no numbers, no logos anywhere. Landscape 16:9."),
}


def png_size(path: Path) -> list[int]:
    with path.open("rb") as f:
        head = f.read(24)
    return list(struct.unpack(">II", head[16:24]))


def generate(name: str) -> str:
    head = (f"Use your image generation tool to make ONE image, then copy the generated file into the current "
            f"directory as {name}.png and reply with its absolute path and pixel size.\n\n")
    prompt = head + (PHOTOS[name][1] if name in PHOTOS else f"Style: {STYLE}\n\nSubject: {IMAGES[name][1]}")
    run = subprocess.run(["codex", "exec", "--skip-git-repo-check", "-s", "workspace-write", "-C", str(OUT), prompt],
                         capture_output=True, text=True)
    if not (OUT / f"{name}.png").is_file():
        return f"{name}: FAILED\n{run.stdout[-800:]}\n{run.stderr[-800:]}"
    return f"{name}: ok"


def record() -> None:
    old = {a["path"]: a for a in json.loads(RECORD.read_text())["assets"]} if RECORD.exists() else {}
    assets = []
    for name, (use, subject) in {**IMAGES, **PHOTOS}.items():
        path = OUT / f"{name}.png"
        if not path.is_file():
            continue
        data = path.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        prev = old.get(f"images/{name}.png", {})
        assets.append({
            "path": f"images/{name}.png", "tool": "codex exec · image_generation",
            "created": prev.get("created") if prev.get("sha256") == digest else date.today().isoformat(),
            "use": use, "intent": subject, "style": "photographic (in intent)" if name in PHOTOS else STYLE, "dimensions": png_size(path),
            "sha256": digest, "bytes": len(data), "label": "AI 生成"})
    RECORD.write_text(json.dumps({"assets": assets}, ensure_ascii=False, indent=2) + "\n")
    print(f"{len(assets)} images recorded -> {RECORD.relative_to(ROOT)}")


def main() -> None:
    args = sys.argv[1:]
    force = "--force" in args
    names = [a for a in args if a != "--force"] or list(IMAGES)
    unknown = set(names) - set(IMAGES) - set(PHOTOS)
    assert not unknown, f"unknown images: {unknown}"
    OUT.mkdir(parents=True, exist_ok=True)
    todo = [n for n in names if force or not (OUT / f"{n}.png").is_file()]
    for n in todo:
        (OUT / f"{n}.png").unlink(missing_ok=True)
    with ThreadPoolExecutor(3) as pool:
        for line in pool.map(generate, todo):
            print(line, flush=True)
    record()


if __name__ == "__main__":
    main()
