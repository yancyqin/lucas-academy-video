"""The listening page (review.html): every 拿不准 item with the sound to judge it by, and 通过 / 重配 buttons.

Each narration item plays the line as the film plays it, and again with a few seconds around it (music and all);
picture items play a short clip around the moment. Decisions go to decisions.json through serve.py; opened as a
plain file the page still works and keeps choices in the browser, with a copy button.
"""
from __future__ import annotations

import html
import json
import subprocess
from pathlib import Path

from common import FAIL, UNSURE, mmss, short_hash
from decisions import report_id


def _clip_audio(src: Path, a: float, b: float, dst: Path) -> None:
    if dst.exists():
        return
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{max(0.0, a):.3f}", "-t", f"{b - max(0.0, a):.3f}",
                    "-i", str(src), "-map", "0:a:0", "-ac", "2", "-c:a", "aac", "-b:a", "160k", str(dst)], check=True)


def _clip_video(src: Path, a: float, b: float, dst: Path, audio: Path | None) -> None:
    if dst.exists():
        return
    cmd = ["ffmpeg", "-v", "error", "-y", "-ss", f"{max(0.0, a):.3f}", "-t", f"{b - max(0.0, a):.3f}", "-i", str(src)]
    if audio:
        cmd += ["-ss", f"{max(0.0, a):.3f}", "-t", f"{b - max(0.0, a):.3f}", "-i", str(audio), "-map", "0:v:0", "-map", "1:a:0"]
    else:
        cmd += ["-map", "0:v:0", "-map", "0:a:0?"]
    cmd += ["-vf", "scale=960:-2", "-c:v", "libx264", "-crf", "23", "-preset", "veryfast", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", str(dst)]
    subprocess.run(cmd, check=True)


def build(out: Path, report: dict, video: Path, audio: Path | None = None) -> Path:
    clips = out / "clips"
    clips.mkdir(exist_ok=True)
    sound = audio or video
    cards = []
    for it in report["items"]:
        if it["verdict"] not in (FAIL, UNSURE) and it["code"] != "narration.second_pass":
            continue
        media = []
        tag = short_hash(report["sha256"], it["key"])
        if it["area"] == "narration" and "lo" in it:
            line = clips / f"{tag}-line.m4a"
            ctx = clips / f"{tag}-context.m4a"
            _clip_audio(sound, it["lo"], it["hi"], line)
            _clip_audio(sound, it["lo"] - 2.0, it["hi"] + 1.5, ctx)
            media = [{"kind": "audio", "label": "这一句", "src": f"clips/{line.name}"},
                     {"kind": "audio", "label": "成片里前后几秒", "src": f"clips/{ctx.name}"}]
        elif it["area"] == "picture" and it.get("t0") is not None:
            v = clips / f"{tag}.mp4"
            _clip_video(video, it["t0"] - 1.0, it.get("t1", it["t0"]) + 1.0, v, audio)
            media = [{"kind": "video", "label": "前后一秒", "src": f"clips/{v.name}"}]
        elif it.get("t0") is not None:
            c = clips / f"{tag}.m4a"
            _clip_audio(sound, it["t0"], it.get("t1", it["t0"] + 4), c)
            media = [{"kind": "audio", "label": "这一段", "src": f"clips/{c.name}"}]
        cards.append({**{k: it.get(k) for k in ("key", "area", "verdict", "code", "title", "detail", "t0", "t1",
                                                  "line", "text", "heard", "diff")},
                      "at": mmss(it["t0"]) if it.get("t0") is not None else "", "media": media})
    data = {"film": report.get("film") or Path(report["video"]).stem, "video": Path(report["video"]).name,
            "sha": report["sha256"][:12], "id": report_id(report), "created": report["created"], "cards": cards,
            "skipped": report.get("skipped", []),
            "checked": {"narration": len(report["sections"].get("narration", []) or []),
                        "loudness": report["sections"].get("loudness"),
                        "format": report["sections"].get("format")}}
    page = TEMPLATE.replace("__TITLE__", html.escape(f"自动检测 · {data['film']}")).replace(
        "__DATA__", json.dumps(data, ensure_ascii=False).replace("</", "<\\/"))
    dst = out / "review.html"
    dst.write_text(page, encoding="utf-8")
    return dst


TEMPLATE = r"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<style>
:root{--bg:#f6f5f2;--card:#fff;--ink:#1d1d1f;--muted:#6b6b70;--line:#e3e1dc;--want:#c62828;--want-bg:#fde8e8;
--got:#1554b8;--got-bg:#e6efff;--ok:#1f7a3d;--ok-bg:#e3f4e8;--warn:#9a5b00;--warn-bg:#fff2d9;--bad:#b3261e;--bad-bg:#fde4e1}
@media (prefers-color-scheme:dark){:root{--bg:#161618;--card:#1f1f22;--ink:#ececf0;--muted:#9a9aa3;--line:#33333a;
--want:#ff8a80;--want-bg:#3d1f1f;--got:#8ab4ff;--got-bg:#1c2a44;--ok:#7bd88f;--ok-bg:#1b3324;--warn:#ffc266;--warn-bg:#3a2c12;
--bad:#ff8a80;--bad-bg:#3d1f1f}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.6 -apple-system,"PingFang SC","Hiragino Sans GB",system-ui,sans-serif}
header{position:sticky;top:0;z-index:2;background:var(--bg);border-bottom:1px solid var(--line);padding:12px 16px}
header h1{font-size:18px;margin:0}
header .meta{color:var(--muted);font-size:13px}
.counts{display:flex;gap:8px;flex-wrap:wrap;margin-top:6px}
.pill{border-radius:999px;padding:2px 10px;font-size:13px;font-weight:600}
.pill.wait{background:var(--warn-bg);color:var(--warn)}.pill.fail{background:var(--bad-bg);color:var(--bad)}
.pill.ok{background:var(--ok-bg);color:var(--ok)}
main{max-width:860px;margin:0 auto;padding:16px}
h2{font-size:16px;margin:24px 0 8px}
.hint{color:var(--muted);font-size:13px;margin:0 0 10px}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px 16px;margin:10px 0}
.card.done-pass{border-color:var(--ok)}.card.done-redo{border-color:var(--bad)}
.card .top{display:flex;justify-content:space-between;gap:10px;align-items:baseline}
.card .title{font-weight:600}
.card .at{color:var(--muted);font-variant-numeric:tabular-nums;font-size:13px;white-space:nowrap}
.detail{color:var(--muted);font-size:13px;margin-top:2px;word-break:break-word}
.text{margin-top:8px;font-size:16px;line-height:1.8;word-break:break-word}
.text .want{color:var(--want);background:var(--want-bg);text-decoration:line-through;border-radius:3px;padding:0 2px}
.text .got{color:var(--got);background:var(--got-bg);border-radius:3px;padding:0 2px}
.heard{color:var(--muted);font-size:13px;margin-top:4px}
.media{display:flex;flex-wrap:wrap;gap:12px;margin-top:10px}
.media figure{margin:0;flex:1 1 260px;min-width:0}
.media figcaption{font-size:12px;color:var(--muted)}
audio{width:100%;height:36px}video{width:100%;border-radius:8px;background:#000}
.actions{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin-top:12px}
button{font:inherit;border-radius:8px;border:1px solid var(--line);background:var(--card);color:var(--ink);padding:6px 14px;cursor:pointer}
button.pass.on{background:var(--ok);border-color:var(--ok);color:#fff}
button.redo.on{background:var(--bad);border-color:var(--bad);color:#fff}
input.note{flex:1 1 200px;min-width:0;font:inherit;padding:6px 10px;border-radius:8px;border:1px solid var(--line);background:var(--bg);color:var(--ink)}
details{margin-top:8px}summary{cursor:pointer;color:var(--muted)}
.legend{font-size:13px;color:var(--muted)}
.legend span{border-radius:3px;padding:0 4px}
.offline{background:var(--warn-bg);color:var(--warn);padding:8px 12px;border-radius:8px;font-size:13px;margin-top:8px;display:none}
ul.plain{padding-left:18px;color:var(--muted);font-size:14px}
</style>
</head>
<body>
<header>
  <h1 id="h"></h1>
  <div class="meta" id="meta"></div>
  <div class="counts" id="counts"></div>
  <div class="offline" id="offline">没有连上检测服务器（qa.py serve），选择只存在这个浏览器里。<button id="copy">复制我的选择</button></div>
</header>
<main>
  <section id="unsure-sec">
    <h2>需要你听一听</h2>
    <p class="hint">自动检测拿不准的地方。听完点「通过」或「重配」，可以写一句备注。
      <span class="legend">红色划线 = 稿子里有、没听到；<span style="color:var(--got);background:var(--got-bg)">蓝色</span> = 实际听到的。</span></p>
    <div id="unsure"></div>
  </section>
  <section id="fail-sec">
    <h2>不通过（我来修，修好再发给你）</h2>
    <p class="hint">这些是确定的问题，不需要你决定；放在这里方便你听一下是什么。</p>
    <div id="fail"></div>
  </section>
  <section id="auto-sec">
    <details><summary id="auto-sum"></summary>
      <p class="hint">medium 听到的字和稿子不一样，但 small 模型在这些地方听到的正好是稿子上的字，所以自动算通过。small 也可能是「猜」对的；有空可以听一下。</p>
      <div id="auto"></div>
    </details>
  </section>
  <section>
    <h2>其他</h2>
    <ul class="plain" id="other"></ul>
  </section>
</main>
<script>
const DATA = __DATA__;
const STORE = "qa-decisions-" + DATA.id;
let decisions = {}, online = false;
const $ = (id) => document.getElementById(id);
const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));

function diffHtml(diff){
  if(!diff) return "";
  return diff.map(d => d.op==="equal" ? esc(d.a)
    : d.op==="delete" ? `<span class="want">${esc(d.a)}</span>`
    : d.op==="insert" ? `<span class="got">${esc(d.b)}</span>`
    : `<span class="want">${esc(d.a)}</span><span class="got">${esc(d.b)}</span>`).join("");
}
function mediaHtml(m){
  return `<div class="media">${m.map(x => `<figure><figcaption>${esc(x.label)}</figcaption>${
    x.kind==="video" ? `<video controls preload="metadata" src="${esc(x.src)}"></video>`
                     : `<audio controls preload="none" src="${esc(x.src)}"></audio>`}</figure>`).join("")}</div>`;
}
function card(c, withActions){
  const d = decisions[c.key] || {};
  const done = d.decision ? " done-" + d.decision : "";
  const text = c.diff ? `<div class="text">${diffHtml(c.diff)}</div><div class="heard">Whisper 听到：${esc(c.heard)}</div>`
                      : (c.text ? `<div class="text">${esc(c.text)}</div>` : "");
  const actions = withActions ? `<div class="actions">
      <button class="pass${d.decision==="pass"?" on":""}" data-k="${c.key}" data-d="pass">通过</button>
      <button class="redo${d.decision==="redo"?" on":""}" data-k="${c.key}" data-d="redo">重配 / 重做</button>
      <input class="note" data-k="${c.key}" placeholder="备注（可选）" value="${esc(d.note||"")}">
    </div>` : "";
  return `<div class="card${done}" id="c-${c.key}">
    <div class="top"><div class="title">${esc(c.title)}</div><div class="at">${esc(c.at)}</div></div>
    ${c.detail ? `<div class="detail">${esc(c.detail)}</div>` : ""}
    ${text}${mediaHtml(c.media||[])}${actions}</div>`;
}
function render(){
  const unsure = DATA.cards.filter(c => c.verdict==="unsure"), fail = DATA.cards.filter(c => c.verdict==="fail");
  const waiting = unsure.filter(c => !decisions[c.key]?.decision).length;
  const redo = unsure.filter(c => decisions[c.key]?.decision==="redo").length;
  $("h").textContent = "自动检测 · " + DATA.film;
  $("meta").textContent = `${DATA.video} · sha ${DATA.sha} · ${DATA.created}`;
  $("counts").innerHTML = (waiting ? `<span class="pill wait">等你听 ${waiting}</span>` : `<span class="pill ok">拿不准的都听完了</span>`)
    + (redo ? `<span class="pill fail">要重配 ${redo}</span>` : "")
    + (fail.length ? `<span class="pill fail">不通过 ${fail.length}</span>` : `<span class="pill ok">没有不通过</span>`);
  $("unsure").innerHTML = unsure.length ? unsure.map(c => card(c, true)).join("") : `<p class="hint">没有拿不准的地方。</p>`;
  $("fail").innerHTML = fail.length ? fail.map(c => card(c, false)).join("") : `<p class="hint">没有。</p>`;
  const auto = DATA.cards.filter(c => c.code==="narration.second_pass");
  $("auto-sec").style.display = auto.length ? "" : "none";
  $("auto-sum").textContent = `自动放过的 ${auto.length} 句（两个模型意见不一）`;
  $("auto").innerHTML = auto.map(c => card(c, false)).join("");
  const n = DATA.checked.narration, lo = DATA.checked.loudness, f = DATA.checked.format;
  $("other").innerHTML = [
    n ? `配音：逐句检查了 ${n} 句` : "",
    lo ? `响度 ${lo.lufs.toFixed(1)} LUFS，真峰值 ${lo.true_peak.toFixed(1)} dBTP` : "",
    f && f.width ? `${f.width}×${f.height} · ${f.fps} fps · ${f.vcodec}/${f.acodec} · ${f.duration.toFixed(2)} 秒` : "",
    ...DATA.skipped.map(s => "跳过：" + s)].filter(Boolean).map(s => `<li>${esc(s)}</li>`).join("");
}
async function save(key, decision, note){
  const c = DATA.cards.find(x => x.key===key);
  if(decision===undefined) decision = decisions[key]?.decision ?? null;
  if(decision===null && !note){ delete decisions[key]; } else { decisions[key] = {decision, note: note||"", title: c?.title}; }
  if(online){
    try{
      const r = await fetch("/decision", {method:"POST", headers:{"Content-Type":"application/json"},
        body: JSON.stringify({key, decision, note, title: c?.title, report: DATA.id})});
      if(r.ok){ decisions = (await r.json()).decisions; }
      else if(r.status===409){ delete decisions[key]; render(); alert("这部片子重新检查过了，这个页面是旧的。请刷新页面再决定。"); return; }
    }catch(e){ online = false; $("offline").style.display = "block"; }
  }
  try{ localStorage.setItem(STORE, JSON.stringify(decisions)); }catch(e){}
  render();
}
document.addEventListener("click", (e) => {
  const b = e.target.closest("button[data-k]"); if(!b) return;
  const k = b.dataset.k, cur = decisions[k]?.decision, note = document.querySelector(`input.note[data-k="${k}"]`)?.value || "";
  save(k, cur===b.dataset.d ? null : b.dataset.d, note);
});
document.addEventListener("change", (e) => {
  const i = e.target.closest("input.note"); if(!i) return;
  const k = i.dataset.k; if(!decisions[k]?.decision) return;
  save(k, decisions[k].decision, i.value);
});
$("copy").addEventListener("click", async () => {
  try{ await navigator.clipboard.writeText(JSON.stringify({report: DATA.id, decisions}, null, 1)); $("copy").textContent = "已复制"; }catch(e){}
});
(async () => {
  try{
    const r = await fetch("decisions.json", {cache:"no-store"});
    if(r.ok){ decisions = await r.json(); online = (await fetch("/ping")).ok; }
  }catch(e){}
  if(!online){
    $("offline").style.display = "block";
    try{ decisions = JSON.parse(localStorage.getItem(STORE) || "{}"); }catch(e){}
  }
  render();
})();
</script>
</body>
</html>
"""
