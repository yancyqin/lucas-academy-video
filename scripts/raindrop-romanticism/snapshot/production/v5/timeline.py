"""Keep picture, narration, music, and on-screen labels on the same frame clock."""
from collections import defaultdict
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import json
import subprocess
import sys
import wave

import numpy as np
from picture import P, V4, FF, FPS, MUSE_GALLERY, frame, probe_duration, inserts
from finish_walk import ART_LABELS, PLAN, CUTS, Take, burn_labels, write_overlays

MUSIC = P.parents[2] / 'romanticism-music-gallery/music'
SR = 48000
VOICE_PROFILES = {'louise': 'Louise 1.1×', 'fangfang': 'Fangfang 1.2×'}
VIDEO_PATH = P / 'parts/clean-picture.mp4'
PARTS = P / 'parts'
EXPORTS = P / 'exports'


def decode(path, channels):
    output = subprocess.check_output([FF, '-v', 'error', '-i', str(path), '-ar', str(SR),
                                      '-ac', str(channels), '-f', 'f32le', '-'])
    return np.frombuffer(output, dtype='<f4').reshape(-1, channels).copy()


def write_wav(path, audio):
    with wave.open(str(path), 'wb') as file:
        file.setparams((2, audio.shape[1], SR, 0, 'NONE', 'not compressed'))
        file.writeframes(np.round(audio * 32767).astype('<i2').tobytes())


def read_takes(name, selected=None):
    lines = json.loads((P / 'voices' / f'{name}.json').read_text())['lines']
    by_scene = defaultdict(list)
    for line in lines:
        if selected is not None and line['scene_id'] not in selected:
            continue
        source = P / 'voices' / name / (line['id'] + '.wav')
        samples = decode(source, 1)[:, 0]
        assert len(samples) > SR / 3, source
        active = np.flatnonzero(np.abs(samples) > .002)
        assert len(active) > SR / 10, source
        # Trim excessive padding without clipping quiet consonants or breathing.
        samples = samples[max(0, active[0] - 3200):min(len(samples), active[-1] + 4800)]
        by_scene[line['scene_id']].append((line['caption'], samples))
    for scene in PLAN['scenes']:
        if scene.get('text') and (selected is None or scene['id'] in selected):
            assert ' '.join(text for text, _ in by_scene[scene['id']]).split() == scene['text'].split(), scene['id']
    return by_scene


def timeline(takes):
    new_scenes = []
    cursor = 0
    old_scenes = []
    old_cursor = 0
    for scene in PLAN['scenes']:
        if frame(scene['start']) > old_cursor:
            old_scenes.append({'id': 'salon-coda', 'section': 'gallery',
                               'start': old_cursor / FPS, 'end': scene['start']})
        old_scenes.append(scene)
        old_cursor = frame(scene['end'])
    for scene in old_scenes:
        old_first, old_last = frame(scene['start']), frame(scene['end'])
        old_count = old_last - old_first
        minimum = old_count
        if scene.get('text') and takes and scene['id'] in next(iter(takes.values())):
            longest = max(sum(len(phrase) for _, phrase in voice[scene['id']]) / SR
                          + .22 * (len(voice[scene['id']]) - 1) for voice in takes.values())
            minimum = max(minimum, int(np.ceil((longest + .75) * FPS)))
        new_scenes.append({**scene, 'start': cursor / FPS, 'end': (cursor + minimum) / FPS,
                           'seconds': minimum / FPS, 'old_first': old_first, 'old_count': old_count,
                           'first': cursor, 'count': minimum})
        cursor += minimum
    return {'duration': cursor / FPS, 'scenes': new_scenes}


def map_frame(index, scenes):
    for scene in scenes:
        if index <= scene['old_first'] + scene['old_count']:
            return scene['first'] + round((index - scene['old_first']) * scene['count'] / scene['old_count'])
    raise ValueError(index)


def shot_annotations(plan):
    def timed(take, first, last, section):
        start = map_frame(frame(first), plan['scenes'])
        end = map_frame(frame(last), plan['scenes'])
        return take, start, end - start, section

    return ([timed(Take('salon', name, art=name), start, end, 'painting')
             for name, start, end in ART_LABELS] +
            [timed(Take(item.kind, item.name), item.start, item.end, 'interlude') for item in inserts()])


def make_mix(plan, voice):
    count = frame(plan['duration']) * (SR // FPS)
    speech = np.zeros(count, np.float32)
    duck = np.ones(count, np.float32)
    captions = []
    for scene in plan['scenes']:
        takes = voice.get(scene['id'], ())
        cursor = round((scene['start'] + .25) * SR)
        for text, samples in takes:
            last = cursor + len(samples)
            assert last <= round(scene['end'] * SR), scene['id']
            speech[cursor:last] = samples
            captions.append((cursor / SR, last / SR, text))
            start_attack = max(0, cursor - 12000)
            end_attack = max(0, cursor - 3600)
            start_release = min(count, last + 4600)
            end_release = min(count, last + 15700)
            before = slice(start_attack, end_attack)
            after = slice(start_release, end_release)
            duck[before] = np.minimum(duck[before], np.linspace(1, .29, end_attack - start_attack))
            duck[end_attack:start_release] = .29
            duck[after] = np.minimum(duck[after], np.linspace(.29, 1, end_release - start_release))
            cursor = last + round(.22 * SR)
    active = speech[np.abs(speech) > .01]
    speech *= .128 / np.sqrt(np.mean(active**2))
    mix = np.repeat(speech[:, None], 2, axis=1)

    def edge(section, end=False):
        entries = [s for s in plan['scenes'] if s['section'] == section]
        return max(s['end'] for s in entries) if end else min(s['start'] for s in entries)

    reprise = next(s['start'] for s in plan['scenes'] if s['id'] == 'listen')
    credits = next(s['start'] for s in plan['scenes'] if s['id'] == 'credits')
    cues = [
        (0, reprise, 'prelude-28-15', 0, 0, .65, .70),
        (reprise, edge('history', True), 'prelude-28-15', 0, 0, 1.35, 1),
        (edge('goya'), edge('delacroix', True), 'nocturne-9-2', 0, 1.2, 1.4, 1),
        (edge('wright'), edge('wanderer', True), 'nocturne-c-sharp', 0, 1.2, 1.4, 1),
        (edge('turner'), edge('conclusion'), 'prelude-28-15', 72, 1.1, 1.35, 1),
        (edge('conclusion'), edge('bonus'), 'prelude-28-15', 257, 1.15, 1.6, 1),
        (edge('bonus') + .55, credits, 'nocturne-9-2', 150, 1.3, 2.15, 1),
    ]
    songs = {}
    for start, end, name, offset, attack, release, level in cues:
        if name not in songs:
            song = decode(MUSIC / (name + '.m4a'), 2)
            songs[name] = song * (.059 / np.sqrt(np.mean(song**2)))
        cursor = round(start * SR)
        length = round(end * SR) - cursor
        offset = round(offset * SR)
        chunk = songs[name][offset:offset + length].copy() * level
        if attack:
            ramp = round(attack * SR)
            chunk[:ramp] *= np.linspace(0, 1, ramp)[:, None]
        if release:
            ramp = round(release * SR)
            chunk[-ramp:] *= np.linspace(1, 0, ramp)[:, None]
        mix[cursor:cursor + len(chunk)] += chunk * duck[cursor:cursor + len(chunk), None]
    peak = float(np.max(np.abs(mix)))
    mix *= min(1, .92 / max(.001, peak))
    first = round(reprise * SR)
    clean = songs['prelude-28-15'][:10 * SR, 0]
    corr = float(np.corrcoef(mix[first:first + 10 * SR, 0], clean)[0, 1])
    assert corr > .9999 and np.all(duck[first:first + round(9.8 * SR)] == 1), corr
    return mix, captions, {'listen_start': reprise, 'listen_seconds': 10, 'reprise_correlation': corr,
                           'introduction_sample_offset': 0, 'reprise_sample_offset': 0,
                           'peak': float(np.max(np.abs(mix)))}


def video_slices(plan, ending=None):
    sections = []
    for scene in plan['scenes']:
        old_count, count = scene['old_count'], scene['count']
        if count == old_count and sections and sections[-1][1] == sections[-1][2]:
            start, old, new = sections.pop()
            sections.append((start, old + count, new + count))
        else:
            sections.append((scene['old_first'], old_count, count))
        if scene['id'] == ending:
            break
    if len(sections) == 1 and ending is None:
        return VIDEO_PATH
    dest = PARTS / ('opening-timed.mp4' if ending else 'retimed.mp4')
    parts = PARTS / ('opening-timed' if ending else 'timed')
    parts.mkdir(exist_ok=True)

    def encode(index_section):
        index, (start, old_count, new_count) = index_section
        part = parts / f'{index:03d}.mp4'
        speed = new_count / old_count
        effect = (f'trim=end_frame={old_count},setpts=(PTS-STARTPTS)*{speed:.12f},fps=24,'
                  'tpad=stop_mode=clone:stop_duration=0.12,setsar=1')
        subprocess.run([FF, '-y', '-v', 'error', '-ss', str(start / FPS), '-i', str(VIDEO_PATH),
                        '-filter_threads', '2', '-vf', effect, '-frames:v', str(new_count),
                        '-an', '-c:v', 'h264_videotoolbox', '-b:v', '12M', '-pix_fmt', 'yuv420p',
                        '-video_track_timescale', '12288', '-g', '48', '-bf', '0', str(part)], check=True)
        assert frame(probe_duration(part)) == new_count, part
        return part, new_count

    with ThreadPoolExecutor(max_workers=2) as pool:
        files = list(pool.map(encode, enumerate(sections)))
    concat(files, dest)
    return dest


def concat(files, output, audio=None, captions=None):
    manifest = output.with_suffix('.concat.txt')
    manifest.write_text(''.join(f"file '{path}'\nduration {count/FPS:.12f}\n" for path, count in files))
    command = [FF, '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', str(manifest)]
    if audio:
        command += ['-i', str(audio)]
    if captions:
        command += ['-i', str(captions)]
    command += ['-map', '0:v:0', '-c:v', 'copy']
    if audio:
        command += ['-map', '1:a:0', '-c:a', 'aac', '-b:a', '256k']
    if captions:
        command += ['-map', '2:s:0', '-c:s', 'mov_text', '-metadata:s:s:0', 'language=eng',
                    '-metadata:s:s:0', 'title=English', '-disposition:s:0', 'default']
    temp = output.with_suffix('.partial.mp4')
    subprocess.run(command + ['-movflags', '+faststart', str(temp)], check=True)
    assert frame(probe_duration(temp)) == sum(count for _, count in files), output
    temp.replace(output)


def label_picture(video, plan, review=False, ending=None):
    # Use short blocks to burn the artwork and title labels without dropped frames.
    total = frame(next(s['end'] for s in plan['scenes'] if s['id'] == ending)) if ending else frame(plan['duration'])
    chunks = [(first, min(432, total - first)) for first in range(0, total, 432)]
    output = PARTS / ('review-labeled' if review else 'sample-labeled' if ending else 'labeled')
    output.mkdir(exist_ok=True)
    blocks = PARTS / ('sample-blocks' if ending else 'blocks')
    blocks.mkdir(exist_ok=True)
    label_plan = plan if review else {**plan, 'scenes': [{**s, 'text': ''} for s in plan['scenes']]}
    overlay_dir = P / 'overlays' / output.name
    overlay_dir.mkdir(exist_ok=True)
    overlays = write_overlays(shot_annotations(plan), overlay_dir, label_plan,
                              title_y=735, show_generated_credit=False,
                              live_gallery_credit=not MUSE_GALLERY.is_file())

    def label(index_chunk):
        index, chunk = index_chunk
        first, count = chunk
        part = blocks / f'{first:05d}.mp4'
        if review:
            source = originals[index]
            existing = output / source.name
            if index not in (0, 1, len(chunks) - 2, len(chunks) - 1) and existing.is_file():
                assert frame(probe_duration(existing)) == count
                return existing, count
        else:
            subprocess.run([FF, '-v', 'error', '-y', '-ss', str(first / FPS), '-i', str(video),
                            '-frames:v', str(count), '-an', '-c:v', 'h264_videotoolbox',
                            '-b:v', '12M', '-pix_fmt', 'yuv420p', '-bf', '0', '-g', '48',
                            '-video_track_timescale', '12288', str(part)], check=True)
            source = part
        result = burn_labels((source, first, count, overlays), output_dir=output)
        return result, count

    if review:
        from picture import clean_parts
        originals = clean_parts()
        chunks = [(cut['first'], cut['count']) for cut in CUTS]
    with ThreadPoolExecutor(max_workers=4) as pool:
        files = list(pool.map(label, enumerate(chunks)))
    return files


def vtt_timestamp(seconds):
    millis = round(seconds * 1000)
    h, remainder = divmod(millis, 3600000)
    m, remainder = divmod(remainder, 60000)
    s, ms = divmod(remainder, 1000)
    return f'{h:02}:{m:02}:{s:02}.{ms:03}'


def write_captions(path, captions):
    import textwrap
    cues = ['WEBVTT\n']
    for start, end, text in captions:
        lines = textwrap.wrap(text, width=57, break_long_words=False)
        total = sum(len(line.split()) for line in lines)
        elapsed = 0
        for pos in range(0, len(lines), 2):
            block = lines[pos:pos + 2]
            first = start + (end - start) * elapsed / total
            elapsed += sum(len(line.split()) for line in block)
            last = start + (end - start) * elapsed / total
            cues.append(f'{vtt_timestamp(first)} --> {vtt_timestamp(last)}\n' + '\n'.join(block) + '\n')
    path.write_text('\n'.join(cues))


def main():
    if '--picture-review' in sys.argv:
        plan = timeline({})
        files = label_picture(VIDEO_PATH, plan, review=True)
        concat(files, EXPORTS / '压力焦虑肖邦浪漫-画面审阅版.mp4', V4 / 'exports/english-walk-mix.wav')
        return
    names = [name for name in VOICE_PROFILES if '--' + name in sys.argv] or list(VOICE_PROFILES)
    ending = 'listen' if '--opening-voices' in sys.argv else None
    selected = {'p002', 'p003', 'p004'} if ending else None
    takes = {name: read_takes(name, selected) for name in names}
    plan = timeline(takes)
    print('Picture length', plan['duration'], flush=True)
    picture = video_slices(plan, ending=ending)
    files = label_picture(picture, plan, ending=ending)
    receipts = {}
    for name in names:
        mix, captions, receipt = make_mix(plan, takes[name])
        suffix = '-opening' if ending else ''
        audio = PARTS / f'{name}{suffix}-mix.wav'
        caption_path = EXPORTS / f'{name}{suffix}-english.vtt'
        sample_count = sum(count for _, count in files) * (SR // FPS)
        write_wav(audio, mix[:sample_count])
        write_captions(caption_path, captions)
        version = '英文开场试配' if ending else '英文版'
        output = EXPORTS / ('压力焦虑肖邦浪漫-' + VOICE_PROFILES[name].replace('×', 'x').replace(' ', '-') + '-' + version + '.mp4')
        concat(files, output, audio, None if '--no-embedded-subtitles' in sys.argv else caption_path)
        receipts[name] = {**receipt, 'film': output.name, 'captions': caption_path.name, 'phrases': len(captions)}
        print('Rendered', output, flush=True)
    plan_file = P / ('sample-edit-plan.json' if ending else 'edit-plan.json')
    plan_file.write_text(json.dumps({**plan, 'versions': receipts}, ensure_ascii=False, indent=2) + '\n')


if __name__ == '__main__':
    main()
