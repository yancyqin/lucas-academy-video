"""Print the edit decision list: time range, lyrics, source, treatment.

One row per shot, generated from shots.py and the song JSON so it can never drift
from what actually rendered.
"""
import json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from shots import SHOTS, COVERS

REPO = pathlib.Path(__file__).resolve().parents[2]
song = json.loads((REPO / 'src/songs/rejoice.json').read_text())
lines = song['lines']

def mmss(t): return f"{int(t)//60}:{t%60:05.2f}"

print("| # | 时间段 | 歌词 | 素材 (取用点) | 处理 |")
print("|---|---|---|---|---|")
for sid, src, si, a, b, mv, tr in SHOTS:
    covered = [l for l in lines if a - 0.35 <= l['t'] < b - 0.35]
    lyr = "<br>".join(
        ("*(回声)* " if l.get('echo') else "") + l['text'] for l in covered
    ) or "—（器乐）"
    bits = []
    if tr.get('still'):
        z = tr.get('zoom'); bits.append(f"静帧 Ken Burns {z[0]}→{z[1]}")
    else:
        bits.append({'in':'慢推','out':'Zoom out','left':'左移','right':'右移',
                     'up':'上移','none':'不动'}[mv])
    if tr.get('fog'):  bits.append(f"雾 {tr['fog']}")
    if tr.get('exposure') is not None: bits.append(f"曝光 {tr['exposure']}")
    if tr.get('lightRamp'): bits.append("金光 ramp")
    print(f"| {sid} | {mmss(a)}–{mmss(b)} | {lyr} | `{src}` @{si}s | {', '.join(bits)} |")
