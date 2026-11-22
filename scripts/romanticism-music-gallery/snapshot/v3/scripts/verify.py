"""Verify the rendered media, musical program, and representative frames."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from html.parser import HTMLParser
from urllib.parse import unquote
import subprocess,json,numpy as np,concurrent.futures,math,hashlib
ROOT=Path(__file__).resolve().parents[1]
FF='/opt/homebrew/bin/ffmpeg';FP='/opt/homebrew/bin/ffprobe'
plan=json.loads((ROOT/'edit-plan.json').read_text())
master=ROOT/'exports/山海与人间-中英标签纯音乐版.mp4'
assert (ROOT/'checks/build-result.json').exists(),'Build is not complete'
files=[(master,plan['duration']),(ROOT/'exports/自然篇-肖邦-中英标签版.mp4',plan['tracks'][2]['end']),(ROOT/'exports/人间篇-贝多芬-中英标签版.mp4',plan['duration']-plan['tracks'][3]['start'])]
result={'files':[]}
for p,expected in files:
    probe=json.loads(subprocess.check_output([FP,'-v','error','-show_format','-show_streams','-show_chapters','-of','json',str(p)]))
    v=[s for s in probe['streams'] if s['codec_type']=='video'];a=[s for s in probe['streams'] if s['codec_type']=='audio']
    assert len(v)==len(a)==1 and (v[0]['width'],v[0]['height'],v[0]['r_frame_rate'])==(1920,1080,'24/1')
    duration=float(probe['format']['duration']);assert abs(duration-expected)<.1,(p,duration,expected)
    result['files'].append(dict(file=p.name,bytes=p.stat().st_size,duration=duration,width=1920,height=1080,fps=24,audio=a[0]['codec_name'],chapters=len(probe['chapters'])))
    if p==master:
        assert len(probe['chapters'])==5
        for c,t in zip(probe['chapters'],plan['tracks']):assert abs(float(c['start_time'])-t['start'])<.002
print('PROBES PASSED',flush=True)

# Decode the full exported video and audio, not just its metadata.
with (ROOT/'checks/master-decode.log').open('w') as err:
    subprocess.run([FF,'-hide_banner','-v','error','-i',str(master),'-map','0:v','-map','0:a','-f','null','-'],check=True,stderr=err,stdout=subprocess.DEVNULL)
assert not (ROOT/'checks/master-decode.log').read_text().strip()
result['full_master_decode']='passed'
print('FULL DECODE PASSED',flush=True)

def pcm(p):
    return np.frombuffer(subprocess.check_output([FF,'-hide_banner','-v','error','-i',str(p),'-map','0:a:0','-ac','1','-ar','8000','-f','f32le','-']),dtype='<f4')
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
    decoded,reference=list(pool.map(pcm,[master,ROOT.parent/'audio/complete-program.wav']))
length=min(len(decoded),len(reference));assert abs(len(decoded)-len(reference))<800
decoded=decoded[:length];reference=reference[:length]
correlations=[]
for t in plan['tracks']:
    lo=round((t['start']+.2)*8000);hi=min(length,round((t['end']-.1)*8000))
    x=decoded[lo:hi].astype('float64');y=reference[lo:hi].astype('float64')
    cor=float(np.dot(x,y)/(np.linalg.norm(x)*np.linalg.norm(y)))
    assert cor>.99,(t['id'],cor)
    assert hashlib.sha256(Path(t['file']).read_bytes()).hexdigest()==t['sha256']
    correlations.append(dict(track=t['id'],complete_track_correlation=cor,source_hash_verified=True))
result['audio_matches_complete_music_program']=correlations
result['audio_policy']='Exactly five complete instrumental recordings; no narration or source-video soundtrack.'
print('MUSIC PROGRAM PASSED',correlations,flush=True)

frames=ROOT/'checks/frames';frames.mkdir(exist_ok=True)
def frame(s):
    at=s['global_start']+min(7,s['seconds']/2);p=frames/(s['id']+'.jpg')
    subprocess.run([FF,'-hide_banner','-v','error','-y','-ss',str(at),'-i',str(master),'-frames:v','1',str(p)],check=True)
    im=Image.open(p).convert('RGB');pixels=np.asarray(im)
    assert pixels.std()>8,(s['id'],'unexpected empty frame')
    return p
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:paths=list(pool.map(frame,plan['shots']))
font=ImageFont.truetype('/System/Library/Fonts/STHeiti Medium.ttc',16)
contact=Image.new('RGB',(1920,math.ceil(len(paths)/5)*250),(11,18,20));d=ImageDraw.Draw(contact)
for i,(p,s) in enumerate(zip(paths,plan['shots'])):
    im=Image.open(p);im.thumbnail((380,214),Image.Resampling.LANCZOS);x=i%5*384;y=i//5*250
    contact.paste(im,(x+(384-im.width)//2,y));title=s['title']
    if len(title)>19:title=title[:18]+'…'
    n=int(s['global_start']);d.text((x+5,y+218),f'{n//60:02}:{n%60:02} {title}',font=font,fill=(223,224,207))
contact.save(ROOT/'checks/final-contact.jpg',quality=92)
result['representative_frames']=len(paths)

missing=[];refs=[]
class Links(HTMLParser):
    def handle_starttag(self,tag,attrs):
        for k,v in attrs:
            if k in ('href','src') and v and not v.startswith(('http:','https:','#','data:')):
                refs.append(v)
                if not (ROOT/unquote(v)).exists():missing.append(v)
links=Links();links.feed((ROOT/'preview.html').read_text());assert not missing,missing
result['local_links']={'count':len(refs),'missing':missing}
(ROOT/'checks/local-link-audit.json').write_text(json.dumps(result['local_links'],ensure_ascii=False,indent=2))
(ROOT/'checks/verified.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
print('VERIFIED',len(paths),'scenes',len(refs),'local links',flush=True)
