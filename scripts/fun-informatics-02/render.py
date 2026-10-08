"""Episode 2, Chinese-only adapter to the established chunk renderer."""
import hashlib
import importlib.util
import json
import os
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
shared.LANGS = ("zh",)

if __name__ == "__main__":
    timeline = json.loads((shared.PUB / "timeline.zh.json").read_text())
    if timeline.get("draft"):
        raise SystemExit("Final film cannot render while Chinese narration is missing; rebuild fi02:timeline after all takes exist.")
    check = json.loads((ROOT / "out/fun-informatics-02/narration-check.json").read_text())
    review_path = ROOT / "out/fun-informatics-02/narration-review.json"
    reviewed = json.loads(review_path.read_text()) if review_path.exists() else {}
    if check["checked"] != check["expected"]:
        raise SystemExit("Every Chinese voice take must be checked before final render")
    unresolved = [cid for cid in check["flagged"] if reviewed.get(cid,{}).get("sha256") != check["cues"][cid]["sha256"]]
    if unresolved: raise SystemExit("Unresolved narration checks: " + ", ".join(unresolved))
    media=Path(os.environ.get("LUCAS_MEDIA", ROOT.parent / "lucas-academy-media"))
    if not media.is_dir() and "LUCAS_MEDIA" not in os.environ:
        media=ROOT.parents[1] / "lucas-academy-media"
    voices=media / "outputs/louise/zh/fun-informatics-02-v1"
    for cid, record in check["cues"].items():
        if hashlib.sha256((voices/(cid+".wav")).read_bytes()).hexdigest()!=record["sha256"]:
            raise SystemExit(f"{cid}: voice changed after check")
    files = sorted((ROOT / "src/videos/fun-informatics-02").glob("*.ts*")) + [ROOT / "src/lib/timeRamps.ts", shared.PUB / "timeline.zh.json"]
    files += sorted(p for p in shared.PUB.rglob("*") if p.is_file() and p.suffix in (".jpg",".png",".mp4",".ogg"))
    digest = hashlib.sha256(b"".join(p.read_bytes() for p in files)).hexdigest()
    shared.WORK.mkdir(parents=True, exist_ok=True)
    stamp = shared.WORK / "fingerprint.txt"
    if not stamp.exists() or stamp.read_text() != digest:
        for ok in shared.WORK.glob("*.ok"):
            ok.unlink()
    stamp.write_text(digest)
    if len(sys.argv) == 1 or sys.argv[1].startswith("--"):
        sys.argv.insert(1, "zh")
    if not any(a.startswith("--concurrency") for a in sys.argv):
        sys.argv.extend(["--concurrency", "2"])
    shared.main()
