#!/usr/bin/env python3
"""Pick page for 蓝色浪潮 (Chopin Nocturne Op. 9 No. 2 + paintings ↔ Muse): the two free recordings, the blue filter
on the Wanderer, the Muse clips we already have, the new painting candidates and a proposed order on the music.

  .venv-reframe/bin/python scripts/blue-wave/pick_page.py   -> <data>/pick-page/index.html (+ img/, media/)
Serve over http (launch config "blue-wave-pick", port 8131); file:// only shows a static snapshot in the browser pane.
"""
import html, json, os, subprocess
from PIL import Image

DATA = os.environ.get("BLUE_WAVE_DATA", "/Users/yqin/repo/playground/lucas-academy-video-data/blue-wave")
OUT = f"{DATA}/pick-page"

RECORDINGS = [
    {"id": "levy", "src": "music/raw/levy-musopen.flac", "who": "Frank Lévy（Commons 和文件 ARTIST 标签；MusicBrainz 写 Aya Higuchi，待核实）",
     "len": "4:31", "fmt": "FLAC 96 kHz / 24-bit", "item": "https://archive.org/details/musopen-chopin-complete-works-flac",
     "sha1": "1fb95d92276f65030efb1d1b693d146bddd1a64c",
     "sections": [(1, "A 主题"), (29, "A′"), (58, "B"), (88, "A″"), (117, "B′"), (145, "A‴"), (174, "尾声"), (205, "高潮"), (228, "华彩 → 结束")]},
    {"id": "higuchi", "src": "music/raw/musopen-b.m4a", "who": "Aya Higuchi（文件标签和 MusicBrainz 一致）",
     "len": "4:37", "fmt": "ALAC 48 kHz / 24-bit", "item": "https://archive.org/details/musopen-chopin",
     "sha1": "58edffadbc89b1f45a36a2a5dd66435b15677025",
     "sections": [(0, "A 主题"), (29, "A′"), (59, "B"), (89, "A″"), (120, "B′"), (151, "A‴"), (180, "尾声"), (215, "高潮"), (235, "华彩 → 结束")]},
]

EXISTING = [
    {"art": "blue-dancers", "title": "德加《蓝色舞者》", "en": "Edgar Degas · Blue Dancers · 1898 · Pushkin Museum",
     "clips": [("footage/muse/blue-dancers-vertical.mp4", "Muse（你做的竖版，10 秒）")],
     "note": "听得见的舞 里那段。竖版：放进横屏要么放在自己的虚化背景上（像短视频那样），要么我再做一张横版 Codex 图你重做 Muse。"},
    {"art": "parasol", "title": "莫奈《撑阳伞的女人》", "en": "Claude Monet · Woman with a Parasol · 1875 · National Gallery of Art (CC0)",
     "clips": [("footage/existing/muse-parasol.i60.mp4", "Muse：她的脸（6.4 秒）"), ("footage/existing/minimax-parasol.mp4", "MiniMax：风吹山坡（5.9 秒）")],
     "note": "印象派的秘密 里那两段。蓝天、白裙、风——很「蓝色浪潮」。"},
    {"art": "impression-sunrise", "title": "莫奈《印象·日出》", "en": "Claude Monet · Impression, Sunrise · 1872 · Musée Marmottan Monet",
     "clips": [("footage/existing/le-havre-dawn-muse-original.mp4", "Muse：勒阿弗尔港的黎明（7 秒）")],
     "note": "印象派的秘密 里那段。蓝灰色的港口，可以当一段过渡。"},
]

# group, id, title, english line, why it fits, what Muse could move, flags
CANDIDATES = [
    ("浪", "great-wave", "葛饰北斋《神奈川冲浪里》", "Katsushika Hokusai · The Great Wave off Kanagawa · c. 1830–32 · The Met (CC0)",
     "字面上的「蓝色浪潮」，用的是当时新到日本的普鲁士蓝；和肖邦写 Op. 9 是同一两年（1830–32）。和结尾的雾海首尾呼应：开头是海浪，结尾是云海。",
     "巨浪卷起、碎成浪花，三条船被抬起", "推荐 · 开场"),
    ("浪", "miranda", "沃特豪斯《米兰达——暴风雨》", "John William Waterhouse · Miranda – The Tempest · 1916 · private collection",
     "穿蓝裙的女子站在礁石上看暴风雨里的船——浪潮 + 美丽的女人 + 浪漫主义的戏剧感。",
     "浪拍礁石、她的红发和裙子被风吹", "推荐 · 尾声高潮"),
    ("浪", "ninth-wave", "艾瓦佐夫斯基《九级浪》", "Ivan Aivazovsky · The Ninth Wave · 1850 · Russian Museum",
     "风暴过后抱着桅杆的幸存者迎着日出——挣扎和希望。颜色偏金绿，不太蓝。", "大浪推起、阳光穿过浪", ""),
    ("革命", "missolonghi", "德拉克洛瓦《希腊在迈索隆吉翁的废墟上》", "Eugène Delacroix · Greece on the Ruins of Missolonghi · 1826 · Bordeaux",
     "浪漫主义的「革命」：希腊独立战争，女子化身希腊，白衣蓝披风。注意：她的上衣在胸口敞开（不算裸体，但请你看一下）。"
     "《自由引导人民》没有列：画中女子袒胸。", "披风被风掀起、她抬眼", "胸口敞开"),
    ("夜", "rhone", "梵高《罗纳河上的星夜》", "Vincent van Gogh · Starry Night Over the Rhône · 1888 · Musée d'Orsay",
     "蓝色的夜、河上的煤气灯倒影、前景一对散步的恋人——浪漫又梦幻。", "倒影闪动、星星闪、恋人慢慢走", "推荐"),
    ("夜", "kramskoi-moonlit", "克拉姆斯柯依《月夜》", "Ivan Kramskoi · Moonlit Night · 1880 · Tretyakov Gallery",
     "白衣女子夜里坐在池塘边的长椅上——就是一首画出来的「夜曲」。", "她转头、月光在水上、叶子轻动", "推荐"),
    ("夜", "whistler-chelsea", "惠斯勒《夜曲：蓝与银——切尔西》", "James McNeill Whistler · Nocturne: Blue and Silver – Chelsea · 1871 · Tate",
     "惠斯勒借音乐把夜景画叫做「夜曲」，几乎只有蓝。画很抽象，Muse 只能动水和灯。", "水面、远处的灯", ""),
    ("夜", "kuindzhi-dnieper", "库因芝《第聂伯河上的月夜》", "Arkhip Kuindzhi · Moonlit Night on the Dnieper · 1880 · Russian Museum",
     "月光照在河上，当年展出时观众以为画后面藏了灯。整幅很暗，偏绿。", "云移开、月光在河上闪", ""),
    ("蓝衣女子", "broglie", "安格尔《布罗伊公主》", "Jean-Auguste-Dominique Ingres · Princesse de Broglie · 1851–53 · The Met (CC0)",
     "一身蓝色缎子礼服，安格尔最美的肖像之一。", "她呼吸、眼神移动、缎子上的光流动", "推荐"),
    ("蓝衣女子", "haussonville", "安格尔《奥松维尔伯爵夫人》", "Jean-Auguste-Dominique Ingres · Comtesse d'Haussonville · 1845 · The Frick Collection",
     "淡蓝色丝绸长裙，身后镜子里是她的背影。和布罗伊公主二选一。", "她把手从下巴放下、转头", ""),
    ("蓝衣女子", "blue-dancers-orsay", "德加《蓝色舞者》（奥赛版）", "Edgar Degas · Blue Dancers · c. 1893 · Musée d'Orsay",
     "德加的另一幅蓝色舞者（你说的「另外一幅」是不是这幅？）。", "舞者整理肩带、裙摆晃", ""),
    ("蓝衣女子", "pearl-earring", "维米尔《戴珍珠耳环的少女》", "Johannes Vermeer · Girl with a Pearl Earring · c. 1665 · Mauritshuis",
     "蓝头巾；不是浪漫主义时期，但很美、很梦幻。", "她转向我们、珍珠反光", ""),
    ("蓝衣女子", "shalott", "沃特豪斯《夏洛特夫人》", "John William Waterhouse · The Lady of Shalott · 1888 · Tate",
     "白衣女子坐船漂向卡米洛——浪漫、梦幻；颜色不太蓝。", "船漂、烛火摇、她的头发", ""),
]

ORDER = [  # music section (Lévy time), painting id, what goes there — the plan as of 2026-11-05 (owner's picks)
    ("0:00 A 主题", "great-wave", "开场：蓝色的浪 · Codex 照片做 Muse"),
    ("0:29 A′", "impression-sunrise", "现成 Muse：勒阿弗尔港的黎明"),
    ("0:58 B", "blue-dancers-orsay", "奥赛版 · Muse 跳舞版（02-dance）；接普希金版《蓝色舞者》（现成竖版 Muse，横屏里上下摇）"),
    ("1:28 A″", "rhone", "星夜、恋人 · Codex 照片做 Muse"),
    ("1:57 B′", "kramskoi-moonlit", "月夜、白衣女子 · 原画直接做 Muse"),
    ("2:25 A‴", "shalott", "夏洛特夫人（原画做的 Muse）→ 惠斯勒《夜曲：蓝与银——切尔西》只用原画、静止叠化，蓝色滤镜统一色调"),
    ("2:54 尾声", "miranda", "浪拍礁石 · 原画直接做 Muse"),
    ("3:25 高潮", "liberty", "1830 年七月革命，肖邦正在写 Op. 9 · 蓝色滤镜 · 只用原画：叠化进来，慢慢推到她和三色旗之间，再叠化出去"),
    ("3:48 华彩 → 结束", "wanderer", "雾海上的旅人：原画扩成 16:9 横屏（中间是原画，两边 Codex 照笔触补）+ 蓝色滤镜 D 40 %，43 秒 · 做 Muse"),
]

TITLES = {c[1]: c[2] for c in CANDIDATES} | {e["art"]: e["title"] for e in EXISTING} | {"wanderer": "弗里德里希《雾海上的旅人》",
                                                                                     "liberty": "德拉克洛瓦《自由引导人民》"}

def thumb(pid, side=1000):
    os.makedirs(f"{OUT}/img", exist_ok=True)
    dst = f"{OUT}/img/{pid}.jpg"
    im = Image.open(f"{DATA}/art/{pid}.jpg").convert("RGB"); w, h = im.size
    im.thumbnail((side, side), Image.LANCZOS); im.save(dst, quality=86)
    return f"img/{pid}.jpg", w, h

def media(src, name, audio=False):
    os.makedirs(f"{OUT}/media", exist_ok=True)
    dst = f"{OUT}/media/{name}"
    if not os.path.exists(dst):
        if audio:
            cmd = ["ffmpeg", "-v", "error", "-y", "-i", f"{DATA}/{src}", "-vn", "-ar", "48000", "-c:a", "aac", "-b:a", "256k", dst]
        else:
            cmd = ["ffmpeg", "-v", "error", "-y", "-i", f"{DATA}/{src}", "-an", "-vf", "scale='min(1280,iw)':-2:flags=lanczos,fps=30",
                   "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", "-movflags", "+faststart", dst]
        subprocess.run(cmd, check=True)
    return f"media/{name}"

def esc(s): return html.escape(s, quote=True)

def build():
    os.makedirs(f"{OUT}/img", exist_ok=True)
    rec_html = []
    for r in RECORDINGS:
        url = media(r["src"], f"{r['id']}.m4a", audio=True)
        marks = " ".join(f'<button class="seek" data-a="{r["id"]}" data-t="{t}">{t//60}:{t%60:02d} {esc(n)}</button>' for t, n in r["sections"])
        rec_html.append(f'''<div class="rec"><h3>{esc(r["who"])}</h3>
<audio id="a-{r["id"]}" controls preload="metadata" src="{url}"></audio>
<div class="marks">{marks}</div>
<p class="meta">{r["len"]} · {r["fmt"]} · Musopen「Set Chopin Free」2015 · <b>CC0（公有领域）</b> ·
<a href="{r["item"]}" target="_blank">archive.org</a> · SHA-1 <code>{r["sha1"][:12]}…</code></p></div>''')

    tints = "".join(f'<figure><img src="tint/tint-{s}.jpg" alt=""><figcaption>{k} · {lab}</figcaption></figure>'
                    for k, (s, lab) in zip("ABCD", [("0", "原画"), ("0.15", "15 % 很淡"), ("0.25", "25 % 淡"), ("0.4", "40 % 明显一点")]))
    wide = ""
    for name, lab in [("real-wanderer.png", "Codex 仿古照片（原画比例）"), ("real-wanderer-wide.png", "Codex 横版（左右补雾海，给横屏）")]:
        if os.path.exists(f"{DATA}/codex/{name}"):
            im = Image.open(f"{DATA}/codex/{name}").convert("RGB"); im.thumbnail((1200, 1200)); im.save(f"{OUT}/img/{name[:-4]}.jpg", quality=86)
            wide += f'<figure><img src="img/{name[:-4]}.jpg" alt=""><figcaption>{lab}</figcaption></figure>'
    if not wide:
        wide = '<p class="meta">Codex 仿古照片还在生成（原画比例一张、横版一张），好了我再刷新这页。</p>'

    ex_html = []
    for e in EXISTING:
        src, w, h = thumb(e["art"])
        clips = "".join(f'<figure><video src="{media(c, os.path.basename(c).replace(".i60", ""))}" controls loop muted playsinline preload="metadata"></video>'
                        f'<figcaption>{esc(lab)}</figcaption></figure>' for c, lab in e["clips"])
        ex_html.append(f'''<div class="card wide"><div class="pair"><figure><img src="{src}" alt=""><figcaption>原画 {w}×{h}</figcaption></figure>{clips}</div>
<h3>{esc(e["title"])} <span class="badge have">已有视频</span></h3><p class="en">{esc(e["en"])}</p><p>{esc(e["note"])}</p></div>''')

    groups = []
    for g in ["浪", "夜", "蓝衣女子", "革命"]:
        cards = []
        for grp, pid, title, en, why, moves, flag in CANDIDATES:
            if grp != g: continue
            src, w, h = thumb(pid)
            badge = "".join(f'<span class="badge {"rec" if "推荐" in f else "warn"}">{esc(f)}</span>' for f in flag.split(" · ") if f) if flag else ""
            cards.append(f'''<div class="card"><img src="{src}" alt="" loading="lazy"><h3>{esc(title)} {badge}</h3>
<p class="en">{esc(en)} · {w}×{h}</p><p>{esc(why)}</p><p class="muse">Muse 可以动：{esc(moves)}</p></div>''')
        groups.append(f'<h2 class="g">{g}</h2><div class="grid">{"".join(cards)}</div>')

    rows = "".join(f'<tr><td>{esc(t)}</td><td><img src="img/{pid}.jpg" alt=""></td><td>{esc(TITLES[pid])}</td><td>{esc(why)}</td></tr>'
                   for t, pid, why in ORDER)
    for _, pid, _ in ORDER: thumb(pid)

    page = f'''<!doctype html><html lang="zh"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>蓝色浪潮 · 选画</title><style>
:root{{--bg:#f6f8fb;--fg:#17202e;--mute:#5b6678;--card:#fff;--line:#d9e0ea;--blue:#2457a6;--warn:#a65b16}}
@media (prefers-color-scheme:dark){{:root{{--bg:#0e1420;--fg:#e6ecf5;--mute:#97a3b6;--card:#172033;--line:#2a3550;--blue:#8db4ff;--warn:#f0a35c}}}}
body{{margin:0;background:var(--bg);color:var(--fg);font:15px/1.55 -apple-system,"PingFang SC",system-ui,sans-serif}}
main{{max-width:1180px;margin:0 auto;padding:24px 16px 80px}} h1{{font-size:28px;margin:0 0 4px}} h2{{margin:36px 0 10px;font-size:21px}}
h2.g{{font-size:18px;color:var(--blue)}} h3{{font-size:16px;margin:8px 0 2px}} p{{margin:4px 0}} .en,.meta{{color:var(--mute);font-size:13px}}
.rec{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px 14px;margin:10px 0}} audio{{width:100%}}
.marks{{display:flex;flex-wrap:wrap;gap:6px;margin:8px 0}} .seek{{border:1px solid var(--line);background:transparent;color:var(--fg);border-radius:14px;padding:2px 10px;cursor:pointer;font-size:13px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:14px}} .card{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:10px}}
.card img{{width:100%;height:220px;object-fit:contain;background:#0001;border-radius:6px}} .card.wide{{margin:12px 0}}
.pair{{display:flex;gap:10px;flex-wrap:wrap}} .pair figure{{flex:1 1 220px;margin:0}} .pair img,.pair video{{width:100%;height:300px;object-fit:contain;background:#0002;border-radius:6px}}
figcaption{{font-size:12px;color:var(--mute)}} .muse{{font-size:13px;color:var(--blue)}}
.badge{{font-size:11px;border-radius:9px;padding:1px 7px;margin-left:4px;vertical-align:2px;white-space:nowrap}} .badge.rec{{background:var(--blue);color:#fff}}
.badge.warn{{background:var(--warn);color:#fff}} .badge.have{{background:#2f8f5b;color:#fff}}
.tints{{display:grid;grid-template-columns:repeat(4,1fr);gap:8px}} .tints figure{{margin:0}} .tints img{{width:100%;border-radius:6px}}
.codex{{display:flex;gap:10px;flex-wrap:wrap}} .codex figure{{margin:0;flex:1 1 300px}} .codex img{{width:100%;border-radius:6px}}
table{{border-collapse:collapse;width:100%;background:var(--card)}} td{{border-bottom:1px solid var(--line);padding:6px 8px;vertical-align:middle}} td img{{height:64px;border-radius:4px}}
ol li{{margin:6px 0}} @media (max-width:640px){{.tints{{grid-template-columns:repeat(2,1fr)}}}}
</style></head><body><main>
<h1>蓝色浪潮 · 选画</h1><p class="meta">肖邦《降E大调夜曲》Op. 9 No. 2（1830–32 写，1832 出版，献给 Marie Pleyel）· 画 ↔ Muse · 2026-11-05</p>

<h2>1 · 录音（两个都是 Musopen 的 CC0 公有领域录音，听一下选一个）</h2>
{"".join(rec_html)}
<p class="meta">按钮是我听出来的段落：主题 A 回来三次（0:29、1:28、2:25），中间是 B，2:54 以后是尾声，3:25 左右最强（con forza），3:48 高音华彩，然后结束。前面每段约 28 秒——一段一幅画正好。</p>

<h2>2 · 结尾：雾海上的旅人 + 淡蓝滤镜</h2>
<div class="tints">{tints}</div>
<div class="codex" style="margin-top:12px">{wide}</div>

<h2>3 · 已经有 Muse 视频的画</h2>{"".join(ex_html)}

<h2>4 · 新候选（都是公有领域，大图 ≥ 1800 px）</h2>{"".join(groups)}

<h2>5 · 方案（按 Frank Lévy 版 4:31 的时间，2026-11-05 定）</h2>
<table>{rows}</table>
<p class="meta">成片执行计划（给 Codex）：FILM-PLAN.md。Muse 视频用 7 段新的 + 2 段已有的。写实的画（月夜、夏洛特夫人、米兰达）直接拿原画做；惠斯勒《夜曲》和自由引导人民最后只用原画，不用视频，雾海上的旅人用原画扩成的横屏；写意的画（神奈川冲浪里、梵高、德加）用 Codex 仿古照片。
全部参考图和提示词在一个文件夹：muse-refs/（MUSE-PROMPTS.md）；仿古照片和原画对比：<a href="codex.html">codex.html</a>。</p>

<h2>6 · 已定</h2><ol>
<li>录音：第一个（4:31，Musopen CC0）。</li>
<li>格式：横屏 16:9 长片，之后再剪竖屏短视频（仿古照片都按原画比例，两种都能用）。</li>
<li>蓝色滤镜：旅人 D（40 %）；夏洛特夫人 → 惠斯勒、自由引导人民也加，色调统一。</li>
<li>不用：《撑阳伞的女人》、《布罗伊公主》、《希腊在迈索隆吉翁的废墟上》（换成《自由引导人民》）。</li>
<li>奥赛版《蓝色舞者》用跳舞版视频；惠斯勒《夜曲》和《自由引导人民》只用原画（叠化进出，自由引导人民慢慢推近）。「fade in / fade out」= 和前后段交叉叠化。</li>
<li>蓝色滤镜 0.40：旅人（你选的 D），夏洛特夫人、惠斯勒、自由引导人民先用同样强度，色调统一。片子里不加文字。</li>
</ol>
</main><script>
document.querySelectorAll(".seek").forEach(b=>b.onclick=()=>{{const a=document.getElementById("a-"+b.dataset.a);
document.querySelectorAll("audio").forEach(x=>{{if(x!==a)x.pause()}});a.currentTime=+b.dataset.t;a.play()}});
document.querySelectorAll("audio").forEach(a=>a.onplay=()=>document.querySelectorAll("audio").forEach(x=>{{if(x!==a)x.pause()}}));
</script></body></html>'''
    open(f"{OUT}/index.html", "w").write(page)
    print("wrote", f"{OUT}/index.html")

if __name__ == "__main__":
    build()
