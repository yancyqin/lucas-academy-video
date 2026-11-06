#!/usr/bin/env python3
"""Check page for the 蓝色浪潮 Codex photos: each painting next to its photo, a slider that dissolves one into the other
(the cut the film will make), and the blue-filtered version where the owner asked for the filter.

  .venv-reframe/bin/python scripts/blue-wave/codex_page.py   -> <data>/pick-page/codex.html (+ img/codex-*.jpg)
Served with the pick page (launch config "blue-wave-pick", port 8131): http://localhost:8131/codex.html
"""
import html, os, sys
from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
from tint import tint

DATA = os.environ.get("BLUE_WAVE_DATA", "/Users/yqin/repo/playground/lucas-academy-video-data/blue-wave")
OUT = f"{DATA}/pick-page"
FILTER = 0.4          # the owner's D for the Wanderer (11-05); the other filtered paintings shown at the same strength

# film order: photo id, painting id, title, blue filter?
SHOTS = [
    ("great-wave", "great-wave", "葛饰北斋《神奈川冲浪里》", False),
    ("blue-dancers-orsay", "blue-dancers-orsay", "德加《蓝色舞者》（奥赛版）", False),
    ("rhone", "rhone", "梵高《罗纳河上的星夜》", False),
    ("kramskoi-moonlit", "kramskoi-moonlit", "克拉姆斯柯依《月夜》", False),
    ("shalott", "shalott", "沃特豪斯《夏洛特夫人》", True),
    ("miranda", "miranda", "沃特豪斯《米兰达——暴风雨》", False),
    ("liberty", "liberty", "德拉克洛瓦《自由引导人民》", True),
    ("wanderer", "wanderer", "弗里德里希《雾海上的旅人》", True),
    ("wanderer-wide", "wanderer", "《雾海上的旅人》横版（左右补雾海）", True),
]

def small(src, dst, side=1100, strength=0.0):
    im = Image.open(src).convert("RGB"); w, h = im.size
    im.thumbnail((side, side), Image.LANCZOS)
    (tint(im, strength) if strength else im).save(f"{OUT}/img/{dst}", quality=86)
    return f"img/{dst}", w, h

def esc(s): return html.escape(s, quote=True)

def build():
    os.makedirs(f"{OUT}/img", exist_ok=True)
    cards = []
    for pid, art, title, blue in SHOTS:
        photo = f"{DATA}/codex/real-{pid}.png"
        if not os.path.exists(photo):
            cards.append(f'<div class="card"><h3>{esc(title)}</h3><p class="meta">还没生成：codex/real-{pid}.png</p></div>'); continue
        a, aw, ah = small(f"{DATA}/art/{art}.jpg", f"codex-art-{pid}.jpg")
        p, pw, ph = small(photo, f"codex-{pid}.jpg")
        figs = [f'<figure><img src="{a}" alt=""><figcaption>原画 {aw}×{ah}</figcaption></figure>',
                f'<figure><img src="{p}" alt=""><figcaption>Codex 照片 {pw}×{ph}</figcaption></figure>']
        if blue:
            t, _, _ = small(photo, f"codex-{pid}-blue.jpg", strength=FILTER)
            figs.append(f'<figure><img src="{t}" alt=""><figcaption>照片 + 蓝色滤镜 {FILTER:.0%}</figcaption></figure>')
        # the photo fills the painting's box in the dissolve, as align.py will register it
        fade = (f'<div class="fade" style="aspect-ratio:{aw}/{ah};width:min(100%,{520 * aw / ah:.0f}px)">'
                f'<img src="{a}" alt=""><img class="top" src="{p}" alt=""></div>'
                f'<input type="range" min="0" max="100" value="0" aria-label="原画 ↔ 照片">')
        cards.append(f'<div class="card"><h3>{esc(title)}</h3><div class="row">{"".join(figs)}</div>'
                     f'<p class="meta">拖动滑块：原画 ↔ 照片叠化</p>{fade}</div>')
    page = f'''<!doctype html><html lang="zh"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>蓝色浪潮 · 仿古照片</title><style>
:root{{--bg:#f6f8fb;--fg:#17202e;--mute:#5b6678;--card:#fff;--line:#d9e0ea}}
@media (prefers-color-scheme:dark){{:root{{--bg:#0e1420;--fg:#e6ecf5;--mute:#97a3b6;--card:#172033;--line:#2a3550}}}}
body{{margin:0;background:var(--bg);color:var(--fg);font:15px/1.55 -apple-system,"PingFang SC",system-ui,sans-serif}}
main{{max-width:1180px;margin:0 auto;padding:24px 16px 80px}} h1{{font-size:28px;margin:0 0 4px}} h3{{font-size:17px;margin:4px 0 8px}}
.meta{{color:var(--mute);font-size:13px;margin:8px 0 4px}} .card{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px;margin:16px 0}}
.row{{display:flex;gap:10px;flex-wrap:wrap}} figure{{margin:0;flex:1 1 260px}} figure img{{width:100%;height:360px;object-fit:contain;background:#0002;border-radius:6px}}
figcaption{{font-size:12px;color:var(--mute)}}
.fade{{position:relative;margin:0 auto;overflow:hidden;border-radius:6px}}
.fade img{{position:absolute;inset:0;width:100%;height:100%;object-fit:fill}} .fade .top{{opacity:0}}
input[type=range]{{display:block;width:100%;max-width:720px;margin:8px auto 0}}
</style></head><body><main>
<h1>蓝色浪潮 · 仿古照片</h1><p class="meta">Codex 按原画生成的照片，片子里的顺序；之后你用它们做 Muse。滤镜那几张是之后加的效果预览，照片本身不偏色。</p>
{"".join(cards)}
</main><script>
document.querySelectorAll(".card").forEach(c=>{{const r=c.querySelector("input"),t=c.querySelector(".fade .top");
if(r&&t)r.oninput=()=>t.style.opacity=r.value/100}});
</script></body></html>'''
    open(f"{OUT}/codex.html", "w").write(page)
    print("wrote", f"{OUT}/codex.html")

if __name__ == "__main__":
    build()
