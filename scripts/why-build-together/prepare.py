"""Build the actual scene timing, mixed local narration, and Chinese captions."""
from __future__ import annotations
from fractions import Fraction
import json, math, re, subprocess, sys
from pathlib import Path
import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'out/why-build-together-v01'
FPS,SR=30,48000
sys.path.insert(0,str(ROOT/'scripts'))
import music_ducking
from youtube_tags import hashtags,tags

def stamp(t,sep=','):
    ms=round(t*1000);h,ms=divmod(ms,3600000);m,ms=divmod(ms,60000);s,ms=divmod(ms,1000)
    return f'{h:02}:{m:02}:{s:02}{sep}{ms:03}'

def read_audio(path):
    a,sr=sf.read(path,dtype='float32');a=a.mean(axis=1) if a.ndim>1 else a
    if sr!=SR:
        ratio=Fraction(SR,sr);a=resample_poly(a,ratio.numerator,ratio.denominator).astype(np.float32)
    active=a[np.abs(a)>.015];rms=float(np.sqrt(np.mean(active**2)))
    a*=min(.105/max(rms,1e-6),.82/max(float(np.abs(a).max()),1e-6))
    return a

def main():
    spec=json.loads((OUT/'script.json').read_text());rows=spec['rows']
    scenes=[];cursor=0;insert=None;audio={}
    for row in rows:
        voice=read_audio(OUT/'audio/louise'/(row['id']+'.wav'));audio[row['id']]=voice
        tail=3.0 if row==rows[-1] else .85 if row['text'].endswith('？') else .45
        count=math.ceil((.2+len(voice)/SR+tail)*FPS)
        scenes.append(dict(**row,start_frame=cursor,frames=count,voice_offset=.2,voice_seconds=len(voice)/SR))
        cursor+=count
        if row['kind']=='insert_intro':
            insert=dict(start_frame=cursor,frames=8514,seconds=283.8)
            cursor+=insert['frames']
    assert insert and insert['frames']==round(insert['seconds']*FPS)
    intro_frames=insert['start_frame'];outro_start=intro_frames+insert['frames']
    for scene in scenes:
        scene['piece']='intro' if scene['start_frame']<intro_frames else 'outro'
        scene['local_start']=scene['start_frame'] if scene['piece']=='intro' else scene['start_frame']-outro_start
    timing=dict(**spec,width=1920,height=1080,fps=FPS,frames=cursor,seconds=cursor/FPS,
                intro_frames=intro_frames,outro_frames=cursor-outro_start,insert=insert,scenes=scenes)
    (OUT/'timeline.json').write_text(json.dumps(timing,ensure_ascii=False,indent=2)+'\n')
    (Path(__file__).parent/'timeline.json').write_text(json.dumps(timing,ensure_ascii=False,indent=2)+'\n')
    for piece,length in [('intro',intro_frames),('outro',cursor-outro_start)]:
        total=length/FPS;voice_mix=np.zeros(round(total*SR),dtype=np.float32);cues=[]
        for scene in scenes:
            if scene['piece']!=piece:continue
            at=scene['local_start']/FPS+scene['voice_offset'];data=audio[scene['id']]
            start=round(at*SR);voice_mix[start:start+len(data)]+=data
            cues.append({'speech':{'start':at,'end':at+len(data)/SR}})
        bed_source=ROOT.parent/'lucas-academy-video-data/curiosity-builds-20261118/v5/music/raindrop.wav'
        raw=subprocess.check_output(['ffmpeg','-v','error','-ss','0' if piece=='intro' else '120','-i',str(bed_source),'-t',str(total),'-ar',str(SR),'-ac','1','-f','f32le','-'])
        bed=np.frombuffer(raw,dtype='<f4').copy();bed=np.pad(bed,(0,max(0,len(voice_mix)-len(bed))))[:len(voice_mix)]
        bed_rms=float(np.sqrt(np.mean(bed**2)));bed_lufs=20*math.log10(max(bed_rms,1e-8))
        env_file=OUT/(piece+'-ducking.wav')
        opening_quiet_end=next(s['start_frame']/FPS for s in scenes if s['id']=='n003')
        music_ducking.envelope(cues,total,bed_lufs,env_file,quiet=[(0,opening_quiet_end)] if piece=='intro' else [])
        env,esr=sf.read(env_file,dtype='float32');gain=np.interp(np.arange(len(voice_mix))/SR,np.arange(len(env))/esr,env).astype(np.float32)
        mixed=voice_mix+bed*gain
        # A soft edge at each piece protects the audio handoff, preserving the full takes.
        fade=min(round(.025*SR),len(mixed)//2);mixed[:fade]*=np.linspace(0,1,fade);mixed[-fade:]*=np.linspace(1,0,fade)
        assert np.isfinite(mixed).all() and np.abs(mixed).max()<.99
        sf.write(OUT/(piece+'.wav'),mixed,SR,subtype='PCM_24')
        sf.write(OUT/(piece+'-voice.wav'),voice_mix,SR,subtype='PCM_24')
    captions=[]
    for scene in scenes:
        aligned=OUT/'audio/aligned'/(scene['id']+'.json')
        if aligned.exists():
            words=json.loads(aligned.read_text())['words'];groups=[];group=[]
            for word in words:
                if group and len(''.join(w['word'] for w in group)+word['word'])>30:
                    groups.append(group);group=[]
                group.append(word)
                if re.search(r'[。！？；]$',word['word']):groups.append(group);group=[]
            if group:groups.append(group)
            for group in groups:
                start=max(0,min(group[0]['start'],scene['voice_seconds']-.05))
                end=max(start+.03,min(group[-1]['end'],scene['voice_seconds']))
                offset=scene['start_frame']/FPS+scene['voice_offset']
                captions.append((offset+start,offset+end,''.join(w['word'] for w in group).strip()))
            continue
        tokens=[x for x in re.split(r'(?<=[，。！？；：])',scene['text']) if x.strip()]
        chunks=[];current=''
        for token in tokens:
            if current and len(current+token)>30:chunks.append(current);current=''
            current+=token
        if current:chunks.append(current)
        weights=[max(1,len(c)) for c in chunks];total=sum(weights);done=0
        for text,weight in zip(chunks,weights):
            a=scene['start_frame']/FPS+scene['voice_offset']+scene['voice_seconds']*done/total
            done+=weight;b=scene['start_frame']/FPS+scene['voice_offset']+scene['voice_seconds']*done/total
            captions.append((a,b,text))
    original=Path(spec['embedded_subtitles']).read_text(encoding='utf-8-sig')
    original_cues=0
    for block in re.split(r'\n\s*\n',original.strip()):
        lines=block.splitlines()
        if len(lines)<3:continue
        timing_text=lines[1]
        nums=re.findall(r'(\d\d):(\d\d):(\d\d),(\d\d\d)',timing_text)
        if len(nums)!=2:continue
        to_seconds=lambda q:int(q[0])*3600+int(q[1])*60+int(q[2])+int(q[3])/1000
        a,b=map(to_seconds,nums);offset=intro_frames/FPS
        captions.append((a+offset,b+offset,'\n'.join(lines[2:])));original_cues+=1
    assert original_cues==27
    captions.sort(key=lambda c:c[0])
    for a,b,text in captions:assert 0<=a<b<=cursor/FPS+.01 and text
    (OUT/'why-build-together.zh-CN.srt').write_text('\n\n'.join(f'{i}\n{stamp(a)} --> {stamp(b)}\n{text}' for i,(a,b,text) in enumerate(captions,1))+'\n')
    (OUT/'why-build-together.zh-CN.vtt').write_text('WEBVTT\n\n'+'\n\n'.join(f'{stamp(a,".")} --> {stamp(b,".")}\n{text}' for a,b,text in captions)+'\n')
    chapter_rows=[]
    names={'n001':'穿越：喂饱五千人','n003':'孩子的需要','n007':'信息与内容','n010':'从兴趣出发，共同创作','n013':'合作、负责与陪伴','n015':'从一个小兴趣开始'}
    for scene in scenes:
        if scene['id'] in names:chapter_rows.append((scene['start_frame']/FPS,names[scene['id']]))
    old=json.loads((ROOT/'docs/curiosity-builds/youtube.json').read_text())
    project_names=['Balanced Chess：逆转与落石','Bible Sequence：经文游戏','梵高房间','Journey of Art 艺术画廊','The Sky：宇宙与流水','Painterly Chameleon：画作里的捉迷藏','7×7 与 11×11 魔方','Coder Arena：编程与排行','用公式建造过山车','你对什么感到好奇？']
    for t,name in zip(old['metadata']['zh']['chapterStarts'],project_names):chapter_rows.append((intro_frames/FPS+t,name))
    chapter_rows.sort();chapters='\n'.join(f'{int(t)//60}:{int(t)%60:02} {name}' for t,name in chapter_rows)
    original_desc=old['metadata']['zh']['description'];credits=original_desc.split('配乐与录音来源\n',1)[-1].split('\n#education',1)[0]
    description=chapters+'\n\n为什么陪孩子一起做项目？从孩子的需要、信息内容和共同创作出发，观看九个 Lucas Academy 项目，再回到合作、负责与陪伴。\n\n项目入口\nhttps://lucasacademy.org\nhttps://is.lucasacademy.org\n\nBy Lucas Academy Team\n新场景：Muse 生成的概念演示；需求金字塔和局部黑白效果由动画制作。项目展示为既有项目录像及概念建造示意。中文旁白：本地 Qwen3-TTS 演绎与本地 Louise 音色转换。\n\n配乐与录音来源\n'+credits+'\n\n'+hashtags(['curiosity','creativeprojects','projectbasedlearning','family','collaboration'])+'\n'
    assert description.startswith('0:00 ') and len(description)<5000
    (OUT/'youtube-description.zh.txt').write_text(description)
    (OUT/'youtube-tags.txt').write_text(tags(['curiosity','creativeprojects','projectbasedlearning','family','collaboration'])+'\n')
    (OUT/'chapters.json').write_text(json.dumps([dict(seconds=t,title=name) for t,name in chapter_rows],ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(seconds=cursor/FPS,intro_seconds=intro_frames/FPS,embedded_seconds=283.8,outro_seconds=(cursor-outro_start)/FPS,caption_count=len(captions)),ensure_ascii=False))

if __name__=='__main__':main()
