"""The project's YouTube tag rule (owner, 2026-10-07; README "YouTube tags").

Every film carries the DEFAULT tags, and every tag is lowercase: in the Studio
tags field and in the hashtag line that ends the description. A film adds a few
topic tags of its own. The description generators import this:

    sys.path.insert(0, str(ROOT / "scripts"))
    from youtube_tags import hashtags, tags
"""
from __future__ import annotations

import re
from collections.abc import Iterable

DEFAULT = ["education", "christianeducation", "parenting",
           "art", "arthistory", "stem",
           "bilingual", "bilingualchildren", "lucas_academy"]
MAX_HASHTAGS = 15      # with more than 15, YouTube ignores every hashtag on the video
MAX_TAGS_CHARS = 500   # the Studio tags field


def _key(tag: str) -> str:
    """'Lucas Academy', '#LucasAcademy' and 'lucas_academy' count as the same tag."""
    return re.sub(r"[\s_#-]", "", tag.lower())


def _own(own: Iterable[str]) -> list[str]:
    """The film's own tags, lowercase, without repeats or anything the defaults already cover."""
    seen, out = {_key(t) for t in DEFAULT}, []
    for tag in own:
        t = tag.strip().lstrip("#").strip().lower()
        if t and _key(t) not in seen:
            seen.add(_key(t))
            out.append(t)
    return out


def tags(own: Iterable[str]) -> str:
    """The Studio tags field: the film's own topic tags first, then the defaults."""
    line = ", ".join([*_own(own), *DEFAULT])
    assert len(line) <= MAX_TAGS_CHARS, f"tags are {len(line)} characters; YouTube allows {MAX_TAGS_CHARS}"
    return line


def hashtags(own: Iterable[str] = ()) -> str:
    """The hashtag line that ends a description. The defaults come first, because YouTube shows a
    description's first three hashtags (#education #christianeducation #parenting) above the title."""
    words = [*DEFAULT, *(re.sub(r"[\s-]+", "", t) for t in _own(own))]
    assert len(words) <= MAX_HASHTAGS, f"{len(words)} hashtags; with more than {MAX_HASHTAGS} YouTube ignores them all"
    return " ".join(f"#{w}" for w in words)
