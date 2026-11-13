"""Build one common picture timeline and external captions for two languages."""
from pathlib import Path
import argparse
import hashlib
import json
import math

ROOT=Path(__file__).resolve().parents[2]
PUBLIC=ROOT/'public/family-ai-lab-02'
DOC=ROOT/'docs/family-ai-lab-02'
FPS=30


def timestamp(frame):
    ms=round(frame/FPS*1000);hours,ms=divmod(ms,3600000);minutes,ms=divmod(ms,60000);seconds,ms=divmod(ms,1000)
    return f'{hours:02}:{minutes:02}:{seconds:02},{ms:03}'


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--voiced',action='store_true');args=parser.parse_args()
    script=json.loads((Path(__file__).parent/'script.json').read_text())
    narration=json.loads((PUBLIC/'narration.json').read_text()) if args.voiced else None
    rows=[];frame=0
    for row in script['lines']:
        if narration:
            seconds={lang:narration[lang][row['id']]['seconds'] for lang in ('en','zh')}
            for lang in seconds:assert narration[lang][row['id']]['caption']==row[lang],('stale narration',row['id'],lang)
        else:seconds={'en':len(row['en'].split())/2.6,'zh':sum('\u3400'<=c<='\u9fff' for c in row['zh'])/3.5}
        body=math.ceil((max(seconds.values())+.1)*FPS)
        body=max(body,round(row.get('minSeconds',0)*FPS))
        duration=body+round((.4+row.get('hold',0))*FPS)
        rows.append({**row,'from':frame,'duration':duration,'voiceSeconds':seconds})
        frame+=duration
    timeline={'fps':FPS,'durationInFrames':frame,'narrated':args.voiced,'defaultLanguage':'en','scenes':script['scenes'],'workingTitle':script['workingTitle'],'lines':rows,'scriptSha256':hashlib.sha256((Path(__file__).parent/'script.json').read_bytes()).hexdigest(),'delivery':'One clean English-label picture; default English and independent Chinese audio; external SRTs only.'}
    (PUBLIC/'timeline.json').write_text(json.dumps(timeline,ensure_ascii=False,indent=2)+'\n')
    (DOC/'timeline.json').write_text(json.dumps(timeline,ensure_ascii=False,indent=2)+'\n')
    for lang in ('en','zh'):
        body=''
        for i,row in enumerate(rows,1):
            start=row['from']+3;end=min(row['from']+row['duration']-3,start+math.ceil((row['voiceSeconds'][lang]+.1)*FPS))
            body+=f'{i}\n{timestamp(start)} --> {timestamp(end)}\n{row[lang]}\n\n'
        (PUBLIC/f'{lang}.srt').write_text(body)
    print('Voiced' if args.voiced else 'Estimated',len(rows),'cue pairs,',frame,'frames,',frame/FPS,'seconds')


if __name__=='__main__':main()
