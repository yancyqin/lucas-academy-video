"""Assemble each complete language and perform a local transcription check."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

P=Path(__file__).resolve().parent


def main():
    pending={'zh','en'};started=time.monotonic();checks=P/'checks/final-audio';checks.mkdir(exist_ok=True)
    while pending:
        if time.monotonic()-started>2700:raise TimeoutError('Conversion still unfinished; preserve cached files.')
        ready=[lang for lang in sorted(pending) if (P/f'voice-manifest-{lang}.json').is_file()]
        if not ready:
            time.sleep(3);continue
        subprocess.run([sys.executable,str(P/'assemble_narration.py'),'--ready-only'],check=True)
        delivery=json.loads((P/'narration-delivery.json').read_text())
        for lang in ready:
            track=next(t for t in delivery['tracks'] if t['language']==lang)
            wav=Path(track['wav']);prefix=checks/f'narration-{lang}'
            subprocess.run(['/opt/homebrew/bin/ffmpeg','-v','error','-y','-i',str(wav),'-ar','16000','-ac','1',str(prefix.with_suffix('.wav'))],check=True)
            with (checks/f'asr-{lang}.log').open('w') as log:
                subprocess.run(['/opt/homebrew/bin/whisper-cli','-m','@USER_HOME@/.cache/whisper/ggml-small-q5_1.bin',
                    '-f',str(prefix.with_suffix('.wav')),'-l',lang,'-t','2','-otxt','-oj','-of',str(prefix),'-np'],
                    stdout=log,stderr=log,check=True)
            assert prefix.with_suffix('.txt').is_file() and prefix.with_suffix('.txt').stat().st_size>1000
            (checks/f'completed-{lang}.json').write_text(json.dumps(dict(language=lang,file=str(wav),
                audio_sha256=hashlib.sha256(wav.read_bytes()).hexdigest(),asr=str(prefix.with_suffix('.txt'))),indent=2))
            pending.remove(lang);print('Local transcription complete:',lang,flush=True)
    plan=json.loads((P/'synthesis-plan.json').read_text())
    combined=[]
    for lang in ['zh','en']:
        manifest=json.loads((P/f'voice-manifest-{lang}.json').read_text())
        assert manifest['source_sha256']==plan['source_sha256']
        combined.extend(manifest['items'])
    assert len(combined)==len(plan['requests'])
    (P/'voice-manifest.json').write_text(json.dumps(dict(source_sha256=plan['source_sha256'],
        target_voices=plan['target_voices'],items=combined),ensure_ascii=False,indent=2))
    subprocess.run([sys.executable,str(P/'assemble_narration.py')],check=True)
    print('Both full narration previews and local transcriptions are ready for final review.',flush=True)


if __name__=='__main__':main()
