"""Small owner-requested voice auditions; preserve requests and avoid duplicate synthesis."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import netrc
from pathlib import Path
import urllib.request

P = Path(__file__).resolve().parent
OUT = P / 'auditions/2026-11-20-emotion'
OUT.mkdir(parents=True, exist_ok=True)
SCENES = json.loads((P / 'edit-plan.json').read_text())['scenes']
TEXT = '\n\n'.join(next(s['text_zh'] for s in SCENES if s['id'] == key).strip()
                   for key in ['p010', 'p011'])
CASES = {
    'minimax-auto': dict(voice_id='Chinese (Mandarin)_Wise_Women', label='MiniMax 2.8 HD 阅历女声 自然叙事'),
    'minimax-sad': dict(voice_id='Chinese (Mandarin)_Wise_Women', emotion='sad', label='MiniMax 2.8 HD 阅历女声 悲伤演绎'),
    'minimax-male': dict(voice_id='Chinese (Mandarin)_Gentleman', label='MiniMax 2.8 HD 温润男声 自然叙事'),
}


def synth(name, retry_rejected=False):
    case = CASES[name]
    folder = OUT / name
    folder.mkdir(exist_ok=True)
    receipt = folder / 'receipt.json'
    audio = folder / 'original.mp3'
    if receipt.exists():
        previous = json.loads(receipt.read_text())
        if previous.get('state') == 'success' and audio.exists():
            print('Already generated', name, flush=True)
            return
        if retry_rejected and previous.get('state') == 'rejected' and previous.get('base_resp', {}).get('status_code') == 2013:
            receipt.replace(folder / 'receipt-invalid-parameters.json')
            (folder / 'request.json').replace(folder / 'request-invalid-parameters.json')
        else:
            raise RuntimeError(f'{name} has a previous submission; inspect its receipt before submitting again')
    settings = dict(voice_id=case['voice_id'], speed=1.0, vol=1.0, pitch=0)
    if 'emotion' in case:
        settings['emotion'] = case['emotion']
    body = dict(model='speech-2.8-hd', text=TEXT, stream=False, output_format='hex',
                voice_setting=settings, language_boost='Chinese',
                audio_setting=dict(sample_rate=32000, bitrate=128000, format='mp3', channel=1))
    (folder / 'request.json').write_text(json.dumps(body, ensure_ascii=False, indent=2))
    receipt.write_text(json.dumps(dict(state='sending', model=body['model'], case=name,
                                      source_scene_ids=['p010', 'p011'], characters=len(TEXT),
                                      at=datetime.now(timezone.utc).isoformat()), ensure_ascii=False, indent=2))
    key = netrc.netrc(str(Path.home() / '.netrc')).authenticators('api.minimaxi.com')[2]
    request = urllib.request.Request('https://api.minimax.cn/v1/t2a_v2',
                                    data=json.dumps(body).encode(),
                                    headers={'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            result = json.load(response)
    except Exception as error:
        receipt.write_text(json.dumps(dict(state='unknown', error=str(error)[:250]), ensure_ascii=False, indent=2))
        raise
    metadata = {key: value for key, value in result.items() if key != 'data'}
    if result.get('base_resp', {}).get('status_code') != 0:
        receipt.write_text(json.dumps(dict(state='rejected', **metadata), ensure_ascii=False, indent=2))
        raise RuntimeError(str(result.get('base_resp')))
    raw = bytes.fromhex(result['data']['audio'])
    assert len(raw) > 5000
    temp = audio.with_suffix('.incoming.mp3')
    temp.write_bytes(raw)
    temp.replace(audio)
    receipt.write_text(json.dumps(dict(state='success', case=name, label=case['label'],
                                      model=body['model'], voice_setting=settings,
                                      sha256=hashlib.sha256(raw).hexdigest(), **metadata),
                                 ensure_ascii=False, indent=2))
    print('Generated', name, result.get('extra_info'), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('case', choices=list(CASES))
    parser.add_argument('--retry-rejected', action='store_true')
    args = parser.parse_args()
    synth(args.case, args.retry_rejected)
