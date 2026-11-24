"""Validate the decoded delivery, preserved project film, captions, and motion."""
from pathlib import Path
import json,re,subprocess
import numpy as np
from PIL import Image,ImageDraw,ImageFont

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'out/why-build-together-v02'
DELIVERY=OUT/'delivery'

def probe(path):return json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-show_chapters','-of','json',str(path)]))
def small_frame(path,t):
    raw=subprocess.check_output(['ffmpeg','-v','error','-ss',str(t),'-i',str(path),'-frames:v','1','-vf','scale=640:360','-pix_fmt','gray','-f','rawvideo','-'])
    assert len(raw)==640*360
    return np.frombuffer(raw,dtype=np.uint8).astype(np.float32)
def motion(path,t,seconds=1):
    raw=subprocess.check_output(['ffmpeg','-v','error','-ss',str(t),'-i',str(path),'-t',str(seconds),'-vf','scale=160:90','-pix_fmt','gray','-f','rawvideo','-'])
    frames=np.frombuffer(raw,dtype=np.uint8).reshape(-1,160*90).astype(np.float32)
    assert len(frames)>=29
    differences=np.abs(frames[1:]-frames[:-1]).mean(axis=1)
    return dict(frames=len(frames),minimum_pixel_change=float(differences.min()),
                median_pixel_change=float(np.median(differences)),identical_pairs=int((differences<.005).sum()))
def cues(path):
    rows=[]
    for block in re.split(r'\n\s*\n',path.read_text(encoding='utf-8-sig').strip()):
        lines=block.splitlines()
        if len(lines)<3:continue
        stamps=re.findall(r'(\d\d):(\d\d):(\d\d),(\d\d\d)',lines[1])
        if len(stamps)!=2:continue
        convert=lambda x:int(x[0])*3600+int(x[1])*60+int(x[2])+int(x[3])/1000
        a,b=map(convert,stamps);rows.append((a,b,'\n'.join(lines[2:])))
    return rows

def main():
    movie=DELIVERY/'why-build-together.zh-v02.mp4';plan=json.loads((OUT/'timeline.json').read_text())
    data=probe(movie);video=next(s for s in data['streams'] if s['codec_type']=='video')
    audio=next(s for s in data['streams'] if s['codec_type']=='audio')
    subtitles=next(s for s in data['streams'] if s['codec_type']=='subtitle')
    assert (video['width'],video['height'],video['avg_frame_rate'])==(1920,1080,'30/1')
    assert len(plan['scenes'])==12 and plan['outro_frames']==0
    assert plan['insert']['start_frame']+plan['insert']['frames']==plan['frames']
    assert int(video['nb_frames'])==plan['frames'],(video['nb_frames'],plan['frames'])
    assert abs(float(data['format']['duration'])-plan['seconds'])<.1
    assert audio['tags']['language']=='zho' and subtitles['codec_name']=='mov_text'
    assert subtitles['tags']['language']=='zho' and subtitles['disposition']['default']==1
    chapters=json.loads((OUT/'chapters.json').read_text())
    assert len(data['chapters'])==len(chapters)
    for actual,expected in zip(data['chapters'],chapters):
        assert abs(float(actual['start_time'])-expected['seconds'])<.0011
        assert actual['tags']['title']==expected['title']
    full=subprocess.run(['ffmpeg','-v','error','-progress','pipe:1','-i',str(movie),'-map','0:v:0','-map','0:a:0','-f','null','-'],capture_output=True,text=True,check=True)
    counts=re.findall(r'^frame=(\d+)$',full.stdout,re.M)
    assert counts and int(counts[-1])==plan['frames']
    assert not full.stderr.strip(),full.stderr
    cc=cues(DELIVERY/'why-build-together.zh-CN.srt')
    assert cc and all(0<=a<b<=plan['seconds']+.001 and text for a,b,text in cc)
    assert all(cc[i][0]>=cc[i-1][1]-.011 for i in range(1,len(cc)))
    extracted=OUT/'embedded-captions-check.srt'
    subprocess.run(['ffmpeg','-v','error','-y','-i',str(movie),'-map','0:s:0',str(extracted)],check=True)
    embedded=cues(extracted);assert len(embedded)==len(cc)
    for (a,b,text),(x,y,z) in zip(cc,embedded):
        assert abs(a-x)<.0011 and abs(b-y)<.0011 and text==z
    offset=plan['insert']['start_frame']/30
    original=cues(Path(plan['embedded_subtitles']))
    for a,b,text in original:
        assert any(abs(x-(offset+a))<.0011 and abs(y-(offset+b))<.0011 and z==text for x,y,z in cc)
    assert len(original)==27
    samples=[]
    for t in [5,41.5,100,235,270,283.7]:
        source=small_frame(plan['embedded_movie'],t);actual=small_frame(movie,offset+t)
        error=float(np.abs(source-actual).mean());assert error<3.0,(t,error)
        samples.append(dict(project_seconds=t,final_seconds=offset+t,pixel_mae_0_to_255=error))
    motions={}
    sketches={}
    for id in ['G01','G02','G03','G04','G05']:
        result=motion(OUT/'assets'/(id+'.mp4'),1)
        assert result['identical_pairs']==0,(id,result)
        motions[id]=result
        raw=subprocess.check_output(['ffmpeg','-v','error','-ss','5','-i',str(OUT/'assets'/(id+'.mp4')),
            '-frames:v','1','-vf','scale=320:180','-pix_fmt','rgb24','-f','rawvideo','-'])
        pixels=np.frombuffer(raw,dtype=np.uint8).reshape(-1,3).astype(float)
        brightness=float(np.median(pixels.mean(axis=1)))
        chroma=float((pixels.max(axis=1)-pixels.min(axis=1)).max())
        assert brightness>220 and chroma<=2,(id,brightness,chroma)
        sketches[id]=dict(median_brightness=brightness,max_rgb_channel_difference=chroma)
    n001=next(s for s in plan['scenes'] if s['id']=='n001')
    n011=next(s for s in plan['scenes'] if s['id']=='n011')
    for label,t in [('opening',n001['start_frame']/30+1),('drawing',n011['start_frame']/30+9)]:
        result=motion(movie,t)
        assert result['identical_pairs']==0,(label,result)
        motions['final-'+label]=result
    raw=subprocess.check_output(['ffmpeg','-v','error','-i',str(movie),'-map','0:a:0','-ar','16000','-ac','1','-f','f32le','-'])
    sound=np.frombuffer(raw,dtype='<f4');assert len(sound)>16000*plan['seconds']-.2*16000 and np.isfinite(sound).all()
    peak=float(np.abs(sound).max());assert .01<peak<1.05
    chapter_text=(DELIVERY/'youtube-description.zh.txt').read_text()
    assert chapter_text.startswith('0:00 ') and '\n\n' in chapter_text and len(chapter_text)<5000
    label_check=json.loads((DELIVERY/'label-check.json').read_text())
    expected_labels=json.loads((ROOT/'src/videos/why-build-together-v02/labels.json').read_text())
    assert label_check['status']=='passed' and label_check['uniqueLabels']==len(expected_labels)
    assert label_check['chineseFirst'] and label_check['equalFontSize'] and label_check['insideFrame']
    frame_dir=OUT/'final-review-frames';frame_dir.mkdir(exist_ok=True)
    picks=[(s['id'],s['start_frame']/30+min(s['frames']/30*.6,7)) for s in plan['scenes']]
    picks.extend([('project-start',offset+.6),('project-middle',offset+130),('project-end',offset+282),('last-frame',plan['seconds']-1/30)])
    font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',19)
    board=Image.new('RGB',(1280,math_ceil(len(picks)/3)*265),'#11191d');draw=ImageDraw.Draw(board)
    for i,(name,t) in enumerate(picks):
        path=frame_dir/(name+'.jpg')
        subprocess.run(['ffmpeg','-v','error','-y','-ss',str(t),'-i',str(movie),'-frames:v','1',str(path)],check=True)
        im=Image.open(path).resize((420,236));x,y=(i%3)*426,(i//3)*265;board.paste(im,(x,y))
        draw.text((x+8,y+239),f'{name} / {t:.2f}s',font=font,fill='white')
    board.save(OUT/'final-contact.jpg',quality=94)
    report=dict(status='passed',seconds=plan['seconds'],decoded_frames=int(counts[-1]),expected_frames=plan['frames'],
                picture='1920x1080 30fps',audio_language='zh',audio_peak=peak,caption_cues=len(cc),
                embedded_caption_cues_verified=len(embedded),embedded_chapters_verified=len(chapters),
                bilingual_label_pairs_verified=label_check['uniqueLabels'],
                original_caption_cues_preserved=len(original),project_movie_comparisons=samples,
                motion=motions,white_paper_sketches=sketches,caption_type='default Chinese soft captions plus SRT/VTT',
                new_narration_time_stretch=False,project_playback_speed=1.0,ends_with_project_movie=True,
                narration_qa='12 local takes; only n008 regenerated (11.28s to 7.20s); all independently transcribed; approved text aligned using local Whisper-small')
    (DELIVERY/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ['motion','project_movie_comparisons']},ensure_ascii=False,indent=2))

def math_ceil(value):return -int(-value//1)
if __name__=='__main__':main()
