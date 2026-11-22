"""English film labels, separate SRTs, and the owner's unlettered cover frame."""
from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[1]
PREVIOUS = ROOT.parent / 'v3'
FONT = '/System/Library/Fonts/STHeiti Medium.ttc'
plan = json.loads((PREVIOUS / 'edit-plan.json').read_text())
prior = json.loads((PREVIOUS / 'label-style.json').read_text())
plan.update(version=4, title='山、海、人间', title_en='Mountains, Seas, and Mortals',
            label_policy='English-only picture, including all native gallery signs. Separate English and Simplified Chinese SRT files.',
            opening_labels=[
                dict(id='entrance', start=.5, end=5.5, english='From Gallery to Space', chinese='从画廊到星空'),
                dict(id='album', start=6.5, end=11.5, english='Mountains, Seas, and Mortals', chinese='山、海、人间'),
                dict(id='hear', start=12.5, end=20.5, english='Hear and see', chinese='聆听与观看'),
                dict(id='world', start=13.5, end=20.5, english='how the Romantics saw the world', chinese='浪漫主义者眼中的世界'),
            ])
(ROOT / 'edit-plan.json').write_text(json.dumps(plan, ensure_ascii=False, indent=2))
overlays = []


def label(key, text, size, y, center=False, gradient=None):
    assert not re.search(r'[\u3400-\u9fff]', text), text
    image = Image.new('RGBA', (1920, 1080))
    draw = ImageDraw.Draw(image)
    if gradient == 'bottom':
        for row in range(980, 1080):
            draw.line((0, row, 1920, row), fill=(9, 15, 17, min(210, round((row - 980) / 80 * 210))))
    elif gradient == 'top':
        for row in range(112):
            draw.line((0, row, 1920, row), fill=(7, 13, 15, round(195 * (1 - row / 112))))
    while True:
        font = ImageFont.truetype(FONT, size)
        bbox = draw.textbbox((0, 0), text, font=font)
        if bbox[2] - bbox[0] <= 1780:
            break
        size -= 1
    x = (1920 - (bbox[2] - bbox[0])) / 2 - bbox[0] if center else 65
    if key == 'album':
        x = 84
    draw.text((x, y), text, font=font, fill='#f3ebd9', stroke_width=2,
              stroke_fill='#101820')
    image.save(ROOT / 'labels' / (key + '.png'))
    overlays.append(dict(id=key, english=text, font_px=size, language='en', lines=1))


for shot in plan['shots']:
    label(shot['id'], prior['artworks'][shot['asset_id']]['english'], 36, 1013, gradient='bottom')
for track in plan['tracks']:
    label(track['id'], prior['music'][track['id']]['english'], 36, 26, gradient='top')
label('entrance', 'From Gallery to Space', 42, 830, center=True)
label('album', plan['title_en'], 50, 857)
label('hear', 'Hear and see', 42, 806, center=True)
label('world', 'how the Romantics saw the world', 42, 866, center=True)
style = dict(version=4, languages=['en'], native_language='en',
             artwork_format='Title · Artist', no_biography=True, no_date_in_film_labels=True,
             overlays=overlays, artworks=prior['artworks'], music=prior['music'], native=prior['native'],
             subtitles=['en', 'zh-Hans'], subtitles_burned_in=False)
(ROOT / 'label-style.json').write_text(json.dumps(style, ensure_ascii=False, indent=2))


def srt_time(seconds):
    value = round(seconds * 1000)
    h, value = divmod(value, 3_600_000)
    m, value = divmod(value, 60_000)
    s, ms = divmod(value, 1000)
    return f'{h:02}:{m:02}:{s:02},{ms:03}'


cues = [
    dict(start=.5, end=5.5, en='From Gallery to Space', zh='从画廊到星空'),
    dict(start=6.5, end=11.5, en=plan['title_en'], zh=plan['title']),
    dict(start=12.5, end=13.5, en='Hear and see', zh='聆听与观看'),
    dict(start=13.5, end=20.5, en='Hear and see\nhow the Romantics saw the world', zh='聆听与观看\n浪漫主义者眼中的世界'),
]
for track in plan['tracks']:
    start, end = (23, 32) if track['id'] == 'rain' else (track['start'], track['start'] + 9)
    pair = prior['music'][track['id']]
    cues.append(dict(start=start, end=end, en=pair['english'], zh=pair['chinese']))
for shot in plan['shots']:
    pair = prior['artworks'][shot['asset_id']]
    cues.append(dict(start=shot['label_start'], end=shot['label_end'],
                     en=pair['english'], zh=pair['chinese']))
cues.sort(key=lambda cue: cue['start'])
for i, cue in enumerate(cues):
    assert 0 <= cue['start'] < cue['end'] <= plan['duration']
    if i:
        assert cue['start'] >= cues[i-1]['end'] - .001, (cue, cues[i-1])
    assert not re.search(r'[\u3400-\u9fff]', cue['en'])


def write_srt(name, language, start=0, end=plan['duration']):
    selected = [dict(start=max(c['start'], start)-start, end=min(c['end'], end)-start,
                     text=c[language]) for c in cues if c['end'] > start and c['start'] < end]
    content = '\n\n'.join(f"{i}\n{srt_time(c['start'])} --> {srt_time(c['end'])}\n{c['text']}"
                           for i, c in enumerate(selected, 1)) + '\n'
    destination = ROOT / 'subtitles' / name
    destination.write_text(content, encoding='utf-8-sig')
    return dict(file=name, language='en' if language == 'en' else 'zh-Hans',
                cues=len(selected), offset_seconds=start,
                duration_seconds=end-start, sha256=hashlib.sha256(destination.read_bytes()).hexdigest())


subtitle_records = []
for language in ['en', 'zh']:
    subtitle_records.append(write_srt('山、海、人间.' + language + '.srt', language))
    subtitle_records.append(write_srt('自然篇-肖邦.' + language + '.srt', language, 0, plan['tracks'][2]['end']))
    subtitle_records.append(write_srt('人间篇-贝多芬.' + language + '.srt', language, plan['tracks'][3]['start'], plan['duration']))
(ROOT / 'subtitles/cues.json').write_text(json.dumps(cues, ensure_ascii=False, indent=2))
(ROOT / 'checks/subtitle-audit.json').write_text(json.dumps(
    dict(status='passed', files=subtitle_records, no_overlapping_cues=True,
         same_timing_in_both_languages=True, content='On-screen headings, music, artwork titles and artists; no invented narration.'),
    ensure_ascii=False, indent=2))

# Preserve exactly the owner-selected frame: no text, no crop, no retouching.
source = ROOT / 'assets/owner-cover-frame.png'
cover = Image.open(source).convert('RGB')
assert cover.size == (1920, 1080)
cover.resize((1280, 720), Image.Resampling.LANCZOS).save(ROOT / 'poster.jpg', quality=94, subsampling=0, optimize=True)
(ROOT / 'checks/cover-layout.json').write_text(json.dumps(
    dict(source='assets/owner-cover-frame.png', source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
         canvas=[1280, 720], crop=False, text=False, painting_id='sierra',
         work='Among the Sierra Nevada Mountains, California — Albert Bierstadt',
         owner_request='Use this selected frame as the cover, without text.'), ensure_ascii=False, indent=2))
print('Prepared', len(overlays), 'English overlays,', len(cues), 'cues per main-film SRT, six SRT files, and one unlettered cover.')
