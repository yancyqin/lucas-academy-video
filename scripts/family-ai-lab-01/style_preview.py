"""Make a short tour of the actual delivered film, retaining both audio tracks."""
from pathlib import Path
import json
import subprocess

ROOT = Path(__file__).resolve().parents[2]


def main():
    timeline = json.loads((ROOT / 'public/family-ai-lab-01/timeline.json').read_text())
    revision = timeline.get('visualRevision', timeline['revision'])
    folder = ROOT / f'out/family-ai-lab-01/delivery/v{revision}'
    source = folder / 'family-ai-lab-01.bilingual.mp4'
    target = folder / 'style-preview.mp4'
    cues = {line['id']: line for line in timeline['lines']}
    selected = ['fa01-01-01', 'fa01-01-04', 'fa01-03-02', 'fa01-04-04',
                'fa01-05-04', 'fa01-06-05', 'fa01-07-07', 'fa01-08-01', 'fa01-08-10']
    filters, pads, ranges = [], [], []
    for index, name in enumerate(selected):
        cue = cues[name]
        start = cue['from'] / timeline['fps'] + (3 if index == 0 else .5)
        end = start + 6
        assert end <= timeline['durationInFrames'] / timeline['fps']
        ranges.append({'cue': name, 'fromSeconds': start, 'toSeconds': end})
        filters.append(f'[0:v:0]trim=start={start}:end={end},setpts=PTS-STARTPTS[v{index}]')
        for audio in (0, 1):
            filters.append(f'[0:a:{audio}]atrim=start={start}:end={end},asetpts=PTS-STARTPTS[a{index}_{audio}]')
        pads.append(f'[v{index}][a{index}_0][a{index}_1]')
    filters.append(''.join(pads) + f'concat=n={len(selected)}:v=1:a=2[v][en][zh]')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-threads', '2', '-i', str(source),
                    '-filter_complex_threads', '2', '-filter_complex', ';'.join(filters),
                    '-map', '[v]', '-map', '[en]', '-map', '[zh]',
                    '-c:v', 'libx264', '-threads', '3', '-crf', '20', '-preset', 'fast',
                    '-c:a', 'aac', '-b:a', '192k', '-ar', '48000',
                    '-metadata:s:a:0', 'language=eng', '-metadata:s:a:1', 'language=zho',
                    '-disposition:a:0', 'default', '-disposition:a:1', '0',
                    '-movflags', '+faststart', str(target)], check=True)
    probe = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_streams',
                                                '-show_format', '-of', 'json', str(target)]))
    assert abs(float(probe['format']['duration']) - 54) < .1
    assert len(probe['streams']) == 3
    assert [(s['tags']['language'], s['disposition']['default']) for s in probe['streams']
            if s['codec_type'] == 'audio'] == [('eng', 1), ('zho', 0)]
    (folder / 'style-preview.json').write_text(json.dumps({'seconds': 54, 'source': str(source.relative_to(ROOT)),
                                                          'ranges': ranges}, indent=2) + '\n')
    print('54-second style preview:', target)


if __name__ == '__main__':
    main()
