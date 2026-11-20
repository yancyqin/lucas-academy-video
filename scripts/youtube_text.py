"""The upload text for every film (owner, 2026-11-20: 「要带tags」「简介最开始就是分章节」; README "YouTube tags").

    sys.path.insert(0, str(ROOT / "scripts"))
    from youtube_text import upload_text
    text = upload_text(title=..., chapters=[(0, "开场"), (45.2, "…")], duration=film_seconds,
                       body=[intro, sources, credits, byline], own_tags=[...], more_tags=[...],
                       settings=[...], lang="zh")

The description STARTS with the chapters (first `0:00`, at least three, each at least 10 s — YouTube's rules),
then the film's own text, and ENDS with the hashtag line (defaults first). 【标签】 is always there, written
`#tag #tag`. `scripts/qa/qa.py upload` checks a finished folder against the same rules.
"""
from __future__ import annotations

from collections.abc import Iterable, Sequence

from youtube_tags import hashtags, tags

MIN_CHAPTER = 10.0
MAX_DESCRIPTION = 5000


def stamp(seconds: float) -> str:
    s = int(seconds)
    h, rest = divmod(s, 3600)
    return f"{h}:{rest // 60:02d}:{rest % 60:02d}" if h else f"{rest // 60}:{rest % 60:02d}"


def chapter_lines(chapters: Sequence[tuple[float, str]], duration: float | None = None) -> str:
    """'0:00 name' lines. The first chapter is forced to 0:00; a chapter shorter than 10 s is an error, not
    silently dropped, so the film's chapter list gets fixed where it is made."""
    rows = sorted((max(0.0, float(t)), n.strip()) for t, n in chapters)
    if not rows:
        raise ValueError("a film needs chapters (YouTube: at least three, the first at 0:00)")
    rows[0] = (0.0, rows[0][1])
    if len(rows) < 3:
        raise ValueError(f"only {len(rows)} chapters; YouTube needs at least three")
    for (a, n1), (b, n2) in zip(rows, rows[1:]):
        if b - a < MIN_CHAPTER:
            raise ValueError(f"chapter 「{n1}」 is {b - a:.1f} s long; YouTube needs at least {MIN_CHAPTER:.0f} s")
    if duration is not None and duration - rows[-1][0] < MIN_CHAPTER:
        raise ValueError(f"the last chapter 「{rows[-1][1]}」 starts {duration - rows[-1][0]:.1f} s before the end")
    if any(not n for _, n in rows):
        raise ValueError("every chapter needs a name")
    return "\n".join(f"{stamp(t)} {n}" for t, n in rows)


def description(chapters, duration, body: Iterable[str], own_tags: Iterable[str]) -> str:
    parts = [chapter_lines(chapters, duration), *[b.strip() for b in body if b and b.strip()], hashtags(own_tags)]
    text = "\n\n".join(parts)
    if "<" in text or ">" in text:
        raise ValueError("YouTube does not accept < or > in a description")
    if len(text) > MAX_DESCRIPTION:
        raise ValueError(f"the description is {len(text)} characters; YouTube allows {MAX_DESCRIPTION}")
    return text


def upload_text(*, title: str, chapters, duration: float | None, body: Iterable[str], own_tags: Iterable[str],
                more_tags: Iterable[str] = (), settings: Iterable[str] = (), lang: str = "zh") -> str:
    if not 0 < len(title) <= 100:
        raise ValueError(f"the title is {len(title)} characters; YouTube allows 100")
    own_tags = list(own_tags)
    desc = description(chapters, duration, body, own_tags)
    count = (f"（可直接粘贴，约 {len(desc)} 字符，YouTube 上限 5000）" if lang == "zh"
             else f"(paste as is, about {len(desc)} characters; YouTube allows 5000)")
    return f"""【标题 / Title】
{title}

【简介 / Description】{count}
{desc}

【标签 / Tags】
{tags([*own_tags, *more_tags])}

【上传设置 / Upload settings】
{chr(10).join(f"· {s}" for s in settings)}
"""
