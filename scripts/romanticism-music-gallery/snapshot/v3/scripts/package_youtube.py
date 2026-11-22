#!/usr/bin/env python3
"""Package the approved v3 film without re-encoding its picture or audio."""
from __future__ import annotations

import csv
import hashlib
import html
import json
from pathlib import Path
import shutil
import subprocess
import sys
from datetime import datetime, timezone

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT.parent
VIDEO_REPO = Path('@VIDEO_REPO@')
DEST = Path('@USER_HOME@/Desktop/山海与人间-YouTube上传')
sys.path.insert(0, str(VIDEO_REPO / 'scripts'))
from youtube_tags import DEFAULT, hashtags, tags

PLAN = json.loads((ROOT / 'edit-plan.json').read_text())
CREDITS = json.loads((ROOT / 'sources/credits.json').read_text())
LABELS = json.loads((ROOT / 'label-style.json').read_text())
TOPICS = ['chopin', 'beethoven', 'romanticism', 'classicalmusic', 'piano',
          'orchestra', 'painting', 'museum', 'artgallery', 'instrumentalmusic',
          '肖邦', '贝多芬', '浪漫主义']
MAIN = '01-山海与人间-纯音乐-中英标签.mp4'
NATURE = '备用分篇/自然篇-肖邦-纯音乐.mp4'
HUMAN = '备用分篇/人间篇-贝多芬-纯音乐.mp4'
OPENING = '预览/18秒开场.mp4'
FONT = Path('/System/Library/Fonts/STHeiti Medium.ttc')


def write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(8 * 1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def timestamp(seconds: float) -> str:
    seconds = int(seconds)
    return f'{seconds // 60}:{seconds % 60:02d}'


def clone_file(source: Path, relative: str):
    target = DEST / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(target.name + '.copying')
    if temporary.exists():
        temporary.unlink()
    result = subprocess.run(['/bin/cp', '-c', str(source), str(temporary)],
                            capture_output=True, text=True)
    if result.returncode:
        shutil.copy2(source, temporary)
    temporary.replace(target)
    source_hash, target_hash = sha256(source), sha256(target)
    assert source_hash == target_hash, relative
    print(f'Copied and SHA-256 verified: {relative}', flush=True)
    return {'file': relative, 'bytes': target.stat().st_size,
            'sha256': target_hash, 'identical_to_approved_export': True,
            'approved_export': source.name}


def probe(path: Path):
    command = ['/opt/homebrew/bin/ffprobe', '-v', 'error', '-show_format',
               '-show_streams', '-show_chapters', '-of', 'json', str(path)]
    data = json.loads(subprocess.check_output(command))
    video = next(s for s in data['streams'] if s['codec_type'] == 'video')
    audio = next(s for s in data['streams'] if s['codec_type'] == 'audio')
    assert video['width'] == 1920 and video['height'] == 1080
    assert video['codec_name'] == 'h264' and audio['codec_name'] == 'aac'
    assert video['avg_frame_rate'] == '24/1'
    assert int(audio['sample_rate']) == 48000 and audio['channels'] == 2
    return {'duration_seconds': float(data['format']['duration']),
            'width': video['width'], 'height': video['height'], 'fps': 24,
            'video_codec': video['codec_name'], 'audio_codec': audio['codec_name'],
            'sample_rate': int(audio['sample_rate']), 'channels': audio['channels'],
            'embedded_chapters': len(data.get('chapters', []))}


def make_cover(language: str):
    source = PROJECT / 'art/monk-sea.jpg'
    original = Image.open(source).convert('RGB')
    canvas = Image.new('RGB', (1280, 720), '#101d22')
    fitted = original.copy()
    fitted.thumbnail(canvas.size, Image.Resampling.LANCZOS)
    x, y = (1280 - fitted.width) // 2, (720 - fitted.height) // 2
    canvas.paste(fitted, (x, y))
    if language == 'zh':
        lines, size, top = ['山海与人间'], 136, 195
        filename = '04-封面-中文.jpg'
    else:
        lines, size, top = ['Mountains, Seas', '& Human Life'], 102, 155
        filename = '05-封面-英文.jpg'
    font = ImageFont.truetype(str(FONT), size)
    draw = ImageDraw.Draw(canvas)
    boxes = []
    for i, line in enumerate(lines):
        bounds = draw.textbbox((0, 0), line, font=font, stroke_width=2)
        width, height = bounds[2] - bounds[0], bounds[3] - bounds[1]
        assert width <= 1120
        left = (1280 - width) // 2
        baseline_top = top + i * 126
        position = (left - bounds[0], baseline_top - bounds[1])
        draw.text((position[0] + 2, position[1] + 4), line, font=font,
                  fill='#193039', stroke_width=3, stroke_fill='#193039')
        draw.text(position, line, font=font, fill='#f3eedf',
                  stroke_width=1, stroke_fill='#30434a')
        boxes.append([left, baseline_top, left + width, baseline_top + height])
    assert max(b[3] for b in boxes) < 500  # The complete monk is below the title.
    canvas.save(DEST / filename, quality=94, subsampling=0, optimize=True)
    assert (DEST / filename).stat().st_size < 2 * 1024 * 1024
    return {'file': filename, 'language': language, 'title_lines': lines,
            'canvas': [1280, 720], 'font_size': size, 'text_boxes': boxes,
            'painting': 'Monk by the Sea — Caspar David Friedrich',
            'painting_sha256': sha256(source),
            'painting_source': next(a['source'] for a in CREDITS['artworks']
                                    if a['id'] == 'monk-sea'),
            'painting_placement': [x, y, fitted.width, fitted.height],
            'composition': 'Entire original image contained, no crop or rearrangement.',
            'cover_copy': 'Title only; one language per cover.',
            'owner_exception': 'Owner explicitly chose 山海与人间 without a question mark.'}


def music_chapters(language: str):
    en = ['Chopin · Raindrop Prelude, Op. 28 No. 15',
          'Chopin · Nocturne in E-flat major, Op. 9 No. 2',
          'Chopin · Nocturne in C-sharp minor, B. 49',
          'Beethoven · Pathétique Sonata, II. Adagio cantabile',
          'Beethoven · Egmont Overture, Op. 84']
    zh = ['肖邦 ·《雨滴》前奏曲 Op. 28 No. 15',
          '肖邦 · 降 E 大调夜曲 Op. 9 No. 2',
          '肖邦 · 升 C 小调夜曲 B. 49',
          '贝多芬 ·《悲怆》奏鸣曲第二乐章',
          '贝多芬 ·《埃格蒙特》序曲 Op. 84']
    return '\n'.join(f"{timestamp(t['start'])} {label}"
                     for t, label in zip(PLAN['tracks'], zh if language == 'zh' else en))


def short_credits(language: str):
    zh = language == 'zh'
    blocks = [
        ('录音来源 / Music recordings' if zh else 'Music recordings'),
        'Chopin: Jeannette Fang (Op. 28 No. 15), Musopen recording (Op. 9 No. 2), Frank Levy (B. 49). CC0 1.0.',
        'https://archive.org/details/musopen-chopin-complete-works-flac',
        'https://commons.wikimedia.org/wiki/File:Chopin_-_Nocturne_No._2_in_E-flat_major,_Op._9_No._2_(Frank_Levy).flac',
        'Beethoven: Daniel Veesey (Pathétique II), Czech National Symphony Orchestra (Egmont). CC0 1.0.',
        'https://freemusicarchive.org/music/Daniel_Veesey/Beethovens_Sonata_No_in_C_Minor_Pathetique/Sonata_8_Pathetique_-_II_Adagio_cantabile/',
        'https://archive.org/details/MusopenCollectionAsFlac',
        'https://creativecommons.org/publicdomain/zero/1.0/',
        ('Op. 9 No. 2 的原始目录演奏者署名不一致，因此本片仅署 Musopen 录音。' if zh else
         'Op. 9 No. 2 is credited as a Musopen recording because the source catalogs disagree on the performer.'),
        '',
        ('雕塑扫描 / Sculpture scans · CC BY 4.0' if zh else 'Sculpture scans · CC BY 4.0'),
    ]
    short_names = ['Lion and Serpent', 'Die Marseillaise', 'Philopoemen',
                   'Seated Lion', 'Bacchante couchée', 'Head of Christ']
    for scan, name in zip(CREDITS['scans'][:6], short_names):
        blocks.extend([f"{name} — {scan['model_credit']}", scan['model_source']])
    blocks += [
        'https://creativecommons.org/licenses/by/4.0/',
        ('模型经缩放、定向、落地、减面及贴图缩小；Philopoemen 合并六段网格，Seated Lion 移除重复网格。' if zh else
         'Models scaled, oriented, grounded, decimated and textures resized. Philopoemen: six mesh segments joined and welded; Seated Lion: duplicate mesh omitted.'),
        'The Enslaved Woman / A Little Girl with Kittens — SMK Open, public domain.',
        'https://open.smk.dk/artwork/image/KMS5025',
        'https://open.smk.dk/artwork/image/KMS5471',
        'Moose the Dragon — original sculpture and scan, Lucas Academy.',
        '',
        ('绘画与画面 / Paintings and visuals' if zh else 'Paintings and visuals'),
        ('绘画原作已进入公版；包括浪漫主义绘画及其后续的文学与风景画回响。' if zh else
         'Public-domain paintings, including Romantic art and its later literary and landscape echoes.'),
        'The Last of the Mohicans (1920), public-domain silent-film excerpts:',
        'https://archive.org/details/PublicdomainTheLastoftheMohicans',
        ('展厅为虚拟沙龙；入口、修道院、巴黎及旅人动态沿用既有生成画面，作氛围演绎。' if zh else
         'The salon is virtual. The gallery entrance, monastery, Paris and animated wanderer reuse generated atmospheric visuals.'),
    ]
    return '\n'.join(blocks)


def make_metadata(language: str):
    zh = language == 'zh'
    title = ('山海与人间｜肖邦 × 贝多芬 · 浪漫主义音乐画廊（纯音乐，无配音）' if zh else
             'Mountains, Seas & Human Life | Chopin & Beethoven · Romantic Art | Instrumental')
    intro = ('先听音乐，再慢慢看一幅画。\n\n'
             '我们从画廊走进星空穹顶，在自然的画墙前听三首肖邦，再随贝多芬走近人的一生、苦难与自由。'
             '五首完整录音，三十四幅重点作品，纯音乐，无配音。作品与曲目标记都用中英文呈现。\n\n'
             '浪漫主义，以及它在后来的风景与文学绘画中留下的回响，让我们从山海望向人间。'
             '哪幅画让你愿意多停一会儿？\n\n'
             'Yancy 与 Eunice 共同创作。\n\n曲目章节\n' if zh else
             'Listen first. Then take your time with a painting.\n\n'
             'Step from a gallery into a salon beneath a starry dome. Three complete Chopin recordings accompany nature; '
             'Beethoven takes us toward the course of a life, suffering and freedom. '
             'Five complete recordings, thirty-four featured paintings, no narration, and simple English and Chinese labels.\n\n'
             'This walk follows Romantic art and its later echoes in landscape and literary painting. '
             'Which painting makes you want to stay a little longer?\n\n'
             'Created by Yancy and Eunice.\n\nMusic chapters\n')
    description = (intro + music_chapters(language) + '\n\n' + short_credits(language)
                   + '\n\n' + hashtags(TOPICS))
    settings = (f'主片文件：{MAIN}\n'
                '画面：1920 × 1080，24 fps，H.264；声音：AAC，48 kHz，双声道。\n'
                '类别：教育。\n'
                '中文封面：04-封面-中文.jpg；英文封面：05-封面-英文.jpg。\n'
                '中文与英文标题、简介分别保存在本文件与 03-YouTube英文.txt；按上传语言选用。\n'
                '只复制“简介”栏正文到视频说明；“标签”栏按项目格式单独复制。\n'
                '片中作品及音乐标记：英文在上、中文在下，同组字号相同。\n'
                '完整署名及逐曲、逐画清单见 06-素材署名.txt 与“资料”文件夹。' if zh else
                f'Main upload: {MAIN}\n'
                'Picture: 1920 × 1080, 24 fps, H.264. Audio: AAC, 48 kHz, stereo.\n'
                'Category: Education.\n'
                'English cover: 05-封面-英文.jpg. Chinese cover: 04-封面-中文.jpg.\n'
                'Choose the English or Chinese title and description for the upload language.\n'
                'Copy only the Description text into the description field; use Tags separately.\n'
                'On-screen artwork and music labels: English above Chinese, equal font sizes within each pair.\n'
                'Full credits and track/artwork inventories: 06-素材署名.txt and 资料/.')
    assert len(title) <= 100
    assert len(description) <= 5000, (language, len(description))
    assert description.splitlines()[-1] == hashtags(TOPICS)
    assert description.splitlines()[-1].split()[:8] == ['#' + t for t in DEFAULT]
    assert tags(TOPICS).split()[-8:] == ['#' + t for t in DEFAULT]
    text = (f'【标题 / Title】\n{title}\n\n'
            f'【简介 / Description】\n{description}\n\n'
            f'【标签 / Tags】\n{tags(TOPICS)}\n\n'
            f'【上传设置 / Upload settings】\n{settings}\n')
    filename = '02-YouTube中文.txt' if zh else '03-YouTube英文.txt'
    (DEST / filename).write_text(text)
    return {'file': filename, 'language': language, 'title': title,
            'title_characters': len(title), 'description_characters': len(description),
            'studio_tags_characters': len(tags(TOPICS)),
            'hashtags': hashtags(TOPICS), 'studio_tags': tags(TOPICS)}


def public_credits():
    music = [{k: v for k, v in m.items() if k not in ['local_file']}
             for m in CREDITS['music']]
    artwork_fields = ['id', 'title', 'titleEn', 'artist', 'artistEn', 'year',
                      'dateLabel', 'medium', 'source', 'imageSource', 'license', 'sha256']
    room_catalog = {a['id']: a for a in CREDITS['room_works']}
    artworks = []
    for source_art in CREDITS['artworks']:
        art = {k: source_art[k] for k in artwork_fields if k in source_art}
        room_art = room_catalog[art['id']]
        art.setdefault('titleEn', room_art['title_en'])
        art.setdefault('artistEn', room_art['artist_en'])
        artworks.append(art)
    footage = [{k: v for k, v in f.items() if k != 'file'} for f in CREDITS['footage']]
    for f in footage:
        if not f['source'].startswith('https://'):
            f['source'] = 'Owner-approved generated atmospheric footage, reused from the companion film.'
    opening = {'name': 'gallery-entry', 'kind': 'generated-atmospheric-footage',
               'sha256': CREDITS['opening']['sha256'], 'start': 0, 'end': 8.3,
               'source': 'Owner-approved generated gallery entrance, dissolving into the rendered virtual salon.'}
    return {'title': PLAN['title'], 'english_title': 'Mountains, Seas & Human Life',
            'creators': ['Yancy', 'Eunice'], 'duration_seconds': PLAN['duration'],
            'audio': 'Five complete music recordings; no narration; no source-video soundtracks.',
            'label_policy': 'English above Chinese; equal font size per pair; simple artwork/artist or music labels.',
            'curatorial_note': CREDITS['curatorial_note'],
            'music': music, 'featured_artworks': artworks,
            'background_room_works': CREDITS['room_works'],
            'sculpture_scans': CREDITS['scans'],
            'central_sculpture': CREDITS['central_sculpture'],
            'footage': [opening, *footage],
            'virtual_salon': {'paintings': 56, 'third_party_scans': 8,
                             'central_sculpture': 'Moose the Dragon'},
            'cover': {'work': 'Monk by the Sea', 'artist': 'Caspar David Friedrich',
                      'source': next(a['source'] for a in artworks if a['id'] == 'monk-sea'),
                      'composition': 'Original full image, proportionally contained, title added in sky.'}}


def write_inventories(credits):
    artworks_by_id = {a['id']: a for a in credits['featured_artworks']}
    with (DEST / '资料/逐曲清单.csv').open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['顺序', '开始', '开始秒', '结束秒', '作曲家', '作品', '演奏者记录',
                         '许可记录', '来源', '署名说明', '源音频SHA256'])
        for i, m in enumerate(credits['music'], 1):
            writer.writerow([i, timestamp(m['start']), m['start'], m['end'], m['composer'],
                             m['title'], m['performer'], m['license'], m['source'],
                             m.get('credit_note', ''), m['sha256']])
    with (DEST / '资料/逐画清单.csv').open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['顺序', '分篇', '开始', '开始秒', '结束秒', '画作中文', '画作英文',
                         '作者中文', '作者英文', '年代', '片中中文标记', '片中英文标记',
                         '作品来源', '图像来源', '许可记录', '图像SHA256'])
        for i, shot in enumerate(sorted(PLAN['shots'], key=lambda s: s['global_start']), 1):
            label = LABELS['artworks'][shot['asset_id']]
            art = artworks_by_id[shot['asset_id']]
            writer.writerow([i, '自然' if shot['track'] in ['rain', 'nocturne', 'distance'] else '人间',
                             timestamp(shot['global_start']), shot['global_start'], shot['global_end'],
                             art['title'], art['titleEn'], art['artist'], art['artistEn'],
                             art.get('dateLabel', art['year']), label['chinese'], label['english'],
                             art['source'], art['imageSource'], art['license'], art['sha256']])
    text = [PLAN['title'] + ' / Mountains, Seas & Human Life',
            'Yancy 与 Eunice 共同创作 / Created by Yancy and Eunice',
            '完整素材来源与署名 / Complete source credits', '',
            '音乐 / Music', '']
    for m in credits['music']:
        text += [f"{timestamp(m['start'])} {m['composer']} · {m['title']}",
                 f"{m['performer']} · {m['license']}", m['source'],
                 m.get('credit_note', ''), '']
    text += ['许可 / License: https://creativecommons.org/publicdomain/zero/1.0/', '',
             '雕塑扫描 / Sculpture scans', '']
    for s in credits['sculpture_scans']:
        text += [s.get('model_title', s['title_en']),
                 f"{s.get('model_credit', 'SMK Open')} · {s['license']}",
                 s.get('model_source', s['source']), s['license_url'],
                 'Modifications: ' + s['modifications'], '']
    text += ['Moose the Dragon — original sculpture and scan from Lucas Academy.', '',
             '重点绘画 / Featured paintings', '']
    for a in credits['featured_artworks']:
        text += [f"{a['titleEn']} / {a['title']} — {a['artistEn']} / {a['artist']}",
                 str(a.get('dateLabel', a['year'])) + ' · ' + a['license'],
                 a['source'], a['imageSource'], '']
    text += ['展厅背景作品 / Room paintings',
             '此处含主要作品及背景墙作品；与上面重点作品会有重叠。', '']
    for a in credits['background_room_works']:
        text += [f"{a['title_en']} / {a['title_zh']} — {a['artist_en']} ({a['year']})",
                 a['license'], a['source'], '']
    text += ['视频画面 / Footage',
             'The Last of the Mohicans (1920), public-domain silent film.',
             'https://archive.org/details/PublicdomainTheLastoftheMohicans',
             '入口、修道院、巴黎及旅人动态沿用既有的生成画面，作为氛围演绎。',
             'The gallery entrance, monastery, Paris and animated wanderer reuse generated atmospheric footage.',
             '星空展厅为同一原生虚拟沙龙的连续运镜。',
             'The starry salon is a rendered virtual space, filmed along a continuous camera route.', '',
             '封面 / Covers',
             'Monk by the Sea / 海边的修道士 — Caspar David Friedrich / 弗里德里希',
             credits['cover']['source'],
             '保留全幅原始构图，在天空留白处排片名。中文、英文各一张。', '']
    (DEST / '06-素材署名.txt').write_text('\n'.join(text))


def write_preview():
    cards = []
    for file, heading, detail in [
        (MAIN, '主片 · 山海与人间', '29:00 · 肖邦与贝多芬 · 5 首完整录音'),
        (NATURE, '自然篇 · 肖邦', '13:36 · 三首肖邦'),
        (HUMAN, '人间篇 · 贝多芬', '15:23 ·《悲怆》第二乐章与《埃格蒙特》序曲'),
        (OPENING, '开场预览', '18 秒 · 从画廊到星空沙龙')]:
        cards.append(f'<section><h2>{html.escape(heading)}</h2><p>{html.escape(detail)}</p>'
                     f'<video controls preload="none" playsinline src="{html.escape(file)}"></video></section>')
    document = '''<!doctype html><html lang="zh-CN"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>山海与人间 · 上传包预览</title>
<style>body{background:#101c22;color:#f4efdf;font:17px/1.6 system-ui,sans-serif;max-width:1060px;margin:40px auto;padding:0 22px}h1{font-size:34px;font-weight:600;margin-bottom:2px}h2{font-size:22px;margin:0}p{color:#b6c5cc}section{margin:30px 0 46px}video{display:block;width:100%;aspect-ratio:16/9;background:#000;border-radius:8px}a{color:#d2e5ed}nav{display:flex;gap:18px;flex-wrap:wrap}.covers{display:grid;grid-template-columns:1fr 1fr;gap:18px}.covers img{width:100%}@media(max-width:650px){.covers{grid-template-columns:1fr}body{margin-top:24px}h1{font-size:28px}}</style>
<h1>山海与人间</h1><p>Mountains, Seas &amp; Human Life<br>Yancy 与 Eunice · 纯音乐，无配音</p>
<nav><a href="02-YouTube中文.txt">中文上传文案</a><a href="03-YouTube英文.txt">English metadata</a><a href="06-素材署名.txt">完整素材署名</a><a href="使用说明.txt">使用说明</a></nav>
''' + ''.join(cards) + '''<section><h2>独立中英文封面</h2><div class="covers"><a href="04-封面-中文.jpg"><img src="04-封面-中文.jpg" alt="中文封面：山海与人间"></a><a href="05-封面-英文.jpg"><img src="05-封面-英文.jpg" alt="English cover: Mountains, Seas and Human Life"></a></div></section></html>'''
    (DEST / '打开预览.html').write_text(document)


def main():
    marker = DEST / '资料/上传包信息.json'
    if DEST.exists() and not marker.exists():
        raise RuntimeError(f'Refusing to overwrite an unrelated existing folder: {DEST}')
    DEST.mkdir(parents=True, exist_ok=True)
    (DEST / '资料').mkdir(exist_ok=True)
    write_json(marker, {'project': 'romanticism-music-gallery', 'approved_version': 3,
                        'title': PLAN['title'], 'created_utc': datetime.now(timezone.utc).isoformat(),
                        'cover_owner_choice': '山海与人间；不改成问句',
                        'editing_policy': 'Approved exports copied byte-for-byte; no re-encoding.'})
    files = []
    exports = [('山海与人间-中英标签纯音乐版.mp4', MAIN, PLAN['duration']),
               ('自然篇-肖邦-中英标签版.mp4', NATURE, 815.916667),
               ('人间篇-贝多芬-中英标签版.mp4', HUMAN, 923.0),
               ('从画廊到星空沙龙-中英标签开场.mp4', OPENING, 18)]
    for export, destination, duration in exports:
        record = clone_file(ROOT / 'exports' / export, destination)
        record['media'] = probe(DEST / destination)
        assert abs(record['media']['duration_seconds'] - duration) < 0.06
        files.append(record)
    assert files[0]['media']['embedded_chapters'] == 5
    cover_records = [make_cover(language) for language in ['zh', 'en']]
    metadata = [make_metadata(language) for language in ['zh', 'en']]
    public = public_credits()
    write_json(DEST / '资料/完整素材来源.json', public)
    write_inventories(public)
    write_preview()
    (DEST / '使用说明.txt').write_text(
        '山海与人间 — YouTube 上传包\n\n'
        '上传主片：01-山海与人间-纯音乐-中英标签.mp4（29 分 00 秒）。\n'
        '自然篇与人间篇放在“备用分篇”；18 秒开场放在“预览”。\n'
        '双击“打开预览.html”即可在本地查看，所有媒体都在这个文件夹内。\n\n'
        '02-YouTube中文.txt 与 03-YouTube英文.txt 各自包含标题、简介、标签与上传设置。\n'
        '按所需语言复制相应内容；简介中的录音、雕塑与视频署名请保留。\n'
        '04-封面-中文.jpg 与 05-封面-英文.jpg 为 1280 × 720 的独立语言封面。\n'
        '封面按本次确认只用片名《山海与人间》，保留原画全幅构图。\n\n'
        '本片纯音乐、无配音；作品与曲目标记为英文在上、中文在下，同组字号相同。\n'
        '沿用已确认的 v3 成片、运镜、转场与五首完整录音。\n'
        'Yancy 与 Eunice 共同创作。\n\n'
        '06-素材署名.txt：完整署名。\n'
        '资料/逐曲清单.csv 与 资料/逐画清单.csv：五首录音和三十四幅重点画作，含时间与来源。\n'
        '资料/完整素材来源.json：另含展厅背景画作、扫描雕塑及画面来源记录。\n'
        '资料/校验记录.json：文件 SHA-256、时长、规格及检查结果。\n')
    # Portable metadata must not contain workspace paths, local servers, or external dependencies.
    for file in DEST.rglob('*'):
        if file.is_file() and file.suffix in ['.txt', '.json', '.csv', '.html']:
            text = file.read_text(encoding='utf-8-sig')
            assert '/Users/' not in text and '127.0.0.1' not in text, file
    original_checks = json.loads((ROOT / 'checks/verified.json').read_text())
    assert original_checks['full_master_decode'] == 'passed'
    assert len(PLAN['shots']) == 34 and len(public['music']) == 5
    inventory = []
    for file in sorted(DEST.rglob('*')):
        if file.is_file() and file.name != '校验记录.json':
            inventory.append({'file': str(file.relative_to(DEST)), 'bytes': file.stat().st_size,
                              'sha256': sha256(file)})
    report = {'status': 'passed', 'checked_utc': datetime.now(timezone.utc).isoformat(),
              'videos': files, 'covers': cover_records, 'upload_metadata': metadata,
              'all_files': inventory,
              'approved_master_full_decode': 'Previously passed; exact SHA-256 copy verified in this package.',
              'featured_artworks': 34, 'music_recordings': 5,
              'labels': {'order': ['English', 'Chinese'], 'equal_font_size_per_pair': True,
                         'source_audit': 'Approved v3 label-style-qa and final visual review passed.'},
              'portability': 'No workspace paths or local-server references in package documents.',
              'cover_visual_review': 'pending', 'browser_package_review': 'pending'}
    write_json(DEST / '资料/校验记录.json', report)
    write_json(ROOT / 'checks/youtube-package.json',
               {'path': str(DEST), 'status': 'awaiting visual review',
                'master_sha256': files[0]['sha256'], 'total_bytes': sum(f['bytes'] for f in inventory)})
    print(json.dumps({'package': str(DEST), 'metadata': metadata,
                      'files': len(inventory) + 1,
                      'total_bytes': sum(f['bytes'] for f in inventory)}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
