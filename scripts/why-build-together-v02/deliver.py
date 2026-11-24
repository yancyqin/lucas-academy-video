"""Assemble the finished 1080p movie with default Chinese soft captions."""
import hashlib,html,json,re,shutil,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'out/why-build-together-v02'
DELIVERY=OUT/'delivery';DELIVERY.mkdir(exist_ok=True)

def main():
    plan=json.loads((OUT/'timeline.json').read_text());master=Path(plan['embedded_movie'])
    output=DELIVERY/'why-build-together.zh-v02.mp4'
    lengths=[plan['intro_frames'],plan['insert']['frames']]
    # AAC decoding can expose encoder padding beyond a segment's declared end.
    # Trim each input to its exact frame/sample count before concatenating.
    graph=''.join(f'[{source}:v]fps=30,trim=end_frame={frames},setpts=N/(30*TB),setsar=1,format=yuv420p[v{i}];'
                  for i,(source,frames) in enumerate(zip([0,2],lengths)))
    graph+=''.join(f'[{source}:a]aresample=48000,atrim=end_sample={frames*1600},asetpts=N/SR/TB,aformat=channel_layouts=stereo[a{i}];'
                   for i,(source,frames) in enumerate(zip([1,2],lengths)))
    graph+='[v0][a0][v1][a1]concat=n=2:v=1:a=1[vc][a];[vc]setpts=N/(30*TB)[v]'
    chapters=json.loads((OUT/'chapters.json').read_text())
    escape=lambda s:re.sub(r'([\\=;#])',r'\\\1',s).replace('\n',' ')
    metadata=';FFMETADATA1\n'
    for i,row in enumerate(chapters):
        end=chapters[i+1]['seconds'] if i+1<len(chapters) else plan['seconds']
        metadata+=f"[CHAPTER]\nTIMEBASE=1/1000\nSTART={round(row['seconds']*1000)}\nEND={round(end*1000)}\ntitle={escape(row['title'])}\n"
    (OUT/'chapters.ffmetadata').write_text(metadata)
    chapter_args=[]
    for i,row in enumerate(chapters):
        chapter_args.extend([f'-metadata:c:{i}',f"title={row['title']}"])
    with (OUT/'final-encode.log').open('w') as log:
        subprocess.run(['ffmpeg','-hide_banner','-y','-i',str(OUT/'intro-picture.mp4'),'-i',str(OUT/'intro.wav'),'-i',str(master),
          '-i',str(OUT/'why-build-together.zh-CN.srt'),
          '-f','ffmetadata','-i',str(OUT/'chapters.ffmetadata'),
          '-filter_complex',graph,'-map','[v]','-map','[a]','-map','3:0','-map_metadata','-1','-map_chapters','4',
          '-c:v','libx264','-preset','fast','-crf','17','-pix_fmt','yuv420p','-r','30','-fps_mode','cfr',
          '-c:a','aac','-b:a','256k','-c:s','mov_text','-metadata:s:a:0','language=zho','-metadata:s:s:0','language=zho',
          '-metadata:s:s:0','title=简体中文','-disposition:s:0','default','-metadata','title=孩子做项目，我们真正看重什么？',
          '-metadata','artist=Lucas Academy Team',*chapter_args,'-movflags','+faststart',str(output)],check=True,stdout=log,stderr=log)
    for name in ['why-build-together.zh-CN.srt','why-build-together.zh-CN.vtt','youtube-description.zh.txt','youtube-tags.txt','label-check.json']:
        shutil.copy2(OUT/name,DELIVERY/name)
    vtt=(OUT/'why-build-together.zh-CN.vtt').read_text()
    player='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>孩子做项目，我们真正看重什么？</title><style>body{margin:0;background:#10191d;color:#f8f6ef;font:18px/1.7 -apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif}main{max-width:1200px;margin:40px auto;padding:0 24px}h1{font-size:28px;font-weight:500}video{display:block;width:100%;background:#000;border-radius:6px}p{color:#afc5c5}a{color:#9ed3c4;margin-right:24px}::cue{font-size:25px;background:rgba(0,0,0,.76);color:white}</style><main><h1>孩子做项目，我们真正看重什么？</h1><video controls preload="metadata" src="why-build-together.zh-v02.mp4"><track id="zh" kind="subtitles" label="简体中文" srclang="zh" default></video><p>中文旁白 · 完整项目展示 · 中文字幕</p><a href="why-build-together.zh-v02.mp4" download>视频</a><a href="why-build-together.zh-CN.srt" download>中文字幕</a></main><script>const vtt=VTT_JSON;const tr=document.getElementById('zh');tr.src=URL.createObjectURL(new Blob([vtt],{type:'text/vtt'}));tr.addEventListener('load',()=>{tr.track.mode='showing'});</script></html>'''
    (DELIVERY/'打开预览.html').write_text(player.replace('VTT_JSON',json.dumps(vtt,ensure_ascii=False)))
    facts=dict(title=plan['title'],expected_seconds=plan['seconds'],embedded_start=plan['insert']['start_frame']/30,
               embedded_seconds=283.8,ends_with_project_movie=True,width=1920,height=1080,fps=30,subtitles='default Chinese mov_text plus SRT/VTT; not burned',
               movie_sha256=hashlib.sha256(output.read_bytes()).hexdigest(),source_movie_sha256=hashlib.sha256(master.read_bytes()).hexdigest())
    (DELIVERY/'delivery.json').write_text(json.dumps(facts,ensure_ascii=False,indent=2)+'\n')
    print('Assembled',output,flush=True)

if __name__=='__main__':main()
