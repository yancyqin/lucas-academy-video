"""Pack the owner's six independent Muse shots with exact-size references."""
from pathlib import Path
import hashlib
import html
import json
import shutil
import zipfile

ROOT=Path(__file__).resolve().parents[2]
DOC=ROOT/'docs/family-ai-lab-02/design-v2'
OUT=ROOT/'out/family-ai-lab-02/muse-pack'
ART=ROOT/'public/family-ai-lab-02/orbital-v2/art'


def main():
    spec=json.loads((DOC/'muse-pack.json').read_text())
    OUT.mkdir(parents=True,exist_ok=True)
    rows=[]
    zh=['# Muse 单镜头生成包','视频由用户手动生成；一张参考图对应一条独立六秒视频。先做 G1a、G1b，之后再做 G2–G5。','每条 prompt.txt 已包含完整设置，上传同名 PNG 后复制即可。不要一次把六个提示词合在同一个视频里。']
    en=['# Muse single-shot pack','One uploaded reference per separate six-second video. Start with G1a and G1b.']
    cards=[]
    for i,row in enumerate(spec['shots'],1):
        stem=f'{i:02}-{row["id"]}-{row["name"]}'
        dest=OUT/(stem+'.png')
        shutil.copy2(ART/row['reference'],dest)
        prompt_zh=spec['commonZh']+'\n\n'+row['zh']
        prompt_en=spec['commonEn']+'\n\n'+row['en']
        (OUT/(stem+'.prompt.zh.txt')).write_text(prompt_zh+'\n')
        (OUT/(stem+'.prompt.en.txt')).write_text(prompt_en+'\n')
        zh.extend([f'\n## {row["id"]} · {row["title"]}',f'参考图：{dest.name}',f'\n```text\n{prompt_zh}\n```'])
        en.extend([f'\n## {row["id"]}',f'Reference: {dest.name}',f'\n```text\n{prompt_en}\n```'])
        rows.append({**row,'packImage':dest.name,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest()})
        cards.append(f'<section><h2>{html.escape(row["id"]+" · "+row["title"])}</h2><img src="{dest.name}" alt="{html.escape(row["title"])}"><label>中文提示词</label><textarea readonly>{html.escape(prompt_zh)}</textarea><label>English prompt</label><textarea readonly>{html.escape(prompt_en)}</textarea></section>')
    extra=OUT/'backgrounds';extra.mkdir(exist_ok=True)
    for name in ('lab-workbench.png','cargo-bay.png'):
        shutil.copy2(ART/name,extra/name)
    shutil.copy2(ROOT/'public/family-ai-lab-02/design-v2/01-orbital.png',OUT/'00-style-reference.png')
    shutil.copy2(DOC/'full-film-prompts.json',OUT/'IMAGEGEN-PROMPTS.json')
    (OUT/'PROMPTS.zh.md').write_text('\n\n'.join(zh)+'\n')
    (OUT/'PROMPTS.en.md').write_text('\n\n'.join(en)+'\n')
    (OUT/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>Family AI Lab · Muse 单镜头</title><style>body{margin:40px auto;max-width:1100px;padding:0 24px;background:#07111c;color:#e9faff;font:18px system-ui}section{margin:50px 0}img{display:block;width:100%;border:1px solid #31576c}textarea{box-sizing:border-box;width:100%;min-height:145px;padding:16px;margin:8px 0 20px;background:#0c2030;color:#f0faff;font:16px/1.6 system-ui;border:1px solid #396780}label{display:block;margin-top:15px;color:#8fe5ff}</style><h1>Muse · 一条视频一个镜头</h1><p>每张图分别上传，生成六秒、16:9视频。先做 G1a、G1b。下方文本框可全选复制。中文和英文选一种即可。</p>'+''.join(cards))
    (OUT/'manifest.json').write_text(json.dumps({**spec,'shots':rows},ensure_ascii=False,indent=2)+'\n')
    (OUT/'README.md').write_text('解压后打开 index.html：每条镜头有图片和可复制的中英文提示词。\n也可打开 PROMPTS.zh.md，或使用与 PNG 同名的 prompt.zh.txt / prompt.en.txt。\n先生成 G1a、G1b；其他四条可随后分别生成。每条固定机位、单一主动作、六秒、16:9。\n00-style-reference.png 只作全片风格参照，不替代每条自己的参考图。backgrounds/ 是给中后段动画用的环境原图。\n所有图像是内置 imagegen 生成，完整图像提示词和来源哈希记录在仓库 docs/family-ai-lab-02/design-v2/full-film-prompts.json。\n')
    # The owner may unpack the ZIP beside it. Include only this build's known
    # deliverables, never an extracted copy or unrelated files in the folder.
    names=['00-style-reference.png','IMAGEGEN-PROMPTS.json','PROMPTS.zh.md','PROMPTS.en.md','index.html','manifest.json','README.md','backgrounds/lab-workbench.png','backgrounds/cargo-bay.png']
    for i,row in enumerate(rows,1):
        stem=f'{i:02}-{row["id"]}-{row["name"]}'
        names.extend([stem+'.png',stem+'.prompt.zh.txt',stem+'.prompt.en.txt'])
    if (OUT/'reference-overview.png').is_file():names.append('reference-overview.png')
    files=sorted(OUT/name for name in names)
    (OUT/'SHA256SUMS').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+str(p.relative_to(OUT))+'\n' for p in files))
    archive=OUT/'FamilyAiLab02-Muse-Single-Shots.zip'
    temporary=archive.with_suffix('.zip.part')
    with zipfile.ZipFile(temporary,'w',zipfile.ZIP_DEFLATED) as z:
        for p in files+[OUT/'SHA256SUMS']:z.write(p,'FamilyAiLab02-Muse-Single-Shots/'+str(p.relative_to(OUT)))
    with zipfile.ZipFile(temporary) as z:
        assert z.testzip() is None
        assert len(z.infolist())==len(files)+1
        for row in rows:
            assert hashlib.sha256(z.read('FamilyAiLab02-Muse-Single-Shots/'+row['packImage'])).hexdigest()==row['sha256']
    temporary.replace(archive)
    print('Packed and verified six references, both prompt languages, world reference and two background plates:',archive)


if __name__=='__main__':main()
