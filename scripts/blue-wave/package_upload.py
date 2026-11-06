#!/usr/bin/env python3
"""Verify and copy the approved film/cover pair into the owner's upload folder."""
import hashlib, json, pathlib, shutil, struct, subprocess
import walk
from notes import write_notes

DATA=pathlib.Path(walk.DATA)
FILM=DATA/"film"
OUT=pathlib.Path('/Users/yqin/Desktop/蓝色浪潮-上传')
TITLE='蓝色浪潮 | 肖邦 夜曲 Op. 9, No. 2'
TITLE_EN='Blue Wave | Chopin Nocturne Op. 9, No. 2'

def probe(path):
    return json.loads(subprocess.run(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(path)],capture_output=True,text=True,check=True).stdout)

def media_hash(path):
    return subprocess.run(['ffmpeg','-v','error','-i',str(path),'-map','0:v:0','-map','0:a:0','-c','copy','-f','streamhash','-hash','sha256','-'],capture_output=True,text=True,check=True).stdout

def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        while chunk:=f.read(4*1024*1024): h.update(chunk)
    return h.hexdigest()

def faststart(path):
    atoms=[]; size=path.stat().st_size; pos=0
    with path.open('rb') as f:
        while pos<size:
            f.seek(pos); n,kind=struct.unpack('>I4s',f.read(8))
            if n==1: n=struct.unpack('>Q',f.read(8))[0]
            if n==0: n=size-pos
            atoms.append(kind.decode('ascii')); pos+=n
    if atoms.index('moov')>atoms.index('mdat'): raise RuntimeError('Missing faststart: '+str(path))
    return atoms

def main():
    if not (FILM/'jobs/revision.done.json').exists(): raise RuntimeError('Revised film has not finished validation')
    OUT.mkdir(exist_ok=True)
    manifest={}
    for key,name in [('draft','蓝色浪潮-draft.mp4'),('final','蓝色浪潮.mp4'),('review','蓝色浪潮-review.mp4')]:
        path=FILM/name; validation=FILM/f'check/{key}-validation.json'
        v=json.loads(validation.read_text())
        if v['decoded_frames']!=8144 or v.get('wanderer_sequence')!='painting-muse-painting':
            raise RuntimeError('Missing verified painting -> Muse -> painting sequence: '+key)
        if v['unexpected_black_frames'] or v['potential_flashes'] or v['true_peak_dbtp']>-1: raise RuntimeError('Validation failed: '+key)
        # Metadata-only stream copy: verify both encoded streams are identical.
        if probe(path)['format'].get('tags',{}).get('title')!=TITLE:
            before=media_hash(path); tmp=path.with_name(path.stem+'.title.part.mp4')
            subprocess.run(['ffmpeg','-v','error','-y','-i',str(path),'-map','0','-c','copy','-metadata','title='+TITLE,'-movflags','+faststart',str(tmp)],check=True)
            if media_hash(tmp)!=before: raise RuntimeError('Metadata update changed encoded media')
            tmp.replace(path)
        meta=probe(path); vs=next(s for s in meta['streams'] if s['codec_type']=='video'); aud=next(s for s in meta['streams'] if s['codec_type']=='audio')
        if int(vs['nb_frames'])!=8144 or abs(float(vs['duration'])-float(aud['duration']))>1/30: raise RuntimeError('Packaged A/V duration mismatch')
        atoms=faststart(path)
        v.update({'bytes':path.stat().st_size,'duration':float(meta['format']['duration']),'video_duration':float(vs['duration']),'audio_duration':float(aud['duration']),'ffprobe':meta})
        validation.write_text(json.dumps(v,ensure_ascii=False,indent=2))
        render=path.with_suffix('.render.json')
        if render.exists():
            r=json.loads(render.read_text()); r.update({'size_bytes':path.stat().st_size,'ffprobe':meta}); render.write_text(json.dumps(r,ensure_ascii=False,indent=2))
        sha=digest(path)
        if key!='draft':
            dst=OUT/name; tmp=OUT/(path.stem+'.part.mp4'); shutil.copy2(path,tmp)
            if digest(tmp)!=sha: raise RuntimeError('Upload copy mismatch: '+str(dst))
            tmp.replace(dst)
        manifest[key]={'path':str(path),'desktop_path':str(OUT/name) if key!='draft' else None,'duration_s':v['duration'],'bytes':path.stat().st_size,'MiB':round(path.stat().st_size/1024**2,2),'resolution':v['resolution'],'frames':8144,'LUFS':v['lufs'],'true_peak_dBTP':v['true_peak_dbtp'],'faststart_verified':True,'sha256':sha,'title':TITLE,'atoms':atoms}
    write_notes()
    shutil.copy2(FILM/'NOTES.md',OUT/'NOTES.md')
    (OUT/'片名.txt').write_text(TITLE+'\n'+TITLE_EN+'\n\n曲目：肖邦《降 E 大调夜曲》，Op. 9, No. 2。\nNocturne in E-flat major, Op. 9, No. 2.\n')
    covers={}
    for lang in ['zh','en']:
        path=OUT/f'cover.{lang}.jpg'
        if not path.exists(): raise RuntimeError('Missing selected cover: '+str(path))
        covers[lang]={'path':str(path),'bytes':path.stat().st_size,'sha256':digest(path),'design':'A','work':'Op. 9, No. 2'}
    manifest['covers']=covers
    (FILM/'delivery.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
    print(json.dumps(manifest,ensure_ascii=False,indent=2),flush=True)

if __name__=='__main__': main()
