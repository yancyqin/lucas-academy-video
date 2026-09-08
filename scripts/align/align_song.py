"""Force-align a known lyric sheet to an isolated vocal and write a song JSON.

The lyrics are known, so this is alignment, never transcription: the text is the
authority and only its timing is being measured.

Unlike align_lyrics.py this needs no seed timings in the song JSON -- it takes a
plain `section|text` sheet and measures every line from scratch, which is what a
song has before any hand timing exists.

Each line gets both a start and an end. A start alone leaves display length to a
global hold constant, and that constant is what makes lines vanish mid-phrase when
the gap between two lines is longer than it.

  .venv-align/bin/python scripts/align/align_song.py \
      --vocal "stems/rejoice/0 Lead Vocals.mp3" \
      --lyrics scripts/mv/data/rejoice-lyrics.txt --audio audio/songs/rejoice.mp3 \
      --title Rejoice --out src/songs/rejoice.json
"""
import argparse, json, pathlib, subprocess

REPO = pathlib.Path(__file__).resolve().parents[2]

ap = argparse.ArgumentParser()
ap.add_argument('--vocal', required=True)
ap.add_argument('--lyrics', required=True)
ap.add_argument('--audio', required=True, help="song path relative to public/")
ap.add_argument('--title', default='')
ap.add_argument('--subtitle', default=None)
ap.add_argument('--fps', type=int, default=30)
ap.add_argument('--model', default='medium')
ap.add_argument('--out', required=True)
args = ap.parse_args()

sheet = [l for l in pathlib.Path(args.lyrics).read_text().splitlines() if l.strip()]
lines = [{'section': s, 'text': t} for s, t in (l.split('|', 1) for l in sheet)]
print(f'{len(lines)} lyric lines', flush=True)

# Always work from a wav. Suno's mp3 exports carry broken headers -- one reports
# 1299s for a 313s file -- so anything that trusts a header slices the wrong range.
vocal = REPO / 'tmp/align/vocal-for-align.wav'
vocal.parent.mkdir(parents=True, exist_ok=True)
subprocess.run(['ffmpeg', '-v', 'error', '-i', args.vocal, '-ac', '1', '-ar', '16000',
                '-y', str(vocal)], check=True)
dur = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                            '-of', 'csv=p=0', str(vocal)], capture_output=True,
                           text=True).stdout)
print(f'vocal {dur:.2f}s', flush=True)

import stable_whisper
model = stable_whisper.load_model(args.model, device='cpu')
result = model.align(str(vocal), '\n'.join(l['text'] for l in lines), language='en')

words = [w for seg in result.segments for w in seg.words]
print(f'aligned {len(words)} words', flush=True)

# Walk the word stream line by line: the aligner is fed the same text, in the same
# order, so line boundaries fall on cumulative word counts.
cursor = 0
for line in lines:
    n = len(line['text'].split())
    span = words[cursor:cursor + n]
    if span:
        line['t'] = round(span[0].start, 2)
        line['end'] = round(span[-1].end, 2)
    cursor += n

missing = [l for l in lines if 't' not in l]
if missing:
    print(f'WARNING {len(missing)} lines got no words', flush=True)

song = {
    'title': args.title, 'audio': args.audio, 'fps': args.fps,
    'durationSeconds': round(dur, 2),
    'timingSource': f'forced alignment against {pathlib.Path(args.vocal).name}',
    'lines': lines,
}
if args.subtitle:
    song['subtitle'] = args.subtitle
out = REPO / args.out
out.write_text(json.dumps(song, indent=2, ensure_ascii=False) + '\n')
print(f'wrote {args.out}', flush=True)

prev = None
for i, l in enumerate(lines):
    t, e = l.get('t'), l.get('end')
    flag = ''
    if t is None:
        flag = '  <- NO WORDS'
    elif prev is not None and t < prev:
        flag = '  <- OUT OF ORDER'
    if t is not None:
        prev = t
        print(f'{i:3} {int(t)//60}:{t%60:05.2f} -> {int(e)//60}:{e%60:05.2f} '
              f'{l["section"]:<9} {l["text"]}{flag}')
    else:
        print(f'{i:3}   --   {l["section"]:<9} {l["text"]}{flag}')
