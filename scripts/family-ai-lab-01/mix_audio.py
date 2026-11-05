"""Select inspected takes, align two tracks to one picture, normalize to -16 LUFS.

Run with .venv-align/bin/python. Raw TTS takes remain in the media repository.
The selected WAVs are copied to the ignored project inputs for portable backup.
"""
from pathlib import Path
import argparse
import hashlib
import json
import math
import shutil
import subprocess
import numpy as np
import soundfile as sf

ROOT=Path(__file__).resolve().parents[2]
MEDIA=ROOT.parent/'lucas-academy-media'
PUBLIC=ROOT/'public/family-ai-lab-01'
OUT=ROOT/'out/family-ai-lab-01'


def select():
    choices=json.loads((ROOT/'docs/family-ai-lab-01/voice-choices.json').read_text())
    manifest={'en':{},'zh':{}}
    for lang in ('en','zh'):
        lines=json.loads((ROOT/f'docs/family-ai-lab-01/voice.{lang}.json').read_text())
        for line in lines:
            key=f'{lang}/{line["id"]}'
            decision=choices[key]
            assert decision['checked'],key
            name=line['id']+(f'.take{decision["take"]}' if decision.get('take') else '')
            source=MEDIA/f'outputs/louise/{lang}/family-ai-lab-01-v1/s1.10/{name}.wav'
            meta=json.loads(source.with_suffix('.json').read_text())
            samples,rate=sf.read(source,dtype='float32')
            assert samples.ndim==1 and rate==24000,(key,samples.shape,rate)
            assert len(samples)/rate>.5,key
            dest=PUBLIC/f'narration/{lang}/{line["id"]}.wav'
            dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,dest)
            manifest[lang][line['id']]={
                'clip':str(dest.relative_to(PUBLIC)),'seconds':len(samples)/rate,'samples':len(samples),'sampleRate':rate,
                'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'source':str(source.relative_to(MEDIA)),
                'caption':line['caption'],'spoken':meta['spoken'],'settingsSha256':meta['settingsSha256'],
                'check':decision['note']}
    (PUBLIC/'narration.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print('Selected and copied',sum(len(v) for v in manifest.values()),'inspected takes')


def loudnorm(source,dest):
    first=subprocess.run(['ffmpeg','-hide_banner','-i',str(source),'-af','loudnorm=I=-16:TP=-1:LRA=7:print_format=json','-f','null','-'],text=True,capture_output=True,check=True)
    a=first.stderr.rfind('{');b=first.stderr.rfind('}')+1
    measured=json.loads(first.stderr[a:b])
    filt='loudnorm=I=-16:TP=-1:LRA=7:linear=true:print_format=json'+''.join(':'+k+'='+measured[v] for k,v in [('measured_I','input_i'),('measured_TP','input_tp'),('measured_LRA','input_lra'),('measured_thresh','input_thresh'),('offset','target_offset')])
    second=subprocess.run(['ffmpeg','-hide_banner','-y','-i',str(source),'-af',filt,'-ar','48000','-ac','1','-c:a','pcm_s24le',str(dest)],text=True,capture_output=True,check=True)
    a=second.stderr.rfind('{');b=second.stderr.rfind('}')+1
    return {'input':measured,'output':json.loads(second.stderr[a:b])}


def mix():
    tl=json.loads((PUBLIC/'timeline.json').read_text());assert tl.get('narrated')
    narration=json.loads((PUBLIC/'narration.json').read_text())
    folder=OUT/'audio';folder.mkdir(parents=True,exist_ok=True)
    rate=24000;length=math.ceil(tl['durationInFrames']/tl['fps']*rate)
    checks={}
    for lang in ('en','zh'):
        audio=np.zeros(length,dtype=np.float32)
        for line in tl['lines']:
            info=narration[lang][line['id']];p=PUBLIC/info['clip']
            assert hashlib.sha256(p.read_bytes()).hexdigest()==info['sha256'],str(p)
            samples,sr=sf.read(p,dtype='float32');assert sr==rate
            start=round((line['from']+3)/tl['fps']*rate)
            limit=round((line['from']+line['duration'])/tl['fps']*rate)
            assert start+len(samples)<=limit,(lang,line['id'],'speech would overrun picture interval')
            audio[start:start+len(samples)]+=samples
        dry=folder/f'{lang}.dry.wav';sf.write(dry,audio,rate,subtype='PCM_24')
        checks[lang]=loudnorm(dry,folder/f'{lang}.wav')
        subprocess.run(['ffmpeg','-v','error','-y','-i',str(folder/f'{lang}.wav'),'-c:a','aac','-b:a','192k','-metadata',f'language={"eng" if lang=="en" else "zho"}',str(folder/f'{lang}.m4a')],check=True)
        print('Aligned and normalized',lang,len(audio)/rate,'seconds')
    (folder/'loudness.json').write_text(json.dumps(checks,indent=2)+'\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--select',action='store_true');args=parser.parse_args()
    select() if args.select else mix()
