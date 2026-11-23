"""Short provider auditions using owner-authorized keys; no full narration."""
from datetime import datetime, timezone
import hashlib
import json
import netrc
from pathlib import Path
import re
import sys
import time

import msgpack
import requests

from finish_auditions import normalize

P = Path(__file__).resolve().parent
MEDIA = P.parents[3]/'lucas-academy-media'
OUT = P/'auditions/2026-11-20-alternative-providers'
DEST = Path('@USER_HOME@/Desktop/肖邦配音试听-2026-11-20')


def texts():
    scenes = {x['id']: x for x in json.loads((P/'edit-plan.json').read_text())['scenes']}
    return dict(
        en=scenes['p010']['text'].strip()+'\n\n'+scenes['p011']['text'].split(' Then he told her')[0].strip(),
        zh=scenes['p010']['text_zh'].strip()+'\n\n肖邦看到她时惊呼了一声，说：“啊，我就知道，你们已经死了！”')


def generate(provider, language):
    identifier = f'{provider}-{language}'
    folder = OUT/identifier
    folder.mkdir(parents=True, exist_ok=True)
    receipt_file = folder/'receipt.json'
    if receipt_file.exists():
        old = json.loads(receipt_file.read_text())
        print(identifier, 'existing submission state', old['state'], flush=True)
        return
    text = texts()[language]
    secrets = netrc.netrc(str(Path.home()/'.netrc'))
    if provider == 'eleven-v4':
        secret = secrets.authenticators('api.elevenlabs.io')[2]
        voice = 'EXAVITQu4vr4xnSDxMaL'  # Sarah, confirmed available on this account.
        endpoint = 'https://api.elevenlabs.io/v1/text-to-speech/'+voice
        request = dict(text=text, model_id='eleven_v4', language_code=language,
                       voice_settings=dict(stability=.5, similarity_boost=.75))
        payload = json.dumps(request).encode()
        headers = {'xi-api-key':secret, 'Content-Type':'application/json'}
        metadata = dict(endpoint=endpoint, body=request, voice_name='Sarah', short_audition=True)
        filename = '11-ElevenV4-英文自然叙事.mp3'
    else:
        assert provider == 'fish-s2.1-free'
        secret = secrets.authenticators('api.fish.audio')[2]
        profile_name = 'fangfang/zh' if language == 'zh' else 'louise/en'
        profile_path = MEDIA/'profiles'/profile_name/'profile.json'
        profile = json.loads(profile_path.read_text())
        assert profile.get('consent')
        reference = profile_path.parent/profile['reference_audio']
        endpoint = 'https://api.fish.audio/v1/tts'
        body = dict(text=text, format='mp3', sample_rate=44100, mp3_bitrate=128,
                    latency='normal', chunk_length=300, normalize=True,
                    temperature=.7, top_p=.7, language='zh-CN' if language=='zh' else 'en',
                    prosody=dict(speed=1, volume=0),
                    references=[dict(audio=reference.read_bytes(), text=profile['reference_text'])])
        payload = msgpack.packb(body, use_bin_type=True)
        # Explicit free-model header: never fall back to the paid default.
        headers = {'Authorization':'Bearer '+secret, 'Content-Type':'application/msgpack',
                   'model':'s2.1-pro-free'}
        metadata = dict(endpoint=endpoint, model='s2.1-pro-free', short_audition=True,
                        text=text, voice_reference=profile_name,
                        reference_sha256=hashlib.sha256(reference.read_bytes()).hexdigest(),
                        reference_handling='Inline conditioning; no public voice model created')
        filename = '12-FishS2.1免费版-Fangfang中文.mp3' if language=='zh' else '13-FishS2.1免费版-Louise英文.mp3'
    (folder/'request.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2))
    receipt_file.write_text(json.dumps(dict(state='sending', at=datetime.now(timezone.utc).isoformat())))
    print('Generating', identifier, 'text chars',len(text),flush=True)
    started = time.monotonic()
    try:
        # API keys use explicit headers. Disable requests' automatic .netrc
        # Basic-auth injection, which otherwise overrides Fish's Bearer header
        # and adds a conflicting second credential to ElevenLabs requests.
        session = requests.Session()
        session.trust_env = False
        response = session.post(endpoint, headers=headers, data=payload, timeout=(20,180))
        content_type = response.headers.get('Content-Type','')
        if response.status_code != 200 or 'json' in content_type:
            try:error = response.json()
            except Exception:error = dict(message=response.text[:500])
            safe = json.loads(json.dumps(error).replace(secret,'[redacted]'))
            receipt = dict(state='rejected', http_status=response.status_code, error=safe)
            receipt_file.write_text(json.dumps(receipt,ensure_ascii=False,indent=2))
            print(identifier, 'rejected', response.status_code, str(safe)[:400],flush=True)
            return
        assert len(response.content)>5000
        audio = folder/'original.mp3'
        audio.write_bytes(response.content)
        receipt = dict(state='success', http_status=200, content_type=content_type,
                       bytes=len(response.content), seconds_elapsed=round(time.monotonic()-started,2),
                       model=metadata.get('model',request['model_id'] if provider=='eleven-v4' else None),
                       sha256=hashlib.sha256(response.content).hexdigest())
        receipt_file.write_text(json.dumps(receipt,ensure_ascii=False,indent=2))
        delivery = normalize(audio,DEST/filename)
        (folder/'delivery.json').write_text(json.dumps(dict(file=str(DEST/filename),**delivery),ensure_ascii=False,indent=2))
        print(identifier,'success',delivery['duration'],'seconds',flush=True)
    except Exception as e:
        previous=json.loads(receipt_file.read_text())
        if previous.get('state') != 'success':
            receipt_file.write_text(json.dumps(dict(state='unknown', error=str(e).replace(secret,'[redacted]')[:350]),indent=2))
        print(identifier,'error',str(e).replace(secret,'[redacted]')[:250],flush=True)


if __name__ == '__main__':
    DEST.mkdir(exist_ok=True)
    generate('eleven-v4','en')
    generate('fish-s2.1-free','zh')
    generate('fish-s2.1-free','en')
