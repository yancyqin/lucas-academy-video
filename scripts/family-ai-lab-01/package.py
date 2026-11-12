"""Prepare the approved film and selected frame covers for a single bilingual upload."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
from youtube_tags import hashtags, tags

DEST = Path.home() / 'Desktop/家庭AI实验室-感知机-上传'
STEM = 'family-ai-lab-perceptron'
TITLES = {
    'en': '3 million times faster than Claude Fable 5.1. 10 million times faster than GPT-6-Astra!',
    'zh': '比Claude Fable 5.1快300万倍，比GPT-6-Astra快1000万倍！',
}
OWN = {
    'en': ['familyailab', 'perceptron', 'machinelearning', 'aiforkids', 'artificialintelligence', 'rosenblatt'],
    'zh': ['家庭ai实验室', '感知机', '机器学习', '亲子实验', '人工智能', '科普'],
}
CHAPTERS = {
    'en': ['Back to 1957 and the race', 'The speed headline', 'Pictures become numbers', 'Be a neuron',
           'Teach the browser lab', 'Meet the perceptron', 'From one neuron to modern AI', 'Try it at the family table'],
    'zh': ['穿越到1957，开始比赛', '速度标题', '图片变成数字', '你来当神经元',
           '教网页实验室认图', '揭晓感知机', '从一个神经元到今天的AI', '在家和孩子一起试试'],
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def probe(path):
    return json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_streams',
                                              '-show_format', '-of', 'json', str(path)]))


def audio_hash(path, index):
    return subprocess.check_output(['ffmpeg', '-v', 'error', '-i', str(path), '-map', f'0:a:{index}',
                                    '-c:a', 'copy', '-f', 'hash', '-hash', 'sha256', '-'], text=True).strip()


def upload_text(lang, timeline, values):
    if lang == 'en':
        intro = ("Let’s take Claude Fable 5.1 and GPT-6-Astra back to 1957 for an AI speed race. "
                 "Then try it at your family table: turn pictures into zeros and ones, play a neuron, "
                 "and teach the browser lab with your own examples.\n\n"
                 f"The perceptron trained on {values['train_n']} pictures. The JavaScript version took "
                 f"{values['x_us']} microseconds per picture on this computer. It got all ten test pictures right.\n\n"
                 "The title is a bit of a tease. This model has one job: recognizing sevens. "
                 "Winning that speed test doesn’t make it smarter overall. The experiment helps us and our kids see how machines learn.")
        lab = 'Try the lab and printable worksheets: https://ai.lucasacademy.org/'
        heading = 'Chapters'
        credit = ('By Lucas Academy Team\n'
                  'Narration: Louise, synthetic voice in English and Chinese.\n'
                  'Imagined time-travel, lab and family footage: Muse. Period sets: ImageGen. '
                  'Diagrams, original experiment records and browser capture: Lucas Academy.')
        method = 'Experiment: the selected original full round; medians on the same 20×20 input task. No overall model-ability ranking is implied.'
    else:
        intro = ("带上 Claude Fable 5.1 和 GPT-6-Astra，穿越到一九五七年。先来场认数字七的速度比赛，再回到家里的餐桌，拿纸和笔试试：一张图怎么变成数字，机器又怎么从例子里学？\n\n"
                 f"这一轮，感知机学过{values['train_n']}张图。JavaScript 版判断一张只用{values['x_us']}微秒。十张测试图全部答对。\n\n"
                 "标题玩了个噱头。这个模型专门认七，跑得快不代表整体能力更强。做这个实验，是为了和孩子一起看懂机器怎么学。")
        lab = '实验室和学习单：https://ai.lucasacademy.org/'
        heading = '章节'
        credit = ('作者：Lucas Academy Team\n'
                  '配音：Louise，中英文合成旁白。\n'
                  '穿越、机房和家庭示意片段：Muse；复古场景底图：ImageGen；图解、原始实验记录和网页录屏：Lucas Academy。')
        method = '实验沿用原始整轮记录，同一项20×20图片任务，用时取中位数；不作模型整体能力排名。'
    chapters = []
    for scene, name in enumerate(CHAPTERS[lang], 1):
        seconds = int(next(line['from'] for line in timeline['lines'] if line['scene'] == scene) / timeline['fps'])
        chapters.append(f'{seconds//60}:{seconds%60:02} {name}')
    sources = ('Rosenblatt, The Perceptron (1957): '
               'https://perceptrondemo.com/assets/rosenblatt-perceptron-perceiving-1957-1ea0ab61.pdf')
    description = '\n\n'.join([intro, lab, heading+'\n'+'\n'.join(chapters), method, sources, credit, hashtags(OWN[lang])])
    assert len(TITLES[lang]) <= 100
    assert len(description) < 5000
    settings = (f'主视频 / Main video: {STEM}.mp4\n'
                '原始语言 / Original language: English\n'
                f'独立中文配音 / Chinese audio: {STEM}.zh.m4a\n'
                f'独立英文配音 / English audio: {STEM}.en.m4a\n'
                f'字幕 / Captions: {STEM}.en.srt; {STEM}.zh-Hans.srt\n'
                f'封面 / Thumbnail: cover.{lang}.jpg\n'
                '中英文标题与简介用于同一影片的语言版本 / Localized metadata for one shared video\n'
                '类别 / Category: Education')
    return f'【标题 / Title】\n{TITLES[lang]}\n\n【简介 / Description】\n{description}\n\n【标签 / Tags】\n{tags(OWN[lang])}\n\n【上传设置 / Upload settings】\n{settings}\n'


def main():
    assert not DEST.exists(), f'Refusing to replace an existing upload folder: {DEST}'
    source = ROOT / 'out/family-ai-lab-01/delivery/v3'
    film = source / 'family-ai-lab-01.bilingual.mp4'
    approved = json.loads((ROOT/'docs/family-ai-lab-01/verification.json').read_text())
    assert sha(film) == approved['filmSha256'], 'Approved film changed'
    covers = json.loads((ROOT/'docs/family-ai-lab-01/cover-frame-02.json').read_text())
    timeline = json.loads((ROOT/'public/family-ai-lab-01/timeline.json').read_text())
    values = json.loads((ROOT/'docs/family-ai-lab-01/selected-data.json').read_text())['derived']
    with tempfile.TemporaryDirectory(prefix='.fal01-upload-', dir=DEST.parent) as temporary:
        folder = Path(temporary) / DEST.name
        folder.mkdir()
        shutil.copy2(film, folder/f'{STEM}.mp4')
        assert sha(folder/f'{STEM}.mp4') == approved['filmSha256']
        for source_lang, dest_lang in [('en', 'en'), ('zh-Hans', 'zh-Hans')]:
            src = source/f'{source_lang}.srt';dest = folder/f'{STEM}.{dest_lang}.srt'
            shutil.copy2(src, dest);assert sha(src) == sha(dest)
        audio = {}
        for index, lang in enumerate(('en', 'zh')):
            dest = folder/f'{STEM}.{lang}.m4a'
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(film), '-map', f'0:a:{index}',
                            '-c:a', 'copy', '-metadata', f'language={"eng" if lang=="en" else "zho"}',
                            '-movflags', '+faststart', str(dest)], check=True)
            info = probe(dest)
            assert len(info['streams']) == 1 and info['streams'][0]['codec_name'] == 'aac'
            assert abs(float(info['format']['duration'])-445.5) < .1
            assert audio_hash(film,index) == audio_hash(dest,0)
            audio[lang] = {'seconds':float(info['format']['duration']), 'encodedAudioMatchesMovie':True}
        for record in covers['covers']:
            if not record['path'].endswith('.jpg'):continue
            src = ROOT/record['path'];dest = folder/f"cover.{record['language']}.jpg"
            assert sha(src) == record['sha256'];shutil.copy2(src,dest)
            image = probe(dest)['streams'][0]
            assert (image['width'],image['height']) == (1280,720)
            assert dest.stat().st_size < 2_000_000
        for lang in ('en','zh'):
            (folder/f'youtube-description.{lang}.txt').write_text(upload_text(lang,timeline,values))
        (folder/'NOTES.txt').write_text(
            '家庭AI实验室 · 感知机 · 上传包\n\n'
            f'主文件：{STEM}.mp4\n'
            '这是已确认的完整v3影片，7分25.5秒，1920×1080，30fps。英文默认，中文为第二条音轨；画面无字幕。\n'
            '另附中英文M4A独立音轨，供平台单独接收配音文件时使用。两条配音均直接从本包主影片无损提取，起止时间一致。\n'
            'en.srt是英文字幕，zh-Hans.srt是简体中文字幕，按需要单独导入。\n'
            'cover.en.jpg / cover.zh.jpg 是本次选定的封面：背景取影片00:02对应的无字原始帧，标题由代码排版。\n'
            'youtube-description.en.txt / .zh.txt 包含对应标题、简介、章节、标签和文件设置；中英文属于同一影片。\n'
            'SHA256SUMS用于核对文件；PACKAGE.json记录本包版本和校验结果。\n')
        records = {str(path.relative_to(folder)):{'bytes':path.stat().st_size,'sha256':sha(path)}
                   for path in sorted(folder.rglob('*')) if path.is_file()}
        receipt = {'destination':str(DEST),'filmVisualRevision':3,'filmSha256':approved['filmSha256'],
                   'seconds':445.5,'defaultLanguage':'en','audio':audio,'embeddedSubtitles':0,
                   'coverBackgroundSeconds':2,'coverRecord':'docs/family-ai-lab-01/cover-frame-02.json','files':records}
        (folder/'PACKAGE.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
        files = sorted(path for path in folder.rglob('*') if path.is_file())
        sums = ''.join(sha(path)+'  '+str(path.relative_to(folder))+'\n' for path in files)
        (folder/'SHA256SUMS').write_text(sums)
        for row in sums.splitlines():
            digest,name=row.split('  ',1);assert sha(folder/name) == digest
        folder.rename(DEST)
    (ROOT/'docs/family-ai-lab-01/upload-package.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
    print('Upload package:',DEST)
    print('Verified files:',len(list(DEST.iterdir())))


if __name__ == '__main__':
    main()
