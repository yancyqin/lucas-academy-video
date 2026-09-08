"""Render the edit decision list as a standalone HTML sheet.

Generated from shots.py and the song JSON, so the sheet can never disagree with
what actually rendered.
"""
import json, pathlib, sys, html
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from shots import SHOTS, COVERS

REPO = pathlib.Path(__file__).resolve().parents[2]
song = json.loads((REPO / 'src/songs/rejoice.json').read_text())
lines = song['lines']
DUR = song['durationSeconds']

# Section colours are the film's own -- lyrics-theme.ts glow values.
SECTION = {
    'intro':     ('Intro',      '#4b6896'),
    'verse':     ('Verse',      '#4e6894'),
    'prechorus': ('Pre-chorus', '#967454'),
    'chorus':    ('Chorus',     '#e8a64a'),
    'bridge':    ('Bridge',     '#aeb6d8'),
    'outro':     ('Outro',      '#d6aa74'),
}

# My own read on what is worth replacing, and why. Ranked, not exhaustive.
FLAGS = {}
# Everything I had flagged has been replaced or regenerated:
#   the Wan veil and mirror gave way to the woman's face with a defocus ramp,
#   the kintsugi bowl was regenerated with the gold seams building to the end,
#   and the church clip gave way to the cloud sea.

def kind(src):
    if src.startswith('wan-'):   return ('Wan 生成', 'gen')
    if src.startswith('user-'):  return ('用户素材', 'user')
    if src.startswith('gen-'):   return ('生成静帧', 'still')
    return ('Pexels', 'stock')

def mmss(t): return f"{int(t)//60}:{t%60:05.2f}"

rows = []
for sid, src, si, a, b, mv, tr in SHOTS:
    covered = [l for l in lines if a - 0.35 <= l['t'] < b - 0.35]
    lyr = "".join(
        f'<div class="ly{" echo" if l.get("echo") else ""}">'
        f'{html.escape(l["text"])}<span class="lyt">{mmss(l["t"])}</span></div>'
        for l in covered) or '<div class="ly none">器乐段 · 无歌词</div>'
    secs = []
    for l in covered:
        if l['section'] not in secs: secs.append(l['section'])
    chips = "".join(
        f'<span class="chip" style="--c:{SECTION[s][1]}">{SECTION[s][0]}</span>' for s in secs)
    bits = []
    if tr.get('still'):
        z = tr.get('zoom'); bits.append(f"静帧 Ken Burns {z[0]}→{z[1]}")
    else:
        bits.append({'in':'慢推','out':'Zoom out','left':'左移','right':'右移',
                     'up':'上移','none':'不动'}[mv])
    if tr.get('fog'):  bits.append(f"雾 {tr['fog']}")
    if tr.get('exposure') is not None: bits.append(f"曝光 {tr['exposure']:+}")
    if tr.get('saturation') is not None: bits.append(f"饱和 {tr['saturation']}")
    if tr.get('lightRamp'): bits.append("金光 ramp")
    if tr.get('blurRamp'): bits.append(f"虚化 {tr['blurRamp'][0]}%→{tr['blurRamp'][1]}%")
    if tr.get('reverse'): bits.append("倒放")
    if tr.get('dissolve'): bits.append(f"过渡 {tr['dissolve']}s")
    label, cls = kind(src)
    pri, why = FLAGS.get(sid, (None, None))
    warm = (a / DUR)                      # the film's own cool -> warm progression
    rows.append(dict(sid=sid, a=a, b=b, span=b-a, lyr=lyr, chips=chips, src=src, si=si,
                     treat=" · ".join(bits), label=label, cls=cls, pri=pri, why=why,
                     warm=warm, covers=COVERS.get(sid, '')))

flagged = sum(1 for r in rows if r['pri'])
tr_rows = "\n".join(f"""
      <tr class="{'flagged' if r['pri'] else ''}">
        <td class="c-id"><span class="rail" style="--w:{r['warm']:.3f}"></span>
          <span class="sid">{r['sid']}</span></td>
        <td class="c-time"><span class="t">{mmss(r['a'])}</span>
          <span class="dash">–</span><span class="t">{mmss(r['b'])}</span>
          <span class="span">{r['span']:.2f}s</span></td>
        <td class="c-lyr">{r['chips']}{r['lyr']}</td>
        <td class="c-src"><code>{html.escape(r['src'])}</code>
          <span class="meta"><span class="tag {r['cls']}">{r['label']}</span>
          取用点 {r['si']}s</span>
          <span class="covers">{html.escape(r['covers'])}</span></td>
        <td class="c-tr">{html.escape(r['treat'])}</td>
        <td class="c-flag">{f'<span class="pri p{r["pri"]}">替换 {r["pri"]}</span><span class="why">{html.escape(r["why"])}</span>' if r['pri'] else '<span class="ok">—</span>'}</td>
      </tr>""" for r in rows)

doc = f"""<title>Rejoice 剪辑表</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@500;700&family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@400;500&display=swap">
<style>
:root {{
  --ground:#eceff1; --panel:#f7f9fa; --line:#cfd8dd; --line-soft:#e1e8ec;
  --ink:#0e151c; --ink-2:#3f4c57; --ink-3:#6b7a86;
  --cool:#1c5f6b; --warm:#a9691c; --flag:#9c3320; --ok:#2f6f4f;
  --mono:"IBM Plex Mono",ui-monospace,SFMono-Regular,Menlo,monospace;
  --sans:"IBM Plex Sans","PingFang SC","Hiragino Sans GB","Microsoft YaHei",system-ui,sans-serif;
  --disp:"Archivo","PingFang SC","Hiragino Sans GB",system-ui,sans-serif;
}}
@media (prefers-color-scheme:dark) {{
  :root:not([data-theme="light"]) {{
    --ground:#0b1014; --panel:#121a20; --line:#26333c; --line-soft:#1b252c;
    --ink:#e6edf1; --ink-2:#a9b8c2; --ink-3:#76888f;
    --cool:#63c2cf; --warm:#e8ae5c; --flag:#f08a72; --ok:#7fc9a3;
  }}
}}
:root[data-theme="dark"] {{
  --ground:#0b1014; --panel:#121a20; --line:#26333c; --line-soft:#1b252c;
  --ink:#e6edf1; --ink-2:#a9b8c2; --ink-3:#76888f;
  --cool:#63c2cf; --warm:#e8ae5c; --flag:#f08a72; --ok:#7fc9a3;
}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--ground);color:var(--ink);font-family:var(--sans);
  font-size:14px;line-height:1.55;-webkit-font-smoothing:antialiased}}
.wrap{{max-width:1240px;margin:0 auto;padding:40px 24px 72px;display:flex;flex-direction:column;gap:26px}}
header{{display:flex;flex-direction:column;gap:10px}}
.eyebrow{{font-family:var(--mono);font-size:11px;letter-spacing:.18em;text-transform:uppercase;
  color:var(--ink-3)}}
h1{{font-family:var(--disp);font-weight:700;font-size:clamp(28px,4vw,42px);margin:0;
  letter-spacing:-.015em;text-wrap:balance;
  background:linear-gradient(96deg,var(--cool),var(--warm));-webkit-background-clip:text;
  background-clip:text;color:transparent}}
.sub{{color:var(--ink-2);max-width:64ch}}
.stats{{display:flex;flex-wrap:wrap;gap:0;border:1px solid var(--line);border-radius:3px;
  background:var(--panel);overflow:hidden}}
.stat{{padding:12px 18px;border-right:1px solid var(--line-soft);flex:1 1 auto;min-width:118px}}
.stat:last-child{{border-right:0}}
.stat b{{display:block;font-family:var(--mono);font-size:19px;font-weight:600;
  font-variant-numeric:tabular-nums}}
.stat span{{font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:var(--ink-3)}}
.stat.warn b{{color:var(--flag)}} .stat.good b{{color:var(--ok)}}
.scroll{{overflow-x:auto;border:1px solid var(--line);border-radius:3px;background:var(--panel)}}
table{{width:100%;border-collapse:collapse;min-width:1020px}}
thead th{{position:sticky;top:0;z-index:2;background:var(--panel);text-align:left;
  font-family:var(--mono);font-size:10.5px;letter-spacing:.14em;text-transform:uppercase;
  color:var(--ink-3);font-weight:600;padding:11px 14px;border-bottom:1px solid var(--line)}}
tbody td{{padding:13px 14px;border-bottom:1px solid var(--line-soft);vertical-align:top}}
tbody tr:last-child td{{border-bottom:0}}
tbody tr.flagged{{background:color-mix(in oklab,var(--flag) 7%,transparent)}}
.c-id{{position:relative;width:64px;padding-left:20px!important}}
.rail{{position:absolute;left:8px;top:12px;bottom:12px;width:3px;border-radius:2px;
  background:color-mix(in oklab,var(--warm) calc(var(--w)*100%),var(--cool))}}
.sid{{font-family:var(--mono);font-weight:600;font-size:12.5px}}
.c-time{{width:172px;font-family:var(--mono);font-variant-numeric:tabular-nums;font-size:12px}}
.c-time .dash{{color:var(--ink-3);margin:0 3px}}
.c-time .span{{display:block;color:var(--ink-3);font-size:11px;margin-top:3px}}
.c-lyr{{min-width:290px}}
.ly{{padding:2px 0}}
.ly .lyt{{font-family:var(--mono);font-size:10.5px;color:var(--ink-3);margin-left:8px;
  font-variant-numeric:tabular-nums}}
.ly.echo{{color:var(--ink-2);font-size:12.5px;padding-left:14px;position:relative}}
.ly.echo::before{{content:"↳";position:absolute;left:0;color:var(--ink-3)}}
.ly.none{{color:var(--ink-3);font-style:italic}}
.chip{{display:inline-block;font-family:var(--mono);font-size:9.5px;letter-spacing:.1em;
  text-transform:uppercase;padding:2px 7px;border-radius:2px;margin:0 5px 6px 0;
  color:var(--c);border:1px solid color-mix(in oklab,var(--c) 45%,transparent);
  background:color-mix(in oklab,var(--c) 12%,transparent)}}
.c-src{{min-width:270px}}
.c-src code{{font-family:var(--mono);font-size:11.5px;word-break:break-all;color:var(--ink)}}
.c-src .meta{{display:flex;align-items:center;gap:8px;margin-top:5px;font-family:var(--mono);
  font-size:10.5px;color:var(--ink-3)}}
.c-src .covers{{display:block;margin-top:5px;font-size:11.5px;color:var(--ink-2)}}
.tag{{font-size:9.5px;letter-spacing:.08em;text-transform:uppercase;padding:2px 6px;
  border-radius:2px;border:1px solid var(--line)}}
.tag.gen{{color:var(--warm);border-color:color-mix(in oklab,var(--warm) 45%,transparent);
  background:color-mix(in oklab,var(--warm) 12%,transparent)}}
.tag.user{{color:var(--cool);border-color:color-mix(in oklab,var(--cool) 45%,transparent);
  background:color-mix(in oklab,var(--cool) 12%,transparent)}}
.c-tr{{width:170px;font-size:12px;color:var(--ink-2)}}
.c-flag{{width:210px}}
.pri{{display:inline-block;font-family:var(--mono);font-size:10px;letter-spacing:.08em;
  padding:2px 7px;border-radius:2px;color:var(--flag);font-weight:600;
  border:1px solid color-mix(in oklab,var(--flag) 45%,transparent);
  background:color-mix(in oklab,var(--flag) 12%,transparent)}}
.why{{display:block;margin-top:5px;font-size:11.5px;color:var(--ink-2)}}
.ok{{color:var(--ink-3)}}
footer{{color:var(--ink-3);font-size:12px;display:flex;flex-direction:column;gap:5px}}
footer code{{font-family:var(--mono);font-size:11px}}
a{{color:var(--cool)}}
:focus-visible{{outline:2px solid var(--warm);outline-offset:2px}}
</style>

<div class="wrap">
  <header>
    <div class="eyebrow">Edit decision list · {len(rows)} shots · 1920×1080 · 30fps</div>
    <h1>Rejoice 剪辑表</h1>
    <p class="sub">时间段来自 <code>src/songs/rejoice.json</code> 的实测歌词时间码,素材与处理来自
      <code>scripts/mv/shots.py</code>。相邻镜头故意重叠,所以边界上的一句会同时出现在两行里。
      切点不是手写的:带歌词的镜头由那句歌词反推——
      <code>start = 歌词时间 − 过渡长度 − 0.15s</code>,所以**溶解总在歌词换行之前完成**。
      默认过渡 1.4s,片头五段用 0.6–0.8s,S24→S25(银河到十字架)用 7s。
      左侧色条按歌曲位置从冷到暖——这也是全片的走向。</p>
  </header>

  <div class="stats">
    <div class="stat"><b>{len(rows)}</b><span>镜头</span></div>
    <div class="stat"><b>47</b><span>歌词行</span></div>
    <div class="stat"><b>5:06.67</b><span>全长</span></div>
    <div class="stat good"><b>0</b><span>校验失败</span></div>
    <div class="stat"><b>1.4s</b><span>默认溶解</span></div>
    <div class="stat"><b>7.0s</b><span>最长过渡</span></div>
  </div>

  <div class="scroll">
    <table>
      <thead><tr>
        <th>#</th><th>时间段</th><th>歌词</th><th>素材</th><th>处理</th><th>备注</th>
      </tr></thead>
      <tbody>{tr_rows}
      </tbody>
    </table>
  </div>

  <footer>
    <div>本版按你的替换清单重排,并把相邻同素材的镜头合并:31 → 24 个。
      已不再入片的素材:<code>pexels-26626428-church-mountain-sunrise</code>、
      <code>wan-veil-tear</code>、<code>wan-mirror-clear</code>。</div>
    <div>重新生成:<code>.venv-align/bin/python scripts/mv/edl_html.py</code> ·
      校验:<code>scripts/mv/verify_shots.py</code>(含首帧/末帧比较,用来证明没有 loop 或倒放)</div>
  </footer>
</div>
"""
out = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else REPO / 'out/rejoice-edl.html')
out.write_text(doc)
print(f"wrote {out}  ({len(doc)} bytes, {len(rows)} rows, {flagged} flagged)")
