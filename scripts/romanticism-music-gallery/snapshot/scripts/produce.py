"""Music-only gallery film. No narration or source-video audio is admitted."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,subprocess,math,concurrent.futures,wave,hashlib,os

ROOT=Path(__file__).resolve().parents[1]
PLAN=json.loads((ROOT/'edit-plan.json').read_text())
FF='/opt/homebrew/bin/ffmpeg';FP='/opt/homebrew/bin/ffprobe';FPS=24;FADE=1.25
FONT='/System/Library/Fonts/STHeiti Medium.ttc'
for n in ['stages','labels','parts','chapters','audio','exports','checks']:(ROOT/n).mkdir(exist_ok=True)
def font(n):return ImageFont.truetype(FONT,n)
def run(args,**kw):return subprocess.run(args,check=True,stdout=subprocess.DEVNULL,**kw)
def probe(path):
 return json.loads(subprocess.check_output([FP,'-v','error','-show_entries','format=duration:stream=codec_type,width,height,r_frame_rate','-of','json',str(path)]))
def common(threads=2,preset='fast',crf=20):
 return ['-c:v','libx264','-threads',str(threads),'-preset',preset,'-crf',str(crf),'-pix_fmt','yuv420p','-r',str(FPS),'-g','48','-colorspace','bt709','-color_primaries','bt709','-color_trc','bt709','-color_range','tv']
def atomic_png(im,path):
 tmp=path.with_name(path.stem+'.tmp.png');im.save(tmp);tmp.replace(path)

def prepare_graphics(s,t):
 sid=s['id'];label=ROOT/'labels'/(sid+'.png')
 overlay=Image.new('RGBA',(1920,1080),(0,0,0,0));d=ImageDraw.Draw(overlay)
 if s['album_opening']:
  d.rectangle((0,0,1920,1080),fill=(4,10,13,160))
  d.text((150,323),'山海与人间',font=font(108),fill=(244,236,213,255))
  d.text((157,483),'浪漫主义音乐画廊',font=font(43),fill=(222,221,201,255))
  d.text((157,574),'肖邦  ×  贝多芬',font=font(34),fill=(222,221,201,255))
  d.text((158,833),'Yancy 与 Eunice 共同创作',font=font(26),fill=(196,207,197,255))
 elif s['track_opening']:
  d.rectangle((0,0,1920,128),fill=(7,13,15,200))
  d.text((65,27),f"{'自然' if t['part']=='nature' else '人间'}  ·  {t['title']}",font=font(30),fill=(235,229,210,255))
  d.text((65,74),s['music_label'],font=font(23),fill=(187,202,192,255))
 if not s['album_opening']:
  for y in range(946,1080):
   alpha=min(245,int((y-946)/90*240));d.line((0,y,1920,y),fill=(9,15,17,alpha))
  title=f"《{s['title']}》" if s['type']=='art' else s['title']
  date=s.get('dateLabel',str(s.get('year','')))
  if date:title+='  '+date
  f=font(31)
  if d.textbbox((0,0),title,font=f)[2]>1780:f=font(26)
  d.text((65,962),title,font=f,fill=(244,240,227,255))
  d.text((67,1007),s['artist'],font=font(23),fill=(205,215,205,255))
  if s.get('first_artist') and s.get('bio'):d.text((67,1043),s['bio'],font=font(19),fill=(164,183,173,255))
 atomic_png(overlay,label)
 s['label_file']=str(label)
 if s['type']=='art':
  im=Image.open(s['file']).convert('RGB')
  if s.get('detail'):
   w,h=im.size;im=im.crop((int(.22*w),0,int(.88*w),int(.35*h)))
  factor=min(2260/im.width,1130/im.height)
  im=im.resize((round(im.width*factor),round(im.height*factor)),Image.Resampling.LANCZOS)
  canvas=Image.new('RGB',(2400,1350),(11,18,20));canvas.paste(im,((2400-im.width)//2,38+(1180-im.height)//2))
  p=ROOT/'stages'/(sid+'.png');atomic_png(canvas,p);s['stage_file']=str(p)

for t in PLAN['tracks']:
 for i,s in enumerate(t['shots']):
  s['render_duration']=s['seconds']+(FADE if i<len(t['shots'])-1 else 0)
  s['render_frames']=round(s['render_duration']*FPS)
  prepare_graphics(s,t)

# Source audio is decoded once. Constant gain preserves musical dynamics.
audio_parts=[]
for t in PLAN['tracks']:
 f=ROOT/'audio'/(t['id']+'.wav');seconds=t['video_duration']+t['gap_after']
 if not f.exists():
  run([FF,'-hide_banner','-loglevel','error','-y','-i',t['file'],'-af',f"volume={t['gain_db']}dB,apad",'-t',str(seconds),'-ar','48000','-ac','2','-c:a','pcm_s16le',str(f)])
 audio_parts.append(f)
mix=ROOT/'audio/complete-program.wav'
with wave.open(str(mix),'wb') as out:
 out.setnchannels(2);out.setsampwidth(2);out.setframerate(48000)
 for f in audio_parts:
  with wave.open(str(f),'rb') as source:
   assert (source.getnchannels(),source.getsampwidth(),source.getframerate())==(2,2,48000)
   while b:=source.readframes(262144):out.writeframes(b)
print('AUDIO READY',round(PLAN['duration'],2),flush=True)

def render_shot(s):
 out=ROOT/'parts'/(s['id']+'.mp4');signature=hashlib.sha256(json.dumps(s,sort_keys=True,ensure_ascii=False).encode()).hexdigest();stamp=out.with_suffix('.json')
 if out.exists() and stamp.exists() and json.loads(stamp.read_text()).get('signature')==signature:return out
 tmp=out.with_name(out.stem+'.tmp.mp4');cmd=[FF,'-hide_banner','-loglevel','error','-y']
 frames=s['render_frames'];seconds=frames/FPS
 if s['type']=='art':
  # Art containing nudity is a static reproduction throughout, never animated.
  zoom='1' if s.get('nudity') or s.get('detail') else f'1+0.018*on/{max(1,frames-1)}'
  cmd+=['-i',s['stage_file'],'-loop','1','-framerate',str(FPS),'-i',s['label_file']]
  bg=f"[0:v]zoompan=z='{zoom}':x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2':d={frames}:s=1920x1080:fps={FPS},setsar=1[bg]"
 else:
  cmd+=['-i',s['file'],'-loop','1','-framerate',str(FPS),'-i',s['label_file']]
  bg='[0:v]fps=24,scale=1920:958:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=0x0b1214,tpad=stop_mode=clone:stop_duration=4,setsar=1[bg]'
 fade_start=6 if s['album_opening'] else min(9,max(3,seconds-2))
 graph=bg+f";[1:v]format=rgba,fade=t=out:st={fade_start}:d=1.5:alpha=1[title];[bg][title]overlay=0:0:format=auto,scale=out_color_matrix=bt709:out_range=tv,format=yuv420p[v]"
 cmd+=['-filter_complex_threads','1','-filter_complex',graph,'-map','[v]','-an','-frames:v',str(frames)]
 cmd+=common()+['-movflags','+faststart',str(tmp)]
 run(cmd)
 actual=probe(tmp);assert abs(float(actual['format']['duration'])-seconds)<.06,(s['id'],actual)
 tmp.replace(out);stamp.write_text(json.dumps(dict(signature=signature,seconds=seconds)))
 print('SHOT',s['id'],s['asset_id'],round(seconds,2),flush=True);return out

all_shots=[s for t in PLAN['tracks'] for s in t['shots']]
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:list(pool.map(render_shot,all_shots))

def render_track(t):
 out=ROOT/'chapters'/(t['id']+'.mp4');tmp=out.with_name(out.stem+'.tmp.mp4')
 inputs=[ROOT/'parts'/(s['id']+'.mp4') for s in t['shots']]
 if out.exists() and out.stat().st_mtime>=max(p.stat().st_mtime for p in inputs):return out
 cmd=[FF,'-hide_banner','-loglevel','error','-y'];graph=[]
 for i,f in enumerate(inputs):cmd+=['-i',str(f)];graph.append(f'[{i}:v]settb=AVTB,setpts=PTS-STARTPTS[v{i}]')
 previous='v0';elapsed=0
 for i in range(1,len(inputs)):
  elapsed+=t['shots'][i-1]['seconds'];name=f'x{i}'
  graph.append(f'[{previous}][v{i}]xfade=transition=fade:duration={FADE}:offset={elapsed:.6f}[{name}]');previous=name
 graph.append(f'[{previous}]fade=t=in:st=0:d=0.7,fade=t=out:st={t["video_duration"]-.8}:d=0.8,format=yuv420p[final]')
 cmd+=['-filter_complex_threads','1','-filter_complex',';'.join(graph),'-map','[final]','-an','-frames:v',str(t['frames'])]
 cmd+=common(threads=3,preset='veryfast',crf=19)+['-movflags','+faststart','-progress',str(ROOT/'checks'/(t['id']+'-render-progress.txt')),str(tmp)]
 run(cmd);assert abs(float(probe(tmp)['format']['duration'])-t['video_duration'])<.06
 tmp.replace(out);print('CHAPTER',t['id'],'READY',flush=True);return out

with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:chapter_files=list(pool.map(render_track,PLAN['tracks']))

gap=ROOT/'chapters/pause.mp4'
if not gap.exists():run([FF,'-hide_banner','-loglevel','error','-y','-f','lavfi','-i','color=c=0x0b1214:s=1920x1080:r=24','-t','1.5','-an']+common(threads=2,preset='veryfast',crf=19)+[str(gap)])

items=[]
for i,f in enumerate(chapter_files):
 items.append(f)
 if i<len(chapter_files)-1:items.append(gap)
concat=ROOT/'chapters/complete-concat.txt';concat.write_text('\n'.join("file '"+str(f)+"'" for f in items))
metadata=ROOT/'chapters/chapters.ffmeta';lines=[';FFMETADATA1','title=山海与人间｜浪漫主义音乐画廊','artist=Yancy & Eunice','comment=纯音乐，无旁白。三首选定肖邦录音及两首贝多芬录音。']
for t in PLAN['tracks']:lines+=['[CHAPTER]','TIMEBASE=1/1000',f'START={round(t["start"]*1000)}',f'END={round(t["end"]*1000)}',f'title={t["title"]} · {t["composer"]}']
metadata.write_text('\n'.join(lines))
master=ROOT/'exports/山海与人间-浪漫主义纯音乐版.mp4';tmp=master.with_name(master.stem+'.tmp.mp4')
run([FF,'-hide_banner','-loglevel','error','-y','-f','concat','-safe','0','-i',str(concat),'-i',str(mix),'-i',str(metadata),'-map','0:v','-map','1:a','-map_metadata','2','-map_chapters','2','-c:v','copy','-c:a','aac','-b:a','320k','-movflags','+faststart','-t',str(PLAN['duration']),str(tmp)])
tmp.replace(master);print('MASTER READY',master,master.stat().st_size,flush=True)

# Also export the two requested subject areas as standalone films.
for part,label,indices in [('nature','自然篇-肖邦-纯音乐版',[0,1,2]),('human','人间篇-贝多芬-纯音乐版',[3,4])]:
 selected=[]
 for j,i in enumerate(indices):
  selected.append(chapter_files[i])
  if j<len(indices)-1:selected.append(gap)
 filelist=ROOT/'chapters'/(part+'-concat.txt');filelist.write_text('\n'.join("file '"+str(f)+"'" for f in selected))
 start=PLAN['tracks'][indices[0]]['start'];end=PLAN['tracks'][indices[-1]]['end'];out=ROOT/'exports'/(label+'.mp4')
 run([FF,'-hide_banner','-loglevel','error','-y','-f','concat','-safe','0','-i',str(filelist),'-ss',str(start),'-i',str(mix),'-map','0:v','-map','1:a','-c:v','copy','-c:a','aac','-b:a','320k','-t',str(end-start),'-metadata',f'title={label}','-movflags','+faststart',str(out)])
 print('PART READY',out.name,out.stat().st_size,flush=True)

verification={'master':str(master),'duration':PLAN['duration'],'artworks':PLAN['artwork_count'],'shots':len(all_shots),'music_only':True,'music_files':[dict(file=t['file'],sha256=t['sha256'],complete_duration=t['audio_duration'],constant_gain_db=t['gain_db']) for t in PLAN['tracks']],'source_video_audio_included':False,'source_art_policy':'Nudity-marked paintings remain static originals. No new AI-generated artwork or video was created for this version.'}
(ROOT/'checks/build-result.json').write_text(json.dumps(verification,ensure_ascii=False,indent=2))
print('ALL EXPORTS COMPLETE',flush=True)
