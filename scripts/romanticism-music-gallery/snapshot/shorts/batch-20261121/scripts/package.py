"""Build a portable Desktop upload package: approved sample plus four new shorts."""
from pathlib import Path
from datetime import datetime,timezone
from PIL import Image
import json,hashlib,shutil,subprocess,sys,html,re

ROOT=Path(__file__).resolve().parents[1]
PROJECT=ROOT.parents[1]
VIDEO_REPO=PROJECT.parent.parent/'lucas-academy-video'
DEST=Path('@USER_HOME@/Desktop/山、海、人间-竖屏短视频-上传')
sys.path.insert(0,str(VIDEO_REPO/'scripts'))
from youtube_tags import hashtags,tags,DEFAULT
batch=json.loads((ROOT/'batch.json').read_text())
common_credits=json.loads((PROJECT/'v4/sources/credits.json').read_text())
W,H=1080,1920

def sha(file):
    digest=hashlib.sha256()
    with file.open('rb')as stream:
        for block in iter(lambda:stream.read(8*1024*1024),b''):digest.update(block)
    return digest.hexdigest()

def write_json(file,value):file.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def clock(value):value=int(value);return f'{value//60}:{value%60:02d}'

def items():
    sample_root=Path(batch['approved_sample'])
    sample=json.loads((sample_root/'edit-plan.json').read_text())
    sample.update(number=1,stem='01-面对辽阔',category='nature',root=str(sample_root),
        video_source=str(sample_root/'exports/面对辽阔-竖屏示范.mp4'),
        srt_source=str(sample_root/'subtitles/面对辽阔-竖屏示范.zh-Hans.srt'),
        poster_source=str(sample_root/'checks/final-23.5.jpg'),
        relation_zh='弗里德里希的两幅风景，把站立的人、雾海与海边的峭壁放在同一次凝望中。',
        relation_en='Two landscapes by Friedrich place people before fog, sea and cliffs, inviting a closer look at how a human figure relates to a vast view.')
    result=[sample]
    for item in batch['jobs']:
        item=dict(item);folder=Path(item['root'])
        if item['id']=='02-silence':item['music']={**item['music'],'performer':'Musopen recording'}
        item.update(video_source=str(folder/'exports'/(item['stem']+'.mp4')),
                    srt_source=str(folder/'subtitles'/(item['stem']+'.zh-Hans.srt')),
                    poster_source=str(folder/'checks'/f'final-{item["first_close"]}.jpg'))
        result.append(item)
    return result

def label_title(item):return next(c['en'][0] for c in item['labels'] if c['id']=='music')

def scan_credits():
    out=['Sculpture scans · CC BY 4.0']
    for scan in common_credits['scans']:
        if scan.get('model_credit'):
            out += [scan.get('model_title',scan['title_en'])+' — '+scan['model_credit'],scan['model_source']]
    out += ['https://creativecommons.org/licenses/by/4.0/',
            'Display modifications: scaled, oriented, grounded, decimated and textures resized. Philopoemen: source segments joined and welded. Seated Lion: duplicate mesh omitted.',
            'The Enslaved Woman / A Little Girl with Kittens — SMK Open, public domain.',
            'https://open.smk.dk/artwork/image/KMS5025',
            'https://open.smk.dk/artwork/image/KMS5471',
            'Moose the Dragon — original sculpture and scan, Lucas Academy.']
    return '\n'.join(out)

def metadata(item,language):
    chinese=language=='zh'
    title=item['title'] if chinese else item['title_en']
    music=item['music'];en_music=label_title(item)
    own=['shorts','romanticism','classicalmusic','painting','museum',
         'chopin' if item['category']=='nature' else 'beethoven',
         'landscape' if item['category']=='nature' else 'humanlife']
    text=(('58 秒，沿着浪漫主义大厅走近两幅相关画作。先看完整作品，再推近局部。\n\n'+item['relation_zh']+
           '\n\n英文画名与画家标签；独立简体中文 SRT。纯音乐，无人声。\n\n画作\n') if chinese else
          ('A 58-second walk through the Romantic Salon, approaching two related paintings. See each whole work, then move closer to selected details.\n\n'+item['relation_en']+
           '\n\nEnglish artwork and artist labels. Separate Simplified Chinese SRT. Instrumental music; no narration.\n\nPaintings\n'))
    for work in item['artworks']:
        text+=(work['title_zh']+' — '+work['artist_zh'] if chinese else work['title_en']+' — '+work['artist_en'])+'\n'+work['source']+'\n'
    text+='\n'+('音乐片段 / Music excerpt' if chinese else 'Music excerpt')+'\n'+en_music+'\n'
    text+=music['performer']+' · '+music['license']+'\n'
    text+=('原录音时间：' if chinese else 'Source recording excerpt: ')+clock(music['excerpt_start'])+'–'+clock(music['excerpt_start']+58)+'\n'
    text+=music['source']+'\n'
    if music.get('credit_note') and '署名' in music['credit_note'] and '不一致' in music['credit_note']:
        text+=('演奏者目录署名不一致，本片按 Musopen 录音署名。\n' if chinese else 'Performer attribution differs between source catalogs; credited here as a Musopen recording.\n')
    text+='\n'+('Yancy 与 Eunice 共同创作。' if chinese else 'Created by Yancy and Eunice.')+'\n\n'+scan_credits()+'\n\n'+hashtags(own)
    filename=item['stem']+('-中文.txt' if chinese else '-英文.txt')
    settings=(f'视频文件：{item["stem"]}.mp4\n字幕文件：{item["stem"]}.zh-Hans.srt（简体中文）。\n'
              '规格：1080 × 1920，9:16，24 fps，58 秒；H.264 / AAC 48 kHz 双声道。\n'
              '视频语言：英文标签。类别：教育。\n'
              '简介保留署名与来源链接。' if chinese else
              f'Video: {item["stem"]}.mp4\nSubtitles: {item["stem"]}.zh-Hans.srt (Simplified Chinese).\n'
              'Format: 1080 × 1920, 9:16, 24 fps, 58 seconds; H.264 / AAC 48 kHz stereo.\n'
              'Picture labels: English. Category: Education.\n'
              'Keep source and attribution links in the description.')
    assert len(title)<=100 and len(text)<=5000,(filename,len(text))
    assert text.splitlines()[-1].split()[:8]==['#'+t for t in DEFAULT]
    body=f'【标题 / Title】\n{title}\n\n【简介 / Description】\n{text}\n\n【标签 / Tags】\n{tags(own)}\n\n【上传设置 / Upload settings】\n{settings}\n'
    (DEST/'上传文案'/filename).write_text(body)
    return {'file':'上传文案/'+filename,'language':language,'title':title,'description_characters':len(text),'tags_characters':len(tags(own))}

def main():
    marker=DEST/'资料/上传包信息.json'
    if DEST.exists() and not marker.exists():raise RuntimeError('Existing unrelated Desktop folder; refusing to overwrite.')
    for name in ['','资料','资料/预览图','上传文案']:(DEST/name).mkdir(parents=True,exist_ok=True)
    write_json(marker,{'project':'romanticism-shorts-batch','created_utc':datetime.now(timezone.utc).isoformat(),
                       'series_films':len(batch['jobs']),'approved_sample':1,'film_count':len(batch['jobs'])+1})
    program=[];records=[];public_sources=[];all_metadata=[]
    attribution=['山、海、人间 · 竖屏短视频','Yancy 与 Eunice 共同创作',f'{len(batch["jobs"])+1} 支各 58 秒，英文标签，独立简体中文字幕，纯音乐、无人声。','']
    for item in items():
        folder=Path(item['root']);check=json.loads((folder/'checks/verified.json').read_text())
        assert check['status']=='passed' and check['full_decode']=='passed'
        assert check['visual_review'].startswith('Passed'),item['id'] if item.get('id') else 'sample'
        source=Path(item['video_source']);target=DEST/(item['stem']+'.mp4')
        result=subprocess.run(['/bin/cp','-c',str(source),str(target)],capture_output=True)
        if result.returncode:shutil.copy2(source,target)
        assert sha(target)==check['video']['sha256']
        srt=DEST/(item['stem']+'.zh-Hans.srt');shutil.copy2(item['srt_source'],srt)
        blocks=srt.read_text(encoding='utf-8-sig').strip().split('\n\n');assert len(blocks)==4
        for block,cue in zip(blocks,item['labels']):assert '\n'.join(block.splitlines()[2:])==cue['zh']
        poster=Image.open(item['poster_source']).convert('RGB');poster.thumbnail((360,640),Image.Resampling.LANCZOS)
        poster_file='资料/预览图/'+item['stem']+'.jpg';poster.save(DEST/poster_file,quality=89)
        en=metadata(item,'en');zh=metadata(item,'zh');all_metadata += [en,zh]
        program.append({'number':item['number'],'title':item['title'],'titleEn':item['title_en'],
                        'category':item['category'],'src':target.name,'srt':srt.name,'poster':poster_file,
                        'pair':' ＋ '.join(w['title_zh'] for w in item['artworks']),
                        'music':label_title(item),'englishMetadata':en['file'],'chineseMetadata':zh['file'],
                        'cues':[{'start':c['start'],'end':c['end'],'text':c['zh']}for c in item['labels']]})
        records.append({'file':target.name,'sha256':sha(target),'bytes':target.stat().st_size,
                        'duration':58,'width':1080,'height':1920,'fps':24,'full_decode':'passed',
                        'chinese_srt':srt.name,'subtitle_cues':4,'artwork_ids':[a['id']for a in item['artworks']],
                        'category':item['category'],'composer':'Chopin' if item['category']=='nature' else 'Beethoven',
                        'source_excerpt_start':item['music']['excerpt_start'],'source_excerpt_seconds':58})
        art_fields=['id','title_zh','title_en','artist_zh','artist_en','source','license','original_sha256']
        public_music={k:v for k,v in item['music'].items() if k not in ['file','local_file']}
        public_sources.append({'title':item['title_en'],'artworks':[{k:a[k]for k in art_fields}for a in item['artworks']],
                               'music':public_music,'layout_snapshot':item['source_snapshot']})
        attribution += [item['stem']+' / '+item['title_en'],'重点作品 / Featured paintings']
        for work in item['artworks']:
            attribution += [work['title_en']+' / '+work['title_zh'],work['artist_en']+' / '+work['artist_zh'],work['source'],work['license'],'']
        m=item['music'];attribution += [label_title(item),m['performer']+' · '+m['license'],m['source'],
            f'Source recording excerpt: {clock(m["excerpt_start"])}–{clock(m["excerpt_start"]+58)}',m.get('credit_note',''),'']
        print('PACKAGED',target.name,target.stat().st_size,flush=True)
    attribution += ['雕塑与中央作品 / Sculpture scans and centerpiece','']
    for scan in common_credits['scans']:
        attribution += [scan.get('model_title',scan['title_en']),scan.get('model_credit','SMK Open')+' · '+scan['license'],
            scan.get('model_source',scan['source']),scan['license_url'],'Modifications: '+scan['modifications'],'']
    attribution += ['Moose the Dragon — original sculpture and scan from Lucas Academy.']
    (DEST/'素材署名.txt').write_text('\n'.join(attribution)+'\n')
    write_json(DEST/'资料/作品与录音来源.json',{'films':public_sources,'sculpture_scans':common_credits['scans'],
                                               'central_sculpture':common_credits['central_sculpture']})
    write_json(DEST/'资料/播放与字幕数据.json',program)
    lines=['山、海、人间 · 竖屏短视频上传包',f'本组共 {len(program)} 支，包含已确认的示范。本次更新《山峦与光》的瀑布镜头，新增《希望与自由》。','',
           '每支 58 秒，1080 × 1920，24 fps。视频只显示英文标签，中文翻译在同名 .zh-Hans.srt 中。',
           '每支使用一段连续音乐片段，首尾轻微淡入淡出。自然题材配肖邦，人文题材配贝多芬。','',
           f'打开“打开预览.html”可切换 {len(program)} 支短片并显示中文字幕。',
           '“上传文案”中每支各有中文、英文版本，包含标题、简介、标签和上传设置。',
           '视频与同名 SRT 一起使用；素材署名已写入各片上传简介。','']
    for item in program:lines += [item['src'],item['pair'],item['music'],'']
    (DEST/'使用说明与片单.txt').write_text('\n'.join(lines))
    build_player(program)
    report={'status':'awaiting browser review','videos':records,'series_films':len(batch['jobs']),'approved_sample_included':True,
            'english_picture':True,'separate_chinese_srt_files':len(program),'featured_artworks_per_film':2,
            'music_policy':'Nature shorts use Chopin; human-theme shorts use Beethoven. No narration.',
            'metadata':all_metadata,'visual_review':'Passed: each new film’s complete paintings, close-ups and English labels inspected.',
            'browser_review':'pending'}
    write_json(DEST/'资料/校验记录.json',report)
    write_json(ROOT/'checks/desktop-package.json',{'path':str(DEST),'status':'awaiting browser review','program':program})
    print('DESKTOP PACKAGE READY FOR PLAYBACK CHECK',DEST,flush=True)

def build_player(program):
    buttons=''.join(f'<button data-index="{i}" type="button"><b>{html.escape(item["titleEn"])}</b><span>{html.escape(item["title"])}</span><small>{html.escape(item["pair"])}</small></button>' for i,item in enumerate(program))
    document='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>山、海、人间 · 竖屏短视频</title>
<style>*{box-sizing:border-box}body{margin:0;padding:26px 20px;background:#101820;color:#f3e8d4;font:16px/1.6 system-ui,sans-serif}main{max-width:1100px;margin:auto}h1{font-size:29px;margin:0}p{color:#b8c7cf}.layout{display:grid;grid-template-columns:minmax(250px,360px) minmax(300px,1fr);gap:38px;margin-top:24px}nav{display:flex;flex-direction:column;gap:10px}button{cursor:pointer;text-align:left;border:1px solid #364d5c;border-radius:7px;color:#eee5d3;background:#15232c;padding:14px 16px;font:inherit}button.active{border-color:#e0bf82;background:#293b43}button b,button span,button small{display:block}button b{font-size:17px}button small{color:#adbec7;margin-top:6px;font-size:13px}article{max-width:430px;margin:auto;width:100%}video{display:block;width:100%;aspect-ratio:9/16;max-height:78vh;background:#000}video::cue{font-size:85%;background:rgba(0,0,0,.7)}article h2{font-size:22px;margin:0}article p{font-size:14px}a{color:#e5c48c}select{font:inherit;background:#20343f;color:#fff;border:1px solid #6e8390;padding:3px 9px}.downloads{display:flex;gap:14px;flex-wrap:wrap}@media(max-width:760px){body{padding:18px 14px}.layout{grid-template-columns:1fr;gap:24px}nav{display:grid;grid-template-columns:1fr 1fr}button{padding:10px}button b{font-size:14px}button small{display:none}h1{font-size:25px}article{max-width:410px}}</style>
<main><h1>山、海、人间 · 竖屏短视频</h1><p>每支两幅相关画作 · 58 秒 · 英文标签、独立中文字幕<br>自然 × 肖邦 ／ 人文 × 贝多芬 · 纯音乐，无人声</p>
<div class="layout"><nav>'''+buttons+'''</nav><article><h2 id="title"></h2><p id="pair"></p><video controls playsinline preload="metadata"></video>
<p>中文字幕：<select aria-label="Chinese subtitles"><option value="off">关闭</option><option value="zh">显示中文</option></select></p>
<p class="downloads"><a id="video-download">视频文件</a><a id="srt-download" download>中文 SRT</a><a id="metadata-en">English metadata</a><a id="metadata-zh">中文上传文案</a></p><p><a href="素材署名.txt">完整素材署名</a> · <a href="使用说明与片单.txt">使用说明与片单</a></p></article></div></main>
<script id="program" type="application/json">'''+json.dumps(program,ensure_ascii=False).replace('</','<\\/')+'''</script><script>
const films=JSON.parse(document.getElementById('program').textContent),video=document.querySelector('video'),select=document.querySelector('select');
const track=video.addTextTrack('subtitles','简体中文','zh-Hans');track.mode='disabled';
function chooseFilm(index){const film=films[index];video.pause();video.src=film.src;video.poster=film.poster;video.load();
 document.getElementById('title').textContent=film.titleEn;document.getElementById('pair').textContent=film.pair+' · '+film.music;
 document.getElementById('video-download').href=film.src;document.getElementById('srt-download').href=film.srt;
 document.getElementById('metadata-en').href=film.englishMetadata;document.getElementById('metadata-zh').href=film.chineseMetadata;
 track.mode='hidden';for(const cue of [...(track.cues||[])])track.removeCue(cue);for(const cue of film.cues)track.addCue(new VTTCue(cue.start,cue.end,cue.text));
 track.mode=select.value==='zh'?'showing':'disabled';document.querySelectorAll('button[data-index]').forEach((button,i)=>button.classList.toggle('active',i===index));
 window.currentFilm=index;
}
document.querySelectorAll('button[data-index]').forEach(button=>button.addEventListener('click',()=>chooseFilm(Number(button.dataset.index))));
select.addEventListener('change',()=>track.mode=select.value==='zh'?'showing':'disabled');chooseFilm(0);
</script></html>'''
    (DEST/'打开预览.html').write_text(document)

if __name__=='__main__':main()
