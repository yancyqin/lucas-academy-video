"""Original electronic score, timed signal sounds and two clean narration mixes."""
from pathlib import Path
import hashlib,json,math,subprocess,sys
import numpy as np
import soundfile as sf
from soundtrack import loudness
from mix_audio import normalize

ROOT=Path(__file__).resolve().parents[2]
PUBLIC=ROOT/'public/family-ai-lab-02'
OUT=ROOT/'out/family-ai-lab-02/orbital-v2/audio'
RATE=24000


def add(track,start,samples):
    at=round(start*RATE);size=min(len(samples),len(track)-at)
    if at>=0 and size>0:track[at:at+size]+=samples[:size]


def blip(hz,duration,amp):
    t=np.arange(round(duration*RATE),dtype=np.float32)/RATE
    return amp*(1-np.exp(-t*300))*np.exp(-t*13)*(np.sin(2*np.pi*hz*t)+.2*np.sin(2*np.pi*hz*2.002*t))


def score(total):
    length=round(total*RATE);bed=np.zeros(length,dtype=np.float32);beat=60/92
    # An authored four-chord cycle and sparse eight-note pulse. No external
    # recordings, songs, soundfonts or generated-service audio are used.
    chords=[(110,164.81,220,261.63),(130.8128,196,261.63,329.63),(98,146.83,196,246.94),(146.83,220,293.66,349.23)]
    bar=beat*16
    for index,start in enumerate(np.arange(0,total,bar)):
        duration=min(bar+1.4,total-start);t=np.arange(round(duration*RATE),dtype=np.float32)/RATE
        fade=np.minimum(1,t/1.1)*np.minimum(1,np.maximum(0,(duration-t)/1.4));pad=np.zeros(len(t),dtype=np.float32)
        for j,hz in enumerate(chords[index%4]):pad+=(.025/(j+1))*np.sin(2*np.pi*hz*t+.012*np.sin(2*np.pi*.17*t))
        add(bed,start,pad*fade)
    pattern=[0,7,12,None,3,None,10,None]
    for i,start in enumerate(np.arange(0,total,beat)):
        n=pattern[i%8]
        if n is not None:add(bed,start,blip(220*2**(n/12),.5,.075))
    fade=np.minimum(1,np.arange(length)/RATE/1.2)*np.minimum(1,(length-np.arange(length))/RATE/2)
    return bed*fade


def effects(timeline):
    track=np.zeros(round(timeline['durationInFrames']/30*RATE),dtype=np.float32);events=[]
    # Quick high-pass-like noise sweep through the cold open, reproducible seed.
    t=np.arange(round(1.8*RATE),dtype=np.float32)/RATE;rng=np.random.default_rng(1957)
    noise=rng.standard_normal(len(t)).astype(np.float32);noise=np.convolve(noise,np.array([1,-.94],dtype=np.float32),mode='same')
    whoosh=.025*noise*np.sin(np.pi*t/1.8)**2+.014*np.sin(2*np.pi*(160*t+280*t*t))*np.sin(np.pi*t/1.8)**2
    add(track,0,whoosh)
    for row in timeline['lines']:
        if row['visual'] in ('send-p','send-play'):
            count=8 if row['visual']=='send-p' else 24
            for i in range(count):
                second=(row['from']+(row['duration']-30)*(i+2)/(count+2))/30
                add(track,second,blip(1046 if i%8==7 else 784,.12,.018))
                events.append({'cue':row['id'],'seconds':second,'type':'byte-complete' if i%8==7 else 'signal-arrival'})
        if row['visual'].startswith('guess-'):
            second=(row['from']+row['duration']*.42)/30;add(track,second,blip(660 if row['visual'] in ('guess-1','guess-3') else 440,.2,.025));events.append({'cue':row['id'],'seconds':second,'type':'answer'})
            if row['visual']=='guess-4':add(track,second+.22,blip(880,.35,.018))
    return track,events


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    tl=json.loads((PUBLIC/'orbital-v2/timeline.json').read_text());manifest=json.loads((PUBLIC/'orbital-v2/narration.json').read_text());total=tl['durationInFrames']/30
    raw_score=score(total);score_path=OUT/'score.wav';sf.write(score_path,raw_score,RATE,subtype='PCM_24');score_level=float(loudness(score_path)['input_i'])
    fx,events=effects(tl);sf.write(OUT/'effects.wav',fx,RATE,subtype='PCM_24')
    sys.path.insert(0,str(ROOT/'scripts'));import music_ducking
    report={}
    for lang in ('en','zh'):
        voice=np.zeros(len(raw_score),dtype=np.float32);cues=[];line_levels={}
        for row in tl['lines']:
            entry=manifest[lang][row['id']];path=PUBLIC/entry['clip'];assert hashlib.sha256(path.read_bytes()).hexdigest()==entry['sha256']
            samples,rate=sf.read(path,dtype='float32');assert rate==RATE
            level=loudness(path);gain=min(10**((-23-float(level['input_i']))/20),.8/max(.001,float(np.max(np.abs(samples)))))
            start=(row['from']+row['speechOffsetFrames'])/30;assert start+len(samples)/RATE<(row['from']+row['duration'])/30
            add(voice,start,samples*gain);cues.append({'speech':{'start':start,'end':start+len(samples)/RATE}});line_levels[row['id']]={'inputLUFS':level['input_i'],'gain':gain}
        sf.write(OUT/f'{lang}.voice-only.wav',voice,RATE,subtype='PCM_24')
        envelope_path=OUT/f'{lang}.music-envelope.wav';music_ducking.envelope(cues,total,score_level,envelope_path)
        envelope,rate=sf.read(envelope_path,dtype='float32');assert rate==1000
        gain=np.interp(np.arange(len(voice))/RATE,np.arange(len(envelope))/1000,envelope).astype(np.float32)
        dry=OUT/f'{lang}.dry.wav';sf.write(dry,voice+raw_score*gain+fx,RATE,subtype='PCM_24')
        levels=normalize(dry,OUT/f'{lang}.wav')
        subprocess.run(['ffmpeg','-v','error','-y','-i',str(OUT/f'{lang}.wav'),'-c:a','aac','-b:a','192k','-metadata',f'language={"eng" if lang=="en" else "zho"}',str(OUT/f'{lang}.m4a')],check=True)
        report[lang]={'loudness':levels,'lineLevels':line_levels,'seconds':total,'score':'Original four-chord electronic pad and sparse authored pulse in orbital_mix.py','scoreLUFS':score_level,'ducking':{'underVoiceDb':music_ducking.UNDER_DB,'inGapsDb':music_ducking.GAP_DB,'minimumGapSeconds':music_ducking.MIN_GAP,'advanceSeconds':music_ducking.ATTACK,'recoverySeconds':music_ducking.RELEASE},'events':events}
        print('Mixed orbital',lang,total,'seconds',flush=True)
    (OUT/'loudness.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')


if __name__=='__main__':main()
