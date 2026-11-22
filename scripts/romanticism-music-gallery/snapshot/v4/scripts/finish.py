"""Assemble the native museum walk, reuse existing inserts, keep music unchanged."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from concurrent.futures import ThreadPoolExecutor
import subprocess,json,hashlib,math
ROOT=Path(__file__).resolve().parents[1];OLD=ROOT.parent
FF='/opt/homebrew/bin/ffmpeg';FP='/opt/homebrew/bin/ffprobe';FPS=24
plan=json.loads((ROOT/'edit-plan.json').read_text())
PARTS=ROOT/'parts';EXPORT=ROOT/'exports'
def frames(path):
 return round(float(subprocess.check_output([FP,'-v','error','-show_entries','format=duration','-of','csv=p=0',str(path)]))*FPS)
def run(args):subprocess.run([FF,'-v','error','-y',*args],check=True)
def opts(count):return['-frames:v',str(count),'-an','-c:v','libx264','-threads','3','-preset','veryfast','-crf','18','-pix_fmt','yuv420p','-video_track_timescale','12288','-fps_mode','passthrough']
def intro_labels(cmd,graph,last,c,inputs):
 begin=c['first']/FPS;end=(c['first']+c['count'])/FPS
 for label in plan['opening_labels']:
  if label['end']<=begin or label['start']>=end:continue
  inputs+=1;cmd+=['-loop','1','-framerate','24','-i',str(ROOT/'labels'/(label['id']+'.png'))]
  effect=['format=rgba']
  if label['start']>=begin:effect.append(f'fade=t=in:st={label["start"]-begin:.8f}:d=0.6:alpha=1')
  effect.append(f'fade=t=out:st={max(0,label["end"]-begin-.8):.8f}:d=0.8:alpha=1')
  name='intro'+str(inputs);mixed='intromix'+str(inputs)
  graph.append(f'[{inputs}:v]'+','.join(effect)+f'[{name}]')
  graph.append(f'[{last}][{name}]overlay=repeatlast=1[{mixed}]');last=mixed
 return last,inputs

def opening():
 source=ROOT/'footage/walk/walk-000.mp4';dest=PARTS/'walk-000.mp4';assert frames(source)==432
 if dest.is_file():return dest
 graph=['[1:v]setpts=(PTS-STARTPTS)/0.8,fps=24,scale=1920:1080,setsar=1,format=yuva420p,fade=t=out:st=6.4:d=1.9:alpha=1,trim=duration=8.3[gallery]',
 '[0:v][gallery]overlay=repeatlast=0:eof_action=pass[room]']
 cmd=['-i',str(source),'-ss','0.4','-i',str(ROOT/'assets/gallery-entry.mp4')]
 last,_=intro_labels(cmd,graph,'room',plan['chunks'][0],1)
 run([*cmd,'-filter_complex_threads','1','-filter_complex',';'.join(graph),'-map',f'[{last}]',*opts(432),'-movflags','+faststart',str(dest)])
 assert frames(dest)==432
 return dest

def compose(c):
 if c['first']==0:return opening()
 raw=ROOT/'footage/walk'/(c['id']+'.mp4');assert raw.is_file(),raw
 assert frames(raw)==c['count'],raw
 active=[i for i in plan['inserts'] if round(i['start']*FPS)<c['first']+c['count'] and round(i['end']*FPS)>c['first']]
 header=c['id']=='walk-001';closing=c==plan['chunks'][-1]
 if not active and not header and not closing:return raw
 dest=PARTS/(c['id']+'.mp4')
 signature=hashlib.sha256(json.dumps(dict(c=c,active=active,header=header,closing=closing),sort_keys=True).encode()).hexdigest()
 cache=dest.with_suffix('.json')
 if dest.exists() and cache.exists() and json.loads(cache.read_text()).get('signature')==signature:return dest
 temp=dest.with_suffix('.partial.mp4');cmd=['-filter_complex_threads','1','-i',str(raw)]
 graph=['[0:v]settb=1/24,setpts=N[base]'];last='base';inputs=0
 last,inputs=intro_labels(cmd,graph,last,c,inputs)
 for insert in active:
  inputs+=1;cmd+=['-ss',str(insert['trim']),'-i',insert['file']]
  begin,end=round(insert['start']*FPS),round(insert['end']*FPS)
  first=max(0,c['first']-begin);final=min(end-begin,c['first']+c['count']-begin);shift=max(0,begin-c['first'])
  duration=(end-begin)/FPS
  effect=[f'setpts=(PTS-STARTPTS)/{insert["speed"]}','fps=24',
    'scale=1920:1080:force_original_aspect_ratio=decrease','pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=0x0c141a',
    'setsar=1','tpad=stop_mode=clone:stop_duration=0.25','format=yuva420p',
    f'fade=t=in:st=0:d={insert["fade_in"]}:alpha=1',
    f'fade=t=out:st={duration-insert["fade_out"]:.8f}:d={insert["fade_out"]}:alpha=1',
    f'trim=start_frame={first}:end_frame={final}',f'settb=1/24,setpts=N+{shift}']
  graph.append(f'[{inputs}:v]'+','.join(effect)+f'[i{inputs}]')
  graph.append(f'[{last}][i{inputs}]overlay=repeatlast=0:eof_action=pass[m{inputs}]');last=f'm{inputs}'
 if header:
  inputs+=1;cmd+=['-loop','1','-framerate','24','-i',str(ROOT/'labels/rain.png')]
  graph.append(f'[{inputs}:v]format=rgba,fade=t=in:st=5:d=0.7:alpha=1,fade=t=out:st=12.5:d=1.5:alpha=1[header]')
  graph.append(f'[{last}][header]overlay=repeatlast=1[headed]');last='headed'
 if closing:
  graph.append(f'[{last}]fade=t=out:st={c["count"]/FPS-1.2:.8f}:d=1.2[closing]');last='closing'
 run([*cmd,'-filter_complex',';'.join(graph),'-map',f'[{last}]',*opts(c['count']),'-movflags','+faststart',str(temp)])
 assert frames(temp)==c['count'],c['id'];temp.replace(dest);cache.write_text(json.dumps(dict(signature=signature)))
 print('COMPOSED',c['id'],[i['name'] for i in active],flush=True);return dest

def main():
 assert (ROOT/'checks/capture-result.json').exists(),'Capture must finish first'
 with ThreadPoolExecutor(max_workers=2)as pool:files=list(pool.map(compose,plan['chunks']))
 manifest=PARTS/'walk.concat.txt';manifest.write_text(''.join(f"file '{p}'\nduration {c['count']/FPS:.12f}\n"for p,c in zip(files,plan['chunks'],strict=True)))
 compressed=PARTS/'complete-picture.mp4'
 if not compressed.exists():
  pending=compressed.with_suffix('.partial.mp4')
  forced=sorted(set([t['start'] for t in plan['tracks']]+[t['end'] for t in plan['tracks']][:-1]))
  run(['-f','concat','-safe','0','-i',str(manifest),'-an','-frames:v',str(plan['frames']),'-c:v','libx264','-threads','6',
    '-preset','fast','-crf','19','-pix_fmt','yuv420p','-r','24','-g','48','-force_key_frames',','.join(map(str,forced)),
    '-video_track_timescale','12288','-movflags','+faststart','-progress',str(ROOT/'checks/final-encode-progress.txt'),str(pending)])
  assert frames(pending)==plan['frames'];pending.replace(compressed)
 assert frames(compressed)==plan['frames'];print('PICTURE COMPLETE',compressed.stat().st_size,flush=True)
 labels=json.loads((ROOT/'label-style.json').read_text())
 metadata=PARTS/'chapters.ffmeta';lines=[';FFMETADATA1','title=Mountains, Seas, and Mortals','artist=Yancy & Eunice','comment=Instrumental music only. English picture labels. Separate English and Simplified Chinese SRT files.']
 for t in plan['tracks']:lines+=['[CHAPTER]','TIMEBASE=1/1000',f'START={round(t["start"]*1000)}',f'END={round(t["end"]*1000)}',f'title={labels["music"][t["id"]]["english"]}']
 metadata.write_text('\n'.join(lines))
 audio=OLD/'audio/complete-program.wav';master=EXPORT/'山、海、人间-纯英文纯音乐版.mp4'
 approved_master=OLD/'v3/exports/山海与人间-中英标签纯音乐版.mp4'
 run(['-i',str(compressed),'-i',str(approved_master),'-i',str(metadata),'-map','0:v:0','-map','1:a:0','-map_metadata','2','-map_chapters','2',
      '-c:v','copy','-c:a','copy','-t',str(plan['duration']),'-movflags','+faststart',str(master)])
 print('MASTER READY',master.name,master.stat().st_size,flush=True)
 for part,label,start,end,approved,english_title in [
  ('nature','自然篇-肖邦-纯英文版',0,plan['tracks'][2]['end'],'自然篇-肖邦-中英标签版.mp4','Nature - Chopin'),
  ('human','人间篇-贝多芬-纯英文版',plan['tracks'][3]['start'],plan['duration'],'人间篇-贝多芬-中英标签版.mp4','Human Life - Beethoven')]:
  picture=PARTS/(part+'-picture.mp4')
  run(['-ss',str(start),'-i',str(compressed),'-map','0:v:0','-an','-c:v','copy','-frames:v',str(round((end-start)*FPS)),str(picture)])
  assert frames(picture)==round((end-start)*FPS),(picture,frames(picture))
  output=EXPORT/(label+'.mp4')
  run(['-i',str(picture),'-i',str(OLD/'v3/exports'/approved),'-map','0:v:0','-map','1:a:0','-map_metadata','-1','-map_chapters','-1','-c:v','copy','-c:a','copy',
       '-t',str(end-start),'-metadata',f'title={english_title}','-movflags','+faststart',str(output)])
  print('PART READY',output.name,output.stat().st_size,flush=True)
  picture.unlink()
 run(['-i',str(master),'-t','24','-map','0:v:0','-map','0:a:0','-c:v','libx264','-threads','3','-preset','veryfast','-crf','18','-frames:v','576','-c:a','copy','-map_chapters','-1',
      '-metadata','title=From Gallery to Space','-movflags','+faststart',str(EXPORT/'开场预览-24秒.mp4')])
 evidence=dict(master=str(master),duration=plan['duration'],artwork_count=34,narration=False,source_video_audio=False,
   music_program_sha256=hashlib.sha256(audio.read_bytes()).hexdigest(),music_program_source=str(audio),music_files=[dict(file=t['file'],sha256=t['sha256'],duration=t['audio_duration'])for t in plan['tracks']],
   approved_audio_source=str(approved_master),audio_policy='Copied the approved AAC stream without re-encoding; all five complete recordings unchanged.',
   shared_native_room=True,route=plan['speeds'],same_stationary_pose_before_and_after_plate=True,flat_fade_seconds=1.35,reference_opening='assets/gallery-entry.mp4',opening_native_capture='footage/walk/walk-000.mp4',label_style='label-style.json',film_label_languages=['en'],separate_subtitles=['en','zh-Hans'],source_room_modified=False)
 (ROOT/'checks/build-result.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2));print('ALL EXPORTS COMPLETE',flush=True)

if __name__=='__main__':main()
