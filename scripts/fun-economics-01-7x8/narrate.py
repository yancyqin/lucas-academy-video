"""Voice 「你会算 7×8 吗？」's new lines with lucas-academy-media (takes that exist are kept). Media Python:
  NARRATE_THREADS=8 ../lucas-academy-media/.conda/bin/python scripts/fun-economics-01-7x8/narrate.py zh
"""
import os
import sys

from common import FILM, PUB, media

name = sys.argv[1]
profile, language, speed, out = {"zh": ("louise/zh", "zh", "1.0", f"outputs/louise/zh/{FILM}-v1"),
                                 "en": ("louise/en", "en", "1.0", f"outputs/louise/en/{FILM}-v1")}[name]
os.chdir(media())
sys.path.insert(0, str(media() / "src"))
import torch  # noqa: E402

torch.set_num_threads(int(os.environ.get("NARRATE_THREADS", "4")))
torch.set_num_interop_threads(2)
from lucas_media.narrate import main  # noqa: E402

sys.argv = ["lucas-narrate", str(PUB / f"narration/{name}.json"), "--profile", profile, "--language", language,
            "--speed", speed, "--output-dir", out, *sys.argv[2:]]
main()
