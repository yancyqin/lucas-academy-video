"""Prepare 「你会算 7×8 吗？」's upload folder on the Desktop (film, Chinese and English captions, cover, description).
It never uploads. Files are moved, not copied (owner's rule); one it replaces goes to out/fun-economics-01-7x8/package-backups/.
  python3 scripts/fun-economics-01-7x8/package.py [--lang en]
"""
import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from common import FILM, LANG, OUT, PUB, ROOT

sys.path.insert(0, str(ROOT / "scripts"))
from youtube_tags import hashtags, tags  # noqa: E402

DELIVERY = OUT / "delivery"
NAME = "你会算7x8吗" + ("-英文版" if LANG == "en" else "")
DEST = Path.home() / f"Desktop/{NAME}-上传"
FILM_FILE = f"{NAME}.mp4" if LANG == "en" else f"{NAME}-中文版.mp4"
TOPICS = {"zh": ["趣味经济学", "乘法", "手指乘法", "数学", "multiplication", "fingermath"],
          "en": ["multiplication", "fingermath", "mathforkids", "funeconomics"]}
CHAPTERS = {"zh": {"hx00": "你会算 7 × 8 吗？", "hx01": "用手指算", "hx02": "为什么可以这样算", "hx03": "结尾的问题"},
            "en": {"hx00": "Can you work out 7 × 8?", "hx01": "With your fingers", "hx02": "Why it works", "hx03": "The closing question"}}
TITLE = {"zh": "你会算 7×8 吗？｜趣味经济学 1 · 番外", "en": "Can You Work Out 7 × 8? | Fun Economics 1 · Extra"}


def stamp(seconds: float) -> str:
    m, s = divmod(int(seconds), 60)
    return f"{m:02d}:{s:02d}"


def describe(chapters: str) -> str:
    if LANG == "en":
        return f"""Everyone knows 7 × 8 = 56. But without the times table, using just your two hands, can you work it out?
The raised fingers make the tens and the bent fingers multiply to the ones. Why does that work? One line of math, 7 × 8 = (10 − 3) × (10 − 2), shows how it matches your fingers; a 10 × 10 dot grid shows why 3 × 2 is added back; and x and y prove it for any two numbers from 6 to 10.

An extra episode of "How Much Does an Ice Pop Cost?" (Fun Economics 1), where 7 × 8 had four paths and the fingers were path three.

By Yancy Qin, Louise Yang | Lucas Academy
Script written with Claude; narration is AI-voiced (the narrator uses Louise's licensed voice). The hands were filmed by the author.

{chapters}

The math in the film:
· 7 × 8 = (10 − 3) × (10 − 2) = 100 − 30 − 20 + 3 × 2 = 50 + 6 = 56
· For any two numbers from 6 to 10: (10 − x)(10 − y) = 100 − 10x − 10y + xy = 10 × (10 − x − y) + x × y. x and y are the bent fingers on each hand, and 10 − x − y is exactly the raised fingers.

Music: Minuet in G major, BWV Anh. 114 (Christian Petzold), recording from Musopen (Aaron Dunn), public domain. The recording is looped, faded and level-adjusted in the film.

Now try 6 × 7: how many fingers are up, and how many are bent? Does your answer match the times table?

{hashtags(TOPICS[LANG])}
"""
    return f"""7 乘 8 等于 56，人人都会背。可不背口诀、只用两只手，你会算吗？
伸出的手指算十位，弯着的手指相乘是个位。这个手指算法为什么对？用一个式子 7 × 8 = (10 − 3) × (10 − 2) 讲清楚式子和手指的关系，用 10 × 10 的点阵看出为什么要加回 3 × 2，最后用 x、y 证明 6 到 10 的任意两个数都这样算。

这是《一根冰棍，要花多少钱？》（趣味经济学 1）的番外：那一集里，7 × 8 有四条路，手指是第三条。

作者 Yancy Qin, Louise Yang | Lucas Academy
文案与 Claude 合作完成；配音为 AI 合成（旁白使用 Louise 的授权声线）。手的视频由作者拍摄。

{chapters}

片中的式子：
· 7 × 8 = (10 − 3) × (10 − 2) = 100 − 30 − 20 + 3 × 2 = 50 + 6 = 56
· 6 到 10 的任意两个数：(10 − x)(10 − y) = 100 − 10x − 10y + xy = 10 × (10 − x − y) + x × y；x、y 是两只手弯着的手指，10 − x − y 正是伸出的手指。

音乐：《G 大调小步舞曲》BWV Anh. 114（Christian Petzold），录音来自 Musopen（Aaron Dunn），公有领域。本片对录音做了循环、淡入淡出和音量调整。

换成 6 乘 7 试试：伸出几根，弯着几根？算出来的，和口诀一样吗？

{hashtags(TOPICS[LANG])}
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
    chapters = "\n".join(f"{'00:00' if p == 'hx00' else stamp(next(c for c in tl['cues'] if c['id'].startswith(p))['start'])} {t}"
                         for p, t in CHAPTERS[LANG].items())
    description = describe(chapters)
    assert len(description) <= 5000, len(description)
    cover = DELIVERY / f"cover.{LANG}.jpg"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(DELIVERY / f"cover.{LANG}.png"), "-vf", "scale=1280:720", "-q:v", "3", str(cover)], check=True)
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
· 修改过或合成的内容：是（合成配音）
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
