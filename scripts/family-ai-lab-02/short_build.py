"""Fit the story and Internet/AI ending to actual bilingual speech."""
from pathlib import Path
import hashlib,json,math,subprocess
from orbital_build import stamp

ROOT=Path(__file__).resolve().parents[2]
PUBLIC=ROOT/'public/family-ai-lab-02'
DEST=PUBLIC/'orbital-v2/short'
DOC=ROOT/'docs/family-ai-lab-02/design-v2/short'
FPS=30


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    script_path=Path(__file__).with_name('short-script.json');script=json.loads(script_path.read_text());voices=json.loads((DEST/'narration.json').read_text())
    rows=[];at=0
    for row in script['lines']:
        seconds={lang:voices[lang][row['id']]['seconds'] for lang in ['en','zh']}
        assert all(voices[lang][row['id']]['caption']==row[lang] for lang in seconds)
        lead=round(row.get('leadInSeconds',0)*FPS)+3
        duration=max(round(row['minSeconds']*FPS),math.ceil(max(seconds.values())*FPS)+lead+12)
        rows.append({**row,'from':at,'duration':duration,'speechOffsetFrames':lead,'voiceSeconds':seconds});at+=duration
    by_visual={r['visual']:r for r in rows};originals={r['id']:r for r in json.loads((DOC.parent/'clips.json').read_text())['clips']}
    # The ending uses previously unused tails in forward source order.
    # Each original's intervals are disjoint; no shot is looped or reversed.
    specs=[('paper','G1b',.2,7.7,0,None),('code','G1a',.8,7.8,0,None),('arrival','G2',1,6,0,None),('cargo','G3',.2,6,0,None),('snack','G4',.2,5.2,33,None),('reply','G5',0,5.8,0,None),('friends','G1b',7.7,10,0,None),('world','G1a',7.8,10,0,None),('online','G5',5.8,10,0,None),('invite','G4',5.2,9.6,0,None)]
    folder=DEST/'clips';folder.mkdir(parents=True,exist_ok=True);old=json.loads((DEST/'clips.json').read_text()) if (DEST/'clips.json').exists() else {};clips=[]
    for visual,origin,start,end,offset,limit in specs:
        cue=by_visual[visual];frames=min(limit,cue['duration']-offset) if limit else cue['duration']-offset;assert frames>0
        original=originals[origin];source=ROOT/original['file'];assert sha(source)==original['sha256']
        name=origin+'-'+visual;video=folder/(name+'.mp4');last=folder/(name+'-last.png');speed=(end-start)/(frames/FPS)
        signature=hashlib.sha256(json.dumps([original['sha256'],start,end,frames]).encode()).hexdigest();cached=old.get(visual,{})
        valid=cached.get('signature')==signature and video.exists() and last.exists() and sha(video)==cached.get('sha256') and sha(last)==cached.get('lastFrameSha256')
        if not valid:
            filters=f'setpts=(PTS-STARTPTS)/{speed:.9f},fps=30,scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,setsar=1,format=yuv420p,tpad=stop_mode=clone:stop_duration=0.15'
            subprocess.run(['ffmpeg','-v','error','-y','-ss',str(start),'-t',str(end-start),'-i',str(source),'-an','-vf',filters,'-frames:v',str(frames),'-c:v','libx264','-crf','18','-preset','fast','-movflags','+faststart',str(video)],check=True)
            subprocess.run(['ffmpeg','-v','error','-y','-i',str(video),'-vf',f'select=eq(n\\,{frames-1})','-fps_mode','vfr','-frames:v','1',str(last)],check=True)
        probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-of','json',str(video)]));assert len(probe['streams'])==1 and int(probe['streams'][0]['nb_frames'])==frames
        clips.append({'id':origin,'visual':visual,'from':cue['from']+offset,'duration':frames,'frames':frames,'src':str(video.relative_to(PUBLIC)),'lastFrame':str(last.relative_to(PUBLIC)),'sha256':sha(video),'lastFrameSha256':sha(last),'original':original['file'],'originalSha256':original['sha256'],'sourceStartSeconds':start,'sourceEndSeconds':end,'speed':speed,'signature':signature})
        print('Prepared short shot',visual,round(frames/FPS,2),'s',flush=True)
    coverage=sum(c['duration'] for c in clips)
    timeline={'fps':FPS,'durationInFrames':at,'aspect':script['aspect'],'workingTitle':script['workingTitle'],'lines':rows,'storyClips':clips,'museOriginalCount':6,'museCoverageSeconds':coverage/FPS,'museCoverageFraction':coverage/at,'scriptSha256':sha(script_path),'cornerCredits':False,'defaultLanguage':'en','delivery':'One picture, English default and Chinese independent audio, external SRTs only.'}
    assert coverage/at>.7
    (DEST/'timeline.json').write_text(json.dumps(timeline,ensure_ascii=False,indent=2)+'\n');(DOC/'short-timeline.json').write_text(json.dumps(timeline,ensure_ascii=False,indent=2)+'\n')
    receipt={c['visual']:c for c in clips};(DEST/'clips.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n');(DOC/'short-clips.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
    for lang in ['en','zh']:
        captions=[];script_lines=['# '+script['workingTitle'][lang]]
        for i,row in enumerate(rows,1):
            start=row['from']+row['speechOffsetFrames'];end=start+math.ceil(row['voiceSeconds'][lang]*FPS)+2;assert end<row['from']+row['duration']
            captions.append(f'{i}\n{stamp(start)} --> {stamp(end)}\n{row[lang]}\n');script_lines.extend(['\n## '+row['id'],row[lang]])
        (DEST/(lang+'.srt')).write_text('\n'.join(captions)+'\n');(DOC/f'short-script.{lang}.md').write_text('\n\n'.join(script_lines)+'\n')
    print('Built short:',round(at/FPS,2),'s;',round(coverage/at*100,1),'% moving Muse footage, 6 originals.')


if __name__=='__main__':main()
