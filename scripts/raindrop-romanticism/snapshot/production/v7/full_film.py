"""Owner-approved full bilingual recut: common timing, no guide, local year repairs."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import html
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import sys
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFont

P=Path(__file__).resolve().parent
P5=P.parent/'v5'; P6=P.parent/'v6'; ASSETS=P/'assets'; PARTS=P/'parts'
DEST=Path('@USER_HOME@/Desktop/压力焦虑肖邦浪漫-完整版-2026-11-21')
GALLERY=P.parents[2]/'romanticism-music-gallery'
FF='/opt/homebrew/bin/ffmpeg'; FPS=24; SR=48000
CLEAN=P5/'parts/retimed.mp4'
LABELED=P5/'exports/压力焦虑肖邦浪漫-Louise-1.1x-英文版.mp4'
ENGLISH_LABELS={
    'n006':('Raindrop Prelude','Frédéric Chopin · Prelude in D-flat major, Op. 28 No. 15'),
    'n019':('Francisco Goya','Court painter · witness to war'),
    'n021':('The Third of May 1808','Francisco Goya'),
    'n022':('I Saw It','Francisco Goya · The Disasters of War'),
    'n023':('Théodore Géricault','Painter of The Raft of the Medusa'),
    'n024':('The Raft of the Medusa','Théodore Géricault'),
    'n026':('Eugène Delacroix','Painter of Liberty Leading the People'),
    'n029':('Liberty Leading the People','Eugène Delacroix'),
    'n030':('Joseph Wright of Derby','Science, light and the sublime'),
    'n031':('Vesuvius in Eruption','Joseph Wright of Derby'),
    'n033':('Caspar David Friedrich','Landscape and the inner world'),
    'n035':('Monk by the Sea','Caspar David Friedrich'),
    'n036':('Wanderer above the Sea of Fog','Caspar David Friedrich'),
    'n037':('J. M. W. Turner','Painter of sea, weather and light'),
    'n038':('The Fighting Temeraire','J. M. W. Turner'),
    'n040':('Rain, Steam and Speed','J. M. W. Turner'),
    'bonus-title':('Coda · Mono no aware','The poignancy of passing things'),
}
sys.path.insert(0,str(P6))
from make_pilot import decode, write_wav, subtitle_chunks, caption_lines, srt_time

def run(args):
    subprocess.run(args,check=True)

def save(path,data):
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')

def load_inputs():
    script=json.loads((P6/'narration-bilingual.json').read_text())
    manifest=json.loads((P6/'voice-manifest.json').read_text())
    overrides=json.loads((P/'year-voice-overrides.json').read_text())
    assert script['source_sha256']==manifest['source_sha256']
    by_id={i['id']:i for i in overrides['items']}
    items=[]
    for item in manifest['items']:
        item=dict(item)
        if item['language']=='zh' and item['id'] in by_id:
            replacement=by_id[item['id']]
            assert replacement['text']==item['text']
            item.update(replacement)
        items.append(item)
    return script,items

def make_plan():
    script,items=load_inputs()
    old=json.loads((P5/'edit-plan.json').read_text())['scenes']
    old_by={s['id']:s for s in old}
    # Exact source ranges retain the existing museum route and approved insets.
    mapping={
        'n006':'p012','n007':'p013','n014':'p015','n015':'p017','n016':'p019',
        'n017':'p021','n018':'p023','n019':'p030','n020':'p031','n021':'p032',
        'n022':'p034','n023':'p040','n024':'p041','n025':'p042','n026':'p048',
        'n027':'p049','n028':'p050','n029':'p051','n030':'p059','n031':'p060',
        'n032':'p061','n033':'p067','n034':'p069','n035':'p070','n036':'p071',
        'n037':'p078','n038':'p079','n039':'p080','n040':'p081','n041':'theme-0',
        'n042':'theme-1','n043':'theme-2','n044':'theme-3','n047':'p093',
        'n048':'bonus-00','n049':'bonus-01','n050':'bonus-02','n051':'bonus-03',
        'n052':'bonus-04','n057':'bonus-08','n058':'bonus-09',
    }
    durations={}
    for item in items:
        with wave.open(item['file']) as w:
            actual=w.getnframes()/w.getframerate()
        assert actual>.3 and abs(actual-item['seconds'])<.06,(item['id'],actual,item['seconds'])
        key=(item['language'],item['paragraph_id'])
        durations[key]=durations.get(key,0)+actual
    scenes=[];cursor=0
    def add(id,seconds,section='',**extra):
        nonlocal cursor
        count=math.ceil((seconds-1e-8)*FPS)
        scene=dict(id=id,first=cursor,count=count,start=cursor/FPS,end=(cursor+count)/FPS,section=section,**extra)
        scenes.append(scene);cursor+=count;return scene
    add('opening-lead',1,'开头')
    for row in script['rows']:
        id=row['id']
        if row['spoken']:
            n=int(id[1:]);voices={l:durations[(l,id)] for l in ['en','zh']}
            seconds=max(voices.values())+.65
            source=None
            if id in mapping:
                s=old_by[mapping[id]];source=[s['start'],s['end']]
                if n>=48:seconds=max(seconds,s['end']-s['start'])
            if id=='n003':seconds=max(15,seconds)
            if id=='n056':seconds=max(seconds,839.125-832.1666666667)
            if id=='n048':add('bonus-title',3,'片尾彩蛋 物哀',source=[756,759])
            scene=add(id,seconds,row['section'].strip(),text_zh=row['zh'],text_en=row['en'],voice_seconds=voices,
                      voice_start=cursor/FPS+.25,source=source)
        elif id=='cue-005':add('listen',10,'肖邦与雨滴')
        elif id=='cue-013':add('listen-heavy',12,'肖邦与雨滴',source=[165.2916666667,168.7916666667])
        elif id=='cue-017':add('listen-clearing',316.367-247,'肖邦与雨滴')
        elif id=='cue-067':add('listen-return',12,'开头的旋律回来了',source=[696.25,708.25])
        elif id=='cue-069':
            last=scenes[-1];length=last['end']-last['start']
            add('piano-ending',316.367-257-12-length,'开头的旋律回来了',source=[721.8333333333,756])
        elif id=='cue-082':add('bonus-hold',20,'片尾彩蛋 物哀',source=[849.0833333333,869.0833333333])
    add('salon-coda',6,'沙龙',source=[869.0833333333,875.0833333333])
    add('credits',10,'片尾署名',source=[875.0833333333,885.0833333333])
    by={s['id']:s for s in scenes}
    by['n008']['source']=[161.7916666667,165.2916666667]
    # Split older combined paragraphs without repeating any tour movement.
    def split_range(ids,a,b):
        total=sum(by[id]['count'] for id in ids);offset=a
        for id in ids:
            end=offset+(b-a)*by[id]['count']/total
            by[id]['source']=[offset,end];offset=end
        assert abs(offset-b)<1e-6
    split_range(['n045','n046'],681.8333333333,696.25)
    split_range(['n053','n054','n055'],821.875,832.1666666667)
    by['n056']['source']=[832.1666666667,839.125]
    by['n003']['visual']='portrait-reconstruction-merge-split'
    by['n004']['visual']='monastery'
    by['n005']['visual']='water-double-pass'
    by['listen-clearing']['visual']='monk-full-painting'
    plan=dict(fps=FPS,frames=cursor,duration=cursor/FPS,source_sha256=script['source_sha256'],scenes=scenes,
              captions={'en':[],'zh':[]},guide_character=False,speech_speed_changed=False,
              common_scene_timing=True,voice_fragments=items,cloud_generation_requests=0,
              voices={'en':'Existing MiniMax performance → local Louise conversion',
                      'zh':'Existing MiniMax performance → local Fangfang conversion; 15 calendar-year fragments repaired using local Qwen → Fangfang'},
              portrait_reconstruction='Hypothetical composition reconstruction after the Louvre 1838 study; joined then separated into surviving originals.')
    save(P/'full-plan.json',plan)
    print('Full timeline:',plan['duration'],'seconds;',len(scenes),'scenes',flush=True)
    return plan

def score_spans(plan):
    b={s['id']:s for s in plan['scenes']};end=plan['duration']
    marks=[(0,b['listen']['start'],'rain',0),
           (b['listen']['start'],b['listen-heavy']['start'],'rain',0),
           (b['listen-heavy']['start'],b['listen-clearing']['start'],'rain',145),
           (b['listen-clearing']['start'],b['listen-clearing']['end'],'rain',247),
           (b['n012']['start'],b['n019']['start'],'rain',0),
           (b['n019']['start'],b['n030']['start'],'n9',0),
           (b['n030']['start'],b['n037']['start'],'ncs',0),
           (b['n037']['start'],b['listen-return']['start'],'rain',72),
           (b['listen-return']['start'],b['piano-ending']['end'],'rain',257),
           (b['bonus-title']['start'],end,'n9',max(0,271.469-(end-b['bonus-title']['start'])))]
    for a,z,_,_ in marks:assert z>a
    for x,y in zip(marks,marks[1:]):assert abs(x[1]-y[0])<1e-6,(x,y)
    return marks

def prepare_audio(plan):
    length=plan['frames']*(SR//FPS)
    score=np.zeros((length,2),np.float32);duck=np.ones(length,np.float32)
    names={'rain':'prelude-28-15.m4a','n9':'nocturne-9-2.m4a','ncs':'nocturne-c-sharp.m4a'}
    songs={}
    for name,file in names.items():
        s=decode(GALLERY/'music'/file,2);s*=.065/np.sqrt(np.mean(s**2));songs[name]=s
    spans=score_spans(plan)
    # One-sided short crossfades preserve the exact start of each listening excerpt.
    for k,(start,end,name,offset) in enumerate(spans):
        a=round(start*SR);z=round(end*SR);src=round(offset*SR);n=z-a;s=songs[name]
        available=min(n,len(s)-src)
        assert available>=n-int(.06*SR),(name,start,end,offset,n-available)
        score[a:a+available]+=s[src:src+available]
        if k>0:
            cross=min(round(.7*SR),n)
            # Fade preceding score out before a fresh phrase; new excerpt starts intact.
            fade=min(round(.12*SR),a)
            score[a-fade:a]*=np.linspace(1,0,fade)[:,None]
    tail=round(4*SR);score[-tail:]*=np.linspace(1,0,tail)[:,None]
    by={s['id']:s for s in plan['scenes']}
    for scene in plan['scenes']:
        if not scene['id'].startswith('n'):continue
        a=round(scene['voice_start']*SR);z=a+round(max(scene['voice_seconds'].values())*SR)
        attack=max(0,a-12000);release=min(length,z+19200)
        duck[attack:a]=np.minimum(duck[attack:a],np.linspace(1,.25,a-attack))
        duck[a:z]=np.minimum(duck[a:z],.25)
        duck[z:release]=np.minimum(duck[z:release],np.linspace(.25,1,release-z))
    score*=duck[:,None]
    listen=by['listen'];a=round(listen['start']*SR)
    corr=float(np.corrcoef(score[a:a+10*SR,0],songs['rain'][:10*SR,0])[0,1])
    assert corr>.99999
    gains={}
    for lang in ['en','zh']:
        voice=np.zeros(length,np.float32);captions=[]
        for scene in plan['scenes']:
            if not scene['id'].startswith('n'):continue
            offset=round(scene['voice_start']*SR)
            units=[i for i in plan['voice_fragments'] if i['language']==lang and i['paragraph_id']==scene['id']]
            compact=lambda t:re.sub(r'\s+','',t)
            assert compact(''.join(u['text'] for u in units))==compact(scene['text_'+lang]),scene['id']
            for item in units:
                v=decode(item['file'])[:,0]
                assert np.isfinite(v).all() and np.max(np.abs(v))>.01
                assert offset+len(v)<=round(scene['end']*SR)
                voice[offset:offset+len(v)]=v
                pieces=subtitle_chunks(item['text'],lang)
                # Force a maximum of two readable subtitle lines.
                packed=[]
                for piece in pieces:
                    lines=caption_lines(piece,lang).splitlines()
                    for index in range(0,len(lines),2):packed.append((' ' if lang=='en' else '').join(lines[index:index+2]))
                weights=[len(re.sub(r'\s','',s)) for s in packed];cursor=0
                for part,weight in zip(packed,weights):
                    start=offset/SR+len(v)/SR*cursor/sum(weights);cursor+=weight
                    end=offset/SR+len(v)/SR*cursor/sum(weights)
                    captions.append(dict(start=start,end=end,text=caption_lines(part,lang),paragraph_id=scene['id']))
                offset+=len(v)
        active=voice[np.abs(voice)>.008];gain=.11/np.sqrt(np.mean(active**2));voice*=gain
        assert np.max(np.abs(voice[a:a+10*SR]))==0
        mix=score+voice[:,None]
        peak=float(np.max(np.abs(mix)));headroom=min(1,.93/peak);mix*=headroom
        gains[lang]={'voice_gain':float(gain),'mix_gain':headroom,'peak':float(np.max(np.abs(mix)))}
        destination=DEST/('02-Chinese-aligned-audio.wav' if lang=='zh' else 'English-mix.wav')
        run([FF,'-v','error','-y','-f','f32le','-ar',str(SR),'-ac','2','-i','-',
             '-c:a','pcm_s24le',str(destination)]) if False else None
        # Temporary 16-bit PCM avoids a second full-sized float copy; final delivery is 24-bit.
        scratch=PARTS/f'audio-{lang}.wav';write_wav(scratch,mix)
        run([FF,'-v','error','-y','-i',str(scratch),'-c:a','pcm_s24le',str(destination)])
        scratch.unlink()
        plan['captions'][lang]=captions
        sub=DEST/('03-English.srt' if lang=='en' else '04-Chinese.srt')
        sub.write_text('\n'.join(f'{i}\n{srt_time(c["start"])} --> {srt_time(c["end"])}\n{c["text"]}\n' for i,c in enumerate(captions,1)),encoding='utf-8')
        print('Aligned full audio ready:',lang,flush=True)
    run([FF,'-v','error','-y','-i',str(DEST/'02-Chinese-aligned-audio.wav'),'-c:a','libmp3lame','-q:a','2',str(DEST/'Chinese-preview.mp3')])
    plan.update(music_spans=[dict(start=a,end=z,track=n,source_offset=o) for a,z,n,o in spans],
                music_reprise_correlation=corr,audio_gains=gains)
    save(P/'full-plan.json',plan)

def encoder(count):
    return ['-an','-c:v','h264_videotoolbox','-b:v','12M','-maxrate','18M','-pix_fmt','yuv420p',
            '-r','24','-g','48','-bf','0','-video_track_timescale','12288','-frames:v',str(count)]

def labels():
    image=Image.new('RGBA',(1920,1080));d=ImageDraw.Draw(image)
    fonts=Path('/System/Library/Fonts/Supplemental')
    serif=ImageFont.truetype(str(fonts/'Georgia.ttf'),40)
    small=ImageFont.truetype(str(fonts/'Arial.ttf'),26)
    d.text((960,954),'Chopin and George Sand',anchor='mm',font=serif,fill='#efe1bd')
    d.text((960,1004),'Eugène Delacroix · 1838 · Surviving portrait fragments',anchor='mm',font=small,fill='#c1b8a8')
    image.save(ASSETS/'portrait-originals-label.png')
    image=Image.new('RGBA',(1920,1080));d=ImageDraw.Draw(image)
    d.text((960,954),'Composition reconstruction',anchor='mm',font=serif,fill='#efe1bd')
    d.text((960,1004),'Hypothetical reassembly after Delacroix’s 1838 study',anchor='mm',font=small,fill='#c1b8a8')
    image.save(ASSETS/'portrait-reconstruction-label.png')
    for id,(title,detail) in ENGLISH_LABELS.items():
        image=Image.new('RGBA',(1920,1080));d=ImageDraw.Draw(image)
        d.text((66,54),title,font=ImageFont.truetype(str(fonts/'Georgia.ttf'),34),fill='#f1e4c6',stroke_width=2,stroke_fill=(12,16,19,235))
        d.text((68,102),detail,font=ImageFont.truetype(str(fonts/'Arial.ttf'),25),fill='#e5e0d7',stroke_width=1,stroke_fill=(12,16,19,230))
        image.save(ASSETS/(id+'-english-label.png'))
    image=Image.new('RGB',(1920,1080),'#101b23');d=ImageDraw.Draw(image)
    def center(y,text,size=30,name='Arial.ttf',color='#d7d1c5'):
        d.text((960,y),text,anchor='mm',font=ImageFont.truetype(str(fonts/name),size),fill=color)
    center(215,'Created together by',28)
    center(285,'Yancy & Eunice',56,'Georgia.ttf','#efe0b6')
    center(425,'Music · Frédéric Chopin',32)
    center(487,'Narration · Louise / Fangfang',29)
    center(549,'The Romantic Salon · shared virtual museum',29)
    center(660,'Falling petals footage · Pexels',25)
    center(709,'Seirai-in photograph · Haruo.takagi · CC BY-SA 4.0',25)
    center(758,'3D sculpture scans · CC BY 4.0 · full attributions in the description',25)
    center(883,'Artwork sources and reconstruction notes accompany this film.',24)
    image.save(ASSETS/'credits-english.png')

def make_tasks(plan):
    by={s['id']:s for s in plan['scenes']};tasks=[]
    end=by['n003']['start'];count=by['n003']['first']
    tasks.append(dict(id='opening',count=count,seconds=count/FPS,kind='opening',source=[0,42.3333333333],file=str(CLEAN)))
    for s in plan['scenes']:
        if s['start']<end:continue
        id=s['id'];task=dict(id=id,count=s['count'],seconds=s['count']/FPS,kind='normal',file=str(CLEAN),source=s.get('source'))
        if id=='n003':task['kind']='portrait'
        elif id=='n004':task.update(file=str(P.parent/'v2/footage/O02-monastery.mp4'),source=[.35,9.65])
        elif id=='n005':task.update(file=str(P5/'footage/cold-water-loop.mp4'),source=[0,18.7083333333])
        elif id=='listen-clearing':task['kind']='painting-hold'
        elif id=='credits':task['kind']='english-credits'
        elif id in ['n009','n010','n011','n012','n013']:
            task.update(kind='museum-hold',file=str(CLEAN),source=[168.5,168.5416666667])
        if id in ENGLISH_LABELS:task['label']=list(ENGLISH_LABELS[id])
        assert task['kind'] in ['portrait','painting-hold','english-credits'] or task['source'],id
        tasks.append(task)
    assert sum(t['count'] for t in tasks)==plan['frames']
    return tasks

def render_task(task):
    output=PARTS/(task['id']+'.mp4');receipt=output.with_suffix('.render.json')
    signature=hashlib.sha256(json.dumps(task,sort_keys=True).encode()).hexdigest()
    if output.exists() and receipt.exists() and json.loads(receipt.read_text()).get('signature')==signature:
        print('Cached',task['id'],flush=True);return output
    seconds=task['seconds'];kind=task['kind']
    cmd=[FF,'-v','error','-y']
    if kind=='english-credits':
        cmd+=['-loop','1','-framerate','24','-i',str(ASSETS/'credits-english.png'),
              '-vf',f'fade=t=in:st=0:d=0.6,fade=t=out:st={seconds-1}:d=1']
    elif kind in ['portrait','painting-hold']:
        cmd+=['-f','lavfi','-i',f'color=c=0x141719:s=1920x1080:r=24:d={seconds}']
    else:cmd+=['-ss',f'{task["source"][0]:.9f}','-i',task['file']]
    if kind=='english-credits':pass
    elif kind=='portrait':
        for f in [P6/'pilot-assets/george-sand-delacroix-1838.jpg',P6/'pilot-assets/chopin-delacroix-1838.jpg',
                  ASSETS/'portrait-composition-reconstruction.png',ASSETS/'portrait-originals-label.png',ASSETS/'portrait-reconstruction-label.png']:
            cmd+=['-loop','1','-framerate','24','-i',str(f)]
        # Smooth inwards / outwards movement, never shake or crop either original.
        q="if(lt(t,1),0,if(lt(t,3.5),(1-cos((t-1)/2.5*PI))/2,if(lt(t,10),1,if(lt(t,12.5),(1+cos((t-10)/2.5*PI))/2,0))))"
        graph='[1:v]scale=-2:780,format=rgba,pad=iw+8:ih+8:4:4:color=0x8d744b[sand];'
        graph+='[2:v]scale=-2:780,format=rgba,pad=iw+8:ih+8:4:4:color=0x8d744b[chopin];'
        graph+=f"[0:v][sand]overlay=x='250+225*({q})':y=90[p1];[p1][chopin]overlay=x='1040-100*({q})':y=90[p2];"
        graph+='[3:v]scale=-2:850,pad=1920:1080:(ow-iw)/2:35:color=0x141719,format=rgba,fade=t=in:st=3:d=1:alpha=1,fade=t=out:st=9.5:d=1:alpha=1[joined];'
        graph+='[p2][4:v]overlay=0:0[p3];'
        graph+='[5:v]format=rgba,fade=t=in:st=3:d=0.7:alpha=1,fade=t=out:st=9.9:d=0.7:alpha=1[recon];'
        graph+='[p3][joined]overlay=0:0[p4];[p4][recon]overlay=0:0,format=yuv420p[v]'
        cmd+=['-filter_complex_threads','2','-filter_complex',graph,'-map','[v]']
    elif kind=='painting-hold':
        cmd+=['-loop','1','-framerate','24','-i',str(GALLERY/'art/monk-sea.jpg')]
        # Complete painting for the musical ending, with a steady museum view underneath.
        cmd+=['-ss','168.5','-i',str(CLEAN)]
        graph=f'[2:v]trim=duration=0.041666667,setpts=PTS-STARTPTS,tpad=stop_mode=clone:stop_duration={seconds},trim=duration={seconds}[room];'
        graph+=f'[1:v]scale=1850:1000:force_original_aspect_ratio=decrease,format=rgba,fade=t=in:st=0:d=1.5:alpha=1,fade=t=out:st={seconds-1.5}:d=1.5:alpha=1[art];'
        graph+='[room][art]overlay=x=(W-w)/2:y=(H-h)/2,format=yuv420p[v]'
        cmd+=['-filter_complex_threads','2','-filter_complex',graph,'-map','[v]']
    else:
        a,b=task['source'];source_seconds=b-a
        if kind=='museum-hold':effect=f'trim=duration={source_seconds:.9f},setpts=PTS-STARTPTS,tpad=stop_mode=clone:stop_duration={seconds}'
        else:effect=f'trim=duration={source_seconds:.9f},setpts=(PTS-STARTPTS)*{seconds/source_seconds:.12f},fps=24,tpad=stop_mode=clone:stop_duration=0.2'
        effect+=',scale=1920:1080,setsar=1'
        if kind=='opening':
            for name in ['pilot-title.png','transition-label.png']:cmd+=['-loop','1','-framerate','24','-i',str(P6/'pilot-assets'/name)]
            # Transition caption follows the actual ceiling reveal on the shortened entrance.
            graph=f'[0:v]{effect}[base];'
            graph+='[1:v]format=rgba,fade=t=in:st=0.35:d=0.6:alpha=1,fade=t=out:st=4.6:d=0.7:alpha=1[title];'
            graph+='[base][title]overlay=0:0[titled];'
            graph+='[2:v]format=rgba,fade=t=in:st=7.5:d=0.7:alpha=1,fade=t=out:st=11.4:d=0.7:alpha=1[label];'
            graph+='[titled][label]overlay=0:0,format=yuv420p[v]'
            cmd+=['-filter_complex_threads','2','-filter_complex',graph,'-map','[v]']
        elif task.get('label'):
            duration=min(8,seconds-.35)
            cmd+=['-loop','1','-framerate','24','-i',str(ASSETS/(task['id']+'-english-label.png'))]
            graph=f'[0:v]{effect}[base];'
            graph+=f'[1:v]format=rgba,fade=t=in:st=0.25:d=0.6:alpha=1,fade=t=out:st={duration-.6}:d=0.6:alpha=1[label];'
            graph+='[base][label]overlay=0:0,format=yuv420p[v]'
            cmd+=['-filter_complex_threads','2','-filter_complex',graph,'-map','[v]']
        else:cmd+=['-filter_threads','2','-vf',effect]
    run(cmd+encoder(task['count'])+[str(output)])
    probe=json.loads(subprocess.check_output(['/opt/homebrew/bin/ffprobe','-v','error','-show_streams','-of','json',str(output)]))
    stream=probe['streams'][0]
    assert int(stream['nb_frames'])==task['count'],(task['id'],stream.get('nb_frames'),task['count'])
    save(receipt,dict(signature=signature,task=task,frames=int(stream['nb_frames'])))
    print('Rendered full-film scene:',task['id'],flush=True)
    return output

def render_picture(plan):
    labels();tasks=make_tasks(plan);save(P/'picture-tasks.json',tasks)
    with ThreadPoolExecutor(max_workers=2) as pool:files=list(pool.map(render_task,tasks))
    concat=PARTS/'concat.txt';concat.write_text(''.join("file '"+str(f)+"'\n" for f in files))
    picture=PARTS/'full-picture.mp4'
    run([FF,'-v','error','-y','-f','concat','-safe','0','-i',str(concat),'-c','copy',str(picture)])
    run([FF,'-v','error','-y','-i',str(picture),'-i',str(DEST/'English-mix.wav'),'-map','0:v:0','-map','1:a:0',
         '-c:v','copy','-c:a','aac','-b:a','256k','-metadata:s:a:0','language=eng',
         '-metadata','title=Pressure? Anxiety? Chopin? Romanticism?','-movflags','+faststart',str(DEST/'01-English-full.mp4')])
    print('FULL ENGLISH FILM READY',flush=True)

def preview_page(plan):
    page=(Path('@USER_HOME@/Desktop/压力焦虑肖邦浪漫-新版样片/样片预览.html')).read_text()
    page=page.replace('浪漫主义沙龙 · 导览角色样片','浪漫主义沙龙 · 完整影片').replace('压力？焦虑？肖邦？浪漫？ · 导览角色样片','压力？焦虑？肖邦？浪漫？')
    page=page.replace('01-English-preview.mp4','01-English-full.mp4')
    page=re.sub(r'<h1>.*?</h1><p>.*?</p>',f'<h1>压力？焦虑？肖邦？浪漫？</h1><p>Yancy &amp; Eunice · 完整版 · {plan["duration"]/60:.1f} 分钟。现实画廊走进深空沙龙，在肖邦的音乐中观看浪漫主义。英文 Louise；中文 Fangfang。两种语言共用画面节奏，保留自然语速。</p>',page,count=1)
    chapters=''.join(f'<button data-seek="{s["start"]:.3f}">{int(s["start"])//60:02}:{int(s["start"])%60:02} · {html.escape(s.get("text_zh",s["section"])[:26])}</button>' for s in plan['scenes'] if s['id'].startswith('n') or s['id'] in ['listen','listen-heavy','listen-clearing','listen-return','piano-ending'])
    page=re.sub(r'(<div class="chapters">).*?(</div></details>)',lambda m:m[1]+chapters+m[2],page,flags=re.S)
    footer='<footer><p>双人像段落：两块现存原作 → 假想合并构图 → 重新拆分。合并部分已标注 Composition reconstruction，依据德拉克洛瓦 1838 年构图草图与原作片段制作，属于数字复原示意。<a href="https://collections.louvre.fr/en/ark:/53355/cl020122665">卢浮宫作品记录</a> · <a href="Portrait-reconstruction.png">合并示意图</a> · <a href="Portrait-reconstruction-generation.json">生成方式、参考与完整提示词</a>。</p><p>导览角色已取消。中文年份逐字读，书面文案及字幕保留数字。年份补录使用本地 Qwen3-TTS → Fangfang；其余复用已完成的 MiniMax 演绎与本地换声，本次未调用云端语音生成。</p><p><a href="中文定稿.docx">中文文案 Word</a> · <a href="英文配音稿.docx">英文文案 Word</a> · <a href="YouTube中文简介.txt">中文简介与标签</a> · <a href="YouTube-English-description.txt">English description and tags</a> · <a href="素材来源与制作说明.json">素材来源与制作说明</a></p></footer>'
    page=re.sub(r'<div class="design">.*?</footer>',lambda m:footer,page,flags=re.S)
    data=json.dumps(plan['captions'],ensure_ascii=False).replace('</','<\\/')
    page=re.sub(r'const CUES=.*?;const v=',lambda m:'const CUES='+data+';const v=',page,flags=re.S)
    (DEST/'影片预览.html').write_text(page,encoding='utf-8')

def package(plan):
    old=Path('@DATA_ROOT@/production/v12/published-release')
    copies={
        old/'04-YouTube封面-暖色画廊-英文.jpg':'Cover-English.jpg',
        old/'05-YouTube封面-暖色画廊-中文.jpg':'Cover-Chinese.jpg',
        P6/'压力焦虑肖邦浪漫-已确认中文文案.docx':'中文定稿.docx',
        Path('@USER_HOME@/Desktop/压力焦虑肖邦浪漫-英文配音稿-新版.docx'):'英文配音稿.docx',
        ASSETS/'portrait-composition-reconstruction.png':'Portrait-reconstruction.png',
        ASSETS/'portrait-reconstruction-generation.json':'Portrait-reconstruction-generation.json',
        PARTS/'n003.mp4':'05-Portrait-merge-split.mp4',
    }
    for src,name in copies.items():shutil.copy2(src,DEST/name)
    tags='#chopin #romanticism #arthistory #art #classicalmusic #visualart #museum #artgallery #mononoaware #stressrelief #anxietyrelief #肖邦 #雨滴 #浪漫主义 #物哀'
    for source,name in [('06-YouTube中文简介与素材署名.txt','YouTube中文简介.txt'),('03-YouTube简介与素材署名.txt','YouTube-English-description.txt')]:
        text=(old/source).read_text()
        # Old edit's chapter clock must never be included in the revised upload notes.
        text=re.sub(r'(?m)^\s*\d{1,2}:\d{2}(?::\d{2})?[^\n]*\n?','',text)
        text=re.sub(r'(?m)^\s*#[^\n]*$','',text)
        text=re.sub(r'(?m)^(?:Chapters|影片章节)\s*\n(?=\s*(?:Music|配乐))','',text)
        chapters=[];previous=None
        for s in plan['scenes']:
            if s['section']==previous:continue
            previous=s['section'];t=int(s['start'])
            chapters.append(f'{t//60:02}:{t%60:02} {s["section"]}')
        english_names={'开头':'From Gallery to Space','肖邦与雨滴':'Chopin and the Raindrop Prelude',
            '革命与动荡的时代':'Revolution and upheaval','戈雅':'Goya','籍里柯':'Géricault','德拉克洛瓦':'Delacroix',
            '赖特与火山':'Wright of Derby and Vesuvius','弗里德里希':'Friedrich','雾海上的旅人':'Wanderer above the Sea of Fog',
            '透纳':'Turner','雨 蒸汽与速度':'Rain, Steam and Speed','感受 自然 时间 人的有限性':'Feeling, nature, time and human finitude',
            '开头的旋律回来了':'The opening melody returns','片尾彩蛋 物哀':'Coda · Mono no aware','沙龙':'The Romantic Salon','片尾署名':'Credits'}
        if name=='YouTube-English-description.txt':
            chapters=[c.split(' ',1)[0]+' '+english_names[c.split(' ',1)[1]] for c in chapters]
        text+='\n\n'+('Chapters' if name=='YouTube-English-description.txt' else '影片章节')+'\n'+'\n'.join(chapters)+'\n\n'+tags+'\n\nPortrait sequence: surviving Delacroix fragments and a hypothetical composition reconstruction after the Louvre 1838 study. Reconstruction is labeled on screen.\n'
        (DEST/name).write_text(text,encoding='utf-8')
    credits=dict(previous_source_credits=json.loads((P5/'sources-and-credits.json').read_text()),
                 portrait_study='https://collections.louvre.fr/en/ark:/53355/cl020122665',
                 portrait_originals=json.loads((P6/'pilot-assets/portrait-sources.json').read_text()),
                 reconstruction=json.loads((ASSETS/'portrait-reconstruction-generation.json').read_text()),
                 guide_character=False,local_year_repairs=15,new_cloud_speech_requests=0,
                 duration=plan['duration'],source_sha256=plan['source_sha256'])
    save(DEST/'素材来源与制作说明.json',credits)
    preview_page(plan)

def main():
    PARTS.mkdir(exist_ok=True);DEST.mkdir(exist_ok=True)
    if '--render-only' in sys.argv:
        plan=json.loads((P/'full-plan.json').read_text());render_picture(plan);package(plan)
    elif '--package-only' in sys.argv:package(json.loads((P/'full-plan.json').read_text()))
    else:
        plan=make_plan();prepare_audio(plan);render_picture(plan);package(plan)
    print('FULL PACKAGE COMPLETE:',DEST,flush=True)

if __name__=='__main__':main()
