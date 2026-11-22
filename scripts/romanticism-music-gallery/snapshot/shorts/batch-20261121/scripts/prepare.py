"""Four more two-painting portrait films in the approved museum-walk style."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,hashlib,math,re,sys

ROOT=Path(__file__).resolve().parents[1]
PROJECT=ROOT.parents[1]
UI=PROJECT.parent.parent/'inception-space-ui'
catalog=json.loads((UI/'content/inception/artworks/romanticism-salon-v1.json').read_text())
original=json.loads((PROJECT/'sources/selected-artworks.json').read_text())
old_plan=json.loads((PROJECT/'v4/edit-plan.json').read_text())
credits=json.loads((PROJECT/'v4/sources/credits.json').read_text())
font_file='/System/Library/Fonts/STHeiti Medium.ttc'
ids={a['id']:a for a in catalog['works']}
prior={a['id']:a for a in original}
music_labels={
 'nocturne':('Chopin · Nocturne Op. 9 No. 2','肖邦 · 夜曲 Op. 9 No. 2'),
 'distance':('Chopin · Nocturne in C-sharp minor','肖邦 · 升 C 小调夜曲'),
 'liberty':('Beethoven · Egmont Overture','贝多芬 ·《埃格蒙特》序曲'),
 'life':('Beethoven · Pathétique, II','贝多芬 ·《悲怆》第二乐章'),
}
configs=[
 dict(id='02-silence',number=2,title='寂静与时间',title_en='Silence and Time',category='nature',
      works=['monk-sea','abbey-oakwood'],music='nocturne',excerpt=0,
      names=['Monk by the Sea','Abbey in the Oakwood'],chinese=['海边的修道士','橡树林中的修道院'],
      detail=[dict(u=.355,v=.60,fov=15),dict(u=.50,v=.57,fov=16.5)],
      start=dict(eye=[-20.5,4.05,-9],target=[-27.375,8,-23],fov=62),
      first_at=12,first_label=12.8,first_detail=17.5,first_close=23.5,pull_at=24.5,walk_at=27,
      second_at=35,second_label=35.5,second_detail=40.5,second_close=47.5,
      closing=dict(distance=13.8,fov=58,y_offset=.2),
      relation_zh='同一位画家笔下的海岸与废墟：人物、荒树和建筑共同带出寂静与时间。',
      relation_en='Friedrich pairs the quiet of an open sea with bare trees and a ruined abbey: two landscapes through which to consider silence and time.'),
 dict(id='03-mountains',number=3,title='山峦与光',title_en='Mountains and Light',category='nature',
      works=['heart-andes','sierra'],music='distance',excerpt=14,
      names=['The Heart of the Andes','Among the Sierra Nevada'],chinese=['安第斯之心','内华达山脉之中'],
      detail=[dict(u=.61,v=.73,fov=8),dict(u=.46,v=.67,fov=10)],
      start=dict(eye=[-22,4.05,12],target=[-27.375,11,-1],fov=62),
      first_at=12,first_label=12.8,first_detail=17.5,first_close=23.5,pull_at=24.5,walk_at=27,
      second_at=34,second_label=34.5,second_detail=39.3,second_close=46.5,
      closing=dict(distance=12.6,fov=56),
      relation_zh='先看丘奇与比尔施塔特的辽阔山景，再走近两幅画中的瀑布：从群山的尺度，看到水落向河流与湖面的细节。',
      relation_en='First take in the expansive mountain landscapes of Church and Bierstadt, then move closer to their waterfalls: water descending into a river and a lake.'),
 dict(id='04-war',number=4,title='战争的两张面孔',title_en='Two Faces of War',category='human',
      works=['wounded','charging'],music='liberty',excerpt=148,
      names=['The Wounded Cuirassier','The Charging Chasseur'],chinese=['负伤的胸甲骑兵','冲锋的猎骑兵'],
      detail=[dict(u=.54,v=.50,fov=25.5),dict(u=.51,v=.50,fov=27)],
      start=dict(eye=[20,4.05,9],target=[27.375,6,2],fov=56),
      first_at=9,first_label=9.6,first_detail=14.2,first_close=20,pull_at=21,walk_at=23,
      second_at=34,second_label=34.5,second_detail=39.3,second_close=46.5,
      closing=dict(distance=8.0,fov=56,y_offset=.25,target_y=3.0),
      relation_zh='籍里柯的两位骑兵，一位负伤退却，一位骑马转身；把疲惫与勇武放在一起观看。',
      relation_en='Two cavalrymen by Géricault: a wounded figure and a mounted officer. The pair brings weariness and martial energy into the same walk.'),
 dict(id='05-life',number=5,title='青年与暮年',title_en='Youth and Old Age',category='human',
      works=['life-youth','life-old'],music='liberty',excerpt=40,
      names=['The Voyage of Life: Youth','The Voyage of Life: Old Age'],chinese=['生命之旅：青年','生命之旅：老年'],
      detail=[dict(u=.70,v=.65,fov=15.5),dict(u=.65,v=.70,fov=12.5)],
      start=dict(eye=[-19.5,4.05,-26],target=[-16,12,-42.375],fov=62),
      first_at=12,first_label=12.8,first_detail=17.5,first_close=23.5,pull_at=24.5,walk_at=27,
      second_at=33,second_label=33.5,second_detail=38.7,second_close=46,
      closing=dict(distance=20.5,fov=60,pair=True),
      relation_zh='科尔《生命之旅》中的青年与老年，两段河流旅程把向往与生命的有限性相连。',
      relation_en='Youth and Old Age from Cole’s Voyage of Life: two river journeys connect expectation with the limits of a human life.'),
 dict(id='06-hope-freedom',number=6,title='希望与自由',title_en='Hope and Freedom',category='human',
      works=['raft-medusa','liberty'],music='liberty',excerpt=482,original_paintings_only=True,
      names=['The Raft of the Medusa','Liberty Leading the People'],chinese=['梅杜萨之筏','自由引导人民'],
      detail=[dict(u=.68,v=.43,fov=15.5),dict(u=.54,v=.50,fov=21)],
      start=dict(eye=[20,4.05,25],target=[27.375,6,17],fov=56),
      first_at=9,first_label=9.6,first_detail=14.2,first_close=20,pull_at=21,walk_at=23,
      second_at=34,second_label=34.5,second_detail=39.3,second_close=46.5,
      closing=dict(distance=12.6,fov=56),
      relation_zh='籍里柯的木筏与德拉克洛瓦的街垒，从向远处挥动布巾的求救者，走向举旗前行的人群。两幅原画连接希望、共同处境与自由。',
      relation_en='From Géricault’s raft to Delacroix’s barricade: a raised cloth seeks rescue; a raised flag gathers a crowd. Two original paintings connect hope, collective struggle and freedom.'),
]
snapshot_files=['content/inception/artworks/romanticism-salon-v1.json',
 'content/inception/artworks/romanticism-sculptures-v1.json','content/inception/artworks/romanticism-selected-scans.json',
 'src/inception/world/rooms/romanticismLayout.js','src/inception/world/rooms/romanticismExhibits.ts',
 'src/inception/world/render/threeRomanticismSalon.ts','src/inception/world/render/romanticismSurfaces.ts',
 'src/inception/world/model/museum.js','src/inception/world/render/threeMuseum.ts']
snapshot={name:hashlib.sha256((UI/name).read_bytes()).hexdigest() for name in snapshot_files}

def stamp(seconds):
    value=round(seconds*1000);h,value=divmod(value,3600000);m,value=divmod(value,60000);s,ms=divmod(value,1000)
    return f'{h:02}:{m:02}:{s:02},{ms:03}'

filters=set(sys.argv[1:])
previous_batch=json.loads((ROOT/'batch.json').read_text()) if (ROOT/'batch.json').exists() else {'jobs':[]}
previous_jobs={j['id']:j for j in previous_batch['jobs']}
jobs=[]
for config in configs:
    if filters and config['id'] not in filters:
        if config['id'] in previous_jobs:jobs.append(previous_jobs[config['id']])
        continue
    folder=ROOT/'jobs'/config['id']
    for name in ['labels','footage','parts','exports','subtitles','checks','sources']:(folder/name).mkdir(parents=True,exist_ok=True)
    works=[]
    for id in config['works']:
        art={**ids[id]};art['file']=str(PROJECT/'art'/(id+'.jpg'))
        assert prior[id].get('nudity') is False or (config.get('original_paintings_only') and id in ['raft-medusa','liberty']),id
        assert hashlib.sha256(Path(art['file']).read_bytes()).hexdigest()==art['original_sha256'],id
        art['nudity']=prior[id].get('nudity');works.append(art)
    track=next(t for t in old_plan['tracks'] if t['id']==config['music'])
    source_credit=next(c for c in credits['music'] if c['sha256']==track['sha256'])
    music={**source_credit,'file':track['file'],'gain_db':track['gain_db'],'excerpt_start':config['excerpt'],'excerpt_seconds':58}
    assert config['excerpt']+58<=track['audio_duration']
    assert hashlib.sha256(Path(music['file']).read_bytes()).hexdigest()==music['sha256']
    cue_list=[
      dict(id='theme',start=.65,end=4.3,en=[config['title_en']],zh=config['title'],y=356,size=49,center=True),
      dict(id='music',start=4.7,end=8.4,en=[music_labels[config['music']][0]],zh=music_labels[config['music']][1],y=230,size=36),
    ]
    for index,art in enumerate(works):
        start=config['first_label'] if index==0 else config['second_label']
        end=config['first_detail']-.15 if index==0 else config['second_detail']-.15
        cue_list.append(dict(id=art['id'],start=start,end=end,en=[config['names'][index],art['artist_en']],
                             zh=config['chinese'][index]+'\n'+art['artist_zh'],y=150,size=38))
    for cue in cue_list:
        image=Image.new('RGBA',(1080,1920));draw=ImageDraw.Draw(image)
        if cue['id']!='theme':
            for y in range(70,340):draw.line((0,y,1080,y),fill=(9,14,22,max(0,round(135*math.sin(math.pi*(y-70)/270)))))
        size=cue['size']
        while True:
            font=ImageFont.truetype(font_file,size)
            if max(draw.textlength(text,font=font) for text in cue['en'])<928:break
            size-=1
        cue['font_px']=size
        for i,text in enumerate(cue['en']):
            assert not re.search(r'[\u3400-\u9fff]',text)
            x=(1080-draw.textlength(text,font=font))/2 if cue.get('center') else 72
            draw.text((x,cue['y']+i*56),text,font=font,fill='#f5ebd6',stroke_width=2,stroke_fill='#101820')
        image.save(folder/'labels'/(cue['id']+'.png'))
    subtitle='\n\n'.join(f'{i}\n{stamp(c["start"])} --> {stamp(c["end"])}\n{c["zh"]}'for i,c in enumerate(cue_list,1))+'\n'
    stem=f'{config["number"]:02}-{config["title"]}'
    (folder/'subtitles'/(stem+'.zh-Hans.srt')).write_text(subtitle,encoding='utf-8-sig')
    plan={**config,'stem':stem,'root':str(folder),'width':1080,'height':1920,'fps':24,'duration':58,'frames':1392,
          'artworks':works,'labels':cue_list,'music':music,'source_repository':str(UI),'source_snapshot':snapshot,
          'picture_language':'en','subtitles':['zh-Hans'],'narration':False}
    (folder/'edit-plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2))
    jobs.append(plan)
(ROOT/'batch.json').write_text(json.dumps({'approved_sample':str(PROJECT/'shorts/01-vastness'),'jobs':jobs,'source_snapshot':snapshot},ensure_ascii=False,indent=2))
(ROOT/'sources/layout-snapshot.json').write_text(json.dumps(snapshot,indent=2))
print('Prepared requested 58-second portrait films. Total batch jobs:',len(jobs))
