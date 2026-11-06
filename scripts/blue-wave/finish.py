#!/usr/bin/env python3
"""Prepare final shots as sharpened clips arrive; render after draft review.

This is the second heavy worker. The first is the single Real-ESRGAN worker.
All alignment, interpolation, rendering, and checks here run sequentially.
"""
import json, os, pathlib, subprocess, sys, time
import walk

HERE=pathlib.Path(__file__).resolve().parent
DATA=pathlib.Path(walk.DATA)

def main():
    gate=DATA/"film/jobs/draft-reviewed.json"
    print('Waiting for locally reviewed draft marker',gate,flush=True)
    while not gate.exists():
        if (DATA/"film/jobs/film.failed.json").exists(): raise RuntimeError('Draft failed; inspect draft.log')
        time.sleep(5)
    print('Draft reviewed; preparing sharpened clips as they complete',flush=True)
    assets=json.loads((DATA/"film/assets.json").read_text())
    spec=json.loads((HERE/"film/blue-wave.json").read_text())
    breath=json.loads((DATA/"music/analysis/levy.breath.json").read_text())
    win=walk.windows(spec); walk.MUSE="sharp"
    needed={pid:asset for pid,asset in assets.items() if "video" in asset}
    prepared=[]
    env={**os.environ,"ALIGN_DATA":str(DATA),"ALIGN_LONG":"3840"}
    while needed:
        progressed=False
        for pid,asset in list(needed.items()):
            source=DATA/"footage/muse/sharp"/f'{asset["clip_id"]}.mp4'
            ready=source.exists() and (pathlib.Path(str(source)+".done.json").exists() or pid=="blue-dancers")
            if not ready: continue
            dest=DATA/"footage/muse/aligned-sharp"/f'{pid}.mp4'
            meta=dest.with_suffix(".json")
            verified=dest.exists() and meta.exists() and json.loads(meta.read_text()).get("verified")
            if not verified:
                print('Register sharpened clip',pid,flush=True)
                subprocess.run([sys.executable,str(HERE/"align_video.py"),pid,str(source),"--to","photo" if "photo" in asset else "painting","--out",str(dest)],env=env,check=True)
                report=json.loads(meta.read_text()); report["verified"]=True; meta.write_text(json.dumps(report,indent=2))
            for i,s in enumerate(spec["shots"]):
                if s["src"] not in [f"muse:{pid}",f"rawmuse:{pid}"]: continue
                a,b,xin,xout=win[i]
                print('Prepare final interpolation',s["id"],flush=True)
                sh=walk.Shot(s,[],breath,a/30,b/30,False,xin/30,xout/30)
                sh.close()
            prepared.append(pid); del needed[pid]; progressed=True
            (DATA/"film/jobs/final-preparation.json").write_text(json.dumps({"prepared":prepared,"waiting":list(needed)},indent=2))
        if not progressed:
            failed=DATA/"film/jobs/upscale.failed.json"
            if failed.exists(): raise RuntimeError('Sharpening failed: '+failed.read_text())
            time.sleep(5)
    if not (DATA/"film/jobs/upscale.done.json").exists():
        while not (DATA/"film/jobs/upscale.done.json").exists(): time.sleep(1)
    print('All 9 final clips registered and interpolated; rendering master',flush=True)
    subprocess.run([sys.executable,"-u",str(HERE/"film.py"),"--muse","sharp"],check=True)

if __name__=="__main__": main()
