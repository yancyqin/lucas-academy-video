"""Synthesize a cube film's narration with the media environment, retaining completed takes.

    ../lucas-academy-media/.conda/bin/python scripts/cube-2x2/narrate.py en|zh [cube-2x2|cube-5x5]

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
# Each film's takes folder under outputs/louise/<lang>/ (a new version when a film's lines are re-voiced as a set).
TAKES = {"cube-2x2": "cube-2x2-v3", "cube-5x5": "cube-5x5-v1"}
lang = sys.argv[1] if len(sys.argv) > 1 else "en"
film = sys.argv[2] if len(sys.argv) > 2 else "cube-2x2"
assert lang in ("zh", "en") and film in TAKES
os.chdir(MEDIA)
sys.path.insert(0, str(MEDIA / "src"))
import torch

torch.set_num_threads(int(os.environ.get("NARRATE_THREADS", "6")))
torch.set_num_interop_threads(2)
from lucas_media.narrate import main
sys.argv = ["lucas-narrate", str(ROOT / f"public/{film}/narration/{lang}.json"),
            "--profile", f"louise/{lang}", "--language", lang, "--speed", "1.0",
            "--output-dir", f"outputs/louise/{lang}/{TAKES[film]}"]
main()
