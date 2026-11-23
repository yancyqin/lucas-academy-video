"""Verify or restore the text-only archive of the published narrated Romanticism film."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
MANIFEST = REPO / 'docs/raindrop-romanticism/archive-manifest.json'


def sha(path):
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for part in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            value.update(part)
    return value.hexdigest()


def inside(root, name):
    relative = Path(name)
    if relative.is_absolute() or '..' in relative.parts:
        raise ValueError('Expected a contained relative path: ' + name)
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError('Path leaves its root: ' + name)
    return path


def verify():
    data = json.loads(MANIFEST.read_text())
    for item in data['files']:
        path = inside(REPO, item['snapshot'])
        if path.stat().st_size != item['bytes'] or sha(path) != item['sha256']:
            raise ValueError('Archive content differs: ' + item['snapshot'])
        inside(Path('/runtime'), item['runtime_path'])
    return data


def restore(root, apply=False):
    data = verify()
    root = root.resolve()
    if root.is_relative_to(REPO):
        raise ValueError('Restore media working data outside the Git checkout.')
    workspace = root.parent.parent
    tokens = {
        '@DATA_ROOT@': str(root), '@UI_ROOT@': str(workspace / 'inception-space-ui'),
        '@MEDIA_ROOT@': str(workspace / 'lucas-academy-media'),
        '@VIDEO_REPO@': str(REPO), '@PLAYGROUND@': str(workspace),
        '@USER_HOME@': str(Path.home()),
    }
    pending = []
    unchanged = 0
    for item in data['files']:
        target = inside(root, item['runtime_path'])
        text = inside(REPO, item['snapshot']).read_text()
        for key, value in tokens.items():
            text = text.replace(key, value)
        content = text.encode()
        if target.exists():
            if target.read_bytes() != content:
                raise ValueError('Existing file differs; use a new destination: ' + str(target))
            unchanged += 1
        else:
            pending.append((target, content))
    if apply:
        for target, content in pending:
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open('xb') as stream:
                stream.write(content)
    return {'mode': 'applied' if apply else 'dry run', 'missing_text_files': len(pending),
            'unchanged': unchanged, 'media_restored': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('verify')
    command = sub.add_parser('restore')
    command.add_argument('--data-root', type=Path, required=True)
    command.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    result = ({'status': 'passed', 'text_files': len(verify()['files'])}
              if args.command == 'verify' else restore(args.data_root, args.apply))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
