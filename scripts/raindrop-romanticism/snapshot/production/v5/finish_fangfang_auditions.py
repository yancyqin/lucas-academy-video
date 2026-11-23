"""Deliver short, accurately labelled voice auditions; leave the film untouched."""
import hashlib
import html
import json
from pathlib import Path
import subprocess
import wave

import numpy as np

from finish_auditions import normalize

P = Path(__file__).resolve().parent
SOURCE = P / 'auditions/2026-11-20-fangfang-minimax'
DEST = Path('@USER_HOME@/Desktop/肖邦配音试听-2026-11-20')
FF = '/opt/homebrew/bin/ffmpeg'


def excerpt(name, end):
    source = SOURCE / name / 'original.wav'
    target = source.with_name('audition.wav')
    subprocess.run([FF, '-v', 'error', '-y', '-i', str(source), '-t', str(end),
                    '-ar', '24000', '-ac', '1', str(target)], check=True)
    return target


def human_excerpts():
    # Each selection ends in a measured pause after a complete sentence.
    paths = [excerpt('owner-opening-fangfang-zh-vc', 13.65),
             excerpt('owner-quote-fangfang-zh-vc', 22.7)]
    parts = []
    for path in paths:
        with wave.open(str(path)) as reader:
            assert reader.getframerate() == 24000 and reader.getsampwidth() == 2
            parts.append(np.frombuffer(reader.readframes(reader.getnframes()), dtype='<i2'))
    joined = np.concatenate([parts[0], np.zeros(21600, dtype='<i2'), parts[1]])
    target = SOURCE / 'human-performance-fangfang-two-excerpts.wav'
    with wave.open(str(target), 'wb') as output:
        output.setparams((1, 2, 24000, 0, 'NONE', 'not compressed'))
        output.writeframes(joined.tobytes())
    return target


def main():
    DEST.mkdir(exist_ok=True)
    tracks = [
        dict(id='english-natural', title='英文 · MiniMax 自然叙事',
             method='MiniMax Speech 2.8 HD · 系统英文女声',
             source=SOURCE/'english-natural/original.mp3',
             file='06-MiniMax英文-自然叙事.mp3',
             note='先听这一条的叙事节奏与情绪。使用 Captivating Female 系统音色，未指定全程悲伤。'),
        dict(id='english-fangfang', title='英文 · MiniMax 演绎＋Fangfang 换声',
             method='MiniMax 自然英文 → 本地 CosyVoice3 换声',
             source=excerpt('minimax-fangfang-en-vc', 23.7),
             file='09-MiniMax演绎-Fangfang英文换声.mp3',
             note='上一条前半段转成 Fangfang 音色，保留源音频节奏。这是跨语言换声实验，可比较英语发音和音色变化。'),
        dict(id='english-louise', title='英文 · MiniMax 演绎＋Louise 换声',
             method='MiniMax 自然英文 → 本地 CosyVoice3 换声',
             source=SOURCE/'minimax-louise-en-vc/original.wav',
             file='10-MiniMax演绎-Louise英文换声.mp3',
             note='相同的英文叙事节选转成 Louise 音色。MiniMax 原生克隆待账号身份认证后再试，本条先比较 Louise 的声音是否更适合影片。'),
        dict(id='chinese-fangfang', title='中文 · MiniMax 演绎＋Fangfang 换声',
             method='MiniMax 自然中文 → 本地 CosyVoice3 换声',
             source=excerpt('minimax-fangfang-zh-vc', 25.1),
             file='07-MiniMax演绎-Fangfang中文换声.mp3',
             note='采用你喜欢的自然叙事版本，再转换为 Fangfang 音色。节选停在“你们已经死了”之后。'),
        dict(id='human-fangfang', title='中文 · 你的真人表演＋Fangfang 换声',
             method='你的两段录音 → 本地 CosyVoice3 换声',
             source=human_excerpts(),
             file='08-真人演绎-Fangfang情绪参考.mp3',
             note='两个节选，中间有短暂停顿：录音 1 的压力焦虑提问；录音 2 的肖邦惊呼与幻觉叙述。直接使用你的表演作为换声源，保留其语速、停顿和起伏；并非连贯的最终文案。'),
    ]
    cards, manifest = [], []
    for track in tracks:
        target = DEST / track['file']
        result = normalize(track['source'], target)
        subprocess.run([FF, '-v', 'error', '-i', str(target), '-f', 'null', '-'], check=True)
        entry = {**{key: str(value) for key, value in track.items()}, **result}
        entry['source_sha256'] = hashlib.sha256(track['source'].read_bytes()).hexdigest()
        manifest.append(entry)
        seconds = round(result['duration'])
        cards.append(f'''<article id="{track['id']}">
<p class="meta">{html.escape(track['method'])} · {seconds} 秒</p>
<h2>{html.escape(track['title'])}</h2><p>{html.escape(track['note'])}</p>
<audio controls preload="none" src="{html.escape(track['file'])}"></audio>
<a download href="{html.escape(track['file'])}">下载 MP3</a></article>''')
    page = '''<!doctype html><html lang="zh-CN"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Fangfang 与英文配音试听</title><style>
*{box-sizing:border-box}body{margin:0;background:#f5f1e9;color:#25211e;font-family:system-ui,sans-serif;line-height:1.8}
main{max-width:880px;margin:auto;padding:44px 24px 72px}h1{font-size:30px;line-height:1.35;margin:0 0 18px}
h2{font-size:21px;line-height:1.4;margin:4px 0 8px}p{margin:8px 0}.intro{color:#5d544a}
article{padding:26px 0;border-bottom:1px solid #d8cfc1}.meta{font-size:13px;color:#75634c}
audio{display:block;width:100%;margin:18px 0 12px}a{color:#73511d}aside{padding:16px 20px;background:#ece4d7;border-radius:10px;margin:28px 0}
.links{display:flex;gap:12px 24px;flex-wrap:wrap;font-size:14px}footer{font-size:14px;color:#5d544a;margin-top:32px}
</style><main><h1>Fangfang 与英文配音试听</h1>
<p class="intro">先比较感情、重音和停顿，再选音色。整片等你修改完文案后再做。这次只有短段干声，没有加入音乐或按画面加速。</p>
<aside>MiniMax 支持原生声音克隆，但当前账号创建克隆音色时返回 2038（voice clone user forbidden），
需要完成账号身份认证。本页的 Fangfang 样本采用本地换声方案。
<a href="https://platform.minimax.cn/docs/api-reference/errorcode" target="_blank" rel="noopener">官方错误码说明</a></aside>
<nav class="links"><a href="#english-natural">自然英文</a><a href="#english-fangfang">Fangfang 英文</a>
<a href="#english-louise">Louise 英文</a><a href="#chinese-fangfang">Fangfang 中文</a><a href="#human-fangfang">真人表演换声</a></nav>
''' + '\n'.join(cards) + '''
<footer>各条只用固定增益调整整体音量，不作动态压缩或语速拉伸。
真人表演样本保留原录音中的口误；换声对音色与细节的保留程度仍以试听为准。
<p><a href="试听.html">上一轮试听：真人原录音、原版 Fangfang、MiniMax 中文自然版与悲伤版</a></p></footer>
<script>document.querySelectorAll('audio').forEach(a=>a.addEventListener('play',()=>document.querySelectorAll('audio').forEach(b=>{if(b!==a)b.pause()})))</script>
</main></html>'''
    target_page = DEST / 'Fangfang与英文试听.html'
    target_page.write_text(page, encoding='utf-8')
    (SOURCE / 'audition-delivery.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    print(json.dumps({'page': str(target_page), 'tracks': manifest}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()


if __name__ == '__main__':
    main()
