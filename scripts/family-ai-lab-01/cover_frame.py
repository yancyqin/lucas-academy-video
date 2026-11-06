"""Typeset the accepted headlines over the owner's selected 00:02 video frame."""
import hashlib
import json
import subprocess
from PIL import Image
from build import ROOT, numbers
from cover_v2 import text, W, H, S, WHITE, GOLD, MINT

OUT = ROOT / 'out/family-ai-lab-01/cover'
BG = ROOT / 'public/family-ai-lab-01/art/cover-frame-00-02.png'
SOURCE = ROOT / 'public/family-ai-lab-01/muse/G4-time-travel-v2.mp4'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    expected = json.loads((ROOT / 'docs/family-ai-lab-01/intro-v2.json').read_text())
    assert sha(SOURCE) == expected['sha256']
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', '2', '-i', str(SOURCE),
                    '-frames:v', '1', str(BG)], check=True)
    values = numbers()
    assert (values['claude_million_zh'], values['astra_ten_million_zh']) == ('300', '1000')
    OUT.mkdir(parents=True, exist_ok=True)
    background = Image.open(BG).convert('RGBA').resize((W*S, H*S), Image.Resampling.LANCZOS)
    # Keep the exact shot composition. This is a text-legibility overlay, not a
    # replacement background; the original extracted frame is preserved intact.
    shade = Image.new('RGBA', background.size)
    shade.putdata([(0, 15, 14, round(205*(1-min(1, x/(1120*S)))**.45))
                   for _ in range(H*S) for x in range(W*S)])
    background = Image.alpha_composite(background, shade)
    records = []
    for lang in ('zh', 'en'):
        image = background.copy()
        if lang == 'zh':
            text(image, '比 Claude Fable 5.1', 64, 58, 41, zh=True)
            text(image, f"快{values['claude_million_zh']}万倍", 56, 120, 106, GOLD, zh=True)
            text(image, '比 GPT-6-Astra', 64, 300, 41, zh=True)
            text(image, f"快{values['astra_ten_million_zh']}万倍！", 56, 356, 106, MINT, zh=True)
            text(image, '偷偷告诉你，在家和孩子一起训练！', 64, 650, 28, zh=True)
        else:
            text(image, f"{values['claude_million_en']} MILLION ×", 60, 58, 90, GOLD)
            text(image, 'FASTER THAN', 65, 164, 32, GOLD)
            text(image, 'Claude Fable 5.1', 64, 208, 43)
            text(image, f"{values['astra_ten_million_en']} MILLION ×", 60, 316, 90, MINT)
            text(image, 'FASTER THAN', 65, 423, 32, MINT)
            text(image, 'GPT-6-Astra!', 64, 468, 43)
            text(image, 'Psst… you can train it at home with your kids!', 64, 656, 25)
        image = image.convert('RGB').resize((W, H), Image.Resampling.LANCZOS)
        for ext in ('png', 'jpg'):
            dest = OUT / f'cover-frame-02.{lang}.{ext}'
            image.save(dest, **({'quality':95, 'subsampling':0, 'optimize':True} if ext == 'jpg' else {}))
            records.append({'language':lang, 'path':str(dest.relative_to(ROOT)), 'size':[W,H], 'sha256':sha(dest)})
    manifest = {'ownerSelection':'Use the background at 00:02 of the approved v3 film',
                'seconds':2, 'source':str(SOURCE.relative_to(ROOT)), 'sourceSha256':sha(SOURCE),
                'background':str(BG.relative_to(ROOT)), 'backgroundSha256':sha(BG),
                'composition':'Exact unlettered source frame; no crop, subject move or image regeneration. Local text-contrast shading and code typography only.',
                'language':'One language per cover; model names retained verbatim.',
                'headlines':{'zh':['比Claude Fable 5.1快300万倍','比GPT-6-Astra快1000万倍！'],
                             'en':['3 million times faster than Claude Fable 5.1','10 million times faster than GPT-6-Astra!']},
                'covers':records}
    (ROOT / 'docs/family-ai-lab-01/cover-frame-02.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n')
    print('Generated Chinese/English covers from the 00:02 frame:', OUT)


if __name__ == '__main__':
    main()
