"""Add centered picture dissolves and longer music fades without moving the film clock."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path

from classical_mix import render_music

ROOT = Path('/Users/yqin/repo/playground/lucas-academy-video-data/curiosity-builds-20261118/v9')
PREVIOUS = ROOT.with_name('v8')
PLAN = json.loads(Path(__file__).with_name('plan.json').read_text())
FX = PLAN['transitions']
FPS = 30
EDIT, OUT, REC = (ROOT / name for name in ['edit', 'delivery', 'records'])


def run(command):
    subprocess.run(command, check=True)


def frames(path):
    return int(subprocess.check_output([
        'ffprobe', '-v', 'error', '-select_streams', 'v:0',
        '-show_entries', 'stream=nb_frames', '-of', 'csv=p=0', str(path)
    ]).strip().split(b',')[0])


def part(path, start=0, length=None):
    return {'file': str(path), 'start_frame': start,
            'frames': frames(path) - start if length is None else length}


def dissolve(parts, boundaries, target, overall_fades=False):
    """Keep all source frames. Add half-transition edge handles, then overlap them.

    A transition is centered on its original cut. The outgoing edge holds only
    during the incoming half, and vice versa, so chapter and SRT times stay exact.
    """
    assert len(boundaries) == len(parts) - 1
    assert all(n % 2 == 0 for n in boundaries)
    total = sum(p['frames'] for p in parts)
    token = hashlib.sha256(json.dumps({
        'parts': [(p, Path(p['file']).stat().st_mtime_ns,
                   Path(p['file']).stat().st_size) for p in parts],
        'transitions': boundaries, 'overall_fades': overall_fades, 'settings': FX
    }, sort_keys=True).encode()).hexdigest()
    receipt = REC / (target.stem + '.dissolves.json')
    if target.exists() and receipt.exists():
        if json.loads(receipt.read_text()).get('digest') == token:
            assert frames(target) == total
            return
    inputs, filters = [], []
    for i, p in enumerate(parts):
        n = p['frames']
        pre = boundaries[i - 1] // 2 if i else 0
        post = boundaries[i] // 2 if i < len(boundaries) else 0
        assert n > pre + post
        inputs += ['-threads', '1', '-ss', f"{p['start_frame']/FPS:.9f}",
                   '-t', f'{n/FPS:.9f}', '-i', p['file']]
        filters.append(
            f'[{i}:v]trim=end_frame={n},setpts=N/(30*TB),fps=30,'
            f'setsar=1,format=yuv420p,tpad=start={pre}:start_mode=clone:'
            f'stop={post}:stop_mode=clone,settb=AVTB[v{i}]')
    current = 'v0'
    cursor = parts[0]['frames']
    transitions = []
    for i, n in enumerate(boundaries, 1):
        name = f'x{i}'
        offset = (cursor - n // 2) / FPS
        filters.append(f'[{current}][v{i}]xfade=transition=fade:'
                       f'duration={n/FPS:.9f}:offset={offset:.9f}[{name}]')
        transitions.append({'cut_frame': cursor, 'frames': n,
                            'start_frame': cursor-n//2, 'end_frame': cursor+n//2})
        cursor += parts[i]['frames']
        current = name
    tail = f'[{current}]trim=end_frame={total},setpts=N/(30*TB)'
    if overall_fades:
        tail += (f",fade=t=in:start_frame=0:nb_frames={FX['film_picture_fade_in_frames']}"
                 f",fade=t=out:start_frame={total-FX['film_picture_fade_out_frames']}:"
                 f"nb_frames={FX['film_picture_fade_out_frames']}")
    filters.append(tail + ',format=yuv420p[out]')
    graph = ';'.join(filters)
    (REC / (target.stem+'.filter.txt')).write_text(graph+'\n')
    temporary = target.with_name(target.stem+'.rendering.mp4')
    command = ['ffmpeg', '-y', '-v', 'error', *inputs,
               '-filter_complex_threads', '2', '-filter_complex', graph,
               '-map', '[out]', '-an', '-frames:v', str(total),
               '-c:v', 'libx264', '-threads', '6', '-preset', 'fast', '-crf', '18',
               '-video_track_timescale', '15360', '-movflags', '+faststart', str(temporary)]
    print('Rendering picture:', target.name, flush=True)
    run(command)
    actual = frames(temporary)
    assert actual == total, (target, actual, total)
    temporary.replace(target)
    receipt.write_text(json.dumps({'digest': token, 'source_parts': parts,
                                  'output_frames': total, 'transitions': transitions,
                                  'overall_fades': overall_fades}, indent=2)+'\n')
    print('Picture ready:', target.name, total/FPS, 'seconds', flush=True)


def mux(picture, music, target, offset=0, standalone=False, metadata=None):
    total = frames(picture)
    seconds = total / FPS
    key = hashlib.sha256(json.dumps([
        str(picture), picture.stat().st_mtime_ns, music.stat().st_mtime_ns,
        offset, standalone, FX, metadata.read_text() if metadata else None
    ]).encode()).hexdigest()
    receipt = REC / (target.stem+'.mux.json')
    if target.exists() and receipt.exists() and json.loads(receipt.read_text()).get('digest') == key:
        return
    command = ['ffmpeg', '-y', '-v', 'error', '-i', str(picture),
               '-ss', str(offset), '-i', str(music)]
    if metadata:
        command += ['-i', str(metadata), '-map_metadata', '2', '-map_chapters', '2']
    else:
        command += ['-map_metadata', '-1', '-map_chapters', '-1']
    command += ['-map', '0:v:0', '-map', '1:a:0']
    if standalone:
        command += ['-vf',
                    f"fade=t=in:start_frame=0:nb_frames={FX['standalone_picture_fade_in_frames']},"
                    f"fade=t=out:start_frame={total-FX['standalone_picture_fade_out_frames']}:"
                    f"nb_frames={FX['standalone_picture_fade_out_frames']}",
                    '-c:v', 'libx264', '-threads', '6', '-preset', 'fast', '-crf', '18',
                    '-af', f"afade=t=in:st=0:d={FX['standalone_audio_fade_in_seconds']}:curve=qsin,"
                    f"afade=t=out:st={seconds-FX['standalone_audio_fade_out_seconds']}:"
                    f"d={FX['standalone_audio_fade_out_seconds']}:curve=qsin"]
    else:
        command += ['-c:v', 'copy']
    temporary = target.with_name(target.stem+'.muxing.mp4')
    command += ['-c:a', 'aac', '-b:a', '192k', '-t', str(seconds),
                '-video_track_timescale', '15360', '-movflags', '+faststart', str(temporary)]
    print('Adding music:', target.name, flush=True)
    run(command)
    assert frames(temporary) == total
    temporary.replace(target)
    receipt.write_text(json.dumps({'digest': key, 'frames': total,
                                  'standalone_edge_fades': standalone}, indent=2)+'\n')


def chapter_picture(index, project):
    intro = ROOT/'builds'/(project['id']+'.mp4')
    parts = [part(intro)]
    boundaries = []
    for j, clip in enumerate(project['clips']):
        parts.append(part(ROOT/'edit'/(clip['file']+'.mp4')))
        boundaries.append(FX['build_to_footage_frames'] if j == 0 else FX['shot_picture_frames'])
    picture = EDIT/f'{index:02d}-{project["id"]}-picture.mp4'
    dissolve(parts, boundaries, picture)
    return picture


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--chapter', choices=[p['id'] for p in PLAN['projects']])
    parser.add_argument('--picture-only', action='store_true')
    args = parser.parse_args()
    sheet, cursor = [], round(PLAN['opening_seconds']*FPS)
    for project in PLAN['projects']:
        length = frames(ROOT/'builds'/(project['id']+'.mp4'))
        length += sum(frames(EDIT/(clip['file']+'.mp4')) for clip in project['clips'])
        sheet.append({'id': project['id'], 'project': project['name'],
                      'url': project['url'], 'start': cursor/FPS, 'seconds': length/FPS})
        cursor += length
    total = cursor/FPS + PLAN['ending_seconds']
    music = None if args.picture_only else render_music(PLAN, sheet, total)
    pictures = []
    for index, (project, chapter) in enumerate(zip(PLAN['projects'], sheet), 1):
        if args.chapter and project['id'] != args.chapter:
            continue
        picture = chapter_picture(index, project)
        assert frames(picture) == round(chapter['seconds']*FPS)
        pictures.append(picture)
        if music:
            mux(picture, music, OUT/f'{index:02d}-{project["id"]}.en.no-voice.mp4',
                chapter['start'], standalone=True)
    if args.chapter:
        return
    (REC/'chapters.json').write_text(json.dumps(sheet, indent=2)+'\n')
    parts = [*[part(p) for p in pictures],
             part(ROOT/'builds/ending.mp4')]
    silent = OUT/'curiosity-builds.en.silent.mp4'
    dissolve(parts, [FX['project_picture_frames']]*(len(parts)-1), silent, overall_fades=True)
    assert frames(silent) == round(total*FPS)
    metadata = EDIT/'chapters.ffmeta'
    lines=[';FFMETADATA1','title='+PLAN['title'],'artist=Lucas Academy Team','language=eng']
    for c in sheet:
        lines+=['[CHAPTER]','TIMEBASE=1/1000',f'START={round(c["start"]*1000)}',f'END={round((c["start"]+c["seconds"])*1000)}','title='+c['project']]
    metadata.write_text('\n'.join(lines)+'\n')
    if music:
        mux(silent, music, OUT/'curiosity-builds.en.no-voice.mp4', metadata=metadata)
        mux(ROOT/'builds/ending.mp4', music, OUT/'ending-preview.en.no-voice.mp4',
            total-PLAN['ending_seconds'], standalone=True)
    print('Completed transition revision:', total, 'seconds', flush=True)


if __name__ == '__main__':
    main()
