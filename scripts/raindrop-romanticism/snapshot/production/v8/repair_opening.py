"""Reconvert opening English clips locally with silent model warm-up edges."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import wave

import numpy as np
import torch

P=Path(__file__).resolve().parent;V6=P.parent/'v6';sys.path.insert(0,str(V6))
from convert_narration import CosyVoiceEngine,enable_mps_flow,cache_reference_features
from lucas_media.joke import save_wav,add_peak_headroom

def main():
    plan=json.loads((P.parent/'v7/full-plan.json').read_text())
    chosen=[x for x in plan['voice_fragments'] if x['language']=='en' and x['id'] in ['n001-01','n002-01','n003-01']]
    engine=CosyVoiceEngine('louise/en');enable_mps_flow(engine.model.model);cache_reference_features(engine)
    outputs=[]
    for index,item in enumerate(chosen):
        folder=P/'opening-repairs'/(item['id']+'-'+item['text_sha256'][:12]);folder.mkdir(parents=True,exist_ok=True)
        receipt=folder/'receipt.json';output=folder/'voice.wav'
        original=V6/'minimax-sources/en'/(item['id']+'-'+item['text_sha256'][:12])/'original.mp3'
        if not (receipt.exists() and output.exists()):
            samples=np.frombuffer(subprocess.check_output(['/opt/homebrew/bin/ffmpeg','-v','error','-i',str(original),'-ar','16000','-ac','1','-f','f32le','-']),dtype='<f4')
            pad=16000;source=folder/'padded-source.wav';padded=np.pad(samples,(pad,pad))
            with wave.open(str(source),'wb') as writer:
                writer.setparams((1,2,16000,0,'NONE','not compressed'));writer.writeframes(np.round(padded*32767).astype('<i2').tobytes())
            torch.manual_seed(20261121+index)
            with torch.inference_mode():
                speech=torch.cat([r['tts_speech'].cpu() for r in engine.model.inference_vc(str(source),str(engine.reference_audio),stream=False,speed=1.0)],dim=1)
            rate=engine.model.sample_rate;start=rate;count=round(len(samples)*rate/16000)
            assert speech.shape[1]>=start+count;speech=speech[:,start:start+count]
            assert torch.isfinite(speech).all();save_wav(output,add_peak_headroom(speech),rate)
            meta=dict(item,state='success',file=str(output),seconds=count/rate,source_seconds=len(samples)/16000,
                source_sha256=hashlib.sha256(original.read_bytes()).hexdigest(),sha256=hashlib.sha256(output.read_bytes()).hexdigest(),
                method='Local Louise conversion of existing MiniMax source; temporary 1-second silence at each edge cropped away; speed=1.0')
            receipt.write_text(json.dumps(meta,ensure_ascii=False,indent=2))
        meta=json.loads(receipt.read_text());outputs.append(meta)
        prefix=folder/'asr'
        r=subprocess.run(['/opt/homebrew/bin/whisper-cli','-m','@USER_HOME@/.cache/whisper/ggml-small-q5_1.bin','-f',str(output),'-l','en','-otxt','-of',str(prefix),'-ng','-t','2','-np'],capture_output=True,text=True)
        r.check_returncode();print(item['id'],prefix.with_suffix('.txt').read_text(),flush=True)
    (P/'opening-overrides.json').write_text(json.dumps(dict(items=outputs,new_cloud_requests=0),ensure_ascii=False,indent=2))

if __name__=='__main__':main()
