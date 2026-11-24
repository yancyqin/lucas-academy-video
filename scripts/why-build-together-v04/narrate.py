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
INSTRUCT = '用清楚、自然的普通话，像和家长轻松交谈。语速自然利落，温和而有好奇心。问句有轻微起伏，陈述句干净收住，避免播音腔、拖长尾音和过度煽情。只读提供的文字。'


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def prepare():
    text = (DOC / 'zh-script-v04.md').read_text().split('## 01 ', 1)[1].split('\n---\n', 1)[0]
    section = 'opening'
    kinds = {'01':'opening', '02':'needs', '03':'content', '04':'building', '05':'closing'}
    rows = []
    for p in text.split('\n\n'):
        p = p.strip()
        if not p:
            continue
        if p.startswith('## '):
            section = kinds[re.search(r'## (\d\d)', p).group(1)]
            continue
        if p.startswith('穿越开场'):
            continue
        p = p.replace('（播视频）', '').strip()
        kind = 'insert_intro' if p.startswith('我们来看一下') else section
        pieces = [x for x in re.split(r'(?<=[。！？；])', p) if x.strip()]
        groups, current = [], ''
        for x in pieces:
            if current and len(current + x) > 55:
                groups.append(current)
                current = ''
            current += x
        if current:
            groups.append(current)
        for value in groups:
            rows.append(dict(id=f'n{len(rows)+1:03}', kind=kind, text=value,
                             spoken_text=value, voice='louise/zh'))
    assert rows[0]['text'].startswith('穿越到两千年前')
    assert rows[-1]['kind']=='insert_intro' and len(rows)==12
    assert sum(r['kind']=='insert_intro' for r in rows) == 1
    rows[7]['spoken_text']='游戏图片短视频，要多少有多少。但这些内容能给孩子带来什么？'
    spec = dict(title='孩子做项目，我们真正看重什么？', language='zh', rows=rows,
                approved_script_sha256=sha(DOC/'zh-script-v04.md'),
                embedded_movie=str(ROOT.parent/'lucas-academy-video-data/curiosity-builds-20261118/v10/delivery/curiosity-builds.en.no-voice.mp4'),
                embedded_subtitles=str(ROOT.parent/'lucas-academy-video-data/curiosity-builds-20261118/v10/delivery/curiosity-builds.en.no-voice.zh-CN.srt'))
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT/'script.json').write_text(json.dumps(spec, ensure_ascii=False, indent=2)+'\n')
    (DOC/'approved-script-v03.json').write_text(json.dumps(spec, ensure_ascii=False, indent=2)+'\n')
    return rows


def tts(rows):
    import mlx.core as mx
    from mlx_audio.tts.utils import load_model
    import numpy as np
    import soundfile as sf
    model = None
    dest = OUT/'audio/qwen'; dest.mkdir(parents=True, exist_ok=True)
    for row in rows:
        wav = dest/(row['id']+'.wav'); meta = wav.with_suffix('.json')
        config = dict(text=row['spoken_text'], model=str(MODEL), speaker='Serena',
                      language='Chinese', instruct=('自然利落地和家长交谈，语速轻快清楚。游戏图片短视频连贯地列举，不逐个拖长，不在列举词之间停顿。全段两个意群，中间只作短暂换气，问句干净收住。不要播音腔，不要过度强调或拉长尾音，只读文字。' if row['id']=='n008' else INSTRUCT), temperature=.65,
                      seed=20261122+int(row['id'][1:])+(200 if row['id']=='n008' else 0), new_cloud_requests=0)
        if wav.exists() and meta.exists():
            old = json.loads(meta.read_text())
            if old.get('config') == config and old.get('sha256') == sha(wav):
                print('Cached', row['id'], flush=True); continue
        if model is None:
            model = load_model(str(MODEL))
        mx.random.seed(config['seed']); start = time.monotonic()
        parts = list(model.generate_custom_voice(text=config['text'], speaker='Serena',
                     language='Chinese', instruct=config['instruct'], temperature=.65, max_tokens=2048))
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
    dest = OUT/'audio/louise'; dest.mkdir(parents=True, exist_ok=True)
    engine = None
    ref = MEDIA/'profiles/louise/zh/reference.wav'
    for row in rows:
        source = OUT/'audio/qwen'/(row['id']+'.wav')
        wav = dest/(row['id']+'.wav'); meta = wav.with_suffix('.json')
        signature = dict(source_sha256=sha(source), reference_sha256=sha(ref),
                         voice='louise/zh', padding_seconds=1, speed=1.0)
        if wav.exists() and meta.exists():
            old=json.loads(meta.read_text())
            if old.get('signature')==signature and old.get('sha256')==sha(wav):
                print('Cached Louise',row['id'],flush=True);continue
        if engine is None:
            engine=CosyVoiceEngine(MEDIA/'profiles/louise/zh/profile.json')
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
