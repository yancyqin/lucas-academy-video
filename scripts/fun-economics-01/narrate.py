"""Voice one narration file with lucas-academy-media, keeping takes that already exist.

Run with lucas-academy-media's Python. Batches can run side by side (README of FUN-INFORMATICS-01: three
processes at four threads each); pass the line ids to voice with --only.

  ../lucas-academy-media/.conda/bin/python scripts/fun-economics-01/narrate.py zh [--only oc00-01,oc00-03]
  ../lucas-academy-media/.conda/bin/python scripts/fun-economics-01/narrate.py mary-zh
  ../lucas-academy-media/.conda/bin/python scripts/fun-economics-01/narrate.py en      (and mary-en)
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for parent in ROOT.parents:
    if (parent / "lucas-academy-media").is_dir():
        MEDIA = parent / "lucas-academy-media"
        break
else:
    raise SystemExit("Cannot find lucas-academy-media")

JOBS = {
    "zh": ("louise/zh", "zh", "1.0", "outputs/louise/zh/fun-economics-01-v1"),
    "mary-zh": ("eunice/en", "zh", "1.05", "outputs/eunice/zh/fun-economics-01-mary-v1"),
    "en": ("louise/en", "en", "1.0", "outputs/louise/en/fun-economics-01-v1"),
    "mary-en": ("eunice/en", "en", "1.05", "outputs/eunice/en/fun-economics-01-mary-v1"),
}
name = sys.argv[1]
profile, language, speed, out = JOBS[name]
extra = sys.argv[2:]
os.chdir(MEDIA)
sys.path.insert(0, str(MEDIA / "src"))
import torch  # noqa: E402

torch.set_num_threads(int(os.environ.get("NARRATE_THREADS", "4")))  # one process at 8 beats two at 4 under memory pressure
torch.set_num_interop_threads(2)
from lucas_media.narrate import main  # noqa: E402

sys.argv = ["lucas-narrate", str(ROOT / f"public/fun-economics-01/narration/{name}.json"),
            "--profile", profile, "--language", language, "--speed", speed, "--output-dir", out, *extra]
main()
