"""Render the new live-action entrance and extend the cold water scene."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from pathlib import Path
import subprocess
import sys

P = Path(__file__).resolve().parent
V4 = P.parent / 'v4'
sys.path.insert(0, str(V4))
from finish_walk import CUTS, FF, FPS, INSERTS, compose, encode_options, frame, make_short, probe_duration

MUSE_GALLERY = P / 'footage/muse-gallery-entry.mp4'
TRANSITION_TITLE = 'From Gallery to Space'
COLD = P / 'footage/cold-water-loop.mp4'
COLD_START = 104.75
COLD_COUNT = 449
REVEAL = P / 'footage/walk'


def gallery_insert():
    original = INSERTS[0]
    if not MUSE_GALLERY.is_file():
        return original
    assert probe_duration(MUSE_GALLERY) >= original.end, MUSE_GALLERY
    speed = .8
    return replace(original, kind='muse', file=str(MUSE_GALLERY), trim=.5 * speed, speed=speed)


def cold_water_loop():
    if COLD.is_file() and frame(probe_duration(COLD)) == COLD_COUNT:
        return
    # The closing light of the first pass gently dissolves into the next descent.
    piece = ('trim=start=0.75:duration=6.3,setpts=(PTS-STARTPTS)/0.65,'
             'fps=24,setsar=1,settb=1/24')
    graph = (f'[0:v]{piece},split=2[first][second];'
             '[first][second]xfade=transition=fade:duration=0.625:offset=9.0416667,'
             'tpad=stop_duration=0.09:stop_mode=clone,format=yuv420p[v]')
    temp = COLD.with_suffix('.partial.mp4')
    subprocess.run([FF, '-y', '-v', 'error', '-filter_complex_threads', '2',
                    '-i', INSERTS[2].file, '-filter_complex', graph, '-map', '[v]',
                    *encode_options(COLD_COUNT), str(temp)], check=True)
    assert frame(probe_duration(temp)) == COLD_COUNT, probe_duration(temp)
    temp.replace(COLD)


def entrance():
    first = compose(CUTS[0], [gallery_insert()], P / 'parts', REVEAL)
    make_short(first, P, P / 'exports/从现实画廊到深空沙龙-新版开场.mp4',
               title_lines=[(822, TRANSITION_TITLE)])


def inserts():
    cold_water_loop()
    return [gallery_insert(), INSERTS[1], replace(INSERTS[2], file=str(COLD), trim=0,
            speed=1, start=COLD_START, end=COLD_START + COLD_COUNT / FPS,
            fade_in=1.10, fade_out=1.20), *INSERTS[3:]]


def clean_parts():
    updated = inserts()
    changed = [updated[0], updated[2]]

    def render(cut):
        start = cut['first']
        if cut['id'] == 'walk-00':
            return compose(cut, updated, P / 'parts', REVEAL)
        if cut['id'] == 'walk-01':
            return REVEAL / 'walk-01.mp4'
        if any(frame(item.start) < start + cut['count'] and frame(item.end) > start
               for item in changed):
            return compose(cut, updated, P / 'parts')
        version_four = V4 / 'parts' / (cut['id'] + '.mp4')
        if version_four.is_file():
            return version_four
        return V4 / 'footage/walk' / version_four.name

    with ThreadPoolExecutor(max_workers=2) as pool:
        return list(pool.map(render, CUTS))


def clean_picture():
    output = P / 'parts/clean-picture.mp4'
    temp = output.with_suffix('.partial.mp4')
    files = clean_parts()
    manifest = P / 'parts/clean-picture.concat.txt'
    manifest.write_text(''.join(f"file '{path}'\nduration {cut['count']/FPS:.12f}\n"
                                for path, cut in zip(files, CUTS, strict=True)))
    subprocess.run([FF, '-y', '-v', 'error', '-f', 'concat', '-safe', '0', '-i', str(manifest),
                    '-c:v', 'copy', '-movflags', '+faststart', str(temp)], check=True)
    assert frame(probe_duration(temp)) == sum(cut['count'] for cut in CUTS)
    temp.replace(output)
    return output


if __name__ == '__main__':
    entrance()
    if '--opening-only' not in sys.argv:
        print(clean_picture(), flush=True)
