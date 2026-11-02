"""Stage the film's pictures in public/fun-informatics-04/ (gitignored) for Remotion.

    python3 scripts/fun-informatics-04/assets.py [--force]

clips/<name>.mp4: every moving picture re-encoded to H.264 without sound, trimmed to the part the film uses. Full-frame
clips are 1920x1080; the small Commons lab recordings keep their own shape at 960 px wide, since the film shows them in
a window instead of blowing them up. clips.json records each clip's source, length and frame rate for
build_timeline.py. stills/<name>: the Codex first frames and the Nobel Prize illustrations. fonts/: Noto Serif SC.
Sources: Muse clips (public/fun-informatics-04/muse/, Yancy 2026-11-01), fetch_sources.py's footage, episode 1's
finished Chinese and English films (lucas-academy-video-data/fun-informatics-01/out/delivery/), whose pictures carry no captions.
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PUB = ROOT / "public/fun-informatics-04"
DATA = next(p / "lucas-academy-video-data" for p in ROOT.parents if (p / "lucas-academy-video-data").is_dir())
FI1 = DATA / "fun-informatics-01/out/delivery/fun-informatics-01.zh.mp4"
FI1_EN = DATA / "fun-informatics-01/out/delivery/fun-informatics-01.en.mp4"
FOOT = PUB / "footage"

# name: (source, in, out or None, "full" | "window", where the picture comes from)
CLIPS = {
    # Muse (Yancy). G1 rippled after 2 s, so the opening uses the Codex still instead; G7 had one flagellum, not used.
    "phototaxis": (PUB / "muse/G2-1.mp4", 0, None, "full", "muse"),
    "goggles": (PUB / "muse/G3-1.mp4", 0, None, "full", "muse"),
    "dots": (PUB / "muse/G4-1.mp4", 0, None, "full", "muse"),
    "notebook": (PUB / "muse/G5-1.mp4", 0, None, "full", "muse"),
    "camera": (PUB / "muse/G6-1.mp4", 0, 5.5, "full", "muse"),  # later frames show mount markings
    # Wikimedia Commons lab recordings
    "chlamy-swim": (FOOT / "commons/chlamy-swim.ogv", 0, None, "window", "commons:chlamy-swim"),
    "chlamy-phototaxis": (FOOT / "commons/chlamy-phototaxis.ogv", 0, None, "window", "commons:chlamy-phototaxis"),
    "zebrafish-chr2": (FOOT / "commons/zebrafish-chr2.ogv", 0, None, "window", "commons:zebrafish-chr2"),
    "zebrafish-wt": (FOOT / "commons/zebrafish-wt.ogv", 0, None, "window", "commons:zebrafish-wt"),
    # episode 1's Chinese film (zh timeline: it02-06, it03-04..08, it04-02..07, it07-07, it08-03..05)
    "fi1-switch": (FI1, 134.1, 145.0, "full", "fi1"),
    "fi1-magic": (FI1, 498.2, 509.7, "full", "fi1"),  # it07-07 「没有魔法，也没有谁躲在里面算」
    "fi1-count": (FI1, 180.1, 210.0, "full", "fi1"),
    "fi1-lamps": (FI1, 215.8, 265.1, "full", "fi1"),
    "fi1-rules": (FI1, 560.4, 584.2, "full", "fi1"),
    # the same moments in episode 1's English film (en timeline), for the English film
    "fi1en-switch": (FI1_EN, 138.6, 148.6, "full", "fi1"),
    "fi1en-count": (FI1_EN, 177.6, 215.2, "full", "fi1"),
    "fi1en-lamps": (FI1_EN, 221.1, 269.2, "full", "fi1"),
    "fi1en-magic": (FI1_EN, 491.2, 503.4, "full", "fi1"),
    "fi1en-rules": (FI1_EN, 556.0, 579.8, "full", "fi1"),
}
for pid, item in json.loads((ROOT / "docs/fun-informatics-04/footage-sources.json").read_text())["pexels"].items():
    CLIPS[f"px{pid}"] = (FOOT / f"pexels/{pid}.mp4", 0, None, "full", f"pexels:{pid}")

STILLS = {f"{n}.png": PUB / f"references/{n}.png" for n in ("dish-green", "dish-beam", "chlamydomonas", "camera-cable")}
STILLS.update({f"nobel-{p.stem}.jpg": p for p in sorted((FOOT / "nobel").glob("*.jpg"))})
FONTS = {f: DATA / "jesu/fonts" / f for f in ("NotoSerifSC-Regular.otf", "NotoSerifSC-Light.otf")}


def probe(path: Path) -> dict:
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                        "stream=width,height,r_frame_rate:format=duration", "-of", "json", str(path)],
                       capture_output=True, text=True, check=True)
    j = json.loads(r.stdout)
    s = j["streams"][0]
    return {"width": s["width"], "height": s["height"], "fps": s["r_frame_rate"], "duration": float(j["format"]["duration"])}


def main() -> None:
    force = "--force" in sys.argv
    for sub in ("clips", "stills", "fonts"):
        (PUB / sub).mkdir(parents=True, exist_ok=True)
    info = {}
    for name, (src, a, b, shape, source) in CLIPS.items():
        out = PUB / f"clips/{name}.mp4"
        if force or not out.is_file():
            vf = ("scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080" if shape == "full"
                  else "scale=960:-2:flags=lanczos")
            cmd = ["ffmpeg", "-v", "error", "-y", "-ss", str(a), "-i", str(src)]
            if b is not None:
                cmd += ["-t", str(b - a)]
            cmd += ["-an", "-vf", f"{vf},format=yuv420p", "-c:v", "libx264", "-crf", "18", "-preset", "medium", str(out)]
            subprocess.run(cmd, check=True)
            print("clip", name, flush=True)
        info[name] = {"source": source, "shape": shape, "probe": probe(out)}
    (PUB / "clips.json").write_text(json.dumps(info, indent=1) + "\n")
    for name, src in {**STILLS}.items():
        if force or not (PUB / f"stills/{name}").is_file():
            shutil.copy2(src, PUB / f"stills/{name}")
    for name, src in FONTS.items():
        if not (PUB / f"fonts/{name}").is_file():
            shutil.copy2(src, PUB / f"fonts/{name}")
    print(f"{len(info)} clips, {len(STILLS)} stills staged in {PUB.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
