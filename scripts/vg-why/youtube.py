"""English YouTube title, description and tags for "Why Did Van Gogh Paint Them?".

    python3 scripts/vg-why/youtube.py

Writes out/vg-why-paint-them/youtube-description.en.txt in the project's layout (title,
description ending in the hashtags, tags, upload settings); tags follow the README's
"YouTube tags" rule via scripts/youtube_tags.py. The film is one upload: Chinese is the default audio,
English is a dub track, so this is the English title and description added in
Studio → Languages. Chapters come from the shared timeline (src/data/vg-why-paint-them.json,
identical for both languages); the works come from shots.ts, the same 31 that
credits.py lists. YouTube allows 5,000 characters in a description.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from youtube_tags import hashtags, tags  # noqa: E402  (README "YouTube tags": lowercase, the default set)

OUT = ROOT / "out/vg-why-paint-them/youtube-description.en.txt"
SOURCES_URL = "https://github.com/yancyqin/lucas-academy-video/blob/main/public/vg-why-paint-them/art/SOURCES.txt"

TITLE = "Why Did Van Gogh Paint Them? | Painting the People He Loved"

LEAD = """A postman with a big beard, and a painter friend with stars behind him. Why did Van Gogh paint them?

In this short film for children and parents, we look closely at Van Gogh's portraits of Joseph Roulin, the postman he called “a more interesting man than many people”, and of Eugène Boch, painted against a deep blue sky full of small stars. We read a few lines from Van Gogh's letters and see how he hoped colour could comfort people, like music. Then come Almond Blossom, a gift for his newborn nephew, and The Starry Night, where you decide which lines feel peaceful and which feel full of energy.

At the end, we share the art lessons these paintings inspired at Lucas Academy, Love Is What Lasts, and ask you: who would you like to look at more carefully?

English audio: in the player, choose Settings → Audio track → English. Subtitles are in English and Chinese."""

# Chapter names follow the sections of the English script (lucas-academy-media data/scripts/vg-why-paint-them/en-edit.md).
CHAPTERS = {
    "vg01": "Why paint this person?",
    "vg02": "Who was Van Gogh?",
    "vg03": "Roulin: a man worth looking at",
    "vg04": "How did a friend care for him?",
    "vg05": "Boch: a friend in front of the stars",
    "vg06": "“I paint the infinite”",
    "vg07": "Colour can speak",
    "vg08": "A painting for a new life",
    "vg09": "Look at the lines, keep your own feeling",
    "vg10": "From Van Gogh to our lessons",
    "vg11": "Who would you look at more carefully?",
}

HASHTAGS = ["vangogh", "vincentvangogh", "starrynight"]
TAGS = ["van gogh", "vincent van gogh", "van gogh for kids", "postman roulin", "joseph roulin", "eugène boch",
        "almond blossom", "the starry night", "van gogh letters", "portraits", "art history for kids", "art lessons"]
UPLOAD = """【上传设置 / Upload settings】
· The film is one upload: vg-why-paint-them.zh.mp4, Chinese as the default audio
· Studio → Languages → English: paste the title and description above
· English audio: vg-why-paint-them.en.m4a as the English dub (same length as the video)
· Subtitles: en.srt and zh-Hans.srt (both line up with either audio track)
· Thumbnail: youtube-cover.en.jpg (1280×720)
· Altered or synthetic content: Yes (the narration is a synthesized voice)
· Category: Education"""


def stamp(t: float) -> str:
    t = int(t)
    return f"{t // 60}:{t % 60:02d}"


def chapters() -> list[str]:
    tl = json.loads((ROOT / "src/data/vg-why-paint-them.json").read_text(encoding="utf-8"))
    first = {}
    for cue in tl["cues"]:
        first.setdefault(cue["id"][:4], cue["start"])
    assert list(first) == list(CHAPTERS), f"sections changed: {list(first)}"
    return [f"{'0:00' if i == 0 else stamp(t)} {CHAPTERS[sec]}" for i, (sec, t) in enumerate(first.items())]


def works() -> dict[str, list[str]]:
    """Every work in shots.ts, grouped by artist: '- Title, year · collection'."""
    shots = (ROOT / "src/videos/vg-why/shots.ts").read_text(encoding="utf-8")
    groups = {"Vincent van Gogh": [], "Giotto": []}
    for m in re.finditer(r"^\s*'?([a-z-]+)'?: \{w: \d+, h: \d+, title: \{zh: '([^']+)', en: (['\"])(.+?)\3\}, meta: (['\"])(.+?)\5\}", shots, re.M):
        art, en, meta = m.group(1), m.group(4), m.group(6)
        groups["Giotto" if art == "giotto" else "Vincent van Gogh"].append(f"- {en.replace('Giotto, ', '')}, {meta}")
    return groups


def main() -> None:
    ch, wk = chapters(), works()
    count = sum(len(rows) for rows in wk.values())
    description = "\n".join([
        LEAD, "", "Chapters", *ch, "",
        f"Pictures: every picture is a real work ({count} in all), from public-domain photographs on Wikimedia Commons. "
        f"Each one's source page and licence: {SOURCES_URL}",
        "", "By Vincent van Gogh:", *wk["Vincent van Gogh"], "", "By Giotto:", *wk["Giotto"], "",
        "Letters quoted: vangoghletters.org (Van Gogh Museum / Huygens ING), letters 652, 663, 673, 705 and 729.",
        "The lesson links and the faith reading are Lucas Academy's own.",
        "Music: Human Horizon A (Yancy, made with Suno)",
        "Narration: AI-synthesized voice",
        "", "Lucas Academy", "", hashtags(HASHTAGS),
    ])
    assert len(description) < 5000, f"description is {len(description)} characters; YouTube allows 5,000"
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(f"【标题 / Title】\n{TITLE}\n\n"
                   f"【简介 / Description】（可直接粘贴，约 {len(description)} 字符，YouTube 上限 5000）\n{description}\n\n"
                   f"【标签 / Tags】\n{tags(TAGS)}\n\n{UPLOAD}\n", encoding="utf-8")
    print(f"{OUT.relative_to(ROOT)}: title {len(TITLE)} chars, description {len(description)} chars, "
          f"{len(ch)} chapters, {sum(len(r) for r in wk.values())} works")


if __name__ == "__main__":
    main()
