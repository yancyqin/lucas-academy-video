"""Use the existing local CosyVoice model to speak the current English script."""
from functools import wraps
from pathlib import Path
import argparse,hashlib,json,os,sys,time
import numpy as np
import soundfile as sf
import torch

ROOT=Path(__file__).resolve().parents[2]
MEDIA=ROOT.parent/'lucas-academy-media'
TRIAL=ROOT.parent/'lucas-academy-video-data/why-build-together-20261122/cosyvoice-en-trial-20261123'
sys.path.insert(0,str(MEDIA/'src'))

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--only');parser.add_argument('--seed-offset',type=int,default=0)
    args=parser.parse_args()
    os.environ.setdefault('TOKENIZERS_PARALLELISM','false')
    from lucas_media.cosyvoice_engine import CosyVoiceEngine
    torch.set_num_threads(4);torch.set_num_interop_threads(1)
    rows=json.loads((TRIAL/'script.json').read_text())['rows']
    if args.only:rows=[r for r in rows if r['id']==args.only]
    profile=MEDIA/'profiles/louise/en/profile.json'
    reference=profile.parent/'reference.wav'
    assert json.loads(profile.read_text())['consent']
    dest=TRIAL/'takes';dest.mkdir(parents=True,exist_ok=True)
    engine=None
    for row in rows:
        wav=dest/(row['id']+'.wav');meta=wav.with_suffix('.json')
        config={'text':row['spoken_text'],'model':'Fun-CosyVoice3-0.5B','mode':'zero-shot',
            'profile':'louise/en','reference_sha256':sha(reference),'profile_sha256':sha(profile),
            'speed':1.0,'seed':20261123+int(row['id'][1:])+args.seed_offset,'new_cloud_requests':0}
        if wav.exists() and meta.exists():
            old=json.loads(meta.read_text())
            if old.get('config')==config and old.get('sha256')==sha(wav):
                print('Cached',row['id'],flush=True);continue
            raise RuntimeError(f'Existing take differs; archive it before a retake: {wav}')
        if engine is None:
            engine=CosyVoiceEngine(profile)
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
                method=getattr(frontend,key);cache={}
                def cached(path,*args,_method=method,_cache=cache,**kwargs):
                    if str(path)!=str(engine.reference_audio):return _method(path,*args,**kwargs)
                    if 'value' not in _cache:_cache['value']=_method(path,*args,**kwargs)
                    return _cache['value']
                setattr(frontend,key,cached)
        print('Generating',row['id'],row['spoken_text'],flush=True)
        torch.manual_seed(config['seed']);started=time.monotonic()
        with torch.inference_mode():
            speech,rate,mode=engine.synthesize(row['spoken_text'],target_language='en',mode='zero-shot',speed=1.0)
        samples=speech.detach().cpu().numpy().reshape(-1)
        assert np.isfinite(samples).all() and .4<len(samples)/rate<45
        peak=float(np.abs(samples).max());assert peak>.005
        if peak>.89:samples*=.89/peak
        sf.write(wav,samples,rate,subtype='PCM_24')
        assert wav.stat().st_size>rate*.4*3
        facts={'config':config,'sha256':sha(wav),'seconds':len(samples)/rate,'sample_rate':rate,
            'peak':float(np.abs(samples).max()),'finite_nonempty':True,'mode':mode,
            'seconds_spent':round(time.monotonic()-started,2),'post_synthesis_time_stretch':False}
        meta.write_text(json.dumps(facts,ensure_ascii=False,indent=2)+'\n')
        print('Saved',row['id'],facts['seconds'],'seconds, generated in',facts['seconds_spent'],flush=True)
    print('Finished',len(rows),'takes',flush=True)

if __name__=='__main__':main()
