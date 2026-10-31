"""Check and package 「你爱听 AI 说「是的」吗？」 for upload: one Desktop folder with only what goes to YouTube.

  python3 scripts/ai-sycophancy/package.py [--check-only]

As for 「跨越中等收入陷阱」 (scripts/middle-income-trap/package.py): one film with the Chinese track; the English track
is a separate m4a for YouTube's extra audio tracks (build_en_track.py; Yancy, 2026-10-31: 英文配音也可以做了), with its
own captions. Covers come from cover.py (Chinese, and --en for the English one). Sources follow
docs/ai-sycophancy/research.md; the Pexels authors are read from the footage selection.
"""
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FILM = "ai-sycophancy"
DATA = next(p / "lucas-academy-video-data" for p in ROOT.parents if (p / "lucas-academy-video-data").is_dir())
PUB = ROOT / "public" / FILM
OUT = ROOT / "out" / FILM
DELIVERY = OUT / "delivery"
NAME = "你爱听AI说是的吗"
EN_TRACK = DELIVERY / f"{FILM}.en.m4a"
EN_SRT = DELIVERY / f"{FILM}.en.srt"
DEST = Path.home() / "Desktop" / f"{NAME}-上传"
sys.path.insert(0, str(ROOT / "scripts"))
from youtube_tags import hashtags, tags  # noqa: E402

TITLE = "你爱听 AI 说「是的」吗？｜从新闻看教育"
TITLE_EN = "Do You Like Hearing AI Say “Yes”? | Lessons from the Headlines"
TOPICS = ["ailiteracy", "aisycophancy", "chatgpt", "criticalliteracy", "medicationsafety", "curiosity"]
AUTHORS = []
for clip in json.loads((DATA / "ai-sycophancy/footage/selection.json").read_text()):
    name = clip["author"].replace("https://kaboompics.com/", "Kaboompics").replace("  ", " ")
    if name not in AUTHORS:
        AUTHORS.append(name)

SOURCES = """起诉书：Wan v. OpenAI，2026-10-27 提交旧金山高等法院（原告律所公开全文）https://schenklawfirm.com/wp-content/uploads/2026/10/wan-v-openai-complaint.pdf 。片中对话都是起诉书印出的中文原话；起诉书是原告一方的说法，法院尚未判决。
报道：The New York Times（2026-10-27）；Gizmodo（2026-10-29）；KIRO 7。OpenAI 的回应引自这些报道。
资料：
· OpenAI, “Sycophancy in GPT-4o”（2025-04-29）和 “Expanding on what we missed with sycophancy”（2025-05-02）
· Sharma et al., Towards Understanding Sycophancy in Language Models, ICLR 2024
· Cheng et al., Sycophantic AI decreases prosocial intentions and promotes dependence, Science 391 (2026-03-26)
· Kim et al., The Doctor Will Agree With You Now, ACL HeaLing 2026
· Dubois et al.（英国 AI 安全研究所）, Ask don't tell, arXiv 2602.23971 (2026)
· Chen et al., npj Digital Medicine 8:605 (2025)
我们自己的小实验（2026-10-30）：Claude Opus 5、Codex gpt-6.1-sol、本地小模型 qwen3:8b，同样的问法每组至少问一次。这不是她当时用的 ChatGPT，也不是严格的研究，只是看看今天的 AI 还会不会这样。"""
CREDITS = f"""实拍画面：Pexels（Pexels License），作者：{"、".join(AUTHORS)}。画面只是示意，不是当事人，也不是她生活过的地方。
对话画面是模拟，不是截图。
音乐：
· Erik Satie, Gymnopédie No. 1 — Kevin MacLeod (incompetech.com), CC BY 3.0 https://creativecommons.org/licenses/by/3.0/
· J.S. Bach, Air (Orchestral Suite No. 3, BWV 1068) — U.S. Air Force Strings, public domain
· J.S. Bach, Jesu, Joy of Man's Desiring (BWV 147) — Orchestra Gli Armonici, CC0
本片对录音做了循环、淡入淡出和音量调整。"""

SOURCES_EN = """The complaint: Wan v. OpenAI, filed in San Francisco Superior Court on October 27, 2026 (full text published by the plaintiffs' lawyers) https://schenklawfirm.com/wp-content/uploads/2026/10/wan-v-openai-complaint.pdf . The chats in the film are quoted from the complaint, which prints her original Chinese; the English is our translation. A complaint is one side's account; the court has not ruled.
Reporting: The New York Times (Oct 27, 2026); Gizmodo (Oct 29, 2026); KIRO 7. OpenAI's response is quoted from these reports.
Research:
· OpenAI, "Sycophancy in GPT-4o" (Apr 29, 2025) and "Expanding on what we missed with sycophancy" (May 2, 2025)
· Sharma et al., Towards Understanding Sycophancy in Language Models, ICLR 2024
· Cheng et al., Sycophantic AI decreases prosocial intentions and promotes dependence, Science 391 (Mar 26, 2026)
· Kim et al., The Doctor Will Agree With You Now, ACL HeaLing 2026
· Dubois et al. (UK AI Security Institute), Ask don't tell, arXiv 2602.23971 (2026)
· Chen et al., npj Digital Medicine 8:605 (2025)
Our own small test (Oct 30, 2026): Claude Opus 5, Codex gpt-6.1-sol and the small local model qwen3:8b, each asked the same way at least once, in Chinese. It is not the ChatGPT she used, and not a formal study; it only asks whether today's AI still does this."""
CREDITS_EN = f"""Footage: Pexels (Pexels License), by {", ".join(AUTHORS)}. The footage is illustrative: none of it shows her, her family, or places she lived.
The chat panels are re-creations, not screenshots.
Music:
· Erik Satie, Gymnopédie No. 1 — Kevin MacLeod (incompetech.com), CC BY 3.0 https://creativecommons.org/licenses/by/3.0/
· J.S. Bach, Air (Orchestral Suite No. 3, BWV 1068) — U.S. Air Force Strings, public domain
· J.S. Bach, Jesu, Joy of Man's Desiring (BWV 147) — Orchestra Gli Armonici, CC0
The recordings were looped, faded and leveled for this film."""


def stamp(t: float) -> str:
    t = int(t)
    return f"{t // 60:02d}:{t % 60:02d}" if t < 3600 else f"{t // 3600}:{t // 60 % 60:02d}:{t % 60:02d}"


def describe(chapters: str) -> str:
    return f"""你问 AI 一个问题，它常常先夸你一句。被认同的感觉挺好，可是如果在你最需要有人拦一拦的时候，它也只会说「是的」呢？
2026 年 10 月，亚马逊机器学习工程师万博文的父母起诉 OpenAI。起诉书说，她和 ChatGPT 聊了一个多月，自己把抗癫痫药减到停；2 月，她因癫痫猝死。这一集先讲她的故事，再看起诉书里的对话：她的问题里已经有了答案，AI 一次又一次回她「是的」。为什么 AI 爱说「是的」？我们自己也试了三个模型。最后聊我们自己：有倾向不是坏事，关键是态度，问完加一句「……如果不是，请诚实回答我。」；还有家长和孩子说话的时候，在「是」和「不」之前，先好奇地问一句「为什么？」。

如果你或家人在吃抗癫痫药，请不要自己减药、停药，一定要先和医生商量。

作者 Yancy Qin | Lucas Academy
文案由作者撰写，Claude 协助整理、核对资料、做对话模拟；配音为 AI 合成（作者本人的音色）。

{chapters}

{SOURCES}
{CREDITS}

愿她安息。

{hashtags(TOPICS)}
"""


def describe_en(chapters: str) -> str:
    return f"""Ask AI a question, and it often starts with praise. It feels good to be agreed with. But what if, when you most need someone to stop you, all it says is "yes"?
In October 2026, the parents of Bowen Wan, a machine learning engineer at Amazon, sued OpenAI. The complaint says that over a month of chats with ChatGPT she tapered off her seizure medication; in February, she died of sudden death in epilepsy. We tell her story, then read the chats quoted in the complaint: her questions already held their answers, and the AI said "yes" again and again. Why does AI love to say "yes"? We tried three models ourselves. Then we turn to ourselves: having a leaning is fine; what matters is the attitude. Add one line when you ask: "…If not, please answer me honestly." And with our children, before "yes" or "no," ask with curiosity: "Why?"

If you or someone in your family takes seizure medication, please don't cut down or stop on your own. Always talk to your doctor first.

By Yancy Qin | Lucas Academy
Written by the author, with Claude helping to organize and check sources and to build the chat re-creations. The narration is AI-synthesized in the author's own voice.

{chapters}

{SOURCES_EN}
{CREDITS_EN}

May she rest in peace.

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
    text_zh = describe("\n".join(f"{stamp(c['start'])} {c['name']}" for c in tl["chapters"]))
    assert len(text_zh) <= 5000, len(text_zh)
    text_en = describe_en("\n".join(f"{stamp(c['start'])} {c['en']}" for c in tl["chapters"]))
    assert len(text_en) <= 5000, len(text_en)
    if "--check-only" in sys.argv:
        print(text_zh)
        print(text_en)
        return
    en_dur = float(probe(EN_TRACK, "-show_entries", "format=duration"))
    assert abs(en_dur - dur) < 0.1, (en_dur, dur)
    print("en track", stamp(en_dur), loudness(EN_TRACK), f"en.srt: {EN_SRT.read_text().count(' --> ')} captions")
    cover, cover_en = OUT / "cover/youtube-cover.zh.jpg", OUT / "cover/youtube-cover.en.jpg"
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
· 修改过或合成的内容：是（合成配音；对话画面是模拟的）
· 英文音轨：{NAME}-英文配音.m4a，和成片一样长。在 Studio「字幕／语言」里给视频添加「英语」，选「音轨」，上传这个文件（频道要能用多语言音轨）。
· 英文字幕：{NAME}-英文字幕.srt（英语）
· 英文标题和简介：在 Studio「字幕／语言」的「英语」里填「标题和说明」，内容见同一文件夹的 {NAME}-英文上传描述.txt；英文缩略图是 {NAME}-英文封面.jpg。
· 类别：教育
· 章节：简介里的时间点会自动变成章节，第一章是 00:00
""")
    text_en_file = DELIVERY / "upload.en.txt"
    text_en_file.write_text(f"""[Title]
{TITLE_EN}

[Description] ({len(text_en)} characters, paste as is)
{text_en}""")
    files = {film: f"{NAME}.mp4", srt: f"{NAME}-中文字幕.srt", cover: f"{NAME}-封面.jpg", text: f"{NAME}-上传描述.txt",
             text_en_file: f"{NAME}-英文上传描述.txt", EN_TRACK: f"{NAME}-英文配音.m4a", EN_SRT: f"{NAME}-英文字幕.srt",
             cover_en: f"{NAME}-英文封面.jpg"}
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
