"""Inspect delivered media and save readable evidence, without changing the source projects."""
import json, subprocess, re
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
ROOT=Path('/Users/yqin/repo/playground/lucas-academy-video-data/curiosity-builds-20261118')
OUT=ROOT/'delivery';REC=ROOT/'records'
def probe(p):return json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-show_chapters','-of','json',str(p)]))
full=OUT/'curiosity-builds.en.no-voice.mp4';data=probe(full)
chapters=json.loads((REC/'chapters.json').read_text())
assert len(chapters)==9 and len(data['chapters'])==9
report={'full':{'file':str(full),'seconds':float(data['format']['duration']),'bytes':full.stat().st_size},'chapters':[],'language':'English','narration':False,'audio_source':'Original procedural instrumental, synthesized from notes; all captured product audio discarded.'}
for p in [full,*sorted(OUT.glob('[0-9][0-9]-*.mp4'))]:
    d=probe(p);v=next(s for s in d['streams'] if s['codec_type']=='video');a=next(s for s in d['streams'] if s['codec_type']=='audio')
    assert (v['width'],v['height'])==(1920,1080)
    assert v['avg_frame_rate']=='30/1' and v['codec_name']=='h264' and a['codec_name']=='aac'
    report['chapters'].append({'file':p.name,'seconds':float(d['format']['duration']),'fps':v['avg_frame_rate'],'frames':v.get('nb_frames'),'audio':a['codec_name']})
decoded=subprocess.run(['ffmpeg','-v','error','-i',str(full),'-f','null','-'],capture_output=True,text=True)
report['decode']={'returncode':decoded.returncode,'errors':decoded.stderr}
assert decoded.returncode==0 and not decoded.stderr.strip(),decoded.stderr
loud=subprocess.run(['ffmpeg','-hide_banner','-i',str(full),'-vn','-af','loudnorm=I=-21:TP=-2:LRA=7:print_format=json','-f','null','-'],capture_output=True,text=True)
try:report['audio_loudness']=json.loads(re.search(r'\{\s*"input_i".*?\}',loud.stderr,re.S).group())
except ValueError:report['audio_loudness']='See final AAC stream; analysis unavailable.'
font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',24)
for kind,offset in [('projects',11),('ideas',1.8)]:
    board=Image.new('RGB',(1440,900),'#080e19');draw=ImageDraw.Draw(board)
    for i,c in enumerate(chapters):
        frame=REC/f'{kind}-{i+1:02d}.jpg';t=c['start']+min(offset,c['seconds']-1)
        subprocess.run(['ffmpeg','-y','-v','error','-ss',str(t),'-i',str(full),'-frames:v','1','-vf','scale=480:270',str(frame)],check=True)
        x=(i%3)*480;y=(i//3)*300;board.paste(Image.open(frame),(x,y));draw.text((x+12,y+272),f'{i+1:02d} {c["project"]}',font=font,fill='#f5e9d4')
    board.save(REC/f'contact-{kind}.jpg',quality=93)
(REC/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
lines=['What Can Curiosity Build?','English • 1920 × 1080 • 30 fps • No narration','','The complete film: curiosity-builds.en.no-voice.mp4','Silent picture master: curiosity-builds.en.silent.mp4','','Chapters:']
for c in chapters:
    s=round(c['start']);lines.append(f'{s//60:02d}:{s%60:02d}  {c["project"]}  —  {c["seconds"]:.1f} seconds')
lines+=['','All nine chapter videos are saved alongside the complete film.','Each chapter: condensed English idea prompt → abstract build visualization → actual project footage.','Inception Space recordings use first-person views. Chess includes its web page and special rules.','The music is an original synthesized instrumental; no voices or product audio are mixed in.']
(OUT/'START-HERE.txt').write_text('\n'.join(lines)+'\n')
print(json.dumps(report,indent=2))
