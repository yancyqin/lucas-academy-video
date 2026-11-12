"""Freeze inspected takes and mix two aligned narration tracks at -16 LUFS."""
from pathlib import Path
import argparse
import hashlib
import json
import math
import shutil
import subprocess
import numpy as np
import soundfile as sf
from soundtrack import create,loudness

ROOT=Path(__file__).resolve().parents[2]
PUBLIC=ROOT/'public/family-ai-lab-02'
MEDIA=ROOT.parent/'lucas-academy-media'
OUT=ROOT/'out/family-ai-lab-02/audio'


def select():
    choices=json.loads((ROOT/'docs/family-ai-lab-02/voice-choices.json').read_text())
    manifest={'en':{},'zh':{}}
    for lang in manifest:
        for row in json.loads((ROOT/f'docs/family-ai-lab-02/voice.{lang}.json').read_text()):
            decision=choices[f'{lang}/{row["id"]}'];assert decision['checked']
            name=row['id']+(f'.take{decision["take"]}' if decision.get('take') else '')
            source=MEDIA/f'outputs/louise/{lang}/family-ai-lab-02-v1/s1.10/{name}.wav';meta=json.loads(source.with_suffix('.json').read_text())
            assert meta['caption']==row['caption'] and meta['settingsSha256']==row['settingsSha256'],('Stale take',lang,name)
            dest=PUBLIC/f'narration/{lang}/{row["id"]}.wav';dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,dest)
            samples,rate=sf.read(dest);assert rate==24000 and samples.ndim==1
            digest=hashlib.sha256(dest.read_bytes()).hexdigest();assert decision['sha256']==digest
            manifest[lang][row['id']]={'clip':str(dest.relative_to(PUBLIC)),'seconds':len(samples)/rate,'sha256':digest,'source':str(source.relative_to(MEDIA)),'caption':row['caption'],'spoken':meta['spoken'],'settingsSha256':meta['settingsSha256'],'review':decision['note']}
    (PUBLIC/'narration.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print('Selected',sum(map(len,manifest.values())),'checked takes')


def normalize(source,dest):
    def measure(args):
        r=subprocess.run(['ffmpeg','-hide_banner',*args],capture_output=True,text=True,check=True)
        return json.loads(r.stderr[r.stderr.rfind('{'):r.stderr.rfind('}')+1])
    m=measure(['-i',str(source),'-af','loudnorm=I=-16:TP=-1:LRA=7:print_format=json','-f','null','-'])
    f='loudnorm=I=-16:TP=-1:LRA=7:linear=true:print_format=json'+''.join(':'+a+'='+m[b] for a,b in [('measured_I','input_i'),('measured_TP','input_tp'),('measured_LRA','input_lra'),('measured_thresh','input_thresh'),('offset','target_offset')])
    return {'input':m,'output':measure(['-y','-i',str(source),'-af',f,'-ar','48000','-ac','1','-c:a','pcm_s24le',str(dest)])}


def mix():
    OUT.mkdir(parents=True,exist_ok=True)
    tl=json.loads((PUBLIC/'timeline.json').read_text());assert tl['narrated']
    manifest=json.loads((PUBLIC/'narration.json').read_text());report={};rate=24000
    for lang in manifest:
        track=np.zeros(math.ceil(tl['durationInFrames']/30*rate),dtype=np.float32)
        cues=[];line_levels={}
        for row in tl['lines']:
            entry=manifest[lang][row['id']];path=PUBLIC/entry['clip'];assert hashlib.sha256(path.read_bytes()).hexdigest()==entry['sha256']
            samples,sr=sf.read(path,dtype='float32');assert sr==rate
            level=loudness(path);gain=10**((-23-float(level['input_i']))/20)
            gain=min(gain,.8/max(.001,float(np.max(np.abs(samples)))))
            samples*=gain;line_levels[row['id']]={'inputLUFS':level['input_i'],'gain':gain}
            start=round((row['from']+3)/30*rate);stop=round((row['from']+row['duration'])/30*rate)
            assert start+len(samples)<stop,('Overrun',lang,row['id'])
            track[start:start+len(samples)]=samples
            cues.append({'speech':{'start':start/rate,'end':(start+len(samples))/rate}})
        sf.write(OUT/f'{lang}.voice-only.wav',track,rate,subtype='PCM_24')
        track+=create(ROOT,tl,cues,lang,rate)
        dry=OUT/f'{lang}.dry.wav';sf.write(dry,track,rate,subtype='PCM_24')
        report[lang]=normalize(dry,OUT/f'{lang}.wav')
        report[lang]['lineLevels']=line_levels
        subprocess.run(['ffmpeg','-v','error','-y','-i',str(OUT/f'{lang}.wav'),'-c:a','aac','-b:a','192k','-metadata',f'language={"eng" if lang=="en" else "zho"}',str(OUT/f'{lang}.m4a')],check=True)
        print('Aligned',lang,len(track)/rate,'seconds')
    (OUT/'loudness.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--select',action='store_true');args=parser.parse_args()
    select() if args.select else mix()
