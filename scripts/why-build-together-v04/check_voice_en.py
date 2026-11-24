"""Transcribe each local take and retain checks for review, without cloud calls."""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import subprocess
import numpy as np
import soundfile as sf

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'out/why-build-together-v04'
MODEL=Path.home()/'.cache/whisper/ggml-small-q5_1.bin'
rows=json.loads((OUT/'script-en.json').read_text())['rows']
folder=OUT/'audio/en/asr';folder.mkdir(parents=True,exist_ok=True)

def check(row):
    source=OUT/'audio/en/louise'/(row['id']+'.wav')
    a,sr=sf.read(source,dtype='float32')
    assert a.ndim==1 and len(a)>sr*.5 and np.isfinite(a).all()
    assert .005<float(np.abs(a).max())<.98
    dest=folder/(row['id']+'.wav'); prefix=folder/row['id']
    subprocess.run(['ffmpeg','-v','error','-y','-i',str(source),'-ar','16000','-ac','1',str(dest)],check=True)
    if not prefix.with_suffix('.txt').exists():
        run=subprocess.run(['/opt/homebrew/bin/whisper-cli','-m',str(MODEL),'-f',str(dest),'-l','en','-otxt','-oj','-of',str(prefix),'-ng','-t','2','-np'],capture_output=True,text=True)
        prefix.with_suffix('.log').write_text(run.stderr);run.check_returncode()
    result=dict(id=row['id'],expected=row['text'],recognized=prefix.with_suffix('.txt').read_text().strip(),
                seconds=len(a)/sr,peak=float(np.abs(a).max()),finite_nonempty=True)
    print(json.dumps(result,ensure_ascii=False),flush=True)
    return result

with ThreadPoolExecutor(max_workers=2) as pool:
    results=list(pool.map(check,rows))
(OUT/'audio/en/qa.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
