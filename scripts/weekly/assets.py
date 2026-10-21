"""Copy an episode's outside assets (shots.py ASSETS) into public/weekly/<ep>/.

A source given as (path, start, seconds) is a video cut to that window instead of copied whole.

  python3 scripts/weekly/assets.py 001
"""
import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PLAYGROUND = next(p for p in ROOT.parents if (p / "lucasgame-academy").is_dir())


def load_shots(ep: str):
    spec = importlib.util.spec_from_file_location(f"weekly_{ep}_shots", ROOT / "scripts/weekly" / ep / "shots.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


if __name__ == "__main__":
    ep = sys.argv[1]
    pub = ROOT / "public/weekly" / ep
    for dest, src in load_shots(ep).ASSETS.items():
        window = None
        if isinstance(src, tuple):
            src, *window = src
        source, target = PLAYGROUND / src, pub / dest
        if not source.exists():
            raise SystemExit(f"missing: {source}")
        if target.exists() and (window or target.stat().st_size == source.stat().st_size):
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        if window:
            subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", str(window[0]), "-i", str(source), "-t", str(window[1]),
                            "-an", "-c:v", "libx264", "-crf", "16", "-preset", "slow", "-pix_fmt", "yuv420p", str(target)], check=True)
        else:
            shutil.copy2(source, target)
        print(f"{dest} <- {src}" + (f" [{window[0]}s +{window[1]}s]" if window else ""))
