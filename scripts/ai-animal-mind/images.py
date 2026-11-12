"""First frames for the Muse clips of 「动物想什么？AI 知道吗？」, made with Codex image generation.

    python3 scripts/ai-animal-mind/images.py [name ...] [--force]

Yancy makes the short videos in Muse; these realistic photographs are the frames to start them from. The picture
carries no text at all (the film has no labels: one picture for the English and the Chinese track). G03 (a monkey
added to Yancy's beach photo) and G04 (the photo itself) were dropped on 2026-11-11 (「不用我的照片了」): those shots
are Pexels footage now.

Writes lucas-academy-video-data/ai-animal-mind/references/<name>.png and records each in
docs/ai-animal-mind/generated-assets.json (tool, intent, size, sha256). Three run at once.
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
DATA = next(p / "lucas-academy-video-data" for p in ROOT.parents if (p / "lucas-academy-video-data").is_dir())
FILM = DATA / "ai-animal-mind"
OUT = FILM / "references"
RECORD = ROOT / "docs/ai-animal-mind/generated-assets.json"

TAIL = (" Realistic photograph, natural colours, not an illustration, not a cartoon. No text, letters, numbers, "
        "signs, labels, watermarks or logos anywhere. Landscape 16:9, the largest native size, no software upscale.")

# name: (where it is used, reference picture or None, subject)
IMAGES = {
    "G01-sunset-hill": ("am00-04..07 一个人，两只猴子，一起看夕阳；am13-01", None,
                        "Seen from behind and a little to the side: a man in a light field shirt sits alone on a "
                        "grassy hilltop ridge in East Africa, looking out over a wide calm lake at sunset. Two wild "
                        "vervet monkeys sit on the grass close beside him, also facing the lake, about an arm's length "
                        "apart from him. The sun is just above the far shore and lays a golden path across the water; "
                        "the sky glows orange and rose. Warm backlight, soft rim light on the monkeys' fur, peaceful."),
    "G02-handshake": ("am00-06 它们先握了握手", None,
                      "Close-up at golden hour on a grassy hillside: two wild vervet monkeys facing each other, each "
                      "reaching out a hand so their hands are just about to clasp in a friendly greeting. Warm low sun "
                      "behind them, glowing rim light on their fur, the lake and evening sky softly out of focus."),
    "G05-hans": ("am06-01..02 一匹会算术的马，汉斯", None,
                 "A sunny cobblestone courtyard in Berlin around 1904, photographed in gently faded early-1900s "
                 "colours: a handsome dark-brown horse stands calmly in the middle; beside it an elderly man with a "
                 "white beard, a black wide-brimmed hat and a long dark coat looks at the horse; a small crowd of "
                 "curious men and women in early-1900s clothes and hats stand around them watching. A small blank "
                 "slate board on a wooden easel stands near the horse. Period-accurate buildings with tall windows."),
    "G05b-hoof": ("am06-02 用蹄子一下一下敲出答案", None,
                  "Low close-up of a dark-brown horse's front leg and hoof raised a little above old grey "
                  "cobblestones, about to tap the ground, in warm morning sunlight in a 1900s courtyard; the hems of "
                  "a few onlookers' long coats softly out of focus in the background."),
    "G06-pigeon-paintings": ("am11-02 鸽子看画（莫奈 / 毕加索）", None,
                             "A grey city pigeon stands on a pale wooden table in a bright, quiet room, its head "
                             "turned toward two small framed paintings propped up side by side on the table. The "
                             "left painting is an Impressionist oil painting of a water-lily pond in soft blues, "
                             "greens and pinks with loose dabbed brushstrokes. The right painting is a Cubist-style "
                             "oil painting of fragmented angular planes in browns, ochres and greys. Neither "
                             "painting copies any real artwork. Soft window daylight."),
    "G07-tamarin-quiet": ("am11-06 小猴子选了没有声音的那边", None,
                          "A tiny cotton-top tamarin monkey with its white crest sits in the middle of a cosy, "
                          "clean wooden play enclosure that has two halves. On the left side a small round speaker "
                          "sits on a little shelf. The right side is an empty, calm corner with a soft folded "
                          "blanket. The tamarin is turning its head toward the quiet right side. Warm, soft light."),
    "G08-chinchilla-music": ("am11-04 老鼠跟着拍子点头（画面用龙猫）", None,
                             "A fluffy grey chinchilla sits upright on a wooden shelf next to a small cream-coloured "
                             "vintage table radio, its big round ears up as if listening closely to the music. Warm, "
                             "cosy home lighting, a softly blurred bookshelf behind."),
    "G09-elephant-speaker": ("am03-03..04 把录音放给大象听", None,
                             "African savanna at golden hour: a small black loudspeaker on a short tripod stands in "
                             "the dry grass in the foreground. In the middle distance an African elephant has turned "
                             "toward it, ears spread wide, trunk slightly raised, about to walk toward the speaker. "
                             "Acacia trees on the horizon, warm dusty light."),
    "G10-dolphin-scarf": ("am05-01..02 和海豚一起造几个新词（11-11 Yancy：换成穿比基尼、不戴面镜和呼吸管的人）", None,
                          "Underwater in clear turquoise shallow sea with sunbeams: a young woman in a simple "
                          "one-colour bikini swims freely, seen from the side, her face uncovered: no mask, no goggles, "
                          "no snorkel, no glasses, eyes open, long hair floating. She holds out a bright red scarf; an "
                          "Atlantic spotted dolphin swims close in front of the scarf, curious, its spotted skin clearly "
                          "visible. Sandy bottom below, light ripples. Natural, documentary feel."),
    "G11a-dog-vacuum": ("am09-02 狗旁边有一个吸尘器", None,
                        "A medium-sized tan and white mixed-breed dog sits on a light wooden floor in a bright, plain "
                        "living room, facing the camera, with a neutral, hard-to-read expression: mouth closed, ears "
                        "half up, eyes looking slightly to the side. Right next to the dog stands an upright grey "
                        "vacuum cleaner. Soft daylight, eye-level camera, the dog in the centre of the frame."),
    "G11b-dog-leash": ("am09-02 狗旁边是一根牵引绳", "G11a-dog-vacuum",
                       "The same dog as in the attached picture, in exactly the same pose, expression, position, "
                       "lighting and camera angle, in the same room and on the same floor. The only change: the grey "
                       "vacuum cleaner is gone, and in its place a red dog leash lies coiled on the floor right next "
                       "to the dog. Nothing else changes."),
}


def png_size(path: Path) -> list[int]:
    with path.open("rb") as f:
        head = f.read(24)
    return list(struct.unpack(">II", head[16:24]))


def ref_file(ref: str) -> Path:
    """The reference is another generated frame (the same dog in a second setting)."""
    return OUT / f"{ref}.png"


def generate(name: str) -> str:
    use, ref, subject = IMAGES[name]
    prompt = (f"This is an automated run and nobody can answer questions. Use your image generation tool to make ONE "
              f"image{', editing the attached picture as described' if ref else ''}, then copy the generated file "
              f"into the current directory as {name}.png and reply with its absolute path and pixel size.\n\n"
              f"{subject}{TAIL}")
    cmd = ["codex", "exec", "--skip-git-repo-check", "-s", "workspace-write", "-C", str(OUT),
           "--enable", "image_generation", "-c", 'model_reasoning_effort="medium"', "-o", str(OUT / f"{name}.last.md")]
    if ref:
        cmd += ["-i", str(ref_file(ref))]
    run = subprocess.run(cmd + ["-"], input=prompt, capture_output=True, text=True)
    if not (OUT / f"{name}.png").is_file():
        return f"{name}: FAILED\n{run.stdout[-600:]}\n{run.stderr[-600:]}"
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
        assets.append({"path": f"references/{name}.png", "tool": "codex exec · image_generation",
                       "created": prev.get("created") if prev.get("sha256") == digest else date.today().isoformat(),
                       "use": use, "reference": f"references/{ref}.png" if ref else None,
                       "intent": subject + TAIL, "dimensions": png_size(path), "sha256": digest, "bytes": len(data)})
    RECORD.parent.mkdir(parents=True, exist_ok=True)
    data = json.loads(RECORD.read_text()) if RECORD.exists() else {}
    data["assets"] = assets  # keep the other keys (cover_images.py records its covers there)
    RECORD.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    print(f"{len(assets)} images recorded -> {RECORD.relative_to(ROOT)}")


def main() -> None:
    args = sys.argv[1:]
    force = "--force" in args
    names = [a for a in args if a != "--force"] or list(IMAGES)
    assert not set(names) - set(IMAGES), f"unknown images: {set(names) - set(IMAGES)}"
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
