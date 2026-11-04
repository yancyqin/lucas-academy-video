"""Each film's second caption track: the Chinese film's English captions (docs/fun-informatics-04/translations.json),
and the English film's Chinese captions (its lines are the Chinese script's, line for line, so zh-draft.md is their
translation), each timed on that film's own lines.

    python3 scripts/fun-informatics-04/captions.py [--lang en]

Each line is split at sentence ends, and at commas where a sentence is still too long, short pieces merged, so a
caption stays within two lines of at most 42 letters, broken evenly between words (a piece still too long is halved
at the space nearest its middle); a line's time is shared among its pieces by length. Chinese pieces stay within 22 characters. Reads public/fun-informatics-04/timeline.<lang>.json, writes
out/fun-informatics-04/delivery/fun-informatics-04.zh.en.srt (or .en.zh-Hans.srt) next to the film's own SRT.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LIMIT = 84  # characters per caption, about two lines on YouTube
OUT = ROOT / "out/fun-informatics-04/delivery"


def split(text: str, marks: str) -> list:
    """Cut after each mark followed by a space, never inside a quotation."""
    parts, cur, inside = [], "", False
    for k, ch in enumerate(text):
        cur += ch
        if ch == '"':
            inside = not inside
        if not inside and ch in marks and (k + 1 == len(text) or text[k + 1] == " "):
            parts.append(cur.strip())
            cur = ""
    if cur.strip():
        parts.append(cur.strip())
    return parts


def halve(text: str) -> list:
    """Cut at the space nearest the middle, again and again until every part fits LIMIT."""
    if len(text) <= LIMIT:
        return [text]
    mid = len(text) // 2
    k = min((i for i, ch in enumerate(text) if ch == " "), key=lambda i: abs(i - mid))
    return halve(text[:k]) + halve(text[k + 1:])


def two_lines(text: str) -> str:
    """A caption over 42 letters goes on two lines, broken at the space nearest the middle."""
    if len(text) <= LIMIT // 2:
        return text
    mid = len(text) // 2
    k = min((i for i, ch in enumerate(text) if ch == " "), key=lambda i: abs(i - mid))
    return text[:k] + "\n" + text[k + 1:]


def pieces(text: str) -> list:
    parts = []
    for sentence in split(text, ".?!;"):
        for part in (split(sentence, ",:") if len(sentence) > LIMIT else [sentence]):
            parts += halve(part)
    out = []
    for part in parts:
        if out and len(out[-1]) + len(part) + 1 <= LIMIT:
            out[-1] += " " + part
        else:
            out.append(part)
    return out


def zh_pieces(text: str, limit: int = 22) -> list:
    """Cut after Chinese punctuation, merge short pieces up to `limit` characters, drop the trailing comma."""
    parts = [p for p in re.split(r"(?<=[，。；：？！、])", text) if p.strip()]
    out = []
    for p in parts:
        if out and len(out[-1]) + len(p) <= limit:
            out[-1] += p
        else:
            out.append(p)
    return [p.rstrip("，。；、") for p in out]


def stamp(s: float) -> str:
    ms = int(round(s * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def main() -> None:
    lang = sys.argv[sys.argv.index("--lang") + 1] if "--lang" in sys.argv else "zh"
    tl = json.loads((ROOT / f"public/fun-informatics-04/timeline.{lang}.json").read_text())
    if lang == "zh":
        other = json.loads((ROOT / "docs/fun-informatics-04/translations.json").read_text())["zh-film-en"]
        cut, show, name = pieces, two_lines, "fun-informatics-04.zh.en.srt"
    else:
        other = {}
        for raw in (ROOT / "docs/fun-informatics-04/zh-draft.md").read_text().splitlines():
            if m := re.match(r"^- (og\d\d-\d\d) \| (.+)$", raw):
                other[m[1]] = re.sub(r"【[^】]*】", "", m[2]).strip()
        cut, show, name = zh_pieces, (lambda p: p), "fun-informatics-04.en.zh-Hans.srt"
    missing = sorted(set(tl["lines"]) - set(other))
    assert not missing, f"no translation for {missing}"
    blocks, n = [], 0
    for lid, cue in sorted(tl["lines"].items(), key=lambda kv: kv[1]["start"]):
        parts = cut(other[lid])
        a, b = cue["start"], cue["end"]
        total = sum(len(p) for p in parts)
        t = a
        for part in parts:
            end = t + (b - a) * len(part) / total
            n += 1
            blocks.append(f"{n}\n{stamp(t)} --> {stamp(end)}\n{show(part)}\n")
            t = end
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text("\n".join(blocks), encoding="utf-8")
    print(f"{n} captions -> {OUT / name}")


if __name__ == "__main__":
    main()
