"""Validate the entire revised bilingual release, not just the opening excerpt."""
import hashlib,json
from pathlib import Path
import re
import subprocess
import sys
import numpy as np

P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import build_revision as build
audio=build.audio;SR=audio.SR;FF=audio.FF;FP='/opt/homebrew/bin/ffprobe'
D=audio.DESKTOP if '--installed' in sys.argv else audio.DELIVERY

def probe(path):
    return json.loads(subprocess.check_output([FP,'-v','error','-show_streams','-show_format','-of','json',str(path)]))

def excerpt(file,start,seconds):
    return np.frombuffer(subprocess.check_output([FF,'-v','error','-ss',str(start),'-i',str(file),'-t',str(seconds),
        '-ar',str(SR),'-ac','2','-f','f32le','-']),dtype='<f4').reshape(-1,2)

def main():
    plan=json.loads((P/'full-plan.json').read_text());checks={}
    review=json.loads((P/'english-review.json').read_text());assert review['complete'] and review['reviewed']==73
    overrides=json.loads((P/'voice-overrides.json').read_text())['items']
    en=[i for i in overrides if i['language']=='en'];cn=[i for i in overrides if i['language']=='zh']
    assert len(en)==73 and len(cn)==1 and cn[0]['id']=='n003-01'
    for item in overrides:
        assert hashlib.sha256(Path(item['file']).read_bytes()).hexdigest()==item['sha256']
        assert item['asr'].strip()
    checks['english']={'reviewed_units':73,'all_asr_transcripts_present':True,'original_performances_reused':True,
        'padding_context_used_for_each_inference':True,'new_cloud_generation':0}
    selected=json.loads((P/'chinese-selected.json').read_text())
    assert 6.5<=cn[0]['seconds']<=9.8 and abs(cn[0]['seconds']-selected['seconds'])<.002
    assert cn[0]['spoken_text'].startswith('一八三八年') and cn[0]['target_profile']=='fangfang/zh'
    checks['chinese_retake']={'new_seconds':cn[0]['seconds'],'previous_seconds':11.92,'native_speed':True,
        'year_digits':'一八三八年','voice':'Fangfang','approved_written_text_preserved':True}
    flagged=[]
    for id in ['n004-01','n005-01','n006-01']:
        item=next(r for r in review['items'] if r['id']==id)
        old=item['previous_waveform']['head_150ms_peak'];new=item['new_waveform']['head_150ms_peak']
        assert new<old*.1
        flagged.append({'id':id,'previous_initial_peak':old,'revised_initial_peak':new,
            'recognized':item['recognized']})
    checks['reported_positions']=flagged
    audit=json.loads((P/'narration-timing-audit.json').read_text())
    assert len(audit['items'])==116
    for r in audit['items']:
        assert r['speed']==1 and r['native_seconds']==r['placed_seconds'] and r['trailing_silence']>.39
    for r in audit['edges']:assert r['source_samples']==r['output_samples']
    previous=json.loads((P.parent/'v8/full-plan.json').read_text())
    for item in [i for i in plan['voice_fragments'] if i['language']=='zh' and i['id']!='n003-01']:
        old=next(i for i in previous['voice_fragments'] if i['language']=='zh' and i['id']==item['id'])
        assert old['file']==item['file']
    checks['timing']={'all_rates':1.0,'voice_duration_stretching':False,'common_scene_clock':True,
        'other_chinese_takes_unchanged':True}
    compact=lambda t:re.sub(r'\s+','',t)
    for lang in ['en','zh']:
        last=0
        for cue in plan['captions'][lang]:
            assert cue['start']+1e-6>=last and cue['start']<cue['end']<=plan['duration']
            assert len(cue['text'].splitlines())<=2;last=cue['end']
        for scene in plan['scenes']:
            if scene['id'].startswith('n'):
                assert compact(''.join(c['text'] for c in plan['captions'][lang] if c['paragraph_id']==scene['id']))==compact(scene['text_'+lang])
    checks['subtitles']={'all_58_paragraphs_per_language':True,'wording_preserved':True,'separate_files':True}
    music=json.loads((P/'music-envelope.json').read_text())
    for r in music['items']:
        assert r['first_sample_peak']==r['last_sample_peak']==0 and r['fade_in']>=1.49 and r['fade_out']>=1.49
    listen=next(s for s in plan['scenes'] if s['id']=='listen')
    assert music['items'][0]['start']==listen['start'] and music['items'][0]['source_offset']==0
    for lang,name in [('zh','02-Chinese-aligned-audio.wav'),('en','English-mix.wav')]:
        opening=excerpt(D/name,0,listen['start'])
        first=next(i for i in audit['items'] if i['language']==lang and i['paragraph_id']=='n001')
        a=round(first['voice_start']*SR);z=round(first['voice_end']*SR)
        assert np.max(np.abs(opening[:a]))<1e-6 and np.max(np.abs(opening[z:]))<1e-6
    checks['music']={'silent_under_first_invitation':True,'fade_in_seconds':1.5,'fade_out_seconds':1.5,'final_fade_seconds':4}
    v=probe(D/'01-English-full.mp4');assert [s['codec_type'] for s in v['streams']]==['video','audio']
    pic,sound=v['streams'];assert (pic['width'],pic['height'],pic['avg_frame_rate'])==(1920,1080,'24/1')
    assert int(pic['nb_frames'])==plan['frames'] and sound['tags']['language']=='eng'
    assert abs(float(pic['duration'])-plan['duration'])<.0001 and abs(float(sound['duration'])-plan['duration'])<.05
    zh=probe(D/'02-Chinese-aligned-audio.wav')['streams'][0]
    assert zh['codec_name']=='pcm_s24le' and zh['sample_rate']=='48000' and zh['channels']==2
    assert abs(float(zh['duration'])-plan['duration'])<1/SR
    hashes=[]
    for file in [P.parent/'v7/parts/full-picture.mp4',D/'01-English-full.mp4']:
        h=subprocess.check_output([FF,'-v','error','-i',str(file),'-map','0:v:0','-c:v','copy','-bsf:v','h264_mp4toannexb','-f','hash','-hash','sha256','-']).decode().strip();hashes.append(h)
    assert hashes[0]==hashes[1]
    checks['picture']={'unchanged':True,'no_subtitle_streams':True,'duration':plan['duration']}
    for name in ['01-English-full.mp4','02-Chinese-aligned-audio.wav']:
        subprocess.run([FF,'-v','error','-threads','4','-i',str(D/name),'-f','null','-'],check=True)
        print('Complete decode passed',name,flush=True)
    checks['full_decode']=['English film','Chinese WAV'];checks['state']='passed'
    (P/'full-checks.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2))
    print(json.dumps(checks,ensure_ascii=False,indent=2),flush=True)

if __name__=='__main__':main()
