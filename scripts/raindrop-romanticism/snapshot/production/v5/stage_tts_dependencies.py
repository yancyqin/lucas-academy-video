"""Stage the exact wheels already selected by pip, with official SHA256 checks."""
from concurrent.futures import ThreadPoolExecutor,as_completed
import hashlib
import json
from pathlib import Path
import re
import urllib.request
from packaging.utils import parse_wheel_filename

from download_local_tts_weights import read_json,download,ROOT,P


def stage(filename):
    name,version,_,_=parse_wheel_filename(filename)
    target=ROOT/'wheels'/filename
    metadata=target.with_suffix('.metadata.json')
    if metadata.exists():row=json.loads(metadata.read_text())
    else:
        for attempt in range(2):
            try:
                with urllib.request.urlopen(f'https://pypi.org/pypi/{name}/{version}/json',timeout=120) as response:data=json.load(response)
                row=next(x for x in data['urls'] if x['filename']==filename)
                metadata.write_text(json.dumps(row));break
            except Exception:
                if attempt==1:raise
    if target.is_file() and hashlib.sha256(target.read_bytes()).hexdigest()==row['digests']['sha256']:
        return filename
    download(row['url'],target,row['size'],row['digests']['sha256'],workers=16,chunk_bytes=512*1024)
    return filename


def main():
    text=(P/'checks/local-tts-install-wheel.log').read_text()
    files=sorted(set(re.findall(r'Downloading\s+([A-Za-z0-9_.+\-]+\.whl)',text)))
    assert len(files)>20,len(files)
    print('Staging exact dependency wheels',len(files),flush=True)
    errors=[]
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures={pool.submit(stage,f):f for f in files}
        for future in as_completed(futures):
            try:print('Ready',future.result(),flush=True)
            except Exception as e:
                errors.append(futures[future]);print('Failed',futures[future],type(e).__name__,flush=True)
    assert not errors,errors
    print('All dependency wheels staged',flush=True)


if __name__=='__main__':main()
