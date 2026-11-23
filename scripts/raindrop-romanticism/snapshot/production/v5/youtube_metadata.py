"""Write the upload descriptions and optional subtitle tracks for the final film."""
from dataclasses import dataclass
import json
from pathlib import Path
import re
import unicodedata

import numpy as np

from timeline import P, SR, vtt_timestamp
from youtube_package import DEST, HASHTAGS, YOUTUBE_TAGS, mandarin_takes

EN_DESCRIPTION = DEST / '03-YouTube简介与素材署名.txt'
ZH_DESCRIPTION = DEST / '06-YouTube中文简介与素材署名.txt'
EN_SUBTITLES = DEST / '07-YouTube英文字幕.srt'
ZH_SUBTITLES = DEST / '08-YouTube简体中文字幕.srt'
TAG_BLOCK = f'{HASHTAGS}\n\nYouTube Tags\n{YOUTUBE_TAGS}\n'


@dataclass
class Cue:
    start: float
    end: float
    text: str


def chinese_description(plan):
    source = json.loads((P / 'sources-and-credits.json').read_text())
    lines = [
        '压力？焦虑？肖邦？浪漫？',
        '',
        '先听十秒肖邦的《雨滴》。那个反复落下的音，和声转暗以后，听起来有了怎样的重量？',
        '',
        '从乔治·桑回忆的马略卡雨夜出发，我们走进深空浪漫主义沙龙。一条线看战争与革命，另一条线看大海、雾和风暴。在那个长期动荡的时代，作曲家和画家怎样表达他们的感受？片尾还有一个关于日本物哀美学的小彩蛋，和大家一起想想感受、自然、时间和人的有限性。',
        '',
        'Yancy 与 Eunice 共同创作',
        '',
        '影片章节',
    ]
    for section, title in (
        ('intro', '从画廊走进深空沙龙'),
        ('chopin', '肖邦与《雨滴》'),
        ('history', '革命与动荡的时代'),
        ('goya', '画家笔下的战争与革命'),
        ('wright', '自然与崇高'),
        ('themes', '感受、自然、时间和人的有限性'),
        ('bonus', '片尾彩蛋 · 日本物哀美学'),
    ):
        start = int(next(scene['start'] for scene in plan['scenes'] if scene['section'] == section))
        minutes, seconds = divmod(start, 60)
        lines.append(f'{minutes}:{seconds:02d} {title}')
    lines.extend(['', '配乐 · 弗雷德里克·肖邦'])
    performers = {
        'nocturne-9-2': '降 E 大调夜曲，Op. 9 No. 2 · Frank Levy',
        'nocturne-c-sharp': '升 C 小调夜曲，B. 49 · Frank Levy',
        'prelude-28-15': '降 D 大调《雨滴》前奏曲，Op. 28 No. 15 · Jeannette Fang',
    }
    for track in source['music']:
        lines.extend([f"{performers[track['id']]} · Musopen · {track['license']}", track['source']])
    photograph = source['photograph']
    gallery = source['opening_gallery']['reference']
    lines.extend([
        '', '图片与镜头',
        f"京都西来院摄影 · {photograph['artist']} · {photograph['license']}",
        photograph['source'],
        photograph['license_url'],
        f"开场画廊参考图 · {gallery['creator']} · {gallery['source']}",
    ])
    for clip in source['live_action']:
        lines.append(f"水上落樱实拍 · {clip['author']} · {clip['source']}")
    lines.extend(['', '雕塑三维扫描 · CC BY 4.0', 'https://creativecommons.org/licenses/by/4.0/'])
    for scan in source['scans']:
        if scan['license'] == 'CC BY 4.0':
            lines.append(f"{scan['title_en']} · {scan['model_credit']} · {scan['model_source']}")
    lines.extend(['扫描模型在虚拟沙龙中调整了尺寸和位置。', '', TAG_BLOCK])
    return '\n'.join(lines)


def english_description():
    text = EN_DESCRIPTION.read_text(encoding='utf-8')
    body, divider, tail = text.partition('\n\nYouTube Tags\n')
    assert divider and tail.strip()
    lines = body.rstrip().splitlines()
    while lines and lines[-1].startswith('#'):
        lines.pop()
    return '\n'.join(lines).rstrip() + '\n\n' + TAG_BLOCK


def read_english_cues():
    filepath = P / 'exports/louise-english.vtt'
    blocks = filepath.read_text(encoding='utf-8').strip().split('\n\n')
    assert blocks[0] == 'WEBVTT'

    def to_seconds(time):
        hour, minute, second = time.split(':')
        return int(hour) * 3600 + int(minute) * 60 + float(second)

    cues = []
    for block in blocks[1:]:
        timing, *lines = block.splitlines()
        first, last = map(to_seconds, timing.split(' --> '))
        if cues and abs(cues[-1].end - first) < .002 and last - first < .85:
            previous = cues[-1]
            # A brief trailing word can share the preceding cue's viewing time.
            shift = min(.85 - (last - first), max(0, previous.end - previous.start - .9))
            first -= shift
            previous.end = first
        cues.append(Cue(first, last, '\n'.join(lines)))
    return cues


def display_width(text):
    return sum(2 if unicodedata.east_asian_width(char) in ('W', 'F') else 1 for char in text)


def split_long_clause(text, limit=64):
    while display_width(text) > limit:
        index = next(i for i in range(1, len(text) + 1) if display_width(text[:i]) > limit) - 1
        space = text.rfind(' ', 0, index)
        if space > index - 8:
            index = space + 1
        yield text[:index]
        text = text[index:]
    if text:
        yield text


def chinese_groups(text):
    text = ' '.join(text.splitlines()).strip()
    clauses = re.findall(r'.+?(?:[。！？；，、]+[”’」』）]*|…+[”’」』）]*|$)', text)
    parts = [chunk for clause in clauses for chunk in split_long_clause(clause)]
    groups = []
    current = ''
    for part in parts:
        if current and (display_width(current + part) > 64 or
                        (display_width(current) >= 27 and current.rstrip('”’」』）').endswith(tuple('。！？')))):
            groups.append(current)
            current = ''
        current += part
    if current:
        if groups and display_width(current) < 12 and display_width(groups[-1] + current) <= 72:
            groups[-1] += current
        else:
            groups.append(current)
    assert ''.join(groups) == text
    return groups


def wrap_chinese(text):
    text = text.strip()
    total = display_width(text)
    if total <= 38:
        return text
    positions = [
        i for i in range(1, len(text)) if
        display_width(text[:i].strip()) <= 39 and display_width(text[i:].strip()) <= 39
        and text[i] not in '，。？！、；：）’”」』'
    ]
    if not positions:
        positions = [i for i in range(1, len(text)) if
                     display_width(text[:i].strip()) <= 39 and display_width(text[i:].strip()) <= 39]
    assert positions, text

    def score(index):
        previous = text[index - 1]
        in_english_word = text[index].isascii() and previous.isascii() and text[index].isalnum() and previous.isalnum()
        clause_end = previous in '，。？！、；：”」』 '
        return abs(display_width(text[:index]) - total / 2) + (11 if in_english_word else 0) - (6 if clause_end else 0)

    cut = min(positions, key=score)
    return text[:cut].rstrip() + '\n' + text[cut:].lstrip()


def speech_weight(text):
    return sum((.66 if char in '。！？；' else .35) if unicodedata.category(char).startswith('P')
               else (0 if char.isspace() else (1 if not char.isascii() or char.isdigit() else .65)) for char in text)


def in_take_boundaries(groups, waveform):
    duration = len(waveform) / SR
    windows = len(waveform) // 960
    rms = np.sqrt(np.mean(waveform[:windows * 960].reshape(windows, 960)**2, axis=1))
    weights = list(map(speech_weight, groups))
    estimate = np.cumsum(weights) * duration / sum(weights)
    breaks = [0.]
    for index, predicted in enumerate(estimate[:-1]):
        low = max(breaks[-1] + .7, predicted - .38)
        high = min(estimate[index + 1] - .54, predicted + .38)
        frames = np.arange(max(0, int(np.ceil(low * 50))), min(windows, int(high * 50) + 1))
        if len(frames):
            distance = np.abs((frames + .5) / 50 - predicted)
            best = frames[np.argmin(rms[frames] + .030 * distance)]
            cut = (best + .5) / 50 if rms[best] < .045 else predicted
        else:
            cut = predicted
        breaks.append(float(cut))
    breaks.append(duration)
    assert all(first < last for first, last in zip(breaks, breaks[1:])), groups
    return breaks


def read_mandarin_cues(plan):
    takes, _, _ = mandarin_takes(plan)
    cues = []
    for scene in plan['scenes']:
        if scene['id'] not in takes:
            continue
        (text, waveform), = takes[scene['id']]
        groups = chinese_groups(text)
        offset = scene['start'] + .25
        breaks = in_take_boundaries(groups, waveform)
        for index, group in enumerate(groups):
            cues.append(Cue(offset + breaks[index], offset + breaks[index + 1], wrap_chinese(group)))
    return cues


def validate_cues(cues, plan, language):
    all_text = ''.join(cue.text for cue in cues)
    expected = ''.join(scene.get(language, '') for scene in plan['scenes'])
    assert re.sub(r'\s+', '', all_text) == re.sub(r'\s+', '', expected)
    reprise = next(scene for scene in plan['scenes'] if scene['id'] == 'listen')
    previous = 0.
    for cue in cues:
        assert round(previous, 3) <= round(cue.start, 3) < round(cue.end, 3) <= plan['duration']
        assert cue.end <= reprise['start'] or cue.start >= reprise['end']
        assert 1 <= len(cue.text.splitlines()) <= 2
        previous = cue.end


def srt(cues):
    sections = []
    for number, cue in enumerate(cues, 1):
        first = vtt_timestamp(cue.start).replace('.', ',')
        last = vtt_timestamp(cue.end).replace('.', ',')
        sections.append(f'{number}\n{first} --> {last}\n{cue.text}')
    return '\n\n'.join(sections) + '\n'


if __name__ == '__main__':
    plan = json.loads((P / 'edit-plan.json').read_text())
    english = read_english_cues()
    mandarin = read_mandarin_cues(plan)
    validate_cues(english, plan, 'text')
    validate_cues(mandarin, plan, 'text_zh')
    contents = [
        (EN_DESCRIPTION, english_description()),
        (ZH_DESCRIPTION, chinese_description(plan)),
        (EN_SUBTITLES, srt(english)),
        (ZH_SUBTITLES, srt(mandarin)),
    ]
    for destination, content in contents:
        temp = destination.with_suffix(destination.suffix + '.partial')
        temp.write_text(content, encoding='utf-8')
        temp.replace(destination)
    print('Exported', len(english), 'English and', len(mandarin), 'Mandarin subtitle cues')
