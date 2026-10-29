"""sketchbook_shorts.py — a vertical loop short for each piece of the Mozart sketchbook (Twinkle has its own short)

    python sketchbook_shorts.py prepare [KEY ...]   cut the music, write DATA/shorts/KEY/{music.wav, config.json, title.png}
    python sketchbook_shorts.py render KEY          film.py -> DATA/shorts/KEY/drawn.mp4, then finish
    python sketchbook_shorts.py finish [KEY ...]    the title + loudness to -18 LUFS -> DATA/shorts/KEY/short.mp4
    python sketchbook_shorts.py check [KEY ...]     length, loudness, and how smoothly the last frame runs into the first
    python sketchbook_shorts.py texts               DATA/shorts/youtube-description.shorts.txt

Owner 2026-10-29: 「除了小星星 每个歌再做一个竖屏loop短视频」. One picture per piece, drawn exactly as in the film (same
plan, same tools, scaled down), on the Twinkle short's vertical layout with a bilingual question under the sheet. The
picture's own stretch of the recording plays, from a breath before its first note to its last note. The short loops:
it opens on a blank sheet with the tool on its way to the first stroke; after the last note the finished sheet slides
off the pad onto the same blank sheet, and the tool comes back to where frame 0 has it (film.py "loop").
"""
import json
import pathlib
import subprocess
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from cover import CHROME, CYAN, EN, GOLD, INK, ZH  # noqa: E402
from sketchbook_youtube import (AI_ZH, BYLINE_EN, BYLINE_ZH, CC, DE_BRA, PIECES, PLAYED_BY, PLAYERS,  # noqa: E402
                                TITLE_EN, TITLE_ZH, link)

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from youtube_tags import hashtags, tags  # noqa: E402

DATA = pathlib.Path("/Users/yqin/repo/playground/lucas-academy-video-data/mozart-sketchbook")
PY = "/Users/yqin/repo/playground/lucas-academy-video/.venv-reframe/bin/python"
HERE = pathlib.Path(__file__).parent
OUT = DATA / "shorts"

# film order: key -> (picture, file name, zh title line 1, en title line 2, YouTube title, zh scene, en scene, hashtag)
SHORTS = {
    "05": (1, "1-费加罗的婚礼-竖屏", "《<g>费加罗的婚礼</g>》，", "“<g>The Marriage of Figaro</g>”?",
           "莫扎特《费加罗的婚礼》，能画出来吗？ Can you draw Mozart's “The Marriage of Figaro”?",
           "婚礼日的早上，小老鼠们踮着脚把大蛋糕抬出厨房。", "The wedding morning: the mice tiptoe the big cake out of the kitchen.",
           "figaro"),
    "20": (1, "2-嬉游曲-竖屏", "莫扎特的<g>嬉游曲</g>，", "Mozart's <g>Divertimento</g>?",
           "莫扎特的嬉游曲，能画出来吗？ Can you draw Mozart's Divertimento?",
           "上午的花园，小刺猬在太阳底下伸懒腰。", "A morning garden: a hedgehog stretches in the sun.", "divertimento"),
    "06": (3, "3-魔笛-竖屏", "《<g>魔笛</g>》，", "“<g>The Magic Flute</g>”?",
           "莫扎特《魔笛》，能画出来吗？ Can you draw Mozart's “The Magic Flute”?",
           "王子吹响魔笛，狮子、小熊和长颈鹿跟着跳起舞来。", "The prince plays the magic flute, and a lion, bears and a giraffe dance.",
           "magicflute"),
    "10": (3, "4-大组曲终曲-竖屏", "《<g>大组曲</g>》，", "the “<g>Gran Partita</g>”?",
           "莫扎特《大组曲》，能画出来吗？ Can you draw Mozart's “Gran Partita”?",
           "动物管乐队游行到了广场，喷泉边的气球飞起来。", "The animal wind band parades into the square, and balloons fly by the fountain.",
           "granpartita"),
    "16": (3, "5-单簧管回旋曲-竖屏", "<g>单簧管</g>回旋曲，", "a <g>Clarinet</g> Rondo?",
           "莫扎特的单簧管回旋曲，能画出来吗？ Can you draw Mozart's Clarinet Rondo?",
           "捉迷藏：小狐狸又在大树后面找到了小兔子。", "Hide-and-seek: the fox finds the bunny behind the big tree again.",
           "clarinetconcerto"),
    "01": (1, "6-第40号交响曲-竖屏", "<g>第40号</g>交响曲，", "<g>Symphony No. 40</g>?",
           "莫扎特第40号交响曲，能画出来吗？ Can you draw Mozart's Symphony No. 40?",
           "大风的傍晚，戴红帽子的小女孩顶着风往家走。", "A windy evening: a girl in a red hat heads home against the wind.",
           "symphony40"),
    "27": (1, "7-弦乐小夜曲-竖屏", "《<g>弦乐小夜曲</g>》，", "“<g>Eine kleine Nachtmusik</g>”?",
           "莫扎特《弦乐小夜曲》，能画出来吗？ Can you draw Mozart's “Eine kleine Nachtmusik”?",
           "傍晚的小街，四只小熊背着手风琴来到窗下。", "An evening street: four bears bring their accordions under the windows.",
           "einekleinenachtmusik"),
    "15": (1, "8-单簧管柔板-竖屏", "<g>单簧管</g>的柔板，", "a <g>Clarinet</g> Adagio?",
           "莫扎特单簧管协奏曲的柔板，能画出来吗？ Can you draw Mozart's Clarinet Adagio?",
           "小男孩抱着小熊爬上床，窗外的小星星在唱歌。", "A little boy climbs into bed with his teddy; outside, the little star sings.",
           "clarinetconcerto"),
    "07": (2, "9-大组曲柔板-竖屏", "《大组曲》的<g>柔板</g>，", "the Gran Partita <g>Adagio</g>?",
           "莫扎特《大组曲》的柔板，能画出来吗？ Can you draw Mozart's Gran Partita Adagio?",
           "夜里的湖，星星一颗颗出来，湖里也有一片星空。", "Night on the lake: the stars come out one by one, and the lake fills with stars too.",
           "granpartita"),
}

# the piece in the tags field, as the long film names it
PIECE_TAGS = {"05": ["费加罗的婚礼", "marriage of figaro overture"], "20": ["嬉游曲", "divertimento k 138"],
              "06": ["魔笛", "magic flute overture"], "10": ["大组曲", "gran partita"], "16": ["单簧管协奏曲", "clarinet concerto k 622"],
              "01": ["第40号交响曲", "symphony no 40"], "27": ["弦乐小夜曲", "eine kleine nachtmusik"],
              "15": ["单簧管协奏曲", "clarinet concerto k 622"], "07": ["大组曲", "gran partita"]}

# the Twinkle short's layout (pictures are all 1536x1024); tools shrink with the sheet
LAYOUT = {"size": [1080, 1920], "sheet_scale": 0.6234, "tool_len": 246, "poses": [[-1.2, [0, -280]]], "rest": [965, 290]}
TOOL_K = 0.6234 / 0.835
DESK_X = {"desk.png": 0.42, "desk-morning.png": 0.5, "desk-day.png": 0.5, "desk-evening.png": 0.5}
PRE = 0.4        # music before the first note: the tool's last stretch to its first stroke
GLIDE = 1.0      # the tool leaves its rest this long before the loop point
LUFS = -18.0     # every short, like the Twinkle short (-18.3)


def ff(*args):
    subprocess.run(["ffmpeg", "-v", "error", "-y", *map(str, args)], check=True)


def scaled(tool):
    return {**tool, "len": round(tool["len"] * TOOL_K)}


TITLE = """<!doctype html><html><head><meta charset="utf-8"><style>
html,body{{margin:0;width:1080px;height:1920px;overflow:hidden;background:transparent}}
.fade{{position:absolute;left:0;right:0;bottom:0;height:960px;background:linear-gradient(180deg,rgba(24,14,6,0) 0%,rgba(24,14,6,.5) 30%,rgba(24,14,6,.6) 100%)}}
.t{{position:absolute;left:0;right:0;top:1150px;text-align:center;color:{ink};text-shadow:0 3px 14px rgba(0,0,0,.55),0 1px 3px rgba(0,0,0,.6)}}
.l{{white-space:nowrap}}
.zh{{font-family:{zh};font-weight:700;font-size:86px;line-height:1.22;letter-spacing:.02em}}
.en{{font-family:{en};font-weight:700;font-size:72px;line-height:1.18}}
.gap{{height:34px}}
.g{{color:{gold}}}.c{{color:{cyan}}}
</style></head><body><div class="fade"></div><div class="t">
<div class="zh l">{zh1}</div><div class="zh l">能<span class="c">画</span>出来吗？</div><div class="gap"></div>
<div class="en l">Can you <span class="c">draw</span></div><div class="en l">{en2}</div>
</div><script>
for (const k of ["zh", "en"]) {{            // a language's two lines shrink together until the longer fits 960 px
  const ls = [...document.querySelectorAll("." + k)];
  ls.forEach(l => l.style.display = "table");
  const w = Math.max(...ls.map(l => l.getBoundingClientRect().width)), s = Math.min(1, 960 / w);
  ls.forEach(l => {{ l.style.fontSize = parseFloat(getComputedStyle(l).fontSize) * s + "px"; l.style.margin = "0 auto"; }});
}}
</script></body></html>"""


def title_png(key, png):
    _, _, zh1, en2, *_ = SHORTS[key]
    page = TITLE.format(ink=INK, zh=ZH, en=EN, gold=GOLD, cyan=CYAN,
                        zh1=zh1.replace("<g>", '<span class="g">').replace("</g>", "</span>"),
                        en2=en2.replace("<g>", '<span class="g">').replace("</g>", "</span>"))
    with tempfile.TemporaryDirectory() as tmp:
        html = pathlib.Path(tmp) / "title.html"; html.write_text(page)
        subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=1",
                        "--window-size=1080,1920", "--default-background-color=00000000", "--allow-file-access-from-files",
                        f"--screenshot={png}", html.as_uri()], check=True, capture_output=True)


def quietest(wav, t0, t1):
    """Middle of the quietest 0.1 s of the recording between t0 and t1 (t1 if there is no room)."""
    if t1 - t0 < 0.15: return t1
    import numpy as np
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t0:.3f}", "-to", f"{t1:.3f}", "-i", wav, "-ac", "1", "-ar", "8000",
                          "-f", "f32le", "-"], capture_output=True, check=True).stdout
    x = np.frombuffer(raw, np.float32) ** 2
    e = np.convolve(x, np.ones(800), "valid")[::200]          # 0.1 s windows every 25 ms
    return t0 + (int(np.argmin(e)) * 200 + 400) / 8000


def prepare(key):
    n = SHORTS[key][0]
    piece = json.load(open(DATA / f"pieces/{key}/config.json"))
    sec = json.load(open(DATA / f"sections/{key}.json"))["sections"][n - 1]
    plan = json.load(open(DATA / f"pieces/{key}/plan-{n:02d}.json"))
    out = OUT / key; out.mkdir(parents=True, exist_ok=True)
    a, b = sec["start"], sec["end"]
    b = quietest(piece["music"], plan["cadence"] + 0.6, b)  # the music stops in the breath after the last note...
    shift = PRE - a                                           # film time = recording time + shift
    cad, end = plan["cadence"] + shift, b + shift
    loop_end = round(max(end, cad + 1.4), 2)                  # room after the last note to slide the sheet off, tool back
    ss = max(0.0, a - PRE)                                    # the breath before the first note (silence at a piece's start)
    ff("-ss", f"{ss:.3f}", "-to", f"{b:.3f}", "-i", piece["music"], "-af",    # ...its ring fading out from the last note
       f"adelay={round((PRE - (a - ss)) * 1000)}:all=1,afade=t=out:st={cad + 0.1:.3f}:d={end - cad - 0.15:.3f}:curve=qua",
       "-c:a", "pcm_s16le", out / "music.wav")
    s = {**piece["sections"][n - 1], "lead_in": shift, "tool": scaled(piece["sections"][n - 1]["tool"])}
    if "tool_lines" in s: s["tool_lines"] = scaled(s["tool_lines"])
    desk = pathlib.Path(piece["desk"])
    cfg = {"desk": str(desk), "desk_x": DESK_X[desk.name], "crayon": piece["crayon"], "music": str(out / "music.wav"),
           "audio_filter": "afade=t=in:d=0.06," + piece["audio_filter"],
           "fade_out": 0.05,                                  # music.wav has faded already; silence to the loop point
           "excerpt": [round(ss, 2), round(b, 2)],             # the part of the recording used, for the credits
           **LAYOUT, "loop": {"glide": GLIDE, "off": [round(cad + 0.15, 2), round(cad + 1.05, 2)], "end": loop_end},
           "sections": [s]}
    json.dump(cfg, open(out / "config.json", "w"), indent=1)
    title_png(key, out / "title.png")
    print(f"{key}: picture {n}, recording {ss:.1f}-{b:.1f} s, short {loop_end:.1f} s")


def render(key):
    out = OUT / key
    cfg = json.load(open(out / "config.json"))
    subprocess.run([PY, str(HERE / "film.py"), str(out / "config.json"), str(out / "drawn.mp4"), "--from", "0",
                    "--to", str(cfg["loop"]["end"]), "--preview", "10"], check=True, cwd=HERE)
    finish(key)


def loudness(mp4):
    """(integrated LUFS, true peak dBFS)"""
    log = subprocess.run(["ffmpeg", "-nostats", "-i", str(mp4), "-af", "ebur128=peak=true", "-f", "null", "-"],
                         capture_output=True, text=True).stderr.split("Summary:")[-1].split()
    return float(log[log.index("I:") + 1]), float(log[log.index("Peak:") + 1])


def finish(key):
    """The title over the drawing, and every short to the same loudness: each one plays on its own."""
    out = OUT / key
    gain = LUFS - loudness(out / "drawn.mp4")[0]
    ff("-i", out / "drawn.mp4", "-i", out / "title.png", "-filter_complex", "[0:v][1:v]overlay=0:0:format=auto,format=yuv420p",
       "-af", f"volume={gain:.1f}dB,alimiter=limit=0.84:attack=5:release=60:level=disabled",
       "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart",
       out / "short.mp4")
    print("wrote", out / "short.mp4", f"(music {gain:+.1f} dB)")


def check(key):
    """Length, loudness, and the loop point: last frame → first frame should look like any other step between frames."""
    import cv2
    import numpy as np
    mp4 = OUT / key / "short.mp4"
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(mp4)],
                               capture_output=True, text=True).stdout)
    lufs, peak = loudness(mp4)
    cap = cv2.VideoCapture(str(mp4)); frames = []
    while True:
        ok, f = cap.read()
        if not ok: break
        frames.append(cv2.resize(f, (270, 480)).astype(np.float32))
    steps = [float(np.abs(b - a).mean()) for a, b in zip(frames, frames[1:])]
    seam = float(np.abs(frames[0] - frames[-1]).mean())
    print(f"{key}: {dur:.1f} s, {lufs:.1f} LUFS, peak {peak:.1f} dBFS · loop point {seam:.2f} vs frame steps median "
          f"{np.median(steps):.2f} / max {max(steps):.2f}")


def mmss(sec):
    sec = round(sec)
    return f"{sec // 60}:{sec % 60:02d}"


def texts():
    src = json.loads((DATA / "music/sources.json").read_text())
    src["27"] = {**src["27"], "page": DE_BRA}
    blocks, lens = [], []
    for key, (n, name, _, _, title, scene_zh, scene_en, tag) in SHORTS.items():
        cfg = json.load(open(OUT / key / "config.json")); lens.append(cfg["loop"]["end"])
        p, who, r = PIECES[key], PLAYERS[PLAYED_BY[key]], src[key]
        p = (p[0].replace("，全曲", ""), p[1].replace(", complete", ""), *p[2:])     # a short is an excerpt
        lic = next((c for c in CC if r["license"].startswith(c)), None)
        pd_zh = "公有领域（美国政府作品）" if PLAYED_BY[key] == "marines" else "公有领域"
        pd_en = "public domain (US government work)" if PLAYED_BY[key] == "marines" else "public domain"
        page = link(r["page"]) + (" （IMSLP #869387）" if key == "27" else "")
        cut = "–".join(mmss(t) for t in cfg["excerpt"])
        music_zh = (f"音乐：莫扎特{" " if p[0][0].isascii() else ""}{p[0]}，{who[0]}。录音许可：{lic or pd_zh}。\n{page}" + (f"\n{CC[lic]}" if lic else "") +
                    f"\n本片节选了录音的 {cut}，并调整了音量。")
        music_en = (f"Music: W. A. Mozart, {p[1]}; {who[1]}. Recording licence: {lic or pd_en}.\n{page.replace('（', '(').replace('）', ')')}" +
                    (f"\n{CC[lic]}" if lic else "") + f"\nModifications: excerpt {cut} of the recording; volume adjusted.")
        desc = "\n".join([
            f"{scene_zh}用{p[2]}跟着音乐一笔一笔画出来，画完星星跟着节拍闪一闪。找找画里藏着的小星星！",
            f"{scene_en} Drawn in {p[3]} stroke by stroke to the music; when it's done, the stars twinkle in time. "
            "Can you find the little star hiding in it?", "",
            f"完整版：《{TITLE_ZH.split('｜')[0]}》，十首莫扎特、54 幅画，从早上画到夜里。",
            f"Full film: {TITLE_EN.split(' | ')[0]}, ten pieces by Mozart and 54 pictures, from morning to night.", "",
            music_zh, "", music_en, "",
            AI_ZH.replace("54 幅画、书桌和画笔", "这幅画、书桌和画笔").replace("把每幅画", "把这幅画"),
            "About the images: the picture, the desk and the tools are AI-generated (Codex image generation). The drawing is "
            "not a recording: our own program takes the picture apart stroke by stroke and draws it to the beat.", "",
            f"{BYLINE_ZH} · {BYLINE_EN.replace('By ', 'by ')}", "",
            "#shorts " + hashtags(["mozart", "classicalmusic", "musicforkids", "kidsart", tag])])   # 15 hashtags at most
        own_tags = [*PIECE_TAGS[key], "莫扎特", "古典音乐", "给孩子的古典音乐",
                    "儿童画", "小星星的莫扎特画本", "mozart", "mozart for kids", "classical music for kids", "drawing to music",
                    "kids drawing", p[3]]
        assert len(title) <= 100 and len(desc.encode()) <= 5000 and "<" not in title + desc and ">" not in title + desc
        blocks += [f"━━━━ {name}.mp4（{cfg['loop']['end']:.0f} 秒） ━━━━", "【标题 / Title】", title, "",
                   "【简介 / Description】", desc, "", "【标签 / Tags】", tags(own_tags), "", ""]
    head = f"""【上传设置 / Upload settings · 9 个短视频都一样】
· 竖屏短视频 1080×1920，30 fps，{min(lens):.0f}–{max(lens):.0f} 秒（都在 3 分钟以内）；会循环：最后一帧接回第一帧
· 标题和简介中英文合在一份（视频里的字本身就是中英文）
· 「相关视频」：在 Studio 里把每个短视频的「相关视频」设成长片《{TITLE_ZH.split('｜')[0]}》
· Altered or synthetic content（经过修改或合成的内容）：是 —— 书桌和画笔是看起来像真实照片的 AI 生成图，画也是 AI 生成的
· 观众：和长片一样，由你决定
· 类别：Education（或 Music）
· Content ID：录音都是公有领域或 CC BY；被认领就申诉（理由选 License 或 Public domain），写法见 lucas-academy-video-data/twinkle-stars/content-id-dispute.txt

"""
    (OUT / "youtube-description.shorts.txt").write_text(head + "\n".join(blocks))
    print(OUT / "youtube-description.shorts.txt")


if __name__ == "__main__":
    what, keys = sys.argv[1], sys.argv[2:] or list(SHORTS)
    if what == "texts": texts()
    else:
        for k in keys: {"prepare": prepare, "render": render, "finish": finish, "check": check}[what](k)
