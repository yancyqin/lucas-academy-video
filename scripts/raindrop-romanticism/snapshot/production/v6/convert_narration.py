"""Convert approved, cached MiniMax performance into the accepted target voices."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import wave

import numpy as np
import torch

P=Path(__file__).resolve().parent
P5=P.parent/'v5'
sys.path.insert(0,str(P5))
from fangfang_voice_conversion_trial import enable_mps_flow,CosyVoiceEngine
from lucas_media.joke import save_wav,add_peak_headroom


def source_parts(source,folder):
    raw=subprocess.check_output(['/opt/homebrew/bin/ffmpeg','-v','error','-i',str(source),
                                 '-ar','16000','-ac','1','-f','f32le','-'])
    samples=np.frombuffer(raw,dtype='<f4');rate=16000;boundaries=[0]
    while len(samples)-boundaries[-1]>28.5*rate:
        start=boundaries[-1]
        # Place the boundary in a quiet interval, without removing any speech.
        left=start+int(17*rate);right=min(start+int(28*rate),len(samples))
        window=320
        frames=samples[left:right][:((right-left)//window)*window].reshape(-1,window)
        energy=np.sqrt(np.mean(frames**2,axis=1))
        cut=left+int(np.argmin(energy))*window+window//2
        assert start+10*rate<cut<start+29*rate
        boundaries.append(cut)
    boundaries.append(len(samples));paths=[]
    for i,(a,b) in enumerate(zip(boundaries,boundaries[1:])):
        path=folder/f'source-{i:02d}.wav'
        with wave.open(str(path),'wb') as writer:
            writer.setparams((1,2,rate,0,'NONE','not compressed'))
            writer.writeframes(np.round(np.clip(samples[a:b],-1,1)*32767).astype('<i2').tobytes())
        paths.append(path)
    return paths,len(samples)/rate


def cache_reference_features(engine):
    reference=str(engine.reference_audio)
    frontend=engine.model.frontend
    for name in ['_extract_speech_token','_extract_speech_feat','_extract_spk_embedding']:
        original=getattr(frontend,name);cached={}
        def wrapped(path,*args,_original=original,_cached=cached,**kwargs):
            if str(path)!=reference:return _original(path,*args,**kwargs)
            if 'value' not in _cached:_cached['value']=_original(path,*args,**kwargs)
            return _cached['value']
        setattr(frontend,name,wrapped)


def convert_ready_pack(items,index,engine):
    """Convert adjacent ready fragments of one paragraph in a single pass."""
    first=items[index];members=[];total=0
    for candidate in items[index:]:
        if candidate['language']!=first['language'] or candidate['id'].split('-')[0]!=first['id'].split('-')[0]:break
        source_folder=P/'minimax-sources'/candidate['language']/(candidate['id']+'-'+candidate['text_sha256'][:12])
        receipt_path=source_folder/'receipt.json'
        folder=P/'voices'/candidate['language']/(candidate['id']+'-'+candidate['text_sha256'][:12])
        if not receipt_path.is_file() or (folder/'receipt.json').is_file():break
        receipt=json.loads(receipt_path.read_text())
        if receipt.get('state')!='success':break
        raw=subprocess.check_output(['/opt/homebrew/bin/ffmpeg','-v','error','-i',str(source_folder/'original.mp3'),
                                     '-ar','16000','-ac','1','-f','f32le','-'])
        samples=np.frombuffer(raw,dtype='<f4')
        if total+len(samples)>int(28.3*16000):break
        assert receipt['text_sha256']==candidate['text_sha256']
        members.append((candidate,receipt,folder,samples));total+=len(samples)
    if len(members)<2:return False
    first_folder=members[0][2];first_folder.mkdir(parents=True,exist_ok=True)
    source=first_folder/'source-batch.wav'
    with wave.open(str(source),'wb') as writer:
        writer.setparams((1,2,16000,0,'NONE','not compressed'))
        writer.writeframes(np.round(np.clip(np.concatenate([m[3] for m in members]),-1,1)*32767).astype('<i2').tobytes())
    started=time.monotonic()
    with torch.inference_mode():
        speech=torch.cat([x['tts_speech'].cpu() for x in engine.model.inference_vc(
            str(source),str(engine.reference_audio),stream=False,speed=1.0)],dim=1)
    assert torch.isfinite(speech).all() and speech.shape[1]>0
    rate=engine.model.sample_rate
    assert abs(speech.shape[1]/rate-total/16000)<.08
    speech=add_peak_headroom(speech);offset=0;source_offset=0
    for j,(candidate,receipt,folder,samples) in enumerate(members):
        folder.mkdir(parents=True,exist_ok=True);output=folder/'voice.wav'
        source_offset+=len(samples)
        end=speech.shape[1] if j==len(members)-1 else round(source_offset*rate/16000)
        fragment=speech[:,offset:end];offset=end
        save_wav(output,fragment,rate)
        metadata=dict(state='success',target_profile=engine.profile_name if hasattr(engine,'profile_name') else json.loads((P/'synthesis-plan.json').read_text())['target_voices'][candidate['language']],
                      source_sha256=receipt['sha256'],text_sha256=candidate['text_sha256'],
                      reference_sha256=hashlib.sha256(engine.reference_audio.read_bytes()).hexdigest(),
                      source_seconds=len(samples)/16000,seconds=fragment.shape[1]/rate,source_parts=1,
                      sample_rate=rate,conversion_seconds=round(time.monotonic()-started,2),
                      batch_members=[m[0]['id'] for m in members],sha256=hashlib.sha256(output.read_bytes()).hexdigest())
        (folder/'receipt.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2))
    print('Converted paragraph group',first['language'],[m[0]['id'] for m in members],flush=True)
    return True


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--language',choices=['zh','en'])
    args=parser.parse_args()
    plan=json.loads((P/'synthesis-plan.json').read_text())
    items=[x for x in plan['requests'] if args.language is None or x['language']==args.language]
    suffix='-'+args.language if args.language else ''
    progress_path=P/('conversion-progress'+suffix+'.json')
    outputs=[];engine=None;profile=None
    for index,item in enumerate(items):
        lang=item['language'];wanted=plan['target_voices'][lang]
        source_folder=P/'minimax-sources'/lang/(item['id']+'-'+item['text_sha256'][:12])
        receipt_path=source_folder/'receipt.json'
        while True:
            if receipt_path.is_file():
                receipt=json.loads(receipt_path.read_text())
                if receipt['state']=='success':break
                if receipt['state'] in ['rejected','unknown']:raise RuntimeError(f'Source generation needs review: {item["id"]}')
            status=P/'generation-status.json'
            if status.is_file() and json.loads(status.read_text()).get('state')=='failed':
                raise RuntimeError('Source generation stopped; keep completed conversions cached.')
            time.sleep(1)
        assert receipt['text_sha256']==item['text_sha256']
        folder=P/'voices'/lang/(item['id']+'-'+item['text_sha256'][:12]);folder.mkdir(parents=True,exist_ok=True)
        output=folder/'voice.wav';metadata_path=folder/'receipt.json'
        if not (output.is_file() and metadata_path.is_file()):
            if profile!=wanted:
                if engine is not None:del engine;torch.mps.empty_cache()
                engine=CosyVoiceEngine(wanted);enable_mps_flow(engine.model.model)
                cache_reference_features(engine);profile=wanted
            convert_ready_pack(items,index,engine)
        if not (output.is_file() and metadata_path.is_file()):
            paths,source_duration=source_parts(source_folder/'original.mp3',folder)
            started=time.monotonic();speech=[]
            with torch.inference_mode():
                for source in paths:
                    speech.extend(x['tts_speech'].cpu() for x in engine.model.inference_vc(
                        str(source),str(engine.reference_audio),stream=False,speed=1.0))
            speech=torch.cat(speech,dim=1)
            assert torch.isfinite(speech).all() and speech.shape[1]>0
            save_wav(output,add_peak_headroom(speech),engine.model.sample_rate)
            metadata=dict(state='success',target_profile=wanted,source_sha256=receipt['sha256'],
                          text_sha256=item['text_sha256'],reference_sha256=hashlib.sha256(engine.reference_audio.read_bytes()).hexdigest(),
                          source_seconds=source_duration,seconds=speech.shape[1]/engine.model.sample_rate,
                          source_parts=len(paths),sample_rate=engine.model.sample_rate,
                          conversion_seconds=round(time.monotonic()-started,2),
                          sha256=hashlib.sha256(output.read_bytes()).hexdigest())
            metadata_path.write_text(json.dumps(metadata,ensure_ascii=False,indent=2))
        else:metadata=json.loads(metadata_path.read_text())
        assert metadata['source_sha256']==receipt['sha256'] and metadata['text_sha256']==item['text_sha256']
        assert abs(metadata['seconds']-metadata['source_seconds'])<.3
        outputs.append(dict(**item,file=str(output),seconds=metadata['seconds'],target_profile=wanted))
        progress_path.write_text(json.dumps(dict(completed=len(outputs),total=len(items),
             language=lang,last_id=item['id']),ensure_ascii=False,indent=2))
        if len(outputs)%10==0 or len(outputs)<=2:print('Converted',len(outputs),'of',len(items),lang,flush=True)
    (P/('voice-manifest'+suffix+'.json')).write_text(json.dumps(dict(source_sha256=plan['source_sha256'],
        target_voices=plan['target_voices'],items=outputs),ensure_ascii=False,indent=2))
    print('All target-voice files exist and were duration checked.',flush=True)


if __name__=='__main__':main()
