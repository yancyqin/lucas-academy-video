"""Rebuild the complete bilingual delivery from the reviewed local conversions."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

P=Path(__file__).resolve().parent;V8=P.parent/'v8';sys.path.insert(0,str(V8))
import revise_audio as audio
audio.P=P;audio.DELIVERY=P/'delivery'

def build():
    overrides=json.loads((P/'voice-overrides.json').read_text())
    assert len([i for i in overrides['items'] if i['language']=='en'])==73
    plan=audio.prepare(V8/'full-plan.json',P/'voice-overrides.json')
    plan.update(revision='v9-full-English-voice-review',english_voice_units_reviewed=73,
        chinese_retakes=['n003-01'],local_cloud_requests=0)
    audio.save(P/'full-plan.json',plan);audio.mux()
    out=audio.DELIVERY
    subprocess.run([audio.FF,'-v','error','-y','-i',str(out/'01-English-full.mp4'),'-t','105',
        '-map','0:v:0','-map','0:a:0','-c','copy','-movflags','+faststart',str(out/'Opening-English-105s.mp4')],check=True)
    item=next(i for i in plan['voice_fragments'] if i['language']=='zh' and i['id']=='n003-01')
    shutil.copy2(item['file'],out/'Chinese-Mallorca-retake.wav')
    return plan

def install(plan):
    audio.install(plan)
    page=audio.DESKTOP/'影片预览.html';text=page.read_text()
    message='<p>整条英文旁白已逐段处理换声起音；中文马略卡岛一句以自然节奏本地重录，保留 Fangfang 音色与逐字年份读法。<a href="Opening-English-105s.mp4">英文前 1 分 45 秒</a> · <a href="Chinese-Mallorca-retake.wav">中文重录一句</a>。快速检查：<button data-seek="40.7">00:41</button> <button data-seek="59.1">00:59</button> <button data-seek="83.5">01:24</button></p>'
    text=text.replace('<div class="controls">',message+'<div class="controls">',1)
    # Fresh local media URLs prevent an open preview from replaying cached v8 audio.
    versioned={'01-English-full.mp4':'01-English-full-v9.mp4',
        '02-Chinese-aligned-audio.wav':'02-Chinese-aligned-audio-v9.wav',
        'Chinese-preview.mp3':'Chinese-preview-v9.mp3',
        '03-English.srt':'03-English-v9.srt','04-Chinese.srt':'04-Chinese-v9.srt'}
    for original,new in versioned.items():
        target=audio.DESKTOP/new
        if target.exists():target.unlink()
        os.link(audio.DESKTOP/original,target)
        text=text.replace('src="'+original+'"','src="'+new+'"').replace('href="'+original+'"','href="'+new+'"')
    page.write_text(text,encoding='utf-8')
    (audio.DESKTOP/'影片预览-音频修订v9.html').write_text(text,encoding='utf-8')

if __name__=='__main__':
    if '--install-only' in sys.argv:install(json.loads((P/'full-plan.json').read_text()))
    else:
        plan=build()
        if '--install' in sys.argv:install(plan)
