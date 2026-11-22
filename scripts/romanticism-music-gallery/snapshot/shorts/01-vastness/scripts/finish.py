"""Finish, inspect and deliver the single portrait sample."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timezone
import subprocess, json, hashlib, shutil, re

ROOT=Path(__file__).resolve().parents[1]
PROJECT=ROOT.parents[1]
FF='/opt/homebrew/bin/ffmpeg';FP='/opt/homebrew/bin/ffprobe'
plan=json.loads((ROOT/'edit-plan.json').read_text())
capture=json.loads((ROOT/'checks/capture-result.json').read_text())
NAME='面对辽阔-竖屏示范'

def run(args):subprocess.run([FF,'-hide_banner','-v','error','-y',*args],check=True)
def sha(file):return hashlib.sha256(file.read_bytes()).hexdigest()

manifest=ROOT/'parts/concat.txt'
manifest.write_text(''.join(f"file '{ROOT/'footage'/(c['id']+'.mp4')}'\nduration {c['count']/plan['fps']:.12f}\n" for c in capture['chunks']))
picture=ROOT/'parts/picture.mp4'
run(['-f','concat','-safe','0','-i',str(manifest),'-an','-frames:v',str(plan['frames']),
     '-c:v','libx264','-threads','4','-preset','fast','-crf','18','-pix_fmt','yuv420p',
     '-r','24','-g','48','-video_track_timescale','12288','-movflags','+faststart',str(picture)])
output=ROOT/'exports'/(NAME+'.mp4')
audio=plan['music']
run(['-i',str(picture),'-ss',str(audio['excerpt_start']),'-i',audio['file'],
     '-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','320k','-ar','48000','-ac','2',
     '-af',f"volume={audio['gain_db']}dB,afade=t=in:st=0:d=0.2,afade=t=out:st=56:d=2",
     '-t','58','-map_metadata','-1','-metadata','title=Facing the Vastness',
     '-metadata','artist=Yancy & Eunice','-metadata','comment=Two Friedrich paintings in the current IS salon. Instrumental Chopin excerpt; English labels; separate Chinese SRT.',
     '-movflags','+faststart',str(output)])

probe=json.loads(subprocess.check_output([FP,'-v','error','-show_streams','-show_format','-of','json',str(output)]))
v=next(s for s in probe['streams'] if s['codec_type']=='video');a=next(s for s in probe['streams'] if s['codec_type']=='audio')
assert (v['width'],v['height'],v['r_frame_rate'])==(1080,1920,'24/1')
assert int(v['nb_frames'])==1392
assert abs(float(probe['format']['duration'])-58)<.05
assert a['channels']==2 and int(a['sample_rate'])==48000
assert len(probe['streams'])==2
with (ROOT/'checks/decode.log').open('w')as errors:
    subprocess.run([FF,'-hide_banner','-v','error','-i',str(output),'-map','0:v','-map','0:a','-f','null','-'],stdout=subprocess.DEVNULL,stderr=errors,check=True)
assert not (ROOT/'checks/decode.log').read_text().strip()
print('FULL SHORT DECODE PASSED',flush=True)

subtitle=ROOT/'subtitles'/(NAME+'.zh-Hans.srt')
blocks=subtitle.read_text(encoding='utf-8-sig').strip().split('\n\n')
assert len(blocks)==len(plan['labels'])==4
for i,(block,cue)in enumerate(zip(blocks,plan['labels']),1):
    lines=block.splitlines();assert int(lines[0])==i
    assert '\n'.join(lines[2:])==cue['zh']
    assert 0<=cue['start']<cue['end']<=58
    assert not any(re.search(r'[\u3400-\u9fff]',text) for text in cue['en'])
assert sha(Path(audio['file']))==audio['sha256']
for file,expected in plan['source_snapshot'].items():
    assert sha(Path(plan['source_repository'])/file)==expected,'IS source changed during recording: '+file

times=[2,7,14,23.5,28.5,35,46,54.5,56]
contact=Image.new('RGB',(900,1680),'#101820');draw=ImageDraw.Draw(contact)
font=ImageFont.truetype('/System/Library/Fonts/STHeiti Medium.ttc',16)
for i,time in enumerate(times):
    frame=ROOT/'checks'/f'final-{time}.jpg'
    run(['-ss',str(time),'-i',str(output),'-frames:v','1',str(frame)])
    image=Image.open(frame);image.thumbnail((296,526));x=i%3*300;y=i//3*560
    contact.paste(image,(x,y));draw.text((x+7,y+532),f'{time:g} s',font=font,fill='white')
contact.save(ROOT/'checks/final-contact.jpg',quality=93)

credits=json.loads((PROJECT/'v4/sources/credits.json').read_text())
credits={'title':plan['title'],'title_en':plan['title_en'],'creators':['Yancy','Eunice'],
         'format':{'width':1080,'height':1920,'fps':24,'duration_seconds':58,'picture_language':'en','subtitles':['zh-Hans'],'voice':False},
         'featured_artworks':[{k:a[k]for k in ['id','title_en','title_zh','artist_en','artist_zh','source','license','original_sha256']}for a in plan['artworks']],
         'music':{**audio,'excerpt_note':'A continuous 58-second excerpt, with a short entrance fade and two-second ending fade. This short does not play the complete 5-minute prelude.'},
         'source_layout_snapshot':plan['source_snapshot'],
         'sculpture_scans':credits['scans'],'central_sculpture':credits['central_sculpture'],
         'scene':'Rendered afresh from the current canonical IS salon. No UI source or room arrangement changed. Two featured title boards are replaced by English overlay captions during this isolated capture.'}
(ROOT/'sources/credits.json').write_text(json.dumps(credits,ensure_ascii=False,indent=2))
evidence={'status':'passed','checked_utc':datetime.now(timezone.utc).isoformat(),
          'video':{'file':output.name,'bytes':output.stat().st_size,'sha256':sha(output),'duration':float(probe['format']['duration']),'width':1080,'height':1920,'fps':24,'frames':1392,'audio':a['codec_name']},
          'full_decode':'passed','current_is_source_hashes_verified':True,'english_picture_labels':True,
          'separate_chinese_subtitle_cues':4,'music_source_hash_verified':True,'no_narration':True,
          'featured_works':['wanderer','chalk-cliffs'],'visual_review':'pending','browser_review':'pending'}
(ROOT/'checks/verified.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2))
print('FINAL MP4 READY',output,output.stat().st_size,flush=True)
