"""好奇新世界 / Curious Worlds: the YouTube upload text of each film (README "YouTube tags", whole-person layout).

The chapters come from the film's own timeline, so they match its cut. Title, description, topic tags and links are
per episode, in scripts/weekly/<ep>/youtube.json: {"title": {"zh", "en"}, "description": {"zh", "en"}, "tags": [...],
"links": [[label, url], ...]}.

  python3 scripts/weekly/youtube.py 001 [zh|en]     -> out/weekly/<ep>/youtube.<lang>.txt
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from youtube_tags import hashtags, tags  # noqa: E402

FRIDAYS = {
    "zh": "每周五下午 4–5 点，好奇新世界每周项目展示：欢迎来听，也欢迎带一个想法来讲。",
    "en": "Fridays 4–5 pm, Curious Worlds Weekly: come to listen, or bring an idea to share.",
}
SETTINGS = {
    "zh": """- 视频：weekly-{ep}.zh.mp4（中文）
- 字幕：weekly-{ep}.zh.zh-Hans.srt（中文简体）、weekly-{ep}.zh.en.srt（English）
- 封面：cover.zh.jpg（一个问题 + 右上角系列名斜带）""",
    "en": """- Video: weekly-{ep}.en.mp4 (English)
- Captions: weekly-{ep}.en.en.srt (English), weekly-{ep}.en.zh-Hans.srt (Chinese, Simplified)
- Cover: cover.en.jpg (one question + the series ribbon)""",
}


def clock(s: float) -> str:
    m, s = divmod(int(s), 60)
    return f"{m}:{s:02d}"


def main(ep: str, lang: str) -> None:
    tl = json.loads((ROOT / "public/weekly" / ep / f"timeline.{lang}.json").read_text())
    meta = json.loads((ROOT / "scripts/weekly" / ep / "youtube.json").read_text())
    chapters = [(0.0, {"zh": "开场", "en": "Opening"}[lang])] + [(c["t"], c[lang]) for c in tl["chapters"]]
    chap = "\n".join(f"{clock(t)} {name}" for t, name in chapters)
    links = "\n".join(f"{label}: {url}" for label, url in meta.get("links", []))
    text = f"""【标题 / Title】
{meta['title'][lang]}

【简介 / Description】
{meta['description'][lang]}

{chap}

{links}

{FRIDAYS[lang]}
lucasacademy.org/weekly

{hashtags(meta.get('tags', []))}

【标签 / Tags】
{tags(meta.get('tags', []))}

【上传设置 / Upload settings】
{SETTINGS[lang].format(ep=ep)}
"""
    out = ROOT / "out/weekly" / ep / f"youtube.{lang}.txt"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    for language in sys.argv[2:] or ["zh", "en"]:
        main(sys.argv[1], language)
