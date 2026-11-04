"""The project's YouTube tag rule (owner, 2026-10-07; README "YouTube tags").

Every film carries the DEFAULT tags, and every tag is lowercase: in the Studio
tags field and in the hashtag line that ends the description. A film adds a few
topic tags of its own. Both are written as hashtags, `#` + the tag with no spaces
inside, one space between (owner, 2026-11-03: 「关键字用 # 和空格，中间没有空格」).
The description generators import this:

    sys.path.insert(0, str(ROOT / "scripts"))
    from youtube_tags import hashtags, tags
"""
from __future__ import annotations

import re
from collections.abc import Iterable

DEFAULT = ["education", "parenting",   # #christianeducation dropped by the owner 2026-11-03
           "art", "arthistory", "stem",
           "bilingual", "bilingualchildren", "lucas_academy"]
MAX_HASHTAGS = 60      # with more than 60, YouTube ignores every hashtag on the video (Help, answer 6390658)
MAX_TAGS_CHARS = 500   # the Studio tags field


def _key(tag: str) -> str:
    """'Lucas Academy', '#LucasAcademy' and 'lucas_academy' count as the same tag."""
    return re.sub(r"[\s_#-]", "", tag.lower())


def _own(own: Iterable[str]) -> list[str]:
    """The film's own tags as hashtag words ('Erik Satie' -> 'eriksatie'), lowercase, without repeats or
    anything the defaults already cover."""
    seen, out = {_key(t) for t in DEFAULT}, []
    for tag in own:
        t = re.sub(r"[\s-]+", "", tag.strip().lstrip("#").lower())
        if t and _key(t) not in seen:
            seen.add(_key(t))
            out.append(t)
    return out


def tags(own: Iterable[str]) -> str:
    """The Studio tags field: the film's own topic tags first, then the defaults, as '#tag #tag'."""
    line = " ".join(f"#{w}" for w in [*_own(own), *DEFAULT])
    assert len(line) <= MAX_TAGS_CHARS, f"tags are {len(line)} characters; YouTube allows {MAX_TAGS_CHARS}"
    return line


def hashtags(own: Iterable[str] = ()) -> str:
    """The hashtag line that ends a description. The defaults come first, because YouTube shows a
    description's first three hashtags (#education #parenting #art) above the title."""
    words = [*DEFAULT, *_own(own)]
    assert len(words) <= MAX_HASHTAGS, f"{len(words)} hashtags; with more than {MAX_HASHTAGS} YouTube ignores them all"
    return " ".join(f"#{w}" for w in words)
