"""Three generated backgrounds, six deterministic 1280x720 covers.

Run with the repository's Pillow environment: .venv-align/bin/python .../cover.py.
No generated typography; all experiment figures come from build.numbers().
"""
from pathlib import Path
import json
from PIL import Image, ImageDraw, ImageFont
from build import ROOT, numbers

W, H, S = 1280, 720, 2
ZH = "/System/Library/Fonts/Hiragino Sans GB.ttc"
EN = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
OUT = ROOT / "out/family-ai-lab-01/cover"
OUT.mkdir(parents=True, exist_ok=True)


def font(size, zh=False):
    return ImageFont.truetype(ZH if zh else EN, round(size * S))


def stamp(im, lines, xy, size, color, *, zh=False, angle=0, spacing=1.19):
    f = font(size, zh)
    text = "\n".join(lines)
    d = ImageDraw.Draw(im)
    box = d.multiline_textbbox((0, 0), text, font=f, spacing=round(size * S * (spacing-1)))
    pad = 15*S
    layer = Image.new("RGBA", (box[2]+2*pad, box[3]+2*pad), (0,0,0,0))
    q = ImageDraw.Draw(layer)
    q.multiline_text((pad, pad-box[1]), text, font=f, fill=color, spacing=round(size*S*(spacing-1)))
    if angle:
        layer = layer.rotate(angle, resample=Image.Resampling.BICUBIC, expand=True)
    x, y = (round(v*S) for v in xy)
    assert 0 <= x and 0 <= y and x+layer.width <= W*S and y+layer.height <= H*S, (text, xy, layer.size)
    im.alpha_composite(layer, (x-pad, y-pad))


def main():
    n = numbers()
    records = []
    for design in (1, 2, 3):
        bg = Image.open(ROOT / f"public/family-ai-lab-01/art/cover-{design}.png").convert("RGBA").resize((W*S,H*S), Image.Resampling.LANCZOS)
        # Preserve the complete generated composition; typography only overlays open space.
        ink = "#152528" if design == 2 else "#fff5df"
        accent = {1:"#ffc05b",2:"#af3b22",3:"#a5ff87"}[design]
        second = "#236879" if design == 2 else "#87dfe3"
        for lang in ("zh", "en"):
            im = bg.copy()
            if lang == "zh":
                stamp(im,[f"比 Claude Fable 5.1 快约 {n['claude_million_zh']} 万倍"],(64,83),25,accent,zh=True,angle=2)
                stamp(im,[f"比 GPT-6-Astra 快 {n['astra_ten_million_zh']} 多万倍"],(95,140),25,second,zh=True,angle=-2)
                stamp(im,["一个 1957 年的 AI，","比 ChatGPT Astra","和 Claude Fable"],(64,242),54,ink,zh=True)
                stamp(im,["还快？"],(63,448),80,accent,zh=True)
                stamp(im,["A 1957 AI model is faster than", "ChatGPT Astra and Claude Fable?"],(66,555),19,ink)
                stamp(im,["偷偷告诉你，在家和孩子一起训练！"],(65,644),24,second,zh=True)
            else:
                stamp(im,[f"About {n['claude_million_en']} million times faster than", "Claude Fable 5.1"],(64,65),23,accent,angle=2)
                stamp(im,[f"Over {n['astra_ten_million_en']} million times faster than", "GPT-6-Astra"],(100,140),23,second,angle=-2)
                stamp(im,["A 1957 AI model","is faster than","ChatGPT Astra","and Claude Fable?"],(64,257),54,ink,spacing=1.17)
                stamp(im,["一个 1957 年的 AI，比 ChatGPT Astra", "和 Claude Fable 还快？"],(65,554),19,ink,zh=True)
                stamp(im,["Psst… you can train it at home with your kids!"],(65,647),22,second)
            path = OUT / f"design-{design}.{lang}.png"
            im.convert("RGB").resize((W,H),Image.Resampling.LANCZOS).save(path)
            records.append({"design":design,"lang":lang,"path":str(path.relative_to(ROOT)),"size":[W,H],"textSource":"code + original JSON only"})
    # One contact sheet is an additional review aid, not an extra design.
    sheet = Image.new("RGB",(1280,3*360),"#202427")
    for i,r in enumerate(records):
        thumb=Image.open(ROOT/r["path"]).resize((640,360),Image.Resampling.LANCZOS)
        sheet.paste(thumb,((i%2)*640,(i//2)*360))
    sheet.save(OUT/"all-designs.png")
    (ROOT/"docs/family-ai-lab-01/covers.json").write_text(json.dumps(records,indent=2)+"\n")
    print("Six covers:",OUT)


if __name__ == "__main__":
    main()
