"""Preserve existing source clips and the revised checked narration takes."""
import json
import shutil
from common import ROOT,PUBLIC,DOCS,sha

BACKUP=ROOT.parent/'lucas-academy-video-data/science-shorts-20261106-v2'


def main():
    data=json.loads((PUBLIC/'data.json').read_text())
    inputs=[PUBLIC/asset['path'] for asset in data['assets'].values()]
    inputs+=[PUBLIC/name for name in ('data.json','timeline.perceptron.json','timeline.optogenetics.json')]
    inputs+=sorted((PUBLIC/'narration').rglob('*.wav'))
    assert len(inputs)==56
    for source in inputs:
        target=BACKUP/'public'/PUBLIC.name/source.relative_to(PUBLIC)
        target.parent.mkdir(parents=True,exist_ok=True)
        if target.exists():assert sha(target)==sha(source),'Refusing to overwrite changed input: '+str(target)
        else:shutil.copy2(source,target)
    shutil.copytree(DOCS,BACKUP/'records',dirs_exist_ok=True)
    restore='''"""Verify the complete backup before restoring selected production inputs."""
import hashlib,shutil,sys
from pathlib import Path
base=Path(__file__).resolve().parent
if len(sys.argv)!=2:raise SystemExit('Usage: python3 restore.py /path/to/lucas-academy-video')
target=Path(sys.argv[1]).resolve()
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for row in (base/'SHA256SUMS').read_text().splitlines():
 expected,name=row.split('  ',1)
 if digest(base/name)!=expected:raise SystemExit('Checksum failed: '+name)
sources=[p for p in (base/'public').rglob('*') if p.is_file()]
for source in sources:
 dest=target/'public'/source.relative_to(base/'public')
 if dest.exists() and digest(dest)!=digest(source):raise SystemExit('Refusing to overwrite differing file: '+str(dest))
for source in sources:
 dest=target/'public'/source.relative_to(base/'public');dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,dest)
print('Verified backup and restored',len(sources),'inputs to',target)
'''
    (BACKUP/'restore.py').write_text(restore)
    (BACKUP/'README.md').write_text('''# Perceptron and optogenetics vertical story shorts

Nine existing owner-made Muse clips, forty-four selected checked Louise WAVs, original-result-derived pixels/points/training paths and both narrated timelines. The perceptron closes with matrix multiplication rather than a QR; both films invite step-by-step learning at Lucas Academy. No new source-media download or generation was needed. Source clip audio is muted. Four approved full-film narration cues were reused exactly; the other selected cues were newly narrated locally. Selected retakes and ASR records are in records/. The v1 backup remains separate and untouched.

Run `python3 restore.py /absolute/path/to/lucas-academy-video`. It validates every SHA256 before writing and refuses differing existing inputs. With the code checkout present, run `python3 scripts/science-shorts/prepare.py --restored`, `.venv-align/bin/python scripts/science-shorts/mix.py`, and `node scripts/science-shorts/render.cjs --movie`. This route requires neither the original full-film public folders nor a voice-generation rerun. It preserves the same bilingual timing and external SRTs.
''')
    files=sorted(p for p in BACKUP.rglob('*') if p.is_file() and p.name!='SHA256SUMS')
    (BACKUP/'SHA256SUMS').write_text(''.join(f'{sha(p)}  {p.relative_to(BACKUP)}\n' for p in files))
    for row in (BACKUP/'SHA256SUMS').read_text().splitlines():
        expected,name=row.split('  ',1);assert sha(BACKUP/name)==expected
    print('Backed up and verified',len(files),'files:',BACKUP)


if __name__=='__main__':main()
