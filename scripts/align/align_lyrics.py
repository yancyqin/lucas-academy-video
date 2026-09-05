"""Force-align known lyrics to a song and write per-line start times.

The lyrics are already known, so this is alignment, never transcription.

Vocal source, best first:
  1. --stem PATH                      an isolated vocal you already have
  2. stems/<song>/*Lead Vocals*       Suno's own stem export
  3. Demucs separation                last resort

Suno's stems are real tracks, not a separation: no bleed, and the backing vocals
come on their own file, which matters because gang vocals in a shared stem are
what make chorus syllable boundaries impossible to measure. Demucs is the fallback
for audio that has no stems.
"""
import argparse, json, pathlib, subprocess, sys, glob

REPO = pathlib.Path(__file__).resolve().parents[2]

ap = argparse.ArgumentParser()
ap.add_argument('--song', default='src/songs/one-breath.json')
ap.add_argument('--stem', help='isolated vocal track; skips stem discovery')
ap.add_argument('--model', default='medium')
args = ap.parse_args()

song_path = REPO / args.song
song = json.loads(song_path.read_text())
work = REPO / 'tmp/align'
work.mkdir(parents=True, exist_ok=True)

def find_vocal() -> pathlib.Path:
    if args.stem:
        return pathlib.Path(args.stem)
    # Stems are filed per song -- stems/<song>/0 Lead Vocals.mp3 -- but an older
    # layout put them loose in stems/. Only these two shapes are searched: a
    # recursive glob would happily return another song's vocal and align against
    # it without complaint.
    name = song_path.stem
    for pattern in (f'stems/{name}/*Lead Vocals*', 'stems/*Lead Vocals*'):
        hits = sorted(glob.glob(str(REPO / pattern)))
        if hits:
            print(f'== stem: {pathlib.Path(hits[0]).relative_to(REPO)}', flush=True)
            return pathlib.Path(hits[0])
    # Loud on purpose. A separated stem mixes the lead with the backing vocals, and
    # gang vocals filling the gaps between chorus lines are what make syllable
    # boundaries unmeasurable. If this fires, the timings will be worse.
    print('!! ' + '=' * 68, flush=True)
    print(f'!! No stem found under stems/ for "{name}". Falling back to Demucs.', flush=True)
    print('!! A separation is markedly worse than a real stem export -- if the song', flush=True)
    print('!! has stems, put them in stems/%s/ and re-run.' % name, flush=True)
    print('!! ' + '=' * 68, flush=True)
    audio = REPO / 'public' / song['audio']
    stem = work / 'htdemucs' / audio.stem / 'vocals.wav'
    if not stem.exists():
        subprocess.run([sys.executable, '-m', 'demucs', '--two-stems=vocals',
                        '-o', str(work), str(audio)], check=True)
    return stem

# Always decode to wav first. Suno's stem exports carry broken MP3 headers -- ffprobe
# reports 1299s for a 313s file -- and anything that trusts the header slices wrongly.
src = find_vocal()
vocal = work / 'vocal-for-align.wav'
subprocess.run(['ffmpeg', '-v', 'error', '-i', str(src), '-ac', '1', '-ar', '44100',
                '-y', str(vocal)], check=True)
dur = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                            '-of', 'csv=p=0', str(vocal)], capture_output=True,
                           text=True).stdout)
print(f'vocal: {src.name} -> {dur:.2f}s', flush=True)

import stable_whisper
model = stable_whisper.load_model(args.model, device='cpu')
lines = song['lines']

# Align in windows split at instrumental gaps. A single whole-song pass can lose the
# vocal through a long break and stack every remaining word on one timestamp.
gaps = sorted(((lines[i + 1]['t'] - lines[i]['t'], (lines[i]['t'] + lines[i + 1]['t']) / 2)
               for i in range(len(lines) - 1)), reverse=True)[:2]
cuts = [0.0] + sorted(g[1] for g in gaps) + [dur]
print(f'windows: {[round(c, 1) for c in cuts]}', flush=True)

out = []
for lo, hi in zip(cuts, cuts[1:]):
    chunk = [l for l in lines if lo <= l['t'] < hi]
    if not chunk:
        continue
    clip = work / f'w{int(lo)}.wav'
    subprocess.run(['ffmpeg', '-v', 'error', '-ss', str(lo), '-to', str(hi),
                    '-i', str(vocal), '-y', str(clip)], check=True)
    r = model.align(str(clip), '\n'.join(l['text'] for l in chunk), language='en')
    words = [w for seg in r.segments for w in seg.words]
    cursor = 0
    for line in chunk:
        if cursor < len(words):
            out.append((line, round(lo + words[cursor].start, 2)))
        cursor += len(line['text'].split())

for line, t in out:
    line['t'] = t
song['timingSource'] = f'forced alignment against {src.name}'
(song_path.parent / (song_path.stem + '.aligned.json')).write_text(
    json.dumps(song, indent=2, ensure_ascii=False) + '\n')
print(f'wrote {song_path.stem}.aligned.json  ({len(out)} lines)', flush=True)
for line, t in out:
    print(f'  {int(t)//60}:{t%60:05.2f}  {line["section"]:<9} {line["text"]}')
