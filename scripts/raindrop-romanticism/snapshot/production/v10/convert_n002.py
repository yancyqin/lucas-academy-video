"""Padded local Fangfang conversion; native duration, no cloud requests."""
import hashlib,json,sys
from pathlib import Path
P=Path(__file__).resolve().parent
sys.path.insert(0,str(P.parent/'v9'))
from convert_all import engine_for,read,convert,asr
from lucas_media.joke import save_wav

def main():
    source=json.loads((P/'n002-retake/serena/generation.json').read_text())
    out=P/'n002-retake/fangfang';out.mkdir(parents=True,exist_ok=True)
    file=out/'voice.wav';receipt=out/'receipt.json'
    if not receipt.exists():
        engine=engine_for('fangfang/zh')
        voice,rate=convert(engine,read(source['file']),out,2026112123)
        save_wav(file,voice,rate)
        plan=json.loads((P.parent/'v9/full-plan.json').read_text())
        old=next(i for i in plan['voice_fragments'] if i['id']=='n002-01' and i['language']=='zh')
        meta=dict(old,text=source['text'],spoken_text=source['text'],
            text_sha256=hashlib.sha256(source['text'].encode()).hexdigest(),file=str(file),
            seconds=voice.shape[1]/rate,source_file=source['file'],source_sha256=source['sha256'],
            sha256=hashlib.sha256(file.read_bytes()).hexdigest(),speed=1.0,
            method='Native local Qwen3-TTS Serena performance → padded local Fangfang conversion',new_cloud_requests=0)
        receipt.write_text(json.dumps(meta,ensure_ascii=False,indent=2))
    meta=json.loads(receipt.read_text());meta['asr']=asr(file,'zh')
    receipt.write_text(json.dumps(meta,ensure_ascii=False,indent=2))
    print(json.dumps(meta,ensure_ascii=False,indent=2),flush=True)

if __name__=='__main__':main()
