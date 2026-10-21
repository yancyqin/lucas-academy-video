#!/usr/bin/env python3
"""Build the Debussy × Impressionism preview page and plan doc from the data folder.

Reads  lucas-academy-video-data/debussy-impressions/{program.json, paintings.json, music/sources.json}
Writes lucas-academy-video-data/debussy-impressions/preview/index.html   (images in preview/img, mp3 in preview/audio)
       lucas-academy-video/DEBUSSY-IMPRESSIONS-PLAN.md
"""
import json, html, os, sys, urllib.parse, hashlib
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
DATA = os.environ.get("DEBUSSY_DATA", os.path.abspath(os.path.join(REPO, "..", "lucas-academy-video-data", "debussy-impressions")))
if not os.path.isdir(DATA):  # worktrees sit two levels deeper
    DATA = "/Users/yqin/repo/playground/lucas-academy-video-data/debussy-impressions"
program = json.load(open(os.path.join(DATA, "program.json")))
paintings = json.load(open(os.path.join(DATA, "paintings.json")))
sources = {s["key"]: s for s in json.load(open(os.path.join(DATA, "music", "sources.json")))}
_norm_path = os.path.join(DATA, "music", "normalized", "report.json")
norm = {r["key"]: r for r in json.load(open(_norm_path))["files"]} if os.path.exists(_norm_path) else {}
by_group = {}
for p in paintings: by_group.setdefault(p["group"], []).append(p)
E = html.escape
def commons_page(name): return "https://commons.wikimedia.org/wiki/File:" + urllib.parse.quote(name.replace(" ", "_"))
def commons_orig(name): return "https://commons.wikimedia.org/wiki/Special:FilePath/" + urllib.parse.quote(name.replace(" ", "_"))
def mmss(s): return f"{int(s)//60}:{int(s)%60:02d}" if s else "—"
def lic_class(lic):
    l = lic.lower()
    if "public domain" in l: return "pd"
    if "cc by" in l: return "by"
    return "other"
def rec_html(key):
    s = sources[key]
    have = bool(s.get("file"))
    mp3 = "audio/" + os.path.basename(s["file"]).rsplit(".", 1)[0] + ".mp3" if have else None
    n = norm.get(key)
    status = (f"已下载，已统一到 {n['out_LUFS']:.0f} LUFS（增益 {n['gain_dB']:+.1f} dB" + (f"，削峰 {n['peak_shaved_dB']:.1f} dB" if n["peak_shaved_dB"] >= 1 else "") + "）") if (have and n) else ("已下载" if have else "只有链接")
    parts = [f'<div class="rec"><div class="rec-head"><span class="lic {lic_class(s["license"])}">{E(s["license"].split(" — ")[0])}</span>'
             f'<strong>{E(s["piece"])}</strong><span class="dur">{mmss(s.get("duration_s"))}</span></div>',
             f'<div class="rec-body"><div>{E(s["performer"])}</div>',
             f'<div class="muted">{E(status)}' + (f' · {E(s["notes"])}' if s.get("notes") else "") + "</div>",
             f'<div class="links"><a href="{E(s["page"])}" target="_blank" rel="noopener">来源页 / 下载</a>' + (f' · <span class="muted">原始：{E(s["file"])}' + (f' · 统一音量后：{E(n["out"])}' if n else "") + "</span>" if have else "") + "</div>"]
    if s.get("credit"): parts.append(f'<div class="credit">署名：<code>{E(s["credit"])}</code></div>')
    if mp3: parts.append(f'<audio controls preload="none" src="{E(mp3)}"></audio>')
    parts.append("</div></div>")
    return "\n".join(parts)
def painting_cards(group, prefix=""):
    out = []
    for p in by_group.get(group, []):
        hires = p.get("hires")
        links = f'<a href="{E(commons_page(p["file"]))}" target="_blank" rel="noopener">Commons</a> · <a href="{E(commons_orig(hires or p["file"]))}" target="_blank" rel="noopener">原图</a>'
        out.append(f'''<figure class="card" id="{E(prefix + p["id"])}">
<a href="{E(commons_orig(hires or p["file"]))}" target="_blank" rel="noopener"><img src="img/{E(p["id"])}.jpg" alt="{E(p["title"])}" loading="lazy"></a>
<figcaption><div class="ptitle">{E(p["title"])}</div><div class="pmeta">{E(p["artist"])} · {E(p["year"])} · {E(p["museum"])}</div><div class="pnote">{E(p["note"])}</div><div class="plinks">{links}</div></figcaption></figure>''')
    return "\n".join(out)
def section(piece, n=None, kind="core"):
    num = f'<span class="num">{n}</span>' if n else ""
    recs = "\n".join(rec_html(k) for k in piece.get("recordings", []))
    if not recs: recs = '<div class="rec pending"><div class="rec-body">还没有可用的录音（PD / CC0 / CC BY）。请在 Musopen 上找：见文末。</div></div>'
    return f'''<section class="piece {kind}" id="{E(piece["key"])}">
<header class="piece-head">{num}<div><h2>{E(piece["zh"])} <span class="fr">{E(piece["fr"])}</span></h2><div class="from">{E(piece["from"])}</div></div></header>
<p class="why">{E(piece["why"])}</p>
{recs}
<div class="grid">{painting_cards(piece["group"], piece["key"] + "-")}</div>
</section>'''
core_total = sum(sources[p["recordings"][0]].get("duration_s", 0) for p in program["core"] if p.get("recordings"))
css = r"""
<style>
/* Layout: one column of pieces, each piece = header + recording card(s) + grid of painting cards. Palette from Monet's Rouen series: fog grey-blue ground, blue-black ink, a gold accent. */
:root{--bg:#eef1f4;--bg2:#ffffff;--fg:#1f2a3a;--muted:#5d6b7c;--line:#cfd6de;--accent:#b8761c;--accent-bg:#fbf1dd;--pd:#2e6b4a;--pd-bg:#e2f1e7;--by:#2c5c8f;--by-bg:#e0ebf7;--other:#8a3b3b;--other-bg:#f6e1e1;
--display:"Noto Serif SC","Songti SC","STSong",serif;--latin:"Cormorant Garamond","Noto Serif SC",serif;--body:-apple-system,"PingFang SC","Hiragino Sans GB","Noto Sans SC","Helvetica Neue",Arial,sans-serif;--mono:ui-monospace,"SF Mono",Menlo,monospace}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--bg:#151c26;--bg2:#1e2733;--fg:#e6e9ee;--muted:#9aa7b7;--line:#34404f;--accent:#e0a84a;--accent-bg:#3a2e17;--pd:#8fd3a8;--pd-bg:#1f3a2a;--by:#9cc3ef;--by-bg:#1f3350;--other:#efa3a3;--other-bg:#4a2323;color-scheme:dark}}
:root[data-theme="dark"]{--bg:#151c26;--bg2:#1e2733;--fg:#e6e9ee;--muted:#9aa7b7;--line:#34404f;--accent:#e0a84a;--accent-bg:#3a2e17;--pd:#8fd3a8;--pd-bg:#1f3a2a;--by:#9cc3ef;--by-bg:#1f3350;--other:#efa3a3;--other-bg:#4a2323;color-scheme:dark}
body{background:var(--bg);color:var(--fg);font-family:var(--body);line-height:1.6;font-size:15px}
.wrap{max-width:1180px;margin:0 auto;padding-block:28px 60px;padding-inline:18px}
h1{font-family:var(--display);font-weight:600;font-size:clamp(28px,4vw,44px);line-height:1.15;margin:0 0 6px;text-wrap:balance}
h1 .fr{font-family:var(--latin);font-weight:500;font-style:italic;color:var(--muted);font-size:.6em;display:block}
.lede{max-width:70ch;color:var(--fg);margin:0 0 10px}
.rules{max-width:70ch;color:var(--muted);font-size:14px;margin:0 0 14px}
.legend{display:flex;flex-wrap:wrap;gap:8px 14px;align-items:center;font-size:13px;color:var(--muted);margin:0 0 30px}
.lic{display:inline-block;font-size:12px;letter-spacing:.04em;padding:2px 8px;border-radius:3px;font-weight:600;white-space:nowrap}
.lic.pd{color:var(--pd);background:var(--pd-bg)}.lic.by{color:var(--by);background:var(--by-bg)}.lic.other{color:var(--other);background:var(--other-bg)}
.toc{display:flex;flex-wrap:wrap;gap:6px 14px;font-size:14px;margin:0 0 36px;padding:12px 14px;border-top:1px solid var(--line);border-bottom:1px solid var(--line)}
.toc a{color:var(--fg);text-decoration:none;border-bottom:1px solid var(--line)}.toc a:hover{border-color:var(--accent)}
.toc .lbl{color:var(--muted);text-transform:uppercase;letter-spacing:.08em;font-size:11px;margin-right:4px}
.piece{margin:0 0 56px;padding-top:8px}
.piece-head{display:flex;gap:16px;align-items:flex-start;margin:0 0 6px}
.num{font-family:var(--latin);font-size:40px;line-height:1;color:var(--accent);min-width:34px;font-weight:600;font-variant-numeric:tabular-nums}
h2{font-family:var(--display);font-weight:600;font-size:clamp(22px,2.6vw,30px);margin:0;line-height:1.2;text-wrap:balance}
h2 .fr{font-family:var(--latin);font-style:italic;font-weight:500;color:var(--muted);font-size:.78em;margin-left:6px}
.from{color:var(--muted);font-size:13px;margin-top:2px}
.why{max-width:75ch;margin:6px 0 14px}
.rec{background:var(--bg2);border:1px solid var(--line);border-left:4px solid var(--accent);border-radius:4px;padding:12px 14px;margin:0 0 12px}
.rec.pending{border-left-color:var(--other)}
.rec-head{display:flex;flex-wrap:wrap;gap:8px 12px;align-items:center;margin-bottom:4px}
.rec-head strong{font-weight:600}.dur{color:var(--muted);font-variant-numeric:tabular-nums;margin-left:auto}
.rec-body{font-size:14px;display:grid;gap:3px}
.muted{color:var(--muted)}.links a,.plinks a,.credit a{color:var(--by)}
.credit code{font-family:var(--mono);font-size:12px;background:var(--bg);padding:1px 6px;border-radius:3px;word-break:break-word}
audio{width:100%;max-width:560px;margin-top:8px;display:block}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:18px 16px;align-items:start;margin-top:16px}
.card{margin:0;background:var(--bg2);border:1px solid var(--line);border-radius:4px;overflow:hidden;min-width:0}
.card img{display:block;width:100%;height:auto;max-width:100%;background:var(--line)}
.card figcaption{padding:10px 12px 12px;font-size:13px;display:grid;gap:4px}
.ptitle{font-family:var(--display);font-weight:600;font-size:14px;line-height:1.35;color:var(--fg)}
.pmeta{color:var(--muted);font-size:12px}.pnote{color:var(--fg);font-size:12.5px;line-height:1.55}.plinks{font-size:12px}
.band{margin:48px 0 18px;padding-top:14px;border-top:2px solid var(--accent)}
.band h2{font-size:clamp(20px,2.4vw,26px)}.band p{max-width:75ch;color:var(--muted);margin:4px 0 0}
table{border-collapse:collapse;width:100%;font-size:13.5px;margin-top:12px}
th,td{text-align:left;vertical-align:top;padding:8px 10px;border-bottom:1px solid var(--line)}th{color:var(--muted);font-weight:600;font-size:12px;letter-spacing:.05em;text-transform:uppercase}
.tablewrap{overflow-x:auto}
footer{margin-top:50px;color:var(--muted);font-size:13px;max-width:75ch}
a:focus-visible,audio:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
@media (max-width:480px){.piece-head{gap:10px}.num{font-size:30px;min-width:26px}.grid{grid-template-columns:1fr 1fr;gap:12px 10px}.card figcaption{padding:8px}}
@media (prefers-reduced-motion:no-preference){.card img{transition:opacity .2s}}
</style>"""
head = f"""<title>德彪西·印象派画单</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,500;0,600;1,500&family=Noto+Serif+SC:wght@600&display=swap">
{css}
<div class="wrap">
<h1>德彪西 × 印象派：曲子和画<span class="fr">Debussy × Impressionism — pieces, recordings and paintings</span></h1>
<p class="lede">镜头语言：每幅画先给一张写实还原（Codex 生成的照片感画面），慢慢溶成印象派成品，定格一会儿，再换下一幅。每首曲子一组画；画的数量跟着乐句走，慢的曲子画少、停得久。</p>
<p class="rules"><strong>音量</strong>：所有录音都已统一到 −18 LUFS（真峰值不超过 −1 dBTP），只用整体增益，曲子内部的强弱不动；个别峰值太高的地方由限幅器削掉，最多只在 2.6% 的时间里起作用。试听的是统一后的版本。</p>
<p class="rules">录音许可照旧：只用公有领域（要在美国也过期）、CC0 或 CC BY（简介里署名）；BY-SA、NC、ND 都不用。画作本身全是公有领域；预览图是维基共享资源 960 px 缩略图，点图或“原图”打开高清原件（大多来自奥赛、芝加哥艺术博物馆、华盛顿国家美术馆、大都会的开放获取扫描）。</p>
<div class="legend"><span class="lic pd">Public domain</span><span>美国政府作品或 1923 年前出版的录音</span><span class="lic by">CC BY</span><span>可用，简介里署名</span><span class="lic other">待找</span><span>还没有可用录音</span></div>
<nav class="toc"><span class="lbl">正片</span>{" ".join(f'<a href="#{E(p["key"])}">{E(p["zh"])}</a>' for p in program["core"])}<span class="lbl">备选</span>{" ".join(f'<a href="#{E(p["key"])}">{E(p["zh"])}</a>' for p in program["extra"])}<span class="lbl">待补录音</span>{" ".join(f'<a href="#{E(p["key"])}">{E(p["zh"])}</a>' for p in program["pending"])}<a href="#rejected">查过但不能用</a></nav>
"""
body = [head]
body.append(f'<div class="band"><h2>正片顺序（六首，约 {mmss(core_total)}）</h2><p>一天的弧线：雾中的教堂 → 水 → 雪 → 舞 → 夜 → 焰火。觉得长就先去掉《雪上足迹》和《世俗舞曲》，剩四首约 23 分钟。</p></div>')
for i, p in enumerate(program["core"], 1): body.append(section(p, i, "core"))
body.append('<div class="band"><h2>备选</h2><p>录音可用，但曲子或演奏有保留，看你要不要。</p></div>')
for p in program["extra"]: body.append(section(p, None, "extra"))
body.append('<div class="band" id="pending-band"><h2>画配好了、还缺录音的曲子</h2><p>这些配对本来最贴切，但维基共享资源、IMSLP、Internet Archive、Free Music Archive 上都没有能用的录音。Musopen 最可能有，它被 Cloudflare 人机验证挡住，Claude in Chrome 扩展连上会话后我再去找。</p></div>')
for p in program["pending"]: body.append(section(p, None, "pending"))
rows = "".join(f"<tr><td>{E(a)}</td><td>{E(b)}</td></tr>" for a, b in program["rejected"])
body.append(f'<div class="band" id="rejected"><h2>查过但不能用的录音</h2><p>免得下次再查一遍。</p></div><div class="tablewrap"><table><thead><tr><th>录音</th><th>为什么不用</th></tr></thead><tbody>{rows}</tbody></table></div>')
body.append('<footer>数据：lucas-academy-video-data/debussy-impressions/（paintings.json、program.json、music/sources.json、music/candidates/ 原始录音、preview/ 本页）。页面由 scripts/debussy-impressions/build_preview.py 生成。</footer></div>')
out_html = os.path.join(DATA, "preview", "index.html")
os.makedirs(os.path.dirname(out_html), exist_ok=True)
open(out_html, "w").write("\n".join(body))
# ---- markdown plan ----
def md_rec(key):
    s = sources[key]
    where = f"本地 `{s['file']}`" if s.get("file") else "未下载"
    return f"| {s['piece']} | {s['performer']} | {s['license']} | {mmss(s.get('duration_s'))} | [来源]({s['page']}) · {where}{(' · ' + s['notes']) if s.get('notes') else ''} |"
def md_paintings(group):
    return "\n".join(f"| {p['artist']} | {p['title']} | {p['year']} | {p['museum']} | [Commons]({commons_page(p['file'])}) · [原图]({commons_orig(p.get('hires') or p['file'])}) | {p['note']} |" for p in by_group.get(group, []))
def md_piece(p, n=None):
    t = f"### {n + '. ' if n else ''}{p['zh']} · {p['fr']}\n\n{p['from']}。{p['why']}\n\n"
    if p.get("recordings"):
        t += "| 录音 | 演奏 | 许可 | 时长 | 来源 / 本地 |\n|---|---|---|---|---|\n" + "\n".join(md_rec(k) for k in p["recordings"]) + "\n\n"
    else:
        t += "录音：还没有可用的（PD / CC0 / CC BY）。\n\n"
    t += "| 画家 | 画 | 年份 | 收藏 | 图 | 写实还原要点 |\n|---|---|---|---|---|---|\n" + md_paintings(p["group"]) + "\n\n"
    return t
md = ["# 德彪西 × 印象派 音乐影片 — 曲子和画的清单 v0.1（2026-10-13）\n",
"预览页（带缩略图和试听）：`lucas-academy-video-data/debussy-impressions/preview/index.html`，同时发布为 Claude 页面（见会话）。本文件由 `scripts/debussy-impressions/build_preview.py` 从 `lucas-academy-video-data/debussy-impressions/{program.json, paintings.json, music/sources.json}` 生成，改数据再跑脚本，不要手改表格。\n",
"## 1. 概念和镜头语言\n",
"- 每幅画：**写实还原（Codex 生成的照片感画面）→ 慢慢溶成印象派成品 → 定格 → 换下一幅**。溶的过程就是片子的内容：观众看着照片变成画。\n- 每首曲子一组画。画的切换跟着乐句的起点走（和巴赫组曲一样的规矩）；慢的曲子画少、每幅停得久，不在慢乐段里赶画。\n- 鲁昂大教堂那一组只需要一张写实照片：同一机位依次溶入清晨、阴天、上午、正午、下午、日落六幅莫奈，画面本身就在讲“光变了，墙没变”。\n- 全片不用 AI 生成的音乐；写实还原是 AI 生成的图，按惯例标注“AI 生成”。\n- 结尾：焰火定格到黑；按片尾规矩留一句开放的问题（待写）。\n",
"## 2. 录音许可和音量\n",
"所有录音统一到 −18 LUFS（真峰值 ≤ −1 dBTP），只用整体增益，不压缩曲子内部的强弱；峰值超出的几首用 192 kHz 过采样的限幅器削峰，限幅器最多只在 2.6% 的时间里起作用。\n",
"只用公有领域（必须在美国也过期：美国政府作品、1923 年前出版的录音）、CC0、CC BY（简介里署名）。BY-SA、NC、ND、Free Art License 不用。IMSLP 上标 “Public Domain – Non-PD US” 的名家老录音不用。维基共享资源上 Marcelle Meyer 1956–57 的整套前奏曲和意象集虽然挂着 PD 标签，但美国要到 2066 年以后才过期，不用。\n",
f"## 3. 正片顺序（六首，约 {mmss(core_total)}）\n",
"一天的弧线：雾中的教堂 → 水 → 雪 → 舞 → 夜 → 焰火。觉得长就先去掉《雪上足迹》和《世俗舞曲》，剩四首约 23 分钟。\n"]
for i, p in enumerate(program["core"], 1): md.append(md_piece(p, str(i)))
md.append("## 4. 备选\n\n录音可用，但曲子或演奏有保留。\n")
for p in program["extra"]: md.append(md_piece(p))
md.append("## 5. 画配好了、还缺录音的曲子\n\n这些配对本来最贴切，录音要在 Musopen 上找（脚本和内置浏览器都被 Cloudflare 人机验证挡住，没有去点验证）。\n")
for p in program["pending"]: md.append(md_piece(p))
md.append("## 6. 查过但不能用的录音\n\n| 录音 | 为什么不用 |\n|---|---|\n" + "\n".join(f"| {a} | {b} |" for a, b in program["rejected"]) + "\n")
md.append("## 7. 文件在哪\n\n- 原始录音：`lucas-academy-video-data/debussy-impressions/music/candidates/`，来源和许可在 `music/sources.json`。\n- 统一音量后的录音：`music/normalized/*.wav`（48 kHz / 24-bit，全部 −18 LUFS、真峰值 ≤ −1 dBTP，和原录音逐采样对齐），由 `scripts/debussy-impressions/normalize.py` 生成，每首的增益和削峰记在 `music/normalized/report.json`。音质测量（频宽、底噪、削波）在 `music/audio_report.jsonl`，由 `audio_report.py` 生成。\n- 画：`paintings.json`（Commons 文件名、收藏、写实还原要点），960 px 预览图在 `preview/img/`。原图按表里的“原图”链接下载（Special:FilePath 直接给原件）。\n- 预览页：`preview/index.html`（试听用的 96 kbps mp3 在 `preview/audio/`）。\n")
open(os.path.join(REPO, "DEBUSSY-IMPRESSIONS-PLAN.md"), "w").write("\n".join(md))
print("wrote", out_html, "and", os.path.join(REPO, "DEBUSSY-IMPRESSIONS-PLAN.md"), "| core total", mmss(core_total))
