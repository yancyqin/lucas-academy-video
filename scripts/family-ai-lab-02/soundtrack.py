"""Original procedural celesta and bead sounds; no acquired music or samples."""
from pathlib import Path
import json
import math
import subprocess
import sys
import numpy as np
import soundfile as sf


def loudness(path,target=-23):
    r=subprocess.run(['ffmpeg','-hide_banner','-i',str(path),'-af',f'loudnorm=I={target}:TP=-1:LRA=7:print_format=json','-f','null','-'],capture_output=True,text=True,check=True)
    return json.loads(r.stderr[r.stderr.rfind('{'):r.stderr.rfind('}')+1])


def create(root,timeline,cues,lang,rate=24000):
    folder=root/'out/family-ai-lab-02/audio';total=timeline['durationInFrames']/30;length=math.ceil(total*rate)
    bed=np.zeros(length,dtype=np.float32)
    def tone(track,start,hz,amp,duration=.62):
        count=round(duration*rate);x=np.arange(count,dtype=np.float32)/rate
        a=np.exp(-x*8)*(1-np.exp(-x*180))
        y=amp*a*(np.sin(2*np.pi*hz*x)+.22*np.sin(2*np.pi*hz*2.01*x)+.09*np.sin(2*np.pi*hz*3.02*x))
        pos=round(start*rate);n=min(count,len(track)-pos)
        if n>0 and pos>=0:track[pos:pos+n]+=y[:n]
    # An authored sixteen-note motif on a G-major pentatonic scale. The rests
    # leave space for the story. This score and its sound recipe are reproducible.
    notes=[392,0,494,587,0,494,440,0,392,0,330,392,0,294,330,0]
    beat=60/92
    for n in range(math.ceil(total/beat)):
        hz=notes[n%len(notes)]
        if hz:tone(bed,n*beat,hz,.15,.85)
        if n%8==0:tone(bed,n*beat,196 if n%16==0 else 164.81,.08,1.5)
    raw=folder/'score.wav';sf.write(raw,bed,rate,subtype='PCM_24')
    measured=loudness(raw)
    sys.path.insert(0,str(root/'scripts'));import music_ducking
    envelope=folder/f'{lang}.music-envelope.wav'
    music_ducking.envelope(cues,total,float(measured['input_i']),envelope)
    gain,gain_rate=sf.read(envelope,dtype='float32');assert gain_rate==1000
    # Interpolate the repository's 1 kHz gain envelope onto the audio samples.
    positions=np.arange(length,dtype=np.float32)/rate
    bed*=np.interp(positions,np.arange(len(gain))/1000,gain).astype(np.float32)
    effects=np.zeros(length,dtype=np.float32);events=[]
    for row in timeline['lines']:
        if row['visual'] in ('send-p','send-play'):
            n=8 if row['visual']=='send-p' else 24
            for j in range(n):
                second=(row['from']+(row['duration']-35)*(j+2)/(n+2))/30
                tone(effects,second,1046 if j%8==7 else 784,.018,.11)
                events.append({'cue':row['id'],'seconds':round(second,5),'type':'byte-complete' if j%8==7 else 'bead-arrival'})
        if row['visual'].startswith('guess-'):
            second=(row['from']+row['duration']*.38)/30
            tone(effects,second,660 if row['visual'] in ('guess-1','guess-3') else 440,.02,.22)
    sf.write(folder/'effects.wav',effects,rate,subtype='PCM_24')
    report={'music':'Original sixteen-note pentatonic celesta recipe in soundtrack.py; no external media','musicUnderVoiceDb':music_ducking.UNDER_DB,'musicInGapsDb':music_ducking.GAP_DB,'minimumGapSeconds':music_ducking.MIN_GAP,'attackSeconds':music_ducking.ATTACK,'releaseSeconds':music_ducking.RELEASE,'scoreLoudness':measured['input_i'],'beadArrivalEvents':events}
    (folder/f'{lang}.soundtrack.json').write_text(json.dumps(report,indent=2)+'\n')
    return bed+effects
