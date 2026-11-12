"""Original short-story electronic score with per-language speech ducking."""
from pathlib import Path
import hashlib,json,subprocess,sys
import numpy as np
import soundfile as sf
from orbital_mix import score,blip,add,RATE
from soundtrack import loudness
from mix_audio import normalize

ROOT=Path(__file__).resolve().parents[2]
PUBLIC=ROOT/'public/family-ai-lab-02'
OUT=ROOT/'out/family-ai-lab-02/orbital-v2/short/audio'


def main():
    OUT.mkdir(parents=True,exist_ok=True);tl=json.loads((PUBLIC/'orbital-v2/short/timeline.json').read_text());manifest=json.loads((PUBLIC/'orbital-v2/short/narration.json').read_text());total=tl['durationInFrames']/30
    music=score(total);sf.write(OUT/'score.wav',music,RATE,subtype='PCM_24');music_level=float(loudness(OUT/'score.wav')['input_i']);fx=np.zeros(len(music),dtype=np.float32)
    for row in tl['lines']:
        if row['visual']=='arrival':
            for i in range(4):add(fx,(row['from']+(row['duration']-25)*(i+1)/4)/30,blip(784+i*90,.18,.014))
        if row['visual']=='questions':
            for i in range(4):add(fx,(row['from']+row['duration']*(i+.35)/4)/30,blip(660 if i%2==0 else 440,.17,.018))
    sys.path.insert(0,str(ROOT/'scripts'));import music_ducking
    report={}
    for lang in ['en','zh']:
        voice=np.zeros(len(music),dtype=np.float32);cues=[]
        for row in tl['lines']:
            entry=manifest[lang][row['id']];path=PUBLIC/entry['clip'];assert hashlib.sha256(path.read_bytes()).hexdigest()==entry['sha256'];samples,rate=sf.read(path,dtype='float32');assert rate==RATE
            level=loudness(path);gain=min(10**((-23-float(level['input_i']))/20),.8/max(.001,float(np.max(np.abs(samples)))))
            start=(row['from']+row['speechOffsetFrames'])/30;assert start+len(samples)/RATE<(row['from']+row['duration'])/30
            add(voice,start,samples*gain);cues.append({'speech':{'start':start,'end':start+len(samples)/RATE}})
        envelope_path=OUT/f'{lang}.envelope.wav';music_ducking.envelope(cues,total,music_level,envelope_path);env,rate=sf.read(envelope_path,dtype='float32');assert rate==1000
        gain=np.interp(np.arange(len(voice))/RATE,np.arange(len(env))/1000,env).astype(np.float32);dry=OUT/f'{lang}.dry.wav';sf.write(dry,voice+music*gain+fx,RATE,subtype='PCM_24');levels=normalize(dry,OUT/f'{lang}.wav')
        subprocess.run(['ffmpeg','-v','error','-y','-i',str(OUT/f'{lang}.wav'),'-c:a','aac','-b:a','192k',str(OUT/f'{lang}.m4a')],check=True)
        report[lang]={'seconds':total,'loudness':levels,'ducking':{'underVoiceDb':music_ducking.UNDER_DB,'inGapsDb':music_ducking.GAP_DB,'minimumGapSeconds':music_ducking.MIN_GAP,'advanceSeconds':music_ducking.ATTACK,'recoverySeconds':music_ducking.RELEASE}}
    (OUT/'loudness.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print('Mixed both short-film tracks:',total,'seconds.')


if __name__=='__main__':main()
