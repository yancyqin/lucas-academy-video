"""Finish local narration if needed, then assemble and verify both versions."""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import subprocess
import sys
import time

P = Path(__file__).resolve().parent
MEDIA = P.parents[3] / 'lucas-academy-media'
HOME = Path.home()
SYNTH = MEDIA / '.conda/bin/python'
RENDER = HOME / '.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3'
FF = '/opt/homebrew/bin/ffmpeg'
PROBE = '/opt/homebrew/bin/ffprobe'
PROFILES = [('louise', 'louise/en', '1.1'), ('fangfang', 'fangfang/zh', '1.2')]


def wait_for_synthesis(pid):
    while True:
        result = subprocess.run(['ps', '-p', str(pid), '-o', 'args='], capture_output=True, text=True)
        if 'raindrop_generate_accelerated_20261119.py --mps-flow' not in result.stdout:
            return
        time.sleep(10)


def complete_voice(profile):
    name, reference, speed = profile
    lines = json.loads((P / 'voices' / (name + '.json')).read_text())['lines']
    missing = [line['id'] for line in lines if not (P / 'voices' / name / (line['id'] + '.wav')).is_file()]
    if missing:
        print(f'Recovering {len(missing)} {name} takes', flush=True)
        with (P / 'checks' / (name + '-recovery.log')).open('a') as log:
            subprocess.run([str(SYNTH), '-u', str(P / 'run_voice.py'), name, reference, speed, '3'],
                           stdout=log, stderr=subprocess.STDOUT, check=True)


def verify(plan):
    receipts = {}
    for name, version in plan['versions'].items():
        file = P / 'exports' / version['film']
        info = json.loads(subprocess.check_output([PROBE, '-v', 'error', '-show_streams',
                                                   '-of', 'json', str(file)]))
        video, audio, captions = info['streams']
        assert (video['width'], video['height'], video['r_frame_rate']) == (1920, 1080, '24/1')
        assert int(video['nb_frames']) == round(plan['duration'] * 24)
        assert audio['codec_name'] == 'aac' and int(audio['sample_rate']) == 48000
        assert captions['codec_name'] == 'mov_text'
        assert version['phrases'] == len(json.loads((P / 'voices' / (name + '.json')).read_text())['lines'])
        subprocess.run([FF, '-v', 'error', '-xerror', '-threads', '3', '-i', str(file),
                        '-map', '0:v:0', '-map', '0:a:0', '-f', 'null', '-'], check=True)
        receipts[name] = {**version, 'frames': int(video['nb_frames']), 'full_decode': 'passed'}
    (P / 'checks/delivery-qa.json').write_text(json.dumps(receipts, ensure_ascii=False, indent=2) + '\n')


if __name__ == '__main__':
    if len(sys.argv) == 2:
        wait_for_synthesis(int(sys.argv[1]))
    with ThreadPoolExecutor(max_workers=2) as workers:
        list(workers.map(complete_voice, PROFILES))
    subprocess.run([str(RENDER), str(P / 'timeline.py')], check=True)
    verify(json.loads((P / 'edit-plan.json').read_text()))
    print('Both English versions passed the delivery checks', flush=True)
