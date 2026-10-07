"""Narration scripts for 「计算机怎么算 1+1=？」 (FUN-INFORMATICS-01.md), from the two edit files.

docs/fun-informatics-01/{zh,en}-edit.md are the source of truth: one line per cue, the same ids in
both, `<strong>` for emphasis, one film-wide `整体语气` / `Overall tone`. This writes
public/fun-informatics-01/narration/{zh,en}.json in lucas-narrate's line format (what the voice
READS: digits and binary spelled out, ASCII respelled) and cues.json (what the captions SHOW).

  python3 scripts/fun-informatics-01/narration.py
  cd ../lucas-academy-media && .conda/bin/lucas-narrate <repo>/public/fun-informatics-01/narration/zh.json \\
      --profile louise/zh --language zh --speed 1.0 --output-dir outputs/louise/zh/fun-informatics-01
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "docs/fun-informatics-01"
OUT = ROOT / "public/fun-informatics-01/narration"
VOICE = {"zh": "louise/zh", "en": "louise/en"}
MODE = "zero-shot-instruct"

SECTION = re.compile(r"^## (IT\d\d)\b")
OVERALL = re.compile(r"^(整体语气|Overall tone|整体语速|Overall speed):\s*(.*)$")
LINE = re.compile(r"^- (it\d\d-\d\d) \| (.+)$")

# What the voice reads where it differs from the caption. Every line with a digit is spelled out here,
# so the speech model never has to guess whether "10" is ten or one-zero.
SPOKEN = {
    "zh": {
        "it00-01": "计算机怎么算一加一？在回答这个问题之前，我们先问另一个问题。",
        "it01-01": "我们先回到最开始的问题：计算机怎么算<strong>一加一</strong>？",
        "it01-02": "你可能会说，这还用算？当然是二。",
        "it01-03": "可是你打开一台计算机，往里面看：<strong>没有</strong>数字。没有一，也没有二。",
        "it01-05": "就靠这些开关，它算出了一加一，也画出了刚才那段放不完的图像。",
        "it02-03": "我们给这两种样子起个名字，写成<strong>零</strong>和<strong>一</strong>。",
        "it03-01": "可是，只有零和一，怎么数数呢？",
        "it03-02": "我们平时有十个数字。九再加一，就要<strong>进位</strong>，写成十。",
        "it03-03": "计算机只有两个数字。它的每一个位置，就像前面那个开关，只有开、关两种样子，只能是零或一，最大就是一。所以一再加一，也要进位，写下来是一个一、一个零，读作一零，不是十哦。",
        "it03-04": "看墙上：零零零零是零。",
        "it03-05": "零零零一是一。",
        "it03-06": "再加一，要进位，就是零零一零，也就是二。",
        "it03-07": "零零一零再加一，就是零零一一，也就是三。",
        "it03-08": "再加一，连着进两位，就是零一零零，也就是四。",
        "it04-01": "那开关自己，是怎么算出一加一的呢？",
        "it04-05": "试试看。关、关：两盏灯都不亮，零加零等于零。",
        "it04-06": "开、关：和灯亮了，零加一等于一。",
        "it04-07": "开、开：和灯灭，进位灯亮。把两盏灯连起来读，进位是一，和是零，就是<strong>一零</strong>。",  # spliced: the first sentence is v1 it07-06 (0–3.8 s), the second voiced alone; whole, 进 came out as 静 in 13 takes
        "it04-08": "所以在计算机里，一加一不写成二，而是写成一个一、一个零，读作<strong>一零</strong>。",
        "it04-09": "就这样一直加一，加到第六十五次，八个开关排成了零一零零零零零一，它就是六十五。",
        "it05-01": "六十五有什么特别的<strong>意思</strong>呢？",
        "it05-02": "数字自己，不会说自己是干什么用的，六十五并没有什么特别的意思。",
        "it05-03": "但是，很久以前，人们约定了一张表，叫<strong>阿斯克码</strong>：在这张表里，六十五就代表大写字母 A。",
        "it06-01": "很多零和一在一起，除了字母，还能变成什么？换一面墙看看。这面墙上的小零件叫<strong>像素</strong>：屏幕上的一个点，也是屏幕上<strong>最小</strong>的一块。",
        "it06-02": "一个像素，两个，三个。三十六个小方块排成八行，是一个三角形。",
        "it06-03": "现在，两千三百零九个彩色的点，各飞各的。你能看出这是什么吗？",
        "it06-04": "它们洛下来了，洛到从一张星系照片里取出的位置上。",  # 洛 so the voice reads luò (it read 落 as là)
        "it06-09": "再看：一千二百六十个像素，挤在一起是一个<strong>点</strong>；排成一行是一条<strong>线</strong>；铺开，是一个<strong>面</strong>。",
        "it07-07": "怎么算的？没有魔法，也没有谁躲在里面算。还是那个一加一：电按规则，流过开关。",
        "it07-10": "刚才那幅放不完的图，每一个像素的颜色，都是这样一次次一加一算出来的。",
        "it08-03": "现在，再看这一串：零一零零零零零一。还是它。",
        "it08-04": "它可以是<strong>六十五</strong>，可以是<strong>A</strong>，可以是一个像素，一小段声音，或者一个动作。",
        "it08-05": "同一串零和一，<strong>五种意思</strong>。它一次都没变，变的只是规则。",
        "it10-01": "一九四八年，一个叫<strong>克劳德·香农</strong>的科学家，想出了一把量信息的尺子：要知道一件事，得<strong>问几个问题</strong>。",
        "it10-02": "玩个游戏。我心里想了一到八里的一个数，你只能问“是不是”的问题。",
        "it10-03": "“比四大吗？”“比六大吗？”“是七吗？”三个问题，一定能猜到。",
        "it10-04": "香农说：这个数里装的信息，就是三个问题，叫<strong>三比特</strong>。一个问题，就是一个比特。",
        "it10-05": "要是答案你早就知道呢？比如一枚两面都是正面的硬币，抛出去不用猜，一个问题都不用问，信息就是零。<strong>能猜到的事，不算信息。</strong>",
        "it10-07": "剩下的格子，规则替我们算出来，不用问。所以棋盘再大，一步也最多<strong>两比特</strong>。",
        "it10-08": "五子棋每一步，一百多个点，“落在哪儿？”大约七个问题。五十五步，几百个问题。一整盘棋，就装在这几百个比特里。",
        "it10-10": "房间中央这座耶稣降生像不一样：它是<strong>梁</strong>出来的。两万个三角形，每一个在哪儿都得问，几百万个问题。没有公式能替你省掉。",  # 梁 so the voice reads liáng (it read 量 as liàng)
        "it11-01": "现在，回到我们的两个问题。计算机怎么算一加一？它用两个开关，算出了一零。",
        "it11-02": "计算机的图像能无限放大吗？不能。图有最小单元。无限的感觉，来自一条规则，和几十亿次一加一。",
    },
    "en": {
        "it00-01": "How does a computer add one plus one? Before we answer that, let's ask a different question first.",
        "it01-01": "Let's go back to the first question: how does a computer add <strong>one plus one</strong>?",
        "it01-02": "You might say: that's easy. It's two.",
        "it01-03": "But open a computer and look inside. <strong>No numbers</strong>. No one, and no two.",
        "it01-05": "With nothing but these switches, it adds one plus one, and it draws that picture that never ran out.",
        "it02-03": "We give those two ways names, and write them <strong>zero</strong> and <strong>one</strong>.",
        "it03-01": "But with only zero and one, how do you count?",
        "it03-02": "We usually have ten digits. Add one to nine, and you have to <strong>carry</strong>: you write ten.",
        "it03-03": "A computer has only two digits. Each place in it is like that switch: only on or off, only zero or one. The biggest digit is one. So add one to one, and it has to carry too: it writes one, zero. Not ten!",
        "it03-04": "Watch the wall: zero zero zero zero is zero.",
        "it03-05": "Zero zero zero one is one.",
        "it03-06": "Add one, carry, and it's zero zero one zero. That's two.",
        "it03-07": "Zero zero one zero plus one is zero zero one one. That's three.",
        "it03-08": "Add one more, carry twice, and it's zero one zero zero. That's four.",
        "it04-01": "So how do the switches themselves add one plus one?",
        "it04-05": "Let's try. Off, off: no lamp lights. Zero plus zero is zero.",
        "it04-06": "On, off: the SUM lamp lights. Zero plus one is one.",
        "it04-07": "On, on: SUM goes dark, CARRY lights. Read the two lamps together, CARRY then SUM, and you get <strong>one, zero</strong>.",
        "it04-08": "So inside a computer, one plus one is not written two. It's written <strong>one, zero</strong>.",
        "it04-09": "Keep adding one, sixty-five times, and eight switches read zero one zero zero zero zero zero one. That is sixty-five.",
        "it05-01": "Does sixty-five <strong>mean</strong> anything special?",
        "it05-02": "A number doesn't tell you what it's for. On its own, sixty-five means nothing special.",
        "it05-03": "But long ago, people agreed on a table called <strong>Askey</strong>. In that table, sixty-five stands for the capital letter A.",
        "it06-01": "Many zeros and ones together: besides letters, what else can they become? Let's look at another wall. Its tiny pieces are called <strong>pixels</strong>: one dot on a screen, and the <strong>smallest</strong> piece a screen has.",
        "it06-03": "Now two thousand three hundred and nine coloured dots fly around on their own. Can you tell what this is?",
        "it06-09": "Look again: twelve hundred and sixty pixels crowded together are a <strong>point</strong>. In a row, a <strong>line</strong>. Spread out, a <strong>plane</strong>.",
        "it07-07": "How is it computed? No magic, and nobody hiding inside. It's still that one plus one: electricity, following a rule, through switches.",
        "it07-10": "That picture that never ran out: the colour of every pixel was computed this way, one plus one, over and over.",
        "it08-03": "Now look at this string again: zero one zero zero zero zero zero one. The same one.",
        "it08-04": "It can be <strong>sixty-five</strong>. It can be <strong>A</strong>. It can be a pixel, a slice of sound, or a move.",
        "it08-05": "One string of zeros and ones, <strong>five meanings</strong>. It never changed once. Only the rule did.",
        "it10-01": "In nineteen forty-eight, a scientist named <strong>Claude Shannon</strong> found a ruler for measuring information: to learn something, <strong>how many questions</strong> do you have to ask?",
        "it10-02": "Let's play. I'm thinking of a number from one to eight, and you may only ask yes-or-no questions.",
        "it10-03": "“Is it bigger than four?” “Bigger than six?” “Is it seven?” Three questions, and you're sure to get it.",
        "it10-04": "Shannon said: the information in that number is three questions. Call it <strong>three bits</strong>. One question is one bit.",
        "it10-05": "And if you already know the answer? Toss a coin with heads on both sides: no need to guess, no question to ask. The information is zero. <strong>What you can guess doesn't count.</strong>",
        "it10-07": "Every other square, the rules work out for us. No questions needed. So however big the board, one step is at most <strong>two bits</strong>.",
        "it10-08": "In Gomoku, each move has over a hundred spots to choose from. “Where did it go?” About seven questions. Fifty-five moves: a few hundred questions. A whole game fits in those few hundred bits.",
        "it11-01": "Now, back to our two questions. How does a computer add one plus one? With two switches, it got one, zero.",
        "it11-02": "Can a computer picture be zoomed in forever? No. A picture has a smallest unit. The feeling of infinity comes from one rule, and billions of one-plus-ones.",
    },
}


def parse(path: Path):
    cues, tone = {}, ""
    section = None
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if m := OVERALL.match(line):
            if m.group(1) in ("整体语气", "Overall tone"):
                tone = m.group(2).strip()
        elif m := SECTION.match(line):
            section = m.group(1).lower()
        elif m := LINE.match(line):
            cid, text = m.groups()
            assert cid.startswith(section), f"{cid} not under {section}"
            cues[cid] = {"section": section, "text": text.split(" | ")[0].strip()}
    return cues, tone


def plain(text: str) -> str:
    return re.sub(r"</?strong>", "", text)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    zh, zh_tone = parse(SRC / "zh-edit.md")
    en, en_tone = parse(SRC / "en-edit.md")
    assert list(zh) == list(en), "zh and en must have the same cue ids in the same order"
    for lang, cues, tone in (("zh", zh, zh_tone), ("en", en, en_tone)):
        missing = [cid for cid, cue in cues.items() if re.search(r"\d", plain(cue["text"])) and cid not in SPOKEN[lang]]
        assert not missing, f"{lang}: lines with digits need a SPOKEN form: {missing}"
        lines = [{"id": cid, "text": SPOKEN[lang].get(cid, cue["text"]), "instruct": tone, "mode": MODE, "speed": 1.0}
                 for cid, cue in cues.items()]
        json.dump({"voice": VOICE[lang], "language": lang, "lines": lines},
                  open(OUT / f"{lang}.json", "w"), ensure_ascii=False, indent=1)
    cues = [{"id": cid, "section": zh[cid]["section"], "zh": plain(zh[cid]["text"]), "en": plain(en[cid]["text"])} for cid in zh]
    json.dump(cues, open(OUT / "cues.json", "w"), ensure_ascii=False, indent=1)
    print(f"{len(cues)} cues -> {OUT}")


if __name__ == "__main__":
    main()
