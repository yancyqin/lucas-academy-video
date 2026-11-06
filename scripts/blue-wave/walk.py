#!/usr/bin/env python3
"""蓝色浪潮: a continuous 30-fps film of paintings and slow Muse footage.

Adapted from the copied scripts/gymnopedies/walk.py. Clips hold their first usable
frame through the complete incoming dissolve, then ease into constant playback.
Motion-compensated 100-fps source caches are streamed one frame at a time.
Paintings have gentle music-derived brightness and optional crop/zoom motion;
per-shot breath=False and zoom=[1,1] make Whistler strictly static. Per-shot tint
uses the exact blue-wave/tint.py formula on every output frame.

The JSON spec retains the Gymnopédies format, adding registered_portrait layout:
painting and full portrait clip share canonical coordinates, with their own
blurred, 40%-darkened background. Matrix columns map normalized source pixels
into the common canvas. Arbitrary still paths use img:/absolute/path.

Usage: walk.py SPEC.json [--draft] [--muse sharp|soft]
"""
import argparse, hashlib, json, os, subprocess, time
from pathlib import Path
import cv2
import numpy as np

# Adapted from the copied Gymnopédies renderer; all caches and edits stay here.
DATA = os.environ.get("BLUE_WAVE_DATA", "/Users/yqin/repo/playground/lucas-academy-video-data/blue-wave")
MUSE = "sharp"
W, H, FPS, IFPS = 1920, 1080, 30, 100
cv2.setNumThreads(2)

def probe(path):
    j=json.loads(subprocess.run(["ffprobe","-v","error","-select_streams","v:0","-show_entries","stream=width,height,r_frame_rate,nb_frames:format=duration","-of","json",str(path)],capture_output=True,text=True,check=True).stdout)
    s=j["streams"][0]
    return s["width"],s["height"],float(j["format"]["duration"])

def src_path(src):
    kind,ref=src.split(":",1)
    if kind=="art": return f"{DATA}/art/{ref}.jpg"
    if kind=="muse": return f"{DATA}/footage/muse/aligned-{MUSE}/{ref}.mp4"
    if kind=="rawmuse":
        asset=json.load(open(f"{DATA}/film/assets.json"))[ref]
        if MUSE=="sharp" or ref=="blue-dancers": return f"{DATA}/footage/muse/sharp/{asset['clip_id']}.mp4"
        return asset["video"]
    return ref

def ease(u): return np.clip(u,0,1)**2*(3-2*np.clip(u,0,1))

def windows(spec):
    n=round((spec["end"]-spec["start"])*FPS)
    out=[]
    for i,sh in enumerate(spec["shots"]):
        xin=round(sh.get("xfade",0)*FPS) if i else 0
        nxt=spec["shots"][i+1] if i+1<len(spec["shots"]) else None
        xout=round(nxt.get("xfade",0)*FPS) if nxt else 0
        a=max(0,round((sh["at"]-spec["start"])*FPS)-xin//2)
        b=min(n,round((nxt["at"]-spec["start"])*FPS)+xout-xout//2) if nxt else n
        out.append((a,b,xin,xout))
    for k in range(n):
        live=[i for i,(a,b,_,_) in enumerate(out) if a<=k<b]
        if not 1<=len(live)<=2: raise ValueError(f"Gap or triple overlap at frame {k}: {live}")
    return out

def blue_filter(frame,strength):
    if not strength: return frame
    rgb=frame.astype(np.float32)
    lum=(rgb[:,:,0]*.299+rgb[:,:,1]*.587+rgb[:,:,2]*.114)/255
    low=np.minimum(lum/.45,1)[...,None]
    high=np.maximum((lum-.45)/.55,0)[...,None]
    tone=np.array([10,20,44],np.float32)+low*np.array([68,92,122],np.float32)+high*np.array([154,129,89],np.float32)
    return np.clip((1-strength)*rgb+strength*tone+.5,0,255).astype(np.uint8)

def dissolve(f0,f1,progress,mode=None):
    alpha=float(ease(progress))
    if mode!="fog_return": return cv2.addWeighted(f0,1-alpha,f1,alpha,0)
    # The Muse camera ends with the traveller at the right; the original puts
    # him in the centre. A soft, spatially staggered cross-dissolve replaces the
    # outgoing figure with existing painted mist before revealing the original
    # figure. It uses only the two existing frames and avoids a double person.
    h,w=f0.shape[:2]; yy,xx=np.ogrid[:h,:w]
    def oval(cx,cy,rx,ry):
        r=np.sqrt(((xx/w-cx)/rx)**2+((yy/h-cy)/ry)**2)
        return np.clip((1.2-r)/.25,0,1).astype(np.float32)
    old=oval(.86,.65,.15,.40); new=oval(.50,.62,.09,.32)
    a=np.full((h,w),alpha,np.float32)
    a=np.maximum(a,old*float(ease(progress/.46)))
    delayed=float(ease((progress-.48)/.52))
    a=a*(1-new)+delayed*new
    a=a[...,None]
    return np.clip(f0.astype(np.float32)*(1-a)+f1.astype(np.float32)*a+.5,0,255).astype(np.uint8)

def raw_box(sw,sh,crop):
    if crop:
        x,y,cw=crop; cw*=sw; ch=cw*H/W
        x=(sw-cw)/2 if x is None else x*sw
        y=(sh-ch)/2 if y is None else y*sh
    else:
        cw=min(sw,sh*W/H); ch=cw*H/W; x=(sw-cw)/2; y=(sh-ch)/2
    return np.array([np.clip(x,0,max(0,sw-cw)),np.clip(y,0,max(0,sh-ch)),cw,ch],np.float64)

def zoom_box(box,z):
    x,y,w,h=box
    return np.array([x+(w-w/z)/2,y+(h-h/z)/2,w/z,h/z])

def viewport(im,box,size):
    x,y,w,h=box; ow,oh=size
    M=np.float32([[ow/w,0,-x*ow/w],[0,oh/h,-y*oh/h]])
    return cv2.warpAffine(im,M,(ow,oh),flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE)

def contain_bounds(sw,sh,ow,oh):
    scale=min(ow/sw,oh/sh); fw,fh=round(sw*scale),round(sh*scale)
    return (ow-fw)//2,(oh-fh)//2,fw,fh

def portrait(im,size,rect=None):
    ow,oh=size
    if rect:
        x,y,w,h=rect; sh,sw=im.shape[:2]
        im=im[round(y*sh):round((y+h)*sh),round(x*sw):round((x+w)*sw)]
    sh,sw=im.shape[:2]
    # A low-resolution blurred backdrop is derived from this very frame, darkened 40%.
    bg=viewport(im,raw_box(sw,sh,None),(max(2,ow//4),max(2,oh//4)))
    bg=cv2.GaussianBlur(bg,(0,0),max(8,ow/110))
    bg=cv2.resize(bg,(ow,oh),interpolation=cv2.INTER_LINEAR)
    bg=(bg.astype(np.float32)*.6+.5).astype(np.uint8)
    x,y,fw,fh=contain_bounds(sw,sh,ow,oh)
    scale=fw/sw
    fore=cv2.resize(im,(fw,fh),interpolation=cv2.INTER_AREA if scale<1 else cv2.INTER_CUBIC)
    bg[y:y+fh,x:x+fw]=fore
    return bg

def registered_portrait(im,size,canvas,matrix):
    """Fit painting and the WHOLE portrait clip in a common registered canvas.

    The enlarged photo's additional top/bottom are preserved; no reflected body
    parts or synthetic edge bands are shown. Empty canvas uses the same blurred,
    darkened image as the side fill.
    """
    ow,oh=size; sh,sw=im.shape[:2]
    bg=viewport(im,raw_box(sw,sh,None),(max(2,ow//4),max(2,oh//4)))
    bg=cv2.resize(cv2.GaussianBlur(bg,(0,0),max(8,ow/110)),(ow,oh))
    bg=(bg.astype(np.float32)*.6+.5).astype(np.uint8)
    x0,y0,x1,y1=canvas; scale=min(ow/(x1-x0),oh/(y1-y0))
    offset=np.array([(ow-(x1-x0)*scale)/2-x0*scale,(oh-(y1-y0)*scale)/2-y0*scale])
    M=np.array(matrix,np.float64).copy()
    M[:,0]/=sw; M[:,1]/=sh; M*=scale; M[:,2]+=offset
    fore=cv2.warpAffine(im,M.astype(np.float32),(ow,oh),flags=cv2.INTER_LINEAR)
    mask=cv2.warpAffine(np.full((sh,sw),255,np.uint8),M.astype(np.float32),(ow,oh),flags=cv2.INTER_LINEAR)
    alpha=mask.astype(np.float32)[...,None]/255
    return np.clip(fore.astype(np.float32)*alpha+bg.astype(np.float32)*(1-alpha)+.5,0,255).astype(np.uint8)

def source_time(n,source_range,hold=0,ease_seconds=.75):
    t=np.arange(n)/FPS
    v=np.ones(n,np.float64)
    v[t<hold]=0
    sel=(t>=hold)&(t<hold+ease_seconds)
    v[sel]=ease((t[sel]-hold)/ease_seconds)
    tau=np.concatenate([[0],np.cumsum(v[:-1])])/FPS
    if tau[-1]<=0: raise ValueError("No moving time in footage shot")
    tau*=source_range/tau[-1]
    speed=np.diff(tau)*FPS
    after=speed[t[:-1]>=hold+ease_seconds]
    if len(after) and after.min()<.7*after.mean()-1e-6:
        raise ValueError("Speed fell below required moving floor")
    return tau,{"min_after_ease":float(after.min()) if len(after) else 0,"max":float(speed.max()),"moving_mean":float(source_range/max((n-1)/FPS-hold,1e-6)),"hold":hold,"ease_in":ease_seconds}

def interpolated(path,a,length,size):
    key=hashlib.sha1(json.dumps([str(path),os.path.getmtime(path),a,length,size,IFPS,"endpoint-pad-v2"]).encode()).hexdigest()[:16]
    out=Path(DATA)/f"footage/cache/{Path(path).stem}-{key}.mp4"
    out.parent.mkdir(parents=True,exist_ok=True)
    if out.exists():
        try:
            w,h,d=probe(out)
            if (w,h)==tuple(size) and d>=length-.03: return str(out)
        except (ValueError,subprocess.CalledProcessError): pass
    vf=f"scale={size[0]}:{size[1]}:flags=lanczos,tpad=stop_mode=clone:stop_duration=0.20,minterpolate=fps={IFPS}:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1,trim=duration={length+.02:.6f},setpts=PTS-STARTPTS"
    print(f"  interpolate {Path(path).stem}: {size}, {length:.2f}s @ {IFPS}fps",flush=True)
    tmp=str(out)+".part.mp4"
    subprocess.run(["ffmpeg","-v","error","-y","-threads","2","-ss",str(a),"-i",str(path),"-an","-vf",vf,"-filter_threads","2","-t",str(length+.02),"-c:v","libx264","-threads","3","-crf","12","-preset","fast","-pix_fmt","yuv420p","-progress",str(out)+".progress","-stats_period","5",tmp],check=True)
    w,h,d=probe(tmp)
    if (w,h)!=tuple(size) or d<length-.03: raise RuntimeError(f"Invalid interpolation cache: {tmp}, {w,h,d}")
    os.replace(tmp,out)
    return str(out)

class Reader:
    def __init__(self,path,w,h):
        self.w,self.h=w,h; self.index=-1; self.cur=None; self.nxt=None; self.eof=False
        self.p=subprocess.Popen(["ffmpeg","-v","error","-threads","2","-i",str(path),"-f","rawvideo","-pix_fmt","rgb24","-"],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL)
        self.nxt=self._read(); self._advance()
    def _read(self):
        b=self.p.stdout.read(self.w*self.h*3)
        return np.frombuffer(b,np.uint8).reshape(self.h,self.w,3) if len(b)==self.w*self.h*3 else None
    def _advance(self):
        self.cur=self.nxt if self.nxt is not None else self.cur
        self.nxt=self._read(); self.index+=1
        if self.nxt is None: self.eof=True
    def frame(self,pos):
        k=int(pos)
        while self.index<k and not self.eof: self._advance()
        if self.cur is None: raise RuntimeError("Empty video stream")
        if self.eof or pos-k<1e-5: return self.cur
        return cv2.addWeighted(self.cur,1-(pos-k),self.nxt,pos-k,0)
    def close(self):
        if self.p.stdout: self.p.stdout.close()
        self.p.terminate(); self.p.wait()

class Shot:
    def __init__(self,spec,piece_ons,breath,t0,t1,draft,xin=0,xout=0,prepare_cache=True):
        self.spec,self.t0,self.t1=spec,t0,t1
        self.w,self.h=(W//2,H//2) if draft else (W,H)
        self.n=round((t1-t0)*FPS); self.xin=round(xin*FPS); self.xout=round(xout*FPS)
        self.path=src_path(spec["src"]); self.reader=None; self.kind="art" if spec["src"].split(":",1)[0] in ("img","art") else "footage"
        self.tint=spec.get("tint",0); self.layout=spec.get("layout","crop")
        if self.kind=="art":
            bgr=cv2.imread(self.path)
            if bgr is None: raise FileNotFoundError(self.path)
            self.img=cv2.cvtColor(bgr,cv2.COLOR_BGR2RGB); sh,sw=self.img.shape[:2]
            self.sw,self.sh=sw,sh; self.first=self.img
            t=t0+np.arange(self.n)/FPS
            b=np.interp(t*breath["fps"],np.arange(len(breath["b"])),breath["b"])
            self.light=.97+.06*b if spec.get("breath",True) else np.ones(self.n)
        else:
            sw,sh,dur=probe(self.path); self.sw,self.sh=sw,sh
            self.source_in=spec.get("in",0)
            source_out=min(spec.get("out",dur-1/24),dur-1/24)
            self.tau,self.speed_report=source_time(self.n,source_out-self.source_in,xin,.75)
            if self.layout in ("contain","registered_portrait"): scale=min(self.w/sw,self.h/sh)
            else:
                b0=raw_box(sw,sh,spec.get("crop")); b1=raw_box(sw,sh,spec.get("crop_to",spec.get("crop")))
                zoom=max(spec.get("zoom",[1,1])); scale=self.w/min(b0[2],b1[2])*zoom
            self.cache_wh=(max(2,round(sw*scale/2)*2),max(2,round(sh*scale/2)*2))
            cap=cv2.VideoCapture(self.path); cap.set(cv2.CAP_PROP_POS_MSEC,self.source_in*1000); ok,frame=cap.read(); cap.release()
            if not ok: raise RuntimeError(f"Cannot read first frame: {self.path}")
            self.first=cv2.resize(cv2.cvtColor(frame,cv2.COLOR_BGR2RGB),self.cache_wh,interpolation=cv2.INTER_AREA)
            if prepare_cache:
                path=interpolated(self.path,self.source_in,source_out-self.source_in,self.cache_wh)
                self.reader=Reader(path,*self.cache_wh)
            print(f"  {spec['src']}: {self.n/FPS:.2f}s, {self.source_in:.3f}..{source_out:.3f}s, {self.speed_report}",flush=True)
        self.report={"id":spec.get("id"),"source":self.path,"start":t0,"end":t1,"frames":self.n,"layout":self.layout,"crop":spec.get("crop"),"crop_to":spec.get("crop_to"),"zoom":spec.get("zoom",[1,1]),"tint":self.tint,"breath":spec.get("breath",True),"hold":xin if self.kind=="footage" else 0}
        if self.layout=="contain": self.report["foreground_bounds"]=list(contain_bounds(sw,sh,self.w,self.h))
        if self.kind=="footage": self.report.update({"in":self.source_in,"out":source_out,"speed":self.speed_report})
    def progress(self,k):
        if self.kind=="art": return float(ease((k-self.xin)/max(self.n-self.xin-self.xout-1,1)))
        return float(ease((k-self.xin)/max(self.n-self.xin-1,1)))
    def frame(self,k):
        k=min(max(0,k),self.n-1); u=self.progress(k)
        if self.kind=="art": im=self.img
        elif self.tau[k]<1e-7: im=self.first
        elif self.reader: im=self.reader.frame(self.tau[k]*IFPS)
        else:
            cap=cv2.VideoCapture(self.path); cap.set(cv2.CAP_PROP_POS_MSEC,(self.source_in+self.tau[k])*1000); ok,f=cap.read(); cap.release()
            if not ok: raise RuntimeError(self.path)
            im=cv2.resize(cv2.cvtColor(f,cv2.COLOR_BGR2RGB),self.cache_wh,interpolation=cv2.INTER_AREA)
        if self.layout=="registered_portrait": f=registered_portrait(im,(self.w,self.h),self.spec["canvas"],self.spec["matrix"])
        elif self.layout=="contain": f=portrait(im,(self.w,self.h),self.spec.get("rect"))
        else:
            sh,sw=im.shape[:2]
            a=raw_box(sw,sh,self.spec.get("crop")); b=raw_box(sw,sh,self.spec.get("crop_to",self.spec.get("crop")))
            z0,z1=self.spec.get("zoom",[1,1]); box=zoom_box(a+(b-a)*u,z0+(z1-z0)*u)
            f=viewport(im,box,(self.w,self.h))
        if self.kind=="art" and self.light[k]!=1: f=np.clip(f.astype(np.float32)*self.light[k]+.5,0,255).astype(np.uint8)
        return blue_filter(f,self.tint)
    def close(self):
        if self.reader: self.reader.close()

def render(spec,draft):
    global W,H
    W,H=spec.get("size",[1920,1080])
    piece=spec["piece"]; start=spec["start"]; end=spec["end"]
    breath=json.load(open(f"{DATA}/music/analysis/{piece}.breath.json"))
    win=windows(spec); n=round((end-start)*FPS); total=n/FPS
    out=Path(DATA)/spec.get("out_dir","film"); out.mkdir(parents=True,exist_ok=True)
    name=spec["name"]+("-draft" if draft else ""); w,h=(W//2,H//2) if draft else (W,H)
    video=out/f"{name}.video.part.mp4"
    enc=subprocess.Popen(["ffmpeg","-v","error","-y","-f","rawvideo","-pix_fmt","rgb24","-s",f"{w}x{h}","-r",str(FPS),"-i","-","-an","-c:v","libx264","-threads","4","-crf","22" if draft else "16","-preset","medium","-pix_fmt","yuv420p",str(video)],stdin=subprocess.PIPE)
    live={}; reports={}; tbegin=time.time()
    try:
        for k in range(n):
            frames=[]
            for i,(a,b,xin,xout) in enumerate(win):
                if a<=k<b:
                    if i not in live:
                        print(f"shot {i+1}/{len(win)} {spec['shots'][i]['id']} at {a/FPS:.3f}s",flush=True)
                        live[i]=Shot(spec["shots"][i],[],breath,start+a/FPS,start+b/FPS,draft,xin/FPS,xout/FPS)
                        reports[i]=live[i].report
                    f=live[i].frame(k-a)
                    weight=float(ease((k-a)/xin)) if xin and k<a+xin else 1.0
                    frames.append((f,weight,i,(k-a)/xin if xin else 1.))
                elif i in live and k>=b:
                    live.pop(i).close()
            if len(frames)==1: img=frames[0][0]
            elif len(frames)==2:
                (f0,_,_,_),(f1,_,idx,progress)=frames
                img=dissolve(f0,f1,progress,spec["shots"][idx].get("dissolve"))
            else: raise RuntimeError(f"Missing frame {k}")
            t=k/FPS; gain=1.
            if spec.get("fade_in",0): gain=min(gain,float(ease(t/spec["fade_in"])))
            if spec.get("fade_out",0): gain=min(gain,float(ease((total-1/FPS-t)/spec["fade_out"])))
            if gain<1: img=np.clip(img.astype(np.float32)*gain+.5,0,255).astype(np.uint8)
            enc.stdin.write(img.tobytes())
            if k%(FPS*10)==0:
                (out/f"{name}.progress.json").write_text(json.dumps({"frame":k,"frames":n,"seconds":t,"elapsed":time.time()-tbegin}))
        enc.stdin.close()
        if enc.wait()!=0: raise RuntimeError("Video encoding failed")
    finally:
        for sh in live.values(): sh.close()
        if enc.poll() is None:
            enc.stdin.close(); enc.terminate(); enc.wait()
    audio=Path(DATA)/f"music/normalized/{piece}.wav"
    final=out/f"{name}.mp4"; temp=out/f"{name}.part.mp4"
    af=[]
    if spec.get("afade_in",0): af.append(f"afade=t=in:st=0:d={spec['afade_in']}")
    if spec.get("afade_out",0): af.append(f"afade=t=out:st={total-spec['afade_out']:.8f}:d={spec['afade_out']}")
    cmd=["ffmpeg","-v","error","-y","-i",str(video),"-ss",str(start),"-i",str(audio),"-map","0:v:0","-map","1:a:0","-c:v","copy"]
    if af: cmd +=["-af",",".join(af)]
    cmd +=["-c:a","aac","-b:a","256k","-ar","48000","-ac","2","-t",f"{total:.8f}","-metadata","title="+spec.get("title",spec["name"]),"-movflags","+faststart",str(temp)]
    subprocess.run(cmd,check=True)
    meta=json.loads(subprocess.run(["ffprobe","-v","error","-show_streams","-show_format","-of","json",str(temp)],capture_output=True,text=True,check=True).stdout)
    vs=next(s for s in meta["streams"] if s["codec_type"]=="video")
    if int(vs["nb_frames"])!=n or abs(float(meta["format"]["duration"])-total)>1/FPS:
        raise RuntimeError("Final frame count or duration failed")
    os.replace(temp,final); video.unlink()
    report={"file":str(final),"size_bytes":final.stat().st_size,"frames":n,"duration":total,"wall_seconds":time.time()-tbegin,"shots":[reports[i] for i in sorted(reports)],"ffprobe":meta}
    (out/f"{name}.render.json").write_text(json.dumps(report,ensure_ascii=False,indent=2))
    print(f"Verified {final}: {n} frames, {total:.6f}s",flush=True)
    return final

if __name__=="__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("spec"); ap.add_argument("--draft",action="store_true"); ap.add_argument("--muse",choices=["sharp","soft"],default="sharp")
    a=ap.parse_args(); MUSE=a.muse
    render(json.load(open(a.spec)),a.draft)
