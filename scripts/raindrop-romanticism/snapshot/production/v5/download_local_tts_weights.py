"""Verified, resumable range downloads from official model and package hosts."""
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
import os
from pathlib import Path
import time
import urllib.request

P=Path(__file__).resolve().parent
ROOT=P/'auditions/2026-11-20-alternative-providers'
MEDIA=P.parents[3]/'lucas-academy-media'


def read_json(url):
    with urllib.request.urlopen(url,timeout=30) as response:return json.load(response)


def download(url,target,size,sha256,workers=64,chunk_bytes=4*1024*1024):
    target.parent.mkdir(parents=True,exist_ok=True)
    if target.is_file() and target.stat().st_size==size:
        if hashlib.file_digest(target.open('rb'),'sha256').hexdigest()==sha256:
            print('Verified existing',target.name,flush=True);return
    partial=target.with_suffix(target.suffix+'.partial')
    journal=target.with_suffix(target.suffix+'.ranges.json')
    done=set(json.loads(journal.read_text()) if journal.exists() else [])
    chunk=chunk_bytes
    fd=os.open(partial,os.O_RDWR|os.O_CREAT,0o600)
    os.ftruncate(fd,size)
    # Resolve the official download redirect once. Repeating Hub metadata
    # redirects for every chunk needlessly slows large model downloads.
    with urllib.request.urlopen(urllib.request.Request(url,headers={'Range':'bytes=0-0'}),timeout=60) as response:
        transfer_url=response.geturl()
        response.read(1)
    def part(index):
        start=index*chunk;end=min(size,start+chunk)-1
        for attempt in range(3):
            try:
                request=urllib.request.Request(transfer_url,headers={'Range':f'bytes={start}-{end}'})
                with urllib.request.urlopen(request,timeout=90) as response:
                    expected=f'bytes {start}-{end}/{size}'
                    assert response.status==206 and response.headers.get('Content-Range')==expected
                    data=response.read()
                assert len(data)==end-start+1
                written=0
                while written<len(data):written+=os.pwrite(fd,data[written:],start+written)
                return index
            except Exception:
                if attempt==2:raise
                time.sleep(1+attempt*2)
    ranges=list(range((size+chunk-1)//chunk));last=time.monotonic()
    print('Downloading',target.name,'MB',round(size/1e6), 'workers',workers,flush=True)
    try:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures=[pool.submit(part,i) for i in ranges if i not in done]
            for future in as_completed(futures):
                done.add(future.result())
                journal.write_text(json.dumps(sorted(done)))
                if time.monotonic()-last>12:
                    print(target.name,'completed',len(done),'of',len(ranges),'chunks',flush=True);last=time.monotonic()
        os.fsync(fd)
    finally:os.close(fd)
    with partial.open('rb') as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
    assert digest==sha256,(target.name,'checksum mismatch')
    partial.replace(target)
    print('Checksum verified',target.name,flush=True)


def main():
    # Download the large MLX wheel separately to make the isolated setup quicker.
    package=read_json('https://pypi.org/pypi/mlx-metal/0.32.4/json')
    wheel=next(x for x in package['urls'] if x['filename']=='mlx_metal-0.32.4-py3-none-macosx_26_0_arm64.whl')
    download(wheel['url'],ROOT/'wheels'/wheel['filename'],wheel['size'],wheel['digests']['sha256'])
    descriptor=json.loads((ROOT/'qwen-local-model.json').read_text())
    model=descriptor['model'];revision=descriptor['revision']
    files=read_json(f'https://huggingface.co/api/models/{model}/tree/{revision}?recursive=true')
    destination=MEDIA/'models/Qwen3-TTS-12Hz-1.7B-CustomVoice-8bit'
    for entry in files:
        if entry['type']!='file' or entry['path'].endswith('.md') or entry['path'].startswith('.'):continue
        url=f'https://huggingface.co/{model}/resolve/{revision}/'+entry['path']
        target=destination/entry['path']
        if entry.get('lfs'):
            download(url,target,entry['size'],entry['lfs']['oid'])
        elif not target.is_file():
            target.parent.mkdir(parents=True,exist_ok=True)
            with urllib.request.urlopen(url,timeout=60) as response:raw=response.read()
            assert len(raw)==entry['size']
            target.write_bytes(raw)
    descriptor['local_path']=str(destination)
    (ROOT/'qwen-local-model.json').write_text(json.dumps(descriptor,indent=2))
    print('All local weights ready',destination,flush=True)


if __name__=='__main__':main()
