"""Local Qwen3-TTS 1.7B expressive auditions in an isolated MLX environment."""
import hashlib
import importlib.metadata
import json
from pathlib import Path
import time

import mlx.core as mx
import numpy as np
import soundfile as sf
from mlx_audio.tts.utils import load_model

P=Path(__file__).resolve().parent
ROOT=P/'auditions/2026-11-20-alternative-providers'


def main():
    descriptor=json.loads((ROOT/'qwen-local-model.json').read_text())
    assert descriptor.get('local_path'), 'Wait for the weight download to finish.'
    scenes={s['id']:s for s in json.loads((P/'edit-plan.json').read_text())['scenes']}
    jobs=[
        dict(id='qwen3-local-zh',language='Chinese',speaker='Vivian',
             text=scenes['p010']['text_zh'].strip()+'\n\n肖邦看到她时惊呼了一声，说：“啊，我就知道，你们已经死了！”',
             instruct='像向身边的人讲述一段往事，语速自然，克制、有呼吸和自然停顿。叙述雨夜时平静而关切，说到肖邦的惊呼时，短暂露出惊惧与难以置信，再收住情绪。不要全程悲腔，不要播音腔。'),
        dict(id='qwen3-local-en',language='English',speaker='Aiden',
             text=scenes['p010']['text'].strip()+'\n\n'+scenes['p011']['text'].split(' Then he told her')[0].strip(),
             instruct='Natural, intimate storytelling at a conversational pace. Quiet and restrained, with concern underneath. Let the quotation briefly sound startled and disbelieving. Avoid theatrical crying or a newsreader cadence.'),
    ]
    pending=[j for j in jobs if not (ROOT/j['id']/'original.wav').is_file()]
    if not pending:
        print('Both local auditions already exist.');return
    print('Loading local MLX model',descriptor['model'],flush=True)
    model=load_model(descriptor['local_path'])
    for job in pending:
        folder=ROOT/job['id'];folder.mkdir(exist_ok=True)
        (folder/'request.json').write_text(json.dumps(dict(**job,model=descriptor['model'],revision=descriptor['revision']),ensure_ascii=False,indent=2))
        mx.random.seed(42)
        print('Generating',job['id'],flush=True)
        started=time.monotonic()
        results=list(model.generate_custom_voice(text=job['text'],speaker=job['speaker'],
            language=job['language'],instruct=job['instruct'],max_tokens=1024,temperature=.7))
        assert results
        audio=np.concatenate([np.asarray(result.audio).reshape(-1) for result in results])
        rate=results[0].sample_rate
        assert np.isfinite(audio).all() and len(audio)>10*rate
        if np.max(np.abs(audio))>.98:audio=audio*.98/np.max(np.abs(audio))
        target=folder/'original.wav';sf.write(target,audio,rate,subtype='PCM_16')
        receipt=dict(state='success',provider='local',model=descriptor['model'],revision=descriptor['revision'],
                     mlx_audio_version=importlib.metadata.version('mlx-audio'),
                     sample_rate=rate,seconds=len(audio)/rate,elapsed_seconds=round(time.monotonic()-started,2),
                     mlx_peak_memory_gb=round(mx.get_peak_memory()/1e9,3),
                     sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
                     voice_note='CustomVoice preset performance; target Fangfang/Louise timbre is a separate local conversion.')
        (folder/'receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2))
        print(json.dumps(receipt,ensure_ascii=False),flush=True)


if __name__=='__main__':main()
