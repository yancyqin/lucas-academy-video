#!/usr/bin/env python3
"""Choose musical accents, registered framing and exact dissolve windows."""
import json, os, pathlib
from PIL import Image
import walk

HERE=pathlib.Path(__file__).resolve().parent
DATA=pathlib.Path(walk.DATA)

def main():
    onsets=json.loads((DATA/"music/analysis/levy.accents.json").read_text())["onsets"]
    snaps=[]
    def snap(target):
        eligible=[x for x in onsets if abs(x["t"]-target)<=1.5]
        strong=[x for x in eligible if x["score"]>=.65]
        best=min(strong,key=lambda x:abs(x["t"]-target)-.3*x["score"]) if strong else max(eligible,key=lambda x:x["score"])
        t=round(best["t"]*30)/30
        snaps.append({"target":target,"onset":best["t"],"actual":t,"score":best["score"],"delta":t-target})
        return t
    boundary={x:snap(x) for x in [29,58,88,117,145,174,205,228]}
    internal={x:snap(x) for x in [6.5,41,63,74.5,79,94,124,151,165,180,236,258]}
    assets=json.loads((DATA/"film/assets.json").read_text())
    portraits={"blue-dancers-orsay","blue-dancers","kramskoi-moonlit"}
    shots=[]
    def art(pid,at,**kw):
        src="img:"+str(DATA/"codex/extended-wanderer.png") if pid=="wanderer-extended" else f"art:{pid}"
        s={"id":pid+"-painting","section":kw.pop("section",pid),"at":at,"src":src,"xfade":2.8,"zoom":[1,1.035],**kw}
        if pid in portraits:
            s.update({"layout":"contain","zoom":[1,1]})
        if pid in ["shalott","whistler-chelsea","liberty","wanderer-extended"]: s["tint"]=.4
        shots.append(s); return s
    def pushed(sh):
        _,pid=sh["src"].split(":",1)
        if sh["src"].startswith("img:"): sw,shp=Image.open(pid).size
        else: sw,shp=assets[pid]["art_size"]
        crop=sh.get("crop",[0,0,1]); x,y,cw=crop; z=sh.get("zoom",[1,1])[-1]
        ch=cw*sw*1080/1920/shp
        return [x+(cw-cw/z)/2,y+(ch-ch/z)/2,cw/z]
    def video(pid,at,previous,source_out=10,**kw):
        s={"id":pid+"-moving","section":previous["section"],"at":at,"src":f"muse:{pid}","in":0,"out":source_out,"xfade":2.8,"hold":2.8,"zoom":[1,1],"speed_mode":"constant","crop":pushed(previous) if pid not in portraits else None,**kw}
        if pid in portraits:
            s.update({"src":f"rawmuse:{pid}","layout":"contain"})
            s.pop("crop",None)
        if "tint" in previous: s["tint"]=previous["tint"]
        shots.append(s); return s
    a=art("great-wave",0,section="S1",crop=[0,.10,1],zoom=[1,1.04])
    video("great-wave",internal[6.5],a,crop_to=[.01923077,.015,.96153846])
    a=art("impression-sunrise",boundary[29],section="S2",crop=[0,.12,1])
    video("impression-sunrise",internal[41],a,7,crop_to=[.01690821,.12,.96618357])
    a=art("blue-dancers-orsay",boundary[58],section="S3")
    video("blue-dancers-orsay",internal[63],a,10,**{"in":1.0})
    a=art("blue-dancers",internal[74.5],section="S3")
    video("blue-dancers",internal[79],a,6.5)
    a=art("rhone",boundary[88],section="S4",crop=[.006,.26,.978],zoom=[1,1.025])
    c=pushed(a); video("rhone",internal[94],a,crop_to=[c[0],.13,c[2]])
    a=art("kramskoi-moonlit",boundary[117],section="S5")
    video("kramskoi-moonlit",internal[124],a,8.5)
    a=art("shalott",boundary[145],section="S6",crop=[.025,.07,.93],zoom=[1,1.025])
    c=pushed(a); video("shalott",internal[151],a,8,crop_to=[c[0],.012,c[2]])
    art("whistler-chelsea",internal[165],section="S6",layout="contain",zoom=[1,1],breath=False,xfade=3)
    a=art("miranda",boundary[174],section="S7",crop=[.01,.04,.95],zoom=[1,1.025])
    c=pushed(a); video("miranda",internal[180],a,crop_to=[c[0],.008,c[2]])
    art("liberty",boundary[205],section="S8",crop=[0,0,1],crop_to=[.29,0,.45],zoom=[1,1],xfade=3)
    a=art("wanderer-extended",boundary[228],section="S9",crop=[0,0,1],zoom=[1,1.03],breath=False,xfade=3)
    video("wanderer-extended",internal[236],a,crop_to=[0,0,1])
    art("wanderer-extended",internal[258],section="S9",crop=[0,0,1],zoom=[1,1],breath=False,xfade=3,id="wanderer-final-painting",dissolve="fog_return")
    shots[0].pop("xfade",None)
    spec={"name":"蓝色浪潮","title":"蓝色浪潮 | 肖邦 夜曲 Op. 9, No. 2","title_en":"Blue Wave | Chopin Nocturne Op. 9, No. 2","piece":"levy","start":0,"end":271.47,"fade_in":2.5,"fade_out":7,"afade_in":0,"afade_out":3,"out_dir":"film","size":[1920,1080],"shots":shots,"accent_snaps":snaps,"section_boundaries":boundary,"revision":"2026-11-05: portraits remain centred; correct only Wanderer opening painting camera, restore approved Muse segment and return painting","notes":["Every portrait uses its own actual image bounds, fitted to full height and centred horizontally, with its own 40%-darkened blurred side fill. No shared registration canvas offsets.","After a true first-frame hold for the WHOLE dissolve, clips ease into constant motion over 0.75 seconds.","Wanderer sequence: the same original PNG with global camera movement and no brightness breath, then the approved Muse footage exactly as in v1, then return to the same PNG. Only the opening still is constrained to a fixed image."]}
    walk.windows(spec)
    dest=HERE/"film/blue-wave.json"; dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(spec,ensure_ascii=False,indent=2))
    (DATA/"film/blue-wave.json").write_text(dest.read_text())
    print(dest)
    for s in snaps: print(f"{s['target']:6.2f} -> {s['actual']:7.3f} score {s['score']:.3f} ({s['delta']:+.3f}s)")

if __name__=="__main__": main()
