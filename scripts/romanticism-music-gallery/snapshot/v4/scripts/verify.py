"""Check rendered v4 picture, exact complete audio, labels and external SRTs."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import concurrent.futures
import hashlib
import json
import math
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
FF = '/opt/homebrew/bin/ffmpeg'
FP = '/opt/homebrew/bin/ffprobe'
plan = json.loads((ROOT / 'edit-plan.json').read_text())
master = ROOT / 'exports/山、海、人间-纯英文纯音乐版.mp4'
files = [
    (master, plan['duration'], '山海与人间-中英标签纯音乐版.mp4'),
    (ROOT / 'exports/自然篇-肖邦-纯英文版.mp4', plan['tracks'][2]['end'], '自然篇-肖邦-中英标签版.mp4'),
    (ROOT / 'exports/人间篇-贝多芬-纯英文版.mp4', plan['duration']-plan['tracks'][3]['start'], '人间篇-贝多芬-中英标签版.mp4'),
]
result = {'files': []}
for file, expected, previous in files:
    probe = json.loads(subprocess.check_output([FP, '-v', 'error', '-show_format', '-show_streams', '-show_chapters', '-of', 'json', str(file)]))
    video = [s for s in probe['streams'] if s['codec_type'] == 'video']
    audio = [s for s in probe['streams'] if s['codec_type'] == 'audio']
    assert len(video) == len(audio) == 1
    # MP4 chapter metadata may add a data stream; subtitles remain external.
    assert not [s for s in probe['streams'] if s['codec_type'] == 'subtitle']
    assert (video[0]['width'], video[0]['height'], video[0]['r_frame_rate']) == (1920, 1080, '24/1')
    assert abs(float(probe['format']['duration']) - expected) < .06
    for chapter in probe['chapters']:
        assert not re.search(r'[\u3400-\u9fff]', chapter['tags']['title'])
    assert not re.search(r'[\u3400-\u9fff]', probe['format']['tags']['title'])
    if file == master:
        assert len(probe['chapters']) == 5
        for chapter, track in zip(probe['chapters'], plan['tracks']):
            assert abs(float(chapter['start_time'])-track['start']) < .002
    result['files'].append(dict(file=file.name, bytes=file.stat().st_size,
                               duration=float(probe['format']['duration']), width=1920,
                               height=1080, fps=24, chapters=len(probe['chapters']),
                               picture_language='en', audio=audio[0]['codec_name']))
print('PROBES PASSED', flush=True)

with (ROOT / 'checks/master-decode.log').open('w') as errors:
    subprocess.run([FF, '-hide_banner', '-v', 'error', '-i', str(master), '-map', '0:v', '-map', '0:a', '-f', 'null', '-'],
                   check=True, stderr=errors, stdout=subprocess.DEVNULL)
assert not (ROOT / 'checks/master-decode.log').read_text().strip()
result['full_master_decode'] = 'passed'
print('FULL DECODE PASSED', flush=True)


def stream_hash(file):
    digest = hashlib.sha256()
    process = subprocess.Popen([FF, '-hide_banner', '-v', 'error', '-i', str(file),
                                '-map', '0:a:0', '-c:a', 'copy', '-f', 'adts', '-'], stdout=subprocess.PIPE)
    for block in iter(lambda: process.stdout.read(1024 * 1024), b''):
        digest.update(block)
    assert process.wait() == 0
    return digest.hexdigest()


audio_checks = []
for file, _, previous in files:
    approved = ROOT.parent / 'v3/exports' / previous
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        actual, expected = list(pool.map(stream_hash, [file, approved]))
    assert actual == expected, (file, actual, expected)
    audio_checks.append(dict(file=file.name, identical_to_approved_audio=True, aac_payload_sha256=actual))
result['audio_streams_unchanged'] = audio_checks
result['audio_policy'] = 'All five complete recordings retained. Master and both parts have byte-identical AAC audio to the approved v3 exports.'
for track in plan['tracks']:
    assert hashlib.sha256(Path(track['file']).read_bytes()).hexdigest() == track['sha256']
result['source_recordings_hash_verified'] = 5
print('ALL THREE AUDIO STREAMS BYTE-IDENTICAL TO APPROVED VERSION', flush=True)

style = json.loads((ROOT / 'label-style.json').read_text())
native = json.loads((ROOT / 'checks/capture-result.json').read_text())
assert native['report']['actualSceneLabels'] == dict(english=70, bilingual=0, unmapped=0)
assert style['languages'] == ['en']
assert len(style['overlays']) == 43
for label in style['overlays'] + native['report']['nativeLabelAudit']:
    assert label['language'] == 'en'
    assert not re.search(r'[\u3400-\u9fff]', label['english'])
result['english_picture_labels'] = dict(overlays=43, native_signs=70, chinese_labels=0)

subtitles = json.loads((ROOT / 'checks/subtitle-audit.json').read_text())
for record in subtitles['files']:
    file = ROOT / 'subtitles' / record['file']
    assert hashlib.sha256(file.read_bytes()).hexdigest() == record['sha256']
    content = file.read_text(encoding='utf-8-sig')
    blocks = [block for block in re.split(r'\n\s*\n', content.strip()) if block]
    assert len(blocks) == record['cues']
    previous_end = -1
    for i, block in enumerate(blocks, 1):
        lines = block.splitlines()
        assert int(lines[0]) == i
        values = re.fullmatch(r'(\d{2}):(\d{2}):(\d{2}),(\d{3}) --> (\d{2}):(\d{2}):(\d{2}),(\d{3})', lines[1])
        assert values, lines[1]
        a,b,c,d,e,f,g,h = map(int, values.groups())
        start=(a*3600+b*60+c)*1000+d
        end=(e*3600+f*60+g)*1000+h
        assert start >= previous_end and start < end <= round(record['duration_seconds']*1000)
        previous_end = end
    if record['language'] == 'en':
        assert not re.search(r'[\u3400-\u9fff]', content)
result['separate_subtitles'] = subtitles
print('ENGLISH LABELS AND SIX SRT FILES PASSED', flush=True)

frames = ROOT / 'checks/frames'
frames.mkdir(exist_ok=True)


def frame(shot):
    at = shot['label_start'] + 2
    file = frames / (shot['id'] + '.jpg')
    subprocess.run([FF, '-hide_banner', '-v', 'error', '-y', '-ss', str(at), '-i', str(master), '-frames:v', '1', str(file)], check=True)
    return file


with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
    paths = list(pool.map(frame, plan['shots']))
font = ImageFont.truetype('/System/Library/Fonts/STHeiti Medium.ttc', 16)
contact = Image.new('RGB', (1920, math.ceil(len(paths)/5)*235), '#0b1214')
draw = ImageDraw.Draw(contact)
for i,(file,shot) in enumerate(zip(paths, plan['shots'])):
    image = Image.open(file)
    image.thumbnail((380, 214), Image.Resampling.LANCZOS)
    x,y = i%5*384, i//5*235
    contact.paste(image,(x,y))
    draw.text((x+5,y+215),shot['asset_id'],font=font,fill='white')
contact.save(ROOT/'checks/final-contact.jpg',quality=91)

opening = Image.new('RGB',(1920,3*292),'#0b1214')
draw = ImageDraw.Draw(opening)
for i, at in enumerate([1.5, 7.5, 12.9, 14.5, 18.1, 23.8]):
    file = frames / f'opening-{at}.jpg'
    subprocess.run([FF,'-hide_banner','-v','error','-y','-ss',str(at),'-i',str(master),'-frames:v','1',str(file)],check=True)
    image=Image.open(file);image.thumbnail((950,267))
    x,y=i%2*960,i//2*292
    opening.paste(image,(x,y));draw.text((x+5,y+268),f'{at:.1f}s',font=font,fill='white')
opening.save(ROOT/'checks/opening-contact.jpg',quality=93)
result['representative_final_artwork_frames'] = len(paths)
result['opening_label_times'] = plan['opening_labels']
result['cover'] = json.loads((ROOT/'checks/cover-layout.json').read_text())
(ROOT/'checks/verified.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
print('VERIFIED: full decode, unchanged complete audio, English picture, external subtitles, 34 artwork samples, opening samples.',flush=True)
