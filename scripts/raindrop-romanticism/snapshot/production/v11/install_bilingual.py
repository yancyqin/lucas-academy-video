"""Keep one clean Desktop upload package, with the two revised performances."""
import hashlib,importlib.util,json,math,os,re,shutil,subprocess,sys
from pathlib import Path

P=Path(__file__).resolve().parent
PACKAGE=Path('@DATA_ROOT@/production/v12/published-release')
plan=json.loads((P/'full-plan.json').read_text())
old=json.loads((P.parent/'v10/full-plan.json').read_text())
STEM='01-压力焦虑肖邦浪漫-v10-英文-Louise'
WAV='02-压力焦虑肖邦浪漫-v10-中文-Fangfang.wav'
M4A='02-压力焦虑肖邦浪漫-v10-中文-Fangfang-YouTube.m4a'
def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for part in iter(lambda:f.read(8*1024*1024),b''):h.update(part)
    return h.hexdigest()
def atomic_text(path,text):
    temp=path.with_name('.'+path.name+'.tmp');temp.write_text(text,encoding='utf-8');os.replace(temp,path)
def save(path,data):atomic_text(path,json.dumps(data,ensure_ascii=False,indent=2)+'\n')
def atomic_copy(a,b):
    temp=b.with_name('.'+b.name+'.tmp');shutil.copy2(a,temp);os.replace(temp,b)
def chapters(text):
    def replace(match):
        mm,ss=int(match[1]),int(match[2]);seconds=mm*60+ss
        if seconds<27:return match[0]
        scene=min(old['scenes'],key=lambda s:abs(s['start']-seconds))
        assert abs(scene['start']-seconds)<1.1,(match[0],scene['id'],scene['start'])
        new=next(s for s in plan['scenes'] if s['id']==scene['id'])
        value=int(new['start']+1e-6);return f'{value//60:02d}:{value%60:02d} '
    return re.sub(r'(?m)^(\d{1,2}):(\d{2}) ',replace,text)

archive=P/'before-upload'
if not archive.exists():shutil.copytree(PACKAGE,archive,copy_function=os.link)
files={P/'delivery/01-English-full.mp4':STEM+'.mp4',
       P/'delivery/02-Chinese-aligned-audio.wav':WAV,
       P/'delivery/Chinese-YouTube.m4a':M4A,
       P/'delivery/03-English.srt':STEM+'.en.srt',
       P/'delivery/04-Chinese.srt':STEM+'.zh-Hans.srt',
       P/'delivery/Chinese-preview.mp3':'资料/中文播放预览.mp3',
       P/'10-压力焦虑肖邦浪漫-英文文案.docx':'10-压力焦虑肖邦浪漫-英文文案.docx'}
for source,name in files.items():atomic_copy(source,PACKAGE/name)
cues=[dict(start=round(c['start'],3),end=round(c['end'],3),text=c['text']) for c in plan['captions']['zh']]
program=json.loads((archive/'资料/播放与字幕数据.json').read_text());program[0].update(src=STEM+'.mp4',srt=STEM+'.zh-Hans.srt',englishSrt=STEM+'.en.srt',chineseAudio=WAV,cues=cues)
save(PACKAGE/'资料/播放与字幕数据.json',program)
page=(archive/'打开预览.html').read_text().replace('-v9-','-v10-').replace('v9（中文开头已重录）','v10（中英文开头已重录）').replace('v9 上传包','v10 上传包').replace('16 分 23 秒','16 分 25 秒').replace('revision=v9.1','revision=v10')
data=json.dumps(plan['captions'],ensure_ascii=False).replace('</','<\\/')
page,n=re.subn(r'const CUES=.*?;const v=',lambda m:'const CUES='+data+';const v=',page,count=1,flags=re.S);assert n==1
atomic_text(PACKAGE/'打开预览.html',page)
source_manifest=json.loads((P.parent/'v10/before-edit/youtube-upload-manifest-v9.json').read_text())['videos'][0]
for language,name in [('en','03-YouTube英文标题简介标签.txt'),('zh','06-YouTube中文标题简介标签.txt')]:
    meta=source_manifest['metadata_'+language]
    blocks=[('标题 / Title',meta['title']),('简介 / Description',meta['description']),('标签 / Tags',' '.join(meta['tags'])),('上传设置 / Upload settings',meta['settings'].replace('\\n','\n'))]
    original='\n\n'.join('【'+label+'】\n'+value for label,value in blocks)+'\n'
    atomic_text(archive/name,original)
    atomic_text(PACKAGE/name,chapters(original))
note='v10 上传包\n英文 Louise 视频＋中文 Fangfang 独立音轨＋中英文独立字幕。\n中英文开头都已按最新两句重录，保留自然语速。镜头延长约 3 秒；其余段落按共同时间线顺延，短的旁白后自然留白。\n打开「打开预览.html」切换语言和字幕。\n中文 WAV 为无损母带；YouTube.m4a 是兼容平台上传的版本。\n封面为已选的暖色画廊设计，中英文各一张；简介保留所有署名、来源与指定标签。\nYouTube 保存为 Private，不公开发布、不安排定时发布。\n'
atomic_text(PACKAGE/'使用说明.txt',note)
for file in PACKAGE.iterdir():
    if '-v9-' in file.name:file.unlink()
helper=Path('@USER_HOME@/.codex/skills/upload-youtube-private/scripts/prepare_upload.py')
output=P/'youtube-upload-manifest.json'
subprocess.run([sys.executable,str(helper),'--package',str(PACKAGE),'--output',str(output)],check=True)
spec=importlib.util.spec_from_file_location('youtube_prepare',helper);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
manifest=json.loads(output.read_text());v=manifest['videos'][0]
en=PACKAGE/(STEM+'.en.srt');en_cues=module.srt(en,plan['duration'])
v['subtitles'].insert(0,dict(file=str(en),language='en',sha256=digest(en),cues=en_cues))
v.update(revision='v10-bilingual-opening',channel_id='UCtn9_kNupjZvWAJVOqWUbYw',channel_name='Lucas Academy',
    chinese_audio=dict(file=str(PACKAGE/WAV),language='zh-Hans',sha256=digest(PACKAGE/WAV),duration=plan['duration']),
    chinese_audio_youtube=dict(file=str(PACKAGE/M4A),language='zh-Hans',sha256=digest(PACKAGE/M4A),duration=plan['duration']),
    thumbnail_en=str(PACKAGE/'04-YouTube封面-暖色画廊-英文.jpg'),thumbnail_zh=str(PACKAGE/'05-YouTube封面-暖色画廊-中文.jpg'),
    altered_content=True,category='Education',made_for_kids=False)
save(output,manifest);save(PACKAGE/'资料/上传清单.json',manifest)
provenance=json.loads((PACKAGE/'资料/素材来源与制作说明.json').read_text());provenance['bilingual_opening_revision']=dict(english_text=next(s for s in plan['scenes'] if s['id']=='n002')['text_en'],chinese_text=next(s for s in plan['scenes'] if s['id']=='n002')['text_zh'],native_english_seconds=13.68,native_chinese_seconds=11.2,all_speech_speed=1.0,new_cloud_requests=0)
save(PACKAGE/'资料/素材来源与制作说明.json',provenance)
delivery=dict(state='complete_local',version='v10',duration=plan['duration'],english_video=str(PACKAGE/(STEM+'.mp4')),chinese_audio=str(PACKAGE/WAV),chinese_audio_youtube=str(PACKAGE/M4A),subtitles=[str(PACKAGE/(STEM+'.en.srt')),str(PACKAGE/(STEM+'.zh-Hans.srt'))],preview=str(PACKAGE/'打开预览.html'),english_retake=str(P/'n002-english/louise/voice.wav'),chinese_retake=str(P.parent/'v10/n002-retake/fangfang/voice.wav'),new_cloud_requests=0,upload_manifest=str(output))
save(P/'delivery.json',delivery)
print(json.dumps(dict(package=str(PACKAGE),duration=plan['duration'],en_cues=len(en_cues),zh_cues=len(cues),sha256=v['sha256']),ensure_ascii=False,indent=2))
