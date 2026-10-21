"""Prepare one language's upload folder on the Desktop for 「都学了三年，放弃就白学了吗？」 (Education Economics 2):
the film, its Chinese and English captions, the cover and the description. It never uploads.

Refuses while a placeholder is in the film or the film changed after quality.py checked it. The folder holds only
what gets uploaded; files are moved, not copied (owner's rule). A replaced file goes to
out/fun-economics-02/package-backups/, never onto the Desktop.
  python3 scripts/fun-economics-02/package.py [--lang en]
"""
import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from common import FILM, OUT, PUB, ROOT

DELIVERY = OUT / "delivery"
LANG = sys.argv[sys.argv.index("--lang") + 1] if "--lang" in sys.argv else "zh"
NAME = "都学了三年放弃就白学了吗" + ("-英文版" if LANG == "en" else "")
DEST = Path.home() / f"Desktop/{NAME}-上传"
FILM_FILE = f"{NAME}.mp4" if LANG == "en" else f"{NAME}-中文版.mp4"
sys.path.insert(0, str(ROOT / "scripts"))
from youtube_tags import hashtags, tags  # noqa: E402

# The series is 教育经济学 / Education Economics from episode 2 on (owner, 2026-10-19).
TOPICS = {"zh": ["教育经济学", "沉没成本", "economics", "sunkcost", "educationeconomics", "pianolessons"],
          "en": ["economics", "sunkcost", "educationeconomics", "pianolessons", "mathforkids"]}
TITLE = {"zh": "都学了三年，放弃就白学了吗？｜教育经济学2 Education Economics 2", "en": "Is Quitting After Three Years a Waste? | Education Economics 2"}
CHAPTERS = {
    "zh": {"sc00": "学了三年，不想学了", "sc01": "「都学了三年了」", "sc02": "往前看，有更好的理由", "sc03": "沉没成本",
           "sc04": "拼错的乐高", "sc05": "第一步错了的作业", "sc06": "为什么舍不得", "sc07": "回到钢琴：现在的选择",
           "sc08": "彩蛋：保罗", "sc09": "结尾的问题"},
    "en": {"sc00": "Three years in, she wants to stop", "sc01": "\"It's been three years\"", "sc02": "Looking forward: better reasons",
           "sc03": "Sunk cost", "sc04": "The LEGO built wrong", "sc05": "Homework with a wrong first step",
           "sc06": "Why it's hard to let go", "sc07": "Back to the piano: today's choice", "sc08": "Easter egg: Paul",
           "sc09": "The closing question"},
}


def stamp(seconds: float) -> str:
    m, s = divmod(int(seconds), 60)
    return f"{m:02d}:{s:02d}"


def footage_credits() -> str:
    sources = json.loads((PUB / "footage/sources.json").read_text())
    used = set(json.loads((PUB / f"timeline.{LANG}.json").read_text())["footage"])
    source = (ROOT / "src/videos/fun-economics-02/FunEconomics02Video.tsx").read_text()
    lines = []
    for s in sources:
        name = f"{s['sec']}-{s['id']}.mp4"
        if name in used and f'"{name}"' in source:
            lines.append(f"· {s['title']} — {s['user']} https://www.pexels.com/video/{s['id']}/")
    return "\n".join(lines)


def describe(lang: str, chapters: str) -> str:
    clips = footage_credits()
    if lang == "en":
        return f"""Mary has been learning piano for three years. The pieces got harder, and one day she says: "I don't want to do piano anymore." Many parents' first reaction: it's been three years and so many lessons; if you quit now, wasn't it all for nothing?
Sticking with things is good, but it matters why. This episode starts with the reasons that look forward, then the economist's sunk cost: what is already spent and can't be gotten back, whichever way you choose, can't help you choose. A LEGO build with one brick in the wrong place and homework with a wrong first step work the same way.
The past has already sunk; the future hasn't come yet; all we can choose is now.

By Yancy Qin | Lucas Academy
Script written with Claude; some pictures are AI-generated; narration is AI-voiced (the narrator uses Louise's licensed voice, Mary uses Eunice's licensed voice). Captions in English and Chinese.

{chapters}

The homework in the film: 7 boxes of 8 pencils shared by 14 classmates. 7 × 8 = 56 pencils, 56 ÷ 14 = 4 each.

Research mentioned in the film:
· The IKEA effect: Norton, Mochon & Ariely (2012), "The IKEA effect: When labor leads to love", Journal of Consumer Psychology 22(3).
· LEGO models taken apart: Ariely, Kamenica & Prelec (2008), "Man's search for meaning: The case of Legos", Journal of Economic Behavior & Organization 67(3–4).
· Adults and children: Arkes & Ayton (1999), "The sunk cost and Concorde effects: Are humans less rational than lower animals?", Psychological Bulletin 125(5).

Video (Pexels):
{clips}
Paintings (public domain, Wikimedia Commons): Rembrandt (and workshop?), The Apostle Paul, c. 1657 (National Gallery of Art, Washington); Valentin de Boulogne (probably), Saint Paul Writing His Epistles, c. 1618–20 (Museum of Fine Arts, Houston); Rembrandt, Saint Paul in Prison, 1627 (Staatsgalerie Stuttgart); Rembrandt, Self-Portrait as the Apostle Paul, 1661 (Rijksmuseum).

Music:
· Minuet in G major, BWV Anh. 114 (Christian Petzold), recording from Musopen (Aaron Dunn), public domain
· Scott Joplin, Solace (1909), recording from Wikimedia Commons (Gnissah), public domain
· Erik Satie, Gymnopédie No. 1, Kevin MacLeod (incompetech.com), CC BY 3.0 https://creativecommons.org/licenses/by/3.0/
The recordings are looped, faded and level-adjusted in the film.
Scripture: Philippians 3:7, 3:13–14, World English Bible (public domain).

So next time a child says "I don't want to do this anymore," or you want to talk yourself into hanging on a little longer, ask yourself: is it the road ahead that keeps you there, or the road you've already walked?

{hashtags(TOPICS[lang])}
"""
    return f"""Mary 学钢琴三年了。曲子越来越难，有一天她说：「我不想学钢琴了。」很多爸爸妈妈的第一反应是：都学了三年了，学费交了那么多，现在放弃，不就白学了？
坚持当然是好的，只是也要看因为什么。这一集先讲往前看的理由，再讲经济学里的沉没成本：已经花掉、不管怎么选都拿不回来的，帮不了我们选择。拼错的乐高、第一步错了的作业，也是同一个道理。
过去的，已经沉下去了；将来，还没有来；能选的，只有现在。

作者 Yancy Qin | Lucas Academy
文案与 Claude 合作完成；部分画面由 AI 生成；配音为 AI 合成（旁白使用 Louise 的授权声线，Mary 使用 Eunice 的授权声线）。中英文字幕。

{chapters}

片中的作业题：一盒铅笔 8 支，7 盒平均分给 14 个同学。7 × 8 = 56 支，56 ÷ 14 = 4 支。

片中提到的研究：
· 宜家效应：Norton, Mochon & Ariely (2012), "The IKEA effect: When labor leads to love", Journal of Consumer Psychology 22(3).
· 被拆掉的乐高：Ariely, Kamenica & Prelec (2008), "Man's search for meaning: The case of Legos", Journal of Economic Behavior & Organization 67(3–4).
· 大人和小孩：Arkes & Ayton (1999), "The sunk cost and Concorde effects: Are humans less rational than lower animals?", Psychological Bulletin 125(5).

视频素材（Pexels）：
{clips}
油画（公有领域，Wikimedia Commons）：伦勃朗（及其工作室？）《使徒保罗》约 1657 年（美国国家美术馆）；瓦伦丁·德·布洛涅（推定）《圣保罗写书信》约 1618–20 年（休斯敦美术馆）；伦勃朗《狱中的圣保罗》1627 年（斯图加特国立美术馆）；伦勃朗《扮作使徒保罗的自画像》1661 年（荷兰国立博物馆）。

音乐：
· 《G 大调小步舞曲》BWV Anh. 114（Christian Petzold），录音来自 Musopen（Aaron Dunn），公有领域
· Scott Joplin《Solace》（1909），录音来自 Wikimedia Commons（Gnissah），公有领域
· Erik Satie《Gymnopédie No. 1》，Kevin MacLeod（incompetech.com），CC BY 3.0 https://creativecommons.org/licenses/by/3.0/
本片对录音做了循环、淡入淡出和音量调整。
经文：腓立比书 3:7、3:13–14，和合本。

那么，下一次，当孩子说「我不想学了」，或者你想劝自己再坚持一下的时候，你会问问自己：让你留下来的，是前面的路，还是身后已经走过的路？

{hashtags(TOPICS[lang])}
"""


def main() -> None:
    tl = json.loads((PUB / f"timeline.{LANG}.json").read_text())
    qa = json.loads((OUT / f"delivery-check.{LANG}.json").read_text())
    film = DELIVERY / f"{FILM}.{LANG}.mp4"
    if not film.exists() and (DEST / FILM_FILE).exists():
        raise SystemExit(f"Already packaged: the film is in {DEST}")
    if qa["missingFootage"]:
        raise SystemExit(f"Placeholders still in the film: {', '.join(qa['missingFootage'])}")
    assert not tl["draft"] and hashlib.sha256(film.read_bytes()).hexdigest() == qa["sha256"], "run quality.py on this film first"
    chapters = []
    for prefix, title in CHAPTERS[LANG].items():
        cue = next(c for c in tl["cues"] if c["id"].startswith(prefix))
        chapters.append(f"{'00:00' if prefix == 'sc00' else stamp(cue['start'])} {title}")
    description = describe(LANG, "\n".join(chapters))
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
    files = {film: FILM_FILE, DELIVERY / f"{FILM}.{LANG}.zh-Hans.srt": zh_srt, DELIVERY / f"{FILM}.{LANG}.en.srt": en_srt,
             cover: f"{NAME}-封面.jpg", text: f"{NAME}-上传描述.txt"}
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
