"""Voice Education Economics 2 with lucas-academy-media (takes that exist are kept). Media Python, one process at a time:
  NARRATE_THREADS=8 ../lucas-academy-media/.conda/bin/python scripts/fun-economics-02/narrate.py zh|mary-zh|en|mary-en [--only ids --force]
"""
import os
import sys

from common import FILM, PUB, media

name = sys.argv[1]
profile, language, speed, out = {
    "zh": ("louise/zh", "zh", "1.0", f"outputs/louise/zh/{FILM}-v1"),
    "mary-zh": ("eunice/en", "zh", "1.05", f"outputs/eunice/zh/{FILM}-mary-v1"),
    "en": ("louise/en", "en", "1.0", f"outputs/louise/en/{FILM}-v1"),
    "mary-en": ("eunice/en", "en", "1.05", f"outputs/eunice/en/{FILM}-mary-v1"),
}[name]
os.chdir(media())
sys.path.insert(0, str(media() / "src"))
import torch  # noqa: E402

torch.set_num_threads(int(os.environ.get("NARRATE_THREADS", "4")))
torch.set_num_interop_threads(2)
from lucas_media.narrate import main  # noqa: E402

sys.argv = ["lucas-narrate", str(PUB / f"narration/{name}.json"), "--profile", profile, "--language", language,
            "--speed", speed, "--output-dir", out, *sys.argv[2:]]
main()
