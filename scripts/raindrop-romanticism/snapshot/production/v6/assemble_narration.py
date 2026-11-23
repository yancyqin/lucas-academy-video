"""Assemble verified target-voice fragments as dry, chapter-indexed previews."""
import argparse
import hashlib
import html
import json
from pathlib import Path
import re
import shutil
import subprocess
import wave

import numpy as np

P=Path(__file__).resolve().parent
DEST=Path('@USER_HOME@/Desktop/压力焦虑肖邦浪漫-新版旁白预览')
FF='/opt/homebrew/bin/ffmpeg'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_audio(path):
    with wave.open(str(path),'rb') as reader:
        assert reader.getnchannels()==1 and reader.getsampwidth()==2
        rate=reader.getframerate()
        samples=np.frombuffer(reader.readframes(reader.getnframes()),dtype='<i2').copy()
    assert len(samples)>0 and np.max(np.abs(samples.astype(np.int32)))>30
    return samples,rate


def clock(seconds):
    n=int(seconds)
    return f'{n//60:02d}:{n%60:02d}'


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--ready-only',action='store_true')
    args=parser.parse_args()
    script=json.loads((P/'narration-bilingual.json').read_text())
    plan=json.loads((P/'synthesis-plan.json').read_text())
    assert script['source_sha256']==plan['source_sha256']
    assert digest(P/'压力焦虑肖邦浪漫-已确认中文文案.docx')==plan['source_sha256']
    DEST.mkdir(exist_ok=True)
    deliveries=[]
    for lang,profile,stem in [('zh','fangfang/zh','01-中文-Fangfang-新版旁白'),('en','louise/en','02-英文-Louise-新版旁白')]:
        items=[x for x in plan['requests'] if x['language']==lang]
        if args.ready_only and any(not (P/'voices'/lang/(x['id']+'-'+x['text_sha256'][:12])/'receipt.json').is_file() for x in items):
            continue
        timeline=[];chunks=[];cursor=0;previous=None;rate=None
        for item in items:
            folder=P/'voices'/lang/(item['id']+'-'+item['text_sha256'][:12])
            output=folder/'voice.wav';receipt=json.loads((folder/'receipt.json').read_text())
            assert receipt['state']=='success' and receipt['target_profile']==profile
            assert receipt['text_sha256']==item['text_sha256'] and digest(output)==receipt['sha256']
            samples,current_rate=read_audio(output)
            if rate is None:rate=current_rate
            assert current_rate==rate and abs(len(samples)/rate-receipt['source_seconds'])<.3
            if previous is None:pause=.25
            elif previous['paragraph_id']==item['paragraph_id']:pause=0
            elif previous['section'].strip()==item['section'].strip():pause=.35
            else:pause=.75
            gap=np.zeros(round(pause*rate),dtype='<i2');chunks.append(gap);cursor+=len(gap)
            timeline.append(dict(**item,start=cursor/rate,end=(cursor+len(samples))/rate,file=str(output)))
            chunks.append(samples);cursor+=len(samples);previous=item
        chunks.append(np.zeros(round(.8*rate),dtype='<i2'))
        raw=P/f'assembled-{lang}-unmastered.wav'
        with wave.open(str(raw),'wb') as writer:
            writer.setparams((1,2,rate,0,'NONE','not compressed'))
            writer.writeframes(np.concatenate(chunks).tobytes())
        measurement=subprocess.run([FF,'-v','info','-i',str(raw),'-af',
             'loudnorm=I=-20:TP=-1.5:LRA=11:print_format=json','-f','null','-'],capture_output=True,text=True,check=True)
        stats=json.loads(re.findall(r'\{\s*"input_i".*?\}',measurement.stderr,re.S)[0])
        gain=min(-20-float(stats['input_i']),-1.5-float(stats['input_tp']))
        wav=DEST/(stem+'.wav');mp3=DEST/(stem+'.mp3')
        subprocess.run([FF,'-v','error','-y','-i',str(raw),'-af',f'volume={gain:.5f}dB',
                        '-ar','48000','-ac','1','-c:a','pcm_s24le',str(wav)],check=True)
        subprocess.run([FF,'-v','error','-y','-i',str(wav),'-c:a','libmp3lame','-q:a','2',str(mp3)],check=True)
        subprocess.run([FF,'-v','error','-i',str(mp3),'-f','null','-'],check=True)
        paragraphs=[]
        for row in script['rows']:
            if not row['spoken']:continue
            selected=[x for x in timeline if x['paragraph_id']==row['id']]
            compact=lambda t:re.sub(r'\s+','',t)
            assert compact(''.join(x['text'] for x in selected))==compact(row[lang])
            paragraphs.append(dict(id=row['id'],section=row['section'].strip(),start=selected[0]['start'],
                                   end=selected[-1]['end'],zh=row['zh'],en=row['en']))
        assert len(paragraphs)==58
        track=dict(language=lang,profile=profile,model='MiniMax Speech 2.8 HD → local CosyVoice3 timbre conversion',
                   wav=str(wav),mp3=str(mp3),wav_sha256=digest(wav),mp3_sha256=digest(mp3),
                   seconds=(cursor+round(.8*rate))/rate,gain_db=round(gain,4),
                   loudness_before=stats,paragraphs=paragraphs,fragments=timeline)
        deliveries.append(track)
        print('Assembled',lang,clock(track['seconds']),'paragraphs',len(paragraphs),flush=True)
    assert deliveries,'No complete language is ready.'
    for name in ['压力焦虑肖邦浪漫-中文定稿.docx','压力焦虑肖邦浪漫-英文配音稿-新版.docx']:
        shutil.copy2(Path('@USER_HOME@/Desktop')/name,DEST/name)
    manifest=dict(source_sha256=plan['source_sha256'],dry_narration=True,music_cues_included_as_silence=False,
                  complete_languages=[x['language'] for x in deliveries],
                  cues=[r for r in script['rows'] if not r['spoken']],tracks=deliveries)
    (P/'narration-delivery.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
    (DEST/'旁白时间索引.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
    panels=[]
    for track in deliveries:
        lang=track['language'];title='中文 · Fangfang' if lang=='zh' else 'English · Louise'
        chapters=[];last=None
        for row in track['paragraphs']:
            if row['section']!=last:
                chapters.append(f'<button data-seek="{row["start"]:.3f}"><time>{clock(row["start"])}</time>{html.escape(row["section"])}</button>')
                last=row['section']
        paragraphs=''.join(f'<button class="paragraph" data-seek="{r["start"]:.3f}"><time>{clock(r["start"])}</time><span>{html.escape(r[lang])}</span></button>' for r in track['paragraphs'])
        panels.append(f'''<section data-language="{lang}"><h2>{title}</h2><p class="meta">{clock(track['seconds'])} · 58 段 · MiniMax 演绎＋本地换声</p>
<audio controls preload="metadata" src="{html.escape(Path(track['mp3']).name)}"></audio>
<p class="links"><a href="{html.escape(Path(track['wav']).name)}" download>下载 WAV</a><a href="{html.escape(Path(track['mp3']).name)}" download>下载 MP3</a></p>
<h3>按章节听</h3><div class="chapters">{''.join(chapters)}</div><details><summary>逐段文案与跳转</summary>{paragraphs}</details></section>''')
    page='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>新版旁白预览</title>
<style>*{box-sizing:border-box}body{margin:0;background:#f5f1e9;color:#28221d;font:16px/1.8 system-ui,sans-serif}main{max-width:980px;margin:auto;padding:44px 24px 70px}h1{font-size:32px;line-height:1.3;margin:0 0 18px}h2{font-size:25px;margin:26px 0 4px}h3{font-size:18px;margin-top:28px}p{margin:8px 0}.intro,.meta,time{color:#75644e}.meta{font-size:14px}audio{width:100%;display:block;margin:20px 0}a{color:#795124}.links{display:flex;gap:24px}nav{display:flex;gap:12px;margin:26px 0}button{font:inherit;cursor:pointer}nav button{padding:6px 22px;border:1px solid #a58a68;background:transparent;border-radius:24px}nav button[aria-pressed=true]{color:white;background:#795124}.chapters{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:9px}.chapters button{display:flex;align-items:baseline;gap:12px;text-align:left;background:#fff9f1;border:1px solid #dfd1bf;border-radius:8px;padding:10px 14px}time{font-variant-numeric:tabular-nums;font-size:13px;flex-shrink:0}details{margin-top:28px}summary{cursor:pointer;color:#795124}.paragraph{display:flex;width:100%;gap:18px;text-align:left;border:0;border-bottom:1px solid #dfd1bf;background:transparent;padding:15px 0;color:inherit}footer{margin-top:36px;border-top:1px solid #dfd1bf;padding-top:20px;font-size:14px}button:focus-visible,a:focus-visible,summary:focus-visible{outline:3px solid #9f772d;outline-offset:4px}[hidden]{display:none!important}@media(max-width:620px){.chapters{grid-template-columns:1fr}h1{font-size:27px}main{padding:30px 18px}}</style>
<main><h1>压力？焦虑？肖邦？浪漫？</h1><p class="intro">新版旁白干声预览，采用已确认文案。此页不含背景音乐，文案中的纯音乐段暂不插入停顿；正式剪辑将按音乐乐句和新配音重新安排。点击章节或文案可跳转。</p>
<nav aria-label="旁白语言"><button data-filter="zh" aria-pressed="true">中文 · Fangfang</button><button data-filter="en" aria-pressed="false">English · Louise</button></nav>
'''+''.join(panels)+'''
<footer><p><a href="压力焦虑肖邦浪漫-中文定稿.docx">中文定稿 Word</a> · <a href="压力焦虑肖邦浪漫-英文配音稿-新版.docx">英文配音稿 Word</a></p><p>整体固定增益调整音量，保留演绎速度与段内停顿。</p></footer>
<script>const audios=[...document.querySelectorAll('audio')];audios.forEach(a=>a.addEventListener('play',()=>audios.forEach(b=>{if(b!==a)b.pause()})));function choose(lang){audios.forEach(a=>a.pause());document.querySelectorAll('section[data-language]').forEach(s=>s.hidden=s.dataset.language!==lang);document.querySelectorAll('[data-filter]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.filter===lang)))}document.querySelectorAll('[data-filter]').forEach(b=>b.addEventListener('click',()=>choose(b.dataset.filter)));document.querySelectorAll('[data-seek]').forEach(b=>b.addEventListener('click',()=>{const a=b.closest('section').querySelector('audio');a.currentTime=Number(b.dataset.seek);a.play().catch(()=>{})}));choose('zh');</script></main></html>'''
    for lang in ['zh','en']:
        if not any(x['language']==lang for x in deliveries):
            page=re.sub(r'<button data-filter="'+lang+r'"[^>]*>.*?</button>','',page)
    page=page.replace("choose('zh');",f"choose('{deliveries[0]['language']}');")
    (DEST/'新版旁白试听.html').write_text(page,encoding='utf-8')
    print('Preview page:',DEST/'新版旁白试听.html',flush=True)


if __name__=='__main__':main()
