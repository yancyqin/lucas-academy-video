"""Back up the production inputs and every immutable raw narration take."""
from pathlib import Path
import hashlib
import json
import shutil

ROOT=Path(__file__).resolve().parents[2]
BACKUP=ROOT.parent/'lucas-academy-video-data/family-ai-lab-02'


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    BACKUP.mkdir(parents=True,exist_ok=True)
    shutil.copytree(ROOT/'public/family-ai-lab-02',BACKUP/'public/family-ai-lab-02',dirs_exist_ok=True)
    shutil.copytree(ROOT/'docs/family-ai-lab-02',BACKUP/'records',dirs_exist_ok=True)
    for series in ('v1','v2'):
        for lang in ('en','zh'):
            folder=ROOT.parent/f'lucas-academy-media/outputs/louise/{lang}/family-ai-lab-02-{series}'
            if not folder.exists():continue
            for p in folder.glob('s*/*'):
                if not p.is_file() or p.suffix not in ('.wav','.json'):continue
                category='raw-narration' if series=='v1' else 'raw-narration-v2'
                target=BACKUP/f'{category}/{lang}'
                if p.parent.name!='s1.10':target=target/p.parent.name
                dest=target/p.name;dest.parent.mkdir(parents=True,exist_ok=True)
                if dest.exists():assert sha(dest)==sha(p),('Immutable take differs',dest)
                else:shutil.copy2(p,dest)
    for name in ('audio','narration','orbital-v2/audio'):
        for p in (ROOT/f'out/family-ai-lab-02/{name}').rglob('*.json'):
            dest=BACKUP/'checks'/name/p.relative_to(ROOT/f'out/family-ai-lab-02/{name}');dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
    (BACKUP/'README.md').write_text('''# Family AI Lab — The tiny pipe

`public/` contains the frozen original course inputs, curriculum artwork, worksheets, actual browser recording and capture receipt, derived code/guessing facts, QR, original imagegen plates, six intact Muse originals, editing derivatives, shared voiced timelines and all selected Louise WAVs. `raw-narration/` and `raw-narration-v2/` retain every original/replacement take with its settings and SHA receipts. Differing raw takes are never overwritten. `records/` and `checks/` preserve scripts, provenance, selected decisions, ASR transcripts, word times and loudness/ducking reports.

Restore with `python3 restore.py /absolute/path/to/video-checkout`. All SHA256SUMS are verified before copying; a differing existing destination refuses the entire restore. Rebuild the current orbital film with `npm run fal02:orbital:build`, `npm run fal02:orbital:mix`, `npm run fal02:orbital:final`, `npm run fal02:orbital:check`. The restored editing derivatives avoid an unnecessary retranscode; `fal02:orbital:clips` can recreate them from the six preserved Muse originals. Selected WAVs need no private voice profile. Original procedural music and sound effects are rebuilt from the committed recipe; no external songs or samples are involved. Historical v1 commands and inputs remain available in the checkout.
''')
    (BACKUP/'restore.py').write_text('''from pathlib import Path
import hashlib,shutil,sys
base=Path(__file__).resolve().parent
if len(sys.argv)!=2:raise SystemExit('Usage: python3 restore.py /absolute/path/to/video-checkout')
target=Path(sys.argv[1]).resolve()
for row in (base/'SHA256SUMS').read_text().splitlines():
    digest,name=row.split('  ',1)
    if hashlib.sha256((base/name).read_bytes()).hexdigest()!=digest:raise SystemExit('Checksum failed: '+name)
files=[p for p in (base/'public').rglob('*') if p.is_file()]
for p in files:
    dest=target/'public'/p.relative_to(base/'public')
    if dest.exists() and dest.read_bytes()!=p.read_bytes():raise SystemExit('Refusing differing file: '+str(dest))
for p in files:
    dest=target/'public'/p.relative_to(base/'public');dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
print('Verified and restored',len(files),'public inputs to',target)
''')
    files=sorted(p for p in BACKUP.rglob('*') if p.is_file() and p.name!='SHA256SUMS')
    rows=[sha(p)+'  '+str(p.relative_to(BACKUP)) for p in files]
    (BACKUP/'SHA256SUMS').write_text('\n'.join(rows)+'\n')
    for row in rows:
        digest,name=row.split('  ',1);assert sha(BACKUP/name)==digest
    print('Backed up and hash-verified',len(files),'files:',BACKUP)


if __name__=='__main__':main()
