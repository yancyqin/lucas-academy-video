"""Canonical scoring plus a stronger Whisper pass for uncertain completed takes.

Number spelling and simplified/traditional forms are normalized without discarding
numbers. Raw transcripts are retained. No speech is silently approved by a score.
"""
from pathlib import Path
import argparse
import difflib
import json
import re
import time
from opencc import OpenCC

ROOT=Path(__file__).resolve().parents[2]
MEDIA=ROOT.parent/'lucas-academy-media'
REPORT=ROOT/'out/family-ai-lab-01/narration/check.json'
OUT=ROOT/'out/family-ai-lab-01/narration/medium.json'
CC=OpenCC('t2s')


def canonical(text,lang):
    text=CC.convert(text).lower()
    en={'0.37':'zero point three seven','1957':'nineteen fifty seven','1958':'nineteen fifty eight','1969':'nineteen sixty nine','1986':'nineteen eighty six','2012':'twenty twelve','2017':'twenty seventeen','1949':'nineteen forty nine','419':'four hundred and nineteen','400':'four hundred','86':'eighty six','20':'twenty','10':'ten','8':'eight','7':'seven','6':'six','5':'five','4':'four','3':'three','2':'two','1':'one','0':'zero'}
    zh={'0.37':'零点三七','1957':'一九五七','1958':'一九五八','1969':'一九六九','1986':'一九八六','2012':'二零一二','2017':'二零一七','1949':'一九四九','1000':'一千','419':'四百一十九','400':'四百','300':'三百','86':'八十六','10':'十','8':'八','7':'七','6':'六','5':'五','4':'四','3':'三','2':'二','1':'一','0':'零'}
    for value,word in sorted((en if lang=='en' else zh).items(),key=lambda v:-len(v[0])):
        text=re.sub(r'(?<!\d)'+re.escape(value)+r'(?!\d)',word,text)
    if lang=='zh':
        def cn(n):
            n=int(n)
            if n<10:return '零一二三四五六七八九'[n]
            if n<100:return ('' if n//10==1 else cn(n//10))+'十'+(cn(n%10) if n%10 else '')
            if n<1000:return cn(n//100)+'百'+(('零' if n%100<10 else '')+cn(n%100) if n%100 else '')
            if n<10000:return cn(n//1000)+'千'+(('零' if n%1000<100 else '')+cn(n%1000) if n%1000 else '')
            return str(n)
        text=re.sub(r'\d+',lambda m:cn(m[0]),text)
    if lang=='en':text=re.sub(r'\ba[.\s]+eye\b','ai',text)
    else:
        text=re.sub(r'\bax\b|\bx\b','艾克斯',text)
    return ''.join(c for c in text if c.isalnum())


def score(expected,heard,lang):
    return difflib.SequenceMatcher(None,canonical(expected,lang),canonical(heard,lang)).ratio()


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--watch',action='store_true');parser.add_argument('--only');parser.add_argument('--threshold',type=float,default=.88);args=parser.parse_args()
    only=set(args.only.split(',')) if args.only else None
    import torch
    torch.set_num_threads(2)
    import whisper
    model=None
    result=json.loads(OUT.read_text()) if OUT.exists() else {}
    while True:
        raw=json.loads(REPORT.read_text()) if REPORT.exists() else {}
        for key,value in raw.items():
            if only and key not in only:continue
            lang,name=key.split('/',1)
            value['canonicalScore']=round(score(value['expected'],value['heard'],lang),3)
            if value['canonicalScore']>=args.threshold or result.get(key,{}).get('sha256')==value['sha256']:continue
            if model is None:model=whisper.load_model('medium',device='cpu')
            wav=MEDIA/f'outputs/louise/{lang}/family-ai-lab-01-v1/s1.10/{name}.wav'
            heard=model.transcribe(str(wav),language=lang,condition_on_previous_text=False,fp16=False,
                initial_prompt='感知机。艾克斯，Claude Fable，GPT Astra，千问。' if lang=='zh' else 'Perceptron, Rosenblatt, Claude Fable, GPT Astra, Qwen, Lucas Academy.')
            text=heard['text'].strip();ratio=score(value['expected'],text,lang)
            result[key]={'sha256':value['sha256'],'model':'medium','expected':value['expected'],'heard':text,'canonicalScore':round(ratio,3)}
            OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
            print(f'{key} {ratio:.3f} | {text}',flush=True)
        if not args.watch or len(raw)>=152:break
        time.sleep(10)


if __name__=='__main__':main()
