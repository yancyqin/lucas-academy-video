"""Align approved text to the finished takes using the cached local Whisper model."""
import json,re
from pathlib import Path
import torch,stable_whisper

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'out/why-build-together-v04'
rows=json.loads((OUT/'script-en.json').read_text())['rows']
torch.set_num_threads(4)
model=None
folder=OUT/'audio/en/aligned';folder.mkdir(exist_ok=True)
for row in rows:
    dest=folder/(row['id']+'.json')
    if dest.exists():continue
    if model is None:model=stable_whisper.load_model('small',device='cpu')
    source=OUT/'audio/en/louise'/(row['id']+'.wav')
    result=model.align(str(source),row['text'],language='en',regroup=False,fast_mode=True,verbose=None)
    assert result is not None,row['id']
    words=[dict(word=w.word,start=w.start,end=w.end) for seg in result.segments for w in seg.words]
    assert words and re.sub(r'\s','',''.join(w['word'] for w in words))==re.sub(r'\s','',row['text'])
    dest.write_text(json.dumps(dict(id=row['id'],text=row['text'],words=words,method='cached local Whisper-small forced alignment; content checked independently with Whisper.cpp'),ensure_ascii=False,indent=2)+'\n')
    print('Aligned',row['id'],len(words),'words',flush=True)
