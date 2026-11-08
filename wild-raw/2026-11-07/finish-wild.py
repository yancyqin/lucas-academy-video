"""Assemble and verify clean Wild footage without captions or audio."""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parent


def run(args):
    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(result.stderr)
    return result


def probe(path):
    return json.loads(run([
        'ffprobe', '-v', 'error', '-show_streams', '-show_format',
        '-of', 'json', str(path)
    ]).stdout)


def main():
    global ROOT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dir', type=Path, default=ROOT,
                        help='Capture directory; defaults to this archived package.')
    parser.add_argument('--verify-only', action='store_true',
                        help='Check footage and decode the master without rebuilding files.')
    args = parser.parse_args()
    ROOT = args.dir.resolve()
    manifest = json.loads((ROOT / 'capture-manifest.json').read_text())
    assert len(manifest['takes']) == 8
    assert not manifest['errors']
    states = set()
    events = set()
    rows = []
    for take in manifest['takes']:
        path = ROOT / take['file']
        p = probe(path)
        streams = p['streams']
        assert len(streams) == 1 and streams[0]['codec_type'] == 'video'
        stream = streams[0]
        assert (stream['width'], stream['height']) == (1920, 1080)
        assert stream['avg_frame_rate'] == '30/1'
        assert stream['pix_fmt'] in {'yuv420p', 'yuvj420p'}
        assert int(stream['nb_frames']) == take['frameCount']
        assert hashlib.sha256(path.read_bytes()).hexdigest() == take['sha256']
        states.update(take.get('states', {}))
        events.update(e['event'] for e in take.get('events', []))
        rows.append({'file': take['file'], 'duration': float(p['format']['duration']),
                     'frames': int(stream['nb_frames']), 'bytes': path.stat().st_size})
    assert {'ground', 'air', 'glide', 'climb', 'swim'} <= states
    assert {'jump', 'glide', 'lunge', 'mantle'} <= events
    quality = next(t for t in manifest['takes'] if t['id'].startswith('07-'))
    assert {'low', 'medium', 'high'} <= {s['tier'] for s in quality['samples']}
    touch = next(t for t in manifest['takes'] if t['id'].startswith('08-'))
    assert touch['jumped']['mode'] == 'air' and touch['glided']['mode'] == 'glide'

    if args.verify_only:
        receipt = json.loads((ROOT / 'verification.json').read_text())
        master = ROOT / receipt['master']
        stream = probe(master)['streams'][0]
        assert stream['codec_name'] == 'h264'
        assert (stream['width'], stream['height']) == (1920, 1080)
        assert stream['avg_frame_rate'] == '30/1'
        assert int(stream['nb_frames']) == sum(t['frameCount'] for t in manifest['takes'])
        assert hashlib.sha256(master.read_bytes()).hexdigest() == receipt['sha256']
        run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-i', str(master),
             '-an', '-f', 'null', '-'])
        print(json.dumps({'verifiedTakes': len(rows), 'master': master.name,
                          'frames': int(stream['nb_frames']), 'decodePassed': True}, indent=2))
        return

    listing = ROOT / 'source' / 'takes.concat.txt'
    listing.write_text(''.join("file '../" + t['file'] + "'\n" for t in manifest['takes']))
    master = ROOT / 'the-wild-raw-1080p30.mp4'
    run(['ffmpeg', '-hide_banner', '-loglevel', 'warning', '-y',
         '-f', 'concat', '-safe', '0', '-i', str(listing), '-an',
         '-vf', 'scale=in_color_matrix=auto:out_color_matrix=bt709:out_range=tv,format=yuv420p',
         '-c:v', 'libx264', '-preset', 'fast', '-crf', '17', '-g', '30',
         '-color_range', 'tv', '-colorspace', 'bt709',
         '-color_primaries', 'bt709', '-color_trc', 'bt709',
         '-movflags', '+faststart', str(master)])
    print('MASTER', master, flush=True)
    p = probe(master)
    expected = sum(t['frameCount'] for t in manifest['takes'])
    assert int(p['streams'][0]['nb_frames']) == expected
    assert p['streams'][0]['pix_fmt'] == 'yuv420p'
    assert p['streams'][0]['color_space'] == 'bt709'
    assert abs(float(p['format']['duration']) - expected / 30) < .05
    decoded = run(['ffmpeg', '-hide_banner', '-loglevel', 'info', '-i', str(master),
                   '-vf', 'blackdetect=d=0.15:pix_th=0.10:pic_th=0.98',
                   '-an', '-f', 'null', '-'])
    black = [line for line in decoded.stderr.splitlines() if 'black_start:' in line]
    assert not black, black
    preview = ROOT / 'the-wild-raw-preview-720p.mp4'
    run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', str(master),
         '-an', '-vf', 'scale=1280:720', '-c:v', 'libx264', '-preset', 'fast',
         '-crf', '22', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(preview)])
    run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', str(master),
         '-vf', 'fps=1/3.2,scale=480:270,tile=4x4', '-frames:v', '1',
         '-q:v', '2', str(ROOT / 'review-contact-sheet.jpg')])
    result = {'master': master.name, 'preview': preview.name, 'durationSeconds': expected / 30,
              'width': 1920, 'height': 1080, 'fps': 30, 'frameCount': expected,
              'videoOnly': True, 'addedText': False, 'promptOverlay': False,
              'blackFramesDetected': False, 'decodePassed': True,
              'statesCaptured': sorted(states), 'eventsCaptured': sorted(events), 'takes': rows,
              'sha256': hashlib.sha256(master.read_bytes()).hexdigest(),
              'bytes': master.stat().st_size,
              'repositorySubmission': 'Rebuilt locally; see capture-manifest.json for the capture review status.'}
    (ROOT / 'verification.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2), flush=True)


if __name__ == '__main__':
    main()
