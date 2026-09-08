"""Trim each lyric line's end to where the singing actually stops.

Forced alignment reports a start and an end per line, but the end of the last word
in a phrase absorbs whatever follows it. Measured against the envelope, line 29 of
this song claimed 22.4 seconds and line 37 claimed 24.5 -- both were running
through instrumental breaks. A line that holds on a timestamp nothing measured is
the documented way lyrics go wrong, so every end here is clamped to the last
moment the vocal is actually above the floor.

Parenthesised echo lines ("(Rejoice)") are the one case with no lead vocal of their
own: the recording sings the phrase twice and answers it, so the echo is placed in
the measured response gap after the phrase it echoes, never on top of a sung line.

  .venv-align/bin/python scripts/align/refine_ends.py --song src/songs/rejoice.json \
      --overrides scripts/mv/data/rejoice-tail-overrides.json \
      --vocal tmp/rejoice/lead.wav
"""
import argparse, json, pathlib
import numpy as np, soundfile as sf

ap = argparse.ArgumentParser()
ap.add_argument('--song', required=True)
ap.add_argument('--vocal', required=True)
ap.add_argument('--hop', type=float, default=0.02)
ap.add_argument('--below-peak', type=float, default=11.0,
                help='dB below the track p95 that still counts as voiced. 11 puts the '
                     'gate at -30 dB here, chosen by measuring labelled windows: sung '
                     'phrases sit at -23..-27 dB, instrumental gaps at -46..-84 dB')
ap.add_argument('--close-gap', type=float, default=0.30)
ap.add_argument('--tail', type=float, default=0.22, help='held after the last voiced frame')
ap.add_argument('--min-hold', type=float, default=1.10)
ap.add_argument('--echo-hold', type=float, default=1.60)
ap.add_argument('--max-hold', type=float, default=6.5,
                help='longest a line may stay up. The gate cannot help on the intro '
                     'break, where instrument bleed reaches -23.6 dB and overlaps the '
                     'sung range, so the last line before a break is capped and fades')
ap.add_argument('--overrides', default=None,
                help='JSON of {line index: {t, end}} measured by hand, applied verbatim')
ap.add_argument('--write', action='store_true')
a = ap.parse_args()

REPO = pathlib.Path(__file__).resolve().parents[2]
song_path = REPO / a.song
song = json.loads(song_path.read_text())
lines = song['lines']

x, sr = sf.read(a.vocal, dtype='float32', always_2d=True)
x = x.mean(axis=1)
hop = int(sr * a.hop); n = len(x) // hop
rms = np.sqrt(np.maximum((x[:n * hop] ** 2).reshape(n, hop).mean(axis=1), 1e-12))
db = 20 * np.log10(rms)
thresh = np.percentile(db, 95) - a.below_peak
voiced = db > thresh
# Close short gaps so a breath inside a phrase does not read as the end of it.
k = int(a.close_gap / a.hop)
padded = voiced.copy()
idx = np.flatnonzero(voiced)
for i, j in zip(idx, idx[1:]):
    if j - i <= k:
        padded[i:j] = True
voiced = padded
print(f'threshold {thresh:.1f} dB   voiced {voiced.mean()*100:.1f}%   {n} frames', flush=True)

def last_voiced(lo, hi):
    """Last voiced time in [lo, hi), or None."""
    i0, i1 = int(lo / a.hop), min(int(hi / a.hop), n)
    if i1 <= i0:
        return None
    seg = np.flatnonzero(voiced[i0:i1])
    return None if not len(seg) else (i0 + seg[-1] + 1) * a.hop

def first_voiced(lo, hi):
    i0, i1 = int(lo / a.hop), min(int(hi / a.hop), n)
    if i1 <= i0:
        return None
    seg = np.flatnonzero(voiced[i0:i1])
    return None if not len(seg) else (i0 + seg[0]) * a.hop

overrides = {}
if a.overrides:
    overrides = {int(k): v for k, v in json.loads(pathlib.Path(a.overrides).read_text()).items()}
    print(f'{len(overrides)} hand-measured overrides', flush=True)

dur = song['durationSeconds']
report = []
for i, line in enumerate(lines):
    nxt = (overrides[i + 1]['t'] if i + 1 in overrides
           else lines[i + 1]['t'] if i + 1 < len(lines) else dur)
    old_end = line.get('end', nxt)
    is_echo = line['text'].strip().startswith('(')

    if i in overrides:
        o = overrides[i]
        line['t'], line['end'] = o['t'], o['end']
        if is_echo:
            line['echo'] = True
        report.append((i, old_end, line['end'], o.get('why', 'override')))
        continue

    if is_echo:
        # The echo answers the previous phrase: put it in the gap that phrase leaves.
        prev_end = lines[i - 1].get('end', line['t']) if i else line['t']
        start = min(prev_end + 0.18, max(prev_end, nxt - a.echo_hold - 0.25))
        end = min(start + a.echo_hold, nxt - 0.12)
        line['t'] = round(max(0.0, start), 2)
        line['end'] = round(max(line['t'] + 0.5, end), 2)
        line['echo'] = True
        report.append((i, old_end, line['end'], 'echo placed in response gap'))
        continue

    lv = last_voiced(line['t'], nxt)
    end = (lv + a.tail) if lv is not None else min(line['t'] + a.min_hold, nxt - 0.1)
    end = min(end, nxt - 0.08) if nxt > line['t'] + a.min_hold else min(end, nxt)
    end = max(end, min(line['t'] + a.min_hold, nxt - 0.05))
    end = min(end, line['t'] + a.max_hold)
    line['end'] = round(min(end, dur), 2)
    if abs(line['end'] - old_end) > 0.75:
        report.append((i, old_end, line['end'], f'trimmed {old_end - line["end"]:+.2f}s'))

song['timingSource'] = (song.get('timingSource', '') +
                        '; ends clamped to measured vocal activity')
print(f'\n{len(report)} lines changed by more than 0.75s:')
for i, o, nn, why in report:
    print(f'  {i:3} {o:7.2f} -> {nn:7.2f}  {why}   {lines[i]["text"][:44]}')

print('\nfinal timing:')
bad = 0
for i, l in enumerate(lines):
    nxt = lines[i + 1]['t'] if i + 1 < len(lines) else dur
    hold = l['end'] - l['t']
    warn = ''
    if l['end'] > nxt + 0.001:
        warn = '  <- OVERLAPS NEXT'; bad += 1
    if hold <= 0:
        warn += '  <- NON-POSITIVE'; bad += 1
    print(f"{i:3} {l['t']:7.2f} -> {l['end']:7.2f}  hold {hold:5.2f}s  "
          f"{l['section']:<9} {l['text'][:46]}{warn}")
print(f'\n{bad} problems')
if a.write and not bad:
    song_path.write_text(json.dumps(song, indent=2, ensure_ascii=False) + '\n')
    print(f'wrote {a.song}')
elif a.write:
    print('NOT written: fix the problems first')
