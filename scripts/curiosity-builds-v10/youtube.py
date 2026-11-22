"""Write the Curiosity Builds upload package in the repository's YouTube format.

Uses README 'YouTube tags' and scripts/youtube_tags.py. Chapters come from the
delivered film, not from a separately maintained text list. The owner selected
cover B and explicitly approved its wording, overriding the default cover-question
preference for this particular cover.
"""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / 'scripts'))
from youtube_tags import DEFAULT, hashtags, tags

DATA = REPO.with_name('lucas-academy-video-data') / 'curiosity-builds-20261118'
FILM = DATA / 'v10'
OUT = FILM / 'delivery'
DOC = REPO / 'docs/curiosity-builds'
DESKTOP = Path('/Users/yqin/Desktop/Curiosity Builds - Final')
DEST = DESKTOP / 'YouTube'
COVERS = {
    'en': DATA / 'covers-v6/02-ideas-to-worlds-neutral-white-v6.png',
    'zh': DATA / 'covers-zh-v1/02-ideas-to-worlds-zh-v1.png',
}
TITLES = {
    'en': 'What Can Curiosity Build? | 9 Projects to Explore',
    'zh': '好奇心能创造什么？｜9个创作项目',
}
OWN = {
    'en': ['curiosity', 'creativeprojects', 'projectbasedlearning', 'inceptionspace',
           'balancedchess', '11x11cube', 'artgallery', 'coderarena', 'biblesequence'],
    'zh': ['好奇心', '创作项目', '项目式学习', 'inceptionspace', 'balancedchess',
           '11x11cube', 'artgallery', 'coderarena', 'biblesequence'],
}
NAMES = {
    'en': {
        'chess': 'Balanced Chess', 'bible': 'Bible Sequence / Next Word',
        'vangogh': 'Van Gogh House', 'journey': 'Journey of Art',
        'sky': 'The Sky / Cosmic Cliffs', 'chameleon': 'Painterly Chameleon / Hide-and-Seek',
        'cube': 'The Cube / 7×7 and 11×11', 'coder': 'Coder Arena / Monthly Ranking',
        'roller': 'A Ride from Formulas',
    },
    'zh': {
        'chess': 'Balanced Chess：逆转与落石', 'bible': 'Bible Sequence：经文复原与下一个词',
        'vangogh': '梵高房间', 'journey': 'Journey of Art 艺术画廊',
        'sky': 'The Sky：宇宙中的流水房间', 'chameleon': 'Painterly Chameleon：画作里的捉迷藏',
        'cube': '魔方：7×7与11×11', 'coder': 'Coder Arena与月度排行',
        'roller': '用公式建造过山车',
    },
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stamp(seconds):
    seconds = int(seconds)
    return f'{seconds // 60}:{seconds % 60:02d}'


def probe(path):
    return json.loads(subprocess.check_output([
        'ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(path)
    ]))


def build(lang, sheet, total):
    if lang == 'en':
        intro = (
            'A chess game with comeback rules. A ride built from formulas. A gallery made from our art.\n\n'
            'Explore nine Lucas Academy projects, from a simple idea and a glimpse of the building '
            'process to something we can play, explore, or create with—from art and living skies '
            'to puzzles, coding competitions, and Bible games.\n\n'
            'What are you curious about?\nWhat will you build?\nWhere will you make a difference?'
        )
        links = ('Explore the projects\nInception Space: https://is.lucasacademy.org\n'
                 'Bible Sequence: https://bible.lucasacademy.org\n'
                 'Painterly Chameleon: https://pc.lucasacademy.org\n'
                 'Lucas Academy: https://lucasacademy.org')
        chapter_heading, end = 'Chapters', 'What are you curious about?'
        visual = ('About the film\nNo narration; English onscreen text, with optional Chinese label subtitles.\n'
                  'Demos: recordings of the actual projects. Monthly Ranking uses an archived server battle.\n'
                  'Build sequences are concept visualizations. Gallery/cube concept sketches and the '
                  'thumbnail were made with ImageGen.\nSky image: NASA/ESA/CSA/STScI — Cosmic Cliffs.\n'
                  'By Lucas Academy Team')
        music_heading = 'Music and recording credits'
    else:
        intro = (
            '有逆转规则的国际象棋，用公式建造的过山车，装着我们作品的艺术画廊。\n\n'
            '跟着九个 Lucas Academy 创作项目，从一个简单想法、几笔建造示意，走进可以玩、可以探索、'
            '可以继续创作的作品：绘画与天空，魔方与编程竞赛，还有经文游戏。\n\n'
            '你对什么感到好奇？\n你想创造什么？\n你想在哪里带来改变？'
        )
        links = ('探索项目\nInception Space：https://is.lucasacademy.org\n'
                 'Bible Sequence：https://bible.lucasacademy.org\n'
                 'Painterly Chameleon：https://pc.lucasacademy.org\n'
                 'Lucas Academy：https://lucasacademy.org')
        chapter_heading, end = '章节', '你对什么感到好奇？'
        visual = ('画面说明\n英文画面文字，无配音；可加载翻译标题与标签的中文字幕。\n'
                  'Demo为实际项目录像，月度排行使用历史服务器对战录像。\n'
                  '建造过程为概念示意；画廊、魔方概念草图及封面使用 ImageGen 制作。\n'
                  '天空图像：NASA/ESA/CSA/STScI — Cosmic Cliffs。\n作者：Lucas Academy Team')
        music_heading = '配乐与录音来源'

    rows = [(row['start'], NAMES[lang][row['id']]) for row in sheet]
    ending = sheet[-1]['start'] + sheet[-1]['seconds']
    rows.append((ending, end))
    assert rows[0][0] == 0
    assert all(b[0] - a[0] >= 10 for a, b in zip(rows, rows[1:]))
    assert total - rows[-1][0] >= 10
    chapters = chapter_heading + '\n' + '\n'.join(f'{stamp(at)} {name}' for at, name in rows)
    credit_source = (OUT / 'MUSIC-CREDITS.txt').read_text()
    music = credit_source.split('In playback order:', 1)[1].split('The earlier C-major Prelude', 1)[0].strip()
    description = '\n\n'.join([intro, links, chapters, visual, music_heading + '\n' + music, hashtags(OWN[lang])])
    studio = tags(OWN[lang])
    settings = (
        'Main video / 主视频：../Curiosity Builds.mp4\n'
        f'Picture / 画面：1920×1080，30 fps，{int(total)//60}:{int(total)%60:02d}.{round(total*10)%10}，16:9\n'
        'Video language / 视频语言：English（英文画面文字，无配音）\n'
        'Audio / 音轨：仅古典配乐，无旁白；没有另一条语言配音\n'
        'Captions / 字幕：../Curiosity Builds.zh-CN.srt（简体中文，翻译画面标题与标签）\n'
        f'Thumbnail / 封面：youtube-cover.{lang}.jpg（本文件夹，1280×720；{"英文" if lang == "en" else "中文"} B 方案）\n'
        'Localized covers / 语言封面：youtube-cover.en.jpg（英文）；youtube-cover.zh.jpg（中文）\n'
        'English metadata / 英文标题简介：youtube-description.en.txt（主语言）\n'
        'Chinese metadata / 中文标题简介：youtube-description.zh.txt（同一影片的可选中文本地化）\n'
        'AI assets / 生成素材：概念草图与封面由 ImageGen 制作；Demo为项目录像\n'
        'Category / 类别：Education\n'
        'Audience and visibility / 观众与公开范围：由你在上传时决定'
    )
    content = (f'【标题 / Title】\n{TITLES[lang]}\n\n'
               f'【简介 / Description】\n{description}\n\n'
               f'【标签 / Tags】\n{studio}\n\n'
               f'【上传设置 / Upload settings】\n{settings}\n')
    assert len(TITLES[lang]) <= 100 and len(description) < 5000 and len(studio) <= 500
    assert description.splitlines()[-1] == hashtags(OWN[lang])
    assert studio == studio.lower()
    assert description.splitlines()[-1].split()[:len(DEFAULT)] == ['#' + t for t in DEFAULT]
    assert all(word.startswith('#') for word in studio.split())
    return content, {'title': TITLES[lang], 'description': description, 'tags': studio,
                     'hashtagLine': hashtags(OWN[lang]), 'chapterCount': len(rows),
                     'chapterStarts': [at for at, _ in rows], 'uploadSettings': settings,
                     'descriptionCharacters': len(description), 'tagCharacters': len(studio)}


def main():
    sheet = json.loads((FILM / 'records/chapters.json').read_text())
    verified = json.loads((FILM / 'records/verification.json').read_text())
    movie = Path(verified['full']['file'])
    total = float(probe(movie)['format']['duration'])
    assert total == 283.8 and verified['decode'] == {'returncode': 0, 'errors': ''}
    assert (DESKTOP / 'Curiosity Builds.mp4').stat().st_size == movie.stat().st_size
    assert (DESKTOP / 'Curiosity Builds.zh-CN.srt').is_file()
    DOC.mkdir(parents=True, exist_ok=True)
    DEST.mkdir(exist_ok=True)
    records = {}
    for lang in ('en', 'zh'):
        content, metadata = build(lang, sheet, total)
        name = f'youtube-description.{lang}.txt'
        for folder in (OUT, DOC, DEST):
            (folder / name).write_text(content, encoding='utf-8')
        records[lang] = {**metadata, 'file': str(DEST / name),
                         'sha256': sha(DEST / name), 'sourceMovieSha256': sha(movie)}
    covers = {}
    for lang, source in COVERS.items():
        cover = OUT / f'youtube-cover.{lang}.jpg'
        # Repository-standard export only; all visual editing was done with ImageGen.
        subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', str(source),
                        '-vf', 'scale=1280:720:flags=lanczos', '-q:v', '2', str(cover)], check=True)
        assert cover.stat().st_size < 2_000_000
        cover_info = probe(cover)['streams'][0]
        assert (cover_info['width'], cover_info['height']) == (1280, 720)
        shutil.copy2(cover, DEST / cover.name)
        covers[lang] = {'source': str(source), 'export': str(DEST / cover.name),
                        'width': 1280, 'height': 720, 'bytes': cover.stat().st_size,
                        'sha256': sha(cover),
                        'headline': 'FROM IDEAS / TO WORLDS' if lang == 'en' else '从想法 / 到世界'}
    manifest = {'layoutSource': 'README.md: YouTube tags', 'tagSource': 'scripts/youtube_tags.py',
                'mainLanguage': 'en', 'oneVideo': True, 'seconds': total,
                'sourceMovie': str(movie), 'sourceMovieSha256': sha(movie),
                'cover': {**covers['en'], 'headlineOwnerApproved': 'FROM IDEAS / TO WORLDS'},
                'covers': covers,
                'metadata': records}
    for target in (DOC / 'youtube.json', OUT / 'youtube-metadata.json',
                   DEST / 'youtube-metadata.json', FILM / 'records/youtube-package.json'):
        target.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    for lang, row in records.items():
        print(f'{lang}: {row["descriptionCharacters"]} description characters; '
              f'{row["tagCharacters"]} tag characters; {row["chapterCount"]} timed chapters')
    print(f'YouTube package: {DEST}')


if __name__ == '__main__':
    main()
