"""Independently transcribe the trial takes, with caches keyed to audio hashes."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from difflib import SequenceMatcher
import argparse,hashlib,json,re,subprocess
import numpy as np
import soundfile as sf

ROOT=Path(__file__).resolve().parents[2]
TRIAL=ROOT.parent/'lucas-academy-video-data/why-build-together-20261122/cosyvoice-en-trial-20261123'
MODEL=Path.home()/'.cache/whisper/ggml-small-q5_1.bin'

def words(text):
    text=text.lower().replace('2,000','two thousand').replace('5,000','five thousand')
    return re.findall(r"[a-z]+(?:'[a-z]+)?",text)

def check(row):
    source=TRIAL/'takes'/(row['id']+'.wav')
    data,sr=sf.read(source,dtype='float32');assert data.ndim==1 and np.isfinite(data).all()
    assert .4<len(data)/sr<45 and .005<float(np.abs(data).max())<.95
    digest=hashlib.sha256(source.read_bytes()).hexdigest()
    folder=TRIAL/'asr'/digest[:12];folder.mkdir(parents=True,exist_ok=True)
    wav=folder/(row['id']+'.wav');prefix=folder/row['id']
    if not prefix.with_suffix('.txt').exists():
        subprocess.run(['ffmpeg','-v','error','-y','-i',str(source),'-ar','16000','-ac','1',str(wav)],check=True)
        run=subprocess.run(['/opt/homebrew/bin/whisper-cli','-m',str(MODEL),'-f',str(wav),'-l','en','-otxt','-oj','-of',str(prefix),'-ng','-t','2','-np'],capture_output=True,text=True)
        prefix.with_suffix('.log').write_text(run.stderr);run.check_returncode()
    text=prefix.with_suffix('.txt').read_text().strip()
    a,b=words(row['spoken_text']),words(text)
    ratio=SequenceMatcher(None,a,b).ratio()
    result={'id':row['id'],'expected':row['spoken_text'],'recognized':text,'seconds':len(data)/sr,
        'word_similarity':round(ratio,4),'exact_normalized_words':a==b,'peak':float(np.abs(data).max()),
        'audio_sha256':digest,'needs_review':ratio<.97,'finite_nonempty':True}
    print(json.dumps(result,ensure_ascii=False),flush=True)
    return result

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--only');parser.add_argument('--available',action='store_true');args=parser.parse_args()
    rows=json.loads((TRIAL/'script.json').read_text())['rows']
    if args.only:rows=[r for r in rows if r['id']==args.only]
    if args.available:rows=[r for r in rows if (TRIAL/'takes'/(r['id']+'.json')).exists()]
    with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(check,rows))
    output=TRIAL/('qa-partial.json' if args.available else ('qa-'+args.only+'.json' if args.only else 'qa.json'))
    output.write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')

if __name__=='__main__':main()
