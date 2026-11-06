"""Prepare inspected Muse spans and an independent voiced orbital timeline."""
from pathlib import Path
import argparse,hashlib,json,math,subprocess

ROOT=Path(__file__).resolve().parents[2]
PUBLIC=ROOT/'public/family-ai-lab-02'
DOC=ROOT/'docs/family-ai-lab-02/design-v2'
DEST=PUBLIC/'orbital-v2'
FPS=30


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare_clips():
    inputs=json.loads((DOC/'clips.json').read_text())['clips']
    # Preserve the complete source files. Only these clearly observed spans
    # become the local editing derivatives; no shot is reversed or looped.
    spans={'G1a':(.8,6.6,1.8),'G1b':(.2,6.2,6.0),'G2':(1.0,6.0,5.0),'G3':(.2,6.0,5.8),'G4':(.2,5.2,5.0),'G5':(0.0,2.4,2.4)}
    folder=DEST/'clips';folder.mkdir(parents=True,exist_ok=True);result={}
    for source in inputs:
        key=source['id'];start,end,duration=spans[key];original=ROOT/source['file'];assert sha(original)==source['sha256']
        frames=round(duration*FPS);video=folder/(key+'.mp4');last=folder/(key+'-last.png');speed=(end-start)/duration
        filters=f'setpts=(PTS-STARTPTS)/{speed:.9f},fps=30,scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,setsar=1,format=yuv420p,tpad=stop_mode=clone:stop_duration=0.2'
        subprocess.run(['ffmpeg','-v','error','-y','-ss',str(start),'-t',str(end-start),'-i',str(original),'-an','-vf',filters,'-frames:v',str(frames),'-c:v','libx264','-crf','18','-preset','fast','-movflags','+faststart',str(video)],check=True)
        probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(video)]));stream=probe['streams'][0]
        assert int(stream['nb_frames'])==frames and stream['width']==1920 and stream['height']==1080 and len(probe['streams'])==1
        subprocess.run(['ffmpeg','-v','error','-y','-i',str(video),'-vf',f'select=eq(n\\,{frames-1})','-fps_mode','vfr','-frames:v','1',str(last)],check=True)
        result[key]={'id':key,'src':str(video.relative_to(PUBLIC)),'lastFrame':str(last.relative_to(PUBLIC)),'frames':frames,'seconds':duration,'sha256':sha(video),'lastFrameSha256':sha(last),'original':source['file'],'originalSha256':source['sha256'],'sourceStartSeconds':start,'sourceEndSeconds':end,'speed':speed,'treatment':'One forward span, muted, 1080p/30 fps; last real frame held only when a narration cue extends beyond the span.'}
        print('Prepared',key,frames,'frames',flush=True)
    (DEST/'story-clips.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    (DOC/'story-clips.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')


def stamp(frame):
    ms=round(frame/FPS*1000);h,ms=divmod(ms,3600000);m,ms=divmod(ms,60000);s,ms=divmod(ms,1000)
    return f'{h:02}:{m:02}:{s:02},{ms:03}'


def build():
    script_path=Path(__file__).parent/'orbital-script.json';script=json.loads(script_path.read_text());voices=json.loads((DEST/'narration.json').read_text());clips=json.loads((DEST/'story-clips.json').read_text())
    rows=[];frame=0
    for line in script['lines']:
        seconds={lang:voices[lang][line['id']]['seconds'] for lang in ('en','zh')}
        for lang in seconds:assert voices[lang][line['id']]['caption']==line[lang],('Stale orbital voice',line['id'],lang)
        lead=round(line.get('leadInSeconds',0)*FPS);body=max(math.ceil((max(seconds.values())+.1)*FPS)+lead,round(line.get('minSeconds',0)*FPS))
        duration=body+round((.4+line.get('hold',0)+line.get('afterHoldSeconds',0))*FPS)
        rows.append({**line,'from':frame,'duration':duration,'speechOffsetFrames':lead+3,'bodyDurationFrames':body,'voiceSeconds':seconds});frame+=duration
    lookup={row['visual']:row for row in rows};story=[]
    def shot(key,visual,offset=0,duration=None):
        row=lookup[visual];story.append({**clips[key],'from':row['from']+offset,'duration':duration if duration is not None else row['duration']-offset})
    shot('G1a','world',duration=clips['G1a']['frames']);shot('G1b','world',offset=clips['G1a']['frames']);shot('G2','received');shot('G3','boxes')
    shot('G4','fruit-seeds',offset=lookup['fruit-seeds']['bodyDurationFrames'])
    shot('G5','picnic',duration=clips['G5']['frames'])
    for clip in story:assert clip['duration']>0
    timeline={'fps':FPS,'durationInFrames':frame,'narrated':True,'defaultLanguage':'en','scenes':script['scenes'],'workingTitle':script['workingTitle'],'lines':rows,'storyClips':story,'scriptSha256':sha(script_path),'visualStyle':'orbital-v2','cornerCredits':False,'delivery':'One clean picture, English default, independent Chinese audio, external subtitles only.'}
    (DEST/'timeline.json').write_text(json.dumps(timeline,ensure_ascii=False,indent=2)+'\n');(DOC/'orbital-timeline.json').write_text(json.dumps(timeline,ensure_ascii=False,indent=2)+'\n')
    for lang in ('en','zh'):
        captions=[];paragraphs=['# '+script['workingTitle'][lang]]
        for i,row in enumerate(rows,1):
            start=row['from']+row['speechOffsetFrames'];end=start+math.ceil((row['voiceSeconds'][lang]+.1)*FPS);assert end<row['from']+row['duration']
            captions.append(f'{i}\n{stamp(start)} --> {stamp(end)}\n{row[lang]}\n')
            paragraphs.extend(['\n## '+row['id'],row[lang]])
        (DEST/(lang+'.srt')).write_text('\n'.join(captions)+'\n');(DOC/f'orbital-script.{lang}.md').write_text('\n\n'.join(paragraphs)+'\n')
    print('Built orbital film:',frame,'frames,',frame/FPS,'seconds; 36 cue pairs and six story spans.')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--clips',action='store_true');args=parser.parse_args()
    prepare_clips() if args.clips else build()
