"""Plan or apply hash-checked deletion of explicitly identified film intermediates.

The caller supplies a local protection manifest. Source footage, approved voices,
final masters, other projects, and unrecognized files are kept. Git never stores
the local deletion plan or personal voice media.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil

VIDEO = {'.mp4', '.mov', '.m4v', '.webm', '.h264'}
AUDIO = {'.wav', '.m4a', '.mp3', '.aiff', '.aif', '.flac'}
ASSEMBLY = {'parts', 'pilot-parts', 'render-parts', 'stages', 'chapters'}
BACKUPS = {'previous-delivery', 'archived-desktop', 'before-upload', 'before-smooth', 'before-edit'}


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for part in iter(lambda: stream.read(8388608), b''):
            h.update(part)
    return h.hexdigest()


def resolve(root, name):
    relative = Path(name)
    if relative.is_absolute() or '..' in relative.parts:
        raise ValueError('Invalid relative path: ' + name)
    path = root / relative
    if path.is_symlink() or not path.resolve().is_relative_to(root):
        raise ValueError('Refusing symlink or out-of-root path: ' + name)
    return path


def reason(relative):
    dirs = set(relative.parts[:-1])
    suffix = relative.suffix.lower()
    if '__pycache__' in dirs and suffix == '.pyc':
        return 'Reproducible Python bytecode'
    if dirs & ASSEMBLY and suffix in VIDEO:
        return 'Encoded assembly intermediate'
    if 'exports' in dirs and suffix in VIDEO:
        return 'Superseded picture export; current master protected separately'
    if dirs & BACKUPS and suffix in VIDEO | AUDIO:
        return 'Superseded delivery backup; approved inputs protected separately'
    if 'raw' in dirs and suffix == '.h264':
        return 'Annex-B duplicate of retained native MP4 capture'
    if 'raw' in dirs and dirs & {'superseded-tail', 'before-art-arrivals'} and suffix in VIDEO:
        return 'Superseded native camera take'
    if relative.parts[:2] in [('production', 'v10'), ('production', 'v11')] and 'delivery' in dirs and suffix in VIDEO:
        return 'Superseded narrated master or preview'
    if relative.parts[:3] == ('production', 'v12', 'inserts') and suffix in VIDEO:
        return 'Rebuildable 60 fps insert or portrait render'
    if relative.parts[:3] == ('production', 'v12', 'delivery') and suffix in VIDEO and relative.name != '01-English-full.mp4':
        return 'Short motion-check preview'
    return None


def plan(root, protection):
    root = root.resolve()
    protected = json.loads(protection.read_text())['files']
    candidates = []
    for file in root.rglob('*'):
        if not file.is_file() or file.is_symlink():
            continue
        name = file.relative_to(root).as_posix()
        if name in protected:
            continue
        why = reason(Path(name))
        if why:
            candidates.append({'file': name, 'bytes': file.stat().st_size,
                               'sha256': sha(file), 'reason': why})
    return {'data_root': str(root), 'protection': str(protection.resolve()),
            'created_at': datetime.now(timezone.utc).isoformat(),
            'candidates': candidates, 'candidate_files': len(candidates),
            'logical_bytes': sum(c['bytes'] for c in candidates),
            'note': 'Logical bytes; hard links and APFS clones can share physical storage.'}


def apply(manifest):
    data = json.loads(manifest.read_text())
    root = Path(data['data_root']).resolve()
    protected = json.loads(Path(data['protection']).read_text())['files']
    # Check every candidate and protected input before the first deletion.
    for name, digest in protected.items():
        path = root / name
        if not path.is_file() or sha(path) != digest:
            raise ValueError('Protected input changed/missing: ' + name)
    for item in data['candidates']:
        path = resolve(root, item['file'])
        if item['file'] in protected or reason(Path(item['file'])) != item['reason']:
            raise ValueError('Not an authorized candidate: ' + item['file'])
        if path.stat().st_size != item['bytes'] or sha(path) != item['sha256']:
            raise ValueError('Candidate changed after inventory: ' + item['file'])
    free_before = shutil.disk_usage(root).free
    for item in data['candidates']:
        resolve(root, item['file']).unlink()
    for name, digest in protected.items():
        if sha(root / name) != digest:
            raise ValueError('Protected input changed during cleanup: ' + name)
    return {'state': 'complete', 'deleted_files': data['candidate_files'],
            'deleted_logical_bytes': data['logical_bytes'],
            'volume_free_before': free_before, 'volume_free_after': shutil.disk_usage(root).free,
            'protected_files_verified': len(protected), 'source_code_deleted': False,
            'completed_at': datetime.now(timezone.utc).isoformat()}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    commands = p.add_subparsers(dest='command', required=True)
    inventory = commands.add_parser('plan')
    inventory.add_argument('--data-root', required=True, type=Path)
    inventory.add_argument('--protection', required=True, type=Path)
    inventory.add_argument('--output', required=True, type=Path)
    deletion = commands.add_parser('apply')
    deletion.add_argument('--plan', required=True, type=Path)
    deletion.add_argument('--output', required=True, type=Path)
    a = p.parse_args()
    if a.command == 'plan':
        data = plan(a.data_root, a.protection)
        a.output.write_text(json.dumps(data, ensure_ascii=False, indent=2))
        print(json.dumps({k: v for k, v in data.items() if k != 'candidates'}, indent=2))
    else:
        data = apply(a.plan)
        a.output.write_text(json.dumps(data, indent=2))
        print(json.dumps(data, indent=2))


if __name__ == '__main__':
    main()
