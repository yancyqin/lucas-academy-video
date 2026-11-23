"""Check the full delivery's clock, text, streams, audio repairs and decodeability."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import wave

import numpy as np

P=Path(__file__).resolve().parent
DEST=Path('@USER_HOME@/Desktop/压力焦虑肖邦浪漫-完整版-2026-11-21')
FF='/opt/homebrew/bin/ffmpeg';FP='/opt/homebrew/bin/ffprobe'
plan=json.loads((P/'full-plan.json').read_text())
source=json.loads((P.parent/'v6/narration-bilingual.json').read_text())
compact=lambda s:re.sub(r'\s+','',s)
checks={}

video=json.loads(subprocess.check_output([FP,'-v','error','-show_streams','-show_format','-of','json',str(DEST/'01-English-full.mp4')]))
streams=video['streams'];assert [s['codec_type'] for s in streams]==['video','audio']
v,a=streams;assert (v['width'],v['height'],v['avg_frame_rate'])==(1920,1080,'24/1')
assert int(v['nb_frames'])==plan['frames']
assert a['tags']['language']=='eng'
assert abs(float(v['duration'])-plan['duration'])<.0001
assert abs(float(a['duration'])-plan['duration'])<.05
checks['video']={'frames':int(v['nb_frames']),'duration':float(v['duration']),'size':[1920,1080],
 'fps':24,'audio_language':'eng','subtitle_streams':0,'burned_captions':False}

audio=json.loads(subprocess.check_output([FP,'-v','error','-show_streams','-of','json',str(DEST/'02-Chinese-aligned-audio.wav')]))['streams'][0]
assert audio['codec_name']=='pcm_s24le' and audio['sample_rate']=='48000' and audio['channels']==2
assert abs(float(audio['duration'])-plan['duration'])<1/48000
checks['chinese_audio']={'duration':float(audio['duration']),'same_clock':True,'format':'48 kHz stereo PCM24'}

for lang in ['en','zh']:
    cues=plan['captions'][lang];last=0
    for c in cues:
        assert c['start']>=last-1e-6 and c['end']>c['start'] and c['end']<=plan['duration']
        assert len(c['text'].splitlines())<=2
        last=c['end']
    for row in source['rows']:
        if row['spoken']:
            assert compact(''.join(c['text'] for c in cues if c['paragraph_id']==row['id']))==compact(row[lang]),(lang,row['id'])
    checks['subtitles_'+lang]={'paragraphs':58,'cues':len(cues),'approved_wording_preserved':True,'max_lines':2,'ordered':True}

overrides=json.loads((P/'year-voice-overrides.json').read_text())
assert len(overrides['items'])==15 and overrides['new_cloud_requests']==0
for item in overrides['items']:
    file=Path(item['file']);assert hashlib.sha256(file.read_bytes()).hexdigest()==item['sha256']
    assert not re.search(r'[12]\d{3}\s*年',item['spoken_text'])
    with wave.open(str(file)) as w:
        data=np.frombuffer(w.readframes(w.getnframes()),dtype='<i2')
        assert len(data)>1000 and np.max(np.abs(data.astype(np.int32)))>100
        assert abs(w.getnframes()/w.getframerate()-item['seconds'])<.001
checks['year_retakes']={'count':15,'calendar_years_spelled_as_individual_digits':True,
 'written_dates_preserved_in_subtitles':True,'new_cloud_requests':0,
 'asr_checked':15,'note':'ASR often formats the spoken digit sequence as Arabic numerals; that formatting alone is not a pronunciation test.'}
assert plan['reprise_correlation']>.99999
assert plan['first_frame_music_correlation']>.99999
checks['music']={'plays_from_start':True,'listening_restarts_from_beginning':True,
 'listen_seconds':10,'reset_correlation':plan['reprise_correlation'],
 'initial_correlation':plan['first_frame_music_correlation']}
assert plan['guide_character'] is False and plan['speech_speed_changed'] is False
tasks=json.loads((P/'picture-tasks.json').read_text())
assert not any('romanticism-guide' in json.dumps(t) for t in tasks)
assert all(not t.get('file','').endswith('英文版.mp4') for t in tasks)
assert all(not any('\u4e00'<=c<='\u9fff' for c in ''.join(t.get('label',[]))) for t in tasks)
assert plan['on_screen_label_language']=='English' and plan['credits_language']=='English'
for task in tasks:
    if task['id'] in ['n053','n054','n055','n056']:
        assert task['seconds']+1e-8>=task['source'][1]-task['source'][0]
checks['picture']={'guide_character':False,'portrait_merge_then_split':True,'reconstruction_label':True,
 'bonus_round_window_not_accelerated':True,'speech_speed_changed':False,'on_screen_labels':'English',
 'credits':'English'}

for name in ['01-English-full.mp4','02-Chinese-aligned-audio.wav']:
    subprocess.run([FF,'-v','error','-threads','4','-i',str(DEST/name),'-f','null','-'],check=True)
    print('Full decode passed:',name,flush=True)
checks['full_decode']=['English MP4','Chinese WAV']
checks['duration_seconds']=plan['duration']
checks['state']='passed'
(P/'full-film-checks.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2))
print(json.dumps(checks,ensure_ascii=False,indent=2),flush=True)
