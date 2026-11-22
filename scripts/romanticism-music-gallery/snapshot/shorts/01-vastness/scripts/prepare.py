"""Prepare one vertical museum-walk sample using the current IS salon."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import json, hashlib, shutil, math

ROOT=Path(__file__).resolve().parents[1]
PROJECT=ROOT.parents[1]
UI=PROJECT.parent.parent/'inception-space-ui'
W,H,FPS,DURATION=1080,1920,24,58
font_file='/System/Library/Fonts/STHeiti Medium.ttc'
catalog=json.loads((UI/'content/inception/artworks/romanticism-salon-v1.json').read_text())
selected=[]
for id in ['wanderer','chalk-cliffs']:
    work=next(a for a in catalog['works'] if a['id']==id)
    source=PROJECT/'art'/(id+'.jpg')
    assert hashlib.sha256(source.read_bytes()).hexdigest()==work['original_sha256']
    selected.append({**work,'file':str(source)})
previous=json.loads((PROJECT/'v4/sources/credits.json').read_text())
music=next(m for m in previous['music'] if 'No. 15' in m['title'])
music_file=PROJECT/'music/prelude-28-15.m4a'
assert hashlib.sha256(music_file.read_bytes()).hexdigest()==music['sha256']

cues=[
    dict(id='theme',start=.65,end=4.3,en=['Facing the Vastness'],zh='面对辽阔',y=356,size=49,center=True),
    dict(id='music',start=4.7,end=8.8,en=['Chopin · Raindrop Prelude'],zh='肖邦 ·《雨滴》前奏曲',y=230,size=36,center=False),
    dict(id='wanderer',start=12.8,end=17.5,en=['Wanderer above the Sea of Fog','Caspar David Friedrich'],zh='雾海上的旅人\n卡斯帕·大卫·弗里德里希',y=150,size=38,center=False),
    dict(id='chalk-cliffs',start=33.5,end=38.7,en=['Chalk Cliffs on Rügen','Caspar David Friedrich'],zh='吕根岛白垩岩\n卡斯帕·大卫·弗里德里希',y=150,size=38,center=False),
]
for cue in cues:
    im=Image.new('RGBA',(W,H));draw=ImageDraw.Draw(im)
    if cue['id'] in ['wanderer','chalk-cliffs','music']:
        for row in range(70,340):
            alpha=max(0,round(135*math.sin(math.pi*(row-70)/270)))
            draw.line((0,row,W,row),fill=(9,14,22,alpha))
    size=cue['size']
    while True:
        font=ImageFont.truetype(font_file,size)
        widths=[draw.textlength(line,font=font) for line in cue['en']]
        if max(widths)<W-152:break
        size-=1
    for i,line in enumerate(cue['en']):
        x=(W-draw.textlength(line,font=font))/2 if cue['center'] else 72
        draw.text((x,cue['y']+i*56),line,font=font,fill='#f5ebd6',stroke_width=2,stroke_fill='#101820')
    im.save(ROOT/'labels'/(cue['id']+'.png'))
    cue['font_px']=size

def stamp(value):
    ms=round(value*1000);h,ms=divmod(ms,3600000);m,ms=divmod(ms,60000);s,ms=divmod(ms,1000)
    return f'{h:02}:{m:02}:{s:02},{ms:03}'
srt='\n\n'.join(f'{i}\n{stamp(c["start"])} --> {stamp(c["end"])}\n{c["zh"]}' for i,c in enumerate(cues,1))+'\n'
(ROOT/'subtitles/面对辽阔-竖屏示范.zh-Hans.srt').write_text(srt,encoding='utf-8-sig')
assets=['content/inception/artworks/romanticism-salon-v1.json',
        'content/inception/artworks/romanticism-sculptures-v1.json',
        'content/inception/artworks/romanticism-selected-scans.json',
        'src/inception/world/rooms/romanticismLayout.js',
        'src/inception/world/render/threeRomanticismSalon.ts',
        'src/inception/world/render/romanticismSurfaces.ts']
snapshot={name:hashlib.sha256((UI/name).read_bytes()).hexdigest() for name in assets}
plan=dict(title='面对辽阔',title_en='Facing the Vastness',width=W,height=H,fps=FPS,duration=DURATION,
          frames=FPS*DURATION,artworks=selected,labels=cues,shared_room='romanticism-salon',
          source_repository=str(UI),source_snapshot=snapshot,
          picture_language='en',separate_subtitles=['zh-Hans'],narration=False,
          music={**music,'file':str(music_file),'excerpt_start':0,'excerpt_seconds':DURATION,
                 'gain_db':-6.57,'fade_in_seconds':.2,'fade_out_seconds':2},
          camera_policy='A continuous native portrait camera walk from the current shared salon to two adjacent paintings; whole painting, optical zoom to a detail, pull back, walk to the second work.')
(ROOT/'edit-plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2))
(ROOT/'sources/layout-snapshot.json').write_text(json.dumps(snapshot,indent=2))
print('Prepared one 58-second portrait sample, two clothed Friedrich paintings, English labels and Chinese-only SRT.')
