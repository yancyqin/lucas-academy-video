"""Edit the actual captures into independently usable chapters and the complete film."""
import argparse, hashlib, json, subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from classical_mix import render_music

ROOT=Path('/Users/yqin/repo/playground/lucas-academy-video-data/curiosity-builds-20261118/v2')
PLAN=json.loads(Path(__file__).with_name('plan.json').read_text())
FONT='/System/Library/Fonts/Supplemental/Arial.ttf'
OUT=ROOT/'delivery'; EDIT=ROOT/'edit'; EDIT.mkdir(exist_ok=True)
def run(args):
    subprocess.run(args,check=True)
def duration(p):
    return float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',str(p)]))
def overlay(project,clip,index):
    im=Image.new('RGBA',(1920,1080)); d=ImageDraw.Draw(im)
    rules=bool(clip.get('rule'))
    if not rules and project['id'] not in ('cube','chameleon','coder','bible'):
        for y in range(180):d.line((0,y,1920,y),fill=(5,10,18,int(180*(1-y/180)**1.4)))
        d.text((64,35),f'{index+1:02d}  /  {project["name"]}',font=ImageFont.truetype(FONT,35),fill='#f7efdf')
        u=project['url'];f=ImageFont.truetype(FONT,24);w=d.textlength(u,font=f)
        d.text((1856-w,40),u,font=f,fill='#b9deea')
    for y in range(920,1080):d.line((0,y,1920,y),fill=(5,10,18,int(170*((y-920)/160)**.7)))
    caption=clip['caption'];font=ImageFont.truetype(FONT,33)
    if d.textlength(caption,font=font)>1770:font=ImageFont.truetype(FONT,31)
    d.text((64,1000),caption,font=font,fill='#fff6e6',stroke_width=1,stroke_fill='#080e19')
    if rules:
        d.rounded_rectangle((1120,65,1860,340),radius=18,fill=(8,14,25,230),outline='#f5bc68',width=2)
        d.text((1150,92),clip['rule']+' RULE',font=ImageFont.truetype(FONT,36),fill='#f5bc68')
        for j,line in enumerate(clip['detail']):d.text((1150,155+j*49),line,font=ImageFont.truetype(FONT,28),fill='#f5f1e6')
    path=EDIT/(clip['file']+'-overlay.png');im.save(path);return path
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
                fade=max(0,seconds-.16)
                hold=min(3,seconds) if c.get('rule') else min(2.5,seconds)
                filters=f'[0:v]scale=1920:1080:flags=lanczos,fps=30,setsar=1[v];[v][1:v]overlay=0:0:enable=\'lt(t,{hold})\',format=yuv420p[out]'
                run(['ffmpeg','-y','-v','error','-ss',str(start),'-i',str(source),'-i',str(png),'-filter_complex',filters,'-map','[out]','-t',str(seconds),'-an','-c:v','libx264','-preset','fast','-crf','18','-video_track_timescale','15360',str(dest)])
            parts.append(dest);length+=seconds
        chapter=EDIT/(f'{i+1:02d}-'+p['id']+'-picture.mp4');concat(parts,chapter)
        chapters.append((i,p,chapter,length));all_parts.append(chapter)
        sheet.append({'chapter':i+1,'project':p['name'],'start':round(cursor,3),'seconds':round(length,3),'url':p['url']});cursor+=length
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
