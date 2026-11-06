"""New concise narration, with exact approved family-intro takes reused by hash."""
import argparse
import json
import os
import shutil
import sys
from common import ROOT, PUBLIC, DOCS, MEDIA, plans, take_dir, sha


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--lang',required=True,choices=['en','zh']);parser.add_argument('--only');parser.add_argument('--take',default='');args=parser.parse_args()
    DOCS.mkdir(parents=True,exist_ok=True);folder=take_dir(args.lang);folder.mkdir(parents=True,exist_ok=True)
    rows=plans(args.lang)
    (DOCS/f'voice.{args.lang}.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
    family=json.loads((ROOT/'public/family-ai-lab-01/narration.json').read_text())
    only=set(args.only.split(',')) if args.only else None
    todo=[]
    for row in rows:
        if only and row['id'] not in only:continue
        name=row['id']+(f'.take{args.take}' if args.take else '')
        wav=folder/(name+'.wav');meta=wav.with_suffix('.json')
        if wav.exists() and meta.exists():
            assert json.loads(meta.read_text())['settingsSha256']==row['settingsSha256'],name
            continue
        if row.get('reuseFamilyCue') and not args.take:
            original=family[args.lang][row['reuseFamilyCue']]
            assert original['caption']==row['caption']
            source=ROOT/'public/family-ai-lab-01'/original['clip'];assert sha(source)==original['sha256']
            shutil.copy2(source,wav)
            meta.write_text(json.dumps({**row,'durationSeconds':original['seconds'],'sampleRate':original['sampleRate'],'reused':original['source'],'sha256':sha(wav)},ensure_ascii=False,indent=2)+'\n')
            print('Reused checked take',args.lang,row['id'],flush=True)
        else:todo.append((row,wav,meta))
    if not todo:return
    os.chdir(MEDIA);sys.path.insert(0,str(MEDIA/'src'))
    import torch
    torch.set_num_threads(3);torch.set_num_interop_threads(2)
    from modelscope import snapshot_download
    normalizer=snapshot_download('pengzhendong/wetext',local_files_only=True)
    import wetext.wetext as frontend
    frontend.snapshot_download=lambda _:normalizer
    from lucas_media.cosyvoice_engine import CosyVoiceEngine
    from lucas_media.joke import DEFAULT_PEAK_DBFS,add_peak_headroom,save_wav
    engine=CosyVoiceEngine(MEDIA/f'profiles/louise/{args.lang}/profile.json')
    for index,(row,wav,meta) in enumerate(todo,1):
        audio,rate,_=engine.synthesize(row['spoken'],target_language=args.lang,mode=row['mode'],instruction=row['instruction'],speed=row['speed'])
        seconds=audio.shape[1]/rate;assert seconds>.5,row['id']
        save_wav(wav,add_peak_headroom(audio,peak_dbfs=DEFAULT_PEAK_DBFS),rate)
        meta.write_text(json.dumps({**row,'durationSeconds':seconds,'sampleRate':rate,'sha256':sha(wav)},ensure_ascii=False,indent=2)+'\n')
        print(f'{args.lang} {index}/{len(todo)} {row["id"]} {seconds:.2f}s',flush=True)


if __name__=='__main__':main()
