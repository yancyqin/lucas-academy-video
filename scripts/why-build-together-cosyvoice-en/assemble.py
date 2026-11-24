"""Join validated CosyVoice takes into a voice-only audition at natural speed."""
from pathlib import Path
import hashlib,json,shutil,subprocess
import numpy as np
import soundfile as sf

ROOT=Path(__file__).resolve().parents[2]
TRIAL=ROOT.parent/'lucas-academy-video-data/why-build-together-20261122/cosyvoice-en-trial-20261123'

def main():
    rows=json.loads((TRIAL/'script.json').read_text())['rows']
    qa=json.loads((TRIAL/'qa.json').read_text())
    assert len(qa)==len(rows)==12
    chunks=[];timeline=[];rate=24000;cursor=round(.15*rate)
    chunks.append(np.zeros(cursor,dtype='float32'))
    for i,row in enumerate(rows):
        path=TRIAL/'takes'/(row['id']+'.wav')
        data,sr=sf.read(path,dtype='float32');assert sr==rate and data.ndim==1
        record=next(q for q in qa if q['id']==row['id'])
        assert record['audio_sha256']==hashlib.sha256(path.read_bytes()).hexdigest()
        assert not record['needs_review'],record
        assert np.isfinite(data).all()
        timeline.append({'id':row['id'],'start':cursor/rate,'seconds':len(data)/rate,'text':row['spoken_text']})
        chunks.append(data);cursor+=len(data)
        gap=round((.55 if i<len(rows)-1 else .35)*rate)
        chunks.append(np.zeros(gap,dtype='float32'));cursor+=gap
    data=np.concatenate(chunks);assert np.isfinite(data).all()
    peak=float(np.abs(data).max());assert .005<peak<.95
    out=TRIAL/'with-ai.cosyvoice-english-audition.wav'
    sf.write(out,data,rate,subtype='PCM_24')
    mp3=out.with_suffix('.mp3')
    subprocess.run(['ffmpeg','-v','error','-y','-i',str(out),'-c:a','libmp3lame','-b:a','192k',
        '-metadata','title=With AI, from Curiosity to Product - CosyVoice English audition',str(mp3)],check=True)
    for path in [out,mp3]:
        run=subprocess.run(['ffmpeg','-v','error','-i',str(path),'-f','null','-'],capture_output=True,text=True,check=True)
        assert not run.stderr.strip(),run.stderr
    report={'status':'complete','model':'local Fun-CosyVoice3-0.5B','method':'Direct zero-shot TTS',
        'voice':'Louise / English reference','script_unchanged':True,'takes':12,'seconds':len(data)/rate,
        'sample_rate':rate,'channels':1,'peak':peak,'speed':1.0,'time_stretch':False,
        'new_cloud_requests':0,'music':False,'youtube_video_modified':False,'timeline':timeline,
        'files':[{'path':str(p),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in [out,mp3]]}
    (TRIAL/'delivery.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    exported=ROOT/'output/audio';exported.mkdir(parents=True,exist_ok=True)
    for path in [out,mp3]:shutil.copy2(path,exported/path.name)
    print(json.dumps({k:v for k,v in report.items() if k!='timeline'},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
