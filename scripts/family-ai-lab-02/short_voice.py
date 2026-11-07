"""Isolated short-film voice project using the established Louise pipeline."""
from pathlib import Path
import argparse,json
import orbital_voice as voice

voice.SCRIPT=Path(__file__).with_name('short-script.json')
voice.BASELINE=voice.PUBLIC/'orbital-v2/narration.json'
voice.SERIES='family-ai-lab-02-short'
voice.SUBDIR='orbital-v2/short'
voice.PREFIX='short'
voice.REUSE_FLAG='reusedFromFull'
voice.DOC=voice.DOC/'short'
voice.DOC.mkdir(parents=True,exist_ok=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['generate','check','select']);p.add_argument('--lang',choices=['en','zh']);p.add_argument('--take',default='');p.add_argument('--model',default='small');p.add_argument('--only');a=p.parse_args();only=set(a.only.split(',')) if a.only else None
    if a.action=='generate':voice.generate(a.lang,a.take,only)
    elif a.action=='check':voice.check(a.lang,a.take,a.model,only)
    else:voice.select()
