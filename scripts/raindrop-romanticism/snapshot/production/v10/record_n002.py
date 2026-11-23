"""Owner's exact two-question revision, generated locally at native speed."""
import hashlib,json,time
from pathlib import Path
import mlx.core as mx
import numpy as np
import soundfile as sf
from mlx_audio.tts.utils import load_model

P=Path(__file__).resolve().parent
MEDIA=P.parents[3]/'lucas-academy-media'
TEXT='听起来平静而优美，对吗？但是你能想象，在写这个前奏曲的那个冬天，肖邦曾在极度悲伤和焦虑中弹琴吗？'
INSTRUCT='自然流畅、温柔而有感染力的纪录片女声。第一句轻轻地向听众提问。接着用但是自然转折，带着真诚的好奇与关切，讲述肖邦的悲伤与焦虑，克制而感人。语速自然，不拖字，不逐字顿读，逗号只作轻微停顿。不要添加或删除任何字。'

def main():
    model=load_model(str(MEDIA/'models/Qwen3-TTS-12Hz-1.7B-CustomVoice-8bit'))
    folder=P/'n002-retake/serena';folder.mkdir(parents=True,exist_ok=True)
    output=folder/'original.wav';receipt=folder/'generation.json'
    if receipt.exists():print(receipt.read_text(),flush=True);return
    seed=2026112122;mx.random.seed(seed);start=time.monotonic()
    parts=list(model.generate_custom_voice(text=TEXT,speaker='Serena',language='Chinese',instruct=INSTRUCT,max_tokens=1024,temperature=.7))
    audio=np.concatenate([np.asarray(r.audio).reshape(-1) for r in parts]);rate=parts[0].sample_rate
    assert np.isfinite(audio).all() and float(np.max(np.abs(audio)))>.01
    audio*=min(1,.98/float(np.max(np.abs(audio))))
    sf.write(output,audio,rate,subtype='PCM_16')
    meta=dict(id='n002-01',paragraph_id='n002',language='zh',text=TEXT,spoken_text=TEXT,
        text_sha256=hashlib.sha256(TEXT.encode()).hexdigest(),file=str(output),seconds=len(audio)/rate,
        performance_speaker='Serena',model='Qwen3-TTS-12Hz-1.7B-CustomVoice-8bit',instruct=INSTRUCT,
        seed=seed,elapsed=time.monotonic()-start,sha256=hashlib.sha256(output.read_bytes()).hexdigest(),new_cloud_requests=0,speed=1.0)
    receipt.write_text(json.dumps(meta,ensure_ascii=False,indent=2))
    print(json.dumps(meta,ensure_ascii=False,indent=2),flush=True)

if __name__=='__main__':main()
