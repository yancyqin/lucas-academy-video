from pathlib import Path
from PIL import Image
import urllib.request,json,hashlib,shutil,concurrent.futures

ROOT=Path(__file__).resolve().parents[1];SRC=ROOT/'sources'
OLD=ROOT.parent.parent/'lucas-academy-video/sites/chopin-romanticism-selection/dist'
old_ids='vesuvius monk-sea abbey-oakwood hannibal third-may wanderer chalk-cliffs raft-medusa hay-wain sea-ice chios missolonghi liberty parliament oxbow chopin-portrait temeraire snow-storm rain-steam ninth-wave heart-andes ophelia'.split()
records=[]
for a in json.loads((OLD/'art.json').read_text()):
 if a['id'] not in old_ids:continue
 a=dict(a);dest=ROOT/'art'/(a['id']+'.jpg');shutil.copy2(OLD/a['image'],dest)
 a.update(file=str(dest),reuse=True,sha256=hashlib.sha256(dest.read_bytes()).hexdigest());records.append(a)

infos={}
for file in ['new-art-imageinfo.json','extra-imageinfo.json','niagara-search.json']:
 for page in json.loads((SRC/file).read_text()).get('query',{}).get('pages',{}).values():
  if page.get('imageinfo'):infos[page['title'].removeprefix('File:')]=page['imageinfo'][0]

new=[
 ('moonrise','海上月出','卡斯帕·大卫·弗里德里希','1822','Caspar David Friedrich - Mondaufgang am Meer - Google Art Project.jpg','https://cdfriedrich.de/en/chronicle/mondaufgang-am-meer-2/',False),
 ('moonwatchers','两人望月','卡斯帕·大卫·弗里德里希','1819–1820','Caspar David Friedrich - Two Men Contemplating the Moon - Google Art Project.jpg','https://artsandculture.google.com/asset/two-men-contemplating-the-moon/AQHW6lwY6LzX1Q',False),
 ('window','窗前的女人','卡斯帕·大卫·弗里德里希','1822','C. D. Friedrich - Woman at a window.jpg','https://artsandculture.google.com/asset/woman-at-a-window-0093/ggGqXUiKkQrSaw',False),
 ('salisbury','草地上的索尔兹伯里大教堂','约翰·康斯特布尔','1831','Constable Salisbury meadows.jpg','https://www.tate.org.uk/art/artworks/constable-salisbury-cathedral-from-the-meadows-t13896',False),
 ('cornfield','麦田','约翰·康斯特布尔','1826','Constable - The Cornfield.jpg','https://www.nationalgallery.org.uk/paintings/john-constable-the-cornfield',False),
 ('norham','诺勒姆城堡：日出','约瑟夫·马洛德·威廉·透纳','约 1845','Joseph Mallord William Turner - Norham Castle, Sunrise - WGA23182.jpg','https://www.tate.org.uk/art/artworks/turner-norham-castle-sunrise-n01981',False),
 ('niagara','尼亚加拉','弗雷德里克·埃德温·丘奇','1857','Niagara-falls-Church.jpg','https://www.nga.gov/artworks/166436-niagara',False),
 ('twilight','荒野暮色','弗雷德里克·埃德温·丘奇','1860','Twilight in the Wilderness by Frederic Edwin Church (3).jpg','https://www.clevelandart.org/art/1965.233',False),
 ('sierra','加利福尼亚内华达山脉之中','阿尔伯特·比尔施塔特','1868','Bierstadt - Among the Sierra Nevada Mountains - 1868.jpg','https://www.si.edu/object/saam_1977.107.1',False),
 ('life-child','生命之旅：童年','托马斯·科尔','1842','Thomas Cole, The Voyage of Life - Childhood, 1842, NGA 52450.jpg','https://www.nga.gov/artworks/52450-voyage-life-childhood',True),
 ('life-youth','生命之旅：青年','托马斯·科尔','1842','Thomas Cole, The Voyage of Life - Youth, 1842, NGA 52451.jpg','https://www.nga.gov/artworks/52451-voyage-life-youth',False),
 ('life-man','生命之旅：壮年','托马斯·科尔','1842','Thomas Cole, The Voyage of Life - Manhood, 1842, NGA 52452.jpg','https://www.nga.gov/artworks/52452-voyage-life-manhood',False),
 ('life-old','生命之旅：老年','托马斯·科尔','1842','Thomas Cole, The Voyage of Life - Old Age, 1842, NGA 52453.jpg','https://www.nga.gov/artworks/52453-voyage-life-old-age',False),
 ('charging','冲锋的猎骑兵','泰奥多尔·籍里柯','1812','GericaultHorseman.jpg','https://commons.wikimedia.org/wiki/File:GericaultHorseman.jpg',False),
 ('wounded','负伤的胸甲骑兵','泰奥多尔·籍里柯','1814','Cuirassier blessé, quittant le feu - Théodore Géricault - Musée du Louvre Peintures INV 4886 ; MN 51.jpg','https://commons.wikimedia.org/wiki/File:Cuirassier_blessé,_quittant_le_feu_-_Théodore_Géricault_-_Musée_du_Louvre_Peintures_INV_4886_;_MN_51.jpg',False),
 ('delacroix-self','自画像','欧仁·德拉克洛瓦','1837','Eugène Delacroix - Self-Portrait - WGA6192.jpg','https://www.wga.hu/html_m/d/delacroi/3/311delac.html',False),
 ('crusaders','十字军进入君士坦丁堡','欧仁·德拉克洛瓦','1840','Prise de Constantinople par les croisés (12 avril 1204) - Eugène Delacroix - Musée du Louvre Peintures INV 3821 ; LP 4674 - après restauration 2026.jpg','https://commons.wikimedia.org/wiki/File:Prise_de_Constantinople_par_les_croisés_(12_avril_1204)_-_Eugène_Delacroix_-_Musée_du_Louvre_Peintures_INV_3821_;_LP_4674_-_après_restauration_2026.jpg',True),
 ('cora','最后的莫希干人：科拉之死','托马斯·科尔','约 1827','Cole Thomas Indian Sacrifice 1826.jpg','https://commons.wikimedia.org/wiki/File:Cole_Thomas_Indian_Sacrifice_1826.jpg',True),
]

def acquire(row):
 ident,title,artist,date,filename,source,nudity=row
 info=infos.get(filename)
 if not info:return dict(id=ident,error='Image metadata missing',file=filename)
 license=info.get('extmetadata',{}).get('LicenseShortName',{}).get('value')
 if license not in ['Public domain','CC0','CC0 1.0']:return dict(id=ident,error='Unapproved licence: '+str(license))
 url=info.get('thumburl') or info['url'];dest=ROOT/'art'/(ident+'.jpg')
 try:
  if not dest.exists():
   req=urllib.request.Request(url,headers={'User-Agent':'LucasAcademyArtworkSelection/1.0'})
   with urllib.request.urlopen(req,timeout=75) as response:data=response.read()
   tmp=dest.with_suffix('.jpg.part');tmp.write_bytes(data)
   with Image.open(tmp) as im:im.verify()
   tmp.replace(dest)
  with Image.open(dest) as im:width,height=im.size
  return dict(id=ident,title=title,artist=artist,dateLabel=date,year=int(''.join(x for x in date if x.isdigit())[:4]),file=str(dest),source=source,imageSource=info['descriptionurl'],download_url=url,license=license,nudity=nudity,width=width,height=height,sha256=hashlib.sha256(dest.read_bytes()).hexdigest(),reuse=False)
 except Exception as e:return dict(id=ident,error=str(e),download_url=url)

with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
 for a in pool.map(acquire,new):records.append(a);print(a['id'],a.get('error','OK'),flush=True)
(SRC/'artworks.json').write_text(json.dumps(records,ensure_ascii=False,indent=2))
print('ART',sum('error' not in a for a in records),'of',len(records),flush=True)
