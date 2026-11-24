"""Local Qwen performance, followed by duration-preserving Louise conversion."""
from __future__ import annotations
import argparse
from functools import wraps
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
MEDIA = ROOT.parent / 'lucas-academy-media'
OUT = ROOT / 'out/why-build-together-v04'
DOC = ROOT / 'docs/why-build-together'
MODEL = MEDIA / 'models/Qwen3-TTS-12Hz-1.7B-CustomVoice-8bit'
INSTRUCT = 'Speak clear, conversational English to parents. Warm, curious, and concise. Keep lists connected, with brief natural pauses. Avoid dramatic emphasis, drawn-out words, and a sales pitch. Read only the supplied words.'


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def prepare():
    return json.loads((OUT/'script-en.json').read_text())['rows']


def tts(rows):
    import mlx.core as mx
    from mlx_audio.tts.utils import load_model
    import numpy as np
    import soundfile as sf
    model = None
    dest = OUT/'audio/en/qwen'; dest.mkdir(parents=True, exist_ok=True)
    for row in rows:
        wav = dest/(row['id']+'.wav'); meta = wav.with_suffix('.json')
        config = dict(text=row['spoken_text'], model=str(MODEL), speaker='Serena',
                      language='English', instruct=INSTRUCT, temperature=.65,
                      seed=20261123+int(row['id'][1:]), new_cloud_requests=0)
        if wav.exists() and meta.exists():
            old = json.loads(meta.read_text())
            if old.get('config') == config and old.get('sha256') == sha(wav):
                print('Cached', row['id'], flush=True); continue
        if model is None:
            model = load_model(str(MODEL))
        mx.random.seed(config['seed']); start = time.monotonic()
        parts = list(model.generate_custom_voice(text=config['text'], speaker='Serena',
                     language='English', instruct=config['instruct'], temperature=.65, max_tokens=2048))
        assert parts, row['id']
        data = np.concatenate([np.asarray(x.audio).reshape(-1) for x in parts])
        rate = parts[0].sample_rate
        assert np.isfinite(data).all() and .5 < len(data)/rate < 28, (row['id'], len(data)/rate)
        peak = float(np.abs(data).max())
        assert peak > .005
        if peak > .9: data *= .9/peak
        sf.write(wav, data, rate, subtype='PCM_16')
        meta.write_text(json.dumps(dict(config=config, duration=len(data)/rate, sample_rate=rate,
                        seconds_spent=round(time.monotonic()-start, 2), sha256=sha(wav)),ensure_ascii=False,indent=2)+'\n')
        print('Qwen', row['id'], round(len(data)/rate,2), row['text'], flush=True)
        mx.clear_cache()


def vc(rows):
    os.environ.setdefault('TOKENIZERS_PARALLELISM','false')
    import numpy as np
    import torch
    import soundfile as sf
    sys.path.insert(0, str(MEDIA/'src'))
    from lucas_media.cosyvoice_engine import CosyVoiceEngine
    torch.set_num_threads(4); torch.set_num_interop_threads(1)
    dest = OUT/'audio/en/louise'; dest.mkdir(parents=True, exist_ok=True)
    engine = None
    ref = MEDIA/'profiles/louise/en/reference.wav'
    for row in rows:
        source = OUT/'audio/en/qwen'/(row['id']+'.wav')
        wav = dest/(row['id']+'.wav'); meta = wav.with_suffix('.json')
        signature = dict(source_sha256=sha(source), reference_sha256=sha(ref),
                         voice='louise/en', padding_seconds=1, speed=1.0)
        if wav.exists() and meta.exists():
            old=json.loads(meta.read_text())
            if old.get('signature')==signature and old.get('sha256')==sha(wav):
                print('Cached Louise',row['id'],flush=True);continue
        if engine is None:
            engine=CosyVoiceEngine(MEDIA/'profiles/louise/en/profile.json')
            if torch.backends.mps.is_available():
                original=engine.model.model.flow.inference
                engine.model.model.flow.to('mps')
                @wraps(original)
                def mps_flow(**kwargs):
                    mel,extra=original(**{k:v.to('mps') if isinstance(v,torch.Tensor) else v for k,v in kwargs.items()})
                    return mel.cpu(),extra
                engine.model.model.flow.inference=mps_flow
            frontend=engine.model.frontend
            for key in ['_extract_speech_token','_extract_speech_feat','_extract_spk_embedding']:
                method=getattr(frontend,key); cache={}
                def cached(path,*args,_method=method,_cache=cache,**kwargs):
                    if str(path)!=str(engine.reference_audio):return _method(path,*args,**kwargs)
                    if 'value' not in _cache:_cache['value']=_method(path,*args,**kwargs)
                    return _cache['value']
                setattr(frontend,key,cached)
        data=np.frombuffer(subprocess.check_output(['ffmpeg','-v','error','-i',str(source),'-ar','16000','-ac','1','-f','f32le','-']),dtype='<f4').copy()
        padded=dest/(row['id']+'.padded.wav');sf.write(padded,np.pad(data,(16000,16000)),16000)
        torch.manual_seed(20261122+int(row['id'][1:]));start=time.monotonic()
        with torch.inference_mode():
            chunks=[x['tts_speech'].cpu() for x in engine.model.inference_vc(str(padded),str(engine.reference_audio),stream=False,speed=1.0)]
        assert chunks
        speech=torch.cat(chunks,dim=1).numpy().reshape(-1);rate=engine.model.sample_rate
        count=round(len(data)*rate/16000)
        assert len(speech)>=rate+count
        speech=speech[rate:rate+count]
        assert np.isfinite(speech).all() and np.abs(speech).max()>.005
        if np.abs(speech).max()>.9:speech*=.9/np.abs(speech).max()
        sf.write(wav,speech,rate,subtype='PCM_24')
        meta.write_text(json.dumps(dict(signature=signature, duration=len(speech)/rate,
                       source_duration=len(data)/16000, sha256=sha(wav),
                       seconds_spent=round(time.monotonic()-start,2), new_cloud_requests=0),ensure_ascii=False,indent=2)+'\n')
        print('Louise',row['id'],round(len(speech)/rate,2),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('stage',choices=['prepare','tts','vc'])
    parser.add_argument('--only')
    args=parser.parse_args(); rows=prepare()
    if args.only:rows=[r for r in rows if r['id']==args.only]
    if args.stage=='tts':tts(rows)
    elif args.stage=='vc':vc(rows)
    else:print('Prepared',len(rows),'narration passages.')
