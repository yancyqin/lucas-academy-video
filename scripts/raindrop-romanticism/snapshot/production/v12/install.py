"""Atomically refresh the single Desktop handoff, retaining approved speech timing."""
from pathlib import Path
import json,hashlib,shutil,os,subprocess,sys,importlib.util
P=Path(__file__).resolve().parent;DEST=Path('@DATA_ROOT@/production/v12/published-release')
STEM='01-压力焦虑肖邦浪漫-v11-英文-Louise';WAV='02-压力焦虑肖邦浪漫-v11-中文-Fangfang.wav';M4A='02-压力焦虑肖邦浪漫-v11-中文-Fangfang-YouTube.m4a'
def digest(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(8388608),b''):h.update(b)
    return h.hexdigest()
def text(p,s):
    q=p.with_name('.'+p.name+'.tmp');q.write_text(s,encoding='utf8');q.replace(p)
def save(p,d):text(p,json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def cp(a,b):
    q=b.with_name('.'+b.name+'.tmp');shutil.copy2(a,q);q.replace(b)
archive=P/'before-smooth'
if not archive.exists():shutil.copytree(DEST,archive,copy_function=os.link)
plan=json.loads((P.parent/'v11/full-plan.json').read_text());capture=json.loads((P/'capture-plan.json').read_text())
for a,b in [('01-English-full.mp4',STEM+'.mp4'),('02-Chinese-aligned-audio.wav',WAV),('Chinese-YouTube.m4a',M4A),('03-English.srt',STEM+'.en.srt'),('04-Chinese.srt',STEM+'.zh-Hans.srt'),('Chinese-preview.mp3','资料/中文播放预览.mp3')]:cp(P/'delivery'/a,DEST/b)
data=json.loads((archive/'资料/播放与字幕数据.json').read_text());data[0].update(src=STEM+'.mp4',srt=STEM+'.zh-Hans.srt',englishSrt=STEM+'.en.srt',chineseAudio=WAV)
save(DEST/'资料/播放与字幕数据.json',data)
page=(archive/'打开预览.html').read_text().replace('-v10-','-v11-').replace('revision=v10','revision=v11-smooth60').replace('v10','v11 · 60 fps')
text(DEST/'打开预览.html',page)
text(DEST/'使用说明.txt','v11 · 1080p60 流畅重录版\n博物馆镜头按最终音轨逐帧重新渲染，使用当前沙龙布局、56 幅画与 9 座展台；相机行走与转向采用连续曲线。\n已确认的中英文配音、背景音乐、文案和字幕时间均沿用 v10，无语音变速。\n英文 Louise 视频，中文 Fangfang 独立音轨，中英文独立字幕，无内嵌字幕。\n打开「打开预览.html」切换语言和字幕。封面及中英文简介保留已选版本。\nYouTube 仅保存 Private。旧视频不会自动删除。\n')
provenance=json.loads((archive/'资料/素材来源与制作说明.json').read_text());provenance['smooth_revision']=dict(version='v11',fps=60,frames=capture['frames'],native_camera_capture=True,ui_head=capture['ui_head'],ui_file_sha256=capture['ui_file_sha256'],camera_curve=capture['interpolation'],audio_identical_to_v10=True,subtitle_times_identical_to_v10=True,cloud_requests=0)
save(DEST/'资料/素材来源与制作说明.json',provenance)
save(DEST/'资料/v11流畅度检查.json',json.loads((P/'checks.json').read_text()))
for f in DEST.iterdir():
    if '-v10-' in f.name:f.unlink()
helper=Path('@USER_HOME@/.codex/skills/upload-youtube-private/scripts/prepare_upload.py');manifest_path=P/'youtube-upload-manifest.json'
subprocess.run([sys.executable,str(helper),'--package',str(DEST),'--output',str(manifest_path)],check=True)
manifest=json.loads(manifest_path.read_text());video=manifest['videos'][0]
previous=json.loads((archive/'资料/上传清单.json').read_text())['videos'][0]
spec=importlib.util.spec_from_file_location('prepare_upload',helper);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
en=DEST/(STEM+'.en.srt');video['subtitles'].insert(0,dict(file=str(en),language='en',sha256=digest(en),cues=m.srt(en,capture['duration'])))
video.update(revision='v11-smooth60',channel_id='UCtn9_kNupjZvWAJVOqWUbYw',channel_name='Lucas Academy',
 chinese_audio=dict(file=str(DEST/WAV),language='zh-Hans',sha256=digest(DEST/WAV),duration=plan['duration']),
 chinese_audio_youtube=dict(file=str(DEST/M4A),language='zh-Hans',sha256=digest(DEST/M4A),duration=plan['duration']),
 thumbnail_en=str(DEST/'04-YouTube封面-暖色画廊-英文.jpg'),thumbnail_zh=str(DEST/'05-YouTube封面-暖色画廊-中文.jpg'),altered_content=True,category='Education',made_for_kids=False)
save(manifest_path,manifest);save(DEST/'资料/上传清单.json',manifest)
save(DEST/'资料/YouTube同步状态.json',dict(revision='v11-smooth60',state='ready_for_private_upload',previous_video_id='SUPERSEDED_PRIVATE_VIDEO',previous_video_unchanged=True))
delivery=dict(version='v11-smooth60',state='complete_local',duration=capture['duration'],fps=60,english_video=str(DEST/(STEM+'.mp4')),chinese_audio=str(DEST/WAV),chinese_audio_youtube=str(DEST/M4A),subtitles=[str(DEST/(STEM+'.en.srt')),str(DEST/(STEM+'.zh-Hans.srt'))],preview=str(DEST/'打开预览.html'),upload_manifest=str(manifest_path),video_sha256=video['sha256'],new_cloud_requests=0)
save(P/'delivery.json',delivery);save(P.parent/'latest.json',dict(revision='v11-smooth60',production=str(P),delivery=str(P/'delivery.json'),state='local_verified_private_upload_pending'))
print(json.dumps(delivery,ensure_ascii=False,indent=2))
