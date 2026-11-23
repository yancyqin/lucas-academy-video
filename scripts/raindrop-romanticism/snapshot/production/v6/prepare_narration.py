"""Create faithful, short synthesis units from the owner-confirmed bilingual script."""
import hashlib
import json
from pathlib import Path
import re

P=Path(__file__).resolve().parent


def split(text,language):
    limit=70 if language=='zh' else 260
    if language=='zh':
        sentences=re.findall(r'[^。！？；]+[。！？；]?[”’]?',text)
    else:
        sentences=re.split(r'(?<=[.!?])\s+',text)
    pieces=[]
    for sentence in sentences:
        sentence=sentence.strip()
        if not sentence:continue
        if len(sentence)<=limit:pieces.append(sentence);continue
        if language=='zh':parts=re.findall(r'[^，、：]+[，、：]?',sentence)
        else:parts=re.split(r'(?<=[,;:])\s+',sentence)
        for part in parts:
            part=part.strip()
            if len(part)<=limit:pieces.append(part);continue
            while len(part)>limit:
                end=limit if language=='zh' else part.rfind(' ',0,limit+1)
                assert end>0
                pieces.append(part[:end].strip());part=part[end:].strip()
            if part:pieces.append(part)
    chunks=[];buffer='';separator='' if language=='zh' else ' '
    for piece in pieces:
        candidate=buffer+separator+piece if buffer else piece
        if len(candidate)>limit and buffer:chunks.append(buffer);buffer=piece
        else:buffer=candidate
    if buffer:chunks.append(buffer)
    compact=lambda s:re.sub(r'\s+','',s)
    assert compact(''.join(chunks))==compact(text),(language,text,chunks)
    return chunks


def main():
    script=json.loads((P/'narration-bilingual.json').read_text())
    requests=[]
    for language in ['zh','en']:
        for row in script['rows']:
            if not row['spoken']:continue
            for i,text in enumerate(split(row[language],language),1):
                requests.append(dict(id=f"{row['id']}-{i:02d}",paragraph_id=row['id'],language=language,
                                     section=row['section'],text=text,text_sha256=hashlib.sha256(text.encode()).hexdigest()))
    manifest=dict(source_sha256=script['source_sha256'],model='speech-2.8-hd',speed=1.0,
                  emotion='automatic natural narration; no global sad setting',
                  target_voices={'zh':'fangfang/zh','en':'louise/en'},requests=requests)
    (P/'synthesis-plan.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
    print('Short synthesis units',len(requests))
    for language in ['zh','en']:
        texts=[x['text'] for x in requests if x['language']==language]
        units=sum(len(t)+sum('\u3400'<=c<='\u9fff' for c in t) for t in texts)
        print(language,'units',len(texts),'estimated billing characters',units,'RMB',round(units*3.5/10000,2))


if __name__=='__main__':main()
