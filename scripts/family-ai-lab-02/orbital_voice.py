"""Nine changed orbital lines; reuse all unchanged, already inspected v1 takes."""
from pathlib import Path
import argparse,hashlib,json,os,shutil,sys

ROOT=Path(__file__).resolve().parents[2]
MEDIA=ROOT.parent/'lucas-academy-media'
PUBLIC=ROOT/'public/family-ai-lab-02'
DOC=ROOT/'docs/family-ai-lab-02/design-v2'
SPEED=1.1


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def plan(lang):
    source=json.loads((Path(__file__).parent/'orbital-script.json').read_text())
    old=json.loads((PUBLIC/'narration.json').read_text())
    rows=[]
    for row in source['lines']:
        if old[lang][row['id']]['caption']==row[lang]:continue
        text=row[lang];spoken=text
        if lang=='zh':
            for a,b in [('米娅','米亚'),(' L、A、Y。','字母 L、A、Y。')]:spoken=spoken.replace(a,b)
        tone=('Please speak with playful curiosity, as if inviting a child into a little space adventure. Warm, lively, natural connected speech. Clear short sentences.' if row['scene']==1 else 'Please tell this story with a warm, curious voice. Natural connected speech, clear and conversational. The explanation is calm and unhurried.') if lang=='en' else ('请用轻快、好奇的语气讲这个太空小冒险，像在和孩子聊天。短句自然连贯，亲切活泼。' if row['scene']==1 else '请用亲切、清楚的普通话讲故事，像坐在孩子旁边说话。语句连贯，节奏平稳。')
        item={'id':row['id'],'caption':text,'spoken':spoken,'voice':f'louise/{lang}','mode':'zero-shot-instruct','instruction':tone,'speed':SPEED,'scene':row['scene']}
        item['settingsSha256']=hashlib.sha256(json.dumps(item,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
        rows.append(item)
    return rows


def folder(lang):return MEDIA/f'outputs/louise/{lang}/family-ai-lab-02-v2/s1.10'


def generate(lang,take,only=None):
    import torch
    torch.set_num_threads(3);torch.set_num_interop_threads(2)
    os.chdir(MEDIA);sys.path.insert(0,str(MEDIA/'src'))
    from modelscope import snapshot_download
    normalizers=Path(snapshot_download('pengzhendong/wetext',local_files_only=True))
    for language in ('en','zh'):
        for name in ('tagger.fst','verbalizer.fst'):assert (normalizers/language/'tn'/name).is_file()
    import wetext.wetext as frontend
    frontend.snapshot_download=lambda model:str(normalizers)
    from lucas_media.cosyvoice_engine import CosyVoiceEngine
    from lucas_media.joke import DEFAULT_PEAK_DBFS,add_peak_headroom,save_wav
    engine=CosyVoiceEngine(MEDIA/f'profiles/louise/{lang}/profile.json')
    target=folder(lang);target.mkdir(parents=True,exist_ok=True)
    rows=plan(lang);(DOC/f'orbital-voice.{lang}.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
    for row in rows:
        if only and row['id'] not in only:continue
        name=row['id']+(f'.take{take}' if take else '')
        wav=target/(name+'.wav');meta=wav.with_suffix('.json')
        if wav.exists():
            assert meta.is_file() and json.loads(meta.read_text())['settingsSha256']==row['settingsSha256'],('Immutable take differs',wav)
            continue
        speech,rate,_=engine.synthesize(row['spoken'],target_language=lang,mode=row['mode'],instruction=row['instruction'],speed=row['speed'])
        seconds=speech.shape[1]/rate;assert seconds>.5
        save_wav(wav,add_peak_headroom(speech,peak_dbfs=DEFAULT_PEAK_DBFS),rate)
        assert wav.stat().st_size>1000
        meta.write_text(json.dumps({**row,'durationSeconds':seconds,'sampleRate':rate},ensure_ascii=False,indent=2)+'\n')
        print(lang,name,round(seconds,2),'seconds',flush=True)


def check(lang,take,model_name='small',only=None):
    import torch,whisper
    torch.set_num_threads(2)
    model=whisper.load_model(model_name,device='cpu')
    path=DOC/('orbital-asr.json' if model_name=='small' else f'orbital-asr.{model_name}.json');report=json.loads(path.read_text()) if path.exists() else {}
    for row in plan(lang):
        if only and row['id'] not in only:continue
        name=row['id']+(f'.take{take}' if take else '');wav=folder(lang)/(name+'.wav');key=lang+'/'+name
        if report.get(key,{}).get('sha256')==sha(wav):continue
        result=model.transcribe(str(wav),language=lang,condition_on_previous_text=False,fp16=False,word_timestamps=True)
        report[key]={'sha256':sha(wav),'expected':row['spoken'],'heard':result['text'].strip(),'segments':result['segments'],'model':model_name}
        path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
        print(key,'|',report[key]['heard'],flush=True)


def select():
    import soundfile as sf
    old=json.loads((PUBLIC/'narration.json').read_text());script=json.loads((Path(__file__).parent/'orbital-script.json').read_text());choices=json.loads((DOC/'orbital-voice-review.json').read_text());manifest={'en':{},'zh':{}}
    for lang in manifest:
        for row in script['lines']:
            prior=old[lang][row['id']]
            if prior['caption']==row[lang]:manifest[lang][row['id']]={**prior,'reusedFromV1':True};continue
            choice=choices[lang+'/'+row['id']];assert choice['checked']
            name=row['id']+(f'.take{choice["take"]}' if choice.get('take') else '');source=folder(lang)/(name+'.wav');meta=json.loads(source.with_suffix('.json').read_text())
            assert meta['caption']==row[lang] and sha(source)==choice['sha256']
            target=PUBLIC/f'orbital-v2/narration/{lang}/{name}.wav';target.parent.mkdir(parents=True,exist_ok=True)
            if target.exists():assert sha(target)==sha(source)
            else:shutil.copy2(source,target)
            samples,rate=sf.read(target);assert rate==24000 and samples.ndim==1
            manifest[lang][row['id']]={'clip':str(target.relative_to(PUBLIC)),'seconds':len(samples)/rate,'sha256':sha(target),'source':str(source.relative_to(MEDIA)),'caption':row[lang],'spoken':meta['spoken'],'settingsSha256':meta['settingsSha256'],'review':choice['note'],'reusedFromV1':False}
    (PUBLIC/'orbital-v2/narration.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    (DOC/'orbital-narration.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print('Selected',sum(len(v) for v in manifest.values()),'takes; reused',sum(x.get('reusedFromV1',False) for v in manifest.values() for x in v.values()))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['generate','check','select']);parser.add_argument('--lang',choices=['en','zh']);parser.add_argument('--take',default='');parser.add_argument('--model',default='small');parser.add_argument('--only');args=parser.parse_args();only=set(args.only.split(',')) if args.only else None
    if args.action=='select':select()
    elif args.action=='generate':generate(args.lang,args.take,only)
    else:check(args.lang,args.take,args.model,only)
