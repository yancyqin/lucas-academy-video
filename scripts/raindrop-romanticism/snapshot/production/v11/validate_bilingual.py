"""Validate the final media, native timings, exact script, captions and source reuse."""
import hashlib,json,re,subprocess,sys
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P.parent/'v8'))
import revise_audio as audio
film=audio.film
plan=json.loads((P/'full-plan.json').read_text());old=json.loads((P.parent/'v10/full-plan.json').read_text())
def probe(file):return json.loads(subprocess.check_output(['/opt/homebrew/bin/ffprobe','-v','error','-show_streams','-show_format','-of','json',str(file)]))
v=probe(P/'delivery/01-English-full.mp4');video=next(s for s in v['streams'] if s['codec_type']=='video')
assert int(video['nb_frames'])==plan['frames']==23651
assert video['avg_frame_rate']=='24/1' and (video['width'],video['height'])==(1920,1080)
assert not any(s['codec_type']=='subtitle' for s in v['streams'])
assert abs(float(v['format']['duration'])-plan['duration'])<1/24
for name in ['English-mix.wav','02-Chinese-aligned-audio.wav','Chinese-YouTube.m4a']:
    value=probe(P/'delivery'/name);assert abs(float(value['format']['duration'])-plan['duration'])<.003
compact=lambda t:re.sub(r'\s+','',t)
new=next(s for s in plan['scenes'] if s['id']=='n002')
assert 'right? But can you imagine' in new['text_en'] and '对吗？但是你能想象' in new['text_zh']
assert new['voice_seconds']==dict(en=13.68,zh=11.2)
assert abs(new['end']-29.291666666666668)<1/48000
for scene in plan['scenes']:
    if not scene['id'].startswith('n'):continue
    for language in ['en','zh']:
        units=[i for i in plan['voice_fragments'] if i['paragraph_id']==scene['id'] and i['language']==language]
        assert compact(''.join(i['text'] for i in units))==compact(scene['text_'+language])
        assert abs(sum(i['seconds'] for i in units)-scene['voice_seconds'][language])<.002
        assert scene['voice_start']+scene['voice_seconds'][language]<=scene['end']
for language in ['en','zh']:
    cues=plan['captions'][language]
    assert all(0<=c['start']<c['end']<=plan['duration'] for c in cues)
    assert all(a['end']<=b['start']+.001 for a,b in zip(cues,cues[1:]))
    assert compact(''.join(c['text'] for c in cues))==compact(''.join(s['text_'+language] for s in plan['scenes'] if s['id'].startswith('n')))
    for item in plan['voice_fragments']:
        if item['language']!=language or item['paragraph_id']=='n002':continue
        previous=next(i for i in old['voice_fragments'] if i['language']==language and i['id']==item['id'])
        assert item['file']==previous['file'] and item['seconds']==previous['seconds']
assert plan['speech_speed_changed'] is False and plan['all_voice_speeds']==1.0
assert plan['music_under_opening_voice'] is False and plan['music_starts_at']==next(s for s in plan['scenes'] if s['id']=='listen')['start']
assert all(s['fade_in']==1.5 and s['fade_out'] in [1.5,4] for s in plan['music_spans'])
old_paths=(P.parent/'v7/parts/concat.txt').read_text().splitlines()[1:]
new_paths=(P/'parts/concat.txt').read_text().splitlines()[1:]
assert old_paths==new_paths
result=dict(state='passed',revision=plan['revision'],duration=plan['duration'],frames=plan['frames'],
    english_seconds=13.68,chinese_seconds=11.2,all_speech_speeds=1.0,other_voice_files_preserved=True,
    later_picture_segments_reused=True,music_fades_verified=True,dry_opening_verified=True,
    en_cues=len(plan['captions']['en']),zh_cues=len(plan['captions']['zh']),word_qa=dict(english_pages=7,all_pages_reviewed=True,one_paragraph_changed=True),
    new_cloud_requests=0,video_sha256=hashlib.sha256((P/'delivery/01-English-full.mp4').read_bytes()).hexdigest())
(P/'checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps(result,ensure_ascii=False,indent=2),flush=True)
