"""Education Economics 2 · sunk cost (FUN-ECONOMICS-02.md; the folders keep the fun-economics-02 name) reuses Fun Economics 1's pipeline where it can: each script here
loads the matching scripts/fun-economics-01 module and points it at this film's folders, lines and timings.

One film per language from one shot list: the picture carries no language-specific text, and each film is paced to
its own voice.
"""
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FILM = "fun-economics-02"
PUB = ROOT / "public" / FILM
OUT = ROOT / "out" / FILM
DOCS = ROOT / "docs" / FILM
LANGS = ("zh", "en")


def base(name: str, folder: str = "fun-economics-01"):
    """Load scripts/<folder>/<name>.py as a module (its own folder on the path, as when it runs)."""
    sys.path.insert(0, str(ROOT / "scripts" / folder))
    spec = importlib.util.spec_from_file_location(f"{folder.replace('-', '_')}_{name}", ROOT / f"scripts/{folder}/{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def media() -> Path:
    for parent in ROOT.parents:
        if (parent / "lucas-academy-media").is_dir():
            return parent / "lucas-academy-media"
    raise SystemExit("Cannot find lucas-academy-media")


VOICES = {lang: {"narrator": media() / f"outputs/louise/{lang}/{FILM}-v1", "mary": media() / f"outputs/eunice/{lang}/{FILM}-mary-v1"}
          for lang in LANGS}
