"""Verify the actual orbital delivery, source media, voices, captions and QR."""
from pathlib import Path
import hashlib,json,math,re,subprocess

ROOT=Path(__file__).resolve().parents[2]
PUBLIC=ROOT/'public/family-ai-lab-02'
DATA=PUBLIC/'orbital-v2'
DOC=ROOT/'docs/family-ai-lab-02/design-v2'
OUT=ROOT/'out/family-ai-lab-02/orbital-v2'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    tl=json.loads((DATA/'timeline.json').read_text());voices=json.loads((DATA/'narration.json').read_text());facts=json.loads((PUBLIC/'facts.json').read_text())
    assert tl['narrated'] and tl['visualStyle']=='orbital-v2' and tl['cornerCredits'] is False
    assert tl['scriptSha256']==sha(Path(__file__).parent/'orbital-script.json')
    frozen=json.loads((DOC.parent/'sources.json').read_text())['sources']
    for source in frozen:assert sha(PUBLIC/source['path'])==source['sha256'],source['path']
    artwork=json.loads((DOC/'assets.json').read_text())['assets']+json.loads((DOC/'full-film-prompts.json').read_text())['assets']
    for asset in artwork:assert sha(ROOT/asset['asset'])==asset['sha256'],asset['asset']
    old_choices=json.loads((DOC.parent/'voice-choices.json').read_text());new_choices=json.loads((DOC/'orbital-voice-review.json').read_text())
    assert facts['codes']['A']=={'number':65,'bits':'01000001'}
    assert ''.join(chr(int(facts['messageBits'][i:i+8],2)) for i in range(0,32,8))=='PLAY'
    assert [row['remaining'] for row in facts['boxPath']]==[[6,7,8,9,10],[6,7,8],[7,8],[7]]
    position=0
    for row in tl['lines']:
        assert row['from']==position;position+=row['duration']
        for lang in ('en','zh'):
            entry=voices[lang][row['id']]
            assert entry['caption']==row[lang] and sha(PUBLIC/entry['clip'])==entry['sha256']
            decision=(old_choices if entry['reusedFromV1'] else new_choices)[f'{lang}/{row["id"]}']
            assert decision['checked'] and decision['sha256']==entry['sha256']
            assert row['speechOffsetFrames']/30+entry['seconds']<row['duration']/30
    assert len(tl['lines'])==36 and position==tl['durationInFrames']
    originals=json.loads((DOC/'clips.json').read_text())['clips'];clips=json.loads((DATA/'story-clips.json').read_text())
    for row in originals:assert sha(ROOT/row['file'])==row['sha256']
    for row in clips.values():
        assert sha(PUBLIC/row['src'])==row['sha256'] and sha(PUBLIC/row['lastFrame'])==row['lastFrameSha256']
        assert row['sourceStartSeconds']<row['sourceEndSeconds'] and row['speed']>0
    assert len(tl['storyClips'])==6
    for shot in tl['storyClips']:assert shot['from']>=0 and shot['from']+shot['duration']<=position
    paper=next(shot for shot in tl['storyClips'] if shot['id']=='G1b');launch=next(shot for shot in tl['storyClips'] if shot['id']=='G1a')
    assert paper['from']==0 and paper['duration']==225 and paper['frames']>=paper['duration']
    assert abs(launch['from']/30-22.4)<1
    challenge=next(row for row in tl['lines'] if row['visual']=='challenge');explanation=next(row for row in tl['lines'] if row['visual']=='one-bit')
    assert launch['from']>=challenge['from']+challenge['speechOffsetFrames']+math.ceil(max(challenge['voiceSeconds'].values())*30)
    assert launch['from']+launch['duration']==explanation['from']
    assert explanation['en'].startswith('Yes!') and explanation['zh'].startswith('可以！')
    assert tl['workingTitle']=={'en':'Can 0 and 1 Talk?','zh':'0和1，能聊天吗？'}
    for first,second in zip(sorted(tl['storyClips'],key=lambda shot:shot['from']),sorted(tl['storyClips'],key=lambda shot:shot['from'])[1:]):assert first['from']+first['duration']<=second['from']
    seed=next(row for row in tl['lines'] if row['visual']=='fruit-seeds');reveal=next(row for row in tl['storyClips'] if row['id']=='G4');assert reveal['from']>=seed['from']+seed['bodyDurationFrames']
    for lang,file in [('en','en'),('zh','zh-Hans')]:
        srt=(DATA/(lang+'.srt')).read_text();assert srt==(OUT/'delivery'/(file+'.srt')).read_text()
        blocks=re.split(r'\n\s*\n',srt.strip());assert len(blocks)==36
        for block,row in zip(blocks,tl['lines']):assert ''.join(block.splitlines()[2:])==row[lang]
    movie=OUT/'delivery/family-ai-lab-02.bilingual.mp4'
    probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(movie)]))
    video=[s for s in probe['streams'] if s['codec_type']=='video'];audio=[s for s in probe['streams'] if s['codec_type']=='audio'];subs=[s for s in probe['streams'] if s['codec_type']=='subtitle']
    assert len(video)==1 and video[0]['width']==1920 and video[0]['height']==1080 and int(video[0]['nb_frames'])==position
    assert video[0]['r_frame_rate']=='30/1' and len(audio)==2 and not subs
    assert [s['tags']['language'] for s in audio]==['eng','zho'] and [s['disposition']['default'] for s in audio]==[1,0]
    assert abs(float(probe['format']['duration'])-position/30)<.1
    assert all(s['codec_name']=='aac' and abs(float(s['duration'])-position/30)<.1 for s in audio)
    black=subprocess.run(['ffmpeg','-hide_banner','-i',str(movie),'-vf','blackdetect=d=0.07:pix_th=0.06:pic_th=0.985','-an','-sn','-f','null','-'],text=True,capture_output=True,check=True)
    assert 'black_start:' not in black.stderr
    levels=[]
    for i in range(2):
        result=subprocess.run(['ffmpeg','-hide_banner','-i',str(movie),'-map',f'0:a:{i}','-af','loudnorm=I=-16:TP=-1:LRA=7:print_format=json','-f','null','-'],text=True,capture_output=True,check=True)
        value=json.loads(result.stderr[result.stderr.rfind('{'):result.stderr.rfind('}')+1]);levels.append(value)
        assert -16.5<float(value['input_i'])<-15.5 and float(value['input_tp'])<-.5
    temp=ROOT/'tmp/family-ai-lab-02';binary=temp/'verify-qr'
    if not binary.exists():subprocess.run(['swiftc','-module-cache-path',str(temp/'swift-cache'),str(Path(__file__).parent/'verify_qr.swift'),'-o',str(binary)],check=True)
    qr=[]
    for visual in ('lab','worksheet','invite'):
        cue=next(row for row in tl['lines'] if row['visual']==visual);second=(cue['from']+int(cue['duration']*.62))/30;image=OUT/f'final-qr-{visual}.png'
        subprocess.run(['ffmpeg','-v','error','-y','-ss',str(second),'-i',str(movie),'-frames:v','1',str(image)],check=True)
        subprocess.run([str(binary),str(image)],check=True)
        small=OUT/f'final-qr-{visual}-720.png';subprocess.run(['ffmpeg','-v','error','-y','-i',str(image),'-vf','scale=1280:720','-frames:v','1',str(small)],check=True);subprocess.run([str(binary),str(small)],check=True)
        qr.append({'visual':visual,'seconds':second,'decodedAt':['1080p','720p']})
    cover=json.loads((DOC/'cover.json').read_text())
    assert cover['sourceFrame']==0 and cover['sourceMovieSha256']==sha(movie) and cover['titles']==tl['workingTitle']
    def frame_pixels(path):return subprocess.check_output(['ffmpeg','-v','error','-i',str(path),'-map','0:v:0','-frames:v','1','-pix_fmt','rgb24','-f','hash','-hash','sha256','-']).decode().strip()
    assert frame_pixels(movie)==frame_pixels(OUT/'cover/first-frame.png')
    for lang,row in cover['covers'].items():
        path=ROOT/row['file'];assert path.stat().st_size<2_000_000 and sha(path)==row['sha256']
        dims=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','stream=width,height','-of','json',str(path)]))['streams'][0]
        assert (dims['width'],dims['height'])==(1280,720) and row['unchangedOutsideTitle']
    result={'movie':str(movie.relative_to(ROOT)),'durationSeconds':position/30,'frames':position,'size':[1920,1080],'fps':30,'sha256':sha(movie),'nativeMuseClips':6,'originalMuseSeconds':sum(x['durationSeconds'] for x in originals),'selectedVoiceTakes':72,'reusedV1Takes':sum(x.get('reusedFromV1',False) for v in voices.values() for x in v.values()),'audioTracks':[{'language':'English','default':True},{'language':'Chinese','default':False}],'loudness':levels,'subtitleTracks':0,'externalSRTs':{'en':36,'zh-Hans':36},'cornerCredits':False,'blackSegments':[],'qr':qr,'sourceScriptSha256':tl['scriptSha256'],'visualSourceSha256':sha(ROOT/'src/videos/family-ai-lab-02/FamilyAiLab02Orbital.tsx')}
    result.update(sourceHashesVerified=len(frozen),artworkHashesVerified=len(artwork),voiceDecisionsVerified=72,opening=tl['opening'],covers={'sourceFrame':0,'pixelMatchToFinalFilm':True,'titles':cover['titles'],'files':{lang:row['file'] for lang,row in cover['covers'].items()}})
    (DOC/'orbital-verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    (OUT/'delivery/verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ['movie','durationSeconds','frames','sha256','cornerCredits','sourceHashesVerified','artworkHashesVerified','voiceDecisionsVerified']},ensure_ascii=False))


if __name__=='__main__':main()
