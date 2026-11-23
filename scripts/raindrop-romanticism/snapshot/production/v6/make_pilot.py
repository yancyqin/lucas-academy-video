"""Build the owner-requested bilingual pilot before a full Romanticism recut."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import html
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import textwrap
import wave

import numpy as np
from PIL import Image,ImageDraw,ImageFont

P=Path(__file__).resolve().parent
P5=P.parent/'v5';ASSETS=P/'pilot-assets';PARTS=P/'pilot-parts'
DEST=Path('@USER_HOME@/Desktop/压力焦虑肖邦浪漫-新版样片')
FF='/opt/homebrew/bin/ffmpeg';FPS=24;SR=48000;W=1920;H=1080
BASE=P5/'parts/retimed.mp4'
MUSIC=P.parents[2]/'romanticism-music-gallery/music/prelude-28-15.m4a'
FONT=Path('/System/Library/Fonts/Supplemental')


def run(command):
    subprocess.run(command,check=True)


def decode(path,channels=1):
    data=subprocess.check_output([FF,'-v','error','-i',str(path),'-ar',str(SR),'-ac',str(channels),'-f','f32le','-'])
    return np.frombuffer(data,dtype='<f4').reshape(-1,channels).copy()


def write_wav(path,samples):
    if samples.ndim==1:samples=samples[:,None]
    with wave.open(str(path),'wb') as writer:
        writer.setparams((samples.shape[1],2,SR,0,'NONE','not compressed'))
        writer.writeframes(np.round(np.clip(samples,-1,1)*32767).astype('<i2').tobytes())


def srt_time(seconds):
    ms=round(seconds*1000);hours,ms=divmod(ms,3600000);minutes,ms=divmod(ms,60000);secs,ms=divmod(ms,1000)
    return f'{hours:02}:{minutes:02}:{secs:02},{ms:03}'


def subtitle_chunks(text,language):
    if language=='en':
        sentences=re.split(r'(?<=[.!?])\s+',text.strip());limit=82
    else:
        sentences=re.findall(r'[^。！？]+[。！？]?[”’]?',text.strip());limit=42
    result=[]
    for sentence in sentences:
        if not sentence:continue
        if len(sentence)<=limit:result.append(sentence);continue
        if language=='en':result.extend(textwrap.wrap(sentence,width=limit,break_long_words=False,break_on_hyphens=False))
        else:
            while len(sentence)>limit:
                options=[i+1 for i,c in enumerate(sentence[:limit]) if c in '，、；：']
                end=max(options) if options and max(options)>18 else limit
                result.append(sentence[:end]);sentence=sentence[end:]
            if sentence:result.append(sentence)
    return result


def caption_lines(text,language):
    if language=='en':return '\n'.join(textwrap.wrap(text,width=43,break_long_words=False,break_on_hyphens=False))
    return '\n'.join(text[i:i+22] for i in range(0,len(text),22))


def prepare_audio():
    script=json.loads((P/'narration-bilingual.json').read_text())
    manifest=json.loads((P/'voice-manifest.json').read_text())
    assert script['source_sha256']==manifest['source_sha256']
    wanted={f'n{i:03}' for i in range(1,8)}
    rows=[r for r in script['rows'] if r['spoken'] and r['id'] in wanted]
    chunks={};durations={}
    for language in ['en','zh']:
        for row in rows:
            items=[i for i in manifest['items'] if i['language']==language and i['paragraph_id']==row['id']]
            values=[]
            for item in items:
                audio=decode(Path(item['file']))[:,0]
                assert np.isfinite(audio).all() and len(audio)>SR*.3
                values.append((item['text'],audio))
            compact=lambda t:re.sub(r'\s+','',t)
            assert compact(''.join(t for t,_ in values))==compact(row[language])
            chunks[(language,row['id'])]=values
            durations[(language,row['id'])]=sum(len(a) for _,a in values)/SR
    cursor=24;scenes=[]
    for row in rows:
        maximum=max(durations[(lang,row['id'])] for lang in ['zh','en'])
        count=math.ceil((maximum+.65)*FPS)
        scenes.append(dict(id=row['id'],section=row['section'].strip(),first=cursor,count=count,
                           start=cursor/FPS,end=(cursor+count)/FPS,voice_start=(cursor+6)/FPS,
                           text_zh=row['zh'],text_en=row['en'],
                           voice_seconds={lang:durations[(lang,row['id'])] for lang in ['zh','en']}))
        cursor+=count
        if row['id']=='n001':
            scenes.append(dict(id='listen',section='listen',first=cursor,count=240,start=cursor/FPS,end=(cursor+240)/FPS))
            cursor+=240
    total=cursor+72;length=total*(SR//FPS)
    voice={lang:np.zeros(length,np.float32) for lang in ['zh','en']};captions={lang:[] for lang in ['zh','en']}
    duck=np.ones(length,np.float32)
    for scene in scenes:
        if not scene['id'].startswith('n'):continue
        first=round(scene['voice_start']*SR)
        longest=round(max(scene['voice_seconds'].values())*SR);last=first+longest
        attack=max(0,first-12000);release=min(length,last+19200)
        duck[attack:first]=np.minimum(duck[attack:first],np.linspace(1,.25,first-attack))
        duck[first:last]=np.minimum(duck[first:last],.25)
        duck[last:release]=np.minimum(duck[last:release],np.linspace(.25,1,release-last))
        for lang in ['zh','en']:
            offset=first
            for text,audio in chunks[(lang,scene['id'])]:
                assert offset+len(audio)<=round(scene['end']*SR)
                voice[lang][offset:offset+len(audio)]=audio
                pieces=subtitle_chunks(text,lang);weights=[len(re.sub(r'\s','',part)) for part in pieces];unit=0
                for part,weight in zip(pieces,weights):
                    a=offset/SR+len(audio)/SR*unit/sum(weights);unit+=weight
                    b=offset/SR+len(audio)/SR*unit/sum(weights)
                    captions[lang].append(dict(start=a,end=b,text=caption_lines(part,lang),paragraph_id=scene['id']))
                offset+=len(audio)
            active=voice[lang][first:offset]
            assert len(active)>0
    for lang in ['zh','en']:
        active=voice[lang][np.abs(voice[lang])>.008]
        voice[lang]*=.11/np.sqrt(np.mean(active**2))
        write_wav(PARTS/f'dry-{lang}.wav',voice[lang])
    song=decode(MUSIC,2);song*=.065/np.sqrt(np.mean(song**2))
    listen=next(s for s in scenes if s['id']=='listen');reset=round(listen['start']*SR)
    score=np.empty((length,2),np.float32);score[:reset]=song[:reset];score[reset:]=song[:length-reset]
    score[max(0,reset-9600):reset]*=np.linspace(1,0,min(reset,9600))[:,None]
    tail=round(2.5*SR);score[-tail:]*=np.linspace(1,0,tail)[:,None]
    score*=duck[:,None]
    assert np.max(np.abs(voice['en'][reset:reset+10*SR]))==0
    assert np.max(np.abs(voice['zh'][reset:reset+10*SR]))==0
    corr=float(np.corrcoef(score[reset:reset+10*SR,0],song[:10*SR,0])[0,1]);assert corr>.99999
    mixes={lang:score+np.repeat(voice[lang][:,None],2,axis=1) for lang in ['zh','en']}
    gain=min(1,.92/max(float(np.max(np.abs(a))) for a in mixes.values()))
    for lang,audio in mixes.items():
        audio*=gain;write_wav(PARTS/f'mix-{lang}.wav',audio)
        output=DEST/('02-Chinese-aligned-audio.wav' if lang=='zh' else 'pilot-english-mix.wav')
        run([FF,'-v','error','-y','-i',str(PARTS/f'mix-{lang}.wav'),'-c:a','pcm_s24le',str(output)])
        filename='03-English.srt' if lang=='en' else '04-Chinese.srt'
        (DEST/filename).write_text('\n'.join(f'{i}\n{srt_time(c["start"])} --> {srt_time(c["end"])}\n{c["text"]}\n' for i,c in enumerate(captions[lang],1)),encoding='utf-8')
    run([FF,'-v','error','-y','-i',str(DEST/'02-Chinese-aligned-audio.wav'),'-c:a','libmp3lame','-q:a','2',str(DEST/'Chinese-preview.mp3')])
    plan=dict(fps=FPS,frames=total,duration=total/FPS,scenes=scenes,captions=captions,source_sha256=script['source_sha256'],
              voices={'zh':'MiniMax performance → Fangfang','en':'MiniMax performance → Louise'},
              speech_speed_changed=False,common_scene_timing=True,raindrop_starts_at_zero=True,
              listening_restarts_at_zero=True,listen_start=listen['start'],listen_seconds=10,reprise_correlation=corr)
    (P/'pilot-plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2))
    print('Common bilingual timeline:',round(plan['duration'],3),'seconds',flush=True)
    return plan


def labels():
    def font(name,size):return ImageFont.truetype(str(FONT/name),size)
    image=Image.new('RGBA',(W,H));draw=ImageDraw.Draw(image)
    draw.text((100,850),'Pressure? Anxiety?',font=font('Georgia Bold.ttf',48),fill=(245,230,192),stroke_width=1,stroke_fill=(25,19,15,200))
    draw.text((100,912),'Chopin? Romanticism?',font=font('Georgia Bold.ttf',48),fill=(245,230,192),stroke_width=1,stroke_fill=(25,19,15,200))
    image.save(ASSETS/'pilot-title.png')
    image=Image.new('RGBA',(W,H));draw=ImageDraw.Draw(image)
    draw.text((100,976),'From Gallery to Space',font=font('Georgia.ttf',34),fill=(250,235,205),stroke_width=1,stroke_fill=(20,20,25,180))
    image.save(ASSETS/'transition-label.png')
    image=Image.new('RGBA',(W,H));draw=ImageDraw.Draw(image)
    draw.text((W/2,905),'Chopin and George Sand',anchor='mm',font=font('Georgia.ttf',40),fill=(250,239,210))
    draw.text((W/2,963),'Eugène Delacroix · 1838 · Two surviving fragments',anchor='mm',font=font('Arial.ttf',26),fill=(215,202,177))
    image.save(ASSETS/'portrait-label.png')


def encode_options(count):
    return ['-frames:v',str(count),'-an','-c:v','h264_videotoolbox','-b:v','12M','-pix_fmt','yuv420p','-video_track_timescale','12288','-g','48','-bf','0']


def render_picture(plan):
    def edge(identifier,end=False):return next(s['end'] if end else s['start'] for s in plan['scenes'] if s['id']==identifier)
    shots=[dict(id='entrance',start=0,end=edge('n003'),source=BASE,trim=0,seconds=42.333333),
           dict(id='portrait',start=edge('n003'),end=edge('n003',True),source=BASE,trim=61.5,seconds=6.5),
           dict(id='monastery',start=edge('n004'),end=edge('n004',True),source=P.parent/'v2/footage/O02-monastery.mp4',trim=.35,seconds=9.3),
           dict(id='cold-water',start=edge('n005'),end=edge('n005',True),source=P5/'footage/cold-water-loop.mp4',trim=0,seconds=18.708333),
           dict(id='return-gallery',start=edge('n006'),end=plan['duration'],source=BASE,trim=131.083333,seconds=23.5)]
    for i,shot in enumerate(shots):
        shot['padded_start']=shot['start']-(.5 if i else 0)
        shot['padded_end']=shot['end']+(.5 if i<len(shots)-1 else 0)
        shot['count']=round((shot['padded_end']-shot['padded_start'])*FPS)
    def render(shot):
        dest=PARTS/(shot['id']+'.mp4');seconds=shot['count']/FPS
        effect=f'trim=duration={shot["seconds"]:.9f},setpts=(PTS-STARTPTS)*{seconds/shot["seconds"]:.12f},fps=24,scale=1920:1080,setsar=1,tpad=stop_mode=clone:stop_duration=0.15'
        command=[FF,'-v','error','-y','-ss',str(shot['trim']),'-i',str(shot['source'])]
        if shot['id']=='portrait':
            command+=['-loop','1','-framerate','24','-i',str(ASSETS/'george-sand-delacroix-1838.jpg'),
                      '-loop','1','-framerate','24','-i',str(ASSETS/'chopin-delacroix-1838.jpg'),
                      '-loop','1','-framerate','24','-i',str(ASSETS/'portrait-label.png')]
            graph=f'[0:v]{effect},gblur=sigma=20,eq=brightness=-0.28:saturation=0.55[bg];'
            graph+='[1:v]scale=-2:750,format=rgba,pad=iw+12:ih+12:6:6:color=0xa48b57[left];[2:v]scale=-2:750,format=rgba,pad=iw+12:ih+12:6:6:color=0xa48b57[right];'
            graph+='[bg][left]overlay=x=335:y=95[p1];[p1][right]overlay=x=975:y=95[p2];[p2][3:v]overlay=0:0:shortest=1[v]'
            command+=['-filter_complex_threads','2','-filter_complex',graph,'-map','[v]']
        else:command+=['-filter_threads','2','-vf',effect]
        run(command+encode_options(shot['count'])+[str(dest)])
        print('Rendered picture shot',shot['id'],flush=True);return dest
    with ThreadPoolExecutor(max_workers=2) as pool:files=list(pool.map(render,shots))
    graph=[];previous='0:v'
    for i in range(1,len(shots)):
        name=f'x{i}'
        graph.append(f'[{previous}][{i}:v]xfade=transition=fade:duration=1:offset={shots[i]["start"]-.5:.9f}[{name}]')
        previous=name
    clean=PARTS/'pilot-clean.mp4';command=[FF,'-v','error','-y','-filter_complex_threads','2']
    for f in files:command+=['-i',str(f)]
    run(command+['-filter_complex',';'.join(graph),'-map',f'[{previous}]',*encode_options(plan['frames']),str(clean)])
    guide=ASSETS/'romanticism-guide-v1.png';title=ASSETS/'pilot-title.png';transition=ASSETS/'transition-label.png'
    windows=[(2.0,7.0,1520,680,300),(15.2,23.6,1550,640,350),
             (edge('n003')-.3,edge('n003')+2.8,1580,660,350),
             (edge('n007')+.6,plan['duration']-1.5,1570,650,350)]
    graph=['[1:v]format=rgba,split=4[g0][g1][g2][g3]'];previous='0:v'
    for i,(start,end,x,y,height) in enumerate(windows):
        graph.append(f'[g{i}]scale=-2:{height},fade=t=in:st={start}:d=0.7:alpha=1,fade=t=out:st={end-.7}:d=0.7:alpha=1[s{i}]')
        graph.append(f'[{previous}][s{i}]overlay=x={x}+3*sin(t*1.1):y={y}+4*sin(t*1.4):enable=\'between(t,{start},{end})\'[v{i}]')
        previous=f'v{i}'
    graph+=['[2:v]format=rgba,fade=t=in:st=0.35:d=0.6:alpha=1,fade=t=out:st=4.6:d=0.7:alpha=1[title]',
            f'[{previous}][title]overlay=0:0:enable=\'between(t,0.35,5.3)\'[titled]',
            '[3:v]format=rgba,fade=t=in:st=7.5:d=0.7:alpha=1,fade=t=out:st=11.4:d=0.7:alpha=1[transition]',
            '[titled][transition]overlay=0:0:enable=\'between(t,7.5,12.1)\'[labeled]',
            f'[labeled]fade=t=out:st={plan["duration"]-1.2}:d=1.2,format=yuv420p[final]']
    picture=PARTS/'pilot-picture.mp4'
    run([FF,'-v','error','-y','-i',str(clean),'-loop','1','-framerate','24','-i',str(guide),
         '-loop','1','-framerate','24','-i',str(title),'-loop','1','-framerate','24','-i',str(transition),
         '-filter_complex_threads','2','-filter_complex',';'.join(graph),'-map','[final]',*encode_options(plan['frames']),str(picture)])
    output=DEST/'01-English-preview.mp4'
    run([FF,'-v','error','-y','-i',str(picture),'-i',str(DEST/'pilot-english-mix.wav'),'-map','0:v:0','-map','1:a:0',
         '-c:v','copy','-c:a','aac','-b:a','256k','-metadata:s:a:0','language=eng','-movflags','+faststart',str(output)])
    plan['picture_shots']=[{k:str(v) if isinstance(v,Path) else v for k,v in s.items()} for s in shots]
    plan['guide_windows']=[dict(start=a,end=b,x=x,y=y,height=h) for a,b,x,y,h in windows]
    (P/'pilot-plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2))
    print('English pilot video ready:',output,flush=True)


def preview_page(plan):
    shutil.copy2(ASSETS/'romanticism-guide-v1.png',DEST/'Guide-design.png')
    shutil.copy2(ASSETS/'guide-generation.json',DEST/'Guide-design-generation.json')
    chapters=''.join(f'<button data-seek="{s["start"]:.3f}">{int(s["start"])//60:02}:{int(s["start"])%60:02} · {html.escape(s.get("text_zh","纯音乐十秒")[:20])}</button>' for s in plan['scenes'])
    data=json.dumps(plan['captions'],ensure_ascii=False).replace('</','<\\/')
    page='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>浪漫主义沙龙 · 导览角色样片</title><style>
*{box-sizing:border-box}body{margin:0;background:#141719;color:#ece5d8;font:16px/1.75 system-ui,sans-serif}main{max-width:1180px;margin:auto;padding:32px 24px 70px}h1{font-size:29px;line-height:1.3}p{color:#c4bba9}a{color:#e1c58c}button,select{font:inherit;background:#292d30;color:#eee4d1;border:1px solid #8b795b;border-radius:5px;padding:6px 13px;cursor:pointer}button[aria-pressed=true]{background:#a88b56;color:#161615}.controls,.links{display:flex;gap:12px;flex-wrap:wrap;margin:16px 0}.screen{position:relative}video{width:100%;display:block;background:#08090b}.captions{position:absolute;bottom:64px;left:9%;right:9%;text-align:center;pointer-events:none;white-space:pre-line;font-size:24px;line-height:1.4;text-shadow:0 2px 4px #000,1px 0 3px #000;color:#fff}.captions span{background:#0009;padding:2px 7px;box-decoration-break:clone}details{margin:24px 0}summary{cursor:pointer;color:#e1c58c}.chapters{display:grid;grid-template-columns:repeat(2,1fr);gap:8px}.chapters button{text-align:left;font-size:14px}.design{display:flex;gap:30px;align-items:center;margin-top:30px}.design img{width:200px;max-width:40%;height:auto}.design p{max-width:670px}footer{font-size:14px;border-top:1px solid #554e41;padding-top:20px;margin-top:30px}@media(max-width:650px){main{padding:20px 14px}.captions{font-size:15px;bottom:46px}.chapters{grid-template-columns:1fr}h1{font-size:23px}.design{gap:15px}}
</style><main><h1>压力？焦虑？肖邦？浪漫？ · 导览角色样片</h1><p>连续开场样片：现实画廊 → 深空沙龙 → 肖邦与桑的肖像 → 马略卡雨夜与水底幻景。使用已确认文案和已完成的 MiniMax 演绎＋Fangfang／Louise 换声。画面按两种语言的共同场景时长调整。</p>
<div class="controls"><button id="english" aria-pressed="true">英文 Louise</button><button id="chinese" aria-pressed="false">中文 Fangfang</button><label>字幕 <select id="subtitle"><option value="none">关闭</option><option value="en">English</option><option value="zh">中文</option></select></label></div>
<div class="screen"><video id="film" controls preload="metadata" src="01-English-preview.mp4"></video><div id="caption" class="captions" aria-live="off"></div></div><audio id="zh" preload="metadata" src="Chinese-preview.mp3"></audio>
<div class="links"><a href="01-English-preview.mp4" download>下载英文视频</a><a href="02-Chinese-aligned-audio.wav" download>下载中文同步音轨 WAV</a><a href="03-English.srt" download>英文字幕 SRT</a><a href="04-Chinese.srt" download>中文字幕 SRT</a></div>
<p>下载的视频没有烧录字幕；这里的字幕可选开关。中文按钮会切换到单独音轨，并跟随视频播放、暂停和跳转。</p><details><summary>按段落跳转</summary><div class="chapters">'''+chapters+'''</div></details>
<div class="design"><img src="Guide-design.png" alt="浪漫主义导览小精灵"><div><h2>导览角色视觉方案</h2><p>暖金提灯、深绿十九世纪服饰与微弱星光。以小幅悬浮和引导手势出现，肖邦雨夜的叙述中淡出；肖像近看时留出完整的欣赏空间。本样片先验证角色形象、出场节奏和在沙龙里的尺度。</p><p><a href="Guide-design.png">查看角色设计图</a> · <a href="Guide-design-generation.json">内置 imagegen 的生成方式与完整提示词</a></p></div></div>
<footer><p>肖像：德拉克洛瓦 1838 年双人肖像后来被分割，本片并置现存的乔治·桑与肖邦两块原作片段；画面标签注明 “Two surviving fragments”。<a href="https://collections.louvre.fr/en/ark:/53355/cl020122665">卢浮宫作品记录</a> · <a href="https://lex.dk/Eug%C3%A8ne_Delacroix">桑肖像图源与公共领域标记</a>。</p><p>本次为样片。按约定，确认角色与样片效果后再制作完整新版。</p></footer>
<script>const CUES='''+data+''';const v=document.getElementById('film'),a=document.getElementById('zh'),cap=document.getElementById('caption'),sub=document.getElementById('subtitle');let language='en';
function sync(force=false){if(language==='zh'&&(force||Math.abs(a.currentTime-v.currentTime)>.13))a.currentTime=v.currentTime}
function choose(lang){a.pause();language=lang;v.muted=lang==='zh';sync(true);document.getElementById('english').setAttribute('aria-pressed',String(lang==='en'));document.getElementById('chinese').setAttribute('aria-pressed',String(lang==='zh'));if(lang==='zh'&&!v.paused)a.play().catch(()=>{})}
document.getElementById('english').onclick=()=>choose('en');document.getElementById('chinese').onclick=()=>choose('zh');v.onplay=()=>{sync(true);if(language==='zh')a.play().catch(()=>{})};v.onpause=()=>a.pause();v.onseeking=()=>{a.pause();sync(true)};v.onseeked=()=>{sync(true);if(language==='zh'&&!v.paused)a.play().catch(()=>{})};v.onended=()=>a.pause();v.onvolumechange=()=>{a.volume=v.volume};v.onwaiting=()=>a.pause();v.onplaying=()=>{sync(true);if(language==='zh')a.play().catch(()=>{})};
function update(){sync();const cues=CUES[sub.value]||[];const c=cues.find(c=>v.currentTime>=c.start&&v.currentTime<c.end);cap.textContent=c?c.text:''}v.ontimeupdate=update;sub.onchange=update;document.querySelectorAll('[data-seek]').forEach(b=>b.onclick=()=>{v.currentTime=Number(b.dataset.seek);v.play().catch(()=>{})});
</script></main></html>'''
    (DEST/'样片预览.html').write_text(page,encoding='utf-8')


def main():
    PARTS.mkdir(exist_ok=True);DEST.mkdir(exist_ok=True)
    labels();plan=prepare_audio();render_picture(plan);preview_page(plan)
    print('Pilot package complete:',DEST,flush=True)


if __name__=='__main__':main()
