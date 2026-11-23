"""Per-fragment transcript differences and waveform/onset measurements for review."""
from difflib import SequenceMatcher
import json
from pathlib import Path
import re
import unicodedata
import wave

import numpy as np

P=Path(__file__).resolve().parent;V8=P.parent/'v8'
SMALL='zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen'.split()
TENS={2:'twenty',3:'thirty',4:'forty',5:'fifty',6:'sixty',7:'seventy',8:'eighty',9:'ninety'}
def number(n):
    if n<20:return SMALL[n]
    return TENS[n//10]+(' '+SMALL[n%10] if n%10 else '')

def tokens(text,expected):
    text=unicodedata.normalize('NFKD',text).encode('ascii','ignore').decode().lower()
    text=re.sub(r'[-–—]',' ',text)
    for year in re.findall(r'\b[12]\d{3}\b',expected):
        first=int(year[:2]);last=int(year[2:]);variants=[number(first)+' '+number(last)]
        if last<10:variants.extend([number(first)+' oh '+number(last),number(first)+' zero '+number(last),number(first)+' hundred and '+number(last)])
        for phrase in variants:text=re.sub(r'\b'+phrase+r'\b',year,text)
    text=text.replace('rain drop','raindrop').replace('de la croix','delacroix')
    for n in range(99,-1,-1):text=re.sub(r'\b'+number(n)+r'\b',str(n),text)
    return re.findall(r'[a-z]+|\d+',text)

def waveform(path):
    with wave.open(str(path)) as w:
        rate=w.getframerate();v=np.frombuffer(w.readframes(w.getnframes()),'<i2').astype(np.float32)/32768
    assert np.isfinite(v).all() and len(v)>rate*.3 and np.max(np.abs(v))>.01
    head=v[:round(.15*rate)]
    return dict(seconds=len(v)/rate,peak=float(np.max(np.abs(v))),
        head_150ms_peak=float(np.max(np.abs(head))),head_150ms_rms=float(np.sqrt(np.mean(head*head))),
        largest_step=float(np.max(np.abs(np.diff(v)))),first_sample=float(v[0]),last_sample=float(v[-1]))

def main():
    plan=json.loads((V8/'full-plan.json').read_text());done=[]
    final_path=P/'voice-overrides.json'
    final={i['id']:i for i in json.loads(final_path.read_text())['items'] if i['language']=='en'} if final_path.exists() else {}
    trusted={i['id']:i for i in json.loads((V8/'opening-overrides.json').read_text())['items']}
    for item in [i for i in plan['voice_fragments'] if i['language']=='en']:
        receipt=P/'english'/(item['id']+'-'+item['text_sha256'][:12])/'receipt.json'
        if item['id'] in final:new=final[item['id']]
        elif item['id'] in trusted:new=trusted[item['id']]
        elif receipt.exists():new=json.loads(receipt.read_text())
        else:continue
        file=Path(new['file']);asr=file.parent/'asr.txt'
        if not asr.exists():continue
        actual=asr.read_text().strip();a=tokens(item['text'],item['text']);b=tokens(actual,item['text'])
        matcher=SequenceMatcher(None,a,b,autojunk=False);changes=[]
        for tag,i,j,x,y in matcher.get_opcodes():
            if tag!='equal':changes.append(dict(expected=' '.join(a[i:j]),recognized=' '.join(b[x:y])))
        stats=waveform(file);old=waveform(item['file'])
        assert abs(stats['seconds']-new['seconds'])<.001
        scene=next(s for s in plan['scenes'] if s['id']==item['paragraph_id'])
        preceding=sum(i['seconds'] for i in plan['voice_fragments'] if i['language']=='en' and i['paragraph_id']==item['paragraph_id'] and i['id']<item['id'])
        done.append(dict(id=item['id'],start=scene['voice_start']+preceding,expected=item['text'],recognized=actual,
            similarity=matcher.ratio(),changes=changes,new_waveform=stats,previous_waveform=old,
            first_two_tokens_match=a[:2]==b[:2],last_two_tokens_match=a[-2:]==b[-2:]))
    result=dict(reviewed=len(done),total=73,complete=len(done)==73,items=done,
        note='ASR names, number formatting and accent differences are review flags, not automatic evidence of a pronunciation error.')
    (P/'english-review.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
    print('Reviewed',len(done),'/ 73')
    for r in done:
        if r['changes']:print(r['id'],round(r['similarity'],3),r['changes'])

if __name__=='__main__':main()
