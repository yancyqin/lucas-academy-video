#!/usr/bin/env python3
"""Inventory only the approved material, and make visual contact sheets."""
import json, os, pathlib, subprocess
import cv2
from PIL import Image, ImageDraw, ImageOps

DATA = pathlib.Path(os.environ.get("BLUE_WAVE_DATA", "/Users/yqin/repo/playground/lucas-academy-video-data/blue-wave"))
ASSETS = [
    ("great-wave", "01-great-wave", "real-great-wave-4k.png"),
    ("impression-sunrise", "../existing/le-havre-dawn-muse-original", None),
    ("blue-dancers-orsay", "02-blue-dancers-orsay-dance", "real-blue-dancers-orsay-4k.png"),
    ("blue-dancers", "blue-dancers-vertical", "real-blue-dancers-vertical-4k.png"),
    ("rhone", "03-rhone", "real-rhone-4k.png"),
    ("kramskoi-moonlit", "04-kramskoi-moonlit", None),
    ("shalott", "05-shalott", None),
    ("whistler-chelsea", None, None),
    ("miranda", "07-miranda", None),
    ("liberty", None, None),
    ("wanderer-extended", "09-wanderer", None),
]

def probe(path):
    return json.loads(subprocess.run(["ffprobe","-v","error","-show_streams","-show_format","-of","json",str(path)],capture_output=True,text=True,check=True).stdout)

def tile(im, label, size=(420,300)):
    out=Image.new("RGB",(size[0],size[1]+30),(28,29,33))
    view=ImageOps.contain(im.convert("RGB"),size,Image.Resampling.LANCZOS)
    out.paste(view,((size[0]-view.width)//2,(size[1]-view.height)//2))
    ImageDraw.Draw(out).text((8,size[1]+7),label,fill="white")
    return out

def main():
    (DATA/"codex/extended-wanderer.png").exists() or (_ for _ in ()).throw(FileNotFoundError("extended wanderer"))
    Image.open(DATA/"codex/extended-wanderer.png").convert("RGB").save(DATA/"art/wanderer-extended.jpg",quality=95)
    rows=[]; manifest={}
    for pid,cid,photo in ASSETS:
        art=DATA/f"art/{pid}.jpg"
        im=Image.open(art)
        record={"art":str(art),"art_size":list(im.size)}
        tiles=[tile(im,pid)]
        if photo:
            source=DATA/"codex"/photo
            link=DATA/"real"/f"{pid}-real.png"
            if not link.exists(): link.symlink_to(source)
            record["photo"]=str(source)
        if cid:
            path=(DATA/"footage/muse"/f"{cid}.mp4").resolve()
            meta=probe(path); stream=next(s for s in meta["streams"] if s["codec_type"]=="video")
            record.update({"video":str(path),"clip_id":path.stem,"video_size":[stream["width"],stream["height"]],"frames":int(stream["nb_frames"]),"duration":float(meta["format"]["duration"]),"fps":stream["r_frame_rate"]})
            cap=cv2.VideoCapture(str(path))
            for f in [0,int(stream["nb_frames"])//2,int(stream["nb_frames"])-1]:
                cap.set(cv2.CAP_PROP_POS_FRAMES,f); ok,frame=cap.read()
                if not ok: raise RuntimeError((path,f))
                tiles.append(tile(Image.fromarray(cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)),f'{path.stem} frame {f}'))
            cap.release()
        while len(tiles)<4: tiles.append(tile(im,"painting only"))
        row=Image.new("RGB",(1680,330))
        for i,t in enumerate(tiles): row.paste(t,(i*420,0))
        rows.append(row); manifest[pid]=record
        print(pid,record,flush=True)
    sheet=Image.new("RGB",(1680,330*len(rows)))
    for i,row in enumerate(rows): sheet.paste(row,(0,330*i))
    sheet.save(DATA/"film/check/source-contact.jpg",quality=88)
    (DATA/"film/assets.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2))

if __name__=="__main__": main()
