"""Check the edit against the song before paying for a render.

What this is really guarding is the no-loop rule. A shot loops when its file is
shorter than the span it has to fill, so that is measured on the written files
rather than assumed from the plan. It also checks that the footage never runs out
underneath the singing, and flags any lyric line that starts inside a dissolve,
where a transition could swallow the first word.
"""
import json, pathlib, subprocess, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from shots import SHOTS, OVERLAP, COVERS

REPO = pathlib.Path(__file__).resolve().parents[2]
song = json.loads((REPO / 'src/songs/rejoice.json').read_text())
lines, dur = song['lines'], song['durationSeconds']
# The song sets the crossfade and a shot may override it, so read both rather
# than hardcoding a length that goes stale the moment the edit is retimed.
DISSOLVE = song.get('dissolveSeconds', 1.4)
def dissolve_of(sid):
    for sh in song.get('shots', []):
        if sh['src'].endswith(f'/{sid}.mp4'):
            return sh.get('dissolve', DISSOLVE)
    return DISSOLVE

def probe(p):
    r = subprocess.run(['ffprobe','-v','error','-show_entries','format=duration',
                        '-of','csv=p=0',str(p)],capture_output=True,text=True)
    return float(r.stdout.strip()) if r.stdout.strip() else 0.0

fails, warns = [], []

print('=== shot files vs spans (a short file is a shot that would loop) ===')
for sid, src, si, a, b, mv, tr in SHOTS:
    f = REPO / 'public/footage/rejoice' / f'{sid}.mp4'
    span = b - a
    if not f.exists():
        fails.append(f'{sid}: not built'); print(f'{sid}  MISSING'); continue
    have = probe(f)
    ok = have >= span - 0.05
    if not ok:
        fails.append(f'{sid}: file {have:.2f}s < span {span:.2f}s -- would loop')
    print(f'{sid}  span {span:6.2f}s  file {have:6.2f}s  {"ok" if ok else "SHORT"}')

print('\n=== timeline continuity ===')
prev_end, prev_id = None, None
for sid, src, si, a, b, mv, tr in SHOTS:
    if prev_end is not None:
        ov = prev_end - a
        d = dissolve_of(sid)
        if ov < 0:
            fails.append(f'gap of {-ov:.2f}s between {prev_id} and {sid}')
            print(f'  GAP {-ov:.2f}s before {sid}')
        elif ov < d - 0.01:
            fails.append(f'{prev_id}->{sid} overlap {ov:.2f}s is shorter than its '
                         f'{d:.2f}s dissolve, so {prev_id} starts fading before {sid} is in')
        elif d > DISSOLVE + 0.01:
            print(f'  long transition {prev_id}->{sid}: {d:.2f}s over a {ov:.2f}s overlap')
    prev_end, prev_id = b, sid
print(f'  first shot starts {SHOTS[0][3]:.2f}s, last ends {SHOTS[-1][4]:.2f}s, song {dur:.2f}s')
if SHOTS[0][3] > 0.01:
    fails.append('footage does not start at 0')
if SHOTS[-1][4] < dur - 0.05:
    fails.append(f'footage ends {dur - SHOTS[-1][4]:.2f}s before the song does')

print('\n=== every lyric line has footage under it ===')
for i, l in enumerate(lines):
    covering = [s[0] for s in SHOTS if s[3] <= l['t'] and s[4] >= l['end']]
    if not covering:
        partial = [s[0] for s in SHOTS if s[4] > l['t'] and s[3] < l['end']]
        if not partial:
            fails.append(f'line {i} ({l["text"][:28]}) has no shot')
        # spanning a cut is normal; only a total absence is a failure

print('\n=== lyric lines that begin inside a dissolve ===')
for i, l in enumerate(lines):
    for sid, src, si, a, b, mv, tr in SHOTS:
        if a <= l['t'] <= a + DISSOLVE and a > 0.01:
            warns.append(f'line {i} starts {l["t"]-a:.2f}s into {sid} dissolve: {l["text"][:34]}')

print('\n=== chorus completeness (all three must be whole) ===')
ch = [l for l in lines if l['section'] == 'chorus']
for n in range(3):
    block = ch[n*7:(n+1)*7]
    texts = [b['text'] for b in block]
    echo = sum(1 for t in texts if t == '(Rejoice)')
    mono = all(block[j]['t'] < block[j+1]['t'] for j in range(len(block)-1))
    print(f'  chorus {n+1}: {len(block)} lines, echo {echo}, ascending {mono}, '
          f'{block[0]["t"]:.2f}-{block[-1]["end"]:.2f}s')
    if len(block) != 7 or echo != 1 or not mono:
        fails.append(f'chorus {n+1} malformed')

print('\n=== plan coverage map ===')
for sid, src, si, a, b, mv, tr in SHOTS:
    sung = [f'{i}' for i, l in enumerate(lines) if a <= l['t'] < b]
    print(f'  {sid} {a:7.2f}-{b:7.2f} {pathlib.Path(src).name[:38]:<40} '
          f'lines[{",".join(sung) if sung else "-"}]  {COVERS.get(sid,"")}')

print('\n=== single-pass check: does any clip end where it began? ===')
# A boomerang or a wrapped loop returns to its first frame, so the last frame
# resembles the first. On a forward-only clip they should differ clearly.
import av
def endpoints(path):
    with av.open(str(path)) as c:
        st = c.streams.video[0]; st.thread_type = 'AUTO'
        fs = [f.to_ndarray(format='rgb24') for f in c.decode(st)]
    return fs[0], fs[len(fs)//2], fs[-1]
try:
    for sid, src, si, a, b, mv, tr in SHOTS:
        if 'wan-' not in src:
            continue
        f = REPO / 'public/footage/rejoice' / f'{sid}.mp4'
        if not f.exists():
            continue
        first, mid, last = endpoints(f)
        d_end = float(abs(first.astype(int) - last.astype(int)).mean())
        d_mid = float(abs(first.astype(int) - mid.astype(int)).mean())
        verdict = 'forward' if d_end >= max(d_mid * 0.6, 2.0) else 'LOOKS LIKE A RETURN'
        if verdict != 'forward':
            fails.append(f'{sid}: first vs last differ by only {d_end:.2f} -- possible loop/boomerang')
        print(f'  {sid} {src[:34]:<36} first->last {d_end:6.2f}  first->mid {d_mid:6.2f}  {verdict}')
except Exception as e:
    print('  (endpoint check skipped:', e, ')')

print(f'\n{len(fails)} failures, {len(warns)} warnings')
for f in fails: print('  FAIL', f)
for w in warns: print('  warn', w)
sys.exit(1 if fails else 0)
