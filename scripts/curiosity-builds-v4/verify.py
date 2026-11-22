"""Inspect delivered media and save readable evidence, without changing the source projects."""
import json, subprocess, re
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
ROOT=Path('/Users/yqin/repo/playground/lucas-academy-video-data/curiosity-builds-20261118/v4')
OUT=ROOT/'delivery';REC=ROOT/'records'
def probe(p):return json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-show_chapters','-of','json',str(p)]))
full=OUT/'curiosity-builds.en.no-voice.mp4';data=probe(full)
chapters=json.loads((REC/'chapters.json').read_text())
assert len(chapters)==9 and len(data['chapters'])==9
plan=json.loads(Path(__file__).with_name('plan.json').read_text())
music=json.loads((REC/'music-cues.json').read_text())
assert {c['key'] for c in music['cues']}=={'mozart','bach','chopin','debussy'}
byid={p['id']:p for p in plan['projects']};chapter_byid={c['id']:c for c in chapters}
assert [p['id'] for p in plan['projects']]==['chess','bible','vangogh','journey','sky','chameleon','cube','coder','roller']
assert [c['id'] for c in chapters]==[p['id'] for p in plan['projects']]
assert [c['tags']['title'] for c in data['chapters']]==[c['project'] for c in chapters]
assert [c['key'] for c in music['cues']]==['bach','chopin','debussy','mozart','mozart']
assert [c['target_lufs'] for c in music['cues']]==sorted(c['target_lufs'] for c in music['cues'])
assert [c['nominal_lufs_after_gain'] for c in music['cues']]==sorted(c['nominal_lufs_after_gain'] for c in music['cues'])
assert abs(chapter_byid['roller']['seconds']-36.2)<.04
assert abs(chapter_byid['chameleon']['seconds']-19.2)<.04
assert [c['seconds'] for c in byid['coder']['clips']]==[10,10]
assert len(plan['ending_questions'])==3 and plan['ending_seconds']==18
assert plan['ending_questions']==['What are you curious about?','What will you build?','Where will you make a difference?']
film_source=Path(__file__).parents[2]/'src/videos/curiosity-builds-v4/Film.tsx'
film=film_source.read_text()
assert 'Lucas Academy' not in film and 'lucasacademy.org' not in film
assert 'jesus-background.mp4' in film and 'sweet-home-v3-preview.mp4' in film
assert min(int(n) for n in re.findall(r'fontSize[:=]["\s]*(\d+)',film))>=48
assert byid['sky']['clips'][1]['file']=='sky-orbit-cosmic-cliffs'
assert json.loads((REC/'cosmic-cliffs.json').read_text())['variant']=='cosmic-cliffs'
assert probe(ROOT/'captures/sweet-home-v3-preview.mp4')['streams'][0]['nb_frames']=='105'
assert byid['journey']['clips']==[{'file':'journey-original-walk','seconds':20,'caption':'Walk through a gallery of our own making.','start':23.5}]
assert abs(float(data['format']['duration'])-(chapters[-1]['start']+chapters[-1]['seconds']+plan['ending_seconds']))<1/30+.001
events=json.loads((REC/'chess-play-events.json').read_text())
assert len(events['table']['actions'])>=4
report={'full':{'file':str(full),'seconds':float(data['format']['duration']),'bytes':full.stat().st_size},'chapters':[],'language':'English','narration':False,'audio_source':'Bach → Chopin → Debussy → Mozart. Original tempo and internal dynamics, continuous sections across chapters. No captured application audio. See MUSIC-CREDITS.txt.','revision_checks':{'order':[c['id'] for c in chapters],'roller_seconds':chapter_byid['roller']['seconds'],'mobius_seconds':byid['roller']['clips'][-1]['seconds'],'chameleon_seconds':chapter_byid['chameleon']['seconds'],'coder_footage_split_seconds':[10,10],'real_chess_plies':len(events['table']['actions']),'journey_source':'Previous Lucas Academy film’s native gallery camera, source 23.5–43.5 s.','closing_questions':plan['ending_questions'],'seconds_per_closing_question':6,'sky_panorama':'Cosmic Cliffs','journey_build':'Actual Sweet Home 3D v3 preview, owner-selected starting view','small_editorial_text':False}}
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
board=Image.new('RGB',(1440,300),'#080e19');draw=ImageDraw.Draw(board)
for i,t in enumerate([3,9,15]):
    frame=REC/f'ending-{i+1:02d}.jpg'
    subprocess.run(['ffmpeg','-y','-v','error','-ss',str(ending_start+t),'-i',str(full),'-frames:v','1','-vf','scale=480:270',str(frame)],check=True)
    x=(i%3)*480;y=(i//3)*300;board.paste(Image.open(frame),(x,y));draw.text((x+12,y+272),f'Question {i+1}',font=font,fill='#f5e9d4')
board.save(REC/'contact-ending.jpg',quality=93)
(REC/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
lines=['What Can Curiosity Build?','English • 1920 × 1080 • 30 fps • No narration','','The complete film: curiosity-builds.en.no-voice.mp4','Silent picture master: curiosity-builds.en.silent.mp4','','Chapters:']
for c in chapters:
    s=round(c['start']);lines.append(f'{s//60:02d}:{s%60:02d}  {c["project"]}  —  {c["seconds"]:.1f} seconds')
lines+=['','All nine chapter videos are saved alongside the complete film.','Each chapter: condensed English idea prompt → abstract build visualization → actual project footage.','Revision 4 opens with Chess. Musical sections continue across chapters: measured Bach → lyrical Chopin → rising Debussy → playful Mozart → orchestral finale.','Journey of Art shows the actual Sweet Home 3D v3 preview moving from the owner-selected open camera, then the previous film’s gallery walk at native speed.','The 36.2-second roller coaster chapter comes last, followed by three closing questions, six seconds each, over the Mozart finale.','Chess: lobby, elevated live play, and the actual Weekly Comeback / Rockfall demos with brief rule labels.','Sky: transition-room opening and an 18-second orbit with the Cosmic Cliffs sky.','Painterly Chameleon lasts 19.2 seconds. Coder footage is split evenly between Coder Arena and a genuine archival Monthly Ranking server battle.','Titles and ending use a faded, blurred picture from the owner-supplied Jesus opening. Small editorial text, branded headers, URLs, and footers have been removed. English. No narration or captured application audio.','See MUSIC-CREDITS.txt for the recording sources and attribution.']
(OUT/'START-HERE.txt').write_text('\n'.join(lines)+'\n')
print(json.dumps(report,indent=2))
