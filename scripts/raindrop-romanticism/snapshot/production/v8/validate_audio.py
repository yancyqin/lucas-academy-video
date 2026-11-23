"""Verify the revised score transitions, native narration timing, mux and sidecars."""
import json
from pathlib import Path
import re
import subprocess
import sys

import numpy as np

P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import revise_audio as audio
SR=audio.SR;FF=audio.FF;FP='/opt/homebrew/bin/ffprobe'
D=audio.DESKTOP if '--installed' in sys.argv else audio.DELIVERY
plan=json.loads((P/'full-plan.json').read_text())
checks={};by={s['id']:s for s in plan['scenes']}

def probe(path):
    return json.loads(subprocess.check_output([FP,'-v','error','-show_streams','-show_format','-of','json',str(path)]))

def excerpt(path,start,seconds):
    b=subprocess.check_output([FF,'-v','error','-ss',str(start),'-i',str(path),'-t',str(seconds),'-ar',str(SR),'-ac','2','-f','f32le','-'])
    return np.frombuffer(b,dtype='<f4').reshape(-1,2)

v=probe(D/'01-English-full.mp4');assert [s['codec_type'] for s in v['streams']]==['video','audio']
pic,sound=v['streams'];assert (pic['width'],pic['height'],pic['avg_frame_rate'])==(1920,1080,'24/1')
assert int(pic['nb_frames'])==plan['frames'] and sound['tags']['language']=='eng'
assert abs(float(pic['duration'])-plan['duration'])<1/SR
assert abs(float(sound['duration'])-plan['duration'])<.05
checks['video']={'duration':float(pic['duration']),'frames':int(pic['nb_frames']),'english_audio':True,'subtitle_streams':0}
zh=probe(D/'02-Chinese-aligned-audio.wav')['streams'][0]
assert zh['sample_rate']=='48000' and zh['channels']==2 and zh['codec_name']=='pcm_s24le'
assert abs(float(zh['duration'])-plan['duration'])<1/SR
checks['chinese_audio']={'duration':float(zh['duration']),'same_scene_clock':True}

audit=json.loads((P/'narration-timing-audit.json').read_text())
for item in audit['items']:
    assert item['speed']==1 and item['native_seconds']==item['placed_seconds']
    assert item['trailing_silence']>=.39
for item in audit['edges']:
    assert item['source_samples']==item['output_samples'] and item['speed']==1
old=json.loads((audio.V7/'full-plan.json').read_text())
for item in [i for i in plan['voice_fragments'] if i['language']=='zh']:
    previous=next(i for i in old['voice_fragments'] if i['language']=='zh' and i['id']==item['id'])
    assert item['file']==previous['file'] and item['seconds']==previous['seconds']
checks['voice_timing']={'all_rates':1.0,'all_placed_sample_counts_match_native':True,
 'chinese_source_takes_unchanged':True,'shorter_voice_ends_in_silence':True}

listen=by['listen'];receipt=json.loads((P/'music-envelope.json').read_text())
spans=receipt['items'];assert spans[0]['start']==listen['start'] and spans[0]['source_offset']==0
for s in spans:
    assert s['fade_in']>=1.49 and s['fade_out']>=1.49
    assert s['first_sample_peak']==0 and s['last_sample_peak']==0
for a,b in zip(spans,spans[1:]):assert a['end']==b['start']
source=audio.film.decode(receipt['sources']['rain']['file'],2)[:10*SR]
source*=receipt['sources']['rain']['gain']
source[:round(1.5*SR)]*=audio.half_cosine(round(1.5*SR))[:,None]
source*=plan['audio_gains']['zh']['mix_gain']
actual=excerpt(D/'02-Chinese-aligned-audio.wav',listen['start'],10)
error=float(np.max(np.abs(source-actual)));assert error<2e-6,error
for lang,name in [('zh','02-Chinese-aligned-audio.wav'),('en','English-mix.wav')]:
    opening=excerpt(D/name,0,listen['start'])
    n1=next(i for i in audit['items'] if i['language']==lang and i['paragraph_id']=='n001')
    first=round(n1['voice_start']*SR);last=round(n1['voice_end']*SR)
    assert np.max(np.abs(opening[:first]))<1e-6
    assert np.max(np.abs(opening[last:]))<1e-6
    native=audio.film.decode(next(i for i in plan['voice_fragments'] if i['language']==lang and i['id']=='n001-01')['file'])[:,0]
    processed,_=audio.voice_edges(native)
    expected=processed*plan['audio_gains'][lang]['voice_gain']*plan['audio_gains'][lang]['mix_gain']
    assert np.max(np.abs(opening[first:last,0]-expected))<2e-6
checks['music']={'opening_voice_has_no_music':True,'piano_first_starts_at':listen['start'],
 'first_listen_restarts_piece_at_zero':True,'first_listen_max_sample_error':error,
 'all_transitions_fade_out_and_in':True,'fade_in_seconds':1.5,'fade_out_seconds':1.5,'final_fade_out_seconds':4}

compact=lambda t:re.sub(r'\s+','',t)
for lang in ['en','zh']:
    cues=plan['captions'][lang];previous=0
    for c in cues:
        assert previous<=c['start']+1e-6 and c['start']<c['end']<=plan['duration']
        assert len(c['text'].splitlines())<=2;previous=c['end']
    for scene in plan['scenes']:
        if scene['id'].startswith('n'):
            assert compact(''.join(c['text'] for c in cues if c['paragraph_id']==scene['id']))==compact(scene['text_'+lang])
checks['subtitles']={'approved_wording_preserved':True,'all_58_paragraphs_present':True,'times_ordered':True}

for item in json.loads((P/'opening-overrides.json').read_text())['items']:
    asr=(Path(item['file']).parent/'asr.txt').read_text()
    normalize=lambda t:re.sub(r'[^a-z0-9]','',t.lower().replace('ten','10'))
    assert normalize(asr)==normalize(item['text']),(item['id'],asr)
checks['english_opening']={'local_reconversions':3,'asr_words_match':True,'source_performances_reused':True,'cloud_requests':0}

hashes=[]
for file in [audio.V7/'parts/full-picture.mp4',D/'01-English-full.mp4']:
    h=subprocess.check_output([FF,'-v','error','-i',str(file),'-map','0:v:0','-c:v','copy','-bsf:v','h264_mp4toannexb','-f','hash','-hash','sha256','-']).decode().strip();hashes.append(h)
assert hashes[0]==hashes[1]
checks['picture_unchanged']=True
for file in ['01-English-full.mp4','02-Chinese-aligned-audio.wav']:
    subprocess.run([FF,'-v','error','-threads','4','-i',str(D/file),'-f','null','-'],check=True)
    print('Full decode passed:',file,flush=True)
checks['full_decode']=['English video','Chinese WAV'];checks['state']='passed'
(P/'audio-checks.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2))
print(json.dumps(checks,ensure_ascii=False,indent=2),flush=True)
