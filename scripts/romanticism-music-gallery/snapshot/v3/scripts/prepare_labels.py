"""Simple bilingual film labels: English above Chinese, identical font size."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json
ROOT=Path(__file__).resolve().parents[1];OLD=ROOT.parent
UI=OLD.parent.parent/'inception-space-ui'
plan=json.loads((ROOT/'edit-plan.json').read_text())
font=lambda n:ImageFont.truetype('/System/Library/Fonts/STHeiti Medium.ttc',n)
titles={
 'oxbow':('The Oxbow','河湾'),
 'sea-ice':('The Sea of Ice','冰海'),
 'hay-wain':('The Hay Wain','干草车'),
 'chalk-cliffs':('Chalk Cliffs on Rügen','吕根岛白垩岩'),
 'hannibal':('Snow Storm: Hannibal','暴风雪：汉尼拔'),
 'monk-sea':('Monk by the Sea','海边的修道士'),
 'vesuvius':('Vesuvius in Eruption','维苏威火山喷发'),
 'abbey-oakwood':('Abbey in the Oakwood','橡树林中的修道院'),
 'moonwatchers':('Two Men Contemplating the Moon','两人望月'),
 'twilight':('Twilight in the Wilderness','荒野暮色'),
 'temeraire':('The Fighting Temeraire','战舰“特梅雷尔”号'),
 'rain-steam':('Rain, Steam and Speed','雨、蒸汽与速度'),
 'snow-storm':('Snow Storm: Steam-Boat','暴风雪：汽船'),
 'ninth-wave':('The Ninth Wave','第九浪'),
 'heart-andes':('The Heart of the Andes','安第斯之心'),
 'wanderer':('Wanderer above the Sea of Fog','雾海上的旅人'),
 'sierra':('Among the Sierra Nevada','内华达山脉之中'),
 'chopin-portrait':('Portrait of Chopin','肖邦像'),
 'ophelia':('Ophelia','奥菲莉娅'),
 'shalott':('The Lady of Shalott','夏洛特夫人'),
 'life-child':('The Voyage of Life: Childhood','生命之旅：童年'),
 'life-youth':('The Voyage of Life: Youth','生命之旅：青年'),
 'life-man':('The Voyage of Life: Manhood','生命之旅：壮年'),
 'life-old':('The Voyage of Life: Old Age','生命之旅：老年'),
 'miranda':('Miranda — The Tempest','米兰达——暴风雨'),
 'chios':('Massacre at Chios','希阿岛的屠杀'),
 'crusaders':('Entry of the Crusaders into Constantinople','十字军进入君士坦丁堡'),
 'raft-medusa':('The Raft of the Medusa','梅杜萨之筏'),
 'parliament':('The Burning of Parliament','议会大厦的焚毁'),
 'wounded':('The Wounded Cuirassier','负伤的胸甲骑兵'),
 'third-may':('The Third of May 1808','1808 年 5 月 3 日'),
 'charging':('The Charging Chasseur','冲锋的猎骑兵'),
 'missolonghi':('Greece at Missolonghi','希腊在迈索隆吉翁'),
 'liberty':('Liberty Leading the People','自由引导人民'),
}
artists={
 '约瑟夫·赖特':('Wright','赖特'),
 '卡斯帕·大卫·弗里德里希':('Friedrich','弗里德里希'),
 '约瑟夫·马洛德·威廉·透纳':('Turner','透纳'),
 '约翰·康斯特布尔':('Constable','康斯特布尔'),
 '托马斯·科尔':('Cole','科尔'),
 '弗雷德里克·埃德温·丘奇':('Church','丘奇'),
 '阿尔伯特·比尔施塔特':('Bierstadt','比尔施塔特'),
 '伊万·艾瓦佐夫斯基':('Aivazovsky','艾瓦佐夫斯基'),
 '弗朗西斯科·戈雅':('Goya','戈雅'),
 '泰奥多尔·籍里柯':('Géricault','籍里柯'),
 '欧仁·德拉克洛瓦':('Delacroix','德拉克洛瓦'),
 '约翰·埃弗里特·米莱':('Millais','米莱'),
 '约翰·威廉·沃特豪斯':('Waterhouse','沃特豪斯'),
}
music={
 'rain':('Chopin · Raindrop Prelude','肖邦 ·《雨滴》前奏曲'),
 'nocturne':('Chopin · Nocturne Op. 9 No. 2','肖邦 · 夜曲 Op. 9 No. 2'),
 'distance':('Chopin · Nocturne in C-sharp minor','肖邦 · 升 C 小调夜曲'),
 'life':('Beethoven · Pathétique, II','贝多芬 ·《悲怆》第二乐章'),
 'liberty':('Beethoven · Egmont Overture','贝多芬 ·《埃格蒙特》序曲'),
}
records=[];art_records={}
def pair_image(key,lines,size,positions,gradient=None,stroke=False):
 im=Image.new('RGBA',(1920,1080));d=ImageDraw.Draw(im)
 if gradient=='bottom':
  for y in range(940,1080):d.line((0,y,1920,y),fill=(9,15,17,min(230,round((y-940)/100*230))))
 elif gradient=='top':
  for y in range(0,148):d.line((0,y,1920,y),fill=(7,13,15,round(210*(1-y/148))))
 while max(d.textbbox((0,0),line,font=font(size))[2] for line in lines)>1770:size-=1
 f=font(size)
 for line,point in zip(lines,positions):
  if key=='entrance':point=((1920-d.textbbox((0,0),line,font=f)[2])/2,point[1])
  d.text(point,line,font=f,fill='#f3ebd9',stroke_width=2 if stroke else 0,stroke_fill='#101820')
 im.save(ROOT/'labels'/(key+'.png'))
 records.append(dict(id=key,english=lines[0],chinese=lines[1],font_px_english=size,font_px_chinese=size,english_above_chinese=positions[0][1]<positions[1][1],lines=2))
 return records[-1]

for s in plan['shots']:
 en,zh=titles[s['asset_id']];ae,az=artists[s['artist']]
 record=pair_image(s['id'],(en+' · '+ae,zh+' · '+az),34,((65,965),(65,1012)),'bottom')
 art_records[s['asset_id']]={**record,'title_en':en,'title_zh':zh,'artist_en':ae,'artist_zh':az}
for t in plan['tracks']:pair_image(t['id'],music[t['id']],34,((65,25),(65,73)),'top')
pair_image('album',('Mountains, Seas & Human Life','山海与人间'),50,((84,834),(84,901)),stroke=True)
pair_image('entrance',('From Gallery to Space','从画廊到星空沙龙'),40,((600,807),(600,863)),stroke=True)

native={}
catalog=json.loads((UI/'content/inception/artworks/romanticism-salon-v1.json').read_text())['works']
for a in catalog:
 en,zh=titles.get(a['id'],(a.get('label_en',a['title_en']).split(', from the series')[0],a['title_zh']))
 for key in {a['title_en'],a.get('label_en',a['title_en'])}:native[key]=dict(english=en,chinese=zh,kind='painting',id=a['id'])
scans=json.loads((UI/'content/inception/artworks/romanticism-sculptures-v1.json').read_text())['works']
for s in scans:native[s['title_en']]=dict(english=s['title_en'],chinese=s['title_zh'],kind='sculpture',id=s['id'])
for en,zh in [('Lion and Serpent','狮子与蛇'),('The Spirit of Liberty','自由之灵'),('Philopoemen','菲洛波门'),('Seated Lion','坐狮'),('Recumbent Bacchante','斜卧的酒神女祭司'),('Head of Christ','基督头像')]:
 native[en]=dict(english=en,chinese=zh,kind='sculpture')
for en,zh in [
 ('THE ROMANTIC SALON','浪漫主义沙龙'),
 ('Nature and the Sublime','自然与崇高'),
 ('An Age of Upheaval','动荡的时代'),
 ('Time and Human Life','时间与人生'),
 ('Literary Echoes and Mono no Aware','文学回响与物哀'),
 ('Moose the Dragon','巨龙 Moose'),
]:native[en]=dict(english=en.title() if en.isupper() else en,chinese=zh,kind='room')

style=dict(version=3,order=['English','Chinese'],same_font_size_per_pair=True,lines_per_label=2,
 artwork_format='Title · Artist / 作品名 · 画家',no_biography=True,no_date_in_film_labels=True,
 overlays=records,artworks=art_records,music={k:dict(english=v[0],chinese=v[1])for k,v in music.items()},native=native)
(ROOT/'label-style.json').write_text(json.dumps(style,ensure_ascii=False,indent=2))
assert all(r['font_px_english']==r['font_px_chinese'] and r['english_above_chinese'] for r in records)
print('BILINGUAL LABELS READY',len(records),'overlays;',len(native),'native title mappings')
