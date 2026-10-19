"""Timeline, voice mix and captions for one language's film of 「都学了三年，放弃就白学了吗？」 (Education Economics 2).

Two films, one per language (owner, 2026-10-19), each paced to its own voice with episode 1's builder
(scripts/fun-economics-01/build_timeline.py): the same picture, cut to that language's takes. The music bed is
Minuet in G, then Joplin's Solace, then Satie's first Gymnopédie; it dips under every voice and rises in each gap
(scripts/music_ducking.py, the project default). Each film ships its own lines' captions and their translation,
both timed on its own voice.

Picture events hang on words (ANCHORS): Whisper's word time from check.py (word-times.json) when there is one, else
the words' share of the take; markers.<lang>.json ({key: film seconds}) overrides one by hand.

Writes public/fun-economics-02/timeline.<lang>.json, audio/<lang>.wav, <lang>.mix.wav and music-bed.<lang>.wav, and
out/fun-economics-02/delivery/fun-economics-02.<lang>.{zh-Hans,en}.srt. A missing take is stood in for by silence of
an estimated length and the timeline is marked draft.
  python3 scripts/fun-economics-02/build_timeline.py [--lang en] [--srt-only]
"""
import json
import sys

from common import FILM, OUT, PUB, ROOT, VOICES, base

b = base("build_timeline")
wp = b.wp
sys.path.insert(0, str(ROOT / "scripts"))
import music_ducking  # noqa: E402  (README "Music under narration")

assert music_ducking.LINE_LUFS == wp.LINE_LUFS
wp.music_envelope = lambda cues, total, bed_lufs, path: music_ducking.envelope(cues, total, bed_lufs, path)
MUSIC = PUB / "music"
b.PUB, b.DELIVERY, b.FILM_NAME, b.VOICES = PUB, OUT / "delivery", FILM, VOICES
b.BED = [("sc00", MUSIC / "minuet-in-g-musopen.ogg"), ("sc03", MUSIC / "solace-joplin.ogg"), ("sc08", MUSIC / "gymnopedie-1-macleod.ogg")]
b.TITLE = {"zh": "都学了三年，放弃就白学了吗？", "en": "Is Quitting After Three Years a Waste?"}
# Seconds after a line for the picture: a question to think about, the title card, a card to read, the last question.
b.HOLD = {
    "sc00-04": 3.5, "sc01-02": 1.0, "sc02-05": 1.0,
    "sc03-02": 1.0, "sc03-03": 1.5, "sc03-04": 1.5,
    "sc04-02": 1.0, "sc04-03": 1.0, "sc04-04": 1.0,
    "sc05-01": 2.0, "sc05-02": 1.5, "sc05-03": 1.0, "sc05-04": 2.0, "sc05-05": 1.0,
    "sc06-02": 1.0, "sc06-04": 1.0,
    "sc07-01": 1.0, "sc07-02": 1.0, "sc07-04": 2.0,
    "sc08-02": 1.0, "sc08-03": 1.5, "sc08-04": 2.0,
    "sc09-01": 4.0,
}
# key -> (cue, Chinese words, English words), as spoken (digits read as words).
ANCHORS = {
    "sc03-02:ship": ("sc03-02", "就像沉到", "like a ship"),
    "sc03-03:keep": ("sc03-03", "坚持学", "keep learning"),
    "sc03-03:stop": ("sc03-03", "不学了", "stop, and"),
    "sc03-03:level": ("sc03-03", "天平不会", "the scale will not"),
    "sc04-01:wrong": ("sc04-01", "发现前面", "you find a brick"),
    "sc04-02:patch": ("sc04-02", "于是想办法修", "So you try"),
    "sc04-04:second": ("sc04-04", "第二次拼", "the second build"),
    "sc05-01:problem": ("sc05-01", "一盒铅笔", "a box holds"),
    "sc05-01:boxes": ("sc05-01", "七盒", "and seven boxes"),
    "sc05-01:kids": ("sc05-01", "十四个同学", "fourteen classmates"),
    "sc05-01:ask": ("sc05-01", "每人分到", "How many"),
    "sc05-02:plus": ("sc05-02", "七加八", "seven plus eight"),
    "sc05-02:fifteen": ("sc05-02", "十五支分给", "Fifteen pencils"),
    "sc05-02:left": ("sc05-02", "还剩一支", "with one left"),
    "sc05-02:cut": ("sc05-02", "难道", "Should she"),
    "sc05-03:mess": ("sc05-03", "接着算", "so she keeps"),
    "sc05-04:boxes": ("sc05-04", "七盒", "seven boxes"),
    "sc05-04:times": ("sc05-04", "是七乘八", "is seven times"),
    "sc05-04:share": ("sc05-04", "五十六支分给", "Fifty-six pencils for"),
    "sc05-04:four": ("sc05-04", "每人四支", "four each"),
    "sc05-05:look": ("sc05-05", "还是看前面", "Look forward"),
    "sc06-02:apart": ("sc06-02", "看着自己", "and people who watch"),
    "sc06-04:not-yet": ("sc06-04", "只是它管的", "But it's about"),
    "sc06-04:sunk": ("sc06-04", "已经沉下去的", "it has no say"),
    "sc07-04:future": ("sc07-04", "将来", "the future"),
    "sc07-04:now": ("sc07-04", "能选的", "all we can choose"),
    "sc07-04:cherish": ("sc07-04", "珍惜当下", "Making the most"),
    "sc09-01:or": ("sc09-01", "或者你想", "or you want"),
    "sc09-01:road": ("sc09-01", "让你留下来的", "is it the path"),
}


def share(text: str, words: str, lang: str) -> float:
    """Where the words start, as a share of the line: a Latin letter in Chinese weighs half a character."""
    def weight(s: str) -> float:
        return sum(0.5 if lang == "zh" and ch.isascii() else 1.0 for ch in s if not ch.isspace())
    return weight(text[:text.index(words)]) / weight(text)


def add_markers(lang: str) -> None:
    """Film seconds of each marked word in this language's timeline."""
    path = PUB / f"timeline.{lang}.json"
    tl = json.loads(path.read_text())
    spoken = {c["id"]: c["spoken"] for c in json.loads((PUB / f"narration/cues.{lang}.json").read_text())}
    heard = json.loads((PUB / "word-times.json").read_text()) if (PUB / "word-times.json").exists() else {}
    cues = {c["id"]: c for c in tl["cues"]}
    marks = {}
    for key, (cid, zh, en) in ANCHORS.items():
        s = cues[cid]["speech"]
        into = heard.get(key, {}).get(lang)
        if into is None:
            into = share(spoken[cid], zh if lang == "zh" else en, lang) * (s["end"] - s["start"])
        marks[key] = round(s["start"] + into, 3)
    hand = PUB / f"markers.{lang}.json"
    if hand.exists():
        marks.update(json.loads(hand.read_text()))
    tl["markers"] = marks
    path.write_text(json.dumps(tl, ensure_ascii=False, indent=1) + "\n")


if __name__ == "__main__":
    lang = sys.argv[sys.argv.index("--lang") + 1] if "--lang" in sys.argv else "zh"
    if "--srt-only" in sys.argv:
        b.write_srt(json.loads((PUB / f"timeline.{lang}.json").read_text())["cues"], lang)
    else:
        b.build(lang)
        add_markers(lang)
