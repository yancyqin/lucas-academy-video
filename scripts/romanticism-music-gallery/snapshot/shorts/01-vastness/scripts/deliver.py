from pathlib import Path
import json,shutil,hashlib,subprocess

ROOT=Path(__file__).resolve().parents[1]
DEST=Path('@USER_HOME@/Desktop/山、海、人间-短视频示范')
plan=json.loads((ROOT/'edit-plan.json').read_text())
verified=json.loads((ROOT/'checks/verified.json').read_text())
assert verified['status']=='passed' and verified['visual_review'].startswith('Passed')
if DEST.exists() and not (DEST/'校验记录.json').exists():
    raise RuntimeError('Refusing to replace an unrelated existing folder.')
DEST.mkdir(parents=True,exist_ok=True)
NAME='面对辽阔-竖屏示范'
source=ROOT/'exports'/(NAME+'.mp4');video=DEST/source.name
result=subprocess.run(['/bin/cp','-c',str(source),str(video)],capture_output=True,text=True)
if result.returncode:shutil.copy2(source,video)
assert hashlib.sha256(video.read_bytes()).hexdigest()==verified['video']['sha256']
shutil.copy2(ROOT/'subtitles'/(NAME+'.zh-Hans.srt'),DEST/(NAME+'.zh-Hans.srt'))

cues=[dict(start=c['start'],end=c['end'],text=c['zh'])for c in plan['labels']]
document='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>面对辽阔 · 竖屏示范</title><style>
body{margin:0;background:#101820;color:#f5eddf;font:16px/1.6 system-ui,sans-serif;padding:24px 18px}main{max-width:480px;margin:auto}h1{font-size:25px;margin:0}p{color:#bdc9d1}video{display:block;width:100%;max-height:78vh;aspect-ratio:9/16;background:black}video::cue{font-size:90%;background:rgba(0,0,0,.7)}a{color:#e3d3af}select{font:inherit;background:#1e303a;color:#eee;border:1px solid #78888f;padding:4px 10px}.links{display:flex;gap:18px;flex-wrap:wrap}
</style><main><h1>Facing the Vastness</h1><p>面对辽阔 · 58 秒 · 1080 × 1920<br>《雾海上的旅人》＋《吕根岛白垩岩》<br>肖邦《雨滴》片段 · 纯音乐，无配音</p>
<video controls playsinline preload="metadata" src="面对辽阔-竖屏示范.mp4"></video>
<p>中文字幕：<select aria-label="Chinese subtitles"><option value="off">关闭</option><option value="zh">显示中文</option></select></p>
<p class="links"><a href="面对辽阔-竖屏示范.mp4">视频文件</a><a href="面对辽阔-竖屏示范.zh-Hans.srt" download>中文 SRT</a><a href="素材署名.txt">素材署名</a></p>
<script id="captions" type="application/json">'''+json.dumps(cues,ensure_ascii=False).replace('</','<\\/')+'''</script>
<script>
const video=document.querySelector('video');const track=video.addTextTrack('subtitles','简体中文','zh-Hans');
for(const c of JSON.parse(document.getElementById('captions').textContent))track.addCue(new VTTCue(c.start,c.end,c.text));
track.mode='disabled';document.querySelector('select').addEventListener('change',e=>track.mode=e.target.value==='zh'?'showing':'disabled');
</script></main></html>'''
(DEST/'打开预览.html').write_text(document)
credits=json.loads((ROOT/'sources/credits.json').read_text())
lines=['面对辽阔 / Facing the Vastness','Yancy 与 Eunice 共同创作','',
       '58 秒竖屏示范，1080 × 1920，24 fps。英文画面，独立简体中文字幕。',
       '本次从当前 IS 浪漫主义大厅重新拍摄；展厅布局与物件位置保持当前源代码的设置。',
       '','重点画作 / Featured works']
for work in plan['artworks']:
    lines += [work['title_en']+' / '+work['title_zh'],work['artist_en']+' / '+work['artist_zh'],
              work['source'],work['license'],'']
music=plan['music']
lines += ['音乐 / Music','Chopin · Prelude in D-flat major, Op. 28 No. 15 “Raindrop”',
          'Jeannette Fang · Musopen recording · source catalog: '+music['license'],music['source'],
          '本支短片使用原选录音的前 58 秒，作固定音量调整与首尾淡入淡出。','',
          '大厅中的扫描模型 / Salon sculpture scans']
for scan in credits['sculpture_scans']:
    lines += [scan.get('model_title',scan['title_en']),scan.get('model_credit','SMK Open')+' · '+scan['license'],
              scan.get('model_source',scan['source']),scan['license_url'],'Modifications: '+scan['modifications'],'']
lines += ['Moose the Dragon — original sculpture and scan from Lucas Academy.']
(DEST/'素材署名.txt').write_text('\n'.join(lines)+'\n')
(DEST/'使用说明.txt').write_text('''面对辽阔 · 竖屏示范

主视频：面对辽阔-竖屏示范.mp4
中文字幕：面对辽阔-竖屏示范.zh-Hans.srt
打开预览.html：可在本地播放并切换中文字幕。

两幅画：弗里德里希《雾海上的旅人》《吕根岛白垩岩》。
镜头从当前 IS 大厅的自然画墙走近第一幅画，展示完整画作，推近人物，再拉回并走到相邻作品，推近白垩岩细节，最后退回大厅。
英文只标主题、曲目、画名与画家；中文 SRT 翻译这些标签。
时长 58 秒，1080 × 1920，24 fps，纯音乐、无人声。
音乐使用原选肖邦《雨滴》的前 58 秒。
''')
(DEST/'校验记录.json').write_text(json.dumps(verified,ensure_ascii=False,indent=2))
print(json.dumps({'folder':str(DEST),'video':str(video),'bytes':video.stat().st_size,'sha256':verified['video']['sha256']},ensure_ascii=False,indent=2))
