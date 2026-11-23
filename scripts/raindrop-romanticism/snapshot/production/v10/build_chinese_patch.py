"""Replace one Mandarin passage without changing any picture or other performance."""
import hashlib,json,os,re,shutil,subprocess,sys
from pathlib import Path
import numpy as np

P=Path(__file__).resolve().parent;V9=P.parent/'v9'
sys.path.insert(0,str(P.parent/'v8'))
import revise_audio as audio
film=audio.film;FF=film.FF;SR=film.SR
PACKAGE=Path('@DATA_ROOT@/production/v12/published-release')
WAV='02-压力焦虑肖邦浪漫-v9-中文-Fangfang.wav'
SRT='01-压力焦虑肖邦浪漫-v9-英文-Louise.zh-Hans.srt'
DOC='09-压力焦虑肖邦浪漫-中文文案.docx'
M4A='02-压力焦虑肖邦浪漫-v9-中文-Fangfang-YouTube.m4a'

def save(path,data):path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(8*1024*1024),b''):h.update(chunk)
    return h.hexdigest()
def compact(text):return re.sub(r'\s+','',text)
def rms(samples):
    active=samples[np.abs(samples)>.008]
    return float(np.sqrt(np.mean(active**2)))

def main():
    plan=json.loads((V9/'full-plan.json').read_text())
    old=next(i for i in plan['voice_fragments'] if i['language']=='zh' and i['id']=='n002-01')
    new=json.loads((P/'n002-retake/fangfang/receipt.json').read_text())
    scene=next(s for s in plan['scenes'] if s['id']=='n002')
    a=round(scene['voice_start']*SR)
    assert scene['voice_start']+new['seconds']<=scene['end']
    original,old_edges=audio.voice_edges(film.decode(old['file'])[:,0])
    revised,new_edges=audio.voice_edges(film.decode(new['file'])[:,0])
    old_gain=plan['audio_gains']['zh']['voice_gain']*plan['audio_gains']['zh']['mix_gain']
    gain=old_gain*rms(original)/rms(revised)
    source=PACKAGE/WAV
    backup=P/'before-edit';backup.mkdir(exist_ok=True)
    for name in [WAV,SRT,DOC,'资料/中文播放预览.mp3','打开预览.html','资料/播放与字幕数据.json','资料/上传清单.json']:
        target=backup/name;target.parent.mkdir(exist_ok=True,parents=True)
        if not target.exists():os.link(PACKAGE/name,target)
    mix=film.decode(backup/WAV,2)
    before_peak=float(np.max(np.abs(mix)))
    mix[a:a+len(original)]-=original[:,None]*old_gain
    mix[a:a+len(revised)]+=revised[:,None]*gain
    assert np.isfinite(mix).all() and np.max(np.abs(mix))<.94
    out=P/'delivery';out.mkdir(exist_ok=True)
    audio.write_pcm24(out/WAV,mix)
    subprocess.run([FF,'-v','error','-y','-i',str(out/WAV),'-c:a','libmp3lame','-q:a','2',str(out/'中文播放预览.mp3')],check=True)
    subprocess.run([FF,'-v','error','-y','-i',str(out/WAV),'-c:a','aac','-b:a','256k','-movflags','+faststart','-metadata:s:a:0','language=zho',str(out/M4A)],check=True)
    subprocess.run([FF,'-v','error','-y','-i',str(out/WAV),'-ss','14','-t','23','-c:a','pcm_s16le',str(out/'中文开头重录-含前后衔接.wav')],check=True)
    old.update(new);scene['text_zh']=new['text'];scene['voice_seconds']['zh']=new['seconds']
    # Keep each question readable. Timings follow this take's actual ASR sentence boundaries.
    asr=json.loads((P/'n002-retake/fangfang/asr.json').read_text())
    chunks=asr['transcription']
    print('ASR timing',[(c['offsets'],c['text']) for c in chunks],flush=True)
    texts=['听起来平静而优美，对吗？','但是你能想象，在写这个前奏曲的那个冬天，','肖邦曾在极度悲伤和焦虑中弹琴吗？']
    assert len(chunks)==3 and compact(''.join(texts))==compact(new['text'])
    boundaries=[0]+[c['offsets']['from']/1000 for c in chunks[1:]]+[new['seconds']]
    captions=[dict(start=scene['voice_start']+boundaries[i],end=scene['voice_start']+boundaries[i+1],text=film.caption_lines(text,'zh'),paragraph_id='n002') for i,text in enumerate(texts)]
    old_captions=plan['captions']['zh'];rest=[c for c in old_captions if c['paragraph_id']!='n002']
    plan['captions']['zh']=sorted(rest+captions,key=lambda c:c['start'])
    assert [c for c in plan['captions']['zh'] if c['paragraph_id']!='n002']==rest
    sub=out/SRT
    sub.write_text('\n'.join(f'{i}\n{film.srt_time(c["start"])} --> {film.srt_time(c["end"])}\n{c["text"]}\n' for i,c in enumerate(plan['captions']['zh'],1)),encoding='utf-8')
    revision=dict(revision='v9.1-Chinese-opening-question',passage='n002',text=new['text'],native_seconds=new['seconds'],speed=1.0,
        start=scene['voice_start'],end=scene['voice_start']+new['seconds'],scene_end=scene['end'],
        normalized_gain=gain,old_gain=old_gain,source=str(P/'n002-retake/serena/original.wav'),converted=new['file'],
        new_cloud_requests=0,english_video_unchanged=True,other_audio_preserved=True,music_envelope_preserved=True,
        subtitle_cues=len(plan['captions']['zh']),before_peak=before_peak,after_peak=float(np.max(np.abs(mix))),
        edges=new_edges)
    # Verify the whole replacement and both untouched sides after lossless encoding.
    encoded=film.decode(out/WAV,2);baseline=film.decode(backup/WAV,2);z=a+max(len(original),len(revised))
    assert len(encoded)==len(baseline)==plan['frames']*(SR//film.FPS)
    error=max(float(np.max(np.abs(encoded[:a]-baseline[:a]))),float(np.max(np.abs(encoded[z:]-baseline[z:]))))
    assert error<3e-7
    expected=(baseline[a:z].copy());expected[:len(original)]-=original[:,None]*old_gain;expected[:len(revised)]+=revised[:,None]*gain
    replacement_error=float(np.max(np.abs(encoded[a:z]-expected)))
    assert replacement_error<3e-7
    revision.update(unedited_audio_max_error=error,replacement_error=replacement_error,sha256=digest(out/WAV),
        youtube_audio_sha256=digest(out/M4A),subtitle_sha256=digest(sub),docx_sha256=digest(P/DOC),state='passed')
    plan.update(revision=revision['revision'],previous_source_sha256=plan['source_sha256'],source_sha256=digest(P/DOC),chinese_opening_revision=revision)
    save(P/'full-plan.json',plan);save(P/'checks.json',revision)
    print(json.dumps(revision,ensure_ascii=False,indent=2),flush=True)

if __name__=='__main__':main()
