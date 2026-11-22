import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
import {mkdir,readFile,writeFile,rename,unlink,stat} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {spawn} from 'node:child_process';
import {once} from 'node:events';
import path from 'node:path';
import {pathToFileURL} from 'node:url';

const ROOT=path.resolve(import.meta.dirname,'..');
const OLD=path.resolve(ROOT,'..');
const UI=path.resolve(OLD,'../../inception-space-ui');
const {romanticismHangingPlan,romanticismPedestalObstacles}=await import(pathToFileURL(path.join(UI,'src/inception/world/rooms/romanticismLayout.js')));
const require=createRequire('@RUNTIME_DEPS@/node/package.json');
const {chromium}=require('playwright');
const old=JSON.parse(await readFile(path.join(OLD,'edit-plan.json'),'utf8'));
const art=JSON.parse(await readFile(path.join(OLD,'sources/selected-artworks.json'),'utf8'));
const catalog=JSON.parse(await readFile(path.join(UI,'content/inception/artworks/romanticism-salon-v1.json'),'utf8'));
const hung=new Map(romanticismHangingPlan(catalog.works).map(a=>[a.id,a]));
const artMap=new Map(art.map(a=>[a.id,a]));
const labelStyle=JSON.parse(await readFile(path.join(ROOT,'label-style.json'),'utf8'));
const W=1920,H=1080,FPS=24;
const snap=t=>Math.round(t*FPS)/FPS;
const ease=t=>{t=Math.max(0,Math.min(1,t));return t*t*(3-2*t)};
const key=(t,eye,target,fov=52)=>({at:Math.round(t*FPS),eye,target,fov});
const Y=4.45;
const obstacles=romanticismPedestalObstacles().map(b=>({...b,x0:b.x0-1,x1:b.x1+1,z0:b.z0-1,z1:b.z1+1}));
const free=([x,z])=>Math.abs(x)<25.7&&Math.abs(z)<40.6&&!obstacles.some(b=>x>=b.x0&&x<=b.x1&&z>=b.z0&&z<=b.z1);
const distance=(a,b)=>Math.hypot(a[0]-b[0],a[1]-b[1]);
function sight(a,b){const n=Math.max(1,Math.ceil(distance(a,b)/.08));for(let i=0;i<=n;i++)if(!free([a[0]+(b[0]-a[0])*i/n,a[1]+(b[1]-a[1])*i/n]))return false;return true}
function route(a,b){
 if(sight(a,b))return[a,b];
 const grid=p=>p.map(Math.round),start=grid(a),finish=grid(b),id=p=>p.join(',');
 const open=[start],cost=new Map([[id(start),0]]),parent=new Map(),seen=new Set();
 while(open.length){
  open.sort((a,b)=>(cost.get(id(a))+distance(a,finish))-(cost.get(id(b))+distance(b,finish)));
  const p=open.shift(),pk=id(p);if(seen.has(pk))continue;seen.add(pk);
  if(pk===id(finish)){
   const list=[b];let n=finish;while(id(n)!==id(start)){list.push(n);n=parent.get(id(n))}list.push(a);list.reverse();
   const simplified=[a];let i=0;
   while(i<list.length-1){let j=list.length-1;while(j>i+1&&!sight(list[i],list[j]))j--;simplified.push(list[j]);i=j}
   return simplified;
  }
  for(const [dx,dz]of [[1,0],[-1,0],[0,1],[0,-1],[1,1],[1,-1],[-1,1],[-1,-1]]){
   const q=[p[0]+dx,p[1]+dz],qk=id(q);if(!free(q)||!sight(p,q))continue;
   const c=cost.get(pk)+Math.hypot(dx,dz);if(c>=(cost.get(qk)??Infinity))continue;
   cost.set(qk,c);parent.set(qk,p);open.push(q);
  }
 }
 throw Error('No clear museum path: '+JSON.stringify({a,b}));
}
function paintingPose(id,t){
 const a=hung.get(id);assert.ok(a,id);let eye=a.position.slice();const upper=eye[1]>7;
 const d=upper?7.1:4.8;
 if(a.wallId==='nature')eye[0]+=d;
 if(a.wallId==='social')eye[0]-=d;
 if(a.wallId==='time')eye[2]+=d;
 if(a.wallId==='echo')eye[2]-=d;
 eye[1]=Y;return key(t,eye,a.position.slice(),upper?34:47);
}
const windows=[
 ['rain',36,66,'oxbow'],['rain',80,110,'sea-ice'],['rain',124,154,'hay-wain'],
 ['rain',168,198,'chalk-cliffs'],['rain',212,242,'hannibal'],['rain',256,280,'monk-sea'],['rain',292,315.5,'vesuvius'],
 ['nocturne',11,51,'abbey-oakwood'],['nocturne',58,99,'moonwatchers'],['nocturne',111,154,'twilight'],
 ['nocturne',166,211,'temeraire'],['nocturne',223,270.8,'rain-steam'],
 ['distance',18,51,'snow-storm'],['distance',62,94,'ninth-wave'],['distance',105,137,'heart-andes'],
 ['distance',148,180,'wanderer'],['distance',192,224.3,'sierra'],
 ['life',25,52,'chopin-portrait'],['life',74,109,'ophelia'],['life',123,153,'shalott'],
 ['life',191,226,'life-child'],['life',240,276,'life-youth'],['life',291,326,'life-man'],['life',343,380.583333,'life-old'],
 ['liberty',32,66,'miranda'],['liberty',78,112,'chios'],['liberty',120,154,'crusaders'],
 ['liberty',166,205,'raft-medusa'],['liberty',217,253,'parliament'],['liberty',261,295,'wounded'],
 ['liberty',307,345,'third-may'],['liberty',357,394,'charging'],['liberty',402,440,'missolonghi'],['liberty',452,540.916667,'liberty']
];
const tracks=old.tracks.map(t=>({...t,shots:[]}));
const shots=[];const anchors=[
 key(0,[0,Y,39],[0,38,-2],51),key(6.4,[0,Y,39],[0,38,-2],51),
 key(8.8,[0,Y,38.6],[0,39,-2],52),key(13,[0,Y,36],[-15,8.7,-22],58),
 key(18.5,[0,Y,32],[14,8.4,-22],56),key(23,[2.5,Y,31],[23,7.8,-10],59)
];
const artistBio=new Map(old.shots.filter(s=>s.bio).map(s=>[s.artist,s.bio]));const seen=new Set();
for(const [trackId,a,b,id]of windows){
 const t=tracks.find(t=>t.id===trackId),start=snap(t.start+a),end=Math.min(t.end,snap(t.start+b));
 const source=artMap.get(id),native=hung.get(id);assert.equal(source.sha256,native.original_sha256,id+' source changed');
 const first=!seen.has(source.artist);seen.add(source.artist);
 const s={...source,id:trackId+'-'+String(t.shots.length).padStart(2,'0'),asset_id:id,track:trackId,type:'art',
  global_start:start,global_end:end,start:start-t.start,end:end-t.start,seconds:end-start,
  flat_start:snap(start+3),flat_end:snap(end-3),first_artist:first,bio:first?artistBio.get(source.artist)||'':'',
  label_start:snap(start+4.5),label_end:snap(start+11),detail:false};
 shots.push(s);t.shots.push(s);anchors.push(paintingPose(id,start),paintingPose(id,end));
}
assert.equal(new Set(shots.map(s=>s.asset_id)).size,34);
const final=anchors.at(-1);final.at=Math.round(old.duration*FPS);
anchors.sort((a,b)=>a.at-b.at);
function lens(p){const[x,y,z]=p.target.map((v,i)=>v-p.eye[i]);return[Math.atan2(x,-z),Math.atan2(y,Math.hypot(x,z))]}
const segments=[];
for(let i=0;i<anchors.length-1;i++){
 const a=anchors[i],b=anchors[i+1];assert.ok(b.at>a.at,'Repeated camera key');
 const p=route([a.eye[0],a.eye[2]],[b.eye[0],b.eye[2]]),lengths=p.slice(1).map((q,i)=>distance(p[i],q));
 segments.push({a,b,path:p,lengths,length:lengths.reduce((n,x)=>n+x,0)});
}
function pose(frame){
 const s=segments.find(s=>frame<=s.b.at)||segments.at(-1),{a,b}=s;
 const u=Math.max(0,Math.min(1,(frame-a.at)/(b.at-a.at))),turn=ease(u);
 let position=[a.eye[0],a.eye[2]];
 if(s.length>0){
  const d=u*s.length;let sofar=0;
  for(let j=0;j<s.lengths.length;j++){
   const L=s.lengths[j];if(d<=sofar+L||j===s.lengths.length-1){
    const v=L?ease((d-sofar)/L):0;position=s.path[j].map((n,k)=>n+(s.path[j+1][k]-n)*v);break;
   }sofar+=L;
  }
 }
 const eye=[position[0],Y,position[1]],l0=lens(a),l1=lens(b);
 const arc=Math.atan2(Math.sin(l1[0]-l0[0]),Math.cos(l1[0]-l0[0]));
 const yaw=l0[0]+arc*turn,pitch=l0[1]+(l1[1]-l0[1])*turn;
 return{eye,target:[eye[0]+10*Math.sin(yaw)*Math.cos(pitch),eye[1]+10*Math.sin(pitch),eye[2]-10*Math.cos(yaw)*Math.cos(pitch)],fov:a.fov+(b.fov-a.fov)*turn};
}
let previous;const speeds={mps:0,degreesPerSecond:0},N=Math.round(old.duration*FPS);
for(let frame=0;frame<N;frame++){
 const p=pose(frame);assert.ok(free([p.eye[0],p.eye[2]]),'Pedestal / wall clearance at '+frame/FPS+' '+JSON.stringify({p,s:segments.find(s=>frame<=s.b.at)}));
 if(previous){
  speeds.mps=Math.max(speeds.mps,Math.hypot(...p.eye.map((v,i)=>v-previous.eye[i]))*FPS);
  const dot=p.target.reduce((sum,v,i)=>sum+(v-p.eye[i])*(previous.target[i]-previous.eye[i]),0)/100;
  speeds.degreesPerSecond=Math.max(speeds.degreesPerSecond,Math.acos(Math.max(-1,Math.min(1,dot)))*180/Math.PI*FPS);
 }previous=p;
}
assert.ok(speeds.mps<4.75,JSON.stringify(speeds));assert.ok(speeds.degreesPerSecond<31,JSON.stringify(speeds));
const flat=shots.filter(s=>s.asset_id!=='liberty').map(s=>({name:s.asset_id,start:s.flat_start,end:s.flat_end}));
const liberty=tracks.at(-1).start;
flat.push({name:'liberty',start:snap(liberty+455),end:snap(liberty+477)},
 {name:'liberty-detail',start:snap(liberty+477),end:snap(liberty+512)},
 {name:'liberty',start:snap(liberty+512),end:snap(liberty+538)});
const parent=path.resolve(OLD,'../raindrop-romanticism/production');
const inserts=[
 {name:'monastery',kind:'muse',file:path.join(parent,'v2/footage/O02-monastery.mp4'),start:snap(tracks[1].start+29),seconds:8,trim:.45,speed:.91},
 {name:'paris',kind:'muse',file:path.join(parent,'v2/footage/O03-paris.mp4'),start:snap(tracks[3].start+6),seconds:8.5,trim:.25,speed:.94},
 {name:'literary-faces',kind:'public-domain-film',file:path.join(OLD,'footage/mohicans-faces.mp4'),start:snap(tracks[3].start+62),seconds:8,trim:0,speed:1},
 {name:'literary-forest',kind:'public-domain-film',file:path.join(OLD,'footage/mohicans-forest.mp4'),start:snap(tracks[3].start+164),seconds:8,trim:0,speed:1},
 {name:'wanderer-motion',kind:'existing-owner-art-extension',file:path.resolve(OLD,'../../lucas-academy-video/sites/chopin-romanticism-selection/dist/assets/video/wanderer.mp4'),start:snap(tracks[2].start+159),seconds:8,trim:.5,speed:.95}
].map(i=>({...i,end:snap(i.start+i.seconds),fade_in:1.35,fade_out:1.35}));
const chunks=[];for(let first=0;first<N;first+=18*FPS)chunks.push({id:'walk-'+String(chunks.length).padStart(3,'0'),first,count:Math.min(18*FPS,N-first)});
const plan={...old,title:'山海与人间',subtitle:'浪漫主义沙龙漫步',version:3,label_policy:'Simple English above Chinese. Exactly two lines; equal font size in both languages. Artwork title and artist only. Native room labels use bilingual titles.',duration:N/FPS,frames:N,tracks,shots,anchors,flat,chunks,speeds,inserts,
 route_policy:'One continuous collision-checked walk in the existing shared native salon. Fixed camera height; stable painting stops; full original static paintings fade into and back out of the same room pose. Source music is unchanged.',
 reference:'sources/reference-style.json',shared_room_catalog_sha256:createHash('sha256').update(JSON.stringify(catalog)).digest('hex')};
for(const n of['checks','footage/walk','labels','sources','parts','exports'])await mkdir(path.join(ROOT,n),{recursive:true});
await writeFile(path.join(ROOT,'edit-plan.json'),JSON.stringify(plan,null,2));
console.log('ROUTE VALIDATED',shots.length,'works',chunks.length,'chunks',speeds);
if(process.argv.includes('--plan'))process.exit(0);

const url='http://127.0.0.1:8095/?world=museum&room=romanticism-salon&debug&manual=1&hud=0&fullscreen=0';
const browser=await chromium.launch({headless:true,executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',args:['--enable-webgl','--ignore-gpu-blocklist']});
try{
 const page=await browser.newPage({viewport:{width:W,height:H},deviceScaleFactor:1});const errors=[];
 page.on('pageerror',e=>errors.push(e.message));await page.goto(url,{waitUntil:'domcontentloaded',timeout:90000});
 await page.waitForFunction(()=>!!window.__museum,undefined,{timeout:90000});
 let arrived=false;
 for(let i=0;i<150;i++){
  const p=await page.evaluate(()=>__museum.step(1000/30,30));if(p.frameFailure)throw Error(p.frameFailure);
  if(p.room==='romanticism-salon'&&p.transit===null){arrived=true;break}await page.waitForTimeout(80);
 }assert.ok(arrived);
 const plates={};for(const a of art)plates[a.id]='data:image/jpeg;base64,'+(await readFile(a.file)).toString('base64');
 const labels={};for(const s of shots)labels[s.id]='data:image/png;base64,'+(await readFile(path.join(ROOT,'labels',s.id+'.png'))).toString('base64');
 for(const t of tracks)labels[t.id]='data:image/png;base64,'+(await readFile(path.join(ROOT,'labels',t.id+'.png'))).toString('base64');
 const report=await page.evaluate(async({W,H,plates,labels,nativeLabels})=>{
  const module=await import('/src/inception/world/model/museum.js');
  const slot=module.MUSEUM_MANIFEST.portalSlots.find(s=>s.id==='romanticism-salon'),index=module.MUSEUM_MANIFEST.portalSlots.indexOf(slot);
  const world=__museum.world;world.resize(W,H,1);
  await document.fonts.load('36px "Heiti SC"','浪漫主义沙龙');
  const salon=world.romanticismSalonOf(slot.id),audit=[],unmatched=[];
  salon.group.traverse(mesh=>{
   if(mesh.name!=='salon-english-label')return;
   const original=mesh.userData.displayText[0],pair=nativeLabels[original];
   if(!pair){unmatched.push(original);return}
   const texture=mesh.material.map,old=texture.image;
   const canvas=document.createElement('canvas');canvas.width=old.width*2;canvas.height=old.height*2;
   const g=canvas.getContext('2d'),back=!mesh.material.transparent;
   if(back){g.fillStyle='#251f1d';g.fillRect(0,0,canvas.width,canvas.height);g.strokeStyle='#947b54';g.lineWidth=12;g.strokeRect(18,18,canvas.width-36,canvas.height-36)}
   g.fillStyle='#f1dfc3';g.textAlign='center';g.textBaseline='middle';
   let size=Math.max(12,Math.floor(canvas.height/2*.68));
   const face='"Heiti SC", "PingFang SC", sans-serif';
   for(;;){g.font=`${size}px ${face}`;if(Math.max(g.measureText(pair.english).width,g.measureText(pair.chinese).width)<=canvas.width-150||size<=12)break;size--}
   g.fillText(pair.english,canvas.width/2,canvas.height*.25);g.fillText(pair.chinese,canvas.width/2,canvas.height*.75);
   const replacement=new texture.constructor(canvas);
   replacement.colorSpace=texture.colorSpace;replacement.anisotropy=texture.anisotropy;replacement.flipY=texture.flipY;
   replacement.needsUpdate=true;mesh.material.map=replacement;mesh.material.needsUpdate=true;
   mesh.name='salon-bilingual-film-label';mesh.userData.displayText=[pair.english,pair.chinese];
   audit.push({original,english:pair.english,chinese:pair.chinese,font_px_english:size,font_px_chinese:size,english_above_chinese:true});
  });
  if(unmatched.length)throw Error('Native labels missing Chinese: '+JSON.stringify(unmatched));
  const store={};for(const[name,src]of Object.entries(plates)){
   const im=new Image();im.src=src;await im.decode();const stage=new OffscreenCanvas(W,H),g=stage.getContext('2d');
   g.fillStyle='#0c141a';g.fillRect(0,0,W,H);g.imageSmoothingQuality='high';const k=Math.min(1816/im.width,1010/im.height);
   g.drawImage(im,(W-im.width*k)/2,(H-im.height*k)/2,im.width*k,im.height*k);store[name]=stage;
   if(name==='liberty'){
    const detail=new OffscreenCanvas(W,H),d=detail.getContext('2d');d.fillStyle='#0c141a';d.fillRect(0,0,W,H);d.imageSmoothingQuality='high';
    const sw=im.width*.66,sh=im.height*.35,f=Math.min(1816/sw,1010/sh);d.drawImage(im,im.width*.22,0,sw,sh,(W-sw*f)/2,(H-sh*f)/2,sw*f,sh*f);store['liberty-detail']=detail;
   }
  }
  const cards={};for(const[name,src]of Object.entries(labels)){const im=new Image();im.src=src;await im.decode();cards[name]=im}
  const canvas=new OffscreenCanvas(W,H);window.musicFilm={center:module.roomCenterFor(slot,index),floor:module.roomFloorY(slot,index),plates:store,cards,canvas,g:canvas.getContext('2d')};
  const actualLabels={english:0,bilingual:0};
  world.scene.traverse(o=>{if(o.name==='salon-english-label')actualLabels.english++;if(o.name==='salon-bilingual-film-label')actualLabels.bilingual++});
  return {...salon.report(),filmLabelLanguage:'en-zh',nativeLabelAudit:audit,actualSceneLabels:actualLabels};
 },{W,H,plates,labels,nativeLabels:labelStyle.native});
 assert.equal(report.works,56);assert.equal(report.sculptures,8);assert.ok(report.dragonLoaded&&!report.failures.length);
 assert.equal(report.nativeLabelAudit.length,70);
 await writeFile(path.join(ROOT,'checks/native-labels.json'),JSON.stringify({capture_only:true,shared_room_code_changed:false,labels:report.nativeLabelAudit},null,2));
 await page.evaluate(({shots,flat,tracks})=>{
  const ease=t=>{t=Math.max(0,Math.min(1,t));return t*t*(3-2*t)};
  window.musicDraw=(p,time,includePlate=true)=>{
   const world=__museum.world,f=window.musicFilm,g=f.g;
   world.camera.fov=p.fov;world.camera.updateProjectionMatrix();world.setWorldTime(time);
   world.setCamera({eye:[f.center.x+p.eye[0],f.floor+p.eye[1],f.center.z+p.eye[2]],target:[f.center.x+p.target[0],f.floor+p.target[1],f.center.z+p.target[2]]});
   const plate=includePlate?flat.find(s=>s.start<=time&&time<s.end):null;
   const alpha=plate?Math.max(0,Math.min(1,(time-plate.start)/1.35,(plate.end-time)/1.35)):0;
   g.globalAlpha=1;g.filter='none';
   if(alpha===1)g.drawImage(f.plates[plate.name],0,0);
   else{world.render();g.filter=`blur(${(6*Math.sin(Math.PI*alpha)).toFixed(2)}px)`;g.drawImage(world.renderer.domElement,0,0);g.filter='none';if(alpha>0){g.globalAlpha=ease(alpha);g.drawImage(f.plates[plate.name],0,0);g.globalAlpha=1}}
   for(const s of shots){if(time<s.label_start||time>=s.label_end)continue;g.globalAlpha=Math.min(1,(time-s.label_start)/.6,(s.label_end-time)/1.5);g.drawImage(f.cards[s.id],0,0);g.globalAlpha=1}
   for(const t of tracks){if(time<t.start||time>=t.start+9||t.id==='rain')continue;g.globalAlpha=Math.min(1,(time-t.start)/.7,(t.start+9-time)/1.5);g.drawImage(f.cards[t.id],0,0);g.globalAlpha=1}
   return f.canvas;
  };
 },{shots,flat,tracks});
 if(process.argv.includes('--qa')){
  const samples=[];
  for(const s of shots){for(const[k,at,plate]of[['room',s.global_start+1.5,false],['painting',s.flat_start+3,true]]){
   const t=snap(at),file=path.join(ROOT,'checks',s.asset_id+'-'+k+'.jpg');
   const jpeg=await page.evaluate(({p,t,plate})=>musicDraw(p,t,plate).convertToBlob({type:'image/jpeg',quality:.88}).then(async b=>new Uint8Array(await b.arrayBuffer()).toBase64()),{p:pose(Math.round(t*FPS)),t,plate});
   await writeFile(file,Buffer.from(jpeg,'base64'));samples.push({id:s.asset_id,kind:k,time:t,file});
  }}
  assert.deepEqual(errors,[]);await writeFile(path.join(ROOT,'checks/route-qa.json'),JSON.stringify({report,speeds,samples,errors},null,2));
  console.log('CAMERA QA READY',samples.length);process.exitCode=0;
 }else{
  const selected=new Set(process.argv.slice(2).filter(x=>!x.startsWith('--')));
  for(const c of chunks){
   if(selected.size&&!selected.has(c.id))continue;
   const file=path.join(ROOT,'footage/walk',c.id+'.mp4');
   if(!process.argv.includes('--recapture')&&await stat(file).then(s=>s.size>10000,()=>false)){console.log('KEPT',c.id);continue}
   const poses=Array.from({length:c.count},(_,i)=>pose(c.first+i));
   const began=Date.now();
   const result=await page.evaluate(async({c,poses,FPS,W,H})=>{
    let failure;const outputs=[];const encoder=new VideoEncoder({output(c){const b=new Uint8Array(c.byteLength);c.copyTo(b);outputs.push(b)},error(e){failure=String(e)}});
    encoder.configure({codec:'avc1.640028',width:W,height:H,bitrate:9_800_000,framerate:FPS,avc:{format:'annexb'}});
    for(let i=0;i<c.count;i++){
     const image=musicDraw(poses[i],(c.first+i)/FPS);
     const frame=new VideoFrame(image,{timestamp:Math.round(i*1e6/FPS),duration:Math.round(1e6/FPS)});
     encoder.encode(frame,{keyFrame:i%48===0});frame.close();
     while(encoder.encodeQueueSize>6&&!failure)await new Promise(r=>setTimeout(r,2));if(failure)throw Error(failure);
    }await encoder.flush();encoder.close();if(failure)throw Error(failure);
    const data=new Uint8Array(outputs.reduce((n,b)=>n+b.length,0));let offset=0;for(const b of outputs){data.set(b,offset);offset+=b.length}return data.toBase64();
   },{c,poses,FPS,W,H});
   const raw=file+'.h264',pending=file+'.pending.mp4';await writeFile(raw,Buffer.from(result,'base64'));
   const mux=spawn('/opt/homebrew/bin/ffmpeg',['-v','error','-y','-fflags','+genpts','-r','24','-i',raw,'-c:v','copy',pending],{stdio:['ignore','ignore','inherit']});
   assert.equal((await once(mux,'exit'))[0],0);await rename(pending,file);await unlink(raw);
   console.log('RECORDED',c.id,(c.first/FPS).toFixed(2),(c.count/FPS).toFixed(2),'in',((Date.now()-began)/1000).toFixed(1)+'s');
  }
  assert.deepEqual(errors,[]);await writeFile(path.join(ROOT,'checks/capture-result.json'),JSON.stringify({report,speeds,errors,frames:N,chunks:chunks.length},null,2));console.log('CAPTURE COMPLETE');
 }
}finally{await browser.close()}
