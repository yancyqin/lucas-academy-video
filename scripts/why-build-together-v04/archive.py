"""Archive verified v04 assets and make a reviewable private upload manifest."""
import hashlib,json,shutil,subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'out/why-build-together-v04'
ARCHIVE=ROOT.parent/'lucas-academy-video-data/why-build-together-20261122/v04'

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()

def main():
    delivery=OUT/'delivery'
    report=json.loads((delivery/'verification.json').read_text())
    playback=json.loads((delivery/'player-check.json').read_text())
    assert report['status']=='passed' and playback[-1]['endState']['ended']
    assert not ARCHIVE.exists(),f'Archive already exists: {ARCHIVE}'
    plan=json.loads((OUT/'timeline.json').read_text())
    scenes={s['id']:s for s in plan['scenes']}
    shots=json.loads((OUT/'shot-usage.json').read_text())
    shots['G05'][0]['source_frames']=min(scenes['n007']['frames'],300)
    shots['G05'][0]['final_still_hold_frames']=max(0,scenes['n007']['frames']-300)
    shots['G06'][0]['source_frames']=min(scenes['n010']['frames'],300)
    shots['G06'][1]['source_start_frame']=min(scenes['n010']['frames'],300)
    shots['G06'][1]['source_frames']=max(0,300-scenes['n010']['frames'])
    (OUT/'shot-usage.json').write_text(json.dumps(shots,indent=2)+'\n')
    facts=json.loads((delivery/'delivery.json').read_text())
    assert sha(delivery/'why-build-together.zh-v04.mp4')==facts['movie_sha256']
    assert sha(delivery/'why-build-together.en-v04.wav')==facts['english_audio_sha256']
    manifest={
        'version':'v04','channel_id':'UCtn9_kNupjZvWAJVOqWUbYw','channel_name':'Lucas Academy',
        'intended_settings':{'visibility':'private','schedule':None,'original_language':'zh-Hans',
            'title_description_language':'zh-Hans','category':'Education','made_for_kids':False,
            'paid_promotion':False},
        'video':{'file':'why-build-together.zh-v04.mp4','sha256':facts['movie_sha256'],
            'bytes':(delivery/'why-build-together.zh-v04.mp4').stat().st_size,
            'seconds':plan['seconds'],'width':1920,'height':1080,'fps':30,'original_audio':'Chinese'},
        'languages':{},'tags':(delivery/'youtube-tags.txt').read_text().split(),
        'source_project_movie_sha256':facts['source_movie_sha256'],
        'actual_studio_status':'not yet uploaded; record separately in upload-receipt.json',
    }
    for language,caption_language in [('zh','zh-CN'),('en','en')]:
        title=(delivery/f'youtube-title.{language}.txt').read_text().strip()
        description=(delivery/f'youtube-description.{language}.txt').read_text()
        assert len(title)<=100 and len(description)<=5000 and description.startswith('0:00 ')
        subtitles=delivery/f'why-build-together.{caption_language}.srt'
        row={'title':title,'description':description,'description_characters':len(description),
            'chapter_count':14,'subtitles':subtitles.name,'subtitle_cues':report['caption_cues' if language=='zh' else 'english_caption_cues'],
            'subtitles_sha256':sha(subtitles),'thumbnail':f'youtube-cover.{language}.jpg'}
        if language=='en':row['audio']={'file':facts['english_audio'],'sha256':facts['english_audio_sha256'],
            'seconds':plan['seconds'],'sample_rate':48000,'channels':2,'format':'PCM signed 16-bit WAV'}
        manifest['languages'][language]=row
    (delivery/'upload-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    shutil.copytree(OUT,ARCHIVE)
    snapshot=ARCHIVE/'source-snapshot'
    for folder in ['scripts/why-build-together-v04','src/videos/why-build-together-v04','docs/why-build-together']:
        shutil.copytree(ROOT/folder,snapshot/folder,ignore=shutil.ignore_patterns('__pycache__'))
    for file in ['scripts/music_ducking.py','scripts/youtube_tags.py','package.json','package-lock.json']:
        target=snapshot/file;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/file,target)
    image=snapshot/'public/images/why-build-together/needs-pyramid-v03.png'
    image.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(ROOT/'public/images/why-build-together/needs-pyramid-v03.png',image)
    records=[dict(path=str(p.relative_to(ARCHIVE)),bytes=p.stat().st_size,sha256=sha(p))
        for p in sorted((ARCHIVE/'delivery').iterdir()) if p.is_file()]
    archive_manifest={'version':'v04','runtime_origin':str(OUT),'source_snapshot':'source-snapshot',
        'changes':['Continuous card movement without looping','Aligned Chinese and English audio with bilingual upload package'],
        'delivery':records}
    (ARCHIVE/'archive-manifest.json').write_text(json.dumps(archive_manifest,ensure_ascii=False,indent=2)+'\n')
    print(ARCHIVE,flush=True)

if __name__=='__main__':main()
