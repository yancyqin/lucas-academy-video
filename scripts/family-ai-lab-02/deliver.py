"""Update the existing desktop delivery, exact audio tracks and YouTube copy."""
from pathlib import Path
import argparse,hashlib,json,os,shutil,subprocess

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'out/family-ai-lab-02/orbital-v2'
DOC=ROOT/'docs/family-ai-lab-02'


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def probe(p):return json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(p)]))


def audio_hash(p,index):return subprocess.check_output(['ffmpeg','-v','error','-i',str(p),'-map',f'0:a:{index}','-c:a','copy','-f','hash','-hash','sha256','-'],text=True).strip()


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--dest',type=Path,default=Path.home()/'Desktop/0和1能聊天吗-交付');args=parser.parse_args();dest=args.dest
    old={}
    if (dest/'SHA256SUMS').exists():
        for line in (dest/'SHA256SUMS').read_text().splitlines():
            digest,name=line.split('  ',1);old[name]=digest
    def allowed(p,new_digest=None):
        if not p.exists():return
        assert p.is_file() and not p.is_symlink(),p
        value=sha(p)
        assert value==new_digest or value==old.get(str(p.relative_to(dest))),('Desktop file edited outside the package; refusing overwrite',str(p))
    def copy(source,relative):
        target=dest/relative;digest=sha(source);allowed(target,digest);target.parent.mkdir(parents=True,exist_ok=True)
        if not target.exists() or sha(target)!=digest:
            temp=target.with_name('.'+target.stem+'.updating'+target.suffix);shutil.copy2(source,temp);os.replace(temp,target)
        assert sha(target)==digest
    full=json.loads((DOC/'design-v2/orbital-verification.json').read_text());short=json.loads((DOC/'design-v2/short/verification.json').read_text())
    full_movie=ROOT/full['movie'];short_movie=ROOT/short['movie'];assert sha(full_movie)==full['sha256'] and sha(short_movie)==short['sha256']
    meta=json.loads((DOC/'youtube.json').read_text())
    assert all(r['sourceMovieSha256']==(full if key.startswith('long/') else short)['sha256'] for key,r in meta.items())
    tl=json.loads((ROOT/'public/family-ai-lab-02/orbital-v2/short/timeline.json').read_text());start=next(r['from'] for r in tl['lines'] if r['visual']=='friends');ending=OUT/'short/delivery/ending-internet-ai.mp4';ending_receipt=ending.with_suffix('.json')
    valid=False
    if ending.exists() and ending_receipt.exists():
        old_end=json.loads(ending_receipt.read_text());valid=old_end.get('sourceSha256')==short['sha256'] and old_end.get('sha256')==sha(ending)
    if not valid:
        subprocess.run(['ffmpeg','-v','error','-y','-ss',str(start/30),'-i',str(short_movie),'-t',str((tl['durationInFrames']-start)/30),'-frames:v',str(tl['durationInFrames']-start),'-map','0:v:0','-map','0:a:0','-map','0:a:1','-vf','scale=720:1280','-c:v','libx264','-crf','20','-preset','fast','-c:a','aac','-b:a','192k','-disposition:a:0','default','-disposition:a:1','0','-movflags','+faststart',str(ending)],check=True)
        ending_receipt.write_text(json.dumps({'sourceSha256':short['sha256'],'startFrame':start,'frames':tl['durationInFrames']-start,'sha256':sha(ending)},indent=2)+'\n')
    ending_info=probe(ending);ev=[s for s in ending_info['streams'] if s['codec_type']=='video'];ea=[s for s in ending_info['streams'] if s['codec_type']=='audio']
    assert len(ev)==1 and (ev[0]['width'],ev[0]['height'])==(720,1280) and int(ev[0]['nb_frames'])==tl['durationInFrames']-start
    assert [(s['tags']['language'],s['disposition']['default']) for s in ea]==[('eng',1),('zho',0)]
    mappings=[
      (full_movie,'01-长片/0和1能聊天吗-双语长片.mp4'),(OUT/'delivery/opening-yes.mp4','01-长片/开头审核-30秒.mp4'),
      (OUT/'delivery/en.srt','01-长片/0和1能聊天吗-双语长片.en.srt'),(OUT/'delivery/zh-Hans.srt','01-长片/0和1能聊天吗-双语长片.zh-Hans.srt'),
      (short_movie,'02-竖屏短片/0和1能聊天吗-竖屏短片.mp4'),(ending,'02-竖屏短片/结尾审核-互联网AI.mp4'),
      (OUT/'short/delivery/en.srt','02-竖屏短片/0和1能聊天吗-竖屏短片.en.srt'),(OUT/'short/delivery/zh-Hans.srt','02-竖屏短片/0和1能聊天吗-竖屏短片.zh-Hans.srt'),
      (OUT/'cover/family-ai-lab-02.en.png','03-封面/英文封面.png'),(OUT/'cover/family-ai-lab-02.zh.png','03-封面/中文封面.png'),
      (OUT/'delivery/credits.md','素材来源说明.md'),(OUT/'delivery/fluentui-emoji-LICENSE.txt','Fluent-Emoji-LICENSE.txt'),
    ]
    for kind,label in [('long','长片'),('short','Shorts')]:
        for lang,name in [('en','English'),('zh','中文')]:mappings.append((DOC/f'youtube/{kind}.{lang}.txt',f'04-YouTube文案/YouTube-{label}-{name}.txt'))
    for source,relative in mappings:assert source.is_file();allowed(dest/relative,sha(source))
    notes=f'''0和1，能聊天吗？ / Can 0 and 1 Talk?

01-长片：4分24.73秒，1920×1080；另附最新30秒开头审核片。
02-竖屏短片：{short['seconds']:.2f}秒，1080×1920，9:16；结尾连接互联网和AI，带俏皮的分享问题。
03-封面：中英文各一张，1280×720，使用长片首帧。
04-YouTube文案：长片、Shorts各有中英文标题、简介、hashtags、Studio标签和上传设置。

两部影片默认英语，并含独立中文音轨。播放器可切换音轨；字幕为单独SRT文件。
每部的中英文M4A直接从对应最终影片无损提取，编码内容和起止时间一致。
视频画面没有烧录字幕。短片另附互联网与AI新结尾的审核片。
中英文YouTube文案是同一视频的语言本地化资料，不是四个不同视频。

代码与制作记录：https://github.com/yancyqin/lucas-academy-video/pull/48
素材来源与许可随包附上。SHA256SUMS用于核对文件完整性。
'''
    notes_path=dest/'使用说明.txt';allowed(notes_path,hashlib.sha256(notes.encode()).hexdigest());allowed(dest/'PACKAGE.json')
    for movie,folder in [(full_movie,'01-长片'),(short_movie,'02-竖屏短片')]:
        for index,label,language in [(0,'英文','eng'),(1,'中文','zho')]:
            target=dest/f'{folder}/{label}音轨.m4a'
            if target.exists() and audio_hash(target,0)==audio_hash(movie,index) and probe(target)['streams'][0]['tags'].get('language')==language:continue
            allowed(target)
    dest.mkdir(parents=True,exist_ok=True)
    for source,relative in mappings:copy(source,relative)
    audio={}
    for kind,movie,folder,seconds in [('long',full_movie,'01-长片',full['durationSeconds']),('short',short_movie,'02-竖屏短片',short['seconds'])]:
        for index,lang,label in [(0,'en','英文'),(1,'zh','中文')]:
            target=dest/f'{folder}/{label}音轨.m4a';expected=audio_hash(movie,index)
            if not target.exists() or audio_hash(target,0)!=expected or probe(target)['streams'][0]['tags'].get('language')!=('eng' if lang=='en' else 'zho'):
                temp=target.with_name('.'+target.stem+'.updating.m4a');subprocess.run(['ffmpeg','-v','error','-y','-i',str(movie),'-map',f'0:a:{index}','-c:a','copy','-metadata:s:a:0','language='+('eng' if lang=='en' else 'zho'),'-movflags','+faststart',str(temp)],check=True);os.replace(temp,target)
            info=probe(target);assert len(info['streams'])==1 and info['streams'][0]['tags']['language']==('eng' if lang=='en' else 'zho') and abs(float(info['format']['duration'])-seconds)<.1 and audio_hash(target,0)==expected
            audio[kind+'/'+lang]={'file':str(target.relative_to(dest)),'encodedAudioMatchesMovie':True,'seconds':float(info['format']['duration'])}
    notes_path.write_text(notes)
    records={str(p.relative_to(dest)):{'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(dest.rglob('*')) if p.is_file() and p.name not in ['SHA256SUMS','PACKAGE.json']}
    record={'destination':str(dest),'longMovieSha256':full['sha256'],'shortMovieSha256':short['sha256'],'shortSeconds':short['seconds'],'defaultLanguage':'en','audio':audio,'youtubeVariants':list(meta),'files':records}
    (dest/'PACKAGE.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n');(DOC/'desktop-package.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
    sums=''.join(sha(p)+'  '+str(p.relative_to(dest))+'\n' for p in sorted(dest.rglob('*')) if p.is_file() and p.name!='SHA256SUMS');(dest/'SHA256SUMS').write_text(sums)
    for row in sums.splitlines():digest,name=row.split('  ',1);assert sha(dest/name)==digest
    print('Updated and verified desktop package:',dest)


if __name__=='__main__':main()
