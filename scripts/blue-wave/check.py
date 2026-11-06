#!/usr/bin/env python3
"""Make inspectable sheets and validate actual media rather than exit codes."""
import argparse, json, pathlib, subprocess
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageOps
import walk

HERE=pathlib.Path(__file__).resolve().parent
DATA=pathlib.Path(walk.DATA)

def tile(frame,label,w=480,h=270):
    im=Image.fromarray(frame) if isinstance(frame,np.ndarray) else frame
    out=Image.new("RGB",(w,h+30),(26,27,31))
    im=ImageOps.contain(im.convert("RGB"),(w,h),Image.Resampling.LANCZOS)
    out.paste(im,((w-im.width)//2,(h-im.height)//2))
    ImageDraw.Draw(out).text((8,h+8),label,fill="white")
    return out

def sheet(tiles,path,columns=3):
    w,h=tiles[0].size; rows=(len(tiles)+columns-1)//columns
    im=Image.new("RGB",(w*columns,h*rows),(26,27,31))
    for i,t in enumerate(tiles): im.paste(t,((i%columns)*w,(i//columns)*h))
    im.save(path,quality=92)

def preflight(muse="soft"):
    spec=json.loads((HERE/"film/blue-wave.json").read_text()); walk.MUSE=muse
    breath=json.loads((DATA/"music/analysis/levy.breath.json").read_text())
    win=walk.windows(spec); dest=DATA/"film/check"; dest.mkdir(exist_ok=True,parents=True)
    thumbnails=[]; rendered=[]; centered=[]
    for i,s in enumerate(spec["shots"]):
        a,b,xin,xout=win[i]
        sh=walk.Shot(s,[],breath,a/30,b/30,True,xin/30,xout/30,prepare_cache=False)
        if sh.layout=="contain":
            x,y,w,h=sh.report["foreground_bounds"]
            if y!=0 or h!=sh.h or abs(x-(sh.w-x-w))>1:
                raise RuntimeError(f'Foreground is not full-height and centred: {s["id"]} {x,y,w,h}')
            centered.append({"id":s["id"],"bounds":sh.report["foreground_bounds"],"output":[sh.w,sh.h]})
        frames=[sh.frame(k) for k in [0,sh.n//2,sh.n-1]]
        strip=[tile(f,f'{s["id"]}: {label}') for f,label in zip(frames,["start","middle","end"])]
        sheet(strip,dest/f'{i+1:02d}-{s["id"]}-framing.jpg')
        rendered.append(sh)
        thumbnails.append(tile(frames[1],f'{i+1:02d} {s["id"]}',w=384,h=216))
        if sh.kind=="footage" and i>0:
            prev=rendered[i-1]
            painting=prev.frame(prev.n-prev.xout)
            first=sh.frame(0)
            blend=cv2.addWeighted(painting,.5,first,.5,0)
            sheet([tile(painting,"painting at dissolve start"),tile(first,"held first usable video frame"),tile(blend,"50% blend")],dest/f'{i+1:02d}-{s["id"]}-transition.jpg')
            if xin:
                held_end=sh.frame(xin-1)
                if not np.array_equal(first,held_end): raise RuntimeError(f'Video/camera moved during dissolve: {s["id"]}')
        sh.close()
    sheet(thumbnails,dest/"preflight-overview.jpg",columns=4)
    # Check the copied tint's formula against the original implementation.
    from tint import tint
    rng=np.random.default_rng(42); colors=rng.integers(0,256,(50,50,3),dtype=np.uint8)
    delta=np.abs(walk.blue_filter(colors,.4).astype(int)-np.array(tint(Image.fromarray(colors),.4)).astype(int)).max()
    if delta>1: raise RuntimeError(f'Tint formula error: {delta}')
    wanderer=[s for s in spec["shots"] if s["section"]=="S9"]
    original="img:"+str(DATA/"codex/extended-wanderer.png")
    if [s["src"] for s in wanderer]!=[original,"muse:wanderer-extended",original] or wanderer[0].get("breath",True):
        raise RuntimeError('Wanderer must be opening painting camera -> approved Muse -> same original painting')
    (dest/"preflight.json").write_text(json.dumps({"shots":len(rendered),"first_frame_holds":"all exact across full dissolve", "tint_max_channel_difference":int(delta),"muse":muse,"centered_foregrounds":centered,"wanderer_sequence":[s["src"] for s in wanderer]},indent=2))
    print('Preflight verified',len(rendered),'shots; exact first-frame holds; tint delta',delta,flush=True)

def frame_at(cap,t):
    cap.set(cv2.CAP_PROP_POS_MSEC,t*1000); ok,f=cap.read()
    if not ok: raise RuntimeError(f'Cannot decode video at {t}')
    return cv2.cvtColor(f,cv2.COLOR_BGR2RGB)

def verify(path):
    from importlib.util import spec_from_file_location,module_from_spec
    ms=spec_from_file_location("blue_wave_normalize",HERE/"../debussy-impressions/normalize.py"); norm=module_from_spec(ms); ms.loader.exec_module(norm)
    spec=json.loads((HERE/"film/blue-wave.json").read_text())
    meta=json.loads(subprocess.run(["ffprobe","-v","error","-count_frames","-show_streams","-show_format","-of","json",str(path)],capture_output=True,text=True,check=True).stdout)
    v=next(s for s in meta["streams"] if s["codec_type"]=="video"); a=next(s for s in meta["streams"] if s["codec_type"]=="audio")
    count=int(v["nb_read_frames"]); expected=round(spec["end"]*30)
    if count!=expected or v["r_frame_rate"]!="30/1": raise RuntimeError(f'Frame count/fps: {count}/{expected}, {v["r_frame_rate"]}')
    if abs(float(v["duration"])-float(a["duration"]))>1/30+.001: raise RuntimeError('A/V duration mismatch')
    if v["pix_fmt"]!="yuv420p" or a["sample_rate"]!="48000" or a["channels"]!=2: raise RuntimeError('Delivery format mismatch')
    if [v["width"],v["height"]] not in [[1920,1080],[960,540]]: raise RuntimeError('Unexpected image size')
    I,LRA,TP=norm.ebur128(str(path))
    if abs(I+18)>.5 or TP>-1: raise RuntimeError(f'Loudness failed: {I} LUFS / {TP} dBTP')
    # Full low-resolution decode checks every frame for black flashes and gross
    # frame-to-frame luma jumps, with no dependence on container frame metadata.
    decoder=subprocess.Popen(["ffmpeg","-v","error","-threads","2","-i",str(path),"-vf","scale=96:54","-pix_fmt","rgb24","-f","rawvideo","-"],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    means=[]; diffs=[]; prev=None
    while True:
        raw=decoder.stdout.read(96*54*3)
        if not raw: break
        if len(raw)!=96*54*3: raise RuntimeError('Partial decoded frame')
        im=np.frombuffer(raw,np.uint8).reshape(54,96,3)
        means.append(float(im.mean()))
        diffs.append(0 if prev is None else float(np.abs(im.astype(np.float32)-prev).mean()))
        prev=im.astype(np.float32)
    err=decoder.stderr.read().decode(); code=decoder.wait()
    if code or err.strip() or len(means)!=expected: raise RuntimeError(f'Full decode failed: {code}, {len(means)}, {err}')
    interior=[i/30 for i,x in enumerate(means) if 2.5<i/30<spec["end"]-7 and x<2]
    jumps=[{"time":i/30,"mean_delta":d} for i,d in enumerate(diffs) if d>16]
    if interior: raise RuntimeError(f'Unexpected black frames: {interior[:10]}')
    if jumps: raise RuntimeError(f'Potential flash/cut: {jumps[:10]}')
    dest=DATA/"film/check"; cap=cv2.VideoCapture(str(path))
    # Whistler must be completely static, including its blurred side fill.
    whistler=next(s for s in spec["shots"] if s["id"]=="whistler-chelsea-painting")
    wi=spec["shots"].index(whistler); ww=walk.windows(spec)[wi]
    static_times=[(ww[0]+ww[2]+45)/30,(ww[0]+ww[1])/60,(ww[1]-ww[3]-45)/30]
    static_frames=[cv2.resize(frame_at(cap,t),(256,144)).astype(np.float32) for t in static_times]
    static_delta=max(float(np.abs(f-static_frames[0]).mean()) for f in static_frames[1:])
    if static_delta>1: raise RuntimeError(f'Whistler moved/breathed: mean pixel change {static_delta}')
    thumbs=[]
    for t in list(range(0,271,10))+[271.4]:
        thumbs.append(tile(frame_at(cap,t),f'{t:06.2f}s',w=384,h=216))
    suffix="draft" if "draft" in path.stem else ("review" if "review" in path.stem else "final")
    sheet(thumbs,dest/f"{suffix}-every-10s.jpg",columns=4)
    bounds=[0]+[float(spec["section_boundaries"][str(x)]) for x in [29,58,88,117,145,174,205,228]]+[spec["end"]]
    for i,(start,end) in enumerate(zip(bounds[:-1],bounds[1:])):
        times=[min(end-.1,start+2),(start+end)/2,max(start,end-2)]
        sheet([tile(frame_at(cap,t),f'S{i+1} {t:.3f}s') for t in times],dest/f'{suffix}-S{i+1}.jpg')
    sheet([tile(frame_at(cap,t),f'{t:.3f}s',w=640,h=360) for t in [232,240,248,256,264,270]],dest/f'{suffix}-ending.jpg',columns=3)
    # Only the OPENING painting is fixed to a still. The approved Muse section
    # must remain present, followed by the return to the original painting.
    wi=next(i for i,s in enumerate(spec["shots"]) if s["section"]=="S9")
    a0,b0,xi,xo=walk.windows(spec)[wi]
    breath=json.loads((DATA/"music/analysis/levy.breath.json").read_text())
    expected_shot=walk.Shot(spec["shots"][wi],[],breath,a0/30,b0/30,v["width"]==960,xi/30,xo/30,prepare_cache=False)
    still_errors=[]
    for t in [230,231.5,233]:
        expected_frame=expected_shot.frame(round(t*30)-a0)
        actual=frame_at(cap,t)
        still_errors.append(float(np.abs(expected_frame.astype(np.float32)-actual.astype(np.float32)).mean()))
    expected_shot.close()
    if max(still_errors)>5: raise RuntimeError(f'Opening painting differs from a global still-image camera movement: {still_errors}')
    muse_errors=[]
    reference=DATA/'film/archive/2026-11-05-v1/蓝色浪潮.mp4'
    if reference.exists():
        ref_cap=cv2.VideoCapture(str(reference))
        for t in [240,248,255]:
            original_frame=cv2.resize(frame_at(ref_cap,t),(960,540))
            current_frame=cv2.resize(frame_at(cap,t),(960,540))
            muse_errors.append(float(np.abs(current_frame.astype(np.float32)-original_frame.astype(np.float32)).mean()))
        ref_cap.release()
        if max(muse_errors)>5: raise RuntimeError(f'Approved Wanderer Muse section changed or is missing: {muse_errors}')
    cap.release()
    report={"file":str(path),"duration":float(meta["format"]["duration"]),"video_duration":float(v["duration"]),"audio_duration":float(a["duration"]),"decoded_frames":len(means),"resolution":[v["width"],v["height"]],"fps":v["r_frame_rate"],"lufs":I,"lra":LRA,"true_peak_dbtp":TP,"bytes":path.stat().st_size,"unexpected_black_frames":interior,"potential_flashes":jumps,"max_frame_mean_absolute_difference":max(diffs),"whistler_static_mean_pixel_difference":static_delta,"wanderer_opening_still_render_errors":still_errors,"wanderer_muse_reference_errors":muse_errors,"wanderer_sequence":"painting-muse-painting","source_check":"all portraits full-height and centred; opening painting uses only global camera movement; approved Muse retained then same painting returns","ffprobe":meta}
    (dest/f"{suffix}-validation.json").write_text(json.dumps(report,ensure_ascii=False,indent=2))
    print('Verified actual delivery:',path,count,'frames',I,'LUFS',TP,'dBTP',flush=True)
    return report

if __name__=="__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("--preflight",action="store_true"); ap.add_argument("--muse",default="soft"); ap.add_argument("file",nargs="?")
    a=ap.parse_args()
    if a.preflight: preflight(a.muse)
    if a.file: verify(pathlib.Path(a.file))
