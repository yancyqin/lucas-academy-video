"""Check actual short-film streams, source integrity, story facts and QR."""
from pathlib import Path
import hashlib,json,re,subprocess

ROOT=Path(__file__).resolve().parents[2]
PUBLIC=ROOT/'public/family-ai-lab-02'
DATA=PUBLIC/'orbital-v2/short'
DOC=ROOT/'docs/family-ai-lab-02/design-v2/short'
OUT=ROOT/'out/family-ai-lab-02/orbital-v2/short'


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    tl=json.loads((DATA/'timeline.json').read_text());voices=json.loads((DATA/'narration.json').read_text());assert tl['scriptSha256']==sha(Path(__file__).with_name('short-script.json'))
    assert tl['museOriginalCount']==6 and tl['museCoverageFraction']>.7 and tl['cornerCredits'] is False
    full=json.loads((DOC.parent/'orbital-verification.json').read_text());assert sha(ROOT/full['movie'])==full['sha256']
    approved=json.loads((DOC/'short-voice-review.json').read_text());baseline=json.loads((PUBLIC/'orbital-v2/narration.json').read_text())
    at=0
    for row in tl['lines']:
        assert row['from']==at;at+=row['duration']
        for lang in ['en','zh']:
            voice=voices[lang][row['id']];assert voice['caption']==row[lang] and sha(PUBLIC/voice['clip'])==voice['sha256']
            if voice.get('reusedFromFull'):assert voice['sha256']==baseline[lang][row['id']]['sha256']
            else:
                decision=approved[lang+'/'+row['id']];assert decision['checked'] and decision['sha256']==voice['sha256']
            assert row['speechOffsetFrames']/30+voice['seconds']<row['duration']/30
    expected_cues=len(json.loads(Path(__file__).with_name('short-script.json').read_text())['lines'])
    assert len(tl['lines'])==expected_cues==11 and at==tl['durationInFrames']
    assert [r['visual'] for r in tl['lines'][-4:]]==['friends','world','online','invite']
    assert tl['lines'][-1]['en']=='A funny story? A new game? What will you share today?'
    assert 'AI' in tl['lines'][-2]['en'] and 'zeros and ones' in tl['lines'][-2]['en']
    originals=set();ranges={}
    for shot in tl['storyClips']:
        assert sha(ROOT/shot['original'])==shot['originalSha256'] and sha(PUBLIC/shot['src'])==shot['sha256'];originals.add(shot['original'])
        assert shot['from']>=0 and shot['from']+shot['duration']<=at and shot['speed']>0
        ranges.setdefault(shot['original'],[]).append((shot['sourceStartSeconds'],shot['sourceEndSeconds']))
    assert len(originals)==6
    for spans in ranges.values():
        spans.sort()
        for a,b in zip(spans,spans[1:]):assert a[1]<=b[0]
    facts=json.loads((PUBLIC/'facts.json').read_text());assert facts['message']=='PLAY' and len(facts['messageBits'])==32 and facts['boxPath'][-1]['remaining']==[7]
    movie=OUT/'delivery/family-ai-lab-02.short.bilingual.mp4';p=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(movie)]));video=[s for s in p['streams'] if s['codec_type']=='video'];audio=[s for s in p['streams'] if s['codec_type']=='audio']
    expected=(1080,1920) if tl['aspect']=='portrait' else (1920,1080)
    assert len(video)==1 and (video[0]['width'],video[0]['height'])==expected and int(video[0]['nb_frames'])==at and video[0]['r_frame_rate']=='30/1'
    assert len(audio)==2 and [(s['tags']['language'],s['disposition']['default']) for s in audio]==[('eng',1),('zho',0)]
    assert not any(s['codec_type']=='subtitle' for s in p['streams']) and all(abs(float(s['duration'])-at/30)<.1 for s in audio)
    for lang,name in [('en','en'),('zh','zh-Hans')]:
        srt=(DATA/(lang+'.srt')).read_text();assert srt==(OUT/'delivery'/(name+'.srt')).read_text();blocks=re.split(r'\n\s*\n',srt.strip());assert len(blocks)==expected_cues
        for block,row in zip(blocks,tl['lines']):assert ''.join(block.splitlines()[2:])==row[lang]
    black=subprocess.run(['ffmpeg','-hide_banner','-i',str(movie),'-vf','blackdetect=d=0.07:pix_th=0.06:pic_th=0.985','-an','-sn','-f','null','-'],text=True,capture_output=True,check=True);assert 'black_start:' not in black.stderr
    levels={}
    for i,lang in enumerate(['en','zh']):
        r=subprocess.run(['ffmpeg','-hide_banner','-i',str(movie),'-map',f'0:a:{i}','-af','loudnorm=I=-16:TP=-1:LRA=7:print_format=json','-f','null','-'],text=True,capture_output=True,check=True);m=json.loads(r.stderr[r.stderr.rfind('{'):r.stderr.rfind('}')+1]);assert -16.6<float(m['input_i'])<-15.4 and float(m['input_tp'])<0;levels[lang]={'integratedLUFS':m['input_i'],'truePeakDBTP':m['input_tp']}
    last=tl['lines'][-1];seconds=(last['from']+int(last['duration']*.65))/30;qr=OUT/'final-qr.png';subprocess.run(['ffmpeg','-v','error','-y','-ss',str(seconds),'-i',str(movie),'-frames:v','1',str(qr)],check=True)
    binary=ROOT/'tmp/family-ai-lab-02/verify-qr';binary.parent.mkdir(parents=True,exist_ok=True)
    if not binary.exists():subprocess.run(['swiftc','-module-cache-path',str(binary.parent/'swift-cache'),str(Path(__file__).with_name('verify_qr.swift')),'-o',str(binary)],check=True)
    subprocess.run([str(binary),str(qr)],check=True)
    small=OUT/'final-qr-720.png';subprocess.run(['ffmpeg','-v','error','-y','-i',str(qr),'-vf','scale=720:-2','-frames:v','1',str(small)],check=True);subprocess.run([str(binary),str(small)],check=True)
    report={'movie':str(movie.relative_to(ROOT)),'sha256':sha(movie),'seconds':at/30,'frames':at,'size':list(expected),'fps':30,'museOriginals':6,'museSeconds':tl['museCoverageSeconds'],'museCoverageFraction':tl['museCoverageFraction'],'forwardSpansWithoutLoops':True,'fullFilmUnchanged':True,'audioTracks':['English default','Chinese'],'subtitleTracks':0,'externalSRTs':{'en':expected_cues,'zh-Hans':expected_cues},'audioLoudness':levels,'blackSegments':[],'qrDecodedAt':['native','720px width'],'ending':['two friends','internet','AI chats','playful sharing question']}
    (DOC/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');(OUT/'delivery/verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
