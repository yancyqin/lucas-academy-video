"""Generate Fangfang Mandarin with the already validated local speech backend."""
from collections import defaultdict
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys

P = Path(__file__).resolve().parent
MEDIA = P.parents[3] / 'lucas-academy-media'
os.environ['TOKENIZERS_PARALLELISM'] = 'false'
sys.path.insert(0, '/private/tmp/raindrop-mlx-20261119')
sys.path.insert(0, str(MEDIA / 'src'))

spec = importlib.util.spec_from_file_location('raindrop_accelerator', '/private/tmp/raindrop_generate_accelerated_20261119.py')
accelerator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(accelerator)
from lucas_media.cosyvoice_engine import CosyVoiceEngine, ASSISTANT_PREFIX


def units(engine, line):
    frontend = engine.model.frontend
    prompt = ASSISTANT_PREFIX + engine.profile.reference_text
    speaker = 'fangfang-mandarin'
    if speaker not in frontend.spk2info:
        engine.model.add_zero_shot_spk(prompt, str(engine.reference_audio), speaker)
    chunks = frontend.text_normalize(line['text'], split=True)
    for index, chunk in enumerate(chunks):
        inputs = frontend.frontend_zero_shot(chunk, prompt, str(engine.reference_audio), 24000, speaker)
        target = inputs['text'].flatten().tolist()
        prior = inputs['prompt_text'].flatten().tolist()
        speech_prior = inputs['llm_prompt_speech_token'].flatten().tolist()
        assert 151646 in prior + target
        seed = int.from_bytes(hashlib.blake2s(f"{speaker}/{line['id']}/{index}".encode(), digest_size=4).digest(), 'little')
        request = dict(text_tokens=prior + target, prompt_speech_tokens=speech_prior,
                       seed=seed, min_len=len(target) * 2, max_len=len(target) * 20)
        yield request, inputs, float(line['speed']), line['id'], index, len(chunks)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--only', default='')
    parser.add_argument('--force', action='store_true')
    args = parser.parse_args()
    script = json.loads((P / 'voices/fangfang-mandarin.json').read_text())
    output = P / 'voices/fangfang-mandarin'
    output.mkdir(exist_ok=True)
    wanted = set(args.only.split(',')) if args.only else None
    lines = [line for line in script['lines'] if
             (not wanted or line['id'] in wanted) and
             (args.force or not (output / (line['id'] + '.wav')).is_file())]
    print(f'Generating {len(lines)} Fangfang Mandarin paragraphs at 1.2x', flush=True)
    if not lines:
        return
    llm = accelerator.module.SpeechLM(str(accelerator.MODEL_DIR))
    accelerator.nn.quantize(llm.backbone, group_size=64, bits=8,
                           class_predicate=lambda path, layer: isinstance(layer, accelerator.nn.Linear))
    engine = CosyVoiceEngine('fangfang/zh')
    accelerator.enable_mps_flow(engine.model.model)
    batch, collected = [], defaultdict(dict)
    for line in lines:
        for item in units(engine, line):
            batch.append(item)
            if len(batch) == 4:
                accelerator.generate_batch(engine, llm, batch, collected, 'fangfang-mandarin', output)
                batch = []
    if batch:
        accelerator.generate_batch(engine, llm, batch, collected, 'fangfang-mandarin', output)
    assert not collected
    assert all((output / (line['id'] + '.wav')).is_file() for line in lines)
    print('Mandarin narration files verified', flush=True)


if __name__ == '__main__':
    main()
