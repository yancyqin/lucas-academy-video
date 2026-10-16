"""Prepare a film's upload folder on the Desktop (film, Chinese and English captions, cover, description). It never uploads.

Refuses while delivery-check.json lists missing footage (a placeholder is still in the film) or the film changed after
quality.py checked it. The folder holds only what gets uploaded, and the files are moved there, not copied, so only one
copy exists (owner's rule). A file it replaces goes to out/fun-economics-01/package-backups/, never onto the Desktop.
  python3 scripts/fun-economics-01/package.py [--lang en]
"""
import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PUB = ROOT / "public/fun-economics-01"
OUT = ROOT / "out/fun-economics-01"
DELIVERY = OUT / "delivery"
LANG = sys.argv[sys.argv.index("--lang") + 1] if "--lang" in sys.argv else "zh"
NAME = "一根冰棍要花多少钱" + ("-英文版" if LANG == "en" else "")
DEST = Path.home() / f"Desktop/{NAME}-上传"
FILM_FILE = f"{NAME}.mp4" if LANG == "en" else f"{NAME}-中文版.mp4"
sys.path.insert(0, str(ROOT / "scripts"))
from youtube_tags import hashtags, tags  # noqa: E402

TOPICS = {"zh": ["趣味经济学", "机会成本", "乘法", "economics", "opportunitycost", "multiplication"],
          "en": ["economics", "opportunitycost", "multiplication", "funeconomics", "mathforkids"]}
CHAPTERS = {
    "zh": {"oc00": "一根冰棍，要花多少钱？", "oc01": "机会成本：没拿到的那两块钱", "oc02": "学一样东西，也一样",
           "oc03": "还不会的时候", "oc04": "7 乘 8，有几条路？", "oc05": "先走路，再背口诀",
           "oc06": "彩蛋：马大和马利亚", "oc07": "结尾的问题"},
    "en": {"oc00": "How much does an ice pop cost?", "oc01": "Opportunity cost: the dollar you didn't get",
           "oc02": "Learning something is the same", "oc03": "Before you know the answer", "oc04": "7 × 8: how many paths?",
           "oc05": "Walk the paths first, then learn the table", "oc06": "Easter egg: Martha and Mary", "oc07": "The closing question"},
}
TITLE = {"zh": "一根冰棍，要花多少钱？｜趣味经济学1 Fun Economics 1", "en": "How Much Does an Ice Pop Cost? | Fun Economics 1"}


def stamp(seconds: float) -> str:
    m, s = divmod(int(seconds), 60)
    return f"{m:02d}:{s:02d}"


def describe(chapters: str) -> str:
    if LANG == "en":
        return f"""An ice pop costs $2, but the walk there and back takes 30 minutes, and those 30 minutes could have earned $1 doing chores. So the ice pop really costs $3.
From ice pops to piano lessons to the most familiar multiplication fact, 7 × 8: learning has a hidden price too. Before you know the answer, working it out yourself teaches you many ways of thinking; memorize the answer first, and you stop thinking.

By Yancy Qin, Louise Yang | Lucas Academy
Script written with Claude; illustrations are AI-generated; narration is AI-voiced (the narrator uses Louise's licensed voice, Mary uses Eunice's licensed voice).

{chapters}

The four paths in the film:
· Add equal groups: multiplying is adding the same number several times.
· Split and join: 8 × 7 = 8 × 5 + 8 × 2 = 40 + 16 = 56, the very example in the US Common Core math standard 3.OA.B.5.
· Fingers: to multiply two numbers from 6 to 10, the raised fingers (how much each number is over 5) add up to the tens, and the bent fingers multiply to the ones. Why it works has a video of its own: Can You Work Out 7 × 8?
· Double and halve: the ancient Egyptian Rhind Mathematical Papyrus (a copy from about 1550 BC) multiplies by doubling. Writing the multiplier as a sum of 1, 2, 4, 8, … is the binary used inside computers.

Coding class homework page: https://lucasacademy.org/programs/coding-class/score-homework

Images (public domain, Wikimedia Commons):
· Portrait of Frédéric Bastiat, drawn by Émile Desmaisons, lithograph by Léveillé (Bibliothèque nationale de France)
· Modern transcription of Problem 41 of the Rhind Mathematical Papyrus (Bakha, after Chace, The Rhind Mathematical Papyrus)
· Johannes Vermeer, Christ in the House of Martha and Mary (c. 1655)

Music:
· Minuet in G major, BWV Anh. 114 (Christian Petzold), recording from Musopen (Aaron Dunn), public domain
· Scott Joplin, Solace (1909), recording from Wikimedia Commons (Gnissah), public domain
· Erik Satie, Gymnopédie No. 1, Kevin MacLeod (incompetech.com), CC BY 3.0 https://creativecommons.org/licenses/by/3.0/
The recordings are looped, faded and level-adjusted in the film.
Scripture: Luke 10:38–42, World English Bible (public domain).

So, the next time you spend 30 minutes, will you see the choice you put down? When you memorize a few words, learn a formula by heart, or let AI write a program for you, do you know what chance you're giving up?
At Lucas Academy, we care about what you learn, and we care even more that, while you learn, you learn how to think.

{hashtags(TOPICS[LANG])}
"""
    return f"""一根冰棍五块钱，可来回要走三十分钟，那三十分钟本来能挣两块钱。买冰棍，其实花了七块钱。
从冰棍到钢琴课，再到一道最熟的乘法 7 × 8：学习里也藏着看不见的价钱。还不会的时候，自己想办法的过程会教给你很多种想法；答案先背下来，就不会再去想了。

作者 Yancy Qin, Louise Yang | Lucas Academy
文案与 Claude 合作完成；插图由 AI 生成；配音为 AI 合成（旁白使用 Louise 的授权声线，Mary 使用 Eunice 的授权声线）。

{chapters}

片中的四条路：
· 连加：乘法就是几个相同的数加起来。
· 拆开再合：8 × 7 = 8 × 5 + 8 × 2 = 40 + 16 = 56，这正是美国 Common Core 数学标准 3.OA.B.5 里的例子。
· 手指：6 到 10 两数相乘，伸出的手指（每个数比 5 多几）合起来是十位，弯着的手指相乘是个位。为什么可以这样算，我们单独做了一个视频：《你会算 7×8 吗？》
· 翻倍和减半：古埃及的莱因德数学纸草书（约公元前 1550 年的抄本）用翻倍做乘法；把乘数拆成 1、2、4、8……的和，就是计算机里的二进制。

编程课作业页：https://lucasacademy.org/programs/coding-class/score-homework

图片（公有领域，Wikimedia Commons）：
· 巴斯夏肖像，Émile Desmaisons 画、Léveillé 石版（法国国家图书馆）
· 莱因德数学纸草书第 41 题的现代誊写图（Bakha，据 Chace《The Rhind Mathematical Papyrus》）
· 维米尔《基督在马大和马利亚家中》（约 1655 年）

音乐：
· 《G 大调小步舞曲》BWV Anh. 114（Christian Petzold），录音来自 Musopen（Aaron Dunn），公有领域
· Scott Joplin《Solace》（1909），录音来自 Wikimedia Commons（Gnissah），公有领域
· Erik Satie《Gymnopédie No. 1》，Kevin MacLeod（incompetech.com），CC BY 3.0 https://creativecommons.org/licenses/by/3.0/
本片对录音做了循环、淡入淡出和音量调整。
经文：路加福音 10:38–42，和合本。

那么，下一次花掉三十分钟的时候，你会看见那个被放下的选项吗？当你背下几个单词、记住一个公式，或者让 AI 直接写出一段程序的时候，你知道自己放下了什么样的机会吗？
在 Lucas Academy，我们在乎你学会了什么，更在乎你在学的过程中，学会怎样思考。

{hashtags(TOPICS[LANG])}
"""


def main() -> None:
    tl = json.loads((PUB / f"timeline.{LANG}.json").read_text())
    qa = json.loads((OUT / f"delivery-check.{LANG}.json").read_text())
    film = DELIVERY / f"fun-economics-01.{LANG}.mp4"
    if not film.exists() and (DEST / FILM_FILE).exists():
        raise SystemExit(f"Already packaged: the film is in {DEST}")
    if qa["missingFootage"]:
        raise SystemExit(f"Placeholders still in the film: {', '.join(qa['missingFootage'])}")
    assert not tl["draft"] and hashlib.sha256(film.read_bytes()).hexdigest() == qa["sha256"], "run quality.py on this film first"
    chapters = []
    for prefix, title in CHAPTERS[LANG].items():
        cue = next(c for c in tl["cues"] if c["id"].startswith(prefix))
        chapters.append(f"{'00:00' if prefix == 'oc00' else stamp(cue['start'])} {title}")
    description = describe("\n".join(chapters))
    assert len(description) <= 5000, len(description)
    cover = DELIVERY / f"cover.{LANG}.jpg"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(DELIVERY / f"cover.{LANG}.png"), "-vf", "scale=1280:720", "-q:v", "3", str(cover)], check=True)
    assert cover.stat().st_size < 2_000_000
    zh_srt, en_srt = f"{NAME}-中文字幕.srt", f"{NAME}-英文字幕.srt"
    content = f"""【标题 / Title】
{TITLE[LANG]}

【简介 / Description】（可直接粘贴，{len(description)} 字符）
{description}
【标签 / Tags】
{tags(TOPICS[LANG])}

【上传设置 / Upload settings】
· 视频：{FILM_FILE}（1920×1080，{stamp(round(tl['durationSeconds']))}，{qa['integratedLUFS']} LUFS）
· 字幕：{zh_srt}（中文）和 {en_srt}（English），两份都上传
· 缩略图：{NAME}-封面.jpg（1280×720）
· 视频语言：{"英语 English" if LANG == "en" else "中文（简体）"}
· 观众：由作者选择
· 修改过或合成的内容：是（合成配音；AI 配图）
· 类别：教育
"""
    text = DELIVERY / f"upload.{LANG}.txt"
    text.write_text(content)
    files = {film: FILM_FILE, DELIVERY / f"fun-economics-01.{LANG}.zh-Hans.srt": zh_srt,
             DELIVERY / f"fun-economics-01.{LANG}.en.srt": en_srt, cover: f"{NAME}-封面.jpg", text: f"{NAME}-上传描述.txt"}
    DEST.mkdir(parents=True, exist_ok=True)
    manifest = []
    for source, name in files.items():
        target = DEST / name
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest() != digest:
            backup = OUT / "package-backups" / datetime.now().strftime("%Y%m%d-%H%M%S")
            backup.mkdir(parents=True, exist_ok=True)
            shutil.move(target, backup / name)
        shutil.move(source, target)
        assert hashlib.sha256(target.read_bytes()).hexdigest() == digest, name
        manifest.append({"file": name, "sha256": digest, "bytes": target.stat().st_size})
    (OUT / f"package-manifest.{LANG}.json").write_text(json.dumps({"destination": str(DEST), "files": manifest}, ensure_ascii=False, indent=2) + "\n")
    print(f"film, captions, cover and description moved to {DEST}")


if __name__ == "__main__":
    main()
