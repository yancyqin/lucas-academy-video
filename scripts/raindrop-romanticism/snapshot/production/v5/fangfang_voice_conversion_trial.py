"""Local performance-preserving voice conversion after MiniMax clone permission rejection."""
from functools import wraps
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

P = Path(__file__).resolve().parent
MEDIA = P.parents[3] / 'lucas-academy-media'
OUT = P / 'auditions/2026-11-20-fangfang-minimax'
OLD = P / 'auditions/2026-11-20-emotion'
os.environ['TOKENIZERS_PARALLELISM'] = 'false'
sys.path.insert(0, str(MEDIA / 'src'))

import torch
torch.set_num_threads(4)
torch.set_num_interop_threads(1)
from lucas_media.cosyvoice_engine import CosyVoiceEngine
from lucas_media.joke import save_wav, add_peak_headroom


def enable_mps_flow(model):
    original = model.flow.inference
    model.flow.to('mps')

    @wraps(original)
    def wrapped(**kwargs):
        inputs = {key: value.to('mps') if isinstance(value, torch.Tensor) else value
                  for key, value in kwargs.items()}
        mel, extra = original(**inputs)
        return mel.cpu(), extra

    model.flow.inference = wrapped


def main():
    jobs = [
        dict(id='minimax-fangfang-zh-vc', source=OLD/'minimax-auto/original.mp3', start=0, duration=27.0,
             description='MiniMax Speech 2.8 HD natural Mandarin performance converted locally to Fangfang timbre'),
        dict(id='owner-fangfang-zh-vc', source=OLD/'input-recordings/New Recording 2.m4a', start=16.0, duration=27.0,
             description='Owner recording 2 performance excerpt converted locally to Fangfang timbre'),
        dict(id='minimax-fangfang-en-vc', source=OUT/'english-natural/original.mp3', start=0, duration=27.0,
             description='MiniMax Speech 2.8 HD natural English performance converted locally to Fangfang timbre'),
        dict(id='owner-opening-fangfang-zh-vc', source=OLD/'input-recordings/New Recording.m4a', start=.5, duration=17.5,
             description='Owner recording 1 opening questions converted locally to Fangfang timbre'),
        dict(id='owner-quote-fangfang-zh-vc', source=OLD/'input-recordings/New Recording 2.m4a', start=31.3, duration=22.7,
             description='Owner recording 2 quoted exclamation and dream narration converted locally to Fangfang timbre'),
    ]
    for job in jobs:
        assert job['source'].is_file(), job['source']
        folder = OUT / job['id']
        folder.mkdir(exist_ok=True)
        source = folder / 'source.wav'
        subprocess.run(['/opt/homebrew/bin/ffmpeg', '-v', 'error', '-y', '-ss', str(job['start']),
                        '-i', str(job['source']), '-t', str(job['duration']), '-ar', '16000', '-ac', '1',
                        str(source)], check=True)
    engine = CosyVoiceEngine('fangfang/zh')
    enable_mps_flow(engine.model.model)
    for job in jobs:
        folder = OUT / job['id']
        target = folder / 'original.wav'
        if target.is_file():
            print('Existing conversion', job['id'], flush=True)
            continue
        print('Converting', job['id'], flush=True)
        started = time.monotonic()
        with torch.inference_mode():
            chunks = [item['tts_speech'].cpu() for item in engine.model.inference_vc(
                str(folder / 'source.wav'), str(engine.reference_audio), stream=False, speed=1.0)]
        speech = torch.cat(chunks, dim=1)
        assert torch.isfinite(speech).all() and speech.shape[1] > 10 * 24000
        save_wav(target, add_peak_headroom(speech), engine.model.sample_rate)
        reference_embedding = engine.model.frontend._extract_spk_embedding(str(engine.reference_audio)).flatten()
        source_embedding = engine.model.frontend._extract_spk_embedding(str(folder / 'source.wav')).flatten()
        converted_embedding = engine.model.frontend._extract_spk_embedding(str(target)).flatten()
        similarity = lambda first, second: float(torch.nn.functional.cosine_similarity(first, second, dim=0))
        metadata = {**{key: str(value) if isinstance(value, Path) else value for key, value in job.items()},
                    'method': 'CosyVoice3 speech-to-speech conversion, not MiniMax-native voice cloning',
                    'target_profile': 'fangfang/zh', 'sample_rate': engine.model.sample_rate,
                    'seconds': speech.shape[1] / engine.model.sample_rate,
                    'source_to_reference_cosine': similarity(source_embedding, reference_embedding),
                    'converted_to_reference_cosine': similarity(converted_embedding, reference_embedding),
                    'sha256': hashlib.sha256(target.read_bytes()).hexdigest()}
        (folder / 'receipt.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2))
        print(job['id'], 'seconds', metadata['seconds'], 'conversion time', round(time.monotonic()-started,2),
              'speaker similarity', metadata['converted_to_reference_cosine'], flush=True)
    print('Local voice conversion auditions complete', flush=True)


if __name__ == '__main__':
    main()
