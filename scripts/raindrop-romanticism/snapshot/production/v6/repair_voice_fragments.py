"""Review alternate, edge-padded conversions for a few ASR-flagged fragments."""
import hashlib
import json
from pathlib import Path
import subprocess
import time
import wave

import numpy as np
import torch

from convert_narration import P,CosyVoiceEngine,enable_mps_flow,cache_reference_features
from lucas_media.joke import save_wav,add_peak_headroom


def main():
    plan=json.loads((P/'synthesis-plan.json').read_text())
    chosen=['n001-01','n026-01','n027-01','n040-02']
    engine=CosyVoiceEngine('louise/en');enable_mps_flow(engine.model.model);cache_reference_features(engine)
    for index,identifier in enumerate(chosen):
        item=next(x for x in plan['requests'] if x['language']=='en' and x['id']==identifier)
        key=identifier+'-'+item['text_sha256'][:12]
        folder=P/'checks/voice-repairs'/key;folder.mkdir(parents=True,exist_ok=True)
        original=P/'minimax-sources/en'/key/'original.mp3'
        samples=np.frombuffer(subprocess.check_output(['/opt/homebrew/bin/ffmpeg','-v','error','-i',str(original),
            '-ar','16000','-ac','1','-f','f32le','-']),dtype='<f4')
        padding=6400
        padded=np.pad(samples,(padding,padding));assert len(padded)/16000<30
        source=folder/'padded-source.wav'
        with wave.open(str(source),'wb') as writer:
            writer.setparams((1,2,16000,0,'NONE','not compressed'))
            writer.writeframes(np.round(np.clip(padded,-1,1)*32767).astype('<i2').tobytes())
        torch.manual_seed(20261121+index);started=time.monotonic()
        with torch.inference_mode():
            speech=torch.cat([x['tts_speech'].cpu() for x in engine.model.inference_vc(
                str(source),str(engine.reference_audio),stream=False,speed=1.0)],dim=1)
        rate=engine.model.sample_rate;offset=round(padding*rate/16000);count=round(len(samples)*rate/16000)
        assert speech.shape[1]>=offset+count
        speech=speech[:,offset:offset+count];assert torch.isfinite(speech).all()
        candidate=folder/'candidate.wav';save_wav(candidate,add_peak_headroom(speech),rate)
        receipt=dict(state='review_candidate',source_sha256=hashlib.sha256(original.read_bytes()).hexdigest(),
                     text_sha256=item['text_sha256'],target_profile='louise/en',
                     reference_sha256=hashlib.sha256(engine.reference_audio.read_bytes()).hexdigest(),
                     source_seconds=len(samples)/16000,seconds=count/rate,sample_rate=rate,source_parts=1,
                     conversion_seconds=round(time.monotonic()-started,2),temporary_edge_padding_seconds=.4,
                     sha256=hashlib.sha256(candidate.read_bytes()).hexdigest())
        (folder/'receipt.json').write_text(json.dumps(receipt,indent=2))
        prefix=folder/'asr'
        result=subprocess.run(['/opt/homebrew/bin/whisper-cli','-m','@USER_HOME@/.cache/whisper/ggml-small-q5_1.bin',
              '-f',str(candidate),'-l','en','-otxt','-of',str(prefix),'-ng','-t','2','-np'],capture_output=True,text=True)
        (folder/'asr.log').write_text(result.stderr);result.check_returncode()
        print(identifier,'EXPECTED',item['text'],'CANDIDATE',prefix.with_suffix('.txt').read_text(),flush=True)


if __name__=='__main__':main()
