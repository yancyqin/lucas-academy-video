"""Freeze the owner's lesson inputs and derive every displayed code and guess."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
COURSE=ROOT.parent/'lucas-academy-ai'
PUBLIC=ROOT/'public/family-ai-lab-02'
DOC=ROOT/'docs/family-ai-lab-02'


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    PUBLIC.mkdir(parents=True,exist_ok=True);DOC.mkdir(parents=True,exist_ok=True)
    script=json.loads((Path(__file__).parent/'script.json').read_text())
    sources=[]
    assets=[('L1-beginner/course.md','source/course.md'),('courses/zero-and-one/index.html','source/lesson.html'),('assets/print/zero-and-one/1.jpg','curriculum/worksheet-front.jpg'),('assets/print/zero-and-one/2.jpg','curriculum/worksheet-back.jpg')]
    for name in ('red_apple_3d','banana_3d','grapes_3d','watermelon_3d'):assets.append((f'L1-beginner/media/{name}.png',f'curriculum/{name}.png'))
    for name in ('binary.html','lab.css','lab.js','math.js'):assets.append((f'assets/labs/{name}',f'lab/{name}'))
    for source,dest in assets:
        p=COURSE/source;d=PUBLIC/dest;d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,d)
        sources.append({'source':source,'path':dest,'sha256':sha(d)})
    live=PUBLIC/'source/live-lesson.html'
    if live.exists():sources.append({'source':script['source'],'path':'source/live-lesson.html','sha256':sha(live)})
    import qrcode
    qrcode.make(script['source'],box_size=12,border=4).save(PUBLIC/'qr.png')
    codes={letter:{'number':ord(letter),'bits':f'{ord(letter):08b}'} for letter in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'}
    assert codes['A']=={'number':65,'bits':'01000001'}
    assert ''.join(chr(int(codes[c]['bits'],2)) for c in 'PLAY')=='PLAY'
    path=[];remain=list(range(1,11))
    for threshold in (5,8,6,7):
        answer=7>threshold
        remain=[n for n in remain if (n>threshold)==answer]
        path.append({'threshold':threshold,'answer':answer,'remaining':remain[:]})
    assert [len(p['remaining']) for p in path]==[5,3,2,1] and remain==[7]
    def depth(items):
        if len(items)<=1:return 0
        threshold=8 if items==list(range(6,11)) else 6 if items==[6,7,8] else items[(len(items)-1)//2]
        return 1+max(depth([n for n in items if n<=threshold]),depth([n for n in items if n>threshold]))
    assert depth(list(range(1,11)))==4
    facts={'codes':codes,'message':'PLAY','messageBits':''.join(codes[c]['bits'] for c in 'PLAY'),'weights':[128,64,32,16,8,4,2,1],'patterns':{str(n):2**n for n in (1,2,3,4,8,10)},'boxPath':path,'worstCase':{'10':4,'1000':10},'fruitClues':{'apple':{'red':True,'visibleSeeds':False},'watermelon':{'red':True,'visibleSeeds':True},'banana':{'red':False,'visibleSeeds':False},'grapes':{'red':False,'visibleSeeds':False}},'scope':'ASCII is seven-bit, zero-padded here to eight bits. Not all characters fit in a byte. Pipe/beads are a story and agreed two-symbol game, not a claim about the capacity of real pipes.'}
    facts['fruitQuestionPaths']={'apple':'10','watermelon':'11','banana':'01','grapes':'00'}
    assert sorted(facts['fruitQuestionPaths'].values())==['00','01','10','11']
    (PUBLIC/'facts.json').write_text(json.dumps(facts,ensure_ascii=False,indent=2)+'\n')
    provenance={'courseUrl':script['source'],'curriculumCommit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=COURSE,text=True).strip(),'ownerStory':'L1-beginner/course.md, opening paragraph','adaptation':'Mia, Leo, the invitation, two treehouses and gift are new story details. Shared code table, bit/byte, number guessing and fruit clues follow the owner lesson. The perceptron extension is left for the preceding film.','sources':sources,'references':[{'url':'https://www.rfc-editor.org/rfc/rfc20','use':'7-bit ASCII embedded in an 8-bit byte with high bit zero; A=65.'},{'url':'https://www.csunplugged.org/en/topics/binary-numbers/whats-it-all-about/','use':'Two states represent a bit; eight bits group into a byte.'}]}
    (DOC/'sources.json').write_text(json.dumps(provenance,ensure_ascii=False,indent=2)+'\n')
    (DOC/'facts.json').write_text(json.dumps(facts,ensure_ascii=False,indent=2)+'\n')
    for lang in ('zh','en'):
        head='# '+('完整中文剧情稿' if lang=='zh' else 'Complete English story script')+'\n\n'+script['workingTitle'][lang]+'\n\n'
        body=''
        for i,name in enumerate(script['scenes'],1):
            body+=f'## S{i} · {name}\n\n'
            for row in script['lines']:
                if row['scene']==i:body+=f'**{row["id"]}** · {row["visual"]}\n\n{row[lang]}\n\n'
        (DOC/f'{lang}-script.md').write_text(head+body)
    print('Prepared',len(assets),'source assets,',len(script['lines']),'cue pairs; ASCII/message/guessing verified')


if __name__=='__main__':main()
