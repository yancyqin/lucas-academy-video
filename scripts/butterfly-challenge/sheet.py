#!/usr/bin/env python3
"""Results sheet for the current round: pairs/ + experiment/{astra,fable}.json -> results-sheet.jpg.

  sheet.py <round label, e.g. 第七轮>

Each row is one pair with the real side outlined in green, the AI side labelled with its species (·扇翅 when the
spec asked for wing blur), both models' picks and the running score.
"""
import json, os, sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(__file__))
import blind_test as bt  # noqa: E402
import codex_hdphoto as r6  # noqa: E402
import codex_scene as r7  # noqa: E402

D = bt.DATA
NAMES = ["玻璃翼蝶", "蓝摩门凤蝶", "孔雀石蝶", "豹纹蛱蝶", "孔雀蛱蝶", "眼灰蝶", "红斑紫蛱蝶", "美洲黑凤蝶", "红带袖蝶", "鸟翼凤蝶"]
F = "/System/Library/Fonts/Hiragino Sans GB.ttc"  # no ✓/✗ glyphs, so 对/错


def main(label):
    ans = json.load(open(f"{D}/pairs/answers.json"))
    ast = {r["n"]: r for r in json.load(open(f"{D}/experiment/astra.json"))}
    fab = {r["n"]: r for r in json.load(open(f"{D}/experiment/fable.json"))}
    sp = {**r6.specs(), **r7.specs()}  # vNN round 6, wNN round 7; answers.json names the slot
    ainame = {k: s["species"].split(" ")[0] + ("·扇翅" if s["blur"] else "") for k, s in sp.items()}
    f28, f40 = ImageFont.truetype(F, 28), ImageFont.truetype(F, 40)
    W, H, side, pad, head = 560, 315, 330, 12, 70
    im = Image.new("RGB", (2 * W + side + 4 * pad, head + 10 * (H + pad) + pad), (24, 28, 26))
    d = ImageDraw.Draw(im)
    total_a = sum(r["correct"] for r in ast.values()); total_f = sum(r["correct"] for r in fab.values())
    title = (f"Challenge 猜一猜哪些蝴蝶是真的？  和AI比一比   ·   {label}   GPT-6-Astra {total_a}/10   "
             f"Claude Fable 5.2 {total_f}/10")
    size = 28
    while size > 16 and d.textlength(title, font=ImageFont.truetype(F, size)) > im.width - 2 * pad:
        size -= 1  # shrink the header until it fits
    d.text((pad, 18), title, fill="white", font=ImageFont.truetype(F, size))
    green, red, grey = (70, 200, 110), (235, 90, 80), (200, 205, 200)
    sa = sf = 0
    for a in ans:
        n = a["n"]; y = head + (n - 1) * (H + pad)
        for j, s in enumerate("AB"):
            x = pad + j * (W + pad)
            im.paste(Image.open(f"{D}/pairs/{n:02d}-{s}.jpg").resize((W, H)), (x, y))
            real = s == a["real"]
            d.rectangle([x, y, x + W - 1, y + H - 1], outline=green if real else (90, 90, 90), width=6 if real else 1)
            lab = f"{s} · 真" if real else f"{s} · AI {ainame[a['ai']]}"
            d.rectangle([x, y, x + 16 + 26 * len(lab), y + 44], fill=(0, 0, 0))
            d.text((x + 10, y + 6), lab, fill=green if real else grey, font=f28)
        ra, rf = ast[n], fab[n]; sa += ra["correct"]; sf += rf["correct"]
        x = pad * 3 + 2 * W
        d.text((x, y + 6), f"{n}. {NAMES[n - 1]}", fill="white", font=f28)
        d.text((x, y + 70), f"Astra 选 {ra['guess']}  {'对' if ra['correct'] else '错'}", fill=green if ra["correct"] else red, font=f28)
        d.text((x, y + 115), f"Fable 选 {rf['guess']}  {'对' if rf['correct'] else '错'}", fill=green if rf["correct"] else red, font=f28)
        d.text((x, y + 185), f"累计 {sa} : {sf}", fill=grey, font=f40)
    im.save(f"{D}/results-sheet.jpg", quality=86)
    print("sheet", sa, sf)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "")
