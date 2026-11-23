"""Audio revision: silent opening, two-sided score fades, natural voice timing."""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

import numpy as np

P=Path(__file__).resolve().parent;V7=P.parent/'v7';V6=P.parent/'v6'
sys.path.insert(0,str(V7))
import full_film as film

FF=film.FF;SR=film.SR;FPS=film.FPS
DELIVERY=P/'delivery'
DESKTOP=film.DEST

def save(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')

def half_cosine(count):
    return ((1-np.cos(np.linspace(0,np.pi,count)))/2).astype(np.float32)

def score_spans(plan):
    # The first spoken invitation is dry; the first piano begins at the listening cue.
    return film.score_spans(plan)[1:]

def voice_edges(samples):
    """Tiny click prevention without trimming, stretching, or gating words."""
    audio=samples.copy();rms=float(np.sqrt(np.mean(audio**2)))
    fade_in=min(round(.006*SR),len(audio)//4)
    # Fade only low-energy final room/noise tails more gently; preserve voiced endings.
    tail=min(round(.1*SR),len(audio)//4)
    quiet=float(np.sqrt(np.mean(audio[-tail:]**2)))<max(.0015,rms*.03)
    fade_out=tail if quiet else min(round(.008*SR),len(audio)//4)
    audio[:fade_in]*=half_cosine(fade_in)
    audio[-fade_out:]*=half_cosine(fade_out)[::-1]
    assert len(audio)==len(samples)
    return audio,dict(fade_in_ms=fade_in/SR*1000,fade_out_ms=fade_out/SR*1000,quiet_tail=quiet,
                      source_samples=len(samples),output_samples=len(audio),speed=1.0)

def write_pcm24(path,audio):
    subprocess.run([FF,'-v','error','-y','-f','f32le','-ar',str(SR),'-ac','2','-i','-',
        '-c:a','pcm_s24le',str(path)],input=audio.astype('<f4',copy=False).tobytes(),check=True)

def prepare(plan_source=None,overrides_source=None):
    DELIVERY.mkdir(exist_ok=True)
    plan=json.loads((plan_source or V7/'full-plan.json').read_text())
    overrides=json.loads((overrides_source or P/'opening-overrides.json').read_text())
    replacement={(i['language'],i['id']):i for i in overrides['items']}
    for item in plan['voice_fragments']:
        key=(item['language'],item['id'])
        if key in replacement:
            value=replacement[key];assert value['text']==item['text'];item.update(value)
    for scene in plan['scenes']:
        if not scene['id'].startswith('n'):continue
        for lang in ['zh','en']:
            scene['voice_seconds'][lang]=sum(i['seconds'] for i in plan['voice_fragments'] if i['language']==lang and i['paragraph_id']==scene['id'])
    length=plan['frames']*(SR//FPS)
    songs={};music={};score=np.zeros((length,2),np.float32)
    files={'rain':'prelude-28-15.m4a','n9':'nocturne-9-2.m4a','ncs':'nocturne-c-sharp.m4a'}
    for name,file in files.items():
        s=film.decode(film.GALLERY/'music'/file,2);gain=.065/np.sqrt(np.mean(s**2));s*=gain;songs[name]=s
        music[name]=dict(file=str(film.GALLERY/'music'/file),gain=float(gain))
    spans=score_spans(plan);span_receipts=[]
    for start,end,name,offset in spans:
        a=round(start*SR);z=round(end*SR);src=round(offset*SR);n=z-a;s=songs[name]
        available=min(n,len(s)-src);assert available>=n-int(.06*SR)
        piece=np.zeros((n,2),np.float32);piece[:available]=s[src:src+available]
        fade_in=min(round(1.5*SR),n//3)
        fade_out=min(round((4 if end==plan['duration'] else 1.5)*SR),n//3)
        piece[:fade_in]*=half_cosine(fade_in)[:,None]
        piece[-fade_out:]*=half_cosine(fade_out)[::-1,None]
        assert np.max(np.abs(piece[0]))==0 and np.max(np.abs(piece[-1]))==0
        score[a:z]=piece
        span_receipts.append(dict(start=start,end=end,track=name,source_offset=offset,
            fade_in=fade_in/SR,fade_out=fade_out/SR,curve='half cosine',
            first_sample_peak=float(np.max(np.abs(piece[0]))),last_sample_peak=float(np.max(np.abs(piece[-1])))))
    duck=np.ones(length,np.float32)
    for scene in plan['scenes']:
        if not scene['id'].startswith('n'):continue
        a=round(scene['voice_start']*SR);z=a+round(max(scene['voice_seconds'].values())*SR)
        attack=max(0,a-12000);release=min(length,z+round(.65*SR))
        duck[attack:a]=np.minimum(duck[attack:a],1-.75*half_cosine(a-attack))
        duck[a:z]=np.minimum(duck[a:z],.25)
        duck[z:release]=np.minimum(duck[z:release],.25+.75*half_cosine(release-z))
    score*=duck[:,None]
    listen=next(s for s in plan['scenes'] if s['id']=='listen');listen_start=round(listen['start']*SR)
    assert np.max(np.abs(score[:listen_start]))==0
    gains={};edge_records=[];duration_audit=[]
    for lang in ['en','zh']:
        voice=np.zeros(length,np.float32);captions=[]
        for scene in plan['scenes']:
            if not scene['id'].startswith('n'):continue
            offset=round(scene['voice_start']*SR);first=offset
            units=[i for i in plan['voice_fragments'] if i['language']==lang and i['paragraph_id']==scene['id']]
            for item in units:
                original=film.decode(item['file'])[:,0]
                assert abs(len(original)/SR-item['seconds'])<.002
                assert np.isfinite(original).all() and np.max(np.abs(original))>.01
                v,receipt=voice_edges(original)
                receipt.update(id=item['id'],language=lang,file=item['file'])
                edge_records.append(receipt)
                assert offset+len(v)<=round(scene['end']*SR)
                voice[offset:offset+len(v)]=v
                pieces=film.subtitle_chunks(item['text'],lang);packed=[]
                for piece in pieces:
                    lines=film.caption_lines(piece,lang).splitlines()
                    for index in range(0,len(lines),2):packed.append((' ' if lang=='en' else '').join(lines[index:index+2]))
                weights=[len(re.sub(r'\s','',s)) for s in packed];cursor=0
                for part,weight in zip(packed,weights):
                    start=offset/SR+len(v)/SR*cursor/sum(weights);cursor+=weight
                    end=offset/SR+len(v)/SR*cursor/sum(weights)
                    captions.append(dict(start=start,end=end,text=film.caption_lines(part,lang),paragraph_id=scene['id']))
                offset+=len(v)
            duration_audit.append(dict(paragraph_id=scene['id'],language=lang,voice_start=first/SR,
                native_seconds=(offset-first)/SR,placed_seconds=(offset-first)/SR,
                voice_end=offset/SR,scene_end=scene['end'],trailing_silence=scene['end']-offset/SR,speed=1.0))
        active=voice[np.abs(voice)>.008];gain=.11/np.sqrt(np.mean(active**2));voice*=gain
        assert np.max(np.abs(voice[listen_start:listen_start+10*SR]))==0
        mix=score+voice[:,None];peak=float(np.max(np.abs(mix)));headroom=min(1,.93/peak);mix*=headroom
        gains[lang]=dict(voice_gain=float(gain),mix_gain=headroom,peak=float(np.max(np.abs(mix))))
        filename='02-Chinese-aligned-audio.wav' if lang=='zh' else 'English-mix.wav'
        write_pcm24(DELIVERY/filename,mix)
        # The dry opening is exactly the processed native narration, with silence after it.
        expected=voice[:listen_start]*headroom
        opening_error=float(np.max(np.abs(mix[:listen_start,0]-expected)))
        assert opening_error<1e-7
        plan['captions'][lang]=captions
        sub=DELIVERY/('03-English.srt' if lang=='en' else '04-Chinese.srt')
        sub.write_text('\n'.join(f'{i}\n{film.srt_time(c["start"])} --> {film.srt_time(c["end"])}\n{c["text"]}\n' for i,c in enumerate(captions,1)),encoding='utf-8')
        print('Revised audio ready',lang,flush=True)
    subprocess.run([FF,'-v','error','-y','-i',str(DELIVERY/'02-Chinese-aligned-audio.wav'),'-c:a','libmp3lame','-q:a','2',str(DELIVERY/'Chinese-preview.mp3')],check=True)
    plan.update(music_spans=span_receipts,audio_gains=gains,revision='v8-audio',speech_speed_changed=False,
        music_starts_at=listen['start'],music_under_opening_voice=False,music_transitions='1.5-second fade out and 1.5-second fade in, half-cosine curves',
        english_opening_reconverted=['n001-01','n002-01','n003-01'])
    # Old correlation values described a different envelope and are not valid for this revision.
    plan.pop('first_frame_music_correlation',None);plan.pop('reprise_correlation',None)
    plan.pop('music_reprise_correlation',None)
    save(P/'full-plan.json',plan)
    save(P/'narration-timing-audit.json',dict(items=duration_audit,edges=edge_records,all_playback_rates=1.0,cloud_requests=0))
    save(P/'music-envelope.json',dict(items=span_receipts,sources=music,opening_music_is_silent=True))
    return plan

def mux():
    subprocess.run([FF,'-v','error','-y','-i',str(V7/'parts/full-picture.mp4'),'-i',str(DELIVERY/'English-mix.wav'),
        '-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','256k','-metadata:s:a:0','language=eng',
        '-metadata','title=Pressure? Anxiety? Chopin? Romanticism?','-movflags','+faststart',str(DELIVERY/'01-English-full.mp4')],check=True)
    for language,source in [('en',DELIVERY/'01-English-full.mp4'),('zh',DELIVERY/'02-Chinese-aligned-audio.wav')]:
        output=DELIVERY/('Opening-'+('English' if language=='en' else 'Chinese')+'.mp4')
        if language=='en':
            args=['-i',str(source),'-t','45','-map','0:v:0','-map','0:a:0','-c','copy']
        else:
            args=['-i',str(DELIVERY/'01-English-full.mp4'),'-i',str(source),'-t','45','-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','256k']
        subprocess.run([FF,'-v','error','-y',*args,'-movflags','+faststart',str(output)],check=True)

def install(plan):
    archive=P/'previous-delivery';archive.mkdir(exist_ok=True)
    for file in DELIVERY.iterdir():
        target=DESKTOP/file.name
        if target.exists() and not (archive/file.name).exists():os.link(target,archive/file.name)
        os.replace(file,target)
    film.preview_page(plan)
    preview=DESKTOP/'影片预览.html';page=preview.read_text()
    note='<p>音频修订：开头人声无配乐；每次换曲柔和淡出、淡入。中文保留原始语速，短段落后自然留白。<a href="Opening-English.mp4">英文开头 45 秒</a> · <a href="Opening-Chinese.mp4">中文开头 45 秒</a>。</p>'
    page=page.replace('<div class="controls">',note+'<div class="controls">',1)
    preview.write_text(page,encoding='utf-8')
    print('Updated full film and Chinese audio installed:',DESKTOP,flush=True)

def main():
    plan=prepare();mux()
    if '--install' in sys.argv:install(plan)

if __name__=='__main__':main()
