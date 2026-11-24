"""Validate actual decoded media, preserved picture/audio, and revised captions."""
from pathlib import Path
import hashlib,json,re,subprocess
import numpy as np
import soundfile as sf

ROOT=Path(__file__).resolve().parents[2]
DATA=ROOT.parent/'lucas-academy-video-data/why-build-together-20261122/english-owner-track-v05'
OLD=ROOT.parent/'lucas-academy-video-data/why-build-together-20261122/v04'
D=DATA/'delivery'

def cues(path):
    result=[]
    for block in re.split(r'\n\s*\n',path.read_text().strip()):
        lines=block.splitlines()
        if len(lines)<3:continue
        matches=re.findall(r'(\d\d):(\d\d):(\d\d),(\d\d\d)',lines[1]);assert len(matches)==2
        seconds=lambda n:int(n[0])*3600+int(n[1])*60+int(n[2])+int(n[3])/1000
        a,b=map(seconds,matches);result.append((a,b,'\n'.join(lines[2:])))
    return result

def main():
    plan=json.loads((DATA/'picture-timeline-v04.json').read_text())
    video=D/'why-build-together.en-owner-v05.mp4';wav=D/'why-build-together.en-owner-v05.wav'
    probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(video)]))
    v=next(s for s in probe['streams'] if s['codec_type']=='video')
    a=next(s for s in probe['streams'] if s['codec_type']=='audio')
    s=next(s for s in probe['streams'] if s['codec_type']=='subtitle')
    assert (v['width'],v['height'],v['avg_frame_rate'])==(1920,1080,'30/1')
    assert int(v['nb_frames'])==plan['frames'] and abs(float(probe['format']['duration'])-plan['seconds'])<.05
    assert a['tags']['language']==s['tags']['language']=='eng' and s['disposition']['default']==1
    def picture_hash(path):return subprocess.check_output(['ffmpeg','-v','error','-i',str(path),'-map','0:v:0','-c','copy','-f','hash','-hash','sha256','-']).decode().strip()
    old_picture=picture_hash(OLD/'delivery/why-build-together.zh-v04.mp4');new_picture=picture_hash(video)
    assert old_picture==new_picture
    decode=subprocess.run(['ffmpeg','-v','error','-progress','pipe:1','-i',str(video),'-map','0:v:0','-map','0:a:0','-f','null','-'],capture_output=True,text=True,check=True)
    assert not decode.stderr.strip(),decode.stderr
    frames=re.findall(r'^frame=(\d+)$',decode.stdout,re.M);assert int(frames[-1])==plan['frames']
    pcm,sr=sf.read(wav,dtype='int16');old_pcm,old_sr=sf.read(OLD/'delivery/why-build-together.en-v04.wav',dtype='int16')
    assert sr==old_sr==48000 and pcm.shape==(plan['frames']*1600,2)
    intro_count=plan['intro_frames']*1600
    assert np.array_equal(pcm[intro_count:],old_pcm[intro_count:])
    assert np.abs(pcm.astype('int32')).max()<32767
    cc=cues(D/'why-build-together.en-owner-v05.srt')
    embedded=DATA/'embedded-en-check.srt'
    subprocess.run(['ffmpeg','-v','error','-y','-i',str(video),'-map','0:s:0',str(embedded)],check=True)
    embedded_cc=cues(embedded);assert len(cc)==len(embedded_cc)==55
    for (x,y,text),(p,q,t) in zip(cc,embedded_cc):assert abs(x-p)<.0011 and abs(y-q)<.0011 and text==t
    original=json.loads((ROOT.parent/'lucas-academy-video-data/curiosity-builds-20261118/v10/records/subtitles.json').read_text())['cues']
    for r in original:assert any(abs(x-(119.5+r['start']/30))<.0011 and abs(y-(119.5+r['end']/30))<.0011 and text==r['en'] for x,y,text in cc)
    positions=json.loads((DATA/'placements.json').read_text())
    source,sr_source=sf.read(DATA/'source/with-ai-english-narration-louise.wav',dtype='float32')
    groups=positions['placements'];assert groups[0]['source_start_sample']==0 and groups[-1]['source_end_sample']==len(source)
    assert all(x['source_end_sample']==y['source_start_sample'] for x,y in zip(groups,groups[1:]))
    assert sum(g['source_end_sample']-g['source_start_sample'] for g in groups)==len(source)
    expected=np.zeros(intro_count,dtype='float32')
    from scipy.signal import resample_poly
    for g in groups:
        assert g['speech_speed']==1.0
        speech=resample_poly(source[g['source_start_sample']:g['source_end_sample']],2,1).astype('float32')*positions['gain']
        index=round(g['start']*48000);expected[index:index+len(speech)]+=speech
    actual,sr_voice=sf.read(DATA/'intro-en-voice.wav',dtype='float32')
    assert sr_voice==48000 and np.max(np.abs(expected-actual))<2e-7
    mix,mix_sr=sf.read(DATA/'intro-en-mix.wav',dtype='float32')
    assert mix_sr==48000 and np.max(np.abs(mix[:round(23.9*48000)]-actual[:round(23.9*48000)]))<3e-7
    facts=json.loads((D/'delivery.json').read_text())
    assert abs(facts['food_comparison']['junk_food_word_seconds']-facts['food_comparison']['food_picture_starts'])<.25
    report={'status':'passed','seconds':plan['seconds'],'decoded_frames':int(frames[-1]),'picture':'1920x1080 30fps',
        'picture_payload_sha256':new_picture,'picture_payload_identical':True,'speech_speed':1.0,
        'source_samples_preserved_once':len(source),'source_sample_rate':sr_source,'source_seconds':len(source)/sr_source,
        'all_voice_samples_verified_after_resampling_and_gain':True,'project_music_pcm_identical':True,
        'captions':55,'original_project_captions_preserved':len(original),'embedded_english_captions_verified':True,
        'first_23_9_seconds_without_music':True,'quiet_cut_rms_max':max(x['rms_10ms'] for x in positions['quiet_cuts']),
        'food_comparison':facts['food_comparison'],'wav_peak_dbfs':float(20*np.log10(np.abs(pcm.astype('float64')).max()/32768))}
    (D/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
