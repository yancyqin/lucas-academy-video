"""Replace the upload dub and its external Chinese captions as one reviewed set."""
from pathlib import Path
import hashlib
import json
import shutil

from youtube_package import DUB, DEST, export_dub
from youtube_metadata import read_mandarin_cues, validate_cues, srt, ZH_SUBTITLES

P = Path(__file__).resolve().parent


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    plan = json.loads((P / 'edit-plan.json').read_text())
    report = json.loads((P / 'checks/fangfang-mandarin-content-qa.json').read_text())
    script = json.loads((P / 'voices/fangfang-mandarin.json').read_text())
    assert len(script['lines']) == len(report['takes']) == 52
    for line in script['lines']:
        record = report['takes'][line['id']]
        assert record['sha256'] == digest(P / 'voices/fangfang-mandarin' / (line['id'] + '.wav'))
        assert record['score'] >= .90 or record.get('reviewed'), (line['id'], record)

    preserved = {p.name: digest(p) for p in DEST.iterdir()
                 if p.is_file() and p.suffix in ('.mp4', '.jpg', '.docx')}
    archive = P / 'archive/tingting-upload-preview'
    archive.mkdir(parents=True, exist_ok=True)
    previous = DEST / '02-压力焦虑肖邦浪漫-普通话音轨.wav'
    receipt = P / 'checks/youtube-mandarin-qa.json'
    if previous.is_file():
        shutil.copy2(previous, archive / previous.name)
        shutil.copy2(ZH_SUBTITLES, archive / ZH_SUBTITLES.name)
        shutil.copy2(receipt, archive / receipt.name)

    # Validate all new captions before replacing either delivery file.
    cues = read_mandarin_cues(plan)
    validate_cues(cues, plan, 'text_zh')
    captions = ZH_SUBTITLES.with_suffix('.incoming.srt')
    captions.write_text(srt(cues), encoding='utf-8')
    export_dub(plan)
    captions.replace(ZH_SUBTITLES)
    if previous.exists():
        assert digest(previous) == digest(archive / previous.name)
        previous.unlink()

    credits_path = P / 'sources-and-credits.json'
    credits = json.loads(credits_path.read_text())
    voices = credits['narration']['voices']
    if not any(v['name'] == 'Fangfang' and v['language'] == 'zh' for v in voices):
        voices.append(dict(name='Fangfang', language='zh', speed=1.2, profile='fangfang/zh'))
    credits['narration']['upload_package'] = dict(
        default_video='Louise English', separate_audio='Fangfang Mandarin',
        mandarin_file=DUB.name, mandarin_script='voices/fangfang-mandarin.json')
    credits_path.write_text(json.dumps(credits, ensure_ascii=False, indent=2) + '\n')
    assert all(digest(DEST / name) == value for name, value in preserved.items())
    print('Fangfang Mandarin dub and Chinese SRT updated; other upload files preserved', flush=True)


if __name__ == '__main__':
    main()
