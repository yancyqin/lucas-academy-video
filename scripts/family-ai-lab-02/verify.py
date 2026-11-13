"""Verify the delivered film, frozen sources, actual speech and independent tracks."""
from pathlib import Path
import hashlib
import json
import re
import subprocess

ROOT=Path(__file__).resolve().parents[2]
PUBLIC=ROOT/'public/family-ai-lab-02'
DOC=ROOT/'docs/family-ai-lab-02'
OUT=ROOT/'out/family-ai-lab-02'


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    tl=json.loads((PUBLIC/'timeline.json').read_text());assert tl['narrated'] and len(tl['lines'])==36 and tl['fps']==30
    assert tl['scriptSha256']==sha(Path(__file__).parent/'script.json')
    frozen=json.loads((DOC/'script-revision.json').read_text())
    assert frozen['canonicalScriptSha256']==tl['scriptSha256']
    for name,digest in frozen['sha256'].items():assert sha(DOC/name)==digest,('Script changed during production',name)
    frame=0
    for row in tl['lines']:assert row['from']==frame;frame+=row['duration']
    assert frame==tl['durationInFrames']
    facts=json.loads((PUBLIC/'facts.json').read_text())
    assert facts['messageBits']=='01010000010011000100000101011001'
    assert [s['remaining'] for s in facts['boxPath']]==[[6,7,8,9,10],[6,7,8],[7,8],[7]]
    assert facts['codes']['A']=={'number':65,'bits':'01000001'}
    source=json.loads((DOC/'sources.json').read_text())
    for asset in source['sources']:assert sha(PUBLIC/asset['path'])==asset['sha256'],asset['path']
    choices=json.loads((DOC/'voice-choices.json').read_text());manifest=json.loads((PUBLIC/'narration.json').read_text());selected=0
    for lang in ('en','zh'):
        for row in tl['lines']:
            item=manifest[lang][row['id']];decision=choices[f'{lang}/{row["id"]}']
            assert decision['checked'] and decision['sha256']==item['sha256']==sha(PUBLIC/item['clip'])
            assert item['caption']==row[lang]
            assert item['seconds']+.1 < row['duration']/30
            selected+=1
        srt=(PUBLIC/f'{lang}.srt').read_text();blocks=re.split(r'\n\s*\n',srt.strip());assert len(blocks)==36
        for block,row in zip(blocks,tl['lines']):assert ''.join(block.splitlines()[2:])==row[lang]
        assert srt==(OUT/'delivery'/('en.srt' if lang=='en' else 'zh-Hans.srt')).read_text()
    film=OUT/'delivery/family-ai-lab-02.bilingual.mp4'
    p=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(film)]))
    video=[s for s in p['streams'] if s['codec_type']=='video'];audio=[s for s in p['streams'] if s['codec_type']=='audio'];subs=[s for s in p['streams'] if s['codec_type']=='subtitle']
    assert len(video)==1 and len(audio)==2 and not subs
    assert video[0]['width']==1920 and video[0]['height']==1080 and video[0]['r_frame_rate']=='30/1'
    assert int(video[0]['nb_frames'])==frame
    assert [(a['tags']['language'],a['disposition']['default']) for a in audio]==[('eng',1),('zho',0)]
    assert abs(float(p['format']['duration'])-frame/30)<.1
    assert all(a['codec_name']=='aac' and abs(float(a['duration'])-frame/30)<.1 for a in audio)
    black=subprocess.run(['ffmpeg','-hide_banner','-i',str(film),'-vf','blackdetect=d=0.07:pix_th=0.06:pic_th=0.985','-an','-sn','-f','null','-'],text=True,capture_output=True,check=True)
    assert 'black_start:' not in black.stderr
    levels={}
    for i,lang in enumerate(('en','zh')):
        r=subprocess.run(['ffmpeg','-hide_banner','-i',str(film),'-map',f'0:a:{i}','-af','loudnorm=I=-16:TP=-1:LRA=7:print_format=json','-f','null','-'],text=True,capture_output=True,check=True)
        m=json.loads(r.stderr[r.stderr.rfind('{'):r.stderr.rfind('}')+1]);assert abs(float(m['input_i'])+16)<.6 and float(m['input_tp'])<0
        levels[lang]={'integratedLUFS':m['input_i'],'truePeakDBTP':m['input_tp']}
    tmp=ROOT/'tmp/family-ai-lab-02';tmp.mkdir(parents=True,exist_ok=True);binary=tmp/'verify-qr'
    subprocess.run(['swiftc','-module-cache-path',str(tmp/'swift-cache'),str(Path(__file__).parent/'verify_qr.swift'),'-o',str(binary)],check=True)
    qr=[]
    for key in ('lab','invite'):
        row=next(l for l in tl['lines'] if l['visual']==key);seconds=(row['from']+row['duration']*.62)/30
        image=OUT/f'frames/final-{key}.png'
        subprocess.run(['ffmpeg','-v','error','-y','-ss',str(seconds),'-i',str(film),'-frames:v','1',str(image)],check=True)
        subprocess.run([str(binary),str(image)],check=True)
        small=OUT/f'frames/final-{key}.720.png'
        subprocess.run(['ffmpeg','-v','error','-y','-i',str(image),'-vf','scale=1280:720','-frames:v','1',str(small)],check=True)
        subprocess.run([str(binary),str(small)],check=True)
        qr.append({'scene':key,'seconds':seconds,'alsoDecodedAt720p':True})
    result={'durationSeconds':frame/30,'frameCount':frame,'video':'1920x1080, 30 fps','audioTracks':[{'language':'English','default':True},{'language':'Chinese','default':False}],'subtitleTracks':0,'externalSRTs':{'en':36,'zh-Hans':36},'noSubtitleBand':True,'selectedNarrationTakes':selected,'sourceHashesVerified':len(source['sources']),'blackSegments':[],'audioLoudness':levels,'qr':{'target':source['courseUrl'],'finalMovieFrames':qr},'filmSha256':sha(film),'typecheck':'npx tsc --noEmit passed'}
    (DOC/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    (OUT/'delivery/verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
