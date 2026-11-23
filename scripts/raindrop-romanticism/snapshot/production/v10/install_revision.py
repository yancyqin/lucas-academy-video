"""Atomically refresh the existing upload package after the one-line retake."""
import hashlib,json,os,re,shutil
from pathlib import Path

P=Path(__file__).resolve().parent;V9=P.parent/'v9'
PACKAGE=Path('@DATA_ROOT@/production/v12/published-release')
plan=json.loads((P/'full-plan.json').read_text());checks=json.loads((P/'checks.json').read_text())
assert checks['state']=='passed'
WAV='02-压力焦虑肖邦浪漫-v9-中文-Fangfang.wav'
M4A='02-压力焦虑肖邦浪漫-v9-中文-Fangfang-YouTube.m4a'
SRT='01-压力焦虑肖邦浪漫-v9-英文-Louise.zh-Hans.srt'
DOC='09-压力焦虑肖邦浪漫-中文文案.docx'
def save(path,data):path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(8*1024*1024),b''):h.update(chunk)
    return h.hexdigest()
def atomic_copy(source,target):
    temp=target.with_name('.'+target.name+'.tmp');shutil.copy2(source,temp);os.replace(temp,target)

expected='fa61a35bf856f9e989b7e9c30b0681e9b4ef3dd20ea132e02a364dfbc0fec84b'
assert digest(PACKAGE/'01-压力焦虑肖邦浪漫-v9-英文-Louise.mp4')==expected
for source,target in [(P/'delivery'/WAV,PACKAGE/WAV),(P/'delivery'/M4A,PACKAGE/M4A),
                      (P/'delivery'/SRT,PACKAGE/SRT),(P/DOC,PACKAGE/DOC),
                      (P/'delivery/中文播放预览.mp3',PACKAGE/'资料/中文播放预览.mp3')]:atomic_copy(source,target)
program=json.loads((PACKAGE/'资料/播放与字幕数据.json').read_text())
program[0]['cues']=[dict(start=round(c['start'],3),end=round(c['end'],3),text=c['text']) for c in plan['captions']['zh']]
program[0]['chineseAudioYouTube']=M4A
save(PACKAGE/'资料/播放与字幕数据.json',program)
page_path=PACKAGE/'打开预览.html';page=page_path.read_text()
new_cues=json.dumps(plan['captions'],ensure_ascii=False).replace('</','<\\/')
page,n=re.subn(r'const CUES=.*?;const v=',lambda _: 'const CUES='+new_cues+';const v=',page,count=1,flags=re.S)
assert n==1
page=page.replace('src="资料/中文播放预览.mp3"','src="资料/中文播放预览.mp3?revision=v9.1"')
page=page.replace('· v9 ·','· v9（中文开头已重录） ·')
page_path.write_text(page,encoding='utf-8')
manifest=json.loads((V9/'youtube-upload-manifest.json').read_text())
v=manifest['videos'][0]
v['chinese_audio'].update(sha256=digest(PACKAGE/WAV),revision=checks['revision'])
v['chinese_audio_youtube']=dict(file=str(PACKAGE/M4A),language='zh-Hans',sha256=digest(PACKAGE/M4A),duration=plan['duration'],revision=checks['revision'])
zh=next(s for s in v['subtitles'] if s['language']=='zh-Hans')
zh.update(sha256=digest(PACKAGE/SRT),cues=program[0]['cues'])
v['chinese_script']=dict(file=str(PACKAGE/DOC),sha256=digest(PACKAGE/DOC),revision=checks['revision'])
save(P/'youtube-upload-manifest.json',manifest);save(PACKAGE/'资料/上传清单.json',manifest)
save(PACKAGE/'资料/中文开头重录检查.json',checks)
provenance=json.loads((PACKAGE/'资料/素材来源与制作说明.json').read_text())
if isinstance(provenance,dict):
    provenance['chinese_opening_revision']=dict(text=checks['text'],method='Local Qwen3-TTS 1.7B → local Fangfang conversion',native_seconds=11.2,speed=1.0,new_cloud_requests=0)
    save(PACKAGE/'资料/素材来源与制作说明.json',provenance)
note=PACKAGE/'使用说明.txt';text=note.read_text()
text+='\n中文开头微调已同步文案、Fangfang 音轨和中文字幕：\n听起来平静而优美，对吗？\n但是你能想象，在写这个前奏曲的那个冬天，肖邦曾在极度悲伤和焦虑中弹琴吗？\n采用本地 Qwen3-TTS 1.7B 生成后本地换声，自然语速 11.2 秒，无新增 API 费用。\n中文 WAV 为无损母带；另附结尾为 YouTube.m4a 的兼容音轨供平台上传。\n'
note.write_text(text,encoding='utf-8')
delivery=json.loads((V9/'delivery.json').read_text())
delivery.update(chinese_opening_revision=checks['revision'],chinese_opening_retake=checks['converted'],chinese_opening_seconds=11.2,
    chinese_audio_youtube=str(PACKAGE/M4A),latest_chinese_checks=str(P/'checks.json'))
save(V9/'delivery.json',delivery);save(P/'delivery.json',delivery)
print(json.dumps(dict(package=str(PACKAGE),revision=checks['revision'],zh_cues=len(program[0]['cues']),english_video_unchanged=True),ensure_ascii=False,indent=2))
