"""Match audition timbres locally, leaving performance timing unchanged."""
import hashlib
import json
from pathlib import Path
import subprocess
import time

from fangfang_voice_conversion_trial import enable_mps_flow, torch, CosyVoiceEngine
from lucas_media.joke import save_wav, add_peak_headroom
from finish_auditions import normalize

P=Path(__file__).resolve().parent
ROOT=P/'auditions/2026-11-20-alternative-providers'
DEST=Path('@USER_HOME@/Desktop/肖邦配音试听-2026-11-20')


def main():
    jobs=[
        ('eleven-v4-en','original.mp3','louise/en','14-ElevenV4演绎-Louise英文换声.mp3'),
        ('qwen3-local-zh','original.wav','fangfang/zh','16-Qwen3本地演绎-Fangfang中文换声.mp3'),
        ('qwen3-local-en','original.wav','louise/en','18-Qwen3本地演绎-Louise英文换声.mp3'),
    ]
    engine=None;active_profile=None
    for identifier,source_name,profile,delivery_name in jobs:
        folder=ROOT/identifier;source=folder/source_name
        if not source.is_file():continue
        converted=folder/'converted.wav'
        if not converted.is_file():
            duration=float(subprocess.check_output(['/opt/homebrew/bin/ffprobe','-v','error',
                '-show_entries','format=duration','-of','default=nw=1:nk=1',str(source)]))
            if duration>29.5:
                print(identifier,'needs clean segment boundaries; preserving original audition',duration,flush=True)
                continue
            wav=folder/'vc-source.wav'
            subprocess.run(['/opt/homebrew/bin/ffmpeg','-v','error','-y','-i',str(source),
                            '-ar','16000','-ac','1',str(wav)],check=True)
            if active_profile!=profile:
                if engine is not None:del engine;torch.mps.empty_cache()
                engine=CosyVoiceEngine(profile);enable_mps_flow(engine.model.model);active_profile=profile
            started=time.monotonic()
            with torch.inference_mode():
                chunks=[item['tts_speech'].cpu() for item in engine.model.inference_vc(
                    str(wav),str(engine.reference_audio),stream=False,speed=1.0)]
            speech=torch.cat(chunks,dim=1)
            assert torch.isfinite(speech).all()
            save_wav(converted,add_peak_headroom(speech),engine.model.sample_rate)
            receipt=dict(target_profile=profile,method='Local CosyVoice3 voice conversion',
                         source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                         seconds=speech.shape[1]/engine.model.sample_rate,
                         elapsed_seconds=round(time.monotonic()-started,2))
            (folder/'conversion.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2))
        result=normalize(converted,DEST/delivery_name)
        (folder/'converted-delivery.json').write_text(json.dumps(dict(file=str(DEST/delivery_name),**result),ensure_ascii=False,indent=2))
        print(delivery_name,result['duration'],flush=True)


if __name__=='__main__':main()
