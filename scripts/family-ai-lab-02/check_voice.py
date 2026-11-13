"""Incremental ASR evidence. Scores never approve narration by themselves."""
from pathlib import Path
import argparse
import difflib
import hashlib
import json
import os
import fcntl
import time

ROOT=Path(__file__).resolve().parents[2]
MEDIA=ROOT.parent/'lucas-academy-media'


def norm(s):return ''.join(c for c in s.lower() if c.isalnum())


def save_report(path,report):
    with path.with_suffix('.lock').open('w') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        current=json.loads(path.read_text()) if path.exists() else {}
        current.update(report)
        temp=path.with_name(f'.{path.name}.{os.getpid()}.tmp')
        temp.write_text(json.dumps(current,ensure_ascii=False,indent=2)+'\n');temp.replace(path)
        report.clear();report.update(current)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--watch',action='store_true');parser.add_argument('--model',default='small');parser.add_argument('--only');parser.add_argument('--lang',choices=['en','zh']);parser.add_argument('--take',default='');args=parser.parse_args()
    import torch
    torch.set_num_threads(2)
    import whisper
    model=whisper.load_model(args.model,device='cpu')
    output=ROOT/f'out/family-ai-lab-02/narration/{args.model}.json';output.parent.mkdir(parents=True,exist_ok=True)
    report=json.loads(output.read_text()) if output.exists() else {}
    only=set(args.only.split(',')) if args.only else None
    while True:
        waiting=0
        for lang in ([args.lang] if args.lang else ['en','zh']):
            plan=ROOT/f'docs/family-ai-lab-02/voice.{lang}.json'
            if not plan.exists():waiting+=1;continue
            for row in json.loads(plan.read_text()):
                if only and row['id'] not in only:continue
                name=row['id']+(f'.take{args.take}' if args.take else '')
                wav=MEDIA/f'outputs/louise/{lang}/family-ai-lab-02-v1/s1.10/{name}.wav';meta=wav.with_suffix('.json')
                if not wav.exists() or not meta.exists():waiting+=1;continue
                digest=hashlib.sha256(wav.read_bytes()).hexdigest();key=f'{lang}/{name}'
                if report.get(key,{}).get('sha256')==digest:continue
                heard=model.transcribe(str(wav),language=lang,condition_on_previous_text=False,fp16=False,word_timestamps=True)
                text=heard['text'].strip()
                report[key]={'sha256':digest,'model':args.model,'expected':row['spoken'],'heard':text,'score':round(difflib.SequenceMatcher(None,norm(row['spoken']),norm(text)).ratio(),3),'segments':heard['segments'],'seconds':json.loads(meta.read_text())['durationSeconds']}
                save_report(output,report)
                print(f'{key} {report[key]["score"]:.3f} | {text}',flush=True)
        if not args.watch or not waiting:break
        time.sleep(8)
    print('Checked',len(report),'candidates:',output,flush=True)


if __name__=='__main__':main()
