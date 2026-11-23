"""Generate the confirmed script with the already accepted MiniMax performance voices."""
from concurrent.futures import ThreadPoolExecutor,wait,FIRST_COMPLETED
from datetime import datetime,timezone
import hashlib
import json
import netrc
from pathlib import Path
import subprocess
import threading
import time
import urllib.request

P=Path(__file__).resolve().parent
BASE='https://api.minimax.cn/v1/t2a_v2'
VOICES={'zh':'Chinese (Mandarin)_Wise_Women','en':'English_captivating_female1'}
LOCK=threading.Lock()
NEXT_START=0.0


def make_one(item,secret):
    global NEXT_START
    folder=P/'minimax-sources'/item['language']/(item['id']+'-'+item['text_sha256'][:12])
    folder.mkdir(parents=True,exist_ok=True)
    audio=folder/'original.mp3';receipt=folder/'receipt.json'
    if receipt.exists():
        old=json.loads(receipt.read_text())
        if old['state']=='success' and audio.is_file():
            assert old['text_sha256']==item['text_sha256']
            return dict(**item,source=str(audio),duration=old['duration'],usage_characters=old['usage_characters'])
        if old['state']=='rejected' and old.get('base_resp',{}).get('status_code')==1002:
            (folder/('rate-limit-rejection-'+datetime.now(timezone.utc).strftime('%H%M%S')+'.json')).write_text(receipt.read_text())
        else:
            raise RuntimeError(f'Inspect previous state before retry: {folder}')
    spoken=item['text'].lstrip('，, \n')
    body=dict(model='speech-2.8-hd',text=spoken,stream=False,output_format='hex',
              language_boost='Chinese' if item['language']=='zh' else 'English',
              voice_setting=dict(voice_id=VOICES[item['language']],speed=1.0,vol=1.0,pitch=0),
              audio_setting=dict(sample_rate=32000,bitrate=128000,format='mp3',channel=1))
    (folder/'request.json').write_text(json.dumps(dict(item=item,body=body),ensure_ascii=False,indent=2))
    with LOCK:
        delay=max(0,NEXT_START-time.monotonic());NEXT_START=max(time.monotonic(),NEXT_START)+7.0
    if delay:time.sleep(delay)
    receipt.write_text(json.dumps(dict(state='sending',text_sha256=item['text_sha256'],at=datetime.now(timezone.utc).isoformat())))
    try:
        request=urllib.request.Request(BASE,data=json.dumps(body).encode(),
            headers={'Authorization':'Bearer '+secret,'Content-Type':'application/json'})
        with urllib.request.urlopen(request,timeout=150) as response:result=json.load(response)
    except Exception as error:
        receipt.write_text(json.dumps(dict(state='unknown',text_sha256=item['text_sha256'],error=type(error).__name__)))
        raise
    status=result.get('base_resp',{}).get('status_code')
    if status!=0:
        receipt.write_text(json.dumps(dict(state='rejected',text_sha256=item['text_sha256'],base_resp=result.get('base_resp')),ensure_ascii=False,indent=2))
        raise RuntimeError(str(result.get('base_resp')))
    raw=bytes.fromhex(result['data']['audio']);assert len(raw)>1000
    audio.write_bytes(raw)
    duration=float(subprocess.check_output(['/opt/homebrew/bin/ffprobe','-v','error','-show_entries','format=duration',
                                         '-of','default=nw=1:nk=1',str(audio)]))
    assert .4<duration<80,(item['id'],duration)
    info=result.get('extra_info',{})
    usage=info.get('usage_characters',0)
    receipt.write_text(json.dumps(dict(state='success',text_sha256=item['text_sha256'],duration=duration,
        usage_characters=usage,sha256=hashlib.sha256(raw).hexdigest(),extra_info=info),ensure_ascii=False,indent=2))
    return dict(**item,source=str(audio),duration=duration,usage_characters=usage)


def main():
    plan=json.loads((P/'synthesis-plan.json').read_text())
    approved=json.loads((P/'approved-script.json').read_text())
    assert plan['source_sha256']==approved['source_sha256']
    assert hashlib.sha256((P/'压力焦虑肖邦浪漫-已确认中文文案.docx').read_bytes()).hexdigest()==approved['source_sha256']
    items=plan['requests']
    status_file=P/'generation-status.json'
    status_file.write_text(json.dumps(dict(state='running',total=len(items))))
    estimated=sum(len(x['text'])+sum('\u3400'<=c<='\u9fff' for c in x['text']) for x in items)
    assert estimated<25000,'Recheck text volume before billing.'
    secret=netrc.netrc(str(Path.home()/'.netrc')).authenticators('api.minimaxi.com')[2]
    results=[];queue=iter(items);pool=ThreadPoolExecutor(max_workers=2);active={}
    print('Confirmed bilingual narration units',len(items),'estimated CNY',round(estimated*3.5/10000,2),flush=True)
    def add():
        try:item=next(queue)
        except StopIteration:return
        active[pool.submit(make_one,item,secret)]=item
    add();add()
    try:
        while active:
            completed,_=wait(active,return_when=FIRST_COMPLETED)
            for future in completed:
                item=active.pop(future);results.append(future.result())
                (P/'minimax-progress.json').write_text(json.dumps(dict(completed=len(results),total=len(items),
                    last_id=item['id'],last_language=item['language']),ensure_ascii=False,indent=2))
                if len(results)%10==0 or len(results)<=2:print('Generated',len(results),'of',len(items),flush=True)
                add()
    except Exception as error:
        for future in active:future.cancel()
        pool.shutdown(wait=True,cancel_futures=True)
        status_file.write_text(json.dumps(dict(state='failed',error=str(error)[:400]),ensure_ascii=False,indent=2))
        raise
    else:pool.shutdown(wait=True)
    ordered={(x['language'],x['id']):x for x in results}
    results=[ordered[(x['language'],x['id'])] for x in items]
    (P/'minimax-source-manifest.json').write_text(json.dumps(dict(source_sha256=approved['source_sha256'],
        model='speech-2.8-hd',voice_ids=VOICES,items=results,
        usage_characters=sum(x['usage_characters'] for x in results)),ensure_ascii=False,indent=2))
    print('Both languages generated and cached; full film untouched.',flush=True)
    status_file.write_text(json.dumps(dict(state='complete',total=len(items))))


if __name__=='__main__':main()
