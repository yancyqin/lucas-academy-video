"""Back up inputs locally, preserving the original selected experiment round."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[2]
BACKUP = ROOT.parent / "lucas-academy-video-data/family-ai-lab-01"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    BACKUP.mkdir(parents=True, exist_ok=True)
    baseline = BACKUP / "baseline-results"
    baseline.mkdir(exist_ok=True)
    for p in (ROOT / "scripts/perceptron-race/results").iterdir():
        if p.is_file():
            dest = baseline / p.name
            if dest.exists() and sha(p) != sha(dest):
                raise RuntimeError("Original baseline differs from preserved baseline: " + p.name)
            if not dest.exists():
                shutil.copy2(p, dest)
    shutil.copytree(ROOT / "public/family-ai-lab-01", BACKUP / "public/family-ai-lab-01", dirs_exist_ok=True)
    shutil.copytree(ROOT / "docs/family-ai-lab-01", BACKUP / "records", dirs_exist_ok=True)
    for folder in ('narration', 'audio'):
        source = ROOT / 'out/family-ai-lab-01' / folder
        if source.exists():
            for p in source.glob('*.json'):
                dest = BACKUP / 'checks' / folder / p.name
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(p, dest)
    restore = '''#!/usr/bin/env python3
"""Restore backed-up media into a video checkout; refuse differing existing files."""
from pathlib import Path
import sys, shutil, hashlib
base=Path(__file__).resolve().parent
if len(sys.argv)!=2: raise SystemExit("Usage: python3 restore.py /absolute/path/to/lucas-academy-video")
target=Path(sys.argv[1]).resolve()
for row in (base/'SHA256SUMS').read_text().splitlines():
    digest,name=row.split('  ',1)
    source=base/name
    if hashlib.sha256(source.read_bytes()).hexdigest()!=digest: raise SystemExit('Checksum failed: '+name)
for source in (base/'public').rglob('*'):
    if not source.is_file(): continue
    dest=target/'public'/source.relative_to(base/'public')
    if dest.exists() and dest.read_bytes()!=source.read_bytes(): raise SystemExit('Refusing to replace differing file: '+str(dest))
for source in (base/'public').rglob('*'):
    if source.is_file():
        dest=target/'public'/source.relative_to(base/'public');dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,dest)
print('Verified and restored',target/'public/family-ai-lab-01')
'''
    (BACKUP / "restore.py").write_text(restore)
    (BACKUP / "README.md").write_text("""# Family AI Lab 01 — local production inputs

Owner-selected original full experiment round; later timing reruns are preserved separately and excluded from the film.

`public/family-ai-lab-01/` contains the three owner-supplied Muse originals, three original built-in ImageGen cover backgrounds and later versioned cover candidates, curriculum snapshots, original browser/terminal recordings, derived capture crops, the live lab QR code, actual 419-picture training sprites, trained-state restoration, common bilingual timeline and 152 selected Louise narration WAVs with hashes. Narration is generated locally with CosyVoice at 1.1 speed. No Suno media was downloaded or used.

`records/` preserves scripts, prompts, source attribution, selected narration decisions, the capture adapter description and selected-data hashes. Later cover/copy review drafts are recorded separately; they do not imply that a new film has been rendered. `checks/` preserves raw Whisper transcripts and audio loudness measurements. `baseline-results/` is immutable: backup refuses a differing original experiment file.

Restore into an empty directory or checkout using `python3 restore.py /absolute/path/to/lucas-academy-video`. It verifies all hashes before copying and refuses differing destination files. Then run `npm run fal01:timeline:voiced`, `npm run fal01:voice:mix`, `npm run fal01:final` to rebuild the narrated film from selected takes. The backed-up generation outputs remain irreplaceable.
""")
    files = sorted(p for p in BACKUP.rglob("*") if p.is_file() and p.name != "SHA256SUMS")
    (BACKUP / "SHA256SUMS").write_text("".join(sha(p) + "  " + str(p.relative_to(BACKUP)) + "\n" for p in files))
    for p in files:
        assert sha(p) == dict((name, digest) for digest, name in (row.split("  ", 1) for row in (BACKUP / "SHA256SUMS").read_text().splitlines()))[str(p.relative_to(BACKUP))]
    print("Backed up and verified", len(files), "files:", BACKUP)


if __name__ == "__main__":
    main()
