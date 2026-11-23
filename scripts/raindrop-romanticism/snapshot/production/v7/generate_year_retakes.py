"""Local-only spoken-year repairs; approved written captions are unchanged."""
import hashlib
import json
from pathlib import Path
import sys
import time

import mlx.core as mx
import numpy as np
import soundfile as sf
from mlx_audio.tts.utils import load_model

P=Path(__file__).resolve().parent;V6=P.parent/'v6'
MEDIA=P.parents[3]/'lucas-academy-media'
sys.path.insert(0,str(MEDIA/'src'))
from lucas_media.pronunciation import chinese_spoken_years


def main():
    plan=json.loads((V6/'synthesis-plan.json').read_text());jobs=[]
    for item in plan['requests']:
        if item['language']!='zh':continue
        spoken=chinese_spoken_years(item['text'])
        if spoken!=item['text']:
            jobs.append(dict(**item,spoken_text=spoken,spoken_sha256=hashlib.sha256(spoken.encode()).hexdigest()))
    (P/'year-retake-plan.json').write_text(json.dumps(dict(items=jobs,new_cloud_requests=0),ensure_ascii=False,indent=2))
    model=load_model(str(MEDIA/'models/Qwen3-TTS-12Hz-1.7B-CustomVoice-8bit'))
    for i,item in enumerate(jobs):
        folder=P/'year-retakes'/(item['id']+'-'+item['spoken_sha256'][:12]);folder.mkdir(parents=True,exist_ok=True)
        target=folder/'original.wav';receipt=folder/'generation.json'
        if target.is_file() and receipt.is_file():continue
        mx.random.seed(42+i);started=time.monotonic()
        output=list(model.generate_custom_voice(text=item['spoken_text'],speaker='Vivian',language='Chinese',
            instruct='自然、平静、温和的艺术纪录片叙述。清晰但不播音腔。年份按写出的四个汉字逐字读出，例如一八三八年，不增加千、百、十；四位数字连续自然，不刻意拉长停顿。其他文字准确照读。',
            max_tokens=1024,temperature=.65))
        audio=np.concatenate([np.asarray(r.audio).reshape(-1) for r in output]);rate=output[0].sample_rate
        assert np.isfinite(audio).all() and len(audio)>rate
        audio*=min(1,.98/max(.001,float(np.max(np.abs(audio)))))
        sf.write(target,audio,rate,subtype='PCM_16')
        meta=dict(state='success',**item,seconds=len(audio)/rate,elapsed_seconds=round(time.monotonic()-started,2),
                  model='Qwen3-TTS 1.7B CustomVoice 8-bit MLX',source_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),new_cloud_requests=0)
        receipt.write_text(json.dumps(meta,ensure_ascii=False,indent=2))
        print('Generated year repair',i+1,'/',len(jobs),item['id'],item['spoken_text'],flush=True)
    (P/'year-generation-complete.json').write_text(json.dumps(dict(total=len(jobs),state='complete')))


if __name__=='__main__':main()
