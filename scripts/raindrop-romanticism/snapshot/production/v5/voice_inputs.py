"""Build local CosyVoice inputs from the approved English script."""
from pathlib import Path
import json
import re

P=Path(__file__).resolve().parent
PLAN=json.loads((P.parent/'v2/edit-plan.json').read_text())

def groups(text):
    sentences=re.split(r'(?<=[.?!])\s+',text)
    chunks=[]
    current=''
    for sentence in sentences:
        candidate=(current+' '+sentence).strip()
        if current and len(candidate.split())>42:
            chunks.append(current)
            current=sentence
        else:
            current=candidate
    if current:
        chunks.append(current)
    return chunks

entries=[]
for scene in PLAN['scenes']:
    text=scene.get('text','')
    if not text:
        continue
    for index,chunk in enumerate(groups(text),1):
        spoken=chunk
        fixes={'mono no aware':'mono no ah-wah-ray','Gericault':'Géricault',
               'Theodore Géricault':'Théodore Géricault','Eugene Delacroix':'Eugène Delacroix'}
        for original,replacement in fixes.items():
            spoken=spoken.replace(original,replacement)
        entries.append({'id':f"{scene['id']}-{index:02d}",'scene_id':scene['id'],
                        'caption':chunk,'text':spoken})
for name,profile,speed in [('louise','louise/en',1.1),('fangfang','fangfang/zh',1.2)]:
    lines=[]
    for line in entries:
        take={**line,'speed':speed}
        if name=='louise':
            take.update(mode='zero-shot-instruct',
                 instruct='Please speak in a curious, unhurried voice, like discovering something together with a child.')
        lines.append(take)
    data={'voice':profile,'language':'en','speed':speed,'lines':lines}
    (P/'voices'/f'{name}.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
print(f'{len(entries)} phrases from {len(set(entry["scene_id"] for entry in entries))} approved narration paragraphs.')
