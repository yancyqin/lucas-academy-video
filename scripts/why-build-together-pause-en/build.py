"""Adapt the owner's performance to the existing picture, without speech stretching."""
from pathlib import Path
import hashlib,html,json,math,re,shutil,subprocess,sys
import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

ROOT=Path(__file__).resolve().parents[2]
DATA=ROOT.parent/'lucas-academy-video-data/why-build-together-20261122/english-pause-alignment-v06'
OLD=ROOT.parent/'lucas-academy-video-data/why-build-together-20261122/v04'
DEST=DATA/'delivery'
SR=48000
sys.path.insert(0,str(ROOT/'scripts'))
import music_ducking

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def stamp(t,sep=','):
    n=round(t*1000);h,n=divmod(n,3600000);m,n=divmod(n,60000);s,n=divmod(n,1000)
    return f'{h:02}:{m:02}:{s:02}{sep}{n:03}'

def main():
    DEST.mkdir(exist_ok=True)
    transcript=json.loads((DATA/'transcript-check.json').read_text());assert transcript['exact_normalized_words']
    source=DATA/'source/with-ai-english-narration-louise.wav'
    audio,sr=sf.read(source,dtype='float32');assert sr==24000 and audio.ndim==1
    alignment=json.loads((DATA/'aligned-source.json').read_text())
    assert sha(source)==alignment['source_sha256']==transcript['source_sha256']
    plan=json.loads((DATA/'picture-timeline-v04.json').read_text());scenes={s['id']:s for s in plan['scenes']}
    intro_count=plan['intro_frames']*1600
    from pause_plan import build_voice
    voice,placements,mapped,speech_cues,cut_checks,gain=build_voice(audio,sr,alignment,plan,DATA)
    assert np.isfinite(voice).all()
    sf.write(DATA/'intro-en-voice.wav',voice,SR,subtype='PCM_24')
    (DATA/'placements.json').write_text(json.dumps({'source_sha256':sha(source),'all_source_samples_used_once':True,
        'source_samples':len(audio),'speech_speed':1.0,'gain':gain,'quiet_cuts':cut_checks,'placements':placements,'rows':list(mapped.values())},ensure_ascii=False,indent=2)+'\n')
    duration=plan['intro_frames']/30
    music=ROOT.parent/'lucas-academy-video-data/curiosity-builds-20261118/v5/music/raindrop.wav'
    raw=subprocess.check_output(['ffmpeg','-v','error','-i',str(music),'-t',str(duration),'-ar',str(SR),'-ac','1','-f','f32le','-'])
    bed=np.frombuffer(raw,dtype='<f4').copy();bed=np.pad(bed,(0,max(0,intro_count-len(bed))))[:intro_count]
    lufs=20*math.log10(max(float(np.sqrt(np.mean(bed*bed))),1e-8))
    music_ducking.envelope(speech_cues,duration,lufs,DATA/'music-ducking.wav',quiet=[(0,23.9)])
    env,esr=sf.read(DATA/'music-ducking.wav',dtype='float32')
    gains=np.interp(np.arange(intro_count)/SR,np.arange(len(env))/esr,env).astype('float32')
    mix=voice+bed*gains
    fade=round(.025*SR);mix[:fade]*=np.linspace(0,1,fade);mix[-fade:]*=np.linspace(1,0,fade)
    assert np.isfinite(mix).all() and float(np.abs(mix).max())<.99
    sf.write(DATA/'intro-en-mix.wav',mix,SR,subtype='PCM_24')
    old_audio=OLD/'delivery/why-build-together.en-v04.wav'
    old_pcm,old_sr=sf.read(old_audio,dtype='int16');assert old_sr==SR and old_pcm.shape==(plan['frames']*1600,2)
    mixed_pcm=np.clip(np.rint(mix*32768),-32768,32767).astype('int16')
    full_pcm=np.concatenate([np.repeat(mixed_pcm[:,None],2,axis=1),old_pcm[intro_count:]],axis=0)
    wav=DEST/'why-build-together.en-pauses-v06.wav'
    sf.write(wav,full_pcm,SR,subtype='PCM_16')
    check,sr2=sf.read(wav,dtype='int16');assert sr2==SR and np.array_equal(check[intro_count:],old_pcm[intro_count:])
    mp3=DEST/'why-build-together.en-pauses-v06.mp3'
    subprocess.run(['ffmpeg','-v','error','-y','-i',str(wav),'-c:a','libmp3lame','-b:a','192k',str(mp3)],check=True)
    captions=[]
    for id in scenes:
        group=[];blocks=[]
        for w in mapped[id]['words']:
            if group and len(''.join(x['word'] for x in group)+w['word'])>74:blocks.append(group);group=[]
            group.append(w)
            if re.search(r'[.!?;]$',w['word']):blocks.append(group);group=[]
        if group:blocks.append(group)
        for group in blocks:captions.append([group[0]['start'],group[-1]['end'],''.join(w['word'] for w in group).strip()])
    project=json.loads((ROOT.parent/'lucas-academy-video-data/curiosity-builds-20261118/v10/records/subtitles.json').read_text())
    for cue in project['cues']:captions.append([duration+cue['start']/30,duration+cue['end']/30,cue['en']])
    captions.sort(key=lambda c:c[0])
    assert all(0<=a<b<=plan['seconds']+.001 for a,b,text in captions)
    assert all(captions[i][0]>=captions[i-1][1]-.001 for i in range(1,len(captions)))
    for ext,sep in [('srt',','),('vtt','.')]:
        text=('WEBVTT\n\n' if ext=='vtt' else '')+'\n\n'.join((f'{i}\n' if ext=='srt' else '')+f'{stamp(a,sep)} --> {stamp(b,sep)}\n{text}' for i,(a,b,text) in enumerate(captions,1))+'\n'
        (DEST/f'why-build-together.en-pauses-v06.{ext}').write_text(text)
    movie=OLD/'delivery/why-build-together.zh-v04.mp4'
    preview=DEST/'why-build-together.en-pauses-v06.mp4'
    subprocess.run(['ffmpeg','-v','error','-y','-i',str(movie),'-i',str(wav),'-i',str(DEST/'why-build-together.en-pauses-v06.srt'),
        '-map','0:v:0','-map','1:a:0','-map','2:0','-map_chapters','0','-map_metadata','0',
        '-c:v','copy','-c:a','aac','-b:a','256k','-c:s','mov_text','-metadata:s:a:0','language=eng',
        '-metadata:s:s:0','language=eng','-disposition:s:0','default','-metadata','title=With AI, from Curiosity to Product',
        '-movflags','+faststart',str(preview)],check=True)
    vtt=(DEST/'why-build-together.en-pauses-v06.vtt').read_text()
    player='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>With AI, from Curiosity to Product</title><style>body{margin:0;background:#102028;color:#f5f3ea;font:18px/1.6 -apple-system,Arial,sans-serif}main{max-width:1200px;margin:35px auto;padding:0 24px}h1{font-size:28px;font-weight:500}video{width:100%;display:block;background:#000}::cue{font-size:25px;background:rgba(0,0,0,.78);color:white}</style><main><h1>With AI, from Curiosity to Product</h1><video controls preload="metadata" src="why-build-together.en-pauses-v06.mp4"><track id="en" kind="subtitles" label="English" srclang="en" default></video></main><script>document.getElementById('en').src=URL.createObjectURL(new Blob([VTT],{type:'text/vtt'}));</script></html>'''
    (DEST/'preview-en-v06.html').write_text(player.replace('VTT',json.dumps(vtt)))
    junk=next(w for w in mapped['n009']['words'] if w['word'].strip()=='junk')
    report={'status':'prepared','timing_method':'native speech; longer natural punctuation pauses','source_sha256':sha(source),'source_seconds':len(audio)/sr,'seconds':plan['seconds'],
        'picture_source':str(movie),'picture_unchanged':True,'speech_speed':1.0,'all_source_samples_used_once':True,
        'project_audio_preserved_pcm_exactly':True,'project_start_seconds':duration,'english_caption_cues':len(captions),
        'food_comparison':{'junk_food_word_seconds':junk['start'],'food_picture_starts':scenes['n009']['start_frame']/30},
        'visibility_requested':'unlisted','files':[{'name':p.name,'bytes':p.stat().st_size,'sha256':sha(p)} for p in [wav,mp3,preview,DEST/'why-build-together.en-pauses-v06.srt']]}
    (DEST/'delivery.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
