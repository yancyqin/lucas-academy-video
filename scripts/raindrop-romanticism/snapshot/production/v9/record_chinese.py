"""Local natural-paced takes of the owner's requested Mallorca sentence."""
import hashlib,json,time
from pathlib import Path
import sys
import mlx.core as mx
import numpy as np
import soundfile as sf
from mlx_audio.tts.utils import load_model

P=Path(__file__).resolve().parent;MEDIA=P.parents[3]/'lucas-academy-media'
def main():
    old=json.loads((P.parent/'v8/full-plan.json').read_text())
    item=next(i for i in old['voice_fragments'] if i['language']=='zh' and i['id']=='n003-01')
    text=item['spoken_text']
    prompt='自然流畅、亲切清楚的纪录片叙述，正常偏明快的语速。像向朋友简洁地介绍一件往事，连贯说完整句话，不拖长声音，不刻意煽情，不逐字顿读，逗号处只轻轻停顿。年份一八三八，四个数字自然连续读，保留年字。肖邦、乔治桑等名字也连贯自然。不要添加或删除任何字。'
    model=load_model(str(MEDIA/'models/Qwen3-TTS-12Hz-1.7B-CustomVoice-8bit'))
    results=[]
    for k,speaker in enumerate(['Vivian','Serena']):
        folder=P/'chinese-retake'/speaker.lower();folder.mkdir(parents=True,exist_ok=True)
        output=folder/'original.wav';receipt=folder/'generation.json'
        if not (output.exists() and receipt.exists()):
            mx.random.seed(202611210+k);start=time.monotonic()
            parts=list(model.generate_custom_voice(text=text,speaker=speaker,language='Chinese',instruct=prompt,max_tokens=768,temperature=.7))
            data=np.concatenate([np.asarray(r.audio).reshape(-1) for r in parts]);rate=parts[0].sample_rate
            assert np.isfinite(data).all();data*=min(1,.98/max(.001,float(np.max(np.abs(data)))))
            sf.write(output,data,rate,subtype='PCM_16')
            meta=dict(item,file=str(output),seconds=len(data)/rate,performance_speaker=speaker,instruct=prompt,
                elapsed=time.monotonic()-start,sha256=hashlib.sha256(output.read_bytes()).hexdigest(),new_cloud_requests=0)
            receipt.write_text(json.dumps(meta,ensure_ascii=False,indent=2))
        meta=json.loads(receipt.read_text());results.append(meta)
        print('Chinese native take',speaker,meta['seconds'],'seconds',flush=True)
    eligible=[r for r in results if 6.5<=r['seconds']<=9.8]
    if not eligible:raise RuntimeError('Natural-paced retakes need review; do not time-stretch.')
    chosen=min(eligible,key=lambda r:abs(r['seconds']-8.5))
    (P/'chinese-selected.json').write_text(json.dumps(chosen,ensure_ascii=False,indent=2))
    print('Selected native performance:',chosen['performance_speaker'],chosen['seconds'],flush=True)

if __name__=='__main__':main()
