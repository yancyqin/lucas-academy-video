"""Owner-requested cover revision, without changing or rendering the film.

The generated background is versioned; all typography is drawn by code.
Run with .venv-align/bin/python scripts/family-ai-lab-01/cover_v2.py.
"""
import hashlib
import json
from PIL import Image, ImageDraw, ImageFont
from build import ROOT, numbers

W, H, S = 1280, 720, 2
OUT = ROOT / 'out/family-ai-lab-01/cover'
BG = ROOT / 'public/family-ai-lab-01/art/cover-v2-bg.png'
WHITE, GOLD, MINT = '#fff8e9', '#ffca75', '#baffb0'
ZH = '/System/Library/Fonts/Hiragino Sans GB.ttc'
EN = '/System/Library/Fonts/Supplemental/Arial Bold.ttf'


def text(image, copy, x, y, size, color=WHITE, zh=False):
    font = ImageFont.truetype(ZH if zh else EN, size*S, index=2 if zh else 0)
    draw = ImageDraw.Draw(image)
    box = draw.textbbox((x*S, y*S), copy, font=font, anchor='lt')
    assert box[0] >= 0 and box[2] <= 790*S and box[3] < H*S, (copy, box)
    draw.text(((x+1)*S, (y+3)*S), copy, font=font, fill='#00100ddd', anchor='lt')
    draw.text((x*S, y*S), copy, font=font, fill=color, anchor='lt')


def main():
    n = numbers()
    assert (n['claude_million_zh'], n['astra_ten_million_zh']) == ('300', '1000')
    OUT.mkdir(parents=True, exist_ok=True)
    background = Image.open(BG).convert('RGBA').resize((W*S, H*S), Image.Resampling.LANCZOS)
    records = []
    for lang in ('zh', 'en'):
        image = background.copy()
        if lang == 'zh':
            text(image, '比 Claude Fable 5.1', 64, 58, 41, zh=True)
            text(image, '快300万倍', 56, 120, 106, GOLD, zh=True)
            text(image, '比 GPT-6-Astra', 64, 300, 41, zh=True)
            text(image, '快1000万倍！', 56, 356, 106, MINT, zh=True)
            text(image, '3 million times faster than Claude Fable 5.1', 66, 500, 21)
            text(image, '10 million times faster than GPT-6-Astra!', 66, 531, 21)
            text(image, '偷偷告诉你，在家和孩子一起训练！', 64, 650, 28, zh=True)
        else:
            text(image, '3 MILLION ×', 60, 58, 90, GOLD)
            text(image, 'FASTER THAN', 65, 164, 32, GOLD)
            text(image, 'Claude Fable 5.1', 64, 208, 43)
            text(image, '10 MILLION ×', 60, 316, 90, MINT)
            text(image, 'FASTER THAN', 65, 423, 32, MINT)
            text(image, 'GPT-6-Astra!', 64, 468, 43)
            text(image, '比 Claude Fable 5.1 快300万倍', 66, 555, 20, zh=True)
            text(image, '比 GPT-6-Astra 快1000万倍！', 66, 585, 20, zh=True)
            text(image, 'Psst… you can train it at home with your kids!', 64, 656, 25)
        dest = OUT / f'cover-v2.{lang}.png'
        image.convert('RGB').resize((W,H), Image.Resampling.LANCZOS).save(dest)
        records.append({'language':lang, 'path':str(dest.relative_to(ROOT)), 'size':[W,H],
                        'sha256':hashlib.sha256(dest.read_bytes()).hexdigest()})
    sheet = Image.new('RGB', (W, H//2), '#001710')
    for i, lang in enumerate(('zh', 'en')):
        sheet.paste(Image.open(OUT / f'cover-v2.{lang}.png').resize((W//2,H//2)), (i*(W//2), 0))
    sheet.save(OUT / 'cover-v2.pair.png')
    manifest = {'status':'style candidate for owner review; video revision not started',
        'background':str(BG.relative_to(ROOT)), 'backgroundSha256':hashlib.sha256(BG.read_bytes()).hexdigest(),
        'headlines':{'zh':['比Claude Fable 5.1快300万倍','比GPT-6-Astra快1000万倍！'],
                     'en':['3 million times faster than Claude Fable 5.1', '10 million times faster than GPT-6-Astra!']},
        'teasers':{'zh':'偷偷告诉你，在家和孩子一起训练！','en':'Psst… you can train it at home with your kids!'},
        'typography':'Code only; no About/Over/约/多 in the new headline.', 'covers':records}
    (ROOT / 'docs/family-ai-lab-01/cover-v2.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n')
    print('Cover candidates:', *(str(ROOT/r['path']) for r in records), sep='\n')


if __name__ == '__main__':
    main()
