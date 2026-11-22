"""Build a self-contained local review page and used-media credits."""
from pathlib import Path
from PIL import Image
from html import escape
from urllib.parse import quote
import json, shutil, hashlib, math

ROOT=Path(__file__).resolve().parents[1]
plan=json.loads((ROOT/'edit-plan.json').read_text())
art=json.loads((ROOT/'sources/selected-artworks.json').read_text())
old=ROOT.parent.parent/'lucas-academy-video/sites/chopin-romanticism-selection/dist'
old_music={x['id']:x for x in json.loads((old/'music.json').read_text())}
music_ids={'rain':'prelude-28-15','nocturne':'nocturne-9-2','distance':'nocturne-c-sharp'}
music=[]
for t in plan['tracks']:
    if t['id'] in music_ids:
        original=old_music[music_ids[t['id']]]
        selected=old/original['audio']
        assert hashlib.sha256(selected.read_bytes()).hexdigest()==t['sha256']
        source=original['source'];license=original['license']
        note=original.get('creditNote','')
    elif t['id']=='life':
        original=json.loads((ROOT/'sources/pathetique-recording.json').read_text())
        source=original['source'];license=original['license'];note='Daniel Veesey 的完整录音。'
    else:
        source='https://commons.wikimedia.org/wiki/File:Beethoven_EgmontOvertureOp.84_LudwigVanBeethoven-EgmontOvertureOp.84.ogg'
        license='CC0 1.0';note='Musopen 录音；使用 Internet Archive 同一项目的 FLAC 母版。'
    music.append(dict(title=t['piece'],composer=t['composer'],performer=t['performer'],source=source,license=license,credit_note=note,local_file=str(Path(t['file']).relative_to(ROOT)),sha256=t['sha256'],duration=t['audio_duration'],start=t['start'],end=t['end'],constant_gain_db=t['gain_db']))

footage=[
    dict(title='走进画廊',creator='Charlotte May',source='https://www.pexels.com/video/arts-inside-a-gallery-5824200/',license='Pexels License',license_url='https://www.pexels.com/license/',file='footage/gallery-5824200.mp4',note='博物馆环境实拍；未将场馆或墙上作品标为特定浪漫主义馆藏。'),
    dict(title='观看的人',creator='Antoni Shkraba',source='https://www.pexels.com/video/friends-looking-at-the-exhibition-of-paintings-7986431/',license='Pexels License',license_url='https://www.pexels.com/license/',file='footage/visitors-7986431.mp4',note='博物馆环境实拍。'),
    dict(title='《最后的莫希干人》',creator='Maurice Tourneur / Clarence Brown，1920',source='https://archive.org/details/PublicdomainTheLastoftheMohicans',license='Public domain',file='footage/mohicans-1920-public-domain.mp4',note='库珀小说改编的默片。使用 596–604 秒、1077–1085 秒附近两段，未使用源片音轨；是文学改编画面，并非历史事件的纪实影像。'),
    dict(title='《雾海上的旅人》艺术延展',creator='上一部影片已有素材',source='Previous owner-created film',license='Owner-provided',file=str(old/'assets/video/wanderer.mp4'),note='沿用旧片 10 秒艺术延展动态。')
]
for f in footage:
    p=Path(f['file'])
    if not p.is_absolute():p=ROOT/p
    f['sha256']=hashlib.sha256(p.read_bytes()).hexdigest()
credits=dict(title=plan['title'],music=music,artworks=art,footage=footage,audio_policy=plan['audio_policy'],curatorial_note=plan['curatorial_note'])
(ROOT/'sources/credits.json').write_text(json.dumps(credits,ensure_ascii=False,indent=2))

thumbs=ROOT/'thumbs';thumbs.mkdir(exist_ok=True)
for a in art:
    im=Image.open(a['file']).convert('RGB');im.thumbnail((720,480),Image.Resampling.LANCZOS)
    im.save(thumbs/(a['id']+'.webp'),quality=86)
shutil.copyfile(ROOT/'checks/render-opening.jpg',ROOT/'poster.jpg')

def stamp(n):
    n=max(0,math.floor(n));return f'{n//60:02}:{n%60:02}'
def link(s):return quote(s,safe='/:')
first={}
for s in plan['shots']:
    if s['type']=='art' and s['asset_id'] not in first:first[s['asset_id']]=s
ordered=sorted(art,key=lambda a:first[a['id']]['global_start'])
cards=[]
for a in ordered:
    s=first[a['id']];part='nature' if s['track'] in music_ids else 'human'
    date=a.get('dateLabel',str(a.get('year','')))
    desc=a.get('description',a.get('curatorial_note',''))
    cards.append(f'''<article class="art-card" data-part="{part}">
      <button class="art-image" data-seek="{s['global_start']}" aria-label="播放《{escape(a['title'])}》所在段落"><img loading="lazy" src="thumbs/{a['id']}.webp" alt="{escape(a['artist'])}《{escape(a['title'])}》"><span>▶ {stamp(s['global_start'])}</span></button>
      <div class="art-copy"><p class="art-date">{escape(date)}</p><h3>{escape(a['title'])}</h3><p class="artist">{escape(a['artist'])}</p>
      <p class="art-desc">{escape(desc)}</p><div class="art-links"><a href="art/{a['id']}.jpg" target="_blank">查看大图 ↗</a><a href="{escape(a.get('source',a.get('imageSource','')))}" target="_blank" rel="noopener">作品资料 ↗</a></div></div></article>''')

visuals=[
    '乡野与白垩岩 → 雨雾、冰海、火山 → 辽阔山谷。',
    '战舰的黄昏 → 蒸汽与海浪 → 荒野暮色与望月的人。',
    '旅人的背影 → 修道院遗迹 → 安第斯与山间光线。',
    '肖像与文学人物 → 科尔《生命之旅》四联画。',
    '脆弱的人 → 战争与海难 → 《自由引导人民》。'
]
rows=[];chapters=[]
for i,(t,m) in enumerate(zip(plan['tracks'],music)):
    rows.append(f'''<tr><td><button data-seek="{t['start']}" class="time-link">{stamp(t['start'])} ↗</button></td><td><strong>{escape(t['title'])}</strong><span>{escape(t['composer'])} · {escape(t['piece'])}</span></td><td>{visuals[i]}</td></tr>''')
    chapters.append(f'''<button class="chapter" data-seek="{t['start']}" data-track="{t['id']}"><span>{i+1:02} / {stamp(t['start'])}</span><strong>{escape(t['title'])}</strong><small>{escape(t['composer'])}</small></button>''')

music_credits=[]
for m in music:
    music_credits.append(f'''<li><strong>{escape(m['composer'])} · {escape(m['title'])}</strong><br>{escape(m['performer'])} · {escape(m['license'])} · <a target="_blank" rel="noopener" href="{escape(m['source'])}">录音来源 ↗</a><p>{escape(m['credit_note'])}</p></li>''')
footage_credits=[]
for f in footage:
    source=f'<a href="{escape(f["source"])}" target="_blank" rel="noopener">来源 ↗</a>' if f['source'].startswith('https://') else '沿用旧片'
    footage_credits.append(f'<li><strong>{escape(f["title"])}</strong> · {escape(f["creator"])} · {escape(f["license"])} · {source}<p>{escape(f["note"])}</p></li>')

files={
    'full':dict(src='exports/山海与人间-浪漫主义纯音乐版.mp4',label='完整影片',offset=0,duration=plan['duration']),
    'nature':dict(src='exports/自然篇-肖邦-纯音乐版.mp4',label='自然篇 · 肖邦',offset=0,duration=plan['tracks'][2]['end']),
    'human':dict(src='exports/人间篇-贝多芬-纯音乐版.mp4',label='人间篇 · 贝多芬',offset=plan['tracks'][3]['start'],duration=plan['duration']-plan['tracks'][3]['start'])
}
data=dict(files=files,tracks=[dict(id=t['id'],start=t['start'],end=t['end'],title=t['title'],piece=t['piece'],composer=t['composer']) for t in plan['tracks']])

html='''<!doctype html><html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>山海与人间 · 浪漫主义音乐画廊</title><style>
:root{color-scheme:dark;--bg:#0b1214;--panel:#141e20;--text:#f1ecdf;--muted:#aabbb4;--line:#32413e;--accent:#d5c99c}*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--bg);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft Yahei",sans-serif;line-height:1.7}a{color:var(--accent);text-underline-offset:4px}button{font:inherit;color:inherit;cursor:pointer}button:focus-visible,a:focus-visible,summary:focus-visible{outline:2px solid var(--accent);outline-offset:5px}.shell{width:min(1220px,calc(100% - 64px));margin:auto}header{padding:46px 0 26px;border-bottom:1px solid var(--line)}.eyebrow{font-size:12px;letter-spacing:.2em;text-transform:uppercase;color:var(--muted);margin:0 0 12px}h1{font-family:"Songti SC","STSong",serif;font-weight:500;font-size:clamp(38px,6vw,66px);line-height:1.2;margin:0 0 16px;letter-spacing:.05em}.subtitle{font-size:17px;color:var(--muted);margin:0;max-width:800px}.meta{display:flex;gap:20px;flex-wrap:wrap;margin:22px 0 0;font-size:12px;color:var(--accent)}nav{display:flex;gap:10px;flex-wrap:wrap;margin:28px 0 16px}.mode,.filter{background:transparent;border:1px solid var(--line);border-radius:999px;padding:9px 19px}.mode[aria-pressed=true],.filter[aria-pressed=true]{background:var(--text);color:var(--bg);border-color:var(--text)}.screen{background:#000;border:1px solid var(--line);border-radius:7px;overflow:hidden}video{display:block;width:100%;aspect-ratio:16/9;background:#070c0d}.player-foot{display:flex;justify-content:space-between;align-items:center;gap:16px;flex-wrap:wrap;padding:13px 18px;background:var(--panel);font-size:13px}#playing{color:var(--muted)}.chapter-strip{display:grid;grid-template-columns:repeat(5,1fr);gap:10px;margin-top:15px}.chapter{background:var(--panel);border:1px solid var(--line);border-radius:5px;padding:14px;text-align:left}.chapter span,.chapter small{display:block;color:var(--muted);font-size:11px}.chapter strong{display:block;font-size:15px;font-weight:500;margin:5px 0}.chapter.active{border-color:var(--accent);box-shadow:inset 0 -2px var(--accent)}.chapter:disabled{opacity:.35;cursor:default}section{margin:55px 0}h2{font-family:"Songti SC","STSong",serif;font-weight:500;font-size:30px;margin:0 0 15px}p{margin-top:0}.intro{max-width:840px;color:var(--muted);font-size:15px}.table-wrap{overflow-x:auto}table{width:100%;border-collapse:collapse;text-align:left;font-size:14px}td,th{border-bottom:1px solid var(--line);padding:17px 16px;vertical-align:top}th{color:var(--muted);font-size:12px;font-weight:400}td:first-child{width:95px;padding-left:0}td:nth-child(2){width:43%}td span{display:block;color:var(--muted);font-size:12px;margin-top:3px}td:last-child{color:var(--muted)}.time-link{border:0;padding:0;background:none;color:var(--accent);white-space:nowrap}.section-top{display:flex;align-items:center;justify-content:space-between;gap:14px;flex-wrap:wrap}.filters{display:flex;gap:8px}.filter{font-size:12px;padding:6px 15px}.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:20px;margin-top:25px}.art-card{border:1px solid var(--line);background:var(--panel);border-radius:7px;overflow:hidden;min-width:0}.art-card[hidden]{display:none}.art-image{display:block;position:relative;border:0;width:100%;height:232px;background:#080f11;padding:15px}.art-image img{height:100%;width:100%;object-fit:contain;transition:transform .3s}.art-image:hover img{transform:scale(1.02)}.art-image span{position:absolute;bottom:8px;right:9px;background:#071012dc;color:#e8e2d0;border:1px solid #64716a;font-size:11px;padding:1px 7px;border-radius:20px}.art-copy{padding:20px}.art-date{font-size:10px;color:var(--accent);letter-spacing:.02em;margin:0 0 6px}h3{font-size:17px;font-weight:500;line-height:1.55;margin:0 0 8px}.artist{font-size:12px;color:var(--muted);margin-bottom:14px}.art-desc{font-size:12px;color:var(--muted);margin:0 0 18px;line-height:1.85}.art-desc:empty{display:none}.art-links{display:flex;gap:20px;font-size:11px;flex-wrap:wrap}.note{font-size:12px;color:var(--muted)}.downloads{display:flex;gap:12px;flex-wrap:wrap}.download{border:1px solid var(--line);border-radius:5px;padding:13px 18px;text-decoration:none;font-size:14px;background:var(--panel)}details{border-top:1px solid var(--line);padding:18px 0}summary{cursor:pointer;color:var(--accent);font-size:15px}.credits{font-size:13px;padding-left:24px;color:var(--muted);max-width:950px}.credits li{padding:13px 0}.credits p{font-size:12px;margin:6px 0 0}.credits strong{color:var(--text);font-weight:400}footer{border-top:1px solid var(--line);padding:26px 0 45px;font-size:12px;color:var(--muted)}.previous{margin-top:25px;padding-top:20px;border-top:1px solid var(--line);font-size:13px}.previous a{margin-right:23px}#notice{margin:12px 0;min-height:22px;font-size:12px;color:var(--muted)}@media(max-width:850px){.grid{grid-template-columns:repeat(2,minmax(0,1fr))}.chapter-strip{grid-template-columns:repeat(3,1fr)}.shell{width:calc(100% - 36px)}.art-image{height:220px}td,th{padding:14px 10px}td:nth-child(2){width:45%}}@media(max-width:520px){header{padding-top:30px}.shell{width:calc(100% - 28px)}.subtitle{font-size:14px}.meta{gap:10px 18px}.chapter-strip{grid-template-columns:repeat(2,1fr)}.chapter{padding:11px}.mode{padding:8px 13px;font-size:12px}.grid{grid-template-columns:1fr}.art-image{height:260px}.player-foot{padding:12px;font-size:11px}section{margin:38px 0}h2{font-size:25px}table{min-width:610px}.downloads{display:grid}.art-copy{padding:18px}.previous a{display:block;margin:12px 0}}@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}.art-image img{transition:none}}
</style></head><body><main class="shell"><header><p class="eyebrow">Yancy & Eunice · A Musical Gallery</p><h1>山海与人间</h1><p class="subtitle">浪漫主义音乐画廊。随肖邦走入自然，随贝多芬回望人的生命、苦难与自由。</p><div class="meta"><span>纯音乐 · 无配音</span><span>34 件作品</span><span>5 首完整录音</span><span>1080p · 约 29 分钟</span></div></header>
<p class="shared-salon"><a class="download" href="http://127.0.0.1:8095/?world=museum&room=romanticism-salon"><span>走进共用的 IS 浪漫主义沙龙 · 56 件平面作品与九座雕塑展台</span><br><span>Enter the shared IS Romantic Salon · 56 artworks and nine sculpture plinths</span></a></p>
<nav aria-label="选择影片"><button class="mode" data-mode="full" aria-pressed="true">完整影片</button><button class="mode" data-mode="nature" aria-pressed="false">自然篇 · 肖邦</button><button class="mode" data-mode="human" aria-pressed="false">人间篇 · 贝多芬</button></nav>
<div class="screen" id="player"><video id="film" controls playsinline preload="metadata" poster="poster.jpg" src="exports/山海与人间-浪漫主义纯音乐版.mp4" aria-label="山海与人间，纯音乐影片"></video><div class="player-foot"><span id="playing">完整影片 · 29:00</span><a id="download-current" href="exports/山海与人间-浪漫主义纯音乐版.mp4" download>下载当前影片 ↓</a></div></div>
<div class="chapter-strip" aria-label="音乐章节">__CHAPTERS__</div><p id="notice" role="status" aria-live="polite"></p>
<section><h2>五段音乐，一次漫游</h2><p class="intro">从乡间水面出发，进入风暴、冰海与暮色；再从一个人的凝望，走向一生的起伏与自由的呼唤。三首肖邦沿用你选定的录音。作品之间缓慢叠化，每幅画的题签在开头短暂出现。</p><div class="table-wrap"><table><thead><tr><th>完整影片时间</th><th>章节 / 音乐</th><th>画面编排</th></tr></thead><tbody>__ROWS__</tbody></table></div><p class="note" style="margin-top:16px">这些配对是本片的策展联想。米莱、沃特豪斯的文学绘画作为浪漫主义意象的后续回响加入。含裸体的原作保留为静态展示。</p></section>
<section><div class="section-top"><h2>画廊 · 按首次出场顺序</h2><div class="filters" aria-label="画作筛选"><button class="filter" data-filter="all" aria-pressed="true">全部 34</button><button class="filter" data-filter="nature" aria-pressed="false">自然</button><button class="filter" data-filter="human" aria-pressed="false">人间</button></div></div><p class="note">点击画面播放对应段落；点击“查看大图”可单独欣赏原作。</p><div class="grid">__CARDS__</div></section>
<section><h2>保存影片</h2><div class="downloads"><a class="download" href="exports/山海与人间-浪漫主义纯音乐版.mp4" download>完整影片 · 29 分钟 ↓</a><a class="download" href="exports/自然篇-肖邦-纯音乐版.mp4" download>自然篇 · 肖邦 ↓</a><a class="download" href="exports/人间篇-贝多芬-纯音乐版.mp4" download>人间篇 · 贝多芬 ↓</a></div><div class="previous">另一期：<a href="../raindrop-romanticism/production/视频预览.html">《压力？焦虑？肖邦？浪漫？》配音预览 ↗</a><a href="../raindrop-romanticism/压力焦虑肖邦浪漫-最终版文案.docx" download>最终版文案 · Word ↓</a></div></section>
<section><details><summary>音乐录音与来源</summary><ul class="credits">__MUSIC_CREDITS__</ul><p class="note">五份完整录音按顺序播放，只调整固定增益以衔接音量，保留音乐自身的强弱变化。影片没有旁白，也没有混入素材视频的原音。</p></details><details><summary>实拍与电影片段</summary><ul class="credits">__FOOTAGE_CREDITS__</ul></details><details><summary>画作资料与完整素材清单</summary><p class="note" style="margin-top:16px">画作资料链接列在每张作品卡片下。所用作品均为公有领域原作，数字图像的来源与署名、录音许可及素材哈希汇总于 <a href="sources/credits.json" download>完整素材清单 JSON ↓</a>。</p></details></section>
<footer>山海与人间 · 浪漫主义音乐画廊<br>Yancy 与 Eunice 共同创作</footer></main>
<script id="program-data" type="application/json">__DATA__</script><script>
const program=JSON.parse(document.getElementById('program-data').textContent),film=document.getElementById('film'),notice=document.getElementById('notice');let mode='full';
const time=s=>{s=Math.max(0,Math.floor(s));return String(Math.floor(s/60)).padStart(2,'0')+':'+String(s%60).padStart(2,'0')};
function setMode(next,seek=null,play=false){const f=program.files[next];mode=next;document.querySelectorAll('.mode').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.mode===mode)));document.getElementById('download-current').href=f.src;document.getElementById('playing').textContent=f.label+' · '+time(f.duration);document.querySelectorAll('.chapter').forEach(b=>{const t=program.tracks.find(t=>t.id===b.dataset.track);b.disabled=t.start<f.offset||t.start>=f.offset+f.duration});const action=()=>{if(seek!==null)film.currentTime=Math.max(0,seek-f.offset);if(play)film.play().catch(()=>{notice.textContent='已跳到对应画面，点击播放器中的播放键即可。'});update()};if(film.getAttribute('src')!==f.src){film.pause();film.src=f.src;film.addEventListener('loadedmetadata',action,{once:true});film.load()}else action()}
function jump(seconds){let f=program.files[mode];if(seconds<f.offset||seconds>=f.offset+f.duration)setMode('full',seconds,true);else setMode(mode,seconds,true);document.getElementById('player').scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth',block:'center'})}
function update(){const at=film.currentTime+program.files[mode].offset;let t=program.tracks.find(t=>at>=t.start&&at<t.end);document.querySelectorAll('.chapter').forEach(b=>b.classList.toggle('active',!!t&&b.dataset.track===t.id));document.getElementById('playing').textContent=program.files[mode].label+' · '+(t?t.composer+' / '+t.title:time(program.files[mode].duration))}
document.querySelectorAll('[data-seek]').forEach(b=>b.addEventListener('click',()=>jump(Number(b.dataset.seek))));document.querySelectorAll('.mode').forEach(b=>b.addEventListener('click',()=>setMode(b.dataset.mode)));document.querySelectorAll('.filter').forEach(b=>b.addEventListener('click',()=>{document.querySelectorAll('.filter').forEach(q=>q.setAttribute('aria-pressed',String(q===b)));document.querySelectorAll('.art-card').forEach(c=>c.hidden=b.dataset.filter!=='all'&&c.dataset.part!==b.dataset.filter)}));film.addEventListener('timeupdate',update);film.addEventListener('error',()=>{notice.textContent='播放器未能载入影片，可使用“下载当前影片”在本机播放器中打开。'});setMode('full');
</script></body></html>'''
for key,value in {'__CHAPTERS__':'\n'.join(chapters),'__ROWS__':'\n'.join(rows),'__CARDS__':'\n'.join(cards),'__MUSIC_CREDITS__':'\n'.join(music_credits),'__FOOTAGE_CREDITS__':'\n'.join(footage_credits),'__DATA__':json.dumps(data,ensure_ascii=False).replace('</',r'<\/')}.items():html=html.replace(key,value)
(ROOT/'视频预览.html').write_text(html)
print('REVIEW READY',len(ordered),'artworks',len(music),'recordings')
