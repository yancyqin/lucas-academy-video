"""Owner-authorized Fangfang cloning and short bilingual MiniMax auditions."""
from datetime import datetime, timezone
import hashlib
import json
import netrc
from pathlib import Path
import sys
import urllib.request
import uuid

P = Path(__file__).resolve().parent
OUT = P / 'auditions/2026-11-20-fangfang-minimax'
PROFILE = P.parents[3] / 'lucas-academy-media/profiles/fangfang/zh/profile.json'
BASE = 'https://api.minimax.cn'
MODEL = 'speech-2.8-hd'


def key():
    return netrc.netrc(str(Path.home() / '.netrc')).authenticators('api.minimaxi.com')[2]


def post(path, body, content_type='application/json'):
    raw = json.dumps(body).encode() if isinstance(body, dict) else body
    request = urllib.request.Request(BASE + path, data=raw,
        headers={'Authorization': 'Bearer ' + key(), 'Content-Type': content_type})
    with urllib.request.urlopen(request, timeout=150) as response:
        result = json.load(response)
    return result


def guarded_call(folder, path, body, content_type='application/json', metadata=None):
    folder.mkdir(parents=True, exist_ok=True)
    receipt = folder / 'receipt.json'
    if receipt.exists():
        previous = json.loads(receipt.read_text())
        if previous.get('state') == 'success':
            return previous['response']
        raise RuntimeError(f'{folder.name} has a previous submission; inspect its receipt before retrying')
    (folder / 'request.json').write_text(json.dumps(
        dict(endpoint=BASE + path, body=body if isinstance(body, dict) else metadata), ensure_ascii=False, indent=2))
    receipt.write_text(json.dumps(dict(state='sending', at=datetime.now(timezone.utc).isoformat())))
    try:
        result = post(path, body, content_type)
    except Exception as error:
        receipt.write_text(json.dumps(dict(state='unknown', error=str(error)[:250]), ensure_ascii=False, indent=2))
        raise
    ok = result.get('base_resp', {}).get('status_code') == 0
    # Binary/hex audio never goes into a receipt or tool output.
    safe = {k: v for k, v in result.items() if k != 'data'}
    if 'data' in result:
        safe['data'] = {k: v for k, v in result['data'].items() if k != 'audio'}
        if ok and result['data'].get('audio'):
            raw = bytes.fromhex(result['data']['audio'])
            assert len(raw) > 5000
            (folder / 'original.mp3').write_bytes(raw)
    receipt.write_text(json.dumps(dict(state='success' if ok else 'rejected', response=safe),
                                 ensure_ascii=False, indent=2))
    if not ok:
        raise RuntimeError(f"{folder.name}: {result.get('base_resp')}")
    return safe


def upload_reference(reference):
    boundary = 'CodexVoiceBoundary' + uuid.uuid4().hex
    raw = reference.read_bytes()
    payload = (
        f'--{boundary}\r\nContent-Disposition: form-data; name="purpose"\r\n\r\nvoice_clone\r\n'
        f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="fangfang-reference.wav"\r\n'
        'Content-Type: audio/wav\r\n\r\n'
    ).encode() + raw + f'\r\n--{boundary}--\r\n'.encode()
    result = guarded_call(OUT / 'reference-upload', '/v1/files/upload', payload,
                          f'multipart/form-data; boundary={boundary}',
                          metadata=dict(purpose='voice_clone', source=str(reference), bytes=len(raw),
                                        sha256=hashlib.sha256(raw).hexdigest()))
    return int(result['file']['file_id'])


def clone():
    profile = json.loads(PROFILE.read_text())
    reference = PROFILE.parent / profile['reference_audio']
    assert reference.is_file() and profile['reference_language'] == 'zh'
    assert profile.get('consent')
    reference_hash = hashlib.sha256(reference.read_bytes()).hexdigest()
    voice_id = 'LucasFangfangRomantic20261120_' + reference_hash[:8]
    file_id = upload_reference(reference)
    body = dict(file_id=file_id, voice_id=voice_id,
                text_validation=profile['reference_text'], accuracy=.7,
                need_noise_reduction=False, need_volume_normalization=False)
    guarded_call(OUT / 'voice-clone', '/v1/voice_clone', body)
    manifest = dict(provider='MiniMax', voice_id=voice_id, speaker='Fangfang',
                    source_profile=str(PROFILE), reference_sha256=reference_hash,
                    model=MODEL, file_id=file_id)
    (P / 'voices/minimax-fangfang.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    print('Fangfang voice clone created and recorded', flush=True)
    return voice_id


def scripts():
    scenes = {s['id']: s for s in json.loads((P / 'edit-plan.json').read_text())['scenes']}
    zh = scenes['p010']['text_zh'].strip() + '\n\n' + scenes['p011']['text_zh'].strip()
    en = scenes['p010']['text'].strip() + '\n\n' + scenes['p011']['text'].strip()
    # Preserve wording and shape only the pauses around the quoted outburst.
    zh_spoken = zh.replace('说：“啊', '说：<#0.35#>“啊').replace('死了！”，随后', '死了！”<#0.65#>随后')
    en_spoken = en.replace('he cried out: Ah,', 'he cried out:<#0.35#> Ah,')
    en_spoken = en_spoken.replace('You were dead! Then', 'You were dead!<#0.65#> Then')
    return dict(zh=dict(caption=zh, spoken=zh_spoken), en=dict(caption=en, spoken=en_spoken))


def speech(name, voice, language, text):
    body = dict(model=MODEL, text=text['spoken'], stream=False, output_format='hex',
                language_boost='Chinese' if language == 'zh' else 'English',
                voice_setting=dict(voice_id=voice, speed=1.0, vol=1.0, pitch=0),
                audio_setting=dict(sample_rate=32000, bitrate=128000, format='mp3', channel=1))
    result = guarded_call(OUT / name, '/v1/t2a_v2', body)
    audio = OUT / name / 'original.mp3'
    assert audio.exists()
    (OUT / name / 'text.json').write_text(json.dumps(text, ensure_ascii=False, indent=2))
    print(name, result.get('extra_info'), flush=True)


def main():
    OUT.mkdir(exist_ok=True)
    voice = clone()
    text = scripts()
    speech('fangfang-zh', voice, 'zh', text['zh'])
    speech('fangfang-en', voice, 'en', text['en'])
    speech('english-natural', 'English_captivating_female1', 'en', text['en'])
    print('Short bilingual auditions generated; full film untouched', flush=True)


if __name__ == '__main__':
    main()
