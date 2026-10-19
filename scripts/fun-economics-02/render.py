"""Render one language's film of 「都学了三年，放弃就白学了吗？」 with episode 1's chunk renderer: muted chunks of
FunEconomics02Zh / FunEconomics02En, joined, the language's mix underneath -> out/fun-economics-02/delivery/
fun-economics-02.<lang>.mp4. Concurrency 2 (the owner's 25 GB memory budget). Refuses a draft timeline, or a take
that changed after check.py looked at it.
  python3 scripts/fun-economics-02/render.py zh|en [--chunks 4]
"""
import hashlib
import json
import sys

from common import FILM, OUT, PUB, ROOT, VOICES, base

fe01 = base("render")
shared = fe01.shared
shared.PUB, shared.WORK, shared.OUT = PUB, OUT / "chunks", OUT / "delivery"
shared.FILM_NAME, shared.COMP_PREFIX = FILM, "FunEconomics02"

if __name__ == "__main__":
    lang = "en" if "en" in sys.argv[1:] else "zh"
    tl = json.loads((PUB / f"timeline.{lang}.json").read_text())
    if tl.get("draft"):
        raise SystemExit("The timeline is a draft (missing takes); voice every line and rebuild it first")
    check = json.loads((OUT / f"narration-check.{lang}.json").read_text())
    cues = {c["id"]: c for c in json.loads((PUB / f"narration/cues.{lang}.json").read_text())}
    if check["checked"] != len(cues):
        raise SystemExit(f"check.py saw {check['checked']} of {len(cues)} takes")
    for cid, record in check["cues"].items():
        if record["spoken"] != cues[cid]["spoken"]:
            raise SystemExit(f"{cid}: the script changed after check.py; re-voice and re-check it")
        if hashlib.sha256((VOICES[lang][cues[cid]["speaker"]] / f"{cid}.wav").read_bytes()).hexdigest() != record["sha256"]:
            raise SystemExit(f"{cid}: the take changed after check.py; run it again")
    # a chunk is redone when anything its picture is made of changed
    files = sorted((ROOT / "src/videos/fun-economics-02").glob("*.ts*")) + [ROOT / "src/videos/fun-economics-01/FunEconomics01Video.tsx",
                                                                          PUB / f"timeline.{lang}.json", PUB / f"audio/{lang}.mix.wav"]
    files += sorted(p for p in PUB.rglob("*") if p.is_file() and p.suffix in (".jpg", ".png", ".mp4", ".ttf"))
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
