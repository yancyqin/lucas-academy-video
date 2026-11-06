#!/usr/bin/env python3
"""Register first frames, reusing the owner's image registration routines."""
import argparse, json, os, pathlib, subprocess, sys
from PIL import Image

HERE=pathlib.Path(__file__).resolve().parent
DATA=pathlib.Path(os.environ.get("BLUE_WAVE_DATA", "/Users/yqin/repo/playground/lucas-academy-video-data/blue-wave"))

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--sharp",action="store_true"); a=ap.parse_args()
    env={**os.environ,"ALIGN_DATA":str(DATA),"ALIGN_LONG":"3840"}
    photos=["great-wave","blue-dancers-orsay","rhone","blue-dancers"]
    report=DATA/"real/aligned/report.json"
    if not report.exists():
        subprocess.run([sys.executable,str(HERE/"../debussy-impressions/align.py"),*photos],env=env,check=True)
    assets=json.loads((DATA/"film/assets.json").read_text())
    rep=json.loads(report.read_text())
    for pid,asset in assets.items():
        if "video" not in asset: continue
        if pid not in rep:
            w,h=asset["art_size"]; scale=3840/max(w,h)
            rep[pid]={"out_size":[round(w*scale)&~1,round(h*scale)&~1],"reference":"painting"}
    report.write_text(json.dumps(rep,ensure_ascii=False,indent=2))
    for pid,asset in assets.items():
        if "video" not in asset: continue
        source=DATA/"footage/muse/sharp"/f'{asset["clip_id"]}.mp4' if a.sharp else pathlib.Path(asset["video"])
        if not a.sharp and pid=="blue-dancers": source=DATA/"footage/muse/sharp/blue-dancers-vertical.mp4"
        dest=DATA/f'footage/muse/aligned-{"sharp" if a.sharp else "soft"}/{pid}.mp4'
        if dest.exists() and dest.with_suffix(".json").exists():
            existing=json.loads(dest.with_suffix(".json").read_text())
            if existing.get("verified"): continue
        subprocess.run([sys.executable,str(HERE/"align_video.py"),pid,str(source),"--to","photo" if pid in photos else "painting","--out",str(dest)],env=env,check=True)
        meta=json.loads(dest.with_suffix(".json").read_text()); meta["verified"]=True
        dest.with_suffix(".json").write_text(json.dumps(meta,ensure_ascii=False,indent=2))

if __name__=="__main__": main()
