"""Validate a Lucas Academy upload package and emit a local manifest; no network."""
from pathlib import Path
import argparse,hashlib,json,re,shutil,subprocess

BLOCKS=['标题 / Title','简介 / Description','标签 / Tags','上传设置 / Upload settings']

def digest(file):
    value=hashlib.sha256()
    with file.open('rb') as stream:
        for chunk in iter(lambda:stream.read(8*1024*1024),b''):value.update(chunk)
    return value.hexdigest()

def inside(folder,relative):
    file=(folder/relative).resolve()
    if not file.is_relative_to(folder) or not file.is_file():raise ValueError('Missing or out-of-package file: '+relative)
    return file

def metadata(file):
    text=file.read_text(encoding='utf-8-sig')
    values={}
    for i,name in enumerate(BLOCKS):
        marker='【'+name+'】'
        if text.count(marker)!=1:raise ValueError('Missing/duplicate metadata block '+name)
        value=text.split(marker,1)[1]
        if i<len(BLOCKS)-1:value=value.split('【'+BLOCKS[i+1]+'】',1)[0]
        values[name]=value.strip()
    title,description,tags=[values[k]for k in BLOCKS[:3]]
    if not title or len(title)>100 or not description or len(description)>5000:raise ValueError('Invalid title/description length')
    if not tags or len(tags)>500:raise ValueError('Invalid tags length')
    return {'title':title,'description':description,'tags':tags.split(),'settings':values[BLOCKS[3]]}

def srt(file,duration):
    text=file.read_text(encoding='utf-8-sig').replace('\r\n','\n').strip()
    stamp=lambda h,m,s,ms:int(h)*3600+int(m)*60+int(s)+int(ms)/1000
    result=[];prior_start=-1
    for block in re.split(r'\n\s*\n',text):
        lines=block.splitlines()
        if len(lines)<3 or not lines[0].isdigit():raise ValueError('Invalid SRT block')
        match=re.fullmatch(r'(\d{2,}):(\d{2}):(\d{2}),(\d{3}) --> (\d{2,}):(\d{2}):(\d{2}),(\d{3})',lines[1])
        if not match:raise ValueError('Invalid SRT timing')
        start=stamp(*match.groups()[:4]);end=stamp(*match.groups()[4:])
        if not 0<=start<end<=duration+.05 or start<prior_start:raise ValueError('SRT cue outside video or out of order')
        prior_start=start;result.append({'start':start,'end':end,'text':'\n'.join(lines[2:])})
    return result

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--ffprobe',default=shutil.which('ffprobe')or'/opt/homebrew/bin/ffprobe')
    args=parser.parse_args();folder=args.package.resolve()
    program=json.loads(inside(folder,'资料/播放与字幕数据.json').read_text())
    videos=[]
    for item in program:
        file=inside(folder,item['src']);subtitle=inside(folder,item['srt'])
        probe=json.loads(subprocess.check_output([args.ffprobe,'-v','error','-show_format','-show_streams','-of','json',str(file)]))
        duration=float(probe['format']['duration'])
        video=next(s for s in probe['streams'] if s['codec_type']=='video')
        if not any(s['codec_type']=='audio'for s in probe['streams']):raise ValueError('Missing audio stream: '+str(file))
        english=metadata(inside(folder,item['englishMetadata']));chinese=metadata(inside(folder,item['chineseMetadata']))
        cues=srt(subtitle,duration)
        expected=item['cues']
        if len(cues)!=len(expected) or any(abs(a['start']-b['start'])>.001 or abs(a['end']-b['end'])>.001 or a['text']!=b['text'] for a,b in zip(cues,expected)):
            raise ValueError('SRT does not match preview data: '+str(subtitle))
        videos.append({'number':item['number'],'file':str(file),'sha256':digest(file),'bytes':file.stat().st_size,
            'duration':duration,'width':video['width'],'height':video['height'],'metadata_en':english,'metadata_zh':chinese,
            'subtitles':[{'file':str(subtitle),'language':'zh-Hans','sha256':digest(subtitle),'cues':cues}],
            'requested_visibility':'private','upload_status':'not uploaded'})
    if len({v['file']for v in videos})!=len(videos):raise ValueError('Duplicate source files')
    result={'package':str(folder),'requested_visibility':'private','publish_authorized':False,'videos':videos}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(f'Validated {len(videos)} local videos and their SRTs. No files uploaded. Manifest: {args.output}')

if __name__=='__main__':main()
