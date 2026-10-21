#!/usr/bin/env python3
"""Draw the film arrangement (film.json) as one sheet: a row per piece with its paintings in order.
Tags: 需 Codex = needs a reconstruction, 画溶画 = painting-to-painting dissolve, 动 = planned MiniMax animation.
usage: python3 arrangement_sheet.py [out.jpg]     (needs Pillow; /usr/bin/python3 has it)
"""
import json, sys
from PIL import Image, ImageDraw, ImageFont
D = "/Users/yqin/repo/playground/lucas-academy-video-data/debussy-impressions"
film = json.load(open(f"{D}/film.json"))
out = sys.argv[1] if len(sys.argv) > 1 else f"{D}/film-arrangement.jpg"
fz = ImageFont.truetype("/System/Library/Fonts/STHeiti Medium.ttc", 26); fs = ImageFont.truetype("/System/Library/Fonts/STHeiti Light.ttc", 18)
H, LW, BG = 170, 300, (250, 248, 244)
tot = sum(p["dur"] for p in film["pieces"]); npt = sum(len(p["paintings"]) for p in film["pieces"])
rows = []
for p in film["pieces"]:
    tiles = []
    for pid, status, *mm in p["paintings"]:
        im = Image.open(f"{D}/preview/img/{pid}.jpg").convert("RGB"); im.thumbnail((10000, H)); d = ImageDraw.Draw(im)
        tag = " · ".join(t for t in ({"photo": "", "codex": "需 Codex", "chain": "画溶画"}[status], "动" if mm else "") if t)
        if tag:
            tw = d.textlength(tag, font=fs); d.rectangle([0, H - 26, tw + 10, H], fill=(20, 20, 20))
            d.text((5, H - 24), tag, font=fs, fill=(255, 220, 120) if mm else (255, 255, 255))
        tiles.append(im)
    row = Image.new("RGB", (LW + sum(t.width + 8 for t in tiles), H + 12), BG); d = ImageDraw.Draw(row)
    m, s = divmod(p["dur"], 60)
    d.text((10, 30), f"{p['n']}. {p['zh']}", font=fz, fill=(30, 30, 40))
    d.text((10, 72), f"{m}:{s:02d} · {len(p['paintings'])} 幅 · 每幅 {p['dur'] / len(p['paintings']):.0f} 秒", font=fs, fill=(90, 90, 100))
    d.text((10, 100), p["theme"], font=fs, fill=(90, 90, 100))
    x = LW
    for t in tiles: row.paste(t, (x, 6)); x += t.width + 8
    rows.append(row)
W = max(r.width for r in rows)
sheet = Image.new("RGB", (W, 60 + sum(r.height for r in rows)), BG); hd = ImageDraw.Draw(sheet)
hd.text((10, 14), f"德彪西 × 印象派 · {film['version']} · {tot // 60}:{tot % 60:02d} · {npt} 幅 · 平均每幅 {tot / npt:.0f} 秒（黄字 = 计划用 MiniMax 让画动起来）", font=fz, fill=(30, 30, 40))
y = 60
for r in rows: sheet.paste(r, (0, y)); y += r.height
if sheet.width > 2400: sheet = sheet.resize((2400, int(sheet.height * 2400 / sheet.width)))
sheet.save(out, quality=85); print("wrote", out, sheet.size)
