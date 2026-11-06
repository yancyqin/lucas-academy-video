#!/usr/bin/env python3
"""Re-render the owner-requested framing and restored Muse ending revision."""
import pathlib, subprocess, sys

HERE=pathlib.Path(__file__).resolve().parent

if __name__=="__main__":
    for flags in [["--draft","--muse","soft"],["--muse","sharp"]]:
        subprocess.run([sys.executable,"-u",str(HERE/"film.py"),*flags],check=True)
