"""Reuse the approved Fangfang reference for local Chinese year repairs."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
import wave

import numpy as np
import torch

P=Path(__file__).resolve().parent;V6=P.parent/'v6';sys.path.insert(0,str(V6))
from convert_narration import CosyVoiceEngine,enable_mps_flow,cache_reference_features
from lucas_media.joke import save_wav,add_peak_headroom


def main():
    while not (P/'year-generation-complete.json').is_file():time.sleep(1)
    jobs=json.loads((P/'year-retake-plan.json').read_text())['items']
    engine=CosyVoiceEngine('fangfang/zh');enable_mps_flow(engine.model.model);cache_reference_features(engine)
    manifest=[]
    for i,item in enumerate(jobs):
        folder=P/'year-retakes'/(item['id']+'-'+item['spoken_sha256'][:12]);output=folder/'voice.wav';receipt=folder/'conversion.json'
        if not (output.is_file() and receipt.is_file()):
            raw=subprocess.check_output(['/opt/homebrew/bin/ffmpeg','-v','error','-i',str(folder/'original.wav'),'-ar','16000','-ac','1','-f','f32le','-'])
            samples=np.frombuffer(raw,dtype='<f4');pad=6400;padded=np.pad(samples,(pad,pad));assert len(padded)/16000<30
            source=folder/'padded-source.wav'
            with wave.open(str(source),'wb') as writer:
                writer.setparams((1,2,16000,0,'NONE','not compressed'));writer.writeframes(np.round(np.clip(padded,-1,1)*32767).astype('<i2').tobytes())
            torch.manual_seed(42+i)
            with torch.inference_mode():
                speech=torch.cat([r['tts_speech'].cpu() for r in engine.model.inference_vc(str(source),str(engine.reference_audio),stream=False,speed=1.0)],dim=1)
            rate=engine.model.sample_rate;offset=round(pad*rate/16000);count=round(len(samples)*rate/16000)
            assert speech.shape[1]>=offset+count;speech=speech[:,offset:offset+count];assert torch.isfinite(speech).all()
            save_wav(output,add_peak_headroom(speech),rate)
            receipt.write_text(json.dumps(dict(state='success',**item,seconds=count/rate,file=str(output),target_profile='fangfang/zh',
                sha256=hashlib.sha256(output.read_bytes()).hexdigest(),method='Local Qwen performance → local Fangfang conversion; calendar-year spoken form repair.'),ensure_ascii=False,indent=2))
        meta=json.loads(receipt.read_text());manifest.append(meta)
        print('Converted year repair',i+1,'/',len(jobs),item['id'],flush=True)
    (P/'year-voice-overrides.json').write_text(json.dumps(dict(items=manifest,new_cloud_requests=0),ensure_ascii=False,indent=2))


if __name__=='__main__':main()
