"""run_all.py — prepare, check and render every piece of the Mozart sketchbook, a few at a time.

    python run_all.py [KEY ...]      default: all ten, longest first; logs in DATA/pieces/KEY/run.log

For each piece: piece.py prepare (analysis, beats, plans, config), a per-frame motion check of the tool (frame px, the
same check as the samples), then piece.py render -> DATA/segments/KEY.mp4.
"""
import pathlib, subprocess, sys
from concurrent.futures import ThreadPoolExecutor

DATA = pathlib.Path("/Users/yqin/repo/playground/lucas-academy-video-data/mozart-sketchbook")
PY = "/Users/yqin/repo/playground/lucas-academy-video/.venv-reframe/bin/python"
HERE = pathlib.Path(__file__).parent
CHECK = str(HERE / "motion_check.py")
ORDER = ["27", "17", "16", "15", "06", "01", "07", "20", "05", "10"]          # longest first


def one(key):
    log_path = DATA / f"pieces/{key}/run.log"; log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "w") as log:
        for step in (["prepare"], ["check"], ["render"]):
            if step == ["check"]:
                cmd = [PY, CHECK, str(DATA / f"pieces/{key}/config.json")]
            else:
                cmd = [PY, str(HERE / "piece.py"), key, step[0]]
            log.write(f"== {' '.join(step)}\n"); log.flush()
            r = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, cwd=HERE)
            if r.returncode != 0 and step != ["check"]:
                print(f"{key}: {step[0]} FAILED (see {log_path})", flush=True); return
    print(f"{key}: done", flush=True)


if __name__ == "__main__":
    keys = sys.argv[1:] or ORDER
    with ThreadPoolExecutor(max_workers=3) as ex: list(ex.map(one, keys))
