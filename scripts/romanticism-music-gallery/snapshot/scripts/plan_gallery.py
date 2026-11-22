from pathlib import Path
import json,subprocess,math,re,hashlib
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
FF='/opt/homebrew/bin/ffmpeg';FP='/opt/homebrew/bin/ffprobe';FPS=24
ART={a['id']:a for a in json.loads((ROOT/'sources/artworks.json').read_text()) if 'error' not in a}
old=ROOT.parent.parent/'lucas-academy-video/sites/chopin-romanticism-selection/dist'
MUSIC_OLD={x['id']:x for x in json.loads((old/'music.json').read_text())}

def duration(f):return float(subprocess.check_output([FP,'-v','error','-show_entries','format=duration','-of','csv=p=0',str(f)]))
def track(key,file,title,composer,piece,artist,part,cues):
 f=ROOT/'music'/file;secs=duration(f)
 return dict(id=key,file=str(f),title=title,composer=composer,piece=piece,performer=artist,part=part,audio_duration=secs,frames=math.ceil(secs*FPS),cues=cues)

tracks=[
 track('rain','prelude-28-15.m4a','雨、雾与边界','肖邦','降 D 大调前奏曲 Op. 28 No. 15「雨滴」','Jeannette Fang','nature',[
  (0,'gallery'),(12,'hay-wain'),(44,'chalk-cliffs'),(76,'monk-sea'),(109,'hannibal'),(144,'sea-ice'),(180,'vesuvius'),(215,'snow-storm'),(256,'oxbow'),(286,'sierra')]),
 track('nocturne','nocturne-9-2.m4a','暮光中的停留','肖邦','降 E 大调夜曲 Op. 9 No. 2','Musopen · 旧片同版录音','nature',[
  (0,'temeraire'),(54,'rain-steam'),(108,'ninth-wave'),(162,'twilight'),(217,'moonwatchers')]),
 track('distance','nocturne-c-sharp.m4a','向远方','肖邦','升 C 小调夜曲 B. 49','Frank Levy','nature',[
  (0,'wanderer'),(16,'wanderer-motion'),(26,'wanderer'),(59,'abbey-oakwood'),(114,'heart-andes'),(170,'sierra')]),
 track('life','beethoven-pathetique-ii.mp3','生命的河流','贝多芬','第八钢琴奏鸣曲 Op. 13「悲怆」· 第二乐章','Daniel Veesey','human',[
  (0,'visitors'),(10,'chopin-portrait'),(43,'film-faces'),(51,'ophelia'),(95,'shalott'),(142,'film-forest'),(150,'life-child'),(197,'life-youth'),(250,'life-man'),(311,'life-old')]),
 track('liberty','beethoven-egmont.flac','自由的代价','贝多芬','《埃格蒙特》序曲 Op. 84','Czech National Symphony Orchestra','human',[
  (0,'miranda'),(45,'wounded'),(89,'charging'),(140,'third-may'),(193,'chios'),(243,'missolonghi'),(293,'crusaders'),(343,'raft-medusa'),(392,'parliament'),(438,'liberty'),(470,'liberty-detail'),(507,'liberty')]),
]

# Keep complete recordings and their dynamics. Only a constant gain is used.
measure_names={'rain':'prelude-28-15','nocturne':'nocturne-9-2','distance':'nocturne-c-sharp','life':'pathetique','liberty':'egmont'}
for t in tracks:
 text=(ROOT/'checks'/(measure_names[t['id']]+'-loudness.txt')).read_text()
 m=json.loads(re.search(r'\{\s*"input_i".*?\}',text,re.S)[0])
 t['measured_lufs']=float(m['input_i']);t['measured_true_peak_db']=float(m['input_tp'])
 t['gain_db']=round(min(-24-t['measured_lufs'],-1.8-t['measured_true_peak_db']),3)
 t['sha256']=hashlib.sha256(Path(t['file']).read_bytes()).hexdigest()

footage={
 'gallery':dict(file=str(ROOT/'footage/gallery-5824200.mp4'),title='走进画廊',artist='博物馆实拍 · Charlotte May',dateLabel='',type='footage',source='https://www.pexels.com/video/arts-inside-a-gallery-5824200/'),
 'visitors':dict(file=str(ROOT/'footage/visitors-7986431.mp4'),title='观看的人',artist='博物馆实拍 · Antoni Shkraba',dateLabel='',type='footage',source='https://www.pexels.com/video/friends-looking-at-the-exhibition-of-paintings-7986431/'),
 'wanderer-motion':dict(file=str(old/'assets/video/wanderer.mp4'),title='雾海上的旅人',artist='弗里德里希 · 旧片艺术延展动态',dateLabel='',type='footage',source='Previous owner-created film'),
 'film-faces':dict(file=str(ROOT/'footage/mohicans-faces.mp4'),title='《最后的莫希干人》',artist='库珀小说改编 · 默片片段',dateLabel='1920',type='footage',source='https://archive.org/details/PublicdomainTheLastoftheMohicans'),
 'film-forest':dict(file=str(ROOT/'footage/mohicans-forest.mp4'),title='《最后的莫希干人》',artist='库珀小说改编 · 默片片段',dateLabel='1920',type='footage',source='https://archive.org/details/PublicdomainTheLastoftheMohicans'),
}
bio={'约瑟夫·赖特':'英国德比画家 · 浪漫主义自然题材的前奏','卡斯帕·大卫·弗里德里希':'德国浪漫主义风景画家','约瑟夫·马洛德·威廉·透纳':'英国浪漫主义风景画家','约翰·康斯特布尔':'英国风景画家','托马斯·科尔':'美国哈德逊河画派画家','弗雷德里克·埃德温·丘奇':'美国哈德逊河画派画家','阿尔伯特·比尔施塔特':'德裔美国风景画家','伊万·艾瓦佐夫斯基':'以海景著称的十九世纪画家','弗朗西斯科·戈雅':'西班牙宫廷画家','泰奥多尔·籍里柯':'法国浪漫主义画家','欧仁·德拉克洛瓦':'法国浪漫主义画家','约翰·埃弗里特·米莱':'英国拉斐尔前派画家 · 文学绘画','约翰·威廉·沃特豪斯':'英国文学绘画 · 浪漫主义意象的后续回响'}
seen=set();global_cursor=0;shots=[]
for ti,t in enumerate(tracks):
 t['start']=global_cursor;t['video_duration']=t['frames']/FPS
 raw=subprocess.check_output([FF,'-hide_banner','-loglevel','error','-i',t['file'],'-ac','1','-ar','6000','-f','f32le','-'])
 samples=np.frombuffer(raw,dtype='<f4');block=300
 n=len(samples)//block;energy=np.sqrt(np.mean(samples[:n*block].reshape(n,block)**2,axis=1))
 cues=t['cues'];adjusted=[]
 for i,(time,key) in enumerate(cues):
  # Quiet points close to the planned music/painting boundary, at most 0.75 s.
  if i and key not in {'wanderer-motion','film-faces','film-forest'}:
   lo=max(0,int((time-.75)*20));hi=min(len(energy),int((time+.75)*20))
   if hi>lo:time=(lo+int(np.argmin(energy[lo:hi])))/20
  adjusted.append((round(time*FPS)/FPS,key))
 local=[]
 for i,(start,key) in enumerate(adjusted):
  end=adjusted[i+1][0] if i+1<len(adjusted) else t['video_duration']
  base='liberty' if key=='liberty-detail' else key
  a=dict(ART[base]) if base in ART else dict(footage[base])
  kind='art' if base in ART else 'footage'
  a.update(id=f"{t['id']}-{i:02}",asset_id=base,track=t['id'],type=kind,start=start,end=end,seconds=end-start,global_start=global_cursor+start,global_end=global_cursor+end,first_artist=False)
  if kind=='art' and a['artist'] not in seen:a['first_artist']=True;a['bio']=bio.get(a['artist'],'');seen.add(a['artist'])
  a['detail']=key=='liberty-detail'
  a['album_opening']=ti==0 and i==0;a['track_opening']=i==0
  a['music_label']=f"{t['composer']} · {t['piece']}"
  local.append(a);shots.append(a)
 t['shots']=local;t['end']=global_cursor+t['video_duration'];t['gap_after']=1.5 if ti<len(tracks)-1 else 0
 global_cursor=t['end']+t['gap_after']

used=sorted({s['asset_id'] for s in shots if s['type']=='art'})
assert len(used)==34,(len(used),used)
human_start=next(t['start'] for t in tracks if t['part']=='human')
plan=dict(title='山海与人间',subtitle='浪漫主义音乐画廊',format='纯音乐 · 无配音',fps=FPS,width=1920,height=1080,duration=global_cursor,nature_end=human_start,artwork_count=len(used),artwork_ids=used,tracks=tracks,shots=shots,audio_policy='Exactly five complete instrumental recordings; constant gain only; source video audio is omitted. The three Chopin files are byte-identical to the owner-selected recordings.',curatorial_note='自然篇由乡野与雨雾进入风暴、冰海与火山，再回到暮色和辽阔。人文篇从肖像、文学与生命之旅，走向战争中的普通人和自由的象征。米莱与沃特豪斯作为英国文学绘画的后续回响单独注明。')
(ROOT/'edit-plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2))
(ROOT/'sources/selected-artworks.json').write_text(json.dumps([ART[i] for i in used],ensure_ascii=False,indent=2))
print('PLANNED',len(used),'works',len(shots),'shots',round(global_cursor,3),'seconds',flush=True)
for t in tracks:print(t['id'],round(t['start'],3),round(t['end'],3),t['gain_db'],'dB',flush=True)
