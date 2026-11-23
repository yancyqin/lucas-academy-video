"""Short English audition: MiniMax performance, local Louise timbre conversion."""
import hashlib
import json
from pathlib import Path
import subprocess
import time

from fangfang_voice_conversion_trial import enable_mps_flow, torch, CosyVoiceEngine
from lucas_media.joke import add_peak_headroom, save_wav
from finish_auditions import normalize

P = Path(__file__).resolve().parent
SOURCE = P / 'auditions/2026-11-20-fangfang-minimax'
OUT = SOURCE / 'minimax-louise-en-vc'
DEST = Path('@USER_HOME@/Desktop/肖邦配音试听-2026-11-20')


def main():
    OUT.mkdir(exist_ok=True)
    target = OUT / 'original.wav'
    source = OUT / 'source.wav'
    if not target.is_file():
        subprocess.run(['/opt/homebrew/bin/ffmpeg', '-v', 'error', '-y', '-i',
                        str(SOURCE/'english-natural/original.mp3'), '-t', '23.7',
                        '-ar', '16000', '-ac', '1', str(source)], check=True)
        engine = CosyVoiceEngine('louise/en')
        enable_mps_flow(engine.model.model)
        started = time.monotonic()
        with torch.inference_mode():
            chunks = [item['tts_speech'].cpu() for item in engine.model.inference_vc(
                str(source), str(engine.reference_audio), stream=False, speed=1.0)]
        speech = torch.cat(chunks, dim=1)
        assert torch.isfinite(speech).all() and speech.shape[1] > 20 * engine.model.sample_rate
        save_wav(target, add_peak_headroom(speech), engine.model.sample_rate)
        metadata = dict(method='MiniMax Speech 2.8 HD performance + local CosyVoice3 voice conversion',
                        native_minimax_clone=False, target_profile='louise/en',
                        reference=str(engine.reference_audio),
                        seconds=speech.shape[1]/engine.model.sample_rate,
                        conversion_seconds=round(time.monotonic()-started, 2),
                        sha256=hashlib.sha256(target.read_bytes()).hexdigest())
        (OUT/'receipt.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2))
    delivery = DEST/'10-MiniMax演绎-Louise英文换声.mp3'
    metadata = normalize(target, delivery)
    (OUT/'delivery.json').write_text(json.dumps(dict(file=str(delivery), **metadata), ensure_ascii=False, indent=2))
    print(json.dumps(dict(file=str(delivery), **metadata), ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
