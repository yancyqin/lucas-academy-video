"""Prepare level-matched dry voice auditions without changing performance timing."""
from pathlib import Path
import hashlib
import html
import json
import re
import subprocess
import wave

import numpy as np

P = Path(__file__).resolve().parent
SOURCE = P / 'auditions/2026-11-20-emotion'
DEST = Path('@USER_HOME@/Desktop/肖邦配音试听-2026-11-20')
FF = '/opt/homebrew/bin/ffmpeg'
PROBE = '/opt/homebrew/bin/ffprobe'


def normalize(source, destination):
    measurement = subprocess.run([FF, '-v', 'info', '-i', str(source), '-af',
        'loudnorm=I=-20:TP=-1.5:LRA=11:print_format=json', '-f', 'null', '-'],
        capture_output=True, text=True, check=True)
    matched = re.findall(r'\{\s*"input_i".*?\}', measurement.stderr, flags=re.S)
    assert len(matched) == 1
    measured = json.loads(matched[0])
    gain = min(-20 - float(measured['input_i']), -1.5 - float(measured['input_tp']))
    subprocess.run([FF, '-v', 'error', '-y', '-i', str(source), '-af', f'volume={gain:.4f}dB',
                    '-ar', '48000', '-ac', '1', '-codec:a', 'libmp3lame', '-q:a', '2',
                    str(destination)], check=True)
    info = json.loads(subprocess.check_output([PROBE, '-v', 'error', '-show_format', '-of', 'json',
                                              str(destination)]))['format']
    assert float(info['duration']) > 10
    return dict(duration=float(info['duration']), gain_db=round(gain, 3),
                sha256=hashlib.sha256(destination.read_bytes()).hexdigest())


def main():
    DEST.mkdir(exist_ok=True)
    snippets = []
    for identifier in ['p010', 'p011']:
        path = P / 'voices/fangfang-mandarin' / (identifier + '.wav')
        raw = subprocess.check_output([FF, '-v', 'error', '-i', str(path), '-ar', '48000',
                                       '-ac', '1', '-f', 'f32le', '-'])
        samples = np.frombuffer(raw, dtype='<f4')
        active = np.flatnonzero(np.abs(samples) > .002)
        snippets.append(samples[max(0, active[0] - 3200):min(len(samples), active[-1] + 4800)])
    baseline = SOURCE / 'cosyvoice3-fangfang-dry.wav'
    joined = np.concatenate([snippets[0], np.zeros(21600, dtype=np.float32), snippets[1]])
    with wave.open(str(baseline), 'wb') as output:
        output.setparams((1, 2, 48000, 0, 'NONE', 'not compressed'))
        output.writeframes(np.round(np.clip(joined, -1, 1) * 32767).astype('<i2').tobytes())

    tracks = [
        dict(id='human-opening', title='真人录音 1 · 开场', model='原录音',
             source=SOURCE/'input-recordings/New Recording.m4a', file='01-真人录音1-开场.mp3',
             note='只调整整体音量，保留原录音的语速、停顿和口误。'),
        dict(id='human-story', title='真人录音 2 · 马略卡雨夜', model='原录音',
             source=SOURCE/'input-recordings/New Recording 2.m4a', file='02-真人录音2-雨夜.mp3',
             note='含开头的一八三八年背景句；后半可与下面的 AI 试听比较。'),
        dict(id='cosyvoice', title='原版 Fangfang', model='CosyVoice 3 · 0.5B · 本地',
             source=baseline, file='03-CosyVoice3-Fangfang-原版干声.mp3',
             note='直接取现有 Fangfang 的生成干声，合成语速为 1.2。没有为了画面再加速。'),
        dict(id='minimax-auto', title='MiniMax · 自然叙事', model='Speech 2.8 HD · 阅历女声',
             source=SOURCE/'minimax-auto/original.mp3', file='04-MiniMax2.8HD-自然叙事.mp3',
             note='由模型根据文案推断情绪，合成语速为 1.0。'),
        dict(id='minimax-sad', title='MiniMax · 悲伤演绎', model='Speech 2.8 HD · 同一阅历女声',
             source=SOURCE/'minimax-sad/original.mp3', file='05-MiniMax2.8HD-悲伤演绎.mp3',
             note='与上一条使用相同音色和文案，明确指定 sad 情绪，合成语速为 1.0。'),
    ]
    cards = []
    manifest = []
    for track in tracks:
        target = DEST / track['file']
        receipt = normalize(track['source'], target)
        manifest.append({**{key: str(value) for key, value in track.items()}, **receipt})
        seconds = round(receipt['duration'])
        cards.append(f'''<article>
<p class="model">{html.escape(track['model'])} · {seconds // 60}:{seconds % 60:02d}</p>
<h2>{html.escape(track['title'])}</h2><p>{html.escape(track['note'])}</p>
<audio controls preload="none" src="{html.escape(track['file'])}"></audio>
<a download href="{html.escape(track['file'])}">下载这一条</a></article>''')

    text = json.loads((SOURCE / 'minimax-auto/request.json').read_text())['text']
    page = '''<!doctype html><html lang="zh-CN"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>肖邦配音试听</title><style>
*{box-sizing:border-box}body{margin:0;background:#f5f1e9;color:#25211e;font-family:system-ui,sans-serif;line-height:1.75}
main{max-width:880px;margin:auto;padding:44px 24px 72px}h1{font-size:32px;margin:0 0 12px}h2{font-size:21px;margin:4px 0 8px}
.intro{max-width:760px;color:#5d544a}article{padding:25px 0;border-bottom:1px solid #d8cfc1}p{margin:8px 0}
.model{font-size:13px;letter-spacing:.02em;color:#75634c}audio{display:block;width:100%;margin:18px 0 12px}
a{color:#73511d;font-size:14px}details{margin-top:32px}pre{font:inherit;white-space:pre-wrap}summary{cursor:pointer;font-weight:600}
</style><main><h1>肖邦配音试听</h1>
<p class="intro">先听语气、重音、停顿和情绪变化。各条使用固定增益调整整体音量，保留各自的表演节奏。
AI 三条采用同一段原稿；MiniMax 使用系统女声，与 Fangfang 音色不同。这轮供选择方向，正式影片等文案定稿后再制作。</p>
''' + '\n'.join(cards) + '<details><summary>查看 AI 试听文案</summary><pre>' + html.escape(text) + '''</pre></details>
<script>document.querySelectorAll('audio').forEach(a=>a.addEventListener('play',()=>document.querySelectorAll('audio').forEach(b=>{if(b!==a)b.pause()})))</script>
</main></html>'''
    (DEST / '试听.html').write_text(page, encoding='utf-8')
    (SOURCE / 'audition-delivery.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    print(json.dumps(manifest, ensure_ascii=False, indent=2), flush=True)


if __name__ == '__main__':
    main()
