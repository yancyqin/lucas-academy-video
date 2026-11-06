"""Incremental Whisper check of both owner-authorized narration tracks.

Use .venv-align/bin/python. --watch checks completed WAVs while TTS continues.
Raw transcripts, word timestamps and hashes are preserved; scores are review aids.
"""
from pathlib import Path
import argparse
import difflib
import hashlib
import json
import re
import time
import os
import fcntl

ROOT = Path(__file__).resolve().parents[2]
MEDIA = ROOT.parent / "lucas-academy-media"
REVISION = json.loads((ROOT/'scripts/family-ai-lab-01/script.json').read_text()).get('revision',1)
REPORT = ROOT / (f"out/family-ai-lab-01/narration/v{REVISION}/check.json" if REVISION>=2 else "out/family-ai-lab-01/narration/check.json")


def norm(text):
    return ''.join(c for c in text.lower() if c.isalnum())


def save_report(result):
    # Retakes can finish in either language at the same time. Merge under a
    # file lock so an older in-memory report cannot discard another check.
    with REPORT.with_suffix('.lock').open('w') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        latest=json.loads(REPORT.read_text()) if REPORT.exists() else {}
        latest.update(result)
        temp=REPORT.with_name(f'.{REPORT.name}.{os.getpid()}.tmp')
        temp.write_text(json.dumps(latest,ensure_ascii=False,indent=2)+'\n')
        temp.replace(REPORT)
        result.clear();result.update(latest)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--watch',action='store_true')
    parser.add_argument('--model',default='small')
    parser.add_argument('--only')
    parser.add_argument('--take',default='')
    args=parser.parse_args()
    import torch
    torch.set_num_threads(2)
    import whisper
    model=whisper.load_model(args.model,device='cpu')
    REPORT.parent.mkdir(parents=True,exist_ok=True)
    result=json.loads(REPORT.read_text()) if REPORT.exists() else {}
    original=ROOT/'out/family-ai-lab-01/narration/check.json'
    previous=json.loads(original.read_text()) if REVISION>=2 and original.exists() else {}
    only=set(args.only.split(',')) if args.only else None
    while True:
        waiting=0
        for lang in ['en','zh']:
            plan=ROOT/f'docs/family-ai-lab-01/voice.{lang}.json'
            if not plan.exists():waiting+=1;continue
            for line in json.loads(plan.read_text()):
                if only and line['id'] not in only:continue
                name=line['id']+(f'.take{args.take}' if args.take else '')
                folder=MEDIA/f'outputs/louise/{lang}/family-ai-lab-01-v{line.get("revision",1)}/s1.10'
                wav=folder/(name+'.wav');meta=folder/(name+'.json')
                if not wav.exists() or not meta.exists():waiting+=1;continue
                key=f'{lang}/{name}'
                digest=hashlib.sha256(wav.read_bytes()).hexdigest()
                if key in result and result[key].get('sha256')==digest and result[key].get('model')==args.model:continue
                reused=json.loads(meta.read_text()).get('reused')
                prior=next(((k,v) for k,v in previous.items() if v.get('sha256')==digest),None) if reused else None
                if prior and args.model==prior[1]['model']:
                    result[key]={**prior[1],'reusedTranscriptFrom':prior[0],'expected':reused['spoken']}
                    save_report(result)
                    print('Reused hash-verified transcript',key,flush=True)
                    continue
                heard=model.transcribe(str(wav),language=lang,condition_on_previous_text=False,fp16=False,word_timestamps=True,
                    initial_prompt='Perceptron, Rosenblatt, Hebb, Claude Fable, GPT Astra, Qwen, Lucas Academy.' if lang=='en' else '普通话。感知机，罗森布拉特，赫布，卢卡斯学院。')
                text=heard['text'].strip()
                score=difflib.SequenceMatcher(None,norm(line['spoken']),norm(text)).ratio()
                result[key]={'sha256':digest,'model':args.model,'expected':line['spoken'],'heard':text,'score':round(score,3),
                    'segments':heard['segments'],'audioSeconds':json.loads(meta.read_text())['durationSeconds']}
                save_report(result)
                print(f'{key} {score:.3f} | {text}',flush=True)
        if not args.watch or waiting==0:break
        time.sleep(5)
    print('Checked',len(result),'takes:',REPORT,flush=True)


if __name__=='__main__':main()
