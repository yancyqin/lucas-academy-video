"""Carry unchanged, checked technical takes into v2 by caption and WAV hash.

S1/S2 are always synthesized again for their new lively direction. English AI
lines are also regenerated, removing the previous artificial A / I separation.
"""
from pathlib import Path
import hashlib
import json
import shutil
from narrate import ROOT, MEDIA, plan


def main():
    archive=ROOT.parent/'lucas-academy-video-data/family-ai-lab-01/archive/v1'
    old=json.loads((archive/'public/family-ai-lab-01/narration.json').read_text())
    report={}
    for lang in ('en','zh'):
        lines=plan(lang)
        (ROOT/f'docs/family-ai-lab-01/voice.{lang}.json').write_text(json.dumps(lines,ensure_ascii=False,indent=2)+'\n')
        dest=MEDIA/f'outputs/louise/{lang}/family-ai-lab-01-v2/s1.10'
        dest.mkdir(parents=True,exist_ok=True)
        for line in lines:
            if line['scene']<=2 or (lang=='en' and 'AI' in line['caption']):continue
            matches=[(id,v) for id,v in old[lang].items() if v['caption']==line['caption']]
            if not matches:continue
            id,v=matches[0]
            source=archive/'public/family-ai-lab-01'/v['clip']
            assert hashlib.sha256(source.read_bytes()).hexdigest()==v['sha256']
            target=dest/(line['id']+'.wav')
            if target.exists():assert target.read_bytes()==source.read_bytes(),str(target)
            else:shutil.copy2(source,target)
            meta={**line,'durationSeconds':v['seconds'],'sampleRate':v['sampleRate'],
                  'reused':{'v1Id':id,'sha256':v['sha256'],'originalSource':v['source'],
                            'originalSettingsSha256':v['settingsSha256'],'spoken':v['spoken'],'previousCheck':v['check']}}
            target.with_suffix('.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
            report[f'{lang}/{line["id"]}']=meta['reused']
        print(lang,'reused',sum(k.startswith(lang+'/') for k in report),'of',len(lines))
    (ROOT/'docs/family-ai-lab-01/reused-voice-v2.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')


if __name__=='__main__':main()
