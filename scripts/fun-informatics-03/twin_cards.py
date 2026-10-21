"""Print the twin-card Pictionary sheets filmed for Fun Informatics 3.

    python3 scripts/fun-informatics-03/twin_cards.py [--a4]

Writes out/fun-informatics-03/twin-cards.pdf (and the .html beside it): one
bilingual set of four pages -- the rules, a page of round-1 cards, a page of
twin cards, and a score sheet with the answers. Each card page holds the four
Chinese cards above the four English ones, so the Chinese and the English film
are both played from one printout.

Every word comes from docs/fun-informatics-03/twin-cards.json, so the cards,
the answers and the plan's word list cannot drift apart.

Rendered by headless Chrome rather than reportlab because Chrome finds PingFang
SC on its own, and a card grid is easier to lay out in CSS. US Letter by default
(printed at home); --a4 switches the page size.
"""
import html
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "docs/fun-informatics-03/twin-cards.json"
OUT = ROOT / "out/fun-informatics-03"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

ROUND1 = "#0f766e"   # teal
ROUND2 = "#c2410c"   # orange
INK = "#1f2937"
MUTED = "#6b7280"
CUT = "#9ca3af"

FONT = {
    "zh": '"PingFang SC", "Hiragino Sans GB", sans-serif',
    "en": '"Avenir Next", "Helvetica Neue", Arial, sans-serif',
}

T = {
    "zh": {
        "title": "双胞胎你画我猜",
        "need": "准备：一支笔、一叠白纸、一枚硬币、一个计时器（手机就行）。沿虚线把卡片剪开，蓝绿色是第一轮，橙色是第二轮。",
        "always": "每一轮都一样：画的人不能说话、不能写字、不能比划，只能画。",
        "r1": "第一轮 · 自由画",
        "r1_steps": [
            "画的人抽一张蓝绿色的卡，自己看，别给别人看。",
            "画 30 秒。猜的人随便猜，想喊几次就喊几次。30 秒内猜中，得 1 分。",
        ],
        "r2": "第二轮 · 双胞胎",
        "r2_steps": [
            "画的人抽一张橙色的卡，放在桌子中间：两个词，大家都看得见。",
            "画的人偷偷抛硬币：正面画左边，反面画右边。",
            "画 15 秒。时间到了，猜的人才能开口，而且只能猜一次。猜中得 1 分。",
        ],
        "think": "玩完想一想：第二轮里，什么样的画，一猜就中？（答案在最后一页，玩完再看）",
        "or": "还是",
        "heads": "正面",
        "tails": "反面",
        "score_r1": ["#", "画的人", "词", "猜中了吗？"],
        "score_r2": ["#", "画的人", "双胞胎", "画的是", "一次猜中？"],
        "total": "猜中：＿＿＿ / 4",
        "answers": "答案：它们哪里不一样？",
        "answers_cols": ["双胞胎", "左边才有", "右边才有"],
    },
    "en": {
        "title": "Twin-Card Pictionary",
        "need": "You need: a pencil, blank paper, a coin, and a timer (a phone works). Cut the cards along the dashed lines. Teal cards are round one, orange cards are round two.",
        "always": "In every round: the person drawing can’t talk, write, or act it out. Only draw.",
        "r1": "Round 1 · Free draw",
        "r1_steps": [
            "The drawer takes a teal card and keeps it secret.",
            "Draw for 30 seconds. Guessers shout as many guesses as they like. Guessed within 30 seconds: 1 point.",
        ],
        "r2": "Round 2 · Twins",
        "r2_steps": [
            "The drawer puts an orange card in the middle of the table, so everyone sees both words.",
            "The drawer flips the coin in secret: heads, draw the left one; tails, the right one.",
            "Draw for 15 seconds. Guessers stay quiet until time is up, then get one guess. Right: 1 point.",
        ],
        "think": "After you play, think about it: in round two, which drawings were guessed right away? (Answers on the last page.)",
        "or": "or",
        "heads": "HEADS",
        "tails": "TAILS",
        "score_r1": ["#", "Drawer", "Word", "Guessed?"],
        "score_r2": ["#", "Drawer", "Twins", "Drew", "1st guess?"],
        "total": "Guessed: _____ / 4",
        "answers": "Answers: what tells them apart?",
        "answers_cols": ["Twins", "Only the left has", "Only the right has"],
    },
}


def esc(s):
    return html.escape(s, quote=False)


def word_size(lang, n, twin):
    """Font size (pt) for a card word of n characters, so the longest still fits.

    Both words on a twin card share one size, set by the longer of the two.
    """
    if lang == "zh":
        if twin:
            return 40 if n <= 2 else 30
        return 64 if n <= 2 else 54
    if twin:
        return 28 if n <= 4 else 24 if n <= 6 else 20 if n <= 8 else 16
    return 40 if n <= 6 else 34 if n <= 9 else 28


def free_card(lang, word):
    t = T[lang]
    return f"""
<div class="card {lang}"><div class="inner" style="--c:{ROUND1}">
  <div class="tag">{esc(t['r1'])}</div>
  <div class="word" style="font-size:{word_size(lang, len(word), False)}pt">{esc(word)}</div>
</div></div>"""


def twin_card(lang, pair):
    t = T[lang]
    a, b = pair
    size = word_size(lang, max(len(a), len(b)), True)
    return f"""
<div class="card {lang}"><div class="inner" style="--c:{ROUND2}">
  <div class="tag">{esc(t['r2'])}</div>
  <div class="twins">
    <div class="half"><div class="w" style="font-size:{size}pt">{esc(a)}</div><div class="coin">{esc(t['heads'])}</div></div>
    <div class="or">{esc(t['or'])}</div>
    <div class="half"><div class="w" style="font-size:{size}pt">{esc(b)}</div><div class="coin">{esc(t['tails'])}</div></div>
  </div>
</div></div>"""


def card_page(cards, colour, label):
    return f"""
<section class="page cards">
  <div class="cutnote"><span style="color:{colour}">{esc(label)}</span> · 沿虚线剪开 / Cut along the dashed lines ✂</div>
  <div class="grid">{''.join(cards)}</div>
</section>"""


def rules_block(lang):
    t = T[lang]
    r1 = "".join(f"<li>{esc(s)}</li>" for s in t["r1_steps"])
    r2 = "".join(f"<li>{esc(s)}</li>" for s in t["r2_steps"])
    return f"""
<div class="rules {lang}">
  <h1>{esc(t['title'])}</h1>
  <p class="lead">{esc(t['need'])}</p>
  <p class="lead strong">{esc(t['always'])}</p>
  <div class="box" style="--c:{ROUND1}"><h2>{esc(t['r1'])}</h2><ol>{r1}</ol></div>
  <div class="box" style="--c:{ROUND2}"><h2>{esc(t['r2'])}</h2><ol>{r2}</ol></div>
  <div class="think">{esc(t['think'])}</div>
</div>"""


def table(cols, rows, colour):
    head = "".join(f"<th>{esc(c)}</th>" for c in cols)
    body = "".join(f"<tr>{''.join(f'<td>{esc(c)}</td>' for c in r)}</tr>" for r in rows)
    return f'<table style="--c:{colour}"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>'


def score_block(lang, pairs):
    t = T[lang]
    blank1 = [[str(i)] + [""] * (len(t["score_r1"]) - 1) for i in range(1, 5)]
    blank2 = [[str(i)] + [""] * (len(t["score_r2"]) - 1) for i in range(1, 5)]
    answers = [[f"{p[lang][0]} / {p[lang][1]}", *p[lang + "_hint"]] for p in pairs]
    return f"""
<div class="score {lang}">
  <h2 style="color:{ROUND1}">{esc(t['r1'])}</h2>
  {table(t['score_r1'], blank1, ROUND1)}
  <div class="total">{esc(t['total'])}</div>
  <h2 style="color:{ROUND2}">{esc(t['r2'])}</h2>
  {table(t['score_r2'], blank2, ROUND2)}
  <div class="total">{esc(t['total'])}</div>
  <h2 class="ans">{esc(t['answers'])}</h2>
  {table(t['answers_cols'], answers, INK)}
</div>"""


def build_html(data, page_size):
    pairs = data["pairs"]
    free = [free_card(lang, w) for lang in ("zh", "en") for w in data["free"][lang]]
    twins = [twin_card(lang, p[lang]) for lang in ("zh", "en") for p in pairs]
    if len(free) != 8 or len(twins) != 8:
        sys.exit(f"each card page holds 4 Chinese + 4 English cards; got {len(free)} round-1 and {len(twins)} twin cards")
    pages = [
        f'<section class="page">{rules_block("zh")}<hr>{rules_block("en")}</section>',
        card_page(free, ROUND1, "第一轮 · 自由画 / Round 1 · Free draw"),
        card_page(twins, ROUND2, "第二轮 · 双胞胎 / Round 2 · Twins"),
        f'<section class="page"><h1 class="sheet">记分表 · Score sheet</h1>'
        f'<div class="cols">{score_block("zh", pairs)}{score_block("en", pairs)}</div></section>',
    ]
    w, h = ("8.5in", "11in") if page_size == "letter" else ("210mm", "297mm")
    return f"""<!doctype html>
<html lang="zh-Hans"><head><meta charset="utf-8">
<title>双胞胎你画我猜 · Twin-Card Pictionary</title>
<style>
@page {{ size: {page_size}; margin: 0; }}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
html {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
body {{ font-family: {FONT['en']}, {FONT['zh']}; color: {INK}; }}
.zh {{ font-family: {FONT['zh']}; }}
.en {{ font-family: {FONT['en']}; }}
.page {{ width: {w}; height: {h}; padding: 0.5in; page-break-after: always; position: relative; overflow: hidden; }}
.page:last-child {{ page-break-after: auto; }}

.cards .cutnote {{ position: absolute; top: 0.18in; left: 0.5in; font-size: 9pt; color: {MUTED}; font-weight: 600; }}
.grid {{ display: grid; grid-template-columns: 1fr 1fr; grid-template-rows: repeat(4, 1fr); height: 100%;
         border-top: 1px dashed {CUT}; border-left: 1px dashed {CUT}; }}
.card {{ border-right: 1px dashed {CUT}; border-bottom: 1px dashed {CUT}; padding: 0.13in; display: flex; }}
.inner {{ flex: 1; border: 2.5px solid var(--c); border-radius: 14px; display: flex; flex-direction: column;
          align-items: center; padding: 0.08in 0.1in 0.12in; }}
.tag {{ align-self: stretch; text-align: center; font-size: 9.5pt; font-weight: 700; letter-spacing: 0.04em;
        color: #fff; background: var(--c); border-radius: 8px; padding: 2px 0; }}
.word {{ flex: 1; display: flex; align-items: center; justify-content: center; text-align: center;
         font-weight: 700; line-height: 1.05; }}
.twins {{ flex: 1; display: flex; align-items: center; justify-content: space-between; width: 100%; }}
.half {{ flex: 1; min-width: 0; display: flex; flex-direction: column; align-items: center; gap: 6px; text-align: center; }}
.half .w {{ height: 0.62in; display: flex; align-items: center; justify-content: center; font-weight: 700; line-height: 1.05; }}
.coin {{ font-size: 7.5pt; font-weight: 700; color: var(--c); border: 1.5px solid var(--c); border-radius: 999px; padding: 1px 8px; }}
.or {{ flex: none; width: 0.42in; text-align: center; font-size: 10pt; color: {MUTED}; margin-bottom: 22px; }}

.rules h1 {{ font-size: 20pt; margin-bottom: 6px; }}
.rules .lead {{ font-size: 10.5pt; line-height: 1.5; margin-bottom: 4px; }}
.rules .strong {{ font-weight: 700; }}
.box {{ border: 2px solid var(--c); border-radius: 12px; padding: 2px 16px 8px; margin: 8px 0; }}
.box h2 {{ color: var(--c); font-size: 12.5pt; margin: 6px 0 2px; }}
.box ol {{ padding-left: 1.3em; font-size: 10.5pt; line-height: 1.6; }}
.think {{ background: #fef3c7; border-radius: 10px; padding: 8px 14px; font-size: 10.5pt; font-weight: 700; margin-top: 8px; }}
hr {{ border: none; border-top: 1px dashed {CUT}; margin: 0.22in 0; }}

h1.sheet {{ font-size: 20pt; margin-bottom: 10px; }}
.cols {{ display: grid; grid-template-columns: 1fr 1fr; gap: 0.3in; }}
.score h2 {{ font-size: 12pt; margin: 10px 0 5px; }}
.score h2.ans {{ margin-top: 22px; }}
table {{ border-collapse: collapse; width: 100%; }}
th {{ background: var(--c); color: #fff; font-size: 9pt; padding: 4px 6px; text-align: left; }}
td {{ border: 1px solid #d1d5db; height: 0.34in; font-size: 9pt; padding: 3px 6px; }}
.score td:first-child {{ width: 0.3in; text-align: center; color: {MUTED}; }}
.score h2.ans + table td {{ height: auto; padding: 6px; }}
.score h2.ans + table td:first-child {{ width: auto; text-align: left; color: {INK}; font-weight: 700; white-space: nowrap; }}
.total {{ text-align: right; font-size: 10.5pt; font-weight: 700; margin-top: 4px; }}
</style></head><body>
{''.join(pages)}
</body></html>"""


def main():
    page_size = "a4" if "--a4" in sys.argv[1:] else "letter"
    data = json.loads(DATA.read_text(encoding="utf-8"))
    OUT.mkdir(parents=True, exist_ok=True)
    suffix = ".a4" if page_size == "a4" else ""
    page = OUT / f"twin-cards{suffix}.html"
    pdf = OUT / f"twin-cards{suffix}.pdf"
    page.write_text(build_html(data, page_size), encoding="utf-8")
    # A throwaway profile, so a Chrome the user already has open does not lock us out.
    with tempfile.TemporaryDirectory() as profile:
        subprocess.run(
            [CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
             f"--user-data-dir={profile}", f"--print-to-pdf={pdf}", page.as_uri()],
            check=True, capture_output=True)
    print(pdf)


if __name__ == "__main__":
    main()
