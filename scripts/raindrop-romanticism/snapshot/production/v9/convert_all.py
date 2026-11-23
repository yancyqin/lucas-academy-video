"""Audit and re-convert every English paragraph using padded local VC context."""
import hashlib,json
from pathlib import Path
import subprocess,sys,time,wave
import numpy as np
import torch

P=Path(__file__).resolve().parent;V6=P.parent/'v6';V8=P.parent/'v8'
sys.path.insert(0,str(V6))
from convert_narration import CosyVoiceEngine,enable_mps_flow,cache_reference_features
from lucas_media.joke import save_wav,add_peak_headroom

FF='/opt/homebrew/bin/ffmpeg'
def read(path):
    return np.frombuffer(subprocess.check_output([FF,'-v','error','-i',str(path),'-ar','16000','-ac','1','-f','f32le','-']),dtype='<f4').copy()

def write(path,data):
    with wave.open(str(path),'wb') as w:
        w.setparams((1,2,16000,0,'NONE','not compressed'));w.writeframes(np.round(np.clip(data,-1,1)*32767).astype('<i2').tobytes())

def convert(engine,data,folder,seed):
    folder.mkdir(parents=True,exist_ok=True)
    padded=np.pad(data,(16000,16000));assert len(padded)/16000<30
    source=folder/'padded-source.wav';write(source,padded);torch.manual_seed(seed)
    with torch.inference_mode():
        voice=torch.cat([r['tts_speech'].cpu() for r in engine.model.inference_vc(str(source),str(engine.reference_audio),stream=False,speed=1.0)],dim=1)
    rate=engine.model.sample_rate;count=round(len(data)*rate/16000)
    assert voice.shape[1]>=rate+count;voice=voice[:,rate:rate+count]
    assert torch.isfinite(voice).all()
    return add_peak_headroom(voice),rate

def asr(file,language):
    prefix=file.parent/'asr'
    if not prefix.with_suffix('.txt').exists():
        r=subprocess.run(['/opt/homebrew/bin/whisper-cli','-m','@USER_HOME@/.cache/whisper/ggml-small-q5_1.bin','-f',str(file),'-l',language,'-otxt','-oj','-of',str(prefix),'-ng','-t','2','-np'],capture_output=True,text=True)
        (file.parent/'asr.log').write_text(r.stderr);r.check_returncode()
    return prefix.with_suffix('.txt').read_text().strip()

def progress(done,total,last):
    (P/'conversion-progress.json').write_text(json.dumps(dict(done=done,total=total,last=last)))

def engine_for(profile):
    e=CosyVoiceEngine(profile);enable_mps_flow(e.model.model);cache_reference_features(e);return e

def main():
    original=json.loads((V8/'full-plan.json').read_text());outputs=[]
    selected=json.loads((P/'chinese-selected.json').read_text())
    folder=P/'chinese-retake/converted';file=folder/'voice.wav';receipt=folder/'receipt.json'
    if not receipt.exists():
        engine=engine_for('fangfang/zh');data=read(selected['file'])
        voice,rate=convert(engine,data,folder,202611219);save_wav(file,voice,rate)
        old=next(i for i in original['voice_fragments'] if i['language']=='zh' and i['id']=='n003-01')
        meta=dict(old,file=str(file),seconds=voice.shape[1]/rate,source_file=selected['file'],
            sha256=hashlib.sha256(file.read_bytes()).hexdigest(),method='Native local Qwen natural-paced retake → padded local Fangfang VC; speed 1.0')
        receipt.write_text(json.dumps(meta,ensure_ascii=False,indent=2));del engine;torch.mps.empty_cache()
    cn=json.loads(receipt.read_text());cn['asr']=asr(file,'zh');outputs.append(cn)
    print('Chinese retake converted:',cn['seconds'],cn['asr'],flush=True)
    units=[i for i in original['voice_fragments'] if i['language']=='en']
    trusted={i['id']:i for i in json.loads((V8/'opening-overrides.json').read_text())['items']}
    todo=[];source_data={}
    for item in units:
        folder=P/'english'/(item['id']+'-'+item['text_sha256'][:12]);receipt=folder/'receipt.json'
        if item['id'] in trusted:
            folder.mkdir(parents=True,exist_ok=True);meta=dict(trusted[item['id']])
            meta['asr']=asr(Path(meta['file']),'en');outputs.append(meta);continue
        if receipt.exists():
            meta=json.loads(receipt.read_text());meta['asr']=asr(Path(meta['file']),'en');outputs.append(meta);continue
        source=V6/'minimax-sources/en'/(item['id']+'-'+item['text_sha256'][:12])/'original.mp3'
        data=read(source);source_data[item['id']]=data;todo.append((item,source))
    progress(len(outputs)-1,len(units),'cached opening')
    # Consecutive clauses keep one VC context, avoiding a model reset mid-paragraph.
    groups=[];current=[];count=0
    for pair in todo:
        item,_=pair;n=len(source_data[item['id']])
        if current and (current[-1][0]['paragraph_id']!=item['paragraph_id'] or count+n>int(26.5*16000)):
            groups.append(current);current=[];count=0
        current.append(pair);count+=n
    if current:groups.append(current)
    engine=engine_for('louise/en') if groups else None
    for k,group in enumerate(groups):
        data=np.concatenate([source_data[i['id']] for i,_ in group]);ids=[i['id'] for i,_ in group]
        group_folder=P/'english-groups'/('-'.join(ids));start=time.monotonic()
        voice,rate=convert(engine,data,group_folder,202611220+k)
        offset=0;source_offset=0
        for j,(item,source) in enumerate(group):
            folder=P/'english'/(item['id']+'-'+item['text_sha256'][:12]);folder.mkdir(parents=True,exist_ok=True)
            source_offset+=len(source_data[item['id']]);end=voice.shape[1] if j==len(group)-1 else round(source_offset*rate/16000)
            fragment=voice[:,offset:end];offset=end;file=folder/'voice.wav';save_wav(file,fragment,rate)
            meta=dict(item,file=str(file),seconds=fragment.shape[1]/rate,source_seconds=len(source_data[item['id']])/16000,
                source_file=str(source),source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                sha256=hashlib.sha256(file.read_bytes()).hexdigest(),vc_context=ids,temporary_padding_seconds=1,
                method='Reused MiniMax performance → locally padded Louise VC; speed 1.0; native length retained')
            (folder/'receipt.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2))
            meta['asr']=asr(file,'en');outputs.append(meta)
        done=len(outputs)-1;progress(done,len(units),ids[-1])
        print('English checked',done,'/',len(units),ids,'seconds',round(time.monotonic()-start,1),flush=True)
        (P/'voice-overrides.partial.json').write_text(json.dumps(dict(items=outputs,new_cloud_requests=0),ensure_ascii=False,indent=2))
    assert sum(i['language']=='en' for i in outputs)==73
    (P/'voice-overrides.json').write_text(json.dumps(dict(items=outputs,new_cloud_requests=0),ensure_ascii=False,indent=2))
    print('All English fragments converted and transcribed; Chinese native retake ready.',flush=True)

if __name__=='__main__':main()
