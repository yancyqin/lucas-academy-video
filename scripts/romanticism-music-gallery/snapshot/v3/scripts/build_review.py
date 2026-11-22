from pathlib import Path
from lxml import html,etree
import json,hashlib,math
ROOT=Path(__file__).resolve().parents[1];OLD=ROOT.parent
plan=json.loads((ROOT/'edit-plan.json').read_text());doc=html.fromstring((OLD/'视频预览.html').read_text())
label_style=json.loads((ROOT/'label-style.json').read_text())
for node in doc.xpath('//*[@id="new-salon-version"]'):node.getparent().remove(node)
reference_sources=json.loads((OLD.parent/'raindrop-romanticism/production/v5/sources-and-credits.json').read_text())
oldnames=['山海与人间-浪漫主义纯音乐版.mp4','自然篇-肖邦-纯音乐版.mp4','人间篇-贝多芬-纯音乐版.mp4']
newnames=['山海与人间-中英标签纯音乐版.mp4','自然篇-肖邦-中英标签版.mp4','人间篇-贝多芬-中英标签版.mp4']
for node in doc.xpath('//*[@href or @src]'):
 for k in ['href','src']:
  value=node.get(k)
  if not value:continue
  if value.startswith(('thumbs/','art/')):value='../'+value
  if value.startswith('../raindrop-romanticism/'):
   value='../'+value
   if value.endswith('/production/视频预览.html'):value=value.replace('/production/视频预览.html','/production/v5/preview.html')
  for a,b in zip(oldnames,newnames):value=value.replace(a,b)
  node.set(k,value)
doc.xpath('//title')[0].text='山海与人间 · 中英简洁标签版'
doc.xpath('//p[@class="subtitle"]')[0].text='纯音乐沙龙漫步。英文在上、中文在下，两行同字号；作品标签只保留作品名与画家。'
heading=doc.xpath('//h1')[0];heading.clear();heading.set('class','bilingual-heading')
etree.SubElement(heading,'span').text='Mountains, Seas & Human Life';etree.SubElement(heading,'span').text='山海与人间'
native_link=doc.xpath('//p[@class="shared-salon"]/a/span')
if len(native_link)==2:native_link[0].text,native_link[1].text=native_link[1].text,native_link[0].text
for b in doc.xpath('//button[contains(concat(" ",normalize-space(@class)," ")," mode ")]'):
 pairs={'full':('Full Film','完整影片'),'nature':('Nature · Chopin','自然 · 肖邦'),'human':('Human Life · Beethoven','人间 · 贝多芬')}
 en,zh=pairs[b.get('data-mode')];b.text=None
 for child in list(b):b.remove(child)
 b.set('class',b.get('class')+' pair-control');etree.SubElement(b,'span').text=en;etree.SubElement(b,'span').text=zh
chapter_names={'rain':('Rain & Mist','雨雾与边界'),'nocturne':('Twilight','暮光中的停留'),'distance':('Into the Distance','向远方'),'life':('The River of Life','生命的河流'),'liberty':('The Price of Freedom','自由的代价')}
for b in doc.xpath('//button[@data-track]'):
 heading=b.xpath('./strong')[0];heading.clear();heading.set('class','chapter-pair');en,zh=chapter_names[b.get('data-track')]
 etree.SubElement(heading,'span').text=en;etree.SubElement(heading,'span').text=zh
 for child in b.xpath('./small'):b.remove(child)
doc.xpath('//div[@class="meta"]/span')[1].text='34 件重点作品'
doc.xpath('//p[@class="intro"]')[0].text='与配音版共用同一座浪漫主义沙龙。从自然画墙走到暮色、文学与生命主题，再沿人文画墙回望苦难与自由。三首肖邦与两首贝多芬均为完整录音。镜头连续行走，到作品前停稳后柔和淡入原画，再淡回同一机位。'
notes=doc.xpath('//section[1]/p[@class="note"]')
if notes:notes[0].text='音乐与画面的配对是本片的策展联想。米莱、沃特豪斯的文学绘画作为浪漫主义意象的后续回响加入。画作保留原貌，重点欣赏时展示静止的完整原图。'
descriptions=[
 '沿自然画墙，从河湾走到冰海、乡野、峭壁、暴风雪与火山。',
 '转到时间主题画墙，停留在废墟、月光、暮色与蒸汽之间。',
 '回到自然画墙，近看风暴、海浪、安第斯山与旅人的背影。',
 '从肖邦肖像与英国文学绘画，走向科尔《生命之旅》四联画。',
 '沿人文画墙看战争、海难与受伤的人，最后停在《自由引导人民》。'
]
for row,description in zip(doc.xpath('//tbody/tr'),descriptions):row.xpath('./td')[-1].text=description
grid=doc.xpath('//div[@class="grid"]')[0];cards={}
for card in list(grid):
 href=card.xpath('.//a[contains(@href,"/art/")]')[0].get('href');cards[Path(href).stem]=card;grid.remove(card)
for s in plan['shots']:
 card=cards[s['asset_id']];button=card.xpath('.//button[@data-seek]')[0]
 button.set('data-seek',str(s['global_start']));n=math.floor(s['global_start']);button.xpath('./span')[0].text=f'▶ {n//60:02}:{n%60:02}'
 card.set('data-art',s['asset_id']);pair=label_style['artworks'][s['asset_id']]
 heading=card.xpath('.//h3')[0];heading.clear();heading.set('class','paired-label')
 etree.SubElement(heading,'span').text=pair['english'];etree.SubElement(heading,'span').text=pair['chinese']
 for node in card.xpath('.//p[@class="artist"]|.//p[@class="art-date"]'):node.getparent().remove(node)
 grid.append(card)
doc.xpath('//div[@class="section-top"]/h2')[0].text='本次重点观看的 34 件作品'
data=json.loads(doc.xpath('//script[@id="program-data"]')[0].text)
for key,name in zip(['full','nature','human'],newnames):data['files'][key]['src']='exports/'+name
data['files']['full']['label']='完整影片 · 中英简洁标签版'
doc.xpath('//script[@id="program-data"]')[0].text=json.dumps(data,ensure_ascii=False)

details=doc.xpath('//details');footage=next(d for d in details if '实拍与电影' in d.xpath('./summary')[0].text_content())
footage.xpath('./summary')[0].text='展厅与借用片段'
ul=footage.xpath('./ul')[0]
for item in list(ul):ul.remove(item)
entries=[
 ('共用的 IS 浪漫主义沙龙','沿用同一展厅、56 件平面作品、8 件馆内雕塑与中央 Moose the Dragon。摄影机路线经过展台避让检查，画前机位固定。','http://127.0.0.1:8095/?world=museum&room=romanticism-salon'),
 ('配音版已有的氛围镜头','入口画廊、修道院和巴黎镜头沿用已完成素材；入口采用保留完整画幅、剪掉开头半秒晃动的版本。',''),
 ('《最后的莫希干人》（1920）','库珀小说改编的公版默片，仅使用人物与树林两段画面，未混入源片音轨。','https://archive.org/details/PublicdomainTheLastoftheMohicans'),
 ('《雾海上的旅人》旧片动态','沿用此前已有的艺术延展片段，在完整原作与展厅机位之间短暂出现。','')
]
for title,description,url in entries:
 li=etree.SubElement(ul,'li');etree.SubElement(li,'strong').text=title
 if url:a=etree.SubElement(li,'a',href=url,target='_blank',rel='noopener');a.text='  来源 ↗'
 etree.SubElement(li,'p').text=description
models=etree.SubElement(footage,'ul',{'class':'credits'})
for scan in reference_sources['scans']:
 li=etree.SubElement(models,'li');etree.SubElement(li,'strong').text=scan.get('model_title',scan['title_en'])
 etree.SubElement(li,'p').text=scan.get('model_credit','SMK Open')+' · '+scan['license']
 a=etree.SubElement(li,'a',href=scan.get('model_source',scan['source']),target='_blank',rel='noopener');a.text='模型来源 ↗'
 a.tail=' · ';a=etree.SubElement(li,'a',href=scan['license_url'],target='_blank',rel='noopener');a.text='许可 ↗'
 etree.SubElement(li,'p').text=scan['modifications']
for a in doc.xpath('//div[@class="previous"]/a'):
 if a.get('href','').endswith('preview.html'):a.text='《压力？焦虑？肖邦？浪漫？》最新配音版 ↗'
source_detail=next(d for d in details if '完整素材' in d.xpath('./summary')[0].text_content())
extra=etree.SubElement(source_detail,'p',{'class':'note'});a=etree.SubElement(extra,'a',href='sources/attribution.txt',download='');a.text='音乐与雕塑模型署名 TXT ↓'
style=doc.xpath('//style')[0];style.text+='\n.version-link{border:1px solid #d5c99c;padding:14px 18px;border-radius:6px;margin:22px 0;color:#d5c99c;font-size:14px}.paired-label span{display:block;font-size:15px;font-weight:400;line-height:1.65;color:var(--text)}.bilingual-heading span{display:block;font-size:clamp(20px,3.4vw,44px);font-weight:500;line-height:1.5;letter-spacing:0}'
style.text+='\n.pair-control span{display:block;font-size:13px;line-height:1.5}.chapter .chapter-pair span{display:block;font-size:14px;line-height:1.6;color:var(--text)}'
previous=html.fragment_fromstring('<p class="note">上一版：<a href="../v2/preview.html">沙龙漫步版 ↗</a></p>')
doc.xpath('//div[@class="downloads"]')[0].addnext(previous)
doc.xpath('//div[@class="screen"]')[0].addnext(html.fragment_fromstring('<p class="note" style="margin:14px 0"><a href="exports/从画廊到星空沙龙-中英标签开场.mp4">先看 18 秒开场转场 ↗</a></p>'))
(ROOT/'preview.html').write_text('<!doctype html>\n'+html.tostring(doc,encoding='unicode',method='html'))

credits=json.loads((OLD/'sources/credits.json').read_text())
credits['title']='山海与人间 · 浪漫主义沙龙漫步'
credits['native_salon']=json.loads((OLD/'shared-salon.json').read_text())
credits['room_works']=reference_sources['room_works']
credits['scans']=reference_sources['scans']
credits['central_sculpture']=reference_sources['central_sculpture']
credits['camera_reference']=json.loads((ROOT/'sources/reference-style.json').read_text())
credits['footage']=[dict(name=i['name'],file=i['file'],sha256=hashlib.sha256(Path(i['file']).read_bytes()).hexdigest(),start=i['start'],end=i['end'],speed=i['speed'],source='Existing owner-authorized footage; see referenced narrated-branch sources.' if i['kind'] not in ['public-domain-film'] else 'https://archive.org/details/PublicdomainTheLastoftheMohicans',kind=i['kind'])for i in plan['inserts']]
credits['opening']=dict(gallery_file='assets/gallery-entry.mp4',sha256=hashlib.sha256((ROOT/'assets/gallery-entry.mp4').read_bytes()).hexdigest(),source_trim=.4,speed=.8,native_capture='footage/walk/walk-000.mp4',composite_seconds=18,source='Same owner-approved Muse gallery entry, same full-width crop and timing, dissolving into the newly captured bilingual native salon.')
credits['sources_reference']=str(OLD.parent/'raindrop-romanticism/production/v5/sources-and-credits.json')
credits['audio_policy']='Same complete 5-recording music-only PCM program as the previous film. All source-video soundtracks are excluded.'
credits['route_summary']=plan['speeds']
credits['label_style']=label_style
(ROOT/'sources/credits.json').write_text(json.dumps(credits,ensure_ascii=False,indent=2))
text=['山海与人间 · 浪漫主义沙龙漫步','Yancy 与 Eunice 共同创作','纯音乐，无配音。','',
 '音乐 / Music']
for m in credits['music']:text += [m['composer']+' · '+m['title'],m['performer']+' · '+m['license'],m['source'],'']
text+=['雕塑扫描模型 / Sculpture scans']
for s in credits['scans']:text += [s.get('model_title',s['title_en']),s.get('model_credit','SMK Open')+' · '+s['license'],s.get('model_source',s['source']),s['license_url'],'Modifications: '+s['modifications'],'']
text+=['Moose the Dragon — original sculpture and scan from Lucas Academy.','',
 '《最后的莫希干人》（1920）/ The Last of the Mohicans','Public-domain silent film, adapted from James Fenimore Cooper.','https://archive.org/details/PublicdomainTheLastoftheMohicans','',
 '画作、录音及画面文件的完整来源见 sources/credits.json。','入口、修道院、巴黎和旅人动态沿用既有的经授权素材。']
(ROOT/'sources/attribution.txt').write_text('\n'.join(text))
print('REVIEW PAGE READY',len(grid),'artworks')
