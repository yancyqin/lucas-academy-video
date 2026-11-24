"""Check the supplied recording independently, then align its approved script."""
from pathlib import Path
import argparse,hashlib,json,re,subprocess
from difflib import SequenceMatcher

ROOT=Path(__file__).resolve().parents[2]
DATA=ROOT.parent/'lucas-academy-video-data/why-build-together-20261122/english-pause-alignment-v06'
SOURCE=DATA/'source/with-ai-english-narration-louise.wav'

def normalize(text):
    text=text.lower()
    # Whisper may format the unchanged spoken range as "$2,000 or $3,000".
    # Preserve the raw transcript; compare that currency notation semantically.
    text=re.sub(r'\$\s*2,?000\s+or\s+\$\s*3,?000', 'two or three thousand dollars', text)
    for number,words in [('2,000','two thousand'),('3,000','three thousand'),('5,000','five thousand'),('2000','two thousand'),('3000','three thousand'),('5000','five thousand')]:text=text.replace(number,words)
    text=re.sub(r'\b2\b','two',text)
    return re.findall(r"[a-z]+(?:'[a-z]+)?",text)

def transcribe(source=SOURCE,folder_name='asr',report_name='transcript-check.json'):
    folder=DATA/folder_name;folder.mkdir(exist_ok=True)
    wav=folder/'source-16k.wav';prefix=folder/'source'
    subprocess.run(['ffmpeg','-v','error','-y','-i',str(source),'-ar','16000','-ac','1',str(wav)],check=True)
    if not prefix.with_suffix('.txt').exists():
        run=subprocess.run(['/opt/homebrew/bin/whisper-cli','-m',str(Path.home()/'.cache/whisper/ggml-small-q5_1.bin'),
            '-f',str(wav),'-l','en','-otxt','-oj','-of',str(prefix),'-ng','-t','3','-np'],capture_output=True,text=True)
        prefix.with_suffix('.log').write_text(run.stderr);run.check_returncode()
    text=prefix.with_suffix('.txt').read_text().strip()
    rows=json.loads((DATA/'script.json').read_text())['rows'];expected=' '.join(r['spoken_text'] for r in rows)
    a,b=normalize(expected),normalize(text);comparison=SequenceMatcher(None,a,b)
    differences=[{'operation':op,'expected':' '.join(a[i:j]),'recognized':' '.join(b[x:y])} for op,i,j,x,y in comparison.get_opcodes() if op!='equal']
    report={'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'expected':expected,'recognized':text,
        'normalization_note':'Compare number spellings and the equivalent currency range $2,000 or $3,000 semantically; the raw transcript is preserved unchanged.',
        'normalized_similarity':comparison.ratio(),'exact_normalized_words':a==b,'differences':differences}
    (DATA/report_name).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report,ensure_ascii=False,indent=2))

def align():
    import torch,stable_whisper
    torch.set_num_threads(4)
    rows=json.loads((DATA/'script.json').read_text())['rows']
    text=' '.join(r['spoken_text'] for r in rows)
    model=stable_whisper.load_model('small.en',device='cpu')
    result=model.align(str(SOURCE),text,language='en',regroup=False,fast_mode=True,verbose=None)
    assert result is not None
    words=[dict(word=w.word,start=w.start,end=w.end) for segment in result.segments for w in segment.words]
    tight=lambda s:re.sub(r'\s','',s)
    assert tight(''.join(w['word'] for w in words))==tight(text)
    grouped=[];cursor=0
    plan=json.loads((DATA/'picture-timeline-v04.json').read_text())
    byid={s['id']:s for s in plan['scenes']}
    for row in rows:
        group=[];joined=''
        while tight(joined)!=tight(row['spoken_text']):
            assert cursor<len(words),row['id']
            w=words[cursor];cursor+=1;group.append(w);joined+=w['word']
            assert tight(row['spoken_text']).startswith(tight(joined)),(row['id'],joined)
        picture=byid[row['id']]
        grouped.append({'id':row['id'],'text':row['spoken_text'],'start':group[0]['start'],'end':group[-1]['end'],
            'span':group[-1]['end']-group[0]['start'],'picture_start':picture['start_frame']/30,
            'picture_seconds':picture['frames']/30,'words':group})
    assert cursor==len(words)
    report={'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'method':'Local Whisper-small.en forced alignment; independent ASR separately recorded','rows':grouped}
    (DATA/'aligned-source.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps([{k:v for k,v in r.items() if k!='words'} for r in grouped],ensure_ascii=False,indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('stage',choices=['transcribe','align','transcribe-mix']);args=parser.parse_args()
    if args.stage=='transcribe-mix':transcribe(DATA/'intro-en-mix.wav','asr-mix','mixed-transcript-check.json')
    elif args.stage=='transcribe':transcribe()
    else:align()
