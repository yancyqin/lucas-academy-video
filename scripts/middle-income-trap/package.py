"""Check and package 「跨越中等收入陷阱」 for upload: one Desktop folder with only what goes to YouTube.

  python3 scripts/middle-income-trap/package.py [--check-only]

One film with the Chinese track; the English track is a separate m4a for YouTube's extra audio tracks
(build_en_track.py; Yancy, 2026-10-27: 做英文配音m4a吧), with its own captions. The cover is rendered first:
  npx remotion still src/index.ts MiddleIncomeTrapCover out/middle-income-trap/delivery/youtube-cover.png
  npx remotion still src/index.ts MiddleIncomeTrapCoverEn out/middle-income-trap/delivery/youtube-cover.en.png
Sources follow the 整理稿 v0.1 source table in the education repo (output/papers/middle_income_trap/).
"""
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FILM = "middle-income-trap"
PUB = ROOT / "public" / FILM
OUT = ROOT / "out" / FILM
DELIVERY = OUT / "delivery"
NAME = "跨越中等收入陷阱"
EN_TRACK = DELIVERY / f"{FILM}.en.m4a"
EN_SRT = DELIVERY / f"{FILM}.en.srt"
DEST = Path.home() / "Desktop" / f"{NAME}-上传"
sys.path.insert(0, str(ROOT / "scripts"))
from youtube_tags import hashtags, tags  # noqa: E402

TITLE = "跨越中等收入陷阱｜从新闻看教育"
TOPICS = ["middleincometrap", "lilu", "criticalliteracy", "curiosity", "argentina", "playtogether"]
SOURCES = """李录原话：Columbia Business School, 36th Annual Graham & Dodd Event with Li Lu ’96（2026-10-05）https://youtu.be/YRhnX_JAbC8 ，中文字幕用哥大官方中文翻译。
资料：
· 世界银行《2024 年世界发展报告：中等收入陷阱》
· Psacharopoulos & Patrinos (2018), Education Economics 26(5)
· Eichengreen, Park & Shin (2013), NBER w18673
· Hanushek & Woessmann (2012), Journal of Development Economics 99
· Rozelle & Hell, Invisible China (2020)
· 欧几里得：Heath (1921), A History of Greek Mathematics；Feynman (1985), Surely You're Joking, Mr. Feynman!；Hardy (1940), A Mathematician's Apology；《庄子·人间世》
· 爱因斯坦：On Education（1936 年演讲），收在 Out of My Later Years（1950）；那句话是他引用别人、并表示认同
· Paulo Freire；Baird et al. (2012), Psychological Science；Bonawitz et al. (2011), Cognition
· Ramani & Siegler (2008), Child Development 79(2)；Berkowitz et al. (2015), Science 350(6257)
· Kühn et al. (2014), Molecular Psychiatry 19(2)；Johannes, Vuorre & Przybylski (2021), Royal Society Open Science 8
· Campante & Glaeser (2009), NBER w15104；Ladeuix & Schiaffino (2022), Revista de Historia Económica；Jaume & Willén (2019), Journal of Labor Economics；OECD PISA 2022
经文：马太福音 13:31–32，和合本。"""
CREDITS = """照片：Martin Luther King Jr., 1962, O. Fernandez, New York World-Telegram and the Sun，美国国会图书馆藏，公有领域。
插图：AI 生成（Codex），不是照片，也不是任何人的原作。
音乐：
· Erik Satie, Gymnopédie No. 1 — Kevin MacLeod (incompetech.com), CC BY 3.0 https://creativecommons.org/licenses/by/3.0/
· J.S. Bach, Air (Orchestral Suite No. 3, BWV 1068) — U.S. Air Force Strings, public domain
· J.S. Bach, Jesu, Joy of Man's Desiring (BWV 147) — Orchestra Gli Armonici, CC0
本片对录音做了循环、淡入淡出和音量调整。"""


TITLE_EN = "Crossing the Middle-Income Trap | Lessons from the Headlines"
# Written in English for English viewers (Yancy, 2026-10-27: 英文标题描述也给我), not a line-by-line translation.
SOURCES_EN = """Li Lu's words: Columbia Business School, 36th Annual Graham & Dodd Event with Li Lu '96 (2026-10-05) https://youtu.be/YRhnX_JAbC8 . The English captions follow CBS's official transcript.
Sources:
· World Bank, World Development Report 2024: The Middle-Income Trap
· Psacharopoulos & Patrinos (2018), Education Economics 26(5)
· Eichengreen, Park & Shin (2013), NBER w18673
· Hanushek & Woessmann (2012), Journal of Development Economics 99
· Rozelle & Hell, Invisible China (2020)
· Euclid: Heath (1921), A History of Greek Mathematics; Feynman (1985), Surely You're Joking, Mr. Feynman!; Hardy (1940), A Mathematician's Apology; Zhuangzi, "In the World of Men" (our translation)
· Einstein, "On Education" (1936), in Out of My Later Years (1950); he was quoting someone else, and agreed
· Paulo Freire; Baird et al. (2012), Psychological Science; Bonawitz et al. (2011), Cognition
· Ramani & Siegler (2008), Child Development 79(2); Berkowitz et al. (2015), Science 350(6257)
· Kühn et al. (2014), Molecular Psychiatry 19(2); Johannes, Vuorre & Przybylski (2021), Royal Society Open Science 8
· Campante & Glaeser (2009), NBER w15104; Ladeuix & Schiaffino (2022), Revista de Historia Económica; Jaume & Willén (2019), Journal of Labor Economics; OECD PISA 2022
Scripture: Matthew 13:31–32, World English Bible (English track); Chinese Union Version (Chinese track)."""
CREDITS_EN = """Photo: Martin Luther King Jr., 1962, O. Fernandez, New York World-Telegram and the Sun, Library of Congress, public domain.
Illustrations: AI-generated (Codex); not photographs, and not anyone's original work.
Music:
· Erik Satie, Gymnopédie No. 1 — Kevin MacLeod (incompetech.com), CC BY 3.0 https://creativecommons.org/licenses/by/3.0/
· J.S. Bach, Air (Orchestral Suite No. 3, BWV 1068) — U.S. Air Force Strings, public domain
· J.S. Bach, Jesu, Joy of Man's Desiring (BWV 147) — Orchestra Gli Armonici, CC0
The recordings were looped, faded and leveled for this film."""


def describe_en(chapters: str) -> str:
    return f"""Li Lu's recent talk at Columbia Business School brought a phrase back into the conversation: the middle-income trap. Many countries climb out of poverty to middle income, and then stop rising for decades. What keeps a person, or a country, stuck under the ceiling? I believe one big factor is the quality of education.
We start with the evidence: one more year of school raises income by about 9%, yet in Latin America plenty of years in school did not bring growth, because students learned too little. Then we ask what is useful to learn in the age of AI, and why learning needn't be useful at all: Euclid's threepence, Feynman's wobbling plate, Hardy's number theory, Zhuangzi's "use of the useless." Questioning the question itself is critical literacy. What can ordinary families do? Ten or fifteen minutes a day, while cooking, at bedtime, even playing games together, is a start. And Argentina reminds us that "eventually" is a heavy word.

By Yancy Qin | Lucas Academy
Written by the author, with Claude helping to organize and check sources. The narration is AI-synthesized in the author's own voice; the illustrations are AI-generated (Codex).

{chapters}

{SOURCES_EN}
{CREDITS_EN}

The affairs of nations are big. What we can do starts at home, today: keep curiosity alive, learn together, explore together.

{hashtags(TOPICS)}
"""


def stamp(t: float) -> str:
    t = int(t)
    return f"{t // 60:02d}:{t % 60:02d}" if t < 3600 else f"{t // 3600}:{t // 60 % 60:02d}:{t % 60:02d}"


def describe(chapters: str) -> str:
    return f"""最近，李录在哥伦比亚商学院的对谈，又把“中等收入陷阱”这个词带火了：很多国家从贫穷走到中等收入以后，就停在那里，几十年都上不去。是什么，让一个国家停在天花板下面？我认为，很重要的一个因素，是教育的质量。
这一集先看证据：多上一年学，收入平均高出大约 9%；拉美上学的年数并不低，学会的却不多。再问“现在学什么有用”：从欧几里得、费曼、哈代到庄子的“无用之用”，学习不一定要有用；敢质疑问题本身，就是批判性素养。普通家庭能做什么？做饭、睡前、一起玩游戏，一天十几分钟就够。最后看阿根廷的例子。

作者 Yancy Qin | Lucas Academy
文案由作者撰写，Claude 协助整理、核对资料；配音为 AI 合成（作者本人的音色）；插图为 AI 生成（Codex）。

{chapters}

{SOURCES}
{CREDITS}

国家的事很大，我们能做的，就从自己家里、从今天开始，保住好奇心、一起学习、一起探索。

{hashtags(TOPICS)}
"""


def probe(path: Path, *entries: str) -> str:
    return subprocess.run(["ffprobe", "-v", "error", *entries, "-of", "csv=p=0", str(path)], capture_output=True, text=True).stdout.strip()


def loudness(path: Path) -> str:
    p = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(path), "-map", "0:a:0", "-af", "ebur128=peak=true", "-f", "null", "-"],
                       capture_output=True, text=True)
    i = re.findall(r"I:\s+(-?[\d.]+) LUFS", p.stderr)
    pk = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", p.stderr)
    return f"{i[-1]} LUFS, peak {pk[-1]} dBFS"


def main() -> None:
    tl = json.loads((PUB / "timeline.json").read_text())
    film = DELIVERY / f"{FILM}.mp4"
    srt = DELIVERY / f"{FILM}.zh-Hans.srt"
    dur = float(probe(film, "-show_entries", "format=duration"))
    assert abs(dur - tl["durationSeconds"]) < 1.0, (dur, tl["durationSeconds"])
    print("film", stamp(dur), probe(film, "-show_entries", "stream=codec_type,width,height").splitlines())
    print("audio", loudness(film))
    black = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(film), "-vf", "blackdetect=d=1.0:pix_th=0.06", "-an", "-f", "null", "-"],
                           capture_output=True, text=True).stderr
    print("black stretches ≥1 s:", re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", black) or "none")
    print(f"zh-Hans.srt: {srt.read_text().count(' --> ')} captions")
    chapters = "\n".join(f"{stamp(c['start'])} {c['name']}" for c in tl["chapters"])
    text_zh = describe(chapters)
    assert len(text_zh) <= 5000, len(text_zh)
    text_en = describe_en("\n".join(f"{stamp(c['start'])} {c['en']}" for c in tl["chapters"]))
    assert len(text_en) <= 5000, len(text_en)
    if "--check-only" in sys.argv:
        print(text_zh)
        print(text_en)
        return
    if EN_TRACK.exists():
        en_dur = float(probe(EN_TRACK, "-show_entries", "format=duration"))
        assert abs(en_dur - dur) < 0.1, (en_dur, dur)
        print("en track", stamp(en_dur), loudness(EN_TRACK), f"en.srt: {EN_SRT.read_text().count(' --> ')} captions")
    cover = DELIVERY / "youtube-cover.jpg"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(DELIVERY / "youtube-cover.png"), "-q:v", "3", str(cover)], check=True)
    # English cover (MiddleIncomeTrapCoverEn → youtube-cover.en.png; Yancy, 2026-10-27: 给我英文封面)
    cover_en = DELIVERY / "youtube-cover.en.jpg"
    if (DELIVERY / "youtube-cover.en.png").exists():
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(DELIVERY / "youtube-cover.en.png"), "-q:v", "3", str(cover_en)], check=True)
    card = stamp(tl["lines"]["sc02-07"]["start"])
    text = DELIVERY / "upload.txt"
    text.write_text(f"""【标题】
{TITLE}

【简介】（可直接粘贴，{len(text_zh)} 字符）
{text_zh}
【标签】
{tags(TOPICS)}

【上传设置】
· 视频：{NAME}.mp4（1920×1080，{stamp(dur)}）
· 字幕：{NAME}-中文字幕.srt（中文简体）
· 缩略图：{NAME}-封面.jpg（1280×720）
· 视频语言：中文（简体）
· 观众：由作者选择
· 修改过或合成的内容：是（合成配音、AI 插图）
· 英文音轨：{NAME}-英文配音.m4a，和成片一样长。在 Studio「字幕／语言」里给视频添加「英语」，选「音轨」，上传这个文件（频道要能用多语言音轨）。
· 英文字幕：{NAME}-英文字幕.srt（英语）
· 英文标题和简介：在 Studio「字幕／语言」的「英语」里填「标题和说明」，内容见同一文件夹的 {NAME}-英文上传描述.txt。
· 类别：教育
· 章节：简介里的时间点会自动变成章节，第一章是 00:00
· 卡片：在 {card} 加一张「视频」卡片，链到《一根冰棍，要花多少钱？｜趣味经济学1》。片子里这句是「可以点击右上角，看我们另一个视频」，画面上有箭头指向右上角；那一集要先上线才能选。
""")
    text_en_file = DELIVERY / "upload.en.txt"
    text_en_file.write_text(f"""[Title]
{TITLE_EN}

[Description] ({len(text_en)} characters, paste as is)
{text_en}""")
    files = {film: f"{NAME}.mp4", srt: f"{NAME}-中文字幕.srt", cover: f"{NAME}-封面.jpg", text: f"{NAME}-上传描述.txt",
             text_en_file: f"{NAME}-英文上传描述.txt"}
    if EN_TRACK.exists():
        files |= {EN_TRACK: f"{NAME}-英文配音.m4a", EN_SRT: f"{NAME}-英文字幕.srt"}
    if cover_en.exists():
        files[cover_en] = f"{NAME}-英文封面.jpg"
    DEST.mkdir(parents=True, exist_ok=True)
    manifest = []
    for source, name in files.items():
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        shutil.copy2(source, DEST / name)
        assert hashlib.sha256((DEST / name).read_bytes()).hexdigest() == digest, name
        manifest.append({"file": name, "sha256": digest, "bytes": (DEST / name).stat().st_size})
    (OUT / "package-manifest.json").write_text(json.dumps({"destination": str(DEST), "files": manifest}, ensure_ascii=False, indent=2) + "\n")
    print(f"copied to {DEST}")


if __name__ == "__main__":
    main()
