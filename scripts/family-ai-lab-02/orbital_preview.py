"""Export the complete opening, affirmative answer and first explanation."""
from pathlib import Path
import argparse,hashlib,json,subprocess

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'out/family-ai-lab-02/orbital-v2'


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--picture',type=Path,help='Completed first render chunk, or a complete film');args=parser.parse_args()
    source=args.picture or OUT/'delivery/family-ai-lab-02.bilingual.mp4'
    if not source.is_absolute():source=ROOT/source
    if source.parent.name.startswith('chunks-'):
        receipt=json.loads(source.with_suffix('.mp4.json').read_text())
        assert receipt['start']==0 and hashlib.sha256(source.read_bytes()).hexdigest()==receipt['sha256']
    tl=json.loads((ROOT/'public/family-ai-lab-02/orbital-v2/timeline.json').read_text())
    cue=next(row for row in tl['lines'] if row['visual']=='one-bit');frames=cue['from']+cue['duration']
    target=OUT/'delivery/opening-yes.mp4'
    subprocess.run(['ffmpeg','-v','error','-y','-i',str(source),'-i',str(OUT/'audio/en.wav'),'-i',str(OUT/'audio/zh.wav'),'-t',str(frames/30),'-map','0:v:0','-map','1:a:0','-map','2:a:0','-map_metadata','-1','-vf','scale=1280:720','-frames:v',str(frames),'-c:v','libx264','-crf','20','-preset','fast','-c:a','aac','-b:a','192k','-metadata','title='+tl['workingTitle']['en'],'-metadata:s:a:0','language=eng','-metadata:s:a:1','language=zho','-metadata:s:a:0','title=English — Louise','-metadata:s:a:1','title=中文 — Louise','-disposition:a:0','default','-disposition:a:1','0','-movflags','+faststart',str(target)],check=True)
    probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-of','json',str(target)]))
    assert int(probe['streams'][0]['nb_frames'])==frames
    assert [(s['tags']['language'],s['disposition']['default']) for s in probe['streams'] if s['codec_type']=='audio']==[('eng',1),('zho',0)]
    assert not any(s['codec_type']=='subtitle' for s in probe['streams'])
    report={'file':str(target.relative_to(ROOT)),'frames':frames,'seconds':frames/30,'size':[1280,720],'audioTracks':['English default','Chinese'],'scope':'Complete S1, including the moved launch, explicit Yes / 可以, and the complete first explanation.','opening':tl['opening'],'sha256':hashlib.sha256(target.read_bytes()).hexdigest()}
    (ROOT/'docs/family-ai-lab-02/design-v2/opening-preview.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False))


if __name__=='__main__':main()
