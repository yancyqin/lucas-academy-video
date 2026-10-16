"""「你会算 7×8 吗？」 (FUN-ECONOMICS-01-7X8.md) reuses Fun Economics 1's pipeline: each script here loads the matching
scripts/fun-economics-01 module and points it at this film's folders, lines and timings."""
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FILM = "fun-economics-01-7x8"
PUB = ROOT / "public" / FILM
OUT = ROOT / "out" / FILM
DOCS = ROOT / "docs" / FILM
LANG = sys.argv[sys.argv.index("--lang") + 1] if "--lang" in sys.argv else "zh"


def base(name: str):
    """Load scripts/fun-economics-01/<name>.py as a module (its own folder on the path, as when it runs)."""
    sys.path.insert(0, str(ROOT / "scripts/fun-economics-01"))
    spec = importlib.util.spec_from_file_location(f"fe01_{name}", ROOT / f"scripts/fun-economics-01/{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def media() -> Path:
    for parent in ROOT.parents:
        if (parent / "lucas-academy-media").is_dir():
            return parent / "lucas-academy-media"
    raise SystemExit("Cannot find lucas-academy-media")


VOICES = {lang: {"narrator": media() / f"outputs/louise/{lang}/{FILM}-v1"} for lang in ("zh", "en")}
