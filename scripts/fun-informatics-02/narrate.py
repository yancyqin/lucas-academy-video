"""Synthesize the film with the media environment, retaining completed takes.

Run using lucas-academy-media/.conda/bin/python. A modest CPU thread count
avoids oversubscription on Apple Silicon while ASR checks run alongside it.
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
lang = sys.argv[1] if len(sys.argv) > 1 else "en"
assert lang in ("zh", "en")
os.chdir(MEDIA)
sys.path.insert(0, str(MEDIA / "src"))
import torch

torch.set_num_threads(2)
torch.set_num_interop_threads(2)
from lucas_media.narrate import main
sys.argv = ["lucas-narrate", str(ROOT / f"public/fun-informatics-02/narration/{lang}.json"),
            "--profile", f"louise/{lang}", "--language", lang, "--speed", "1.0",
            "--output-dir", f"outputs/louise/{lang}/fun-informatics-02-v1"]
main()
