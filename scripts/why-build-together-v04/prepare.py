"""Build the actual scene timing, mixed local narration, and Chinese captions."""
from __future__ import annotations
from fractions import Fraction
import json, math, re, subprocess, sys
from pathlib import Path
import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'out/why-build-together-v04'
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

def voice_path(language,id):
    return OUT/('audio/louise' if language=='zh' else 'audio/en/louise')/(id+'.wav')

def caption_rows(scenes,language):
    captions=[]
    folder=OUT/('audio/aligned' if language=='zh' else 'audio/en/aligned')
    for scene in scenes:
        words=json.loads((folder/(scene['id']+'.json')).read_text())['words'];groups=[];group=[]
        for word in words:
            if language=='zh' and scene['id']=='n007' and word['word'].strip()=='和' and group:
                groups.append(group);group=[]
            limit=30 if language=='zh' else 74
            candidate=''.join(w['word'] for w in group)+word['word']
            if group and len(candidate)>limit:groups.append(group);group=[]
            group.append(word)
            if re.search(r'[。！？；]$' if language=='zh' else r'[.!?;]$',word['word']):groups.append(group);group=[]
        if group:groups.append(group)
        seconds=scene['voice_seconds'] if language=='zh' else scene['voice_seconds_en']
        for group in groups:
            start=max(0,min(group[0]['start'],seconds-.05));end=max(start+.03,min(group[-1]['end'],seconds))
            at=scene['start_frame']/FPS+scene['voice_offset']
            text=''.join(w['word'] for w in group).strip()
            captions.append((at+start,at+end,text))
    return captions

def main():
    spec=json.loads((OUT/'script.json').read_text());en=json.loads((OUT/'script-en.json').read_text())
    rows=spec['rows'];en_byid={r['id']:r for r in en['rows']}
    scenes=[];cursor=0;audio={'zh':{},'en':{}};insert=None
    for row in rows:
        id=row['id'];z=read_audio(voice_path('zh',id));e=read_audio(voice_path('en',id))
        audio['zh'][id]=z;audio['en'][id]=e
        tail=.85 if row['text'].endswith('？') else .45
        count=math.ceil((.2+max(len(z),len(e))/SR+tail)*FPS)
        scenes.append(dict(**row,text_en=en_byid[id]['text'],start_frame=cursor,local_start=cursor,
            frames=count,piece='intro',voice_offset=.2,voice_seconds=len(z)/SR,voice_seconds_en=len(e)/SR))
        cursor+=count
        if row['kind']=='insert_intro':
            insert=dict(start_frame=cursor,frames=8514,seconds=283.8);cursor+=8514
    assert insert and scenes[-1]['kind']=='insert_intro'
    intro_frames=insert['start_frame'];total=intro_frames/FPS
    timing=dict(**spec,width=1920,height=1080,fps=FPS,frames=cursor,seconds=cursor/FPS,
        intro_frames=intro_frames,outro_frames=0,insert=insert,scenes=scenes,languages=['zh','en'],default_audio='zh')
    (OUT/'timeline.json').write_text(json.dumps(timing,ensure_ascii=False,indent=2)+'\n')
    (Path(__file__).parent/'timeline.json').write_text(json.dumps(timing,ensure_ascii=False,indent=2)+'\n')
    bed_source=ROOT.parent/'lucas-academy-video-data/curiosity-builds-20261118/v5/music/raindrop.wav'
    raw=subprocess.check_output(['ffmpeg','-v','error','-i',str(bed_source),'-t',str(total),'-ar',str(SR),'-ac','1','-f','f32le','-'])
    bed=np.frombuffer(raw,dtype='<f4').copy();count=intro_frames*1600
    bed=np.pad(bed,(0,max(0,count-len(bed))))[:count]
    bed_lufs=20*math.log10(max(float(np.sqrt(np.mean(bed**2))),1e-8))
    quiet_end=next(s['start_frame']/FPS for s in scenes if s['id']=='n003')
    for language in ['zh','en']:
        voice=np.zeros(count,dtype=np.float32);cues=[]
        for scene in scenes:
            at=scene['start_frame']/FPS+.2;data=audio[language][scene['id']];index=round(at*SR)
            voice[index:index+len(data)]+=data;cues.append({'speech':{'start':at,'end':at+len(data)/SR}})
        env_file=OUT/(f'intro-{language}-ducking.wav')
        music_ducking.envelope(cues,total,bed_lufs,env_file,quiet=[(0,quiet_end)])
        env,esr=sf.read(env_file,dtype='float32');gain=np.interp(np.arange(count)/SR,np.arange(len(env))/esr,env).astype(np.float32)
        mix=voice+bed*gain;fade=round(.025*SR)
        mix[:fade]*=np.linspace(0,1,fade);mix[-fade:]*=np.linspace(1,0,fade)
        assert np.isfinite(mix).all() and np.abs(mix).max()<.99
        sf.write(OUT/('intro.wav' if language=='zh' else 'intro-en.wav'),mix,SR,subtype='PCM_24')
        sf.write(OUT/(f'intro-{language}-voice.wav'),voice,SR,subtype='PCM_24')
    project=json.loads((ROOT.parent/'lucas-academy-video-data/curiosity-builds-20261118/v10/records/subtitles.json').read_text())
    assert len(project['cues'])==27 and project['total_frames']==8514
    for language in ['zh','en']:
        captions=caption_rows(scenes,language)
        for cue in project['cues']:
            captions.append(((intro_frames+cue['start'])/FPS,(intro_frames+cue['end'])/FPS,cue[language]))
        captions.sort(key=lambda c:c[0])
        assert all(0<=a<b<=cursor/FPS+.001 and text for a,b,text in captions)
        assert all(captions[i][0]>=captions[i-1][1]-.011 for i in range(1,len(captions)))
        suffix='zh-CN' if language=='zh' else 'en'
        (OUT/f'why-build-together.{suffix}.srt').write_text('\n\n'.join(f'{i}\n{stamp(a)} --> {stamp(b)}\n{text}' for i,(a,b,text) in enumerate(captions,1))+'\n')
        (OUT/f'why-build-together.{suffix}.vtt').write_text('WEBVTT\n\n'+'\n\n'.join(f'{stamp(a,".")} --> {stamp(b,".")}\n{text}' for a,b,text in captions)+'\n')
    old=json.loads((ROOT/'docs/curiosity-builds/youtube.json').read_text())
    names={'zh':{'n001':'穿越：喂饱五千人','n003':'孩子的需要','n007':'信息与内容','n010':'从兴趣出发，共同创作'},
        'en':{'n001':'Feeding five thousand','n003':'What children need','n007':'An abundance of content','n010':'Building from curiosity'}}
    project_names={'zh':['Balanced Chess：逆转与落石','Bible Sequence：经文游戏','梵高房间','Journey of Art 艺术画廊','The Sky：宇宙与流水','Painterly Chameleon：画作里的捉迷藏','7×7 与 11×11 魔方','Coder Arena：编程与排行','用公式建造过山车','你对什么感到好奇？'],
        'en':['Balanced Chess: Comeback and Rockfall','Bible Sequence','Van Gogh House','Journey of Art','The Sky','Painterly Chameleon','7×7 and 11×11 cubes','Coder Arena','A roller coaster from formulas','What are you curious about?']}
    original_desc=old['metadata']['zh']['description'];credits=original_desc.split('配乐与录音来源\n',1)[-1].split('\n#education',1)[0].strip()
    bodies={'zh':'为什么陪孩子一起做软件项目？从孩子的需要、信息内容和共同创作出发，完整观看九个 Lucas Academy 项目。\n\n项目入口\nhttps://lucasacademy.org\nhttps://is.lucasacademy.org\n\nBy Lucas Academy Team\nMuse 概念镜头采用白底铅笔画效果；需求金字塔为生成的静态手绘插画，图解使用黑底白线动画。项目展示包含既有项目录像及概念建造示意。配音：中文与英文，Louise，经授权参考音色在本机生成。\n\n配乐与录音来源\n',
        'en':"Why build software projects together? Consider children's need for belonging and recognition, what an abundance of content offers, and what matters in the process. Then explore nine Lucas Academy projects.\n\nExplore the projects\nhttps://lucasacademy.org\nhttps://is.lucasacademy.org\n\nBy Lucas Academy Team\nMuse concept scenes are styled as pencil drawings. The needs pyramid is an AI-generated illustration, with original diagram animations. The project film combines project recordings and conceptual visualizations. Narration: Chinese and English, Louise, generated locally with an authorized reference voice.\n\nMusic and recordings\n"}
    for language in ['zh','en']:
        chapter_rows=[(s['start_frame']/FPS,names[language][s['id']]) for s in scenes if s['id'] in names[language]]
        chapter_rows += [(intro_frames/FPS+t,name) for t,name in zip(old['metadata']['zh']['chapterStarts'],project_names[language])]
        chapter_rows.sort();head='\n'.join(f'{int(t)//60}:{int(t)%60:02} {name}' for t,name in chapter_rows)
        description=head+'\n\n'+bodies[language]+credits+'\n\n'+hashtags(['curiosity','creativeprojects','projectbasedlearning','family','collaboration'])+'\n'
        assert description.startswith('0:00 ') and len(description)<5000
        (OUT/f'youtube-description.{language}.txt').write_text(description)
        (OUT/('chapters.json' if language=='zh' else 'chapters.en.json')).write_text(json.dumps([dict(seconds=t,title=name) for t,name in chapter_rows],ensure_ascii=False,indent=2)+'\n')
    (OUT/'youtube-tags.txt').write_text(tags(['curiosity','creativeprojects','projectbasedlearning','family','collaboration'])+'\n')
    (OUT/'youtube-title.zh.txt').write_text(spec['title']+'\n');(OUT/'youtube-title.en.txt').write_text(en['title']+'\n')
    print(json.dumps(dict(seconds=cursor/FPS,intro_seconds=total,embedded_seconds=283.8,
        chinese_takes_reused=True,english_takes=12,shared_timeline=True,narration_time_stretch=False),ensure_ascii=False))

if __name__=='__main__':main()
