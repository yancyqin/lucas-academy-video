"""Restyle the existing Muse motion as graphite sketches on white paper."""
from concurrent.futures import ThreadPoolExecutor
import hashlib,json,shutil,subprocess,time
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'out/why-build-together-v02'
PRIOR=ROOT.parent/'lucas-academy-video-data/why-build-together-20261122/v01'
DEST=OUT/'assets';DEST.mkdir(parents=True,exist_ok=True)
SOURCES=OUT/'muse';SOURCES.mkdir(exist_ok=True)

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def probe(p):return json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(p)]))
def ff(args,log):
    with log.open('w') as stream:
        subprocess.run(['ffmpeg','-hide_banner','-y',*map(str,args)],check=True,stdout=stream,stderr=stream)

def prepare(id):
    original=PRIOR/'muse'/(id+'.mp4');source=SOURCES/(id+'.mp4')
    if not source.exists():shutil.copy2(original,source)
    assert sha(source)==sha(original)
    motion=PRIOR/'assets'/(id+'.mp4')
    destination=DEST/(id+'.mp4');receipt=DEST/(id+'.json')
    signature=dict(source_sha256=sha(source),motion_source_sha256=sha(motion),pipeline=2,
        effect='white paper graphite; local luminance dodge and fixed paper-space hatching',speed=1.0,
        hatch_sha256=sha(DEST/'hatch.png'),output_fps=30)
    graph=("[0:v]format=gray,gblur=sigma=0.5,split=3[a][b][s];"
           "[b]gblur=sigma=12[blur];"
           "[a][blur]blend=all_expr='clip(255*(A+12)/(B+14),0,255)',eq=contrast=1.18:brightness=0.008[edge];"
           "[s]lut=y='255-(255-val)*0.19'[shade];"
           "[shade][1:v]blend=all_expr='255-(255-A)*B/255'[hatch];"
           "[edge][hatch]blend=all_expr='A*B/255',format=yuv420p[v]")
    if not (receipt.exists() and destination.exists() and json.loads(receipt.read_text()).get('signature')==signature):
        started=time.monotonic()
        ff(['-filter_complex_threads','2','-i',motion,'-loop','1','-framerate','30','-i',DEST/'hatch.png',
            '-filter_complex',graph,'-map','[v]','-frames:v','300','-an','-c:v','libx264','-threads','3',
            '-preset','fast','-crf','17','-pix_fmt','yuv420p','-movflags','+faststart',destination],DEST/(id+'-encode.log'))
        pp=probe(destination);vv=next(x for x in pp['streams'] if x['codec_type']=='video')
        assert int(vv['nb_frames'])==300 and vv['avg_frame_rate']=='30/1'
        receipt.write_text(json.dumps(dict(signature=signature,sha256=sha(destination),seconds_spent=round(time.monotonic()-started,2)),indent=2)+'\n')
    ff(['-sseof','-0.04','-i',destination,'-frames:v','1',DEST/(id+'-last.jpg')],DEST/(id+'-poster.log'))
    print('Prepared white-paper pencil motion:',id,flush=True)
    return id,dict(frames=300,original=str(source),original_sha256=sha(source),prepared_sha256=sha(destination),
                  style='graphite on white paper',playback_speed=1.0)

def main():
    y,x=np.mgrid[:1080,:1920]
    diagonal=(np.mod(x+y,8)<1.3).astype(float)
    cross=(np.mod(x-y+2160,13)<1).astype(float)*.45
    texture=np.round((diagonal+cross)/1.45*255).astype(np.uint8)
    Image.fromarray(texture).save(DEST/'hatch.png')
    with ThreadPoolExecutor(max_workers=2) as pool:
        results=dict(pool.map(prepare,[f'G{i:02}' for i in range(1,6)]))
    (OUT/'assets.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
    font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',21)
    sheet=Image.new('RGB',(1280,5*275),'white');draw=ImageDraw.Draw(sheet)
    for i in range(5):
        id=f'G{i+1:02}'
        for j,t in enumerate([1,5,9]):
            frame=OUT/(id+f'-pencil-check-{t}.jpg')
            ff(['-ss',t,'-i',DEST/(id+'.mp4'),'-frames:v','1',frame],DEST/(id+f'-frame-{t}.log'))
            pic=Image.open(frame).resize((420,236));sheet.paste(pic,(j*426,i*275))
            draw.text((j*426+8,i*275+239),id+f' / {t}s',font=font,fill='#222222')
    sheet.save(OUT/'pencil-contact.jpg',quality=94)
    print('All five Muse scenes restyled; no new generation or timing changes.',flush=True)

if __name__=='__main__':main()
