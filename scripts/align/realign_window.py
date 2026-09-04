"""Re-align one window of a song.

Whole-song alignment can lose the vocal through a long instrumental and dump every
remaining word on a single timestamp. Re-running the aligner on just that window,
with just those lines, gives it nothing to drift through.

    realign_window.py <first-line-index> <last-line-index> <from-sec> <to-sec>
"""
import json, pathlib, subprocess, sys

REPO = pathlib.Path(__file__).resolve().parents[2]
i0, i1, t0, t1 = int(sys.argv[1]), int(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4])

song_path = REPO / 'src/songs/one-breath.json'
song = json.loads(song_path.read_text())
lines = song['lines'][i0:i1 + 1]

stem = REPO / 'tmp/align/htdemucs' / pathlib.Path(song['audio']).stem / 'vocals.wav'
clip = REPO / f'tmp/align/window-{i0}-{i1}.wav'
subprocess.run(['ffmpeg', '-v', 'error', '-ss', str(t0), '-to', str(t1),
                '-i', str(stem), '-y', str(clip)], check=True)

import stable_whisper
model = stable_whisper.load_model('medium', device='cpu')
result = model.align(str(clip), '\n'.join(l['text'] for l in lines), language='en')
words = [w for seg in result.segments for w in seg.words]
print(f'{len(words)} words aligned in window')

cursor = 0
for line in lines:
    n = len(line['text'].split())
    if cursor < len(words):
        print(f"  {t0 + words[cursor].start:7.2f}  (was {line['t']:7.2f})  {line['text']}")
        line['t'] = round(t0 + words[cursor].start, 2)
    cursor += n

song['lines'][i0:i1 + 1] = lines
song_path.write_text(json.dumps(song, indent=2, ensure_ascii=False) + '\n')
print('written')
