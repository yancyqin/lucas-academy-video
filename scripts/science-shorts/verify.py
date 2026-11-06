"""Validate rendered deliveries, original inputs and selected narration together."""
import argparse
import json
import re
import subprocess
from common import ROOT,PUBLIC,DOCS,OUT,SOURCE,sha,plans
from prepare import stamp


def probe(path):
    return json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(path)]))


def audio_hash(path,stream):
    return subprocess.check_output(['ffmpeg','-v','error','-i',str(path),'-map',stream,'-c:a','copy','-f','hash','-hash','sha256','-'],text=True).strip()


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--film');args=parser.parse_args()
    data=json.loads((PUBLIC/'data.json').read_text());choices=json.loads((DOCS/'voice-choices.json').read_text())
    assert len(choices)==sum(len(info['lines']) for info in SOURCE['films'].values())*2 and all(item['checked'] for item in choices.values())
    asr={}
    for name in ('small','medium'):
        asr.update(json.loads((DOCS/f'asr-{name}.json').read_text()))
    baseline=ROOT.parent/'lucas-academy-video-data/family-ai-lab-01/baseline-results'
    result_files={'x':'perceptron-js','claude':'claude-fable','astra':'astra-low','qwen':'qwen-fast'}
    original_hashes={}
    for key,name in result_files.items():
        path=ROOT/f'scripts/perceptron-race/results/{name}.json'
        assert sha(path)==sha(baseline/path.name),name
        assert json.loads(path.read_text())==data['metrics'][key]
        original_hashes[path.name]=sha(path)
    for asset in data['assets'].values():assert sha(PUBLIC/asset['path'])==asset['sha256']
    for lang in ('en','zh'):
        for row in plans(lang):
            decision=choices[f'{lang}/{row["id"]}'];name=row['id']+(f'.take{decision["take"]}' if decision.get('take') else '')
            assert asr[f'{lang}/{name}']['sha256']==decision['sha256']
            assert sha(PUBLIC/f'narration/{lang}/{row["id"]}.wav')==decision['sha256']
    previous=json.loads((DOCS/'verification.json').read_text()) if args.film and (DOCS/'verification.json').exists() else {}
    checked_films={name:item for name,item in previous.get('films',{}).items() if item.get('revision')==2}
    report={'revision':2,'originalResultSha256':original_hashes,'sourceClips':len(data['assets']),'selectedCheckedVoices':len(choices),'films':checked_films}
    for film in ('perceptron','optogenetics'):
        if args.film and args.film!=film:continue
        tl=json.loads((PUBLIC/f'timeline.{film}.json').read_text());assert tl['narrated']
        total=tl['durationInFrames'];fps=tl['fps'];folder=OUT/film;movie=folder/f'{film}.bilingual.mp4'
        assert tl['lines'][0]['from']==0
        for left,right in zip(tl['lines'],tl['lines'][1:]):assert left['from']+left['duration']==right['from']
        assert tl['lines'][-1]['from']+tl['lines'][-1]['duration']==total
        assert tl['shots'][0]['from']==0 and tl['shots'][-1]['from']+tl['shots'][-1]['duration']==total
        for left,right in zip(tl['shots'],tl['shots'][1:]):assert left['from']+left['duration']==right['from']
        for shot in tl['shots']:
            assert 0<shot['rate']<=1.35
            assert shot['in']+shot['duration']/fps*shot['rate']<=shot['out']+.001
            assert shot['out']<=data['assets'][shot['asset']]['seconds']+.001
        if film=='perceptron':
            race=next(line for line in tl['lines'] if line['id']=='p02')
            assert race['duration']/fps>data['metrics']['astra']['median_model']+.5
        for lang,filename in (('en','en'),('zh','zh-Hans')):
            blocks=re.split(r'\n\s*\n',(folder/f'{filename}.srt').read_text().strip())
            assert len(blocks)==len(tl['lines'])==11
            for index,(block,line) in enumerate(zip(blocks,tl['lines']),1):
                rows=block.splitlines();assert rows[0]==str(index)
                assert rows[1]==f'{stamp(line["from"]/fps)} --> {stamp((line["from"]+line["duration"]-round(.28*fps))/fps)}'
                assert re.sub(r'\s','',''.join(rows[2:]))==re.sub(r'\s','',line['text'][lang])
                voice=tl['voices'][lang][line['id']]
                assert sha(PUBLIC/voice['path'])==voice['sha256']
                assert voice['seconds']+.1<=line['duration']/fps
        info=probe(movie);streams=info['streams']
        video=[s for s in streams if s['codec_type']=='video'];audio=[s for s in streams if s['codec_type']=='audio']
        assert len(video)==1 and (video[0]['width'],video[0]['height'])==(1080,1920)
        assert video[0]['r_frame_rate']=='30/1' and int(video[0]['nb_frames'])==total
        assert not [s for s in streams if s['codec_type']=='subtitle']
        assert len(audio)==2 and [(s['tags']['language'],s['disposition']['default']) for s in audio]==[('eng',1),('zho',0)]
        assert all(s['codec_name']=='aac' and int(s['sample_rate'])==48000 for s in audio)
        assert abs(float(info['format']['duration'])-total/fps)<.1
        black=subprocess.run(['ffmpeg','-hide_banner','-threads','2','-i',str(movie),'-filter_threads','1','-vf','blackdetect=d=0.07:pix_th=0.06:pic_th=0.985','-an','-sn','-f','null','-'],capture_output=True,text=True,check=True)
        black_segments=[row for row in black.stderr.splitlines() if 'black_start:' in row];assert not black_segments,black_segments
        levels={}
        for index,lang in enumerate(('en','zh')):
            assert abs(float(audio[index]['duration'])-total/fps)<.1
            assert audio_hash(movie,f'0:a:{index}')==audio_hash(folder/f'{lang}.m4a','0:a:0'),(film,lang)
            checked=subprocess.run(['ffmpeg','-hide_banner','-i',str(movie),'-map',f'0:a:{index}','-af','loudnorm=I=-16:TP=-1:LRA=7:print_format=json','-f','null','-'],capture_output=True,text=True,check=True)
            levels[lang]=json.loads(checked.stderr[checked.stderr.rfind('{'):checked.stderr.rfind('}')+1])
            assert abs(float(levels[lang]['input_i'])+16)<.5 and float(levels[lang]['input_tp'])<0,(film,lang,levels[lang])
        frames=folder/'final-frames';frames.mkdir(exist_ok=True)
        for line in tl['lines']:
            seconds=(line['from']+int(line['duration']*.55))/fps
            subprocess.run(['ffmpeg','-v','error','-y','-ss',str(seconds),'-i',str(movie),'-frames:v','1','-vf','scale=540:960',str(frames/f'{line["id"]}.png')],check=True)
        qr=None
        if film=='perceptron':
            # The revised educational ending has no QR in either closing beat.
            scanner=ROOT/'tmp/science-shorts/scan-qr'
            subprocess.run(['swiftc',str(ROOT/'scripts/science-shorts/scan_qr.swift'),'-o',str(scanner)],check=True)
            for name in ('p10','p11'):
                found=subprocess.check_output([str(scanner),str(frames/f'{name}.png')],text=True).strip()
                assert not found,found
            qr='Absent from both revised closing beats'
        item={'revision':2,'durationSeconds':total/fps,'video':'1080x1920, 30fps','audio':[{'language':s['tags']['language'],'default':bool(s['disposition']['default'])} for s in audio],
              'subtitleTracks':0,'externalCuesPerLanguage':len(tl['lines']),'blackSegments':black_segments,'audioLoudness':levels,
              'standaloneAudio':'AAC payloads match the movie bit for bit','movingFootageCoverage':1.0,'shotCount':len(tl['shots']),
              'qrCheck':qr,'sha256':sha(movie),'bytes':movie.stat().st_size}
        report['films'][film]=item
        print(film,round(total/fps,2),'s; streams, captions, selected takes, source hashes, QR and levels passed',flush=True)
    (DOCS/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')


if __name__=='__main__':main()
