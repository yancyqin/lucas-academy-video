"""Edit the actual captures into independently usable chapters and the complete film."""
import argparse, hashlib, json, subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from classical_mix import render_music

ROOT=Path('/Users/yqin/repo/playground/lucas-academy-video-data/curiosity-builds-20261118/v4')
PLAN=json.loads(Path(__file__).with_name('plan.json').read_text())
FONT='/System/Library/Fonts/Supplemental/Arial.ttf'
OUT=ROOT/'delivery'; EDIT=ROOT/'edit'; EDIT.mkdir(exist_ok=True)
def run(args):
    subprocess.run(args,check=True)
def duration(p):
    return float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',str(p)]))
def overlay(project,clip,index):
    # Large content labels only. No brand headings, URLs, running captions, or footers.
    im=Image.new('RGBA',(1920,1080));d=ImageDraw.Draw(im)
    if clip.get('rule'):
        d.rectangle((1080,0,1920,1080),fill='#080e19')
        title=clip['rule'];d.text((1140,250),title,font=ImageFont.truetype(FONT,70),fill='#f5bc68')
        lines=['Over 5 points behind?','Earn points. Revive a piece.','Each piece returns once.'] if title=='COMEBACK' else ['Rocks may hit the leader.','Kings and queens stay safe.','Level score? No rocks.']
        for j,line in enumerate(lines):d.text((1140,410+j*100),line,font=ImageFont.truetype(FONT,52),fill='#f5f1e6')
    elif project['id']=='coder':
        d.rectangle((1080,0,1920,1080),fill='#080e19')
        words=['Coder','Arena'] if clip['file']=='coder-arena' else ['Monthly','Ranking']
        for j,word in enumerate(words):d.text((1170,405+j*105),word,font=ImageFont.truetype(FONT,90),fill='#f5f1e6')
    path=EDIT/(clip['file']+'-overlay.png');im.save(path);return path

def picture_filter(project,clip):
    n=clip['file'];fit='scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=0x080e19'
    if clip.get('rule'):
        crop='crop=836:836:224:122' if clip['rule']=='COMEBACK' else 'crop=722:722:280:178'
        return f'[0:v]{crop},scale=1080:1080,pad=1920:1080:0:0:color=0x080e19,fps=30,setsar=1[v]'
    if project['id']=='coder':
        crop='crop=750:750:370:180' if n=='coder-arena' else 'crop=688:688:18:18'
        return f'[0:v]{crop},scale=1080:1080,pad=1920:1080:0:0:color=0x080e19,fps=30,setsar=1[v]'
    if n=='chameleon-paint':
        return '[0:v]split=2[a][b];[a]crop=750:970:140:60,scale=960:1080:force_original_aspect_ratio=increase,crop=960:1080[left];[b]crop=550:830:910:180,scale=960:1080:force_original_aspect_ratio=increase,crop=960:1080[right];[left][right]hstack,fps=30,setsar=1[v]'
    if n=='chameleon-seek':
        crop='crop=iw:ih-130:0:60'
    elif project['id']=='bible':
        return "[0:v]crop=1640:400:140:'if(lt(t,5),500,400)',scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=0xf2ecd8,fps=30,setsar=1[v]"
    elif project['id']=='cube':
        return f'[0:v]crop=1200:1000:100:80,format=rgb24,drawbox=x=0:y=0:w=220:h=110:color=0x050a0f:t=fill,drawbox=x=0:y=910:w=320:h=90:color=0x050a0f:t=fill,drawbox=x=1000:y=910:w=200:h=90:color=0x050a0f:t=fill,{fit},fps=30,setsar=1[v]'
    elif project['id']=='roller' and n!='roller-entry':
        crop='crop=iw:ih-200:0:0'
    elif n in ('vangogh-room','chess-play'):
        crop='crop=iw:ih-90:0:0'
    else:crop='null'
    return f'[0:v]{crop},{fit},fps=30,setsar=1[v]'

def concat(paths,dest):
    # Decode the independently encoded clips before joining. Demuxer concatenation
    # can discard frames when Remotion and FFmpeg inputs have different time bases.
    receipt=ROOT/'records'/(dest.stem+'.concat-filter.json')
    token=hashlib.sha256(json.dumps([(str(p),p.stat().st_mtime_ns,p.stat().st_size) for p in paths]).encode()).hexdigest()
    if dest.exists() and receipt.exists() and json.loads(receipt.read_text())['digest']==token:return
    frames=[int(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=nb_frames','-of','csv=p=0',str(p)]).strip().split(b',')[0]) for p in paths]
    inputs=[]
    for p in paths:inputs+=['-threads','1','-i',str(p)]
    filters=';'.join(f'[{i}:v]setpts=N/(30*TB),fps=30,settb=AVTB,setsar=1[v{i}]' for i in range(len(paths)))
    filters+=';'+''.join(f'[v{i}]' for i in range(len(paths)))+f'concat=n={len(paths)}:v=1:a=0,format=yuv420p[out]'
    run(['ffmpeg','-y','-v','error',*inputs,'-filter_complex_threads','2','-filter_complex',filters,'-map','[out]','-an','-c:v','libx264','-threads','6','-preset','fast','-crf','18','-video_track_timescale','15360','-movflags','+faststart',str(dest)])
    actual=int(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=nb_frames','-of','csv=p=0',str(dest)]).strip().split(b',')[0])
    assert actual==sum(frames),(dest,actual,sum(frames))
    receipt.write_text(json.dumps({'digest':token,'input_frames':frames,'output_frames':actual},indent=2)+'\n')
def add_music(picture,dest,music,offset=0):
    if dest.exists() and dest.stat().st_mtime>=max(picture.stat().st_mtime,music.stat().st_mtime):return
    run(['ffmpeg','-y','-v','error','-i',str(picture),'-ss',str(offset),'-i',str(music),'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','192k','-shortest','-movflags','+faststart',str(dest)])
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--available',action='store_true');args=parser.parse_args()
    chapters=[];sheet=[];missing=[];all_parts=[ROOT/'builds/opening.mp4'];cursor=3.
    for i,p in enumerate(PLAN['projects']):
        required=[ROOT/'captures'/(c['file']+'.mp4') for c in p['clips']]
        if any(not x.exists() or x.stat().st_size<1000 for x in required):missing.append(p['id']);continue
        parts=[ROOT/'builds'/(p['id']+'.mp4')];length=7.2
        for c,source in zip(p['clips'],required):
            dest=EDIT/(c['file']+'.mp4');start=c.get('start',0);seconds=min(c['seconds'],duration(source)-start)
            if not dest.exists() or dest.stat().st_mtime<source.stat().st_mtime:
                png=overlay(p,c,i)
                filters=picture_filter(p,c)+';[v][1:v]overlay=0:0,format=yuv420p[out]'
                run(['ffmpeg','-y','-v','error','-ss',str(start),'-i',str(source),'-i',str(png),'-filter_complex',filters,'-map','[out]','-t',str(seconds),'-an','-c:v','libx264','-preset','fast','-crf','18','-video_track_timescale','15360',str(dest)])
            parts.append(dest);length+=seconds
        chapter=EDIT/(f'{i+1:02d}-'+p['id']+'-picture.mp4');concat(parts,chapter)
        chapters.append((i,p,chapter,length));all_parts.append(chapter)
        sheet.append({'chapter':i+1,'id':p['id'],'project':p['name'],'start':round(cursor,3),'seconds':round(length,3),'url':p['url']});cursor+=length
        print('Edited',p['id'],round(length,2),'s',flush=True)
    if missing and not args.available:raise RuntimeError('Missing actual project footage: '+', '.join(missing))
    total=cursor+PLAN['ending_seconds'];music=render_music(PLAN,sheet,total)
    for (i,p,picture,length),chapter_info in zip(chapters,sheet):
        dest=OUT/f'{i+1:02d}-{p["id"]}.en.no-voice.mp4';add_music(picture,dest,music,chapter_info['start'])
    if not missing:
        all_parts.append(ROOT/'builds/ending.mp4');picture=OUT/'curiosity-builds.en.silent.mp4';concat(all_parts,picture)
        add_music(picture,OUT/'curiosity-builds.en.no-voice.mp4',music)
        (ROOT/'records/chapters.json').write_text(json.dumps(sheet,indent=2))
        metadata=EDIT/'chapters.ffmeta';lines=[';FFMETADATA1','title=What Can Curiosity Build?','artist=Lucas Academy Team','language=eng']
        for item in sheet:lines+=['[CHAPTER]','TIMEBASE=1/1000',f'START={round(item["start"]*1000)}',f'END={round((item["start"]+item["seconds"])*1000)}','title='+item['project']]
        metadata.write_text('\n'.join(lines)+'\n')
        final=OUT/'curiosity-builds.en.no-voice.mp4';temp=OUT/'curiosity-builds.en.chaptered.mp4'
        run(['ffmpeg','-y','-v','error','-i',str(final),'-i',str(metadata),'-map_metadata','1','-map_chapters','1','-codec','copy','-movflags','+faststart',str(temp)]);temp.replace(final)
        print('Completed film:',duration(final),'seconds',flush=True)
    else:print('Still waiting for:',', '.join(missing),flush=True)
if __name__=='__main__':main()
