"""Build the local, level-matched audition page without touching the film."""
from pathlib import Path
import html
import json
import subprocess

from finish_auditions import normalize

P=Path(__file__).resolve().parent
ROOT=P/'auditions/2026-11-20-alternative-providers'
DEST=Path('@USER_HOME@/Desktop/肖邦配音试听-2026-11-20')


def main():
    for identifier,filename in [('qwen3-local-zh','15-Qwen3本地-中文原始音色.mp3'),
                                ('qwen3-local-en','17-Qwen3本地-英文原始音色.mp3')]:
        source=ROOT/identifier/'original.wav'
        if source.is_file():normalize(source,DEST/filename)
    tracks=[
        dict(language='zh',title='MiniMax ＋ Fangfang',method='云端自然演绎 → 本地换声',
             file='07-MiniMax演绎-Fangfang中文换声.mp3',note='你已听过并认可的中文版本，作为本轮对照。'),
        dict(language='zh',title='MiniMax ＋ Eunice',method='本地换声免费 · 复用已有 MiniMax 演绎，本次未调用云端生成',
             file='19-MiniMax演绎-Eunice中文换声.mp3',
             note='同一段中文雨夜故事，改用 Eunice 的已有英语参考录音换声。保留中文内容与原演绎节奏；参考录音不影响输出语言。'),
        dict(language='zh',title='MiniMax ＋ Louise（中文音色）',method='本地换声免费 · 复用已有 MiniMax 演绎，本次未调用云端生成',
             file='21-MiniMax演绎-Louise中文换声.mp3',
             note='使用 Louise 的中文参考录音（louise/zh）。保留 MiniMax 的原演绎与节奏。'),
        dict(language='zh',title='MiniMax ＋ Sunny',method='本地换声免费 · 复用已有 MiniMax 演绎，本次未调用云端生成',
             file='23-MiniMax演绎-Sunny中文换声.mp3',
             note='使用 Sunny 的中文参考录音（sunny/zh），与 Fangfang、Eunice 和 Louise 比较。'),
        dict(language='zh',title='Qwen3-TTS 1.7B ＋ Fangfang',method='完全本地 MLX 生成 → 本地换声',
             file='16-Qwen3本地演绎-Fangfang中文换声.mp3',raw='15-Qwen3本地-中文原始音色.mp3',
             note='本地 CustomVoice 模型按自然、克制、有情绪变化的指令演绎，再转为 Fangfang。原始音色是 Vivian。'),
        dict(language='zh',title='Qwen3-TTS 1.7B ＋ Eunice',method='完全本地 MLX 生成 → 本地换声 · 无 API 费用',
             file='20-Qwen3本地演绎-Eunice中文换声.mp3',
             note='复用同一条 Qwen 中文演绎，改为 Eunice 音色。生成与换声都在本机完成，没有平台的每日或每月额度。'),
        dict(language='zh',title='Qwen3-TTS 1.7B ＋ Louise（中文音色）',method='完全本地 MLX 生成 → 本地换声 · 无 API 费用',
             file='22-Qwen3本地演绎-Louise中文换声.mp3',
             note='使用 Louise 的中文参考录音（louise/zh）。与其他 Qwen 中文条目使用相同演绎，可集中比较音色。'),
        dict(language='zh',title='Qwen3-TTS 1.7B ＋ Sunny',method='完全本地 MLX 生成 → 本地换声 · 无 API 费用',
             file='24-Qwen3本地演绎-Sunny中文换声.mp3',
             note='使用 Sunny 的中文参考录音（sunny/zh），生成与换声均在本机完成。'),
        dict(language='en',title='MiniMax ＋ Louise',method='云端自然演绎 → 本地换声',
             file='10-MiniMax演绎-Louise英文换声.mp3',note='你已听过并认可的英文版本，作为本轮对照。'),
        dict(language='en',title='Eleven v4 ＋ Louise',method='云端系统女声 Sarah → 本地换声',
             file='14-ElevenV4演绎-Louise英文换声.mp3',raw='11-ElevenV4-英文自然叙事.mp3',
             note='使用同一段英文，先由 Eleven v4 自然演绎，再转成 Louise。没有创建 ElevenLabs 克隆音色。'),
        dict(language='en',title='Qwen3-TTS 1.7B ＋ Louise',method='完全本地 MLX 生成 → 本地换声',
             file='18-Qwen3本地演绎-Louise英文换声.mp3',raw='17-Qwen3本地-英文原始音色.mp3',
             note='本地模型按自然叙事指令演绎，再转成 Louise。原始音色是英语系统男声 Aiden，可展开听原始表演。'),
        dict(language='en',title='Qwen3-TTS 1.7B · Serena 系统女声',method='完全本地 MLX 生成 · 直接女声，不经过换声',
             file='25-Qwen3系统女声-Serena英文原声.mp3',
             note='Serena 是温和的系统女声，此处跨语言朗读英语。官方预设的母语标为中文；不是英语母语女声，也没有后续换声。'),
        dict(language='en',title='Qwen3-TTS 1.7B · Vivian 系统女声',method='完全本地 MLX 生成 · 直接女声，不经过换声',
             file='26-Qwen3系统女声-Vivian英文原声.mp3',
             note='Vivian 是较明亮的系统女声，此处跨语言朗读英语。官方预设的母语标为中文；可与 Serena 及换成 Louise 的版本比较。'),
    ]
    cards=[];manifest=[]
    for track in tracks:
        path=DEST/track['file']
        if not path.is_file():continue
        subprocess.run(['/opt/homebrew/bin/ffmpeg','-v','error','-i',str(path),'-f','null','-'],check=True)
        seconds=float(subprocess.check_output(['/opt/homebrew/bin/ffprobe','-v','error','-show_entries',
            'format=duration','-of','default=nw=1:nk=1',str(path)]))
        raw=''
        if track.get('raw') and (DEST/track['raw']).is_file():
            raw=f'<details><summary>听原始音色，比较换声前后的表演</summary><audio controls preload="none" src="{html.escape(track["raw"])}"></audio></details>'
        cards.append(f'''<article data-language="{track['language']}">
<p class="meta">{html.escape(track['method'])} · {round(seconds)} 秒</p>
<h2>{html.escape(track['title'])}</h2><p>{html.escape(track['note'])}</p>
<audio controls preload="none" src="{html.escape(track['file'])}"></audio>
<a download href="{html.escape(track['file'])}">下载这一条</a>{raw}</article>''')
        manifest.append(dict(**track,seconds=seconds))
    text='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>配音短样对照</title><style>
*{box-sizing:border-box}body{margin:0;background:#f5f1e9;color:#25211e;font-family:system-ui,sans-serif;line-height:1.8}
main{max-width:880px;margin:auto;padding:40px 24px 72px}h1{font-size:30px;line-height:1.35;margin:0 0 16px}
h2{font-size:22px;line-height:1.4;margin:4px 0 10px}p{margin:8px 0}article{padding:25px 0;border-bottom:1px solid #d8cfc1}
.meta,footer{font-size:14px;color:#75634c}audio{display:block;width:100%;margin:18px 0 12px}a{color:#73511d}
nav{display:flex;gap:12px;margin:24px 0}button{font:inherit;border:1px solid #a99170;border-radius:20px;padding:5px 20px;background:transparent;cursor:pointer}
button[aria-pressed=true]{background:#73511d;color:#fff}details{margin-top:16px}summary{cursor:pointer;color:#73511d}footer{margin-top:28px}
</style><main><h1>配音短样对照</h1>
<p>同一段肖邦雨夜故事。先比较语气、重音、停顿和情绪变化；主要试听都换成相同的 Fangfang 或 Louise 音色。
各条只调整整体音量，没有为了影片拉伸语速。为便于公平比较，短样沿用前一轮试音文字；正式旁白使用已确认的新稿。新增中文 Eunice／Louise／Sunny 六条均复用已有演绎音频，只做本地换声，本轮没有新增云端语音生成请求。Louise 和 Sunny 使用中文参考录音。</p>
<nav aria-label="试听语言"><button type="button" data-filter="zh" aria-pressed="true">中文</button><button type="button" data-filter="en" aria-pressed="false">English</button></nav>
'''+'\n'.join(cards)+'''
<footer><p>Fish Audio 免费版：本轮中英文请求均返回 504 服务端超时，暂无可播放样本；没有切换付费型号。</p>
<p>Qwen3 使用 1.7B CustomVoice 的 8-bit MLX 版本。这里的 Fangfang／Eunice／Louise／Sunny 来自后续本地换声；CustomVoice 的情绪指导与 Base 模型的参考录音克隆属于不同模式。</p>
<p>费用区别：本地换声没有 API 费用，复用同一条已生成的音频换其他音色不需重新付云端生成费。MiniMax 和 Eleven 的新文字生成按用量收费或扣额度；Qwen 本地生成没有平台的每日／每月配额，长文仍需分段。<a href="https://elevenlabs.io/pricing" target="_blank" rel="noopener">ElevenLabs 官方额度与价格</a>。</p>
<p><a href="Fangfang与英文试听.html">上一轮：MiniMax 与真人表演换声</a> · <a href="试听.html">最初五条试听</a></p></footer>
<script>
const audios=[...document.querySelectorAll('audio')];
audios.forEach(a=>a.addEventListener('play',()=>audios.forEach(b=>{if(b!==a)b.pause()})));
function choose(lang){audios.forEach(a=>a.pause());document.querySelectorAll('article').forEach(a=>a.hidden=a.dataset.language!==lang);document.querySelectorAll('button[data-filter]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.filter===lang)));}
document.querySelectorAll('button[data-filter]').forEach(b=>b.addEventListener('click',()=>choose(b.dataset.filter)));choose('zh');
</script></main></html>'''
    page=DEST/'新模型对照试听.html';page.write_text(text,encoding='utf-8')
    (ROOT/'comparison-delivery.json').write_text(json.dumps(dict(page=str(page),tracks=manifest),ensure_ascii=False,indent=2))
    print(str(page),'tracks',len(manifest),flush=True)


if __name__=='__main__':main()
