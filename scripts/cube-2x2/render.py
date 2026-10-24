"""Render one language's film of 「二阶魔方怎么还原？」 (CUBE-2X2.md) with episode 1's chunk renderer: muted chunks
of Cube2x2Zh / Cube2x2En, joined, the language's mix underneath -> out/cube-2x2/delivery/cube-2x2.<lang>.mp4.
Concurrency 2 (the owner's memory budget). Refuses a draft timeline, or a take that changed after check.py
looked at it; a chunk is rendered again only when something its picture is made of changed.

  python3 scripts/cube-2x2/render.py zh|en [--chunks 4]
"""
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PUB = ROOT / "public/cube-2x2"
OUT = ROOT / "out/cube-2x2"
spec = importlib.util.spec_from_file_location("fi01_render", ROOT / "scripts/fun-informatics-01/render.py")
shared = importlib.util.module_from_spec(spec)
spec.loader.exec_module(shared)
shared.PUB, shared.WORK, shared.OUT = PUB, OUT / "chunks", OUT / "delivery"
shared.FILM_NAME, shared.COMP_PREFIX = "cube-2x2", "Cube2x2"
MEDIA = ROOT.parents[0] / "lucas-academy-media"
for parent in ROOT.parents:
    if (parent / "lucas-academy-media").is_dir():
        MEDIA = parent / "lucas-academy-media"
        break

if __name__ == "__main__":
    lang = "en" if "en" in sys.argv[1:] else "zh"
    tl = json.loads((PUB / f"timeline.{lang}.json").read_text())
    if tl.get("draft") and "--draft" not in sys.argv:
        raise SystemExit("The timeline is a draft (missing takes); voice every line and rebuild it first (or pass --draft)")
    report = OUT / f"narration-check{'.en' if lang == 'en' else ''}.json"
    if report.exists() and "--draft" not in sys.argv:
        check = json.loads(report.read_text())
        lines = {l["id"]: l for l in json.loads((PUB / f"narration/{lang}.json").read_text())["lines"]}
        for cid, record in check["cues"].items():
            if record["spoken"] != lines[cid]["text"]:
                raise SystemExit(f"{cid}: the script changed after check.py; re-voice and re-check it")
            take = MEDIA / f"outputs/louise/{lang}/cube-2x2-v1/{cid}.wav"
            if hashlib.sha256(take.read_bytes()).hexdigest() != record["sha256"]:
                raise SystemExit(f"{cid}: the take changed after check.py; run it again")
    files = sorted((ROOT / "src/videos/cube-2x2").glob("*.ts*")) + [PUB / f"timeline.{lang}.json", PUB / f"audio/{lang}.mix.wav"]
    files += sorted(p for p in (PUB / "footage").glob("*") if p.suffix in (".jpg", ".mp4"))
    digest = hashlib.sha256(b"".join(p.read_bytes() for p in files)).hexdigest()
    shared.WORK.mkdir(parents=True, exist_ok=True)
    stamp = shared.WORK / f"fingerprint.{lang}.txt"
    if not stamp.exists() or stamp.read_text() != digest:
        for ok in shared.WORK.glob(f"{lang}.*.ok"):
            ok.unlink()
    stamp.write_text(digest)
    sys.argv = [sys.argv[0], lang, *[a for a in sys.argv[1:] if a not in ("zh", "en", "--draft")]]
    if not any(a.startswith("--concurrency") for a in sys.argv):
        sys.argv.extend(["--concurrency", "2"])
    shared.main()
