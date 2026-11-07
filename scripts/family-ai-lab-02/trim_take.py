"""Create an immutable edited take, preserving the original and edit receipt."""
from pathlib import Path
import argparse
import hashlib
import json
import numpy as np
import soundfile as sf

ROOT=Path(__file__).resolve().parents[2]


def main():
    p=argparse.ArgumentParser();p.add_argument('--lang',choices=['en','zh'],required=True);p.add_argument('--id',required=True);p.add_argument('--start',type=float,default=0);p.add_argument('--end',type=float,required=True);p.add_argument('--source-take',default='');p.add_argument('--take',default='2');p.add_argument('--rebind-current-text',action='store_true');p.add_argument('--reason',required=True);args=p.parse_args()
    folder=ROOT.parent/f'lucas-academy-media/outputs/louise/{args.lang}/family-ai-lab-02-v1/s1.10'
    source=folder/(args.id+(f'.take{args.source_take}' if args.source_take else '')+'.wav');dest=folder/(args.id+'.take'+args.take+'.wav')
    assert not dest.exists(),'Edited takes are immutable: '+str(dest)
    samples,rate=sf.read(source,dtype='float32');start=round(args.start*rate);stop=round(args.end*rate)
    assert 0<=start<stop<=len(samples)
    output=samples[start:stop].copy();fade=min(len(output),round(.01*rate));output[-fade:]*=np.linspace(1,0,fade)
    sf.write(dest,output,rate,subtype=sf.info(source).subtype)
    meta=json.loads(source.with_suffix('.json').read_text())
    original_spoken=meta['spoken']
    if args.rebind_current_text:
        from narrate import plan
        meta.update(next(row for row in plan(args.lang) if row['id']==args.id))
    meta['durationSeconds']=len(output)/rate
    meta['edit']={'source':source.name,'sourceSha256':hashlib.sha256(source.read_bytes()).hexdigest(),'originalSpoken':original_spoken,'startSeconds':start/rate,'endSeconds':stop/rate,'fadeOutSeconds':.01,'reason':args.reason}
    dest.with_suffix('.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
    print('Created',dest.name,len(output)/rate,'seconds; original retained')


if __name__=='__main__':main()
