"""Episode 2, language-specific adapter to the established chunk renderer."""
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
shared.PUB = ROOT / "public/fun-informatics-02"
shared.WORK = ROOT / "out/fun-informatics-02/chunks"
shared.OUT = ROOT / "out/fun-informatics-02/delivery"
shared.FILM_NAME = "fun-informatics-02"
shared.COMP_PREFIX = "FunInformatics02"
shared.LANGS = ("zh", "en")
encoders=subprocess.run(["ffmpeg","-hide_banner","-encoders"],capture_output=True,text=True,check=True).stdout
shared.AUDIO_CODEC = "aac_at" if " aac_at " in encoders else "aac"
# Both tracks already have their final duration. -shortest can drop delayed
# H.264 B-frames from the end of a stream-copy concatenation.
shared.SHORTEST = False

def render(comp, out, frames, concurrency):
    gl = os.environ.get("REMOTION_GL", "angle" if sys.platform == "darwin" else "swangle")
    command = ["npx", "remotion", "render", "src/index.ts", comp, str(out), f"--frames={frames}", "--muted",
               f"--concurrency={concurrency}", f"--gl={gl}", "--timeout=300000", "--offthreadvideo-cache-size-in-bytes=1500000000", "--log=error"]
    if subprocess.run(command, cwd=ROOT).returncode != 0 or not out.is_file(): return False
    actual = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=nb_frames", "-of", "csv=p=0", str(out)], capture_output=True, text=True)
    a, b = map(int, frames.split("-"))
    return actual.returncode == 0 and actual.stdout.strip() == str(b - a + 1)

shared.render = render

if __name__ == "__main__":
    lang = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] in shared.LANGS else "zh"
    suffix = ".en" if lang == "en" else ""
    timeline = json.loads((shared.PUB / f"timeline.{lang}.json").read_text())
    if timeline.get("draft"):
        raise SystemExit(f"Final film cannot render while {lang} narration is missing; rebuild fi02:timeline after all takes exist.")
    check = json.loads((ROOT / f"out/fun-informatics-02/narration-check{suffix}.json").read_text())
    review_path = ROOT / f"out/fun-informatics-02/narration-review{suffix}.json"
    reviewed = json.loads(review_path.read_text()) if review_path.exists() else {}
    if check["checked"] != check["expected"]:
        raise SystemExit(f"Every {lang} voice take must be checked before final render")
    unresolved = [cid for cid in check["flagged"] if reviewed.get(cid,{}).get("sha256") != check["cues"][cid]["sha256"]]
    if unresolved: raise SystemExit("Unresolved narration checks: " + ", ".join(unresolved))
    media=Path(os.environ.get("LUCAS_MEDIA", ROOT.parent / "lucas-academy-media"))
    if not media.is_dir() and "LUCAS_MEDIA" not in os.environ:
        media=ROOT.parents[1] / "lucas-academy-media"
    voices=media / f"outputs/louise/{lang}/fun-informatics-02-v1"
    expected = {line["id"]: line["text"] for line in json.loads((shared.PUB / f"narration/{lang}.json").read_text())["lines"]}
    for cid, record in check["cues"].items():
        if record.get("spoken") != expected[cid]: raise SystemExit(f"{cid}: script changed after check")
        if hashlib.sha256((voices/(cid+".wav")).read_bytes()).hexdigest()!=record["sha256"]:
            raise SystemExit(f"{cid}: voice changed after check")
    files = sorted((ROOT / "src/videos/fun-informatics-02").glob("*.ts*")) + [ROOT / "src/lib/timeRamps.ts", shared.PUB / f"timeline.{lang}.json"]
    files += sorted(p for p in shared.PUB.rglob("*") if p.is_file() and p.suffix in (".jpg",".png",".mp4",".ogg"))
    digest = hashlib.sha256(b"".join(p.read_bytes() for p in files)).hexdigest()
    shared.WORK.mkdir(parents=True, exist_ok=True)
    stamp = shared.WORK / f"fingerprint.{lang}.txt"
    if not stamp.exists() or stamp.read_text() != digest:
        for ok in shared.WORK.glob(f"{lang}.*.ok"):
            ok.unlink()
    stamp.write_text(digest)
    if len(sys.argv) == 1 or sys.argv[1].startswith("--"):
        sys.argv.insert(1, "zh")
    if not any(a.startswith("--concurrency") for a in sys.argv):
        sys.argv.extend(["--concurrency", "2"])
    shared.main()
