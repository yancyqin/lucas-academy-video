"""Force-align known lyrics to a song and emit per-line start times.

Separates the vocal stem with Demucs first -- alignment on a full rock mix is
unreliable, on an isolated vocal it is not. The lyrics are already known, so
this is alignment, never transcription.
"""
import json, pathlib, subprocess, sys

REPO = pathlib.Path(__file__).resolve().parents[2]
song = json.loads((REPO / 'src/songs/one-breath.json').read_text())
audio = REPO / 'public' / song['audio']
work = REPO / 'tmp/align'
work.mkdir(parents=True, exist_ok=True)

stem = work / 'htdemucs' / audio.stem / 'vocals.wav'
if not stem.exists():
    print('== separating vocals (demucs) ==', flush=True)
    subprocess.run([sys.executable, '-m', 'demucs', '--two-stems=vocals',
                    '-o', str(work), str(audio)], check=True)
print('vocal stem:', stem, flush=True)

import stable_whisper
lines = song['lines']
text = '\n'.join(l['text'] for l in lines)

for device in ('cpu',):
    print(f'== aligning on {device} ==', flush=True)
    model = stable_whisper.load_model('medium', device=device)
    result = model.align(str(stem), text, language='en')
    break

words = [w for seg in result.segments for w in seg.words]
print(f'aligned {len(words)} words', flush=True)

# Walk the known word sequence and take each line's first word as its start.
out, cursor = [], 0
for line in lines:
    n = len(line['text'].split())
    if cursor >= len(words):
        out.append(round(line['t'], 2)); continue
    out.append(round(words[cursor].start, 2))
    cursor += n

for line, t in zip(lines, out):
    line['t'] = t
song['timingSource'] = 'demucs+stable-ts forced alignment'
(REPO / 'src/songs/one-breath.aligned.json').write_text(json.dumps(song, indent=2, ensure_ascii=False))
result.save_as_json(str(work / 'words.json'))
print('wrote src/songs/one-breath.aligned.json', flush=True)
for line, t in zip(lines, out):
    print(f'  {int(t)//60:02d}:{t%60:05.2f}  {line["section"]:<9} {line["text"]}')
