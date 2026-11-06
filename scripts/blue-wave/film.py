#!/usr/bin/env python3
"""Blue Wave delivery pipeline, adapted from the copied Gymnopédies assembler.

One continuous recording, without inter-piece gaps. Example:
  film.py --draft --muse soft
  film.py --muse sharp
"""
import argparse, json, pathlib, subprocess
import walk
from check import preflight,verify
from notes import write_notes

HERE=pathlib.Path(__file__).resolve().parent
DATA=pathlib.Path(walk.DATA)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--draft",action="store_true"); ap.add_argument("--muse",choices=["soft","sharp"],default="sharp"); ap.add_argument("--skip-render",action="store_true")
    a=ap.parse_args(); walk.MUSE=a.muse
    spec=json.loads((HERE/"film/blue-wave.json").read_text())
    preflight(a.muse)
    path=DATA/"film"/(spec["name"]+("-draft" if a.draft else "")+".mp4")
    if not a.skip_render: path=walk.render(spec,a.draft)
    verify(path)
    if not a.draft:
        review=DATA/"film/蓝色浪潮-review.mp4"
        tmp=DATA/"film/蓝色浪潮-review.part.mp4"
        subprocess.run(["ffmpeg","-v","error","-y","-i",str(path),"-map","0:v:0","-map","0:a:0","-c:v","libx264","-threads","4","-crf","23","-preset","medium","-pix_fmt","yuv420p","-c:a","copy","-movflags","+faststart",str(tmp)],check=True)
        tmp.replace(review); verify(review)
    write_notes()
    print("Completed",path,flush=True)

if __name__=="__main__": main()
