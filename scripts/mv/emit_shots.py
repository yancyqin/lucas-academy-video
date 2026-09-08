"""Write the shot list into the song JSON that Remotion imports.

shots.py is the single source of truth for the edit; this copies it into
src/songs/rejoice.json so the renderer never re-derives timings of its own.
"""
import json, pathlib, subprocess, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from shots import SHOTS

REPO = pathlib.Path(__file__).resolve().parents[2]
song_path = REPO / 'src/songs/rejoice.json'
song = json.loads(song_path.read_text())

out, problems = [], []
for sid, src, src_in, start, end, move, tr in SHOTS:
    f = REPO / 'public/footage/rejoice' / f'{sid}.mp4'
    shot = {'src': f'footage/rejoice/{sid}.mp4', 'start': start, 'end': end,
            'move': 'none' if tr.get('still') else move}
    if tr.get('lightRamp'):
        shot['lightRamp'] = True
    if tr.get('blurRamp'):
        shot['blurRamp'] = list(tr['blurRamp'])
    if tr.get('dissolve'):
        shot['dissolve'] = tr['dissolve']
    if tr.get('fadeIn'):
        shot['fadeIn'] = list(tr['fadeIn'])
    if tr.get('fadeOut'):
        shot['fadeOut'] = tr['fadeOut']
    if tr.get('tailZoom'):
        shot['tailZoom'] = {'seconds': tr['tailZoom'][0], 'to': tr['tailZoom'][1]}
    if not f.exists():
        problems.append(f'{sid}: {f.name} not built yet')
    else:
        have = float(subprocess.run(['ffprobe','-v','error','-show_entries','format=duration',
                                     '-of','csv=p=0',str(f)],capture_output=True,text=True).stdout)
        if have < (end - start) - 0.05:
            problems.append(f'{sid}: file {have:.2f}s shorter than span {end-start:.2f}s')
    out.append(shot)

song['shots'] = out
song['lyricAnchor'] = 'lower'
song_path.write_text(json.dumps(song, indent=2, ensure_ascii=False) + '\n')
print(f'wrote {len(out)} shots into src/songs/rejoice.json')
for p in problems:
    print('  !', p)
print(f'{len(problems)} problems')
