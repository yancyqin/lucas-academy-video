"""Verify/restore the text production archive and inventory local cleanup candidates.

No operation deletes media, downloads assets, uploads files, or changes visibility.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
DOCS = REPO / 'docs/romanticism-music-gallery'
MANIFEST = DOCS / 'archive-manifest.json'


def sha(path: Path) -> str:
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            value.update(chunk)
    return value.hexdigest()


def contained(root: Path, relative: str) -> Path:
    path = (root / relative).resolve()
    if not path.is_relative_to(root):
        raise ValueError('Path leaves its root: ' + relative)
    return path


def verify() -> dict:
    manifest = json.loads(MANIFEST.read_text())
    for entry in manifest['files']:
        path = contained(REPO, entry['snapshot'])
        if not path.is_file() or path.stat().st_size != entry['bytes'] or sha(path) != entry['sha256']:
            raise ValueError('Archive file changed or missing: ' + entry['snapshot'])
        contained(Path('/runtime'), entry['runtime_path'])
    for entry in manifest['skill_files']:
        path = contained(REPO, entry['file'])
        if not path.is_file() or sha(path) != entry['sha256']:
            raise ValueError('Skill file changed or missing: ' + entry['file'])
    return manifest


def restore(args) -> dict:
    manifest = verify()
    destination = args.data_root.resolve()
    if destination.is_relative_to(REPO):
        raise ValueError('Restore working data outside the video Git checkout.')
    playground = destination.parent.parent
    ui_root = playground / 'inception-space-ui'
    # Several original capture scripts resolve siblings relative to DATA_ROOT.
    # Reject a misleading override rather than silently pointing them elsewhere.
    if args.playground and args.playground.resolve() != playground:
        raise ValueError('The archived scripts require the data root two levels below the workspace.')
    if args.ui_root and args.ui_root.resolve() != ui_root:
        raise ValueError('The archived scripts require inception-space-ui in the same workspace.')
    replacements = {
        '@DATA_ROOT@': str(destination),
        '@UI_ROOT@': str(ui_root),
        '@VIDEO_REPO@': str(REPO),
        '@RUNTIME_DEPS@': str(args.runtime_deps.resolve()),
        '@PLAYGROUND@': str(playground),
        '@USER_HOME@': str(Path.home()),
    }
    pending = []
    unchanged = 0
    for entry in manifest['files']:
        target = contained(destination, entry['runtime_path'])
        text = contained(REPO, entry['snapshot']).read_text()
        for token, value in replacements.items():
            text = text.replace(token, value)
        encoded = text.encode('utf-8')
        if target.exists():
            if not target.is_file() or target.read_bytes() != encoded:
                raise ValueError('Existing file differs; restore to a new folder: ' + str(target))
            unchanged += 1
        else:
            pending.append((target, encoded))
    if args.apply:
        for target, encoded in pending:
            target.parent.mkdir(parents=True, exist_ok=True)
            # Exclusive creation also protects against a file appearing after preflight.
            with target.open('xb') as stream:
                stream.write(encoded)
        roots = ['', 'v3', 'v4', 'shorts/01-vastness']
        batch = json.loads((destination / 'shorts/batch-20261121/batch.json').read_text())
        roots += [str(Path(job['root']).relative_to(destination)) for job in batch['jobs']]
        for relative in roots:
            for folder in ['labels', 'parts', 'footage', 'exports', 'checks', 'sources', 'subtitles']:
                (destination / relative / folder).mkdir(parents=True, exist_ok=True)
    return {'mode': 'applied' if args.apply else 'dry run', 'destination': str(destination),
            'new_text_files': len(pending), 'unchanged_text_files': unchanged,
            'media_restored': False, 'existing_files_overwritten': False}


def inventory(args) -> dict:
    root = args.data_root.resolve()
    if not root.is_dir():
        raise ValueError('Missing data root: ' + str(root))
    candidates, protected = [], []
    for path in sorted(root.rglob('*')):
        if path.is_symlink() or not path.is_file():
            continue
        relative = path.relative_to(root)
        entry = {'file': relative.as_posix(), 'bytes': path.stat().st_size}
        # Encoded picture intermediates and old chapter assembly are reproducible
        # only while the source captures, recordings and approved v3 exports remain.
        if 'parts' in relative.parts or relative.parts[0] in ['stages', 'chapters']:
            entry['reason'] = 'Rebuildable assembly intermediate; preserve its source captures and approved audio first.'
            candidates.append(entry)
        elif '__pycache__' in relative.parts:
            entry['reason'] = 'Python bytecode cache.'
            candidates.append(entry)
        else:
            protected.append(entry)
    folders = {}
    for item in candidates:
        parts = Path(item['file']).parts
        if '__pycache__' in parts:
            prefix = Path(*parts[:parts.index('__pycache__') + 1]).as_posix()
        elif 'parts' in parts:
            prefix = Path(*parts[:parts.index('parts') + 1]).as_posix()
        else:
            prefix = parts[0]
        row = folders.setdefault(prefix, {'folder': prefix, 'files': 0, 'bytes': 0})
        row['files'] += 1
        row['bytes'] += item['bytes']
    report = {'mode': 'read-only inventory; nothing deleted', 'data_root': str(root),
              'candidate_files': len(candidates), 'candidate_logical_bytes': sum(x['bytes'] for x in candidates),
              'protected_files': len(protected), 'protected_logical_bytes': sum(x['bytes'] for x in protected),
              'candidate_folders': sorted(folders.values(), key=lambda x: x['folder']),
              'candidates': candidates, 'protected': protected,
              'space_note': 'Logical file sizes; APFS clones/hard links can share storage. This is not a physical reclaim estimate.',
              'cleanup_gates': ['Merge and verify the video PR before removing code copies.',
                                'Keep v3/exports: v4/finish.py copies its approved AAC streams.',
                                'Keep v4/exports, original art/music/footage, assets and Desktop upload packages.',
                                'Keep the native gallery captures until matching inception-space-ui source is committed.',
                                'Keep cross-project Muse inserts and the separate narrated-film project.']}
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    return {key: value for key, value in report.items() if key not in ['candidates', 'protected']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('verify')
    restore_parser = sub.add_parser('restore', help='Restore text/scripts only; refuses to overwrite different files.')
    restore_parser.add_argument('--data-root', type=Path, required=True)
    restore_parser.add_argument('--ui-root', type=Path, help='Must match the canonical UI sibling in the original workspace layout.')
    restore_parser.add_argument('--playground', type=Path)
    restore_parser.add_argument('--runtime-deps', type=Path, default=Path.home() / '.cache/codex-runtimes/codex-primary-runtime/dependencies')
    restore_parser.add_argument('--apply', action='store_true', help='Write missing text files after preflight; default is dry run.')
    inventory_parser = sub.add_parser('inventory', help='List cleanup candidates; never delete them.')
    inventory_parser.add_argument('--data-root', type=Path, required=True)
    inventory_parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.command == 'verify':
        manifest = verify()
        result = {'status': 'passed', 'runtime_text_files': len(manifest['files']),
                  'skill_files': len(manifest['skill_files'])}
    elif args.command == 'restore':
        result = restore(args)
    else:
        result = inventory(args)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
