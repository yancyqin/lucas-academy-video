#!/usr/bin/env python3
"""Run a restartable local film stage with explicit success/failure markers."""
import json, os, pathlib, subprocess, sys, time, traceback

DATA = pathlib.Path(os.environ.get("BLUE_WAVE_DATA", "/Users/yqin/repo/playground/lucas-academy-video-data/blue-wave"))
HERE = pathlib.Path(__file__).resolve().parent
CLIPS = ["01-great-wave", "02-blue-dancers-orsay-dance", "03-rhone", "04-kramskoi-moonlit", "05-shalott", "07-miranda", "09-wanderer", str(DATA / "footage/existing/le-havre-dawn-muse-original.mp4")]

if __name__ == "__main__":
    stage, *args = sys.argv[1:]
    base = DATA / "film/jobs" / stage
    base.parent.mkdir(parents=True, exist_ok=True)
    start = time.time()
    base.with_suffix(".running.json").write_text(json.dumps({"pid": os.getpid(), "start": start}))
    try:
        command = ([sys.executable, "-u", str(HERE / "upscale_clips.py"), *CLIPS] if stage == "upscale" else
                   [sys.executable, "-u", str(HERE / f"{stage}.py"), *args])
        subprocess.run(command, check=True)
        base.with_suffix(".done.json").write_text(json.dumps({"seconds": time.time()-start, "command": command}, indent=2))
        base.with_suffix(".failed.json").unlink(missing_ok=True)
    except BaseException:
        base.with_suffix(".failed.json").write_text(traceback.format_exc())
        raise
    finally:
        base.with_suffix(".running.json").unlink(missing_ok=True)
