"""Export the revised English picture and a synchronized Mandarin dub."""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import shutil
import subprocess
import sys

import numpy as np

from timeline import FF, FPS, P, SR, decode, frame, make_mix, probe_duration, write_wav

PROBE = str(Path(FF).with_name('ffprobe'))
DEST = Path.home() / 'Desktop/压力焦虑肖邦浪漫-YouTube上传'
VIDEO = DEST / '01-压力焦虑肖邦浪漫-英文-Louise.mp4'
DUB = DEST / '02-压力焦虑肖邦浪漫-普通话-Fangfang.wav'
HASHTAGS = ('#chopin #romanticism #arthistory #art #classicalmusic #visualart #museum '
            '#artgallery #mononoaware #stressrelief #anxietyrelief\n'
            '#肖邦 #雨滴 #浪漫主义 #物哀')
YOUTUBE_TAGS = ', '.join(tag.removeprefix('#') for tag in HASHTAGS.split())


def audio_info(path):
    return json.loads(subprocess.check_output(
        [PROBE, '-v', 'error', '-show_streams', '-of', 'json', str(path)]
    ))['streams']


def mandarin_audio_plan(plan):
    scenes = [dict(scene) for scene in plan['scenes']]
    final_index = next(i for i, scene in enumerate(scenes) if scene['id'] == 'bonus-09')
    final_line, hold = scenes[final_index:final_index + 2]
    assert hold['id'] == 'bonus-hold' and not hold.get('text')
    # The last spoken line may settle into the existing silent picture hold.
    # Its extra breathing room does not move any later voice or video cue.
    final_line['end'] += 2
    final_line['seconds'] += 2
    hold['start'] += 2
    hold['seconds'] -= 2
    return {**plan, 'scenes': scenes}


def mandarin_takes(plan):
    plan = mandarin_audio_plan(plan)
    manifest = json.loads((P / 'voices/fangfang-mandarin.json').read_text())
    assert manifest['voice'] == 'fangfang/zh' and manifest['language'] == 'zh'
    by_id = {line['scene_id']: line for line in manifest['lines']}
    takes, adjustments = {}, {}
    for scene in plan['scenes']:
        if not scene.get('text'):
            continue
        identifier = scene['id']
        recorded = by_id[identifier]
        assert recorded['caption'] == scene['text_zh'], identifier
        path = P / 'voices/fangfang-mandarin' / (recorded['id'] + '.wav')
        samples = decode(path, 1)[:, 0]
        active = np.flatnonzero(np.abs(samples) > .002)
        assert len(active) > SR / 10, path
        first = max(0, active[0] - 3200)
        last = min(len(samples), active[-1] + 4800)
        samples = samples[first:last]
        budget = scene['seconds'] - .65
        speed = len(samples) / SR / budget
        if speed > 1:
            # Leave a little room for atempo's output rounding and for the breath after the line.
            speed *= 1.01
            assert speed <= 1.35, (identifier, 'Voice needs a slower retake or a revised scene budget', speed)
            output = subprocess.check_output([FF, '-v', 'error', '-f', 'f32le',
                                               '-ar', str(SR), '-ac', '1', '-i', 'pipe:0',
                                               '-af', f'atempo={speed:.8f}', '-f', 'f32le', '-'],
                                              input=samples.astype('<f4').tobytes())
            samples = np.frombuffer(output, dtype='<f4')
            adjustments[identifier] = round(speed, 4)
        assert len(samples) > SR / 3 and len(samples) / SR <= scene['seconds'] - .4, identifier
        takes[identifier] = [(recorded['caption'], samples)]
    assert set(takes) == set(by_id)
    return takes, adjustments, 'Fangfang, Mandarin Chinese, CosyVoice3 zero-shot, synthesis speed 1.2'


def export_dub(plan):
    takes, adjustments, original_voice = mandarin_takes(plan)
    mix, captions, receipt = make_mix(mandarin_audio_plan(plan), takes)
    temp = DUB.with_suffix('.partial.wav')
    write_wav(temp, mix)
    (track,) = audio_info(temp)
    assert track['codec_name'] == 'pcm_s16le' and track['channels'] == 2
    assert track['sample_rate'] == str(SR)
    assert int(track['duration_ts']) == frame(plan['duration']) * (SR // FPS)
    temp.replace(DUB)
    receipt.update(voice=original_voice, profile='fangfang/zh', language='zh', synthesis_speed=1.2,
                   paragraphs=len(captions), adjusted_speeds=adjustments,
                   final_line_hold_allowance=2, audio_samples=int(track['duration_ts']))
    (P / 'checks/youtube-mandarin-qa.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print('Exported', DUB, flush=True)


def encoded_audio_hash(file):
    return subprocess.check_output([FF, '-v', 'error', '-i', str(file), '-map', '0:a:0',
                                    '-c', 'copy', '-f', 'streamhash', '-hash', 'sha256', '-'])


def refresh_english(plan):
    sample = json.loads((P / 'sample-edit-plan.json').read_text())
    fields = ('id', 'old_first', 'old_count', 'first', 'count')
    for scene, preview in zip(plan['scenes'], sample['scenes'], strict=True):
        assert all(scene[field] == preview[field] for field in fields), scene['id']
        if scene['end'] >= 18:
            break
    else:
        raise ValueError('The opening eighteen-second block is missing')

    opening = P / 'parts/sample-labeled/00000.mp4'
    block = P / 'parts/labeled/00000.mp4'
    assert frame(probe_duration(opening)) == frame(probe_duration(block)) == 432
    staged = block.with_suffix('.incoming.mp4')
    shutil.copyfile(opening, staged)
    staged.replace(block)

    def refresh(item):
        name, version = item
        film = P / 'exports' / version['film']
        manifest = film.with_suffix('.concat.txt')
        assert manifest.read_text().splitlines()[0] == f"file '{block}'"
        temp = film.with_suffix('.youtube.mp4')
        subprocess.run([FF, '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', str(manifest),
                        '-i', str(film), '-map', '0:v:0', '-map', '1:a:0', '-map_metadata', '1',
                        '-metadata:s:a:0', 'language=eng', '-c', 'copy', '-movflags', '+faststart',
                        str(temp)], check=True)
        video, audio = audio_info(temp)
        assert (video['codec_name'], video['width'], video['height'], video['r_frame_rate']) == (
            'h264', 1920, 1080, '24/1')
        assert audio['codec_type'] == 'audio' and audio['codec_name'] == 'aac'
        assert int(video['nb_frames']) == frame(plan['duration'])
        assert frame(probe_duration(temp)) == frame(plan['duration'])
        assert encoded_audio_hash(temp) == encoded_audio_hash(film), name
        subprocess.run([FF, '-v', 'error', '-xerror', '-threads', '2', '-i', str(temp),
                        '-t', '21', '-map', '0:v:0', '-map', '0:a:0', '-f', 'null', '-'], check=True)
        temp.replace(film)
        return name, film

    with ThreadPoolExecutor(max_workers=2) as pool:
        movies = dict(pool.map(refresh, plan['versions'].items()))
    temp = VIDEO.with_suffix('.partial.mp4')
    shutil.copyfile(movies['louise'], temp)
    temp.replace(VIDEO)
    print('Exported', VIDEO, flush=True)


def write_description(plan):
    assets = json.loads((P / 'sources-and-credits.json').read_text())
    lines = [
        'Pressure? Anxiety? Chopin? Romanticism?',
        '',
        'A walk through the Romantic Salon with Chopin, Goya, Géricault, Delacroix, Wright of Derby, Friedrich, and Turner. The film ends with a coda on mono no aware.',
        '',
        'Created together by Yancy & Eunice',
        '',
        'Chapters',
    ]
    for section, title in (
        ('intro', 'From Gallery to Space'), ('chopin', 'Chopin and the Raindrop Prelude'),
        ('history', 'Revolution and upheaval'), ('goya', 'War and revolution in painting'),
        ('wright', 'Nature and the sublime'), ('themes', 'Feeling, nature, time, and human finitude'),
        ('bonus', 'Coda · Mono no aware'),
    ):
        start = int(next(scene['start'] for scene in plan['scenes'] if scene['section'] == section))
        minutes, seconds = divmod(start, 60)
        lines.append(f'{minutes}:{seconds:02d} {title}')
    lines.extend(['', 'Music · Frédéric Chopin'])
    recordings = {
        'nocturne-9-2': 'Nocturne in E-flat major, Op. 9 No. 2 · Frank Levy',
        'nocturne-c-sharp': 'Nocturne in C-sharp minor, B. 49 · Frank Levy',
        'prelude-28-15': 'Raindrop Prelude in D-flat major, Op. 28 No. 15 · Jeannette Fang',
    }
    for track in assets['music']:
        lines.append(f"{recordings[track['id']]} · Musopen · {track['license']}")
        lines.append(track['source'])
    lines.extend(['', 'Photographs and footage'])
    photograph = assets['photograph']
    lines.append(f"Seirai-in, Kyoto · {photograph['artist']} · {photograph['license']}")
    lines.extend([photograph['source'], photograph['license_url']])
    gallery = assets['opening_gallery']['reference']
    lines.append(f"Opening gallery reference · {gallery['creator']} · {gallery['source']}")
    for clip in assets['live_action']:
        lines.append(f"Falling cherry blossoms · {clip['author']} · {clip['source']}")
    lines.extend(['', '3D sculpture scans · CC BY 4.0', 'https://creativecommons.org/licenses/by/4.0/'])
    for scan in assets['scans']:
        if scan['license'] == 'CC BY 4.0':
            lines.append(f"{scan['title_en']} · {scan['model_credit']} · {scan['model_source']}")
    lines.append('Scans were scaled, positioned, and rendered in the Romantic Salon.')
    lines.extend([
        '',
        HASHTAGS,
        '',
        'YouTube Tags',
        YOUTUBE_TAGS,
    ])
    (DEST / '03-YouTube简介与素材署名.txt').write_text('\n'.join(lines) + '\n')


if __name__ == '__main__':
    DEST.mkdir(exist_ok=True)
    plan = json.loads((P / 'edit-plan.json').read_text())
    if '--mandarin' in sys.argv:
        export_dub(plan)
    else:
        refresh_english(plan)
        write_description(plan)
