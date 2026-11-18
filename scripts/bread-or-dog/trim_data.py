"""Trim lucas-academy-video-data/bread-or-dog to what cannot be regenerated, with sources.tsv + a tested restore.sh.

  python3 scripts/bread-or-dog/trim_data.py [--dry-run]

As the project's rule (memory "Back up only the irreplaceable"): keep the model replies, hand judgments, Codex and Muse
pictures/clip, covers, the exact noise PNGs, and the records (pages, research sources, music sources); move downloads
(Pexels photos and thumbnails, the Geirhos images, the music candidates) and everything the scripts rebuild (test
pictures, film pictures, sheets, duplicates) into one staging folder with a MANIFEST, then to the Trash as one item.
Downloads are listed in sources.tsv (path, url, sha1, bytes); restore.sh downloads them back and rebuilds the rest.
Also staged: the worktree's out/bread-or-dog, public/bread-or-dog, node_modules, and the v1 voice takes (v2 stays for
a re-render). Yancy, 2026-11-17: 「Yes, trim it」.
"""
import hashlib
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = next(p / "lucas-academy-video-data" for p in ROOT.parents if (p / "lucas-academy-video-data").is_dir()) / "bread-or-dog"
MEDIA = next(p / "lucas-academy-media" for p in ROOT.parents if (p / "lucas-academy-media").is_dir())
STAGE = DATA.parent / "_trash-staging" / "面包还是狗-清理-20261117"
DRY = "--dry-run" in sys.argv
PEXELS = "https://images.pexels.com/photos/{id}/pexels-photo-{id}.jpeg?auto=compress&cs=tinysrgb&w={w}"
GEIRHOS = "https://raw.githubusercontent.com/rgeirhos/texture-vs-shape/master/stimuli/style-transfer-preprocessed-512/cat/{f}"


def sha1(p: Path) -> str:
    return hashlib.sha1(p.read_bytes()).hexdigest()


def downloads():
    rows = []
    for p in sorted((DATA / "photos").glob("*.jpg")):
        rows.append((p, PEXELS.format(id=p.stem, w=1400)))
    for p in sorted((DATA / "round2/tiles").glob("*.jpg")):
        rows.append((p, PEXELS.format(id=p.stem, w=640)))
    for p in sorted((DATA / "candidates/pexels").glob("*/*.jpg")):
        rows.append((p, PEXELS.format(id=p.stem, w=400)))
    for p in sorted((DATA / "history/geirhos-stimuli").glob("*.png")):
        rows.append((p, GEIRHOS.format(f=p.name)))
    lic = DATA / "history/geirhos-stimuli/DATASET_LICENSE.txt"
    rows.append((lic, "https://raw.githubusercontent.com/rgeirhos/texture-vs-shape/master/DATASET_LICENSE"))
    src = json.loads((DATA / "music/sources.json").read_text())
    c1 = next(c for c in (src["candidates"] if isinstance(src, dict) else src) if c["id"] == "c1")
    rows.append((DATA / "music" / c1["file"], c1["source_url"]))
    return rows


def to_stage(p: Path, base: Path, label: str, moved: list):
    if not p.exists():
        return
    rel = p.relative_to(base)
    dst = STAGE / label / rel
    size = sum(f.stat().st_size for f in p.rglob("*") if f.is_file()) if p.is_dir() else p.stat().st_size
    moved.append((f"{label}/{rel}", size))
    if not DRY:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(p), str(dst))


def main():
    rows = downloads()
    tsv = "path\turl\tsha1\tbytes\n" + "".join(f"{p.relative_to(DATA)}\t{u}\t{sha1(p)}\t{p.stat().st_size}\n" for p, u in rows)
    if not DRY:
        (DATA / "sources.tsv").write_text(tsv)
    print(len(rows), "downloads in sources.tsv")
    moved = []
    data_items = [DATA / "photos", DATA / "round2/tiles", DATA / "candidates/pexels", DATA / "history/geirhos-stimuli",
                  DATA / "music/candidates", DATA / "music/listen.html", DATA / "test", DATA / "test_sheet.jpg",
                  DATA / "film-pics", DATA / "round2/dogcake_sheet.jpg", DATA / "runs/ollama_pull.log",
                  # duplicates of muse/frames/* and of the Codex originals
                  DATA / "muse/codex/M01_first_16x9.png", DATA / "muse/codex/M01_end_ref_a.png", DATA / "muse/codex/M01_end_ref_b.png",
                  DATA / "muse/codex/ref_k1_dogcake_shiba.png", DATA / "covers/ref_A_cake_dog.png", DATA / "covers/ref_B_cake_cut.png"]
    data_items += sorted((DATA / "candidates").glob("sheet_*.jpg"))
    data_items += sorted((DATA / "round2/test").glob("*.jpg"))  # rebuilt by make_round2.py; the adv*.png stay
    for p in data_items:
        to_stage(p, DATA, "data", moved)
    for p in (ROOT / "out/bread-or-dog", ROOT / "public/bread-or-dog", ROOT / "node_modules"):
        to_stage(p, ROOT, "worktree", moved)
    for lang in ("en", "zh"):
        to_stage(MEDIA / f"outputs/louise/{lang}/bread-or-dog-v1", MEDIA, "media", moved)
    total = sum(s for _, s in moved)
    manifest = (f"面包还是狗 cleanup 2026-11-17 (Yancy: 「Yes, trim it」), {total / 1e6:.0f} MB, {len(moved)} items\n"
                f"Downloads are in data/bread-or-dog/sources.tsv; restore.sh brings them back and rebuilds the rest.\n\n" +
                "".join(f"{s / 1e6:9.2f} MB  {r}\n" for r, s in moved))
    if not DRY:
        STAGE.mkdir(parents=True, exist_ok=True)
        (STAGE / "MANIFEST.txt").write_text(manifest)
        (DATA / "CLEANUP-20261117.txt").write_text(manifest)
    print(manifest)


if __name__ == "__main__":
    main()
