"""Inspect delivered media and save readable evidence, without changing the source projects."""
import json, subprocess, re
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
ROOT=Path('/Users/yqin/repo/playground/lucas-academy-video-data/curiosity-builds-20261118/v2')
OUT=ROOT/'delivery';REC=ROOT/'records'
def probe(p):return json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-show_chapters','-of','json',str(p)]))
full=OUT/'curiosity-builds.en.no-voice.mp4';data=probe(full)
chapters=json.loads((REC/'chapters.json').read_text())
assert len(chapters)==9 and len(data['chapters'])==9
plan=json.loads(Path(__file__).with_name('plan.json').read_text())
music=json.loads((REC/'music-cues.json').read_text())
assert {c['key'] for c in music['cues']}=={'mozart','bach','chopin','debussy'}
assert abs(chapters[0]['seconds']-36.2)<.04
assert abs(chapters[6]['seconds']-19.2)<.04
assert [c['seconds'] for c in plan['projects'][7]['clips']]==[10,10]
assert abs(float(data['format']['duration'])-(chapters[-1]['start']+chapters[-1]['seconds']+plan['ending_seconds']))<1/30+.001
events=json.loads((REC/'chess-play-events.json').read_text())
assert len(events['table']['actions'])>=4
report={'full':{'file':str(full),'seconds':float(data['format']['duration']),'bytes':full.stat().st_size},'chapters':[],'language':'English','narration':False,'audio_source':'Mozart, Bach, Chopin, and Debussy recordings; original tempo and dynamics. No captured application audio. See MUSIC-CREDITS.txt.','revision_checks':{'roller_seconds':chapters[0]['seconds'],'mobius_seconds':plan['projects'][0]['clips'][-1]['seconds'],'chameleon_seconds':chapters[6]['seconds'],'coder_footage_split_seconds':[10,10],'real_chess_plies':len(events['table']['actions']),'closing_questions':plan['ending_questions']}}
for p in [full,*sorted(OUT.glob('[0-9][0-9]-*.mp4'))]:
    d=probe(p);v=next(s for s in d['streams'] if s['codec_type']=='video');a=next(s for s in d['streams'] if s['codec_type']=='audio')
    assert (v['width'],v['height'])==(1920,1080)
    assert v['avg_frame_rate']=='30/1' and v['codec_name']=='h264' and a['codec_name']=='aac'
    if p!=full:
        chapter=chapters[int(p.name[:2])-1]
        assert abs(float(v['duration'])-chapter['seconds'])<1/30+.001,(p,float(v['duration']),chapter['seconds'])
    report['chapters'].append({'file':p.name,'seconds':float(d['format']['duration']),'fps':v['avg_frame_rate'],'frames':v.get('nb_frames'),'audio':a['codec_name']})
assert not any(s['codec_type']=='audio' for s in probe(OUT/'curiosity-builds.en.silent.mp4')['streams'])
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
ending_start=chapters[-1]['start']+chapters[-1]['seconds']
board=Image.new('RGB',(1440,600),'#080e19');draw=ImageDraw.Draw(board)
for i,t in enumerate([1.3,4.5,7.7,11.1,15.5]):
    frame=REC/f'ending-{i+1:02d}.jpg'
    subprocess.run(['ffmpeg','-y','-v','error','-ss',str(ending_start+t),'-i',str(full),'-frames:v','1','-vf','scale=480:270',str(frame)],check=True)
    x=(i%3)*480;y=(i//3)*300;board.paste(Image.open(frame),(x,y));draw.text((x+12,y+272),f'Question {i+1}',font=font,fill='#f5e9d4')
board.save(REC/'contact-ending.jpg',quality=93)
(REC/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
lines=['What Can Curiosity Build?','English • 1920 × 1080 • 30 fps • No narration','','The complete film: curiosity-builds.en.no-voice.mp4','Silent picture master: curiosity-builds.en.silent.mp4','','Chapters:']
for c in chapters:
    s=round(c['start']);lines.append(f'{s//60:02d}:{s%60:02d}  {c["project"]}  —  {c["seconds"]:.1f} seconds')
lines+=['','All nine chapter videos are saved alongside the complete film.','Each chapter: condensed English idea prompt → abstract build visualization → actual project footage.','Revision 2: 36.2-second roller coaster chapter, including entry, line, parabola, overhead spiral, and 12-second Möbius ride.','Chess: lobby, elevated live play, and the actual Weekly Comeback / Rockfall demos with brief rule labels.','Sky: transition-room opening and an 18-second orbit.','Painterly Chameleon is shortened to 19.2 seconds. Coder footage is split evenly between Coder Arena and a genuine archival Monthly Ranking server battle.','The five closing questions appear separately. English wording is lightly polished.','Music: Mozart, Bach, Chopin, and Debussy. No narration or captured application audio.','See MUSIC-CREDITS.txt for the recording sources and attribution.']
(OUT/'START-HERE.txt').write_text('\n'.join(lines)+'\n')
print(json.dumps(report,indent=2))
