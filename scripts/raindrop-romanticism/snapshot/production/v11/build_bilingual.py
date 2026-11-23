"""Fit the revised native English take by lengthening its camera shot, not speech."""
import hashlib,json,math,os,re,shutil,subprocess,sys
from pathlib import Path
import numpy as np
from docx import Document

P=Path(__file__).resolve().parent;V10=P.parent/'v10';V9=P.parent/'v9';V7=P.parent/'v7'
PACKAGE=Path('@DATA_ROOT@/production/v12/published-release')
sys.path.insert(0,str(P.parent/'v8'))
import revise_audio as audio
film=audio.film;FF=film.FF;SR=film.SR;FPS=film.FPS

def save(path,data):path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def balanced(source,reference,out):
    data=film.decode(source)[:,0];ref=film.decode(reference)[:,0]
    rms=lambda a:np.sqrt(np.mean(a[np.abs(a)>.008]**2))
    ratio=float(rms(ref)/rms(data));data*=ratio
    assert np.max(np.abs(data))<1
    subprocess.run([FF,'-v','error','-y','-f','f32le','-ar',str(SR),'-ac','1','-i','-','-c:a','pcm_s24le',str(out)],input=data.astype('<f4').tobytes(),check=True)
    return ratio

def main():
    old=json.loads((V10/'full-plan.json').read_text());plan=json.loads(json.dumps(old))
    en=json.loads((P/'n002-english/louise/receipt.json').read_text())
    baseline=json.loads((V9/'full-plan.json').read_text())
    source=next(s for s in plan['scenes'] if s['id']=='n002')
    old_end=source['end'];old_count=source['count'];old_cut=round(old_end*FPS)
    new_count=max(old_count,math.ceil((.25+max(en['seconds'],11.2)+.5)*FPS))
    added=new_count-old_count;delta=added/FPS
    assert added>=0
    for scene in plan['scenes']:
        if scene['id']=='n002':scene['count']=new_count
        elif scene['first']>=old_cut:
            scene['first']+=added
            if 'voice_start' in scene:scene['voice_start']+=delta
        scene['start']=scene['first']/FPS;scene['end']=(scene['first']+scene['count'])/FPS
    plan['frames']+=added;plan['duration']=plan['frames']/FPS
    source['text_en']=en['text'];source['voice_seconds']['en']=en['seconds']
    # Match each new performance to the former passage's voice level before normal mixing.
    units={i['language']:i for i in plan['voice_fragments'] if i['paragraph_id']=='n002'}
    units['en'].update(en)
    units['en']['source_seconds']=en['seconds']
    levels={}
    for language in ['en','zh']:
        item=units[language]
        if language=='en':item.update(en)
        reference=next(i for i in baseline['voice_fragments'] if i['paragraph_id']=='n002' and i['language']==language)
        out=P/('n002-'+language+'-level-matched.wav')
        ratio=balanced(item['file'],reference['file'],out);levels[language]=ratio
        item.update(unbalanced_voice_file=item['file'],file=str(out),gain_adjustment=ratio,
            sha256=hashlib.sha256(out.read_bytes()).hexdigest(),seconds=float(item['seconds']),speed=1.0)
    save(P/'source-plan.json',plan);save(P/'overrides.json',dict(items=[]))
    audio.P=P;audio.DELIVERY=P/'delivery'
    plan=json.loads((P/'full-plan.json').read_text()) if '--resume-picture' in sys.argv else audio.prepare(P/'source-plan.json',P/'overrides.json')
    compact=lambda t:re.sub(r'\s+','',t)
    for scene in plan['scenes']:
        if not scene['id'].startswith('n'):continue
        for language in ['en','zh']:
            items=[i for i in plan['voice_fragments'] if i['paragraph_id']==scene['id'] and i['language']==language]
            assert compact(''.join(i['text'] for i in items))==compact(scene['text_'+language]),(scene['id'],language)
    # Keep the already reviewed caption boundaries everywhere else, shifted with the picture.
    captions={}
    for language in ['en','zh']:
        captions[language]=[]
        for cue in old['captions'][language]:
            if language=='en' and cue['paragraph_id']=='n002':continue
            copy=dict(cue)
            if cue['start']>=old_end:copy.update(start=cue['start']+delta,end=cue['end']+delta)
            captions[language].append(copy)
    asr=json.loads((P/'n002-english/louise/asr.json').read_text())['transcription']
    print('English ASR',[(r['offsets'],r['text']) for r in asr],flush=True)
    new_cues=[c for c in plan['captions']['en'] if c['paragraph_id']=='n002']
    captions['en']=sorted(captions['en']+new_cues,key=lambda c:c['start'])
    for language in ['en','zh']:
        plan['captions'][language]=captions[language]
        name='03-English.srt' if language=='en' else '04-Chinese.srt'
        (P/'delivery'/name).write_text('\n'.join(f'{i}\n{film.srt_time(c["start"])} --> {film.srt_time(c["end"])}\n{c["text"]}\n' for i,c in enumerate(captions[language],1)),encoding='utf-8')
    # Re-encode only the opening. Every later picture segment is reused without a new render.
    parts=P/'parts';parts.mkdir(exist_ok=True)
    opening=parts/'opening.mp4';new_opening_count=old_cut+added
    start=source['first']
    graph=f'[0:v]split=2[a][b];[a]trim=start_frame=0:end_frame={start},setpts=PTS-STARTPTS[p];'
    graph+=f'[b]trim=start_frame={start}:end_frame={old_cut},setpts=(PTS-STARTPTS)*{new_count/old_count:.12f},fps=24,tpad=stop_mode=clone:stop_duration=0.2,trim=end_frame={new_count}[q];'
    graph+='[p][q]concat=n=2:v=1:a=0,format=yuv420p[v]'
    subprocess.run([FF,'-v','error','-y','-i',str(V7/'parts/opening.mp4'),'-filter_complex_threads','2','-filter_complex',graph,'-map','[v]',*film.encoder(new_opening_count),str(opening)],check=True)
    concat=(V7/'parts/concat.txt').read_text().replace(str(V7/'parts/opening.mp4'),str(opening))
    (parts/'concat.txt').write_text(concat)
    picture=parts/'full-picture.mp4'
    subprocess.run([FF,'-v','error','-y','-f','concat','-safe','0','-i',str(parts/'concat.txt'),'-c','copy',str(picture)],check=True)
    out=P/'delivery/01-English-full.mp4'
    subprocess.run([FF,'-v','error','-y','-i',str(picture),'-i',str(P/'delivery/English-mix.wav'),'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','256k','-metadata:s:a:0','language=eng','-metadata','title=Pressure? Anxiety? Chopin? Romanticism?','-movflags','+faststart',str(out)],check=True)
    subprocess.run([FF,'-v','error','-y','-i',str(P/'delivery/02-Chinese-aligned-audio.wav'),'-c:a','aac','-b:a','256k','-movflags','+faststart','-metadata:s:a:0','language=zho',str(P/'delivery/Chinese-YouTube.m4a')],check=True)
    subprocess.run([FF,'-v','error','-y','-i',str(out),'-t','45','-c','copy','-movflags','+faststart',str(P/'delivery/Opening-English-45s.mp4')],check=True)
    plan.update(revision='v10-bilingual-opening',english_retake_seconds=en['seconds'],chinese_retake_seconds=11.2,
        opening_camera_extension_seconds=delta,opening_added_frames=added,new_cloud_requests=0,volume_adjustments=levels,
        picture_reused_from_n003_onwards=True,all_voice_speeds=1.0)
    save(P/'full-plan.json',plan)
    print('Full bilingual revision built',plan['duration'],'seconds; camera extended',delta,'seconds.',flush=True)

if __name__=='__main__':main()
