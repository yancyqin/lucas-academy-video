from pathlib import Path
import hashlib
import importlib.util
import json

ROOT = Path(__file__).resolve().parents[2]
PUBLIC = ROOT/'public/science-shorts-20261105'
DOCS = ROOT/'docs/science-shorts'
OUT = ROOT/'out/science-shorts'
MEDIA = ROOT.parent/'lucas-academy-media'
SOURCE = json.loads((Path(__file__).parent/'script.json').read_text())
FPS = 30


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def module(name, path):
    spec=importlib.util.spec_from_file_location(name,path)
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result)
    return result


def values():
    data=module('family_numbers',ROOT/'scripts/family-ai-lab-01/build.py').numbers()
    # Read quantities from the preserved original round, then spell them for speech.
    data['train_n_zh']={419:'四百一十九'}[data['train_n']]
    data['pixel_n_zh']={400:'四百'}[data['pixel_n']]
    return data


def plans(lang):
    voice=module('family_speech',ROOT/'scripts/family-ai-lab-01/narrate.py')
    vals=values();result=[]
    for film,info in SOURCE['films'].items():
        for index,item in enumerate(info['lines']):
            caption=item[lang].format(**vals)
            spoken=item.get('spoken',{}).get(lang,caption)
            row={'film':film,'id':item['id'],'caption':caption,'spoken':voice.spoken_text(spoken,lang),
                 'voice':f'louise/{lang}','speed':1.1,'mode':'zero-shot-instruct',
                 'instruction':voice.OPENING_TONE[lang] if index<2 else voice.TONE[lang]}
            if item.get('reuseFamilyCue'):row['reuseFamilyCue']=item['reuseFamilyCue']
            row['settingsSha256']=hashlib.sha256(json.dumps(row,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
            result.append(row)
    return result


def take_dir(lang):
    return MEDIA/f'outputs/louise/{lang}/science-shorts-v1/s1.10'
