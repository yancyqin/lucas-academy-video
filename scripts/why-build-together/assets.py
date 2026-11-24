"""Import authorized Muse downloads, retain originals, and prepare video layers."""
from concurrent.futures import ThreadPoolExecutor
import hashlib,json,subprocess,time,shutil
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'out/why-build-together-v01'
DEST=OUT/'assets';DEST.mkdir(parents=True,exist_ok=True)
SOURCES=OUT/'muse';SOURCES.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def probe(p):return json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(p)]))
def ff(args,log):
    with log.open('w') as stream:
        subprocess.run(['ffmpeg','-hide_banner','-y',*map(str,args)],check=True,stdout=stream,stderr=stream)

def prepare(id):
    downloaded=Path.home()/'Downloads'/f'why-build-together-{id}.mp4'
    assert downloaded.exists(),downloaded
    source=SOURCES/(id+'.mp4')
    if not source.exists():shutil.copy2(downloaded,source)
    assert sha(source)==sha(downloaded)
    p=probe(source);video=next(x for x in p['streams'] if x['codec_type']=='video')
    assert video['width']==1280 and video['height']==720 and abs(float(p['format']['duration'])-10)<.05
    destination=DEST/(id+'.mp4');receipt=DEST/(id+'.json')
    signature=dict(source_sha256=sha(source),pipeline=2,native_fps=video['avg_frame_rate'],speed=1.0,
                   output_fps=30,motion_interpolation='minterpolate mci, bidirectional estimation')
    if not (receipt.exists() and destination.exists() and json.loads(receipt.read_text()).get('signature')==signature):
        started=time.monotonic()
        # Interpolate in the native 720p space before upscaling. A short endpoint
        # pad compensates for interpolation lookahead; output duration stays 10s.
        filters='tpad=stop_mode=clone:stop_duration=0.15,minterpolate=fps=30:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1,trim=duration=10,scale=1920:1080:flags=lanczos,setsar=1'
        if id=='G04':filters+=',colorbalance=gm=-0.025:rh=0.01:bh=0.01'
        if id=='G05':filters+=',eq=gamma=1.08:brightness=0.012:saturation=0.96'
        ff(['-i',source,'-vf',filters,'-an','-c:v','libx264','-preset','fast','-crf','17','-pix_fmt','yuv420p','-movflags','+faststart',destination],DEST/(id+'-encode.log'))
        pp=probe(destination);vv=next(x for x in pp['streams'] if x['codec_type']=='video')
        assert int(vv['nb_frames'])==300 and vv['avg_frame_rate']=='30/1'
        receipt.write_text(json.dumps(dict(signature=signature,sha256=sha(destination),seconds_spent=round(time.monotonic()-started,2)),indent=2)+'\n')
    ff(['-i',destination,'-vf','select=eq(n\\,299)','-frames:v','1',DEST/(id+'-last.jpg')],DEST/(id+'-poster.log'))
    print('Prepared',id,flush=True)
    return id,dict(frames=300,original=str(source),original_sha256=sha(source),prepared_sha256=sha(destination))

def main():
    with ThreadPoolExecutor(max_workers=2) as pool:
        results=dict(pool.map(prepare,[f'G{i:02}' for i in range(1,7)]))
    bw=DEST/'G05-bw.mp4'
    ff(['-i',DEST/'G05.mp4','-vf',"format=gray,gblur=sigma=0.8,edgedetect=low=0.02:high=0.08:mode=wires,lut=y='if(gte(val,12),min(val*5,255),0)',dilation,format=yuv420p",'-an','-c:v','libx264','-preset','fast','-crf','17',bw],DEST/'G05-bw-encode.log')
    ff(['-i',bw,'-vf','select=eq(n\\,299)','-frames:v','1',DEST/'G05-bw-last.jpg'],DEST/'G05-bw-poster.log')
    results['G05-bw']=dict(frames=300,source='G05',prepared_sha256=sha(bw),effect='white contours on black, no timing change')
    (OUT/'assets.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
    font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',21)
    sheet=Image.new('RGB',(1280,6*275),'#11191d');draw=ImageDraw.Draw(sheet)
    for i in range(6):
        id=f'G{i+1:02}'
        for j,t in enumerate([1,5,9]):
            image=OUT/(id+f'-check-{t}.jpg')
            ff(['-ss',t,'-i',SOURCES/(id+'.mp4'),'-frames:v','1',image],DEST/(id+f'-frame-{t}.log'))
            pic=Image.open(image).resize((420,236));sheet.paste(pic,(j*426,i*275))
            draw.text((j*426+8,i*275+239),id+f' / {t}s',font=font,fill='white')
    sheet.save(OUT/'muse-contact.jpg',quality=94)
    print('All six Muse originals and 30 fps layers validated.',flush=True)

if __name__=='__main__':main()
