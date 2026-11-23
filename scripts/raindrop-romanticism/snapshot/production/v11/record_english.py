"""Local English equivalent of the owner's two-question revision."""
import hashlib,json,time
from pathlib import Path
import mlx.core as mx
import numpy as np
import soundfile as sf
from mlx_audio.tts.utils import load_model

P=Path(__file__).resolve().parent;MEDIA=P.parents[3]/'lucas-academy-media'
TEXT="It sounds peaceful and beautiful, right? But can you imagine that, during the winter when he was writing this prelude, Chopin once sat at the piano in profound sorrow and anxiety?"
INSTRUCT='A warm, expressive female documentary narrator speaking natural, fluent English. Invite the listener gently with the first question. Then use But to make a thoughtful turn, with sincere curiosity and restrained compassion for Chopin. Natural conversational pace, connected phrases, no drawn-out vowels, no exaggerated acting. Read exactly the supplied words.'

def main():
    folder=P/'n002-english/serena';folder.mkdir(parents=True,exist_ok=True)
    output=folder/'original.wav';receipt=folder/'generation.json'
    if receipt.exists():print(receipt.read_text(),flush=True);return
    model=load_model(str(MEDIA/'models/Qwen3-TTS-12Hz-1.7B-CustomVoice-8bit'))
    seed=2026112131;mx.random.seed(seed);start=time.monotonic()
    parts=list(model.generate_custom_voice(text=TEXT,speaker='Serena',language='English',instruct=INSTRUCT,max_tokens=1536,temperature=.7))
    data=np.concatenate([np.asarray(r.audio).reshape(-1) for r in parts]);rate=parts[0].sample_rate
    assert np.isfinite(data).all() and np.max(np.abs(data))>.01
    data*=min(1,.98/float(np.max(np.abs(data))))
    sf.write(output,data,rate,subtype='PCM_16')
    meta=dict(id='n002-01',paragraph_id='n002',language='en',text=TEXT,spoken_text=TEXT,
        text_sha256=hashlib.sha256(TEXT.encode()).hexdigest(),file=str(output),seconds=len(data)/rate,
        performance_speaker='Serena',model='Qwen3-TTS-12Hz-1.7B-CustomVoice-8bit',instruct=INSTRUCT,
        seed=seed,elapsed=time.monotonic()-start,sha256=hashlib.sha256(output.read_bytes()).hexdigest(),new_cloud_requests=0,speed=1.0)
    receipt.write_text(json.dumps(meta,indent=2));print(json.dumps(meta,indent=2),flush=True)

if __name__=='__main__':main()
