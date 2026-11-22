"""Inspect delivered media and save readable evidence, without changing the source projects."""
import json, subprocess, re
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
ROOT=Path('/Users/yqin/repo/playground/lucas-academy-video-data/curiosity-builds-20261118/v10')
OUT=ROOT/'delivery';REC=ROOT/'records'
def probe(p):return json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-show_chapters','-of','json',str(p)]))
full=OUT/'curiosity-builds.en.no-voice.mp4';data=probe(full)
chapters=json.loads((REC/'chapters.json').read_text())
assert len(chapters)==9 and len(data['chapters'])==9
plan=json.loads(Path(__file__).with_name('plan.json').read_text())
music=json.loads((REC/'music-cues.json').read_text())
assert {c['key'] for c in music['cues']}=={'mozart','raindrop','chopin','debussy','air'}
byid={p['id']:p for p in plan['projects']};chapter_byid={c['id']:c for c in chapters}
assert [p['id'] for p in plan['projects']]==['chess','bible','vangogh','journey','sky','chameleon','cube','coder','roller']
assert [c['id'] for c in chapters]==[p['id'] for p in plan['projects']]
assert [c['tags']['title'] for c in data['chapters']]==[c['project'] for c in chapters]
assert [c['key'] for c in music['cues']]==['raindrop','debussy','chopin','air','mozart','mozart']
assert [c['target_lufs'] for c in music['cues']]==sorted(c['target_lufs'] for c in music['cues'])
assert [c['nominal_lufs_after_gain'] for c in music['cues']]==sorted(c['nominal_lufs_after_gain'] for c in music['cues'])
assert abs(chapter_byid['roller']['seconds']-36.2)<.04
assert abs(chapter_byid['chameleon']['seconds']-19.2)<.04
assert abs(chapter_byid['bible']['seconds']-31.2)<.04
assert all(c.get('speed')==2 for c in byid['bible']['clips'])
for name in ['bible-home-sequence-view','bible-sequence-read','bible-sequence-complete','bible-home-next-word-view','bible-next-word-start','bible-next-word-finish']:
    proof=json.loads((REC/(name+'.json')).read_text())
    assert not proof['post_capture_zoom'] and all(c['visible'] for c in proof['controls'])
assert json.loads((REC/'bible-sequence-complete.json').read_text())['completed_letters']==41
assert json.loads((REC/'bible-next-word-finish.json').read_text())['correct_predictions']>=6
assert [c['seconds'] for c in byid['coder']['clips']]==[10,10]
assert len(plan['ending_questions'])==3 and plan['ending_seconds']==18
assert plan['ending_questions']==['What are you curious about?','What will you build?','Where will you make a difference?']
film_source=Path(__file__).parents[2]/'src/videos/curiosity-builds-v10/Film.tsx'
film=film_source.read_text()
assert 'Lucas Academy' not in film and 'lucasacademy.org' not in film
assert 'jesus-background.mp4' in film and 'sweet-home-v3-model-only.mp4' in film
assert min(int(n) for n in re.findall(r'fontSize[:=]["\s]*(\d+)',film))>=48
assert byid['sky']['clips']==[{'file':'sky-continuous-cosmic-cliffs','seconds':25,'caption':'Enter a living sky. Rise, turn, and look back.'}]
assert abs(chapter_byid['sky']['seconds']-32.2)<.001
assert chapters[0]['start']==0 and plan['opening_seconds']==0
assert int(data['streams'][0]['nb_frames'])==8514
assert abs(float(data['format']['duration'])-283.8)<.04
sky=json.loads((REC/'sky-continuous.json').read_text())
assert sky['one_continuous_take'] and sky['editorial_cuts']==0 and sky['native_transition_included']
assert sky['frames']==750 and sky['variant']=='cosmic-cliffs' and not sky['errors']
assert 0<sky['entry_frame']<120 and 5<sky['hover_seconds']<9
ascending=[s for s in sky['samples'] if s['phase']=='ascending-orbit']
hover=[s for s in sky['samples'] if s['phase']=='hover-downward-orbit']
assert len(ascending)>25 and len(hover)>8
assert ascending[-1]['pose']['eye'][1]-ascending[0]['pose']['eye'][1]>13
assert max(s['pose']['eye'][1] for s in hover)-min(s['pose']['eye'][1] for s in hover)<.001
assert sum((hover[-1]['pose']['eye'][i]-hover[0]['pose']['eye'][i])**2 for i in [0,2])>30
assert all(s['pose']['target'][1]<s['pose']['eye'][1]-12 for s in hover)
assert probe(ROOT/'edit/sky-continuous-cosmic-cliffs.mp4')['streams'][0]['nb_frames']=='750'
assert json.loads((REC/'cosmic-cliffs.json').read_text())['variant']=='cosmic-cliffs'
assert probe(ROOT/'captures/sweet-home-v3-preview.mp4')['streams'][0]['nb_frames']=='105'
assert byid['journey']['clips']==[{'file':'journey-original-walk','seconds':20,'caption':'Walk through a gallery of our own making.','start':23.5}]
assert 'cube-draft.png' in film
assert 'rotate(' not in film.split("if(id==='cube')",1)[1].split('const P=',1)[0]
asset=film_source.parent/'assets/cube-draft.png'
assert asset.is_file() and asset.stat().st_size>100000
image=Image.open(asset);assert image.mode in ['RGB','RGBA'] and min(image.size)>1000
assert 'data-intro-layout="title-and-illustration"' in film and film.count('{item.question}')==1
assert 'data-process-picture="fixed-right"' in film
assert 'data-process-steps=' not in film and 'mix(trans' not in film
assert plan['intro_motion']['layout_count']==2 and plan['intro_motion']['fixed_right_hand_picture']
assert plan['intro_motion']['title_end_frame']<plan['intro_motion']['prompt_reveal_start_frame']
assert not plan['intro_motion']['process_step_chain']
assert byid['cube']['question']=='Can We Build an 11×11 Cube?'
assert byid['chess']['question']=='What Can Curiosity Build?'
assert byid['chess']['name']=='Balanced Chess'
for project in ['vangogh','journey']:
    concept=film_source.parent/'assets'/(project+'-gallery-concept.png')
    assert concept.is_file() and Image.open(concept).width>1000
    assert (project+'-gallery-concept.png') in [x.name for x in (ROOT/'captures').iterdir()]
assert probe(ROOT/'captures/sweet-home-v3-model-only.mp4')['streams'][0]['nb_frames']=='105'
house=json.loads((REC/'house-model-crop.json').read_text())
assert house['crop']['y']>=548 and house['only_3d_model']
assert 'data-process-prompt="after-title"' in film
assert plan['intro_motion']['diagram_present_from_frame']==42
assert plan['intro_motion']['standalone_title_until_frame']==30
assert plan['intro_motion']['title_zoom_start_frame']==30 and plan['intro_motion']['title_zoom_end_frame']==54
assert plan['intro_motion']['single_title_node'] and 'data-title-motion="standalone-to-layout"' in film
assert 'mix(titleZoom,1.38,1)' in film and 'interpolate(f,[42,60],[0,1]' in film
motion=json.loads((REC/'title-motion-pixels.json').read_text())
assert motion['title_scales_down_and_moves_left']
assert [s['white_text_bbox'][0] for s in motion['samples']]==[339,220,100]
assert plan['intro_motion']['journey_preview_start_frame']==96
assert 'Math.max(0,f-96)*.875' in film
assert len(list((ROOT/'captures/sweet-home-model-frames').glob('frame-*.jpg')))==105
assert 'opening.mp4' not in Path(__file__).with_name('render.py').read_text()
ice=json.loads((REC/'ice-blue-native.json').read_text());assert not ice['errors']
assert ice['selected']==ice['final']=={'funnel':'spaceGlass','blackHole':'white'}
cube_proof=json.loads((REC/'cube-framing.json').read_text())
assert len(cube_proof)==2
for proof in cube_proof:
    crop=proof['source_crop'];card=proof['top_solve_card_source_bounds']
    assert proof['top_steps_retained'] and proof['full_web_viewport'] and proof['right_control_panel_retained']
    assert crop=={'x':0,'y':0,'width':1920,'height':1080} and proof['filter']=='fps=30,setsar=1'
    assert crop['x']<=card['x'] and crop['y']<=card['y']
    assert crop['x']+crop['width']>=card['x']+card['width']
    assert crop['y']+crop['height']>=card['y']+card['height']
transition_count=0
for i,p in enumerate(plan['projects'],1):
    r=json.loads((REC/f'{i:02d}-{p["id"]}-picture.dissolves.json').read_text())
    assert r['output_frames']==round(chapter_byid[p['id']]['seconds']*30)
    assert len(r['transitions'])==len(p['clips'])
    assert all(t['frames'] in [12,18] for t in r['transitions'])
    transition_count+=len(r['transitions'])
    mux=json.loads((REC/f'{i:02d}-{p["id"]}.en.no-voice.mux.json').read_text())
    assert mux['standalone_edge_fades']
full_fx=json.loads((REC/'curiosity-builds.en.silent.dissolves.json').read_text())
assert full_fx['overall_fades'] and len(full_fx['transitions'])==9
assert all(t['frames']==24 for t in full_fx['transitions'])
transition_count+=len(full_fx['transitions'])
assert transition_count==32
for a,b in zip(music['cues'],music['cues'][1:]):
    assert abs(a['mix_end']-b['mix_start']-2)<.002
assert music['cues'][0]['fade_in_seconds']==1.2
assert music['cues'][-1]['fade_out_seconds']==2.4
assert abs(float(data['format']['duration'])-(chapters[-1]['start']+chapters[-1]['seconds']+plan['ending_seconds']))<1/30+.001
events=json.loads((REC/'chess-play-events.json').read_text())
assert len(events['table']['actions'])>=4
report={'full':{'file':str(full),'seconds':float(data['format']['duration']),'bytes':full.stat().st_size},'chapters':[],'language':'English','narration':False,'audio_source':'Chopin Raindrop → Debussy Clair de lune → Chopin Nocturne → Bach Air → Mozart. Original tempo and internal dynamics, continuous sections across chapters. No captured application audio. See MUSIC-CREDITS.txt.','revision_checks':{'order':[c['id'] for c in chapters],'roller_seconds':chapter_byid['roller']['seconds'],'mobius_seconds':byid['roller']['clips'][-1]['seconds'],'chameleon_seconds':chapter_byid['chameleon']['seconds'],'coder_footage_split_seconds':[10,10],'real_chess_plies':len(events['table']['actions']),'journey_source':'Previous Lucas Academy film’s native gallery camera, source 23.5–43.5 s.','closing_questions':plan['ending_questions'],'seconds_per_closing_question':6,'sky_panorama':'Cosmic Cliffs','journey_build':'Actual Sweet Home 3D v3 preview, owner-selected starting view','small_editorial_text':False}}
report['revision_checks'].update({'picture_dissolves':transition_count,'music_crossfade_seconds':2,'film_picture_fade_in_seconds':1,'film_picture_fade_out_seconds':1.2,'music_fade_in_seconds':1.2,'music_fade_out_seconds':2.4,'cube_top_steps_preserved':True,'cube_concept_asset':str(asset),'full_cube_web_viewport':True,'title_motion':'standalone title → same title continuously shrinks/moves into title-and-illustration → process prompt and process → demo','main_and_process_text_overlap':False,'balanced_chess_name':True,'gallery_concepts':'half line art, half colored architectural sketches','house_design':'lower 3D model only','native_ice_blue_roller':True,'separate_opening_part_removed':True,'standalone_title_before_each_chapter_layout':True,'continuous_title_zoom':True,'sky_continuous_take':True,'sky_body_seconds':25,'sky_hover_seconds':sky['hover_seconds'],'intro_layout_count':2,'total_duration_change_seconds_since_v9':0})
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
for kind,offset in [('projects',11),('titles',.8),('ideas',2.2),('introductions',4.0),('late-process',6.3)]:
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
lines+=['','All nine chapter videos are saved alongside the complete film.','Each chapter: condensed English idea prompt → build visualization → actual project footage. Bible now includes homepage selections, Sequence/Rebuild, and Next Word, at approximately 2× speed, in a complete natural viewport.','Final revision: Chess uses Chopin Raindrop; Bible uses Debussy Clair de lune; the art rooms use Chopin Nocturne; Sky uses Bach Air on the G String; Mozart continues through the games, roller coaster, and ending.','Journey of Art shows the actual Sweet Home 3D v3 preview moving from the owner-selected open camera, then the previous film’s gallery walk at native speed.','The 36.2-second roller coaster chapter comes last, followed by three closing questions, six seconds each, over the Mozart finale.','Chess: lobby, elevated live play, and the actual Weekly Comeback / Rockfall demos with brief rule labels.','Sky: one continuous 25-second take from native transition-room flight into the room, rotating while rising, then holding altitude for a downward orbit, under the Cosmic Cliffs sky.','Painterly Chameleon lasts 19.2 seconds. Coder footage is split evenly between Coder Arena and a genuine archival Monthly Ranking server battle.','Titles and ending use a faded, blurred picture from the owner-supplied Jesus opening. Small editorial text, branded headers, URLs, and footers have been removed. English. No narration or captured application audio.','See MUSIC-CREDITS.txt for the recording sources and attribution.']
(OUT/'START-HERE.txt').write_text('\n'.join(lines)+'\n')
with (OUT/'START-HERE.txt').open('a') as f:
    f.write('\nFinal revision 10: Chess starts the film directly with What Can Curiosity Build?; Cube restores Can We Build an 11×11 Cube?. Each project introduction begins with a standalone title. That same title continuously scales down and moves into the first text-left/picture-right layout: title and concept. The title then fades away and the process prompt appears, while the picture stays in place. Demo follows. No centered third layout or bottom step chain. Sky is a single native transition-entry-ascent-hover take. Duration stays 283.8 seconds; all fades and Chinese subtitle cues are synchronized to the revised clock. Half-colored gallery sketches, lower 3D model preview, full cube web viewport and native ice-blue roller shots are retained.\n')
print(json.dumps(report,indent=2))
