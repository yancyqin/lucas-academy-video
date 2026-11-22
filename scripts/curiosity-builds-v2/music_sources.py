"""Restore only the three previously selected Commons recordings needed by this revision."""
from pathlib import Path
import json,hashlib,urllib.request,urllib.parse,subprocess,shutil
R=Path('/Users/yqin/repo/playground/lucas-academy-video-data')
OUT=R/'curiosity-builds-20261118/v2/music'
moz=json.loads((R/'mozart-sketchbook/music/sources.json').read_text())['05']
bach=json.loads((R/'journey/music/sources.json').read_text())[0]
clair=next(x for x in json.loads((R/'debussy-impressions/music/sources.json').read_text()) if x['key']=='clair')
items=[('mozart',moz),('bach',bach),('debussy',clair)]
sources={}
for key,s in items:
    name=urllib.parse.unquote(s['page'].split('/wiki/File:')[1]).replace(' ','_')
    h=hashlib.md5(name.encode()).hexdigest()
    url='https://upload.wikimedia.org/wikipedia/commons/'+h[0]+'/'+h[:2]+'/'+urllib.parse.quote(name,safe='')
    dest=OUT/(key+Path(name).suffix)
    if not dest.exists():
        print('Restoring',key,flush=True)
        req=urllib.request.Request(url,headers={'User-Agent':'LucasAcademyFilm/1.0 (https://lucasacademy.org)'})
        part=dest.with_suffix(dest.suffix+'.part')
        with urllib.request.urlopen(req,timeout=60) as response,part.open('wb') as f:shutil.copyfileobj(response,f)
        part.replace(dest)
    sha=hashlib.sha256(dest.read_bytes()).hexdigest()
    if s.get('sha256'):assert sha==s['sha256'],key+' original hash changed'
    wav=OUT/(key+'.wav')
    if not wav.exists():subprocess.run(['ffmpeg','-y','-v','error','-i',str(dest),'-ar','48000','-ac','2','-c:a','pcm_s24le',str(wav)],check=True)
    sources[key]={**s,'restored_url':url,'restored_sha256':sha,'wav':str(wav)}
    print('Ready',key,flush=True)
chopin=next(x for x in json.loads((R/'romanticism-music-gallery/sources/credits.json').read_text())['music'] if '9 No. 2' in x['title'])
src=R/'romanticism-music-gallery'/chopin['local_file'];wav=OUT/'chopin.wav'
if not wav.exists():subprocess.run(['ffmpeg','-y','-v','error','-i',str(src),'-ar','48000','-ac','2','-c:a','pcm_s24le',str(wav)],check=True)
sources['chopin']={**chopin,'wav':str(wav)}
(OUT/'sources.json').write_text(json.dumps(sources,ensure_ascii=False,indent=2)+'\n')
