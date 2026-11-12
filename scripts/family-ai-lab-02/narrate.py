"""Local, owner-authorized Louise synthesis. Existing differing takes are immutable."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import sys

ROOT=Path(__file__).resolve().parents[2]
MEDIA=ROOT.parent/'lucas-academy-media'
DOC=ROOT/'docs/family-ai-lab-02'
SPEED=1.1
TONE={
 'en':'Please tell this story with a warm, curious voice, like sharing a little adventure with a child. Natural connected speech, clear and conversational. The opening and discoveries are playful; explanations are unhurried.',
 'zh':'请用亲切、好奇的语气，像给孩子讲一个小冒险。开头和发现答案时轻快，解释时慢慢说清楚。自然聊天，不用播报腔。',
}


def plan(lang):
    source=json.loads((Path(__file__).parent/'script.json').read_text())
    rows=[]
    for row in source['lines']:
        text=row[lang]
        spoken=text
        if lang=='en' and row['id']=='fa02-04-03':spoken=spoken.replace('PLAY','play')
        if lang=='zh':
            for a,b in [('米娅','米亚'),('里奥','里奥'),('ASCII','阿斯基'),(' P，','，字母 P，'),(' L、A、Y。','字母 L、A、Y。'),(' PLAY，','，PLAY，')]:spoken=spoken.replace(a,b)
        item={'id':row['id'],'caption':text,'spoken':spoken,'voice':f'louise/{lang}','mode':'zero-shot-instruct','instruction':TONE[lang],'speed':SPEED,'scene':row['scene']}
        if lang=='zh' and row['id'] in ('fa02-07-03','fa02-08-01','fa02-08-02'):
            item['instruction']='请用亲切、清楚的普通话讲故事，像坐在孩子旁边说话。语句连贯，节奏平稳。'
        item['settingsSha256']=hashlib.sha256(json.dumps(item,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
        rows.append(item)
    return rows


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--lang',choices=['en','zh'],required=True);parser.add_argument('--only');parser.add_argument('--take',default='');parser.add_argument('--plan',action='store_true');args=parser.parse_args()
    DOC.mkdir(parents=True,exist_ok=True)
    lines=plan(args.lang)
    (DOC/f'voice.{args.lang}.json').write_text(json.dumps(lines,ensure_ascii=False,indent=2)+'\n')
    dest=MEDIA/f'outputs/louise/{args.lang}/family-ai-lab-02-v1/s1.10';dest.mkdir(parents=True,exist_ok=True)
    only=set(args.only.split(',')) if args.only else None
    todo=[]
    for item in lines:
        if only and item['id'] not in only:continue
        name=item['id']+(f'.take{args.take}' if args.take else '')
        wav=dest/(name+'.wav');meta=dest/(name+'.json')
        if wav.exists() and meta.exists():
            assert json.loads(meta.read_text())['settingsSha256']==item['settingsSha256'],'Changed line requires --take: '+name
        else:todo.append((item,wav,meta))
    if args.plan:print(args.lang,len(todo),'takes planned');return
    if not todo:print('All takes already exist');return
    os.chdir(MEDIA);sys.path.insert(0,str(MEDIA/'src'))
    import torch
    torch.set_num_threads(3);torch.set_num_interop_threads(2)
    from modelscope import snapshot_download
    normalizers=Path(snapshot_download('pengzhendong/wetext',local_files_only=True))
    for language in ('en','zh'):
        for name in ('tagger.fst','verbalizer.fst'):assert (normalizers/language/'tn'/name).is_file()
    import wetext.wetext as frontend
    frontend.snapshot_download=lambda model:str(normalizers)
    from lucas_media.cosyvoice_engine import CosyVoiceEngine
    from lucas_media.joke import DEFAULT_PEAK_DBFS,add_peak_headroom,save_wav
    engine=CosyVoiceEngine(MEDIA/f'profiles/louise/{args.lang}/profile.json')
    for i,(item,wav,meta) in enumerate(todo,1):
        speech,rate,_=engine.synthesize(item['spoken'],target_language=args.lang,mode=item['mode'],instruction=item['instruction'],speed=item['speed'])
        seconds=speech.shape[1]/rate
        assert seconds>.5,('Empty synthesis',item['id'])
        save_wav(wav,add_peak_headroom(speech,peak_dbfs=DEFAULT_PEAK_DBFS),rate)
        meta.write_text(json.dumps({**item,'durationSeconds':seconds,'sampleRate':rate},ensure_ascii=False,indent=2)+'\n')
        print(f'[{i}/{len(todo)}] {args.lang} {item["id"]} {seconds:.2f}s',flush=True)


if __name__=='__main__':main()
