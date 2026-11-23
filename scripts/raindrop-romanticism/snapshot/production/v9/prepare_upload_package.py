"""Assemble the v9 YouTube handoff and archive its former Desktop deliveries."""
import hashlib,html,importlib.util,json,os,re,shutil,subprocess
from pathlib import Path

P=Path(__file__).resolve().parent
DESKTOP=Path('@USER_HOME@/Desktop')
SOURCE=DESKTOP/'压力焦虑肖邦浪漫-完整版-2026-11-21'
PACKAGE=DESKTOP/'压力焦虑肖邦浪漫-YouTube上传'
STAGE=DESKTOP/'.压力焦虑肖邦浪漫-YouTube上传-v9.tmp'
HISTORY=P/'archived-desktop';HISTORY.mkdir(exist_ok=True)
STEM='01-压力焦虑肖邦浪漫-v9-英文-Louise'
TAGS='#chopin #romanticism #arthistory #art #classicalmusic #visualart #museum #artgallery #mononoaware #stressrelief #anxietyrelief #肖邦 #雨滴 #浪漫主义 #物哀'
FFPROBE='/opt/homebrew/bin/ffprobe'
SKILL=Path('@USER_HOME@/.codex/skills/upload-youtube-private')

def link_or_copy(a,b):
    try:os.link(a,b)
    except OSError:shutil.copy2(a,b)
    return str(b)

def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for part in iter(lambda:f.read(8*1024*1024),b''):h.update(part)
    return h.hexdigest()

def metadata(lang):
    source=SOURCE/('YouTube-English-description.txt' if lang=='en' else 'YouTube中文简介.txt')
    title,body=source.read_text().split('\n',1)
    body=re.sub(r'(?m)^YouTube Tags\n[^\n]*\n?','',body)
    body=body.replace('00:04 Chopin and the Raindrop Prelude','00:14 Chopin and the Raindrop Prelude')
    body=body.replace('00:04 肖邦与雨滴','00:14 肖邦与雨滴')
    body=re.sub(r'(?m)^16:06 (?:The Romantic Salon|沙龙)\n?','',body)
    note='Portrait sequence: surviving Delacroix fragments and a hypothetical composition reconstruction after the Louvre 1838 study. Reconstruction is labeled on screen.'
    replacement=note+'\nhttps://collections.louvre.fr/en/ark:/53355/cl020122665' if lang=='en' else '双人像段落展示德拉克洛瓦现存原作片段，以及依据卢浮宫所藏 1838 年构图草图制作的虚拟复原示意。复原画面已明确标注。\nhttps://collections.louvre.fr/en/ark:/53355/cl020122665'
    body=body.replace(note,replacement)
    # The author's exact hashtag set stays in the description and Studio tags.
    body=re.sub(r'(?m)^\s*#[^\n]*$','',body)
    body=re.sub(r'\n{3,}','\n\n',body).strip()+'\n\n'+TAGS
    assert len(title)<=100 and len(body)<=5000
    settings='Visibility: Private; no schedule.\nVideo language: English.\nAudience: General audience; not made for kids.\nCategory: Education.\nPaid promotion: No.\nAltered content: Yes — realistic AI-generated illustrative gallery, monastery and water shots.\nEnglish thumbnail for the main video; Chinese thumbnail is supplied separately.\nAdd English and Simplified Chinese manual subtitles. Attach the synchronized Mandarin audio in Languages if the channel offers manual audio uploads.'
    return dict(title=title,description=body,tags=TAGS.split(),settings=settings)

def blocks(meta):
    return '\n\n'.join('【'+name+'】\n'+value for name,value in [
        ('标题 / Title',meta['title']),('简介 / Description',meta['description']),
        ('标签 / Tags',' '.join(meta['tags'])),('上传设置 / Upload settings',meta['settings'])])+'\n'

def main():
    checks=json.loads((P/'full-checks.json').read_text());assert checks['state']=='passed'
    plan=json.loads((P/'full-plan.json').read_text())
    assert not STAGE.exists(),'A staging package already exists; inspect it before replacing.'
    STAGE.mkdir();(STAGE/'资料').mkdir()
    files={
        SOURCE/'01-English-full-v9.mp4':STEM+'.mp4',
        SOURCE/'02-Chinese-aligned-audio-v9.wav':'02-压力焦虑肖邦浪漫-v9-中文-Fangfang.wav',
        SOURCE/'03-English-v9.srt':STEM+'.en.srt',
        SOURCE/'04-Chinese-v9.srt':STEM+'.zh-Hans.srt',
        SOURCE/'Cover-English.jpg':'04-YouTube封面-暖色画廊-英文.jpg',
        SOURCE/'Cover-Chinese.jpg':'05-YouTube封面-暖色画廊-中文.jpg',
        SOURCE/'中文定稿.docx':'09-压力焦虑肖邦浪漫-中文文案.docx',
        SOURCE/'英文配音稿.docx':'10-压力焦虑肖邦浪漫-英文文案.docx',
        SOURCE/'Chinese-preview-v9.mp3':'资料/中文播放预览.mp3',
        SOURCE/'素材来源与制作说明.json':'资料/素材来源与制作说明.json',
        P/'full-checks.json':'资料/v9成片检查.json',
        P/'browser-checks.json':'资料/v9播放检查.json',
    }
    for source,name in files.items():
        target=STAGE/name;link_or_copy(source,target)
        assert digest(source)==digest(target)
    en=metadata('en');zh=metadata('zh')
    names={'en':'03-YouTube英文标题简介标签.txt','zh':'06-YouTube中文标题简介标签.txt'}
    for language,meta in [('en',en),('zh',zh)]:(STAGE/names[language]).write_text(blocks(meta),encoding='utf-8')
    cues=[dict(start=round(c['start'],3),end=round(c['end'],3),text=c['text']) for c in plan['captions']['zh']]
    program=[dict(number=1,src=STEM+'.mp4',srt=STEM+'.zh-Hans.srt',englishSrt=STEM+'.en.srt',
        chineseAudio='02-压力焦虑肖邦浪漫-v9-中文-Fangfang.wav',englishMetadata=names['en'],chineseMetadata=names['zh'],cues=cues)]
    (STAGE/'资料/播放与字幕数据.json').write_text(json.dumps(program,ensure_ascii=False,indent=2))
    original=(SOURCE/'影片预览-音频修订v9.html').read_text()
    js=original.split(';const v=',1)[1].split('</script>',1)[0]
    caption_data=json.dumps(plan['captions'],ensure_ascii=False).replace('</','<\\/')
    page='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>压力？焦虑？肖邦？浪漫？ · v9 上传包</title><style>*{box-sizing:border-box}body{margin:0;background:#141719;color:#ece5d8;font:16px/1.7 system-ui}main{max-width:1120px;margin:auto;padding:26px 20px 60px}h1{font-size:28px}a{color:#e8c78b}button,select{font:inherit;padding:6px 12px;color:#eee;background:#292d30;border:1px solid #8b795b;border-radius:5px;cursor:pointer}button[aria-pressed=true]{background:#9e824e;color:#101418}.controls,.links{display:flex;gap:12px;flex-wrap:wrap;margin:18px 0}.screen{position:relative}video{width:100%;display:block;background:black}.captions{position:absolute;bottom:64px;left:9%;right:9%;text-align:center;pointer-events:none;white-space:pre-line;font-size:24px;line-height:1.4;text-shadow:0 2px 4px #000;color:#fff}.covers{display:flex;gap:18px;margin:30px 0}.covers a{width:50%}.covers img{width:100%;display:block}p{color:#c8c0b3}@media(max-width:650px){h1{font-size:23px}.captions{font-size:15px;bottom:46px}.covers{flex-direction:column}.covers a{width:100%}}</style><main><h1>压力？焦虑？肖邦？浪漫？</h1><p>Yancy &amp; Eunice · v9 · 16 分 23 秒 · 英文 Louise / 中文 Fangfang</p><div class="controls"><button id="english" aria-pressed="true">英文 Louise</button><button id="chinese" aria-pressed="false">中文 Fangfang</button><label>字幕 <select id="subtitle"><option value="none">关闭</option><option value="en">English</option><option value="zh">中文</option></select></label></div><div class="screen"><video id="film" controls preload="metadata" src="'''+STEM+'''.mp4"></video><div id="caption" class="captions"></div></div><audio id="zh" preload="metadata" src="资料/中文播放预览.mp3"></audio><div class="links"><a href="'''+STEM+'''.mp4" download>英文视频</a><a href="02-压力焦虑肖邦浪漫-v9-中文-Fangfang.wav" download>中文同步音轨</a><a href="'''+STEM+'''.en.srt" download>英文字幕</a><a href="'''+STEM+'''.zh-Hans.srt" download>中文字幕</a></div><p>开头纯人声；音乐柔和淡出、淡入。中文字幕和英文字幕都是独立文件，影片没有烧录字幕。</p><div class="covers"><a href="04-YouTube封面-暖色画廊-英文.jpg"><img src="04-YouTube封面-暖色画廊-英文.jpg" alt="英文封面"></a><a href="05-YouTube封面-暖色画廊-中文.jpg"><img src="05-YouTube封面-暖色画廊-中文.jpg" alt="中文封面"></a></div><div class="links"><a href="03-YouTube英文标题简介标签.txt">英文标题、简介与标签</a><a href="06-YouTube中文标题简介标签.txt">中文标题、简介与标签</a><a href="09-压力焦虑肖邦浪漫-中文文案.docx">中文文案 Word</a><a href="10-压力焦虑肖邦浪漫-英文文案.docx">英文文案 Word</a></div><script>const CUES='''+caption_data+''';const v='''+js+'''</script></main></html>'''
    (STAGE/'打开预览.html').write_text(page,encoding='utf-8')
    (STAGE/'使用说明.txt').write_text('v9 上传包\n英文视频＋中文同步独立音轨＋中英文独立字幕。\n打开「打开预览.html」切换语言和字幕。\n封面保持已选定的暖色画廊设计，两种语言各一张。\n03、06 文本各分标题、简介、标签和上传设置四块，保留素材署名。\nYouTube 先保存为 Private，不公开发布、不安排定时发布。\n',encoding='utf-8')
    archive=HISTORY/'v9-desktop-delivery'
    if not archive.exists():shutil.copytree(SOURCE,archive,copy_function=link_or_copy)
    old=HISTORY/'youtube-upload-before-v9'
    if PACKAGE.exists():
        assert not old.exists(),'The previous upload package archive already exists.'
        PACKAGE.rename(old)
    STAGE.rename(PACKAGE)
    output=P/'youtube-upload-manifest.json'
    subprocess.run(['python3',str(SKILL/'scripts/prepare_upload.py'),'--package',str(PACKAGE),'--output',str(output)],check=True)
    spec=importlib.util.spec_from_file_location('youtube_prepare',SKILL/'scripts/prepare_upload.py');helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
    manifest=json.loads(output.read_text());video=manifest['videos'][0]
    eng=PACKAGE/(STEM+'.en.srt');eng_cues=helper.srt(eng,plan['duration'])
    assert len(eng_cues)==len(plan['captions']['en'])
    video['subtitles'].insert(0,dict(file=str(eng),language='en',sha256=digest(eng),cues=eng_cues))
    cn=PACKAGE/'02-压力焦虑肖邦浪漫-v9-中文-Fangfang.wav'
    probe=json.loads(subprocess.check_output([FFPROBE,'-v','error','-show_format','-show_streams','-of','json',str(cn)]))
    assert abs(float(probe['format']['duration'])-plan['duration'])<1/48000
    video.update(revision='v9',channel_id='UCtn9_kNupjZvWAJVOqWUbYw',channel_name='Lucas Academy',
        chinese_audio=dict(file=str(cn),language='zh-Hans',sha256=digest(cn),duration=plan['duration']),
        thumbnail_en=str(PACKAGE/'04-YouTube封面-暖色画廊-英文.jpg'),thumbnail_zh=str(PACKAGE/'05-YouTube封面-暖色画廊-中文.jpg'),
        altered_content=True,category='Education',made_for_kids=False)
    output.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    shutil.copy2(output,PACKAGE/'资料/上传清单.json')
    print(json.dumps(dict(package=str(PACKAGE),video_sha256=video['sha256'],duration=video['duration'],
        en_cues=len(eng_cues),zh_cues=len(cues),en_description_chars=len(en['description']),zh_description_chars=len(zh['description']),
        source_archive=str(archive)),ensure_ascii=False,indent=2))

if __name__=='__main__':main()
