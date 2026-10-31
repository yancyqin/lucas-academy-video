#!/usr/bin/env python3
"""Build the footage review page for Yancy from Codex's picks: footage/review.html in lucas-academy-video-data.

  python3 scripts/ai-sycophancy/footage_page.py
Reads the shot table from docs/ai-sycophancy/codex-footage.md, the candidates from footage/search/pexels*.json and
Codex's verdicts from footage/review/*.json (a later file overrides an earlier one for the same shot, so a re-review
of a few shots can sit in its own file). Each shot is one row: the sentence, what the shot needs, then Codex's
picks as looping previews. Clicking a preview selects it; the bar at the bottom lists the selection to copy.
Also writes footage/sources.json: every pick with its page, full-quality download link, author and licence.
Serve the footage folder over http (videos do not play from file:// in every browser).
"""
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = next(p / "lucas-academy-video-data" for p in ROOT.parents if (p / "lucas-academy-video-data").is_dir())
FOOT = DATA / "ai-sycophancy/footage"
BRIEF = (ROOT / "docs/ai-sycophancy/codex-footage.md").read_text()

shots, section = [], ""
for line in BRIEF.split("## 镜头表", 1)[1].split("## 交付", 1)[0].splitlines():
    if line.startswith("### SC"):
        section = line[4:]
    elif m := re.match(r"^\| ([GL]\d+)( ★)? \| (.*?) \| (.*?) \| (\d+) \|", line):
        shots.append({"id": m[1], "star": bool(m[2]), "section": section, "line": m[3],
                      "need": m[4].replace("**", ""), "secs": m[5]})

cands = {}
for f in sorted((FOOT / "search").glob("pexels*.json")):
    for shot, items in json.loads(f.read_text()).items():
        cands.setdefault(shot, {}).update({str(x["id"]): x for x in items})
review = {}
for f in sorted((FOOT / "review").glob("*.json")):
    review.update(json.loads(f.read_text()))

e = html.escape
parts, last = [], None
for s in shots:
    if s["section"] != last:
        parts.append(f"<h2>{e(s['section'])}</h2>")
        last = s["section"]
    r = review.get(s["id"])
    picks = (r or {}).get("picks") or []
    ask = s["star"] or len(picks) > 1 or bool((r or {}).get("uncertain"))
    tag = "<span class=ask>请 Yancy 挑</span>" if ask and picks else ""
    head = (f"<div class=meta><b>{s['id']}</b>{' ★' if s['star'] else ''} {tag}"
            f"<div class=line>{e(s['line'])}</div><div class=need>要：{e(s['need'])}（约 {s['secs']} 秒）</div>")
    if r and r.get("uncertain"):
        head += f"<div class=unsure>Codex 拿不准：{e(r['uncertain'])}</div>"
    head += "</div>"
    cells = []
    for k, p in enumerate(picks):
        pid = str(p["id"])
        x = cands.get(s["id"], {}).get(pid)
        if not x:
            continue
        key = f"{s['id']}-{chr(97 + k)}"
        src = f"preview/{s['id']}-{pid}.mp4"
        info = f"{x['w']}×{x['h']} · {x['fps']} fps · {x['dur']} s · {e(x['u'])}"
        caution = f"<div class=caution>注意：{e(p['caution'])}</div>" if p.get("caution") else ""
        cells.append(
            f"<figure data-key='{key}' data-id='{pid}'><video src='{src}' muted loop playsinline preload=none></video>"
            f"<figcaption><b>{key}</b> {'首选' if k == 0 else '备选'} · "
            f"<a href='https://www.pexels.com/video/{e(x['slug'])}-{pid}/' target=_blank>Pexels {pid}</a><br>"
            f"<span class=info>{info}</span><div>{e(p.get('why') or '')}</div>{caution}</figcaption></figure>")
    if not cells:
        why = e((r or {}).get("why_none") or "Codex 还没审")
        more = e("；".join((r or {}).get("search_more") or []))
        cells.append(f"<div class=none>没有合适的：{why}<br><span class=info>{more}</span></div>")
    parts.append(f"<section class=shot>{head}<div class=row>{''.join(cells)}</div></section>")

page = """<!doctype html>
<html lang="zh"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>实拍素材审核</title>
<style>
:root { --bg:#f6f4ef; --fg:#1d1d1b; --mute:#6b6862; --line:#ddd8cf; --pick:#c9a45a; --ask:#b5452f; }
@media (prefers-color-scheme: dark) { :root { --bg:#14171b; --fg:#ece8e0; --mute:#9a958c; --line:#2c3138; } }
body { margin:0; background:var(--bg); color:var(--fg); font:15px/1.5 -apple-system, "PingFang SC", sans-serif; padding:16px 16px 90px; }
h1 { font-size:22px; margin:4px 0 6px; } h2 { font-size:17px; margin:28px 0 8px; border-bottom:1px solid var(--line); padding-bottom:4px; }
.intro { color:var(--mute); max-width:900px; }
.shot { display:grid; grid-template-columns: 260px 1fr; gap:14px; padding:12px 0; border-bottom:1px solid var(--line); }
@media (max-width: 760px) { .shot { grid-template-columns: 1fr; } }
.line { margin:4px 0; } .need, .info { color:var(--mute); font-size:13px; }
.unsure, .caution { color:var(--ask); font-size:13px; } .ask { color:#fff; background:var(--ask); border-radius:4px; padding:0 6px; font-size:12px; }
.row { display:flex; gap:12px; flex-wrap:wrap; }
figure { margin:0; width:320px; max-width:100%; cursor:pointer; border:3px solid transparent; border-radius:6px; }
figure.sel { border-color:var(--pick); } video { width:100%; aspect-ratio:16/9; background:#000; display:block; border-radius:4px; }
figcaption { font-size:13px; padding:4px 2px; } .none { color:var(--mute); font-size:14px; padding:8px; }
#bar { position:fixed; left:0; right:0; bottom:0; background:var(--fg); color:var(--bg); padding:10px 16px; font-size:14px; display:flex; gap:12px; align-items:center; }
#bar button { font:inherit; padding:4px 10px; } #sel { flex:1; overflow:auto; white-space:nowrap; }
</style></head><body>
<h1>实拍素材审核 ·《你爱听 AI 说「是的」吗？》</h1>
<p class=intro>Claude 在 Pexels 上为每个镜头找了 10 个候选，Codex 看过对照图后挑出这里的首选和备选。标「请 Yancy 挑」的有 2–3 个候选。点一下预览就是选它（再点取消）；底部会列出你选的，可以复制给 Claude。没选的镜头就用首选。</p>
BODY
<div id=bar><span>已选：</span><span id=sel>（还没有）</span><button id=copy>复制</button></div>
<script>
const KEY = "footage-picks";
let picks = {};
try { picks = JSON.parse(localStorage.getItem(KEY) || "{}"); } catch (e) {}
const show = () => {
  document.querySelectorAll("figure").forEach(f => f.classList.toggle("sel", picks[f.dataset.key.split("-")[0]] === f.dataset.key));
  const v = Object.values(picks).sort();
  document.getElementById("sel").textContent = v.length ? v.join("  ") : "（还没有）";
  try { localStorage.setItem(KEY, JSON.stringify(picks)); } catch (e) {}
};
document.querySelectorAll("figure").forEach(f => f.addEventListener("click", ev => {
  if (ev.target.tagName === "A") return;
  const shot = f.dataset.key.split("-")[0];
  if (picks[shot] === f.dataset.key) delete picks[shot]; else picks[shot] = f.dataset.key;
  show();
}));
document.getElementById("copy").onclick = () => navigator.clipboard && navigator.clipboard.writeText(Object.values(picks).sort().join(" "));
const io = new IntersectionObserver(es => es.forEach(x => x.isIntersecting ? x.target.play().catch(() => {}) : x.target.pause()), { rootMargin: "200px" });
document.querySelectorAll("video").forEach(v => io.observe(v));
show();
</script></body></html>"""
(FOOT / "review.html").write_text(page.replace("BODY", "\n".join(parts)))
sources = []
for s in shots:
    for k, p in enumerate((review.get(s["id"]) or {}).get("picks") or []):
        x = cands[s["id"]][str(p["id"])]
        sources.append({"shot": s["id"], "pick": chr(97 + k), "source": "pexels", "id": x["id"],
                        "page_url": f"https://www.pexels.com/video/{x['slug']}-{x['id']}/", "download_url": x["hd"],
                        "license": "Pexels License", "license_url": "https://www.pexels.com/license/",
                        "author": x["u"], "author_id": x["uid"], "width": x["w"], "height": x["h"], "fps": x["fps"],
                        "duration": x["dur"], "preview": f"preview/{s['id']}-{x['id']}.mp4",
                        "why": p.get("why"), "caution": p.get("caution")})
(FOOT / "sources.json").write_text(json.dumps(sources, ensure_ascii=False, indent=1))
n = sum(1 for s in shots if review.get(s["id"], {}).get("picks"))
print(f"{FOOT / 'review.html'}: {len(shots)} shots, {n} with picks")
