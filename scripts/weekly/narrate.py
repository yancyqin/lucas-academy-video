"""Voice one language of an episode with lucas-academy-media (run with ITS Python), keeping takes that exist.

  NARRATE_THREADS=8 ../lucas-academy-media/.conda/bin/python scripts/weekly/narrate.py 001 zh [--only op00-01,…] [--force]
Raw takes go to lucas-academy-media/outputs/<voice>/weekly-<ep>-v1/; scripts/weekly/takes.py trims them into the episode.
One voice process at a time: CosyVoice takes 6–8 GB.
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MEDIA = next(p / "lucas-academy-media" for p in ROOT.parents if (p / "lucas-academy-media").is_dir())
VOICE = {"zh": "fangfang/zh", "en": "louise/en"}

ep, lang, *extra = sys.argv[1:]
os.chdir(MEDIA)
sys.path.insert(0, str(MEDIA / "src"))
import torch  # noqa: E402

torch.set_num_threads(int(os.environ.get("NARRATE_THREADS", "8")))
torch.set_num_interop_threads(2)
from lucas_media.narrate import main  # noqa: E402

sys.argv = ["lucas-narrate", str(ROOT / f"public/weekly/{ep}/narration/script.{lang}.json"), "--profile", VOICE[lang],
            "--language", lang, "--output-dir", str(MEDIA / f"outputs/{VOICE[lang]}/weekly-{ep}-v1"), *extra]
main()
