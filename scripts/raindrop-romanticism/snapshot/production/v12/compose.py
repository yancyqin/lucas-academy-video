"""Compose newly rendered 60 fps museum frames with the approved assets and audio."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import json, subprocess, math, shutil, time, hashlib, fcntl
from PIL import Image
P=Path(__file__).resolve().parent;V=P.parent
FF='/opt/homebrew/bin/ffmpeg';FP='/opt/homebrew/bin/ffprobe';FPS=60
plan=json.loads((P/'capture-plan.json').read_text());by={s['id']:s for s in plan['scenes']}
for f in ['inserts','assets','parts','delivery']:(P/f).mkdir(exist_ok=True)
def frame(t):return math.floor(t*60+.5)
def run(cmd):subprocess.run(cmd,check=True)
def enc(n):return ['-an','-c:v','h264_videotoolbox','-b:v','16M','-maxrate','24M','-pix_fmt','yuv420p','-r','60','-g','120','-bf','0','-video_track_timescale','15360','-frames:v',str(n)]
def ready(file,n):
    if not file.exists():return False
    d=json.loads(subprocess.check_output([FP,'-v','error','-select_streams','v:0','-show_entries','stream=nb_frames,avg_frame_rate','-of','json',str(file)]))['streams'][0]
    return int(d.get('nb_frames',-1))==n and d['avg_frame_rate']=='60/1'

def prepare_insert(i):
    if i['kind']=='photo':return
    n=frame(i['end'])-frame(i['start']);out=P/'inserts'/(i['id']+'.mp4')
    if ready(out,n):return
    speed=i['speed'];extra=.25
    # Motion compensation is restricted to slow prerecorded inserts. The 3D museum
    # itself consists of newly rendered camera frames, never interpolated footage.
    effect=f'trim=duration={(n/60+extra)*speed:.9f},setpts=(PTS-STARTPTS)/{speed:.12f},tpad=stop_mode=clone:stop_duration=0.4,'
    effect+='scale=1280:-2,minterpolate=fps=60:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1:search_param=8,'
    effect+='scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=0x0c141a,setsar=1,tpad=stop_mode=clone:stop_duration=0.5'
    tmp=out.with_suffix('.tmp.mp4')
    run([FF,'-v','error','-y','-ss',str(i['trim']),'-i',i['file'],'-filter_threads','2','-vf',effect,*enc(n),str(tmp)])
    assert ready(tmp,n),(i['id'],n);tmp.replace(out);print('Prepared smooth insert',i['id'],n,flush=True)

def plate(id):
    out=P/'assets'/(id+'.png')
    if out.exists():return out
    if id=='goya-i-saw-it':file=V/'v3/footage/art/goya-i-saw-it.jpg'
    else:
        ui=P.parents[3]/'inception-space-ui';catalog=json.loads((ui/'content/inception/artworks/romanticism-salon-v1.json').read_text())
        work=next(w for w in catalog['works'] if w['id']==id);file=ui/'content/inception/assets/artworks'/work['image']
    im=Image.open(file).convert('RGB');scale=min(1816/im.width,1010/im.height)
    im=im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.LANCZOS)
    result=Image.new('RGB',(1920,1080),'#0c141a');result.paste(im,((1920-im.width)//2,(1080-im.height)//2));result.save(out)
    return out

def portrait():
    out=P/'inserts/portrait.mp4';n=frame(by['n003']['end'])-frame(by['n003']['start'])
    if ready(out,n):return out
    cmd=[FF,'-v','error','-y','-f','lavfi','-i',f'color=c=0x141719:s=1920x1080:r=60:d={n/60}']
    for f in [V/'v6/pilot-assets/george-sand-delacroix-1838.jpg',V/'v6/pilot-assets/chopin-delacroix-1838.jpg',V/'v7/assets/portrait-composition-reconstruction.png',V/'v7/assets/portrait-originals-label.png',V/'v7/assets/portrait-reconstruction-label.png']:
        cmd+=['-loop','1','-framerate','60','-i',str(f)]
    q="if(lt(t,1),0,if(lt(t,3.5),(1-cos((t-1)/2.5*PI))/2,if(lt(t,10),1,if(lt(t,12.5),(1+cos((t-10)/2.5*PI))/2,0))))"
    graph='[1:v]scale=-2:780,format=rgba,pad=iw+8:ih+8:4:4:color=0x8d744b[sand];[2:v]scale=-2:780,format=rgba,pad=iw+8:ih+8:4:4:color=0x8d744b[chopin];'
    graph+=f"[0:v][sand]overlay=x='250+225*({q})':y=90[p1];[p1][chopin]overlay=x='1040-100*({q})':y=90[p2];"
    graph+='[3:v]scale=-2:850,pad=1920:1080:(ow-iw)/2:35:color=0x141719,format=rgba,fade=t=in:st=3:d=1:alpha=1,fade=t=out:st=9.5:d=1:alpha=1[joined];[p2][4:v]overlay=0:0[p3];'
    graph+='[5:v]format=rgba,fade=t=in:st=3:d=0.7:alpha=1,fade=t=out:st=9.9:d=0.7:alpha=1[recon];[p3][joined]overlay=0:0[p4];[p4][recon]overlay=0:0,format=yuv420p[v]'
    run(cmd+['-filter_complex_threads','2','-filter_complex',graph,'-map','[v]',*enc(n),str(out)])
    assert ready(out,n);return out

def layers():
    all=[]
    for f in plan['flat']:all.append(dict(file=str(plate(f['id'])),kind='photo',start=f['start'],end=f['end'],fadeIn=1.35,fadeOut=1.35))
    for i in plan['inserts']:
        all.append(dict(i,file=i['file'] if i['kind']=='photo' else str(P/'inserts'/(i['id']+'.mp4'))))
    all.append(dict(file=str(portrait()),kind='video',start=by['n003']['start'],end=by['n003']['end'],fadeIn=.35,fadeOut=.35))
    for id in ['n006','n019','n021','n022','n023','n024','n026','n029','n030','n031','n033','n035','n036','n037','n038','n040','bonus-title']:
        s=by[id];all.append(dict(file=str(V/'v7/assets'/(id+'-english-label.png')),kind='photo',start=s['start']+.25,end=s['start']+min(8,s['end']-s['start']-.35),fadeIn=.6,fadeOut=.6))
    for f,a,b,fi,fo in [('pilot-title.png',.35,5.3,.6,.7),('transition-label.png',7.5,12.1,.7,.7)]:
        all.append(dict(file=str(V/'v6/pilot-assets'/f),kind='photo',start=a,end=b,fadeIn=fi,fadeOut=fo))
    all.append(dict(file=str(V/'v7/assets/credits-english.png'),kind='photo',start=by['credits']['start'],end=plan['duration'],fadeIn=.6,fadeOut=1))
    return all

def compose_chunk(args):
    idx,first,count,overlays=args;name=f'walk-{idx:03d}.mp4';raw=P/'raw'/name;out=P/'parts'/name
    if ready(out,count):return out
    while not ready(raw,count):time.sleep(1)
    selected=[x for x in overlays if frame(x['start'])<first+count and frame(x['end'])>first]
    if not selected and not (first<frame(by['credits']['start'])<first+count):
        shutil.copy2(raw,out);print('Retained native 60 fps',name,flush=True);return out
    cmd=[FF,'-v','error','-y','-filter_complex_threads','2','-i',str(raw)]
    close=frame(by['credits']['start'])
    base='[0:v]settb=1/60,setpts=N'
    if first<close<=first+count:base+=f',fade=t=out:st={(close-first)/60-1.1}:d=1.1'
    elif first>=close:base+=',lutrgb=r=0:g=0:b=0'
    filters=[base+'[base]'];current='base'
    for j,x in enumerate(selected,1):
        a=frame(x['start']);z=frame(x['end']);n=z-a
        offset=max(0,first-a);stop=min(n,first+count-a);shift=max(0,a-first)
        if x['kind']=='photo':cmd+=['-loop','1','-framerate','60','-i',x['file']]
        else:cmd+=['-i',x['file']]
        source='scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=0x0c141a,setsar=1,format=yuva420p'
        if x['fadeIn']:source+=f",fade=t=in:st=0:d={x['fadeIn']}:alpha=1"
        if x['fadeOut']:source+=f",fade=t=out:st={n/60-x['fadeOut']:.9f}:d={x['fadeOut']}:alpha=1"
        source+=f',trim=start_frame={offset}:end_frame={stop},settb=1/60,setpts=N+{shift}'
        filters.append(f'[{j}:v]{source}[layer{j}]');label=f'mix{j}'
        filters.append(f'[{current}][layer{j}]overlay=repeatlast=0:eof_action=pass[{label}]');current=label
    tmp=out.with_suffix('.tmp.mp4')
    run(cmd+['-filter_complex',';'.join(filters),'-map',f'[{current}]',*enc(count),str(tmp)])
    assert ready(tmp,count),(name,count);tmp.replace(out);print('Composed',name,len(selected),flush=True);return out

def main():
    with ThreadPoolExecutor(max_workers=2) as pool:list(pool.map(prepare_insert,plan['inserts']))
    overlay=layers();(P/'overlay-plan.json').write_text(json.dumps(overlay,ensure_ascii=False,indent=2))
    tasks=[(i//1200,i,min(1200,plan['frames']-i),overlay) for i in range(0,plan['frames'],1200)]
    with ThreadPoolExecutor(max_workers=2) as pool:files=list(pool.map(compose_chunk,tasks))
    concat=P/'parts/concat.txt';concat.write_text(''.join(f"file '{f}'\n" for f in files))
    out=P/'delivery/01-English-full.mp4';tmp=out.with_suffix('.tmp.mp4')
    run([FF,'-v','error','-y','-f','concat','-safe','0','-i',str(concat),'-i',str(V/'v11/delivery/English-mix.wav'),'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','256k','-af','apad=pad_dur=0.008333333','-t',str(plan['duration']),'-metadata:s:a:0','language=eng','-movflags','+faststart',str(tmp)])
    assert ready(tmp,plan['frames']);tmp.replace(out)
    for name in ['02-Chinese-aligned-audio.wav','Chinese-YouTube.m4a','Chinese-preview.mp3','03-English.srt','04-Chinese.srt','English-mix.wav']:shutil.copy2(V/'v11/delivery'/name,P/'delivery'/name)
    run([FF,'-v','error','-y','-ss','294','-i',str(out),'-t','24','-c','copy',str(P/'delivery/Smooth-walk-preview.mp4')])
    print('FULL SMOOTH FILM READY',out,flush=True)
if __name__=='__main__':
    with (P/'assembly.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        main()
