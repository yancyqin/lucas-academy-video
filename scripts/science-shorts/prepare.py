"""Stage only existing owner-made clips, then build vertical picture/audio intervals."""
import argparse
import json
import math
import shutil
import subprocess
import re
import textwrap
from common import ROOT, PUBLIC, DOCS, OUT, SOURCE, FPS, values, plans, take_dir, sha


def stamp(seconds):
    ms=round(seconds*1000)
    return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}'


def stage_inputs():
    family=ROOT/'public/family-ai-lab-01';opto=ROOT.parent/'lucas-academy-video-data/fun-informatics-04'
    sources={
      'perceptron-portal':family/'muse/G4-time-travel-v2.mp4',
      'perceptron-1957':family/'muse/G1.mp4',
      'perceptron-lab':family/'muse/G2.mp4',
      'perceptron-family':family/'muse/G3.mp4',
      'opto-algae':opto/'muse/G2-1.mp4','opto-goggles':opto/'muse/G3-1.mp4',
      'opto-dots':opto/'muse/G4-1.mp4','opto-touch':opto/'muse/G5-1.mp4','opto-camera':opto/'muse/G6-1.mp4',
    }
    expected={name:digest for digest,name in [row.split('  ',1) for row in (opto/'SHA256SUMS').read_text().splitlines()]}
    assets={}
    for name,path in sources.items():
        digest=sha(path)
        if name.startswith('opto-'):assert digest==expected['muse/'+path.name],name
        dest=PUBLIC/(name+'.mp4')
        if dest.exists():assert sha(dest)==digest,name
        else:shutil.copy2(path,dest)
        probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=width,height,r_frame_rate:format=duration','-of','json',str(dest)]))
        assets[name]={'path':dest.name,'sha256':digest,'original':str(path),'seconds':float(probe['format']['duration']),
                      'width':probe['streams'][0]['width'],'height':probe['streams'][0]['height'],'credit':'Owner-made Muse illustration; not documentary patient footage'}
    pixels=json.loads((family/'picture.json').read_text())['pixels']
    weights=json.loads((family/'trained-model.json').read_text())['points']
    tiles=json.loads((family/'training-tiles.json').read_text())
    results={name:json.loads((ROOT/f'scripts/perceptron-race/results/{filename}.json').read_text())
             for name,filename in [('x','perceptron-js'),('claude','claude-fable'),('astra','astra-low'),('qwen','qwen-fast')]}
    payload={'pixels':pixels,'weights':weights,'training':tiles,'metrics':results,'values':values(),'assets':assets}
    (PUBLIC/'data.json').write_text(json.dumps(payload,ensure_ascii=False)+'\n')
    return payload


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--estimated',action='store_true');parser.add_argument('--film');parser.add_argument('--restored',action='store_true');args=parser.parse_args()
    PUBLIC.mkdir(parents=True,exist_ok=True);DOCS.mkdir(parents=True,exist_ok=True);OUT.mkdir(parents=True,exist_ok=True)
    payload=json.loads((PUBLIC/'data.json').read_text()) if args.restored else stage_inputs()
    assets=payload['assets']
    for asset in assets.values():assert sha(PUBLIC/asset['path'])==asset['sha256']
    manifest={lang:{item['id']:item for item in plans(lang)} for lang in ('en','zh')}
    choices=json.loads((DOCS/'voice-choices.json').read_text()) if not args.estimated else None
    for film,info in SOURCE['films'].items():
        if args.film and film!=args.film:continue
        previous=json.loads((PUBLIC/f'timeline.{film}.json').read_text()) if args.restored else None
        cursor=0;lines=[];voices={'en':{},'zh':{}}
        for item in info['lines']:
            durations=[]
            for lang in ('en','zh'):
                row=manifest[lang][item['id']]
                if args.estimated:
                    units=len(re.findall(r'[\u3400-\u9fff]',row['caption']))/3.5 if lang=='zh' else len(row['caption'].split())/2.6
                    durations.append(max(2.7,units))
                else:
                    decision=choices[f'{lang}/{item["id"]}'];assert decision['checked']
                    name=item['id']+(f'.take{decision["take"]}' if decision.get('take') else '')
                    target=PUBLIC/f'narration/{lang}/{item["id"]}.wav'
                    if args.restored:
                        old=previous['voices'][lang][item['id']]
                        assert old['settingsSha256']==row['settingsSha256'] and sha(target)==old['sha256']==decision['sha256']
                        seconds=old['seconds']
                    else:
                        wav=take_dir(lang)/(name+'.wav');meta=json.loads(wav.with_suffix('.json').read_text())
                        assert meta['settingsSha256']==row['settingsSha256'] and sha(wav)==meta['sha256'],item['id']
                        target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(wav,target)
                        seconds=meta['durationSeconds']
                    voices[lang][item['id']]={'path':str(target.relative_to(PUBLIC)),'sha256':sha(target),'seconds':seconds,'settingsSha256':row['settingsSha256']}
                    durations.append(seconds)
            duration=math.ceil((max(durations)+.1+.28)*FPS)
            duration=max(duration,round(item.get('minSeconds',0)*FPS))
            if item['id']=='p02':duration=max(duration,round(5.7*FPS))
            if item==info['lines'][-1]:duration+=round(info.get('endHoldSeconds',2)*FPS)
            lines.append({'id':item['id'],'visual':item['visual'],'from':cursor,'duration':duration,
                          'text':{lang:manifest[lang][item['id']]['caption'] for lang in ('en','zh')}})
            cursor+=duration
        if info.get('targetSeconds') and not args.estimated:
            target=round(info['targetSeconds']*FPS)
            adjustment=target-cursor
            # Only shorten the silent ending; keep every selected take and at least .2 s after it.
            assert lines[-1]['duration']+adjustment>=math.ceil((max(durations)+.1+.2)*FPS),(film,'Narration exceeds the one-minute cut',cursor/FPS)
            lines[-1]['duration']+=adjustment
            cursor=target
        lookup={item['id']:item for item in lines};shots=[]
        for item in info['shots']:
            first,last=lookup[item['first']],lookup[item['last']]
            start=first['from'];end=last['from']+last['duration'];seconds=(end-start)/FPS
            rate=min(1.35,(item['out']-item['in'])/seconds)
            assert item['in']+seconds*rate<=assets[item['asset']]['seconds']+.001
            shots.append({**item,'from':start,'duration':end-start,'rate':rate})
        timeline={'film':film,'fps':FPS,'width':1080,'height':1920,'defaultLanguage':'en','durationInFrames':cursor,
                  'narrated':not args.estimated,'lines':lines,'shots':shots,'voices':voices,'title':info['title']}
        (PUBLIC/f'timeline.{film}.json').write_text(json.dumps(timeline,ensure_ascii=False,indent=2)+'\n')
        (DOCS/f'timeline.{film}.json').write_text(json.dumps(timeline,ensure_ascii=False,indent=2)+'\n')
        folder=OUT/film;folder.mkdir(exist_ok=True)
        for lang in ('en','zh'):
            markdown=[f'# {info["title"][lang]}','']+[f'**{line["id"]}** {line["text"][lang]}' for line in lines]
            (DOCS/f'{film}-script.{lang}.md').write_text('\n\n'.join(markdown)+'\n')
            captions=[]
            for index,line in enumerate(lines,1):
                end=line['from']+line['duration']-round(.28*FPS)
                if not args.estimated:
                    speech_end=line['from']+math.ceil((max(voices[lang][line['id']]['seconds'] for lang in ('en','zh'))+.1)*FPS)
                    end=max(end,speech_end)
                copy='\n'.join(textwrap.wrap(line['text'][lang],width=48 if lang=='en' else 24))
                captions.append(f'{index}\n{stamp(line["from"]/FPS)} --> {stamp(end/FPS)}\n{copy}')
            (folder/f'{"zh-Hans" if lang=="zh" else lang}.srt').write_text('\n\n'.join(captions)+'\n')
        print(film,round(cursor/FPS,2),'seconds;',len(lines),'cues;',len(shots),'moving shots',flush=True)
    (DOCS/'assets.json').write_text(json.dumps(assets,ensure_ascii=False,indent=2)+'\n')


if __name__=='__main__':main()
