"""Render 「一根冰棍，要花多少钱？」 with episode 1's chunk renderer: muted chunks, joined, the narration mix underneath.

Concurrency stays at 2 (the owner's 25 GB memory budget). Refuses a draft timeline or narration that changed after
check.py looked at it.
  python3 scripts/fun-economics-01/render.py [zh|en] [--chunks 4]
"""
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("fi01_render", ROOT / "scripts/fun-informatics-01/render.py")
shared = importlib.util.module_from_spec(spec)
spec.loader.exec_module(shared)
shared.PUB = ROOT / "public/fun-economics-01"
shared.WORK = ROOT / "out/fun-economics-01/chunks"
shared.OUT = ROOT / "out/fun-economics-01/delivery"
shared.FILM_NAME = "fun-economics-01"
shared.COMP_PREFIX = "FunEconomics01"
shared.LANGS = ("zh", "en")
encoders = subprocess.run(["ffmpeg", "-hide_banner", "-encoders"], capture_output=True, text=True, check=True).stdout
shared.AUDIO_CODEC = "aac_at" if " aac_at " in encoders else "aac"
shared.SHORTEST = False


def render(comp, out, frames, concurrency):
    gl = os.environ.get("REMOTION_GL", "angle" if sys.platform == "darwin" else "swangle")
    command = ["npx", "remotion", "render", "src/index.ts", comp, str(out), f"--frames={frames}", "--muted",
               f"--concurrency={concurrency}", f"--gl={gl}", "--timeout=300000", "--offthreadvideo-cache-size-in-bytes=1000000000", "--log=error"]
    code = subprocess.run(command, cwd=ROOT).returncode
    if code != 0 or not out.is_file():
        return False
    probe = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=nb_frames", "-of", "json", str(out)],
                           capture_output=True, text=True)
    a, b = map(int, frames.split("-"))
    try:
        return int(json.loads(probe.stdout)["streams"][0]["nb_frames"]) == b - a + 1
    except (ValueError, KeyError, IndexError):
        return False


shared.render = render

if __name__ == "__main__":
    lang = "en" if "en" in sys.argv[1:] else "zh"
    other = "zh" if lang == "en" else "en"
    tl = json.loads((shared.PUB / f"timeline.{lang}.json").read_text())
    if tl.get("draft"):
        raise SystemExit("The timeline is a draft (missing takes); voice every line and rebuild it first")
    check = json.loads((ROOT / f"out/fun-economics-01/narration-check.{lang}.json").read_text())
    sys.path.insert(0, str(ROOT / "scripts/fun-economics-01"))
    from build_timeline import VOICES
    cues = {c["id"]: c for c in json.loads((shared.PUB / f"narration/cues.{lang}.json").read_text())}
    for cid, record in check["cues"].items():
        if record["spoken"] != cues[cid]["spoken"]:
            raise SystemExit(f"{cid}: the script changed after check.py; re-voice and re-check it")
        if hashlib.sha256((VOICES[lang][cues[cid]["speaker"]] / f"{cid}.wav").read_bytes()).hexdigest() != record["sha256"]:
            raise SystemExit(f"{cid}: the take changed after check.py; run it again")
    files = sorted((ROOT / "src/videos/fun-economics-01").glob("*.ts*")) + [shared.PUB / f"timeline.{lang}.json", shared.PUB / f"audio/{lang}.mix.wav"]
    files += sorted(p for p in shared.PUB.rglob("*") if p.is_file() and p.suffix in (".jpg", ".png", ".mp4", ".ttf") and f".{other}." not in p.name)
    digest = hashlib.sha256(b"".join(p.read_bytes() for p in files)).hexdigest()
    shared.WORK.mkdir(parents=True, exist_ok=True)
    stamp = shared.WORK / f"fingerprint.{lang}.txt"
    if not stamp.exists() or stamp.read_text() != digest:
        for ok in shared.WORK.glob(f"{lang}.*.ok"):
            ok.unlink()
    stamp.write_text(digest)
    sys.argv = [sys.argv[0], lang, *[a for a in sys.argv[1:] if a not in ("zh", "en")]]
    if not any(a.startswith("--concurrency") for a in sys.argv):
        sys.argv.extend(["--concurrency", "2"])
    shared.main()
