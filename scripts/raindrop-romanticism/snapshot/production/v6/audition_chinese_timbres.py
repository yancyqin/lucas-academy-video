"""Owner-requested Eunice/Louise Mandarin auditions, entirely local and cached."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
import wave

import numpy as np
import torch

from convert_narration import P,P5,CosyVoiceEngine,enable_mps_flow,cache_reference_features
from lucas_media.joke import save_wav,add_peak_headroom
from finish_auditions import normalize

ROOT=P/'auditions/2026-11-21-chinese-timbres'
DEST=Path('@USER_HOME@/Desktop/肖邦配音试听-2026-11-20')
SOURCES={
    'minimax':P5/'auditions/2026-11-20-fangfang-minimax/minimax-fangfang-zh-vc/source.wav',
    'qwen':P5/'auditions/2026-11-20-alternative-providers/qwen3-local-zh/original.wav',
}


def main():
    jobs=[('minimax','eunice/en','19-MiniMax演绎-Eunice中文换声.mp3'),
          ('qwen','eunice/en','20-Qwen3本地演绎-Eunice中文换声.mp3'),
          ('minimax','louise/zh','21-MiniMax演绎-Louise中文换声.mp3'),
          ('qwen','louise/zh','22-Qwen3本地演绎-Louise中文换声.mp3'),
          ('minimax','sunny/zh','23-MiniMax演绎-Sunny中文换声.mp3'),
          ('qwen','sunny/zh','24-Qwen3本地演绎-Sunny中文换声.mp3')]
    ROOT.mkdir(parents=True,exist_ok=True);engine=None;active=None;deliveries=[]
    for index,(provider,profile,filename) in enumerate(jobs):
        suffix='-zh' if profile=='eunice/en' else '-'+profile.replace('/','-')+'ref-zh'
        folder=ROOT/(provider+'-'+profile.split('/')[0]+suffix);folder.mkdir(exist_ok=True)
        source=SOURCES[provider];assert source.is_file()
        output=folder/'converted.wav';receipt_path=folder/'receipt.json'
        source_sha=hashlib.sha256(source.read_bytes()).hexdigest()
        if not (output.is_file() and receipt_path.is_file()):
            raw=subprocess.check_output(['/opt/homebrew/bin/ffmpeg','-v','error','-i',str(source),
                    '-ar','16000','-ac','1','-f','f32le','-'])
            samples=np.frombuffer(raw,dtype='<f4');padding=6400
            padded=np.pad(samples,(padding,padding));assert len(padded)/16000<30
            wav=folder/'padded-source.wav'
            with wave.open(str(wav),'wb') as writer:
                writer.setparams((1,2,16000,0,'NONE','not compressed'))
                writer.writeframes(np.round(np.clip(padded,-1,1)*32767).astype('<i2').tobytes())
            if active!=profile:
                if engine is not None:del engine;torch.mps.empty_cache()
                engine=CosyVoiceEngine(profile);enable_mps_flow(engine.model.model)
                cache_reference_features(engine);active=profile
            torch.manual_seed(20261121+index);started=time.monotonic()
            with torch.inference_mode():
                speech=torch.cat([item['tts_speech'].cpu() for item in engine.model.inference_vc(
                    str(wav),str(engine.reference_audio),stream=False,speed=1.0)],dim=1)
            rate=engine.model.sample_rate;offset=round(padding*rate/16000);count=round(len(samples)*rate/16000)
            assert speech.shape[1]>=offset+count
            speech=speech[:,offset:offset+count];assert torch.isfinite(speech).all()
            save_wav(output,add_peak_headroom(speech),rate)
            receipt=dict(state='success',provider_performance=provider,target_profile=profile,
                         source_sha256=source_sha,reference_sha256=hashlib.sha256(engine.reference_audio.read_bytes()).hexdigest(),
                         seconds=count/rate,source_seconds=len(samples)/16000,sample_rate=rate,
                         conversion_seconds=round(time.monotonic()-started,2),temporary_edge_padding_removed_seconds=.4,
                         sha256=hashlib.sha256(output.read_bytes()).hexdigest(),new_cloud_requests=0,
                         method='Local CosyVoice3 conversion; existing Mandarin source performance; authorized '+profile+' reference.')
            receipt_path.write_text(json.dumps(receipt,ensure_ascii=False,indent=2))
        receipt=json.loads(receipt_path.read_text());assert receipt['source_sha256']==source_sha and receipt['target_profile']==profile
        assert hashlib.sha256(output.read_bytes()).hexdigest()==receipt['sha256']
        result=normalize(output,DEST/filename)
        delivery=dict(provider=provider,target_profile=profile,file=str(DEST/filename),new_api_cost=0,**result)
        (folder/'delivery.json').write_text(json.dumps(delivery,ensure_ascii=False,indent=2));deliveries.append(delivery)
        print('Ready',filename,round(result['duration'],2),'seconds; new cloud requests: 0',flush=True)
    (ROOT/'delivery-manifest.json').write_text(json.dumps(dict(new_cloud_requests=0,items=deliveries),ensure_ascii=False,indent=2))
    print('Six local Mandarin timbre comparisons ready.',flush=True)


if __name__=='__main__':main()
