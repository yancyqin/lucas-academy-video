"""Transcribe newly completed short takes; carry approved reused takes by WAV hash."""
import argparse
import difflib
import json
import time
from common import ROOT, DOCS, plans, take_dir, sha


def norm(text):
    return ''.join(char for char in text.lower() if char.isalnum())


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--watch',action='store_true');parser.add_argument('--model',default='small');parser.add_argument('--only');parser.add_argument('--take',default='');args=parser.parse_args()
    import torch
    torch.set_num_threads(2)
    import whisper
    model=whisper.load_model(args.model,device='cpu')
    DOCS.mkdir(parents=True,exist_ok=True);path=DOCS/f'asr-{args.model}.json'
    result=json.loads(path.read_text()) if path.exists() else {}
    family=json.loads((ROOT/'docs/family-ai-lab-01/narration-qa.json').read_text())['sentences']
    only=set(args.only.split(',')) if args.only else None
    while True:
        waiting=0
        for lang in ('en','zh'):
            for row in plans(lang):
                if only and row['id'] not in only:continue
                name=row['id']+(f'.take{args.take}' if args.take else '')
                wav=take_dir(lang)/(name+'.wav');meta=wav.with_suffix('.json');key=f'{lang}/{name}'
                if not wav.exists() or not meta.exists():waiting+=1;continue
                digest=sha(wav)
                if result.get(key,{}).get('sha256')==digest:continue
                previous=next((item for item in family if item['sha256']==digest),None)
                if previous and args.model=='small':
                    result[key]={'sha256':digest,'expected':row['spoken'],'heard':previous['whisperMedium'] or previous['whisperSmall'],
                                 'reusedCheckedTake':previous['key'],'model':'previous-approved','seconds':json.loads(meta.read_text())['durationSeconds']}
                else:
                    heard=model.transcribe(str(wav),language=lang,condition_on_previous_text=False,fp16=False,word_timestamps=True,
                        initial_prompt='Perceptron, Claude Fable, GPT Astra, optogenetics, encoding, decoding.' if lang=='en' else '普通话。感知机，编码，解码，光遗传学。')
                    result[key]={'sha256':digest,'expected':row['spoken'],'heard':heard['text'].strip(),'model':args.model,
                                 'seconds':json.loads(meta.read_text())['durationSeconds'],'segments':heard['segments']}
                result[key]['similarity']=round(difflib.SequenceMatcher(None,norm(row['spoken']),norm(result[key]['heard'])).ratio(),3)
                path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
                print(key,result[key]['similarity'],result[key]['heard'],flush=True)
        if not args.watch or not waiting:break
        time.sleep(5)


if __name__=='__main__':main()
