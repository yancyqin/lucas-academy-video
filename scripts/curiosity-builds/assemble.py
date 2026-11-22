"""Edit the actual captures into independently usable chapters and the complete film."""
import argparse, json, subprocess, wave
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT=Path('/Users/yqin/repo/playground/lucas-academy-video-data/curiosity-builds-20261118')
PLAN=json.loads(Path(__file__).with_name('plan.json').read_text())
FONT='/System/Library/Fonts/Supplemental/Arial.ttf'
OUT=ROOT/'delivery'; EDIT=ROOT/'edit'; EDIT.mkdir(exist_ok=True)
def run(args):
    subprocess.run(args,check=True)
def duration(p):
    return float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',str(p)]))
def overlay(project,clip,index):
    im=Image.new('RGBA',(1920,1080)); d=ImageDraw.Draw(im)
    rules=clip['file'] in ('chess-comeback','chess-rockfall')
    if not rules and project['id'] not in ('cube','chameleon','coder','bible'):
        for y in range(180):d.line((0,y,1920,y),fill=(5,10,18,int(180*(1-y/180)**1.4)))
        d.text((64,35),f'{index+1:02d}  /  {project["name"]}',font=ImageFont.truetype(FONT,35),fill='#f7efdf')
        u=project['url'];f=ImageFont.truetype(FONT,24);w=d.textlength(u,font=f)
        d.text((1856-w,40),u,font=f,fill='#b9deea')
    for y in range(920,1080):d.line((0,y,1920,y),fill=(5,10,18,int(170*((y-920)/160)**.7)))
    caption=clip['caption'];font=ImageFont.truetype(FONT,35)
    if d.textlength(caption,font=font)>1770:font=ImageFont.truetype(FONT,31)
    d.text((64,1000),caption,font=font,fill='#fff6e6',stroke_width=1,stroke_fill='#080e19')
    path=EDIT/(clip['file']+'-overlay.png');im.save(path);return path
def concat(paths,dest):
    if dest.exists() and dest.stat().st_mtime>=max(p.stat().st_mtime for p in paths):return
    listing=dest.with_suffix('.concat.txt');listing.write_text(''.join(f"file '{p}'\n" for p in paths))
    run(['ffmpeg','-y','-v','error','-f','concat','-safe','0','-i',str(listing),'-vf','setpts=N/(30*TB),fps=30,format=yuv420p','-an','-c:v','libx264','-preset','fast','-crf','18','-video_track_timescale','15360','-movflags','+faststart',str(dest)])
def synth(seconds,path):
    # An original, sample-free instrumental bed. No speech, external songs or downloaded audio.
    sr=32000;N=int((seconds+.2)*sr);a=np.zeros(N,dtype=np.float32)
    beat=60/96;chords=[[60,64,67,71],[57,60,64,67],[53,57,60,64],[55,59,62,69]]
    rng=np.random.default_rng(181126)
    def tone(start,note,length,amp,kind='pluck'):
        n=int(length*sr);t=np.arange(n,dtype=np.float32)/sr;freq=440*2**((note-69)/12)
        if kind=='pad':env=np.minimum(t/.7,1)*np.minimum((length-t)/.9,1);v=(np.sin(2*np.pi*freq*t)+.15*np.sin(4*np.pi*freq*t))*env
        else:env=(1-np.exp(-t*70))*np.exp(-t*2.5);v=(np.sin(2*np.pi*freq*t)+.22*np.sin(4*np.pi*freq*t)+.07*np.sin(6*np.pi*freq*t))*env
        at=int(start*sr);end=min(N,at+n)
        if at<end:a[at:end]+=v[:end-at]*amp
    for bar in range(int(seconds/(beat*4))+1):
        chord=chords[bar%4];s=bar*beat*4
        for note in chord:tone(s,note,beat*4+.6,.018,'pad')
        tone(s,chord[0]-24,beat*2,.11)
        for k in range(8):
            note=chord[[0,2,1,3,2,1,3,2][k]]+12
            tone(s+k*beat/2,note,1.2,.075 if k%2==0 else .045)
        if bar%2==0:tone(s+beat*3,chord[2]+24,1.8,.025)
    a=np.tanh(a*1.3);a*=np.minimum(np.arange(N)/sr/1.5,1)*np.minimum((N-np.arange(N))/sr/3,1)
    stereo=np.stack((a,np.roll(a,int(sr*.009))),axis=1);stereo=np.clip(stereo,-.95,.95)
    with wave.open(str(path),'wb') as w:w.setnchannels(2);w.setsampwidth(2);w.setframerate(sr);w.writeframes((stereo*32767).astype('<i2').tobytes())
def add_music(picture,dest,music,offset=0):
    if dest.exists() and dest.stat().st_mtime>=max(picture.stat().st_mtime,music.stat().st_mtime):return
    run(['ffmpeg','-y','-v','error','-i',str(picture),'-ss',str(offset),'-i',str(music),'-map','0:v:0','-map','1:a:0','-c:v','copy','-af','loudnorm=I=-21:TP=-2:LRA=7','-c:a','aac','-b:a','192k','-shortest','-movflags','+faststart',str(dest)])
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--available',action='store_true');args=parser.parse_args()
    chapters=[];sheet=[];missing=[];all_parts=[ROOT/'builds/opening.mp4'];cursor=3.
    for i,p in enumerate(PLAN['projects']):
        required=[ROOT/'captures'/(c['file']+'.mp4') for c in p['clips']]
        if any(not x.exists() or x.stat().st_size<1000 for x in required):missing.append(p['id']);continue
        parts=[ROOT/'builds'/(p['id']+'.mp4')];length=7.2
        for c,source in zip(p['clips'],required):
            dest=EDIT/(c['file']+'.mp4');seconds=min(c['seconds'],duration(source))
            if not dest.exists() or dest.stat().st_mtime<source.stat().st_mtime:
                png=overlay(p,c,i)
                fade=max(0,seconds-.16)
                filters=f'[0:v]scale=1920:1080:flags=lanczos,fps=30,setsar=1[v];[v][1:v]overlay=0:0:enable=\'lt(t,4.5)\',fade=t=in:st=0:d=0.16,fade=t=out:st={fade:.3f}:d=0.16,format=yuv420p[out]'
                run(['ffmpeg','-y','-v','error','-i',str(source),'-i',str(png),'-filter_complex',filters,'-map','[out]','-t',str(seconds),'-an','-c:v','libx264','-preset','fast','-crf','18','-video_track_timescale','15360',str(dest)])
            parts.append(dest);length+=seconds
        chapter=EDIT/(f'{i+1:02d}-'+p['id']+'-picture.mp4');concat(parts,chapter)
        chapters.append((i,p,chapter,length));all_parts.append(chapter)
        sheet.append({'chapter':i+1,'project':p['name'],'start':round(cursor,3),'seconds':round(length,3),'url':p['url']});cursor+=length
        print('Edited',p['id'],round(length,2),'s',flush=True)
    if missing and not args.available:raise RuntimeError('Missing actual project footage: '+', '.join(missing))
    total=cursor+4;music=EDIT/'original-instrumental.wav'
    if not music.exists() or abs(duration(music)-total-.2)>.05:synth(total,music)
    for i,p,picture,length in chapters:
        dest=OUT/f'{i+1:02d}-{p["id"]}.en.no-voice.mp4';add_music(picture,dest,music)
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
