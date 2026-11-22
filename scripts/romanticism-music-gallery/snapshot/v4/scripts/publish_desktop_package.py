"""Place the fully checked local package on Desktop and preserve the old package."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
staged = ROOT / 'delivery/山、海、人间-YouTube上传'
desktop = Path('@USER_HOME@/Desktop')
destination = desktop / '山、海、人间-YouTube上传'
previous = desktop / '山海与人间-YouTube上传'

report = json.loads((staged / '资料/校验记录.json').read_text())
assert report['status'] == 'passed'
assert report['browser_package_review']['status'] == 'passed'
assert report['cover_visual_review'].startswith('Passed:')
assert report['labels']['picture_language'] == 'en'
assert all(item['identical_to_approved_audio'] for item in report['audio_unchanged'])
assert len(report['subtitles']['files']) == 6
for item in report['all_files']:
    file = staged / item['file']
    assert file.is_file() and not file.is_symlink()
    digest = hashlib.sha256()
    with file.open('rb') as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            digest.update(block)
    assert digest.hexdigest() == item['sha256'], file


def archive(folder, version):
    marker = folder / '资料/上传包信息.json'
    assert marker.is_file(), 'Do not move an unrelated Desktop folder.'
    information = json.loads(marker.read_text())
    assert information['project'] == 'romanticism-music-gallery'
    assert information['approved_version'] == version
    stamp = datetime.now(ZoneInfo('America/Los_Angeles')).strftime('%Y%m%d-%H%M%S')
    base = ROOT.parent / f'v{version}' / 'delivery-archive'
    base.mkdir(exist_ok=True)
    target = base / (folder.name + '-' + stamp)
    assert not target.exists()
    folder.rename(target)
    return str(target)


archived = []
if destination.exists():
    archived.append(archive(destination, 4))
staged.rename(destination)
if previous.exists():
    archived.append(archive(previous, 3))
record = json.loads((ROOT / 'checks/youtube-package.json').read_text())
record.update(path=str(destination), status='passed', prior_packages_preserved=archived)
(ROOT / 'checks/youtube-package.json').write_text(json.dumps(record, ensure_ascii=False, indent=2))
print(json.dumps({'status': 'passed', 'desktop_package': str(destination),
                  'prior_packages_preserved': archived,
                  'master_sha256': report['videos'][0]['sha256']}, ensure_ascii=False, indent=2))
