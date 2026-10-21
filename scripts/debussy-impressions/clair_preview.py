"""Build the 月光 (Clair de lune) review page: arrangement + photo -> painting for every shot.

Reads edits/03-clair.json, clair/candidates.json (Pexels credits), clair/frames/frames.json,
clair/paint/generated-assets.json (painter manner per AI painting) and paintings.json (the three real ones).
Writes OUTDIR/index.html and OUTDIR/img/*.jpg (960 px wide).
Usage: .venv-reframe/bin/python clair_preview.py OUTDIR
"""
import html, json, os, sys
from PIL import Image

D = '/Users/yqin/repo/playground/lucas-academy-video-data/debussy-impressions'
HERE = os.path.dirname(os.path.abspath(__file__))
out = sys.argv[1]; os.makedirs(f'{out}/img', exist_ok=True)
e = html.escape
ed = json.load(open(f'{HERE}/edits/03-clair.json'))
cands = {c['id']: c for c in json.load(open(f'{D}/clair/candidates.json'))}
frames = json.load(open(f'{D}/clair/frames/frames.json'))
assets = {os.path.basename(a['path']).rsplit('.', 1)[0]: a for a in json.load(open(f'{D}/clair/paint/generated-assets.json'))}
paint = {p['id']: p for p in json.load(open(f'{D}/paintings.json'))}

def img(src, name, w=960):
    im = Image.open(src).convert('RGB')
    if im.width > w: im = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
    im.save(f'{out}/img/{name}.jpg', quality=82, optimize=True); return f'img/{name}.jpg'

def mmss(t): return f"{int(t // 60)}:{int(t % 60):02d}"

SECTIONS = [
    (0.0, "开头主题，很轻", "只有月亮"),
    (58.63, "自由速度，渐强到高点再收", "月出，暖色；你的北京城照片落在高点"),
    (96.5, "琶音段，流动起来", "水面；镜头随音乐越切越快"),
    (160.47, "两次高潮", "港口和城市灯火"),
    (185.62, "平静下来", "惠斯勒的蓝夜"),
    (196.28, "主题回来", "小镇和星空"),
    (268.26, "琶音的回声", "冬夜冰湖、孤树"),
    (290.23, "渐弱到结束", "你的云中满月，淡出"),
]
OWNER = {"beijing-tower": "你的照片", "eave-moon": "你的照片"}

KEPT = {x['id']: i + 1 for i, x in enumerate([x for x in ed['shots'] if not x.get('drop')])}
CLUT = {c['id']: c['clutter'] for c in json.load(open(f'{D}/clair/paint/clutter.json'))} if os.path.exists(f'{D}/clair/paint/clutter.json') else {}
WHY = {k: '你选的删除' for k in ('roof-moon', 'reeds-lake', 'river-bridge', 'marina', 'honfleur', 'night-3')}
WHY['beijing-tower'] = '25 张排不下；想保留的话，删渔村栈桥，它正好落在 1:21 的高点'

def shot_card(n, s):
    k = s['id']
    if k.startswith('night-'):
        p = paint[k]
        a = img(f'{D}/real/aligned/{k}.png', f'{k}-photo'); b = img(f'{D}/art/{k}.jpg', f'{k}-paint')
        who = f"真画：{e(p['artist'].split(' ')[0])}《{e(p['title'].split(' ')[0])}》{e(p['year'])}"
        credit = "照片是 Codex 以前还原的"
    else:
        ph = s.get('photo_final') if s.get('photo_final') and os.path.exists(f"{D}/{s['photo_final']}") else s['photo']
        a = img(f'{D}/{ph}', f'{k}-photo'); b = img(f'{D}/clair/paint/aligned/{k}.png', f'{k}-paint')
        who = f"AI 印象派画 · 仿{e(assets[k].get('style', ''))}"
        if k in OWNER: credit = OWNER[k]
        else:
            c = cands[frames[k]['pexels']]
            credit = f'照片 <a href="{e(c["url"])}" target="_blank" rel="noopener">{e(c["photographer"])} · Pexels</a>'
    if s.get('drop'):
        head = f'<span class="drop">建议删除 · {e(WHY.get(k, s.get("drop_reason", "")))}</span>'
    else:
        head = f'<span class="t">{KEPT[k]} · 出现 {mmss(s.get("breath_cut", s["at"]))}</span>'
    cls = "shot-card dropped" if s.get('drop') else "shot-card"
    return f'''<figure class="{cls}" id="s{n}">
  <div class="pair">
    <button class="shot" data-full="{a}" aria-label="放大镜头 {n} 的照片"><img src="{a}" alt="照片" loading="lazy"><span class="tag">照片</span></button>
    <button class="shot" data-full="{b}" aria-label="放大镜头 {n} 的画"><img src="{b}" alt="画" loading="lazy"><span class="tag">画</span></button>
  </div>
  <figcaption><p class="zh">{head}{e(s['zh'])}</p><p class="en">{who}</p><p class="credit">{credit}</p></figcaption>
</figure>'''

secs = []
for si, (t0, mus, pic) in enumerate(SECTIONS):
    t1 = SECTIONS[si + 1][0] if si + 1 < len(SECTIONS) else ed['end']
    items = [(i + 1, x) for i, x in enumerate(ed['shots']) if t0 <= x.get('at_phrase', x['at']) < t1]
    secs.append(f'<section class="group"><h3><span class="t">{mmss(items[0][1]["at"])}</span>{e(mus)} <span>· {e(pic)}</span></h3><div class="grid">{"".join(shot_card(n, x) for n, x in items)}</div></section>')

widen = []
for k, src, label in (("beijing-tower", "owner-photos/owner-1.jpg", "你的照片：北京城月出"), ("eave-moon", "owner-photos/owner-2.jpg", "你的照片：云中满月"), ("lone-tree", "full/12453183.jpg", "网上照片：孤树与满月")):
    a = img(f'{D}/clair/{src}', f'{k}-orig'); b = img(f'{D}/clair/frames/{k}.png', f'{k}-wide')
    widen.append(f'''<figure class="shot-card"><div class="pair">
  <button class="shot" data-full="{a}" aria-label="放大原图"><img src="{a}" alt="原图" loading="lazy" class="contain"><span class="tag">原图</span></button>
  <button class="shot" data-full="{b}" aria-label="放大扩成横幅的图"><img src="{b}" alt="扩成 16:9" loading="lazy"><span class="tag">Codex 扩成 16:9</span></button>
</div><figcaption><p class="zh">{e(label)}</p></figcaption></figure>''')

page = f'''<meta charset="utf-8">
<title>月光 Photo Preview</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=EB+Garamond:ital,wght@0,400;0,500;1,400&family=Noto+Serif+SC:wght@500;700&family=IBM+Plex+Mono:wght@500&display=swap">
<style>
/* Layout: one quiet nocturne column; each shot is a photo|painting pair in film order, grouped by musical section. */
:root {{
  --night: #0d1320;
  --panel: #151d2c;
  --line: #273246;
  --moon: #ebe6d2;
  --mist: #94a0b3;
  --gold: #d8b25c;
  --display: "EB Garamond", "Noto Serif SC", Georgia, serif;
  --cjk: "Noto Serif SC", "Songti SC", "STSong", serif;
  --body: -apple-system, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", system-ui, sans-serif;
  --mono: "IBM Plex Mono", ui-monospace, Menlo, monospace;
  color-scheme: dark;
}}
body {{ background: var(--night); color: var(--moon); font-family: var(--body); line-height: 1.6; }}
.wrap {{ max-width: 1240px; margin: 0 auto; padding-inline: 20px; padding-block: 40px 80px; display: grid; gap: 56px; }}
header {{ display: grid; gap: 14px; max-width: 70ch; }}
.eyebrow {{ font-family: var(--mono); font-size: 12px; letter-spacing: .14em; text-transform: uppercase; color: var(--gold); margin: 0; }}
h1 {{ font-family: var(--cjk); font-weight: 700; font-size: clamp(30px, 5vw, 46px); line-height: 1.15; margin: 0; text-wrap: balance; }}
h1 i {{ font-family: var(--display); font-weight: 400; color: var(--mist); font-size: .72em; margin-left: .3em; }}
header p, .block > p {{ margin: 0; color: var(--mist); max-width: 70ch; }}
header p b {{ color: var(--moon); font-weight: 500; }}
code {{ font-family: var(--mono); color: var(--gold); font-size: .92em; }}
h2 {{ font-family: var(--cjk); font-weight: 500; font-size: 24px; margin: 0; display: flex; gap: 12px; align-items: baseline; flex-wrap: wrap; }}
h2 span, h3 > span:not(.t) {{ font-family: var(--display); font-style: italic; font-weight: 400; color: var(--mist); font-size: .8em; }}
h3 {{ font-family: var(--cjk); font-weight: 500; font-size: 18px; margin: 0; padding-bottom: 8px; border-bottom: 1px solid var(--line); text-wrap: balance; }}
h3 > span:not(.t) {{ font-family: var(--body); font-style: normal; font-size: .82em; }}
.block, .group {{ display: grid; gap: 20px; }}
.grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(min(100%, 520px), 1fr)); gap: 26px 22px; }}
.shot-card {{ margin: 0; display: grid; gap: 10px; align-content: start; min-width: 0; }}
.pair {{ display: grid; grid-template-columns: 1fr 1fr; gap: 6px; }}
.shot {{ position: relative; display: block; padding: 0; border: 0; background: var(--panel); cursor: zoom-in; border-radius: 3px; overflow: hidden; width: 100%; }}
.shot img {{ display: block; width: 100%; aspect-ratio: 16 / 9; object-fit: cover; transition: transform .4s ease; }}
.shot img.contain {{ object-fit: contain; }}
.shot:hover img {{ transform: scale(1.03); }}
.shot:focus-visible {{ outline: 2px solid var(--gold); outline-offset: 3px; }}
.tag {{ position: absolute; left: 6px; bottom: 6px; padding: 1px 8px; background: var(--night); color: var(--moon); font-size: 12px; border-radius: 2px; }}
figcaption p {{ margin: 0; }}
.zh {{ font-size: 15px; }}
.en {{ font-size: 13.5px; color: var(--moon); opacity: .82; }}
.credit {{ font-size: 12.5px; color: var(--mist); }}
.credit a {{ color: var(--mist); text-decoration-color: var(--line); }}
.credit a:hover {{ color: var(--gold); }}
.t {{ font-family: var(--mono); color: var(--gold); font-size: 12.5px; font-variant-numeric: tabular-nums; margin-right: 8px; }}
.drop {{ display: inline-block; font-size: 12.5px; color: var(--night); background: var(--gold); padding: 0 8px; border-radius: 2px; margin-right: 8px; }}
.dropped .pair {{ opacity: .45; }}
.how {{ border-top: 1px solid var(--line); padding-top: 20px; display: grid; gap: 8px; max-width: 70ch; }}
.how p {{ margin: 0; color: var(--mist); }}
#box {{ position: fixed; inset: 0; background: rgba(5, 8, 14, .94); display: grid; place-items: center; padding: 20px; cursor: zoom-out; z-index: 10; }}
#box[hidden] {{ display: none; }}
#box img {{ max-width: 100%; max-height: calc(100vh - 40px); object-fit: contain; }}
@media (prefers-reduced-motion: reduce) {{ .shot img {{ transition: none; }} .shot:hover img {{ transform: none; }} }}
</style>
<div class="wrap">
  <header>
    <p class="eyebrow">Debussy × Impressionism · 第三首</p>
    <h1>月光 <i>Clair de lune</i></h1>
    <p>Goedhart 钢琴版，<b>5 分 04 秒，24 张</b>。画面跟着旋律呼吸：旋律往上走、变强时，画面变亮、变清楚；落到低音、乐句换气时，画面变暗、变朦胧、往下沉。每吸一口气，照片就多变成画一点；换图放在乐句的换气处，新图在暗处叠进来，再随下一句旋律亮起来。没有定格。</p>
    <p>按你选的删了 6 张；北京城是第 25 张，排不下，先拿掉了。</p>
    <p>预览视频：<code>build/03-clair/03-clair-preview-v8-view.mp4</code>。“出现”是每张图在乐句换气处叠进来的时间，序号和视频里一致。点任意一张图可以放大。</p>
  </header>
  <section class="block">
    <h2>照片和画 <span>Every shot, in film order</span></h2>
    {"".join(secs)}
  </section>
  <section class="block">
    <h2>三张照片先扩成横幅 <span>Widened to 16:9 by Codex</span></h2>
    <p>这三张不能直接裁成 16:9，Codex 先往外延伸画面，原图里的东西没动。</p>
    <div class="grid">{"".join(widen)}</div>
  </section>
  <footer class="how">
    <p>想换哪张画、重画哪张，告诉我镜头号就行。提示词在 <code>docs/DEBUSSY-CLAIR-CODEX-PROMPTS.md</code>，每张都写了仿哪位画家。</p>
  </footer>
</div>
<div id="box" hidden><img alt=""></div>
<script>
const box = document.getElementById('box');
const big = box.querySelector('img');
document.querySelectorAll('.shot').forEach(b => b.addEventListener('click', () => {{
  big.src = b.dataset.full; big.alt = b.querySelector('img').alt; box.hidden = false;
}}));
box.addEventListener('click', () => {{ box.hidden = true; big.src = ''; }});
document.addEventListener('keydown', ev => {{ if (ev.key === 'Escape') {{ box.hidden = true; big.src = ''; }} }});
</script>
'''
open(f'{out}/index.html', 'w').write(page)
print('wrote', f'{out}/index.html')
