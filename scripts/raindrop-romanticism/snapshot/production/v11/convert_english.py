"""Native-length local Louise conversion of the revised English question."""
import hashlib,json,sys
from pathlib import Path
P=Path(__file__).resolve().parent
sys.path.insert(0,str(P.parent/'v9'))
from convert_all import engine_for,read,convert,asr
from lucas_media.joke import save_wav

def main():
    source=json.loads((P/'n002-english/serena/generation.json').read_text())
    folder=P/'n002-english/louise';folder.mkdir(parents=True,exist_ok=True)
    file=folder/'voice.wav';receipt=folder/'receipt.json'
    if not receipt.exists():
        engine=engine_for('louise/en')
        voice,rate=convert(engine,read(source['file']),folder,2026112132)
        save_wav(file,voice,rate)
        plan=json.loads((P.parent/'v10/full-plan.json').read_text())
        old=next(i for i in plan['voice_fragments'] if i['id']=='n002-01' and i['language']=='en')
        meta=dict(old,text=source['text'],spoken_text=source['text'],text_sha256=source['text_sha256'],
            file=str(file),seconds=voice.shape[1]/rate,source_file=source['file'],source_sha256=source['sha256'],
            sha256=hashlib.sha256(file.read_bytes()).hexdigest(),speed=1.0,
            method='Native local Qwen3-TTS performance → padded local Louise English conversion',new_cloud_requests=0)
        receipt.write_text(json.dumps(meta,indent=2))
    meta=json.loads(receipt.read_text());meta['asr']=asr(file,'en')
    receipt.write_text(json.dumps(meta,indent=2));print(json.dumps(meta,indent=2),flush=True)

if __name__=='__main__':main()
