"""Render 「你会算 7×8 吗？」 with Fun Economics 1's chunk renderer (concurrency 2, the owner's memory budget).
  python3 scripts/fun-economics-01-7x8/render.py [zh|en]
"""
import hashlib
import json
import sys

from common import FILM, OUT, PUB, ROOT, VOICES, base

r = base("render")
shared = r.shared
shared.PUB, shared.WORK, shared.OUT = PUB, OUT / "chunks", OUT / "delivery"
shared.FILM_NAME, shared.COMP_PREFIX = FILM, "FunEconomics01Extra"

if __name__ == "__main__":
    lang = "en" if "en" in sys.argv[1:] else "zh"
    tl = json.loads((PUB / f"timeline.{lang}.json").read_text())
    if tl.get("draft"):
        raise SystemExit("The timeline is a draft (missing takes); voice every line and rebuild it first")
    check = json.loads((OUT / f"narration-check.{lang}.json").read_text())
    cues = {c["id"]: c for c in json.loads((PUB / f"narration/cues.{lang}.json").read_text())}
    for cid, record in check["cues"].items():
        if record["spoken"] != cues[cid]["spoken"]:
            raise SystemExit(f"{cid}: the script changed after check.py; re-voice and re-check it")
        if hashlib.sha256((VOICES[lang]["narrator"] / f"{cid}.wav").read_bytes()).hexdigest() != record["sha256"]:
            raise SystemExit(f"{cid}: the take changed after check.py; run it again")
    other = "zh" if lang == "en" else "en"
    files = sorted((ROOT / "src/videos/fun-economics-01-7x8").glob("*.ts*")) + [PUB / f"timeline.{lang}.json", PUB / f"audio/{lang}.mix.wav"]
    files += sorted(p for p in PUB.rglob("*") if p.is_file() and p.suffix in (".jpg", ".png", ".mp4") and f".{other}." not in p.name)
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
