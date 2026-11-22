import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
import {readFile,writeFile,stat,rename,unlink} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {spawn} from 'node:child_process';
import {once} from 'node:events';
import path from 'node:path';
import {pathToFileURL} from 'node:url';

const ROOT=path.resolve(import.meta.dirname,'..');
const plan=JSON.parse(await readFile(path.join(ROOT,'edit-plan.json'),'utf8'));
const UI=plan.source_repository;
for(const [file,sha]of Object.entries(plan.source_snapshot)){
 assert.equal(createHash('sha256').update(await readFile(path.join(UI,file))).digest('hex'),sha,'Latest IS files changed after planning: '+file);
}
const {romanticismHangingPlan,romanticismPedestalObstacles}=await import(pathToFileURL(path.join(UI,'src/inception/world/rooms/romanticismLayout.js')));
const catalog=JSON.parse(await readFile(path.join(UI,'content/inception/artworks/romanticism-salon-v1.json'),'utf8'));
const hanging=romanticismHangingPlan(catalog.works),hung=new Map(hanging.map(a=>[a.id,a]));
const first=hung.get('wanderer'),second=hung.get('chalk-cliffs');
assert.equal(first.wallId,'nature');assert.equal(second.wallId,'nature');
const W=plan.width,H=plan.height,FPS=plan.fps;
const ease=t=>{t=Math.max(0,Math.min(1,t));return t*t*(3-2*t)};
const surface=(work,u=.5,v=.5)=>[work.position[0]+.225,work.position[1]+(.5-v)*work.height,work.position[2]-(u-.5)*work.width];
const eyeFor=work=>[work.position[0]+6.4,work.position[1],work.position[2]];
const firstEye=eyeFor(first),secondEye=eyeFor(second),midZ=(first.position[2]+second.position[2])/2;
const start=[-18,4.05,15.5];
const anchors=[
 {t:0,eye:start,target:[-27.375,9,-12],fov:64},
 {t:1,eye:start,target:[-27.375,7,-14],fov:62},
 {t:12,eye:firstEye,target:surface(first),fov:52},
 {t:17.5,eye:firstEye,target:surface(first),fov:52},
 {t:23.5,eye:firstEye,target:surface(first,.52,.60),fov:24},
 {t:24.5,eye:firstEye,target:surface(first,.52,.60),fov:24},
 {t:27,eye:firstEye,target:surface(first),fov:52},
 {t:33,eye:secondEye,target:surface(second),fov:52},
 {t:38.7,eye:secondEye,target:surface(second),fov:52},
 {t:46,eye:secondEye,target:surface(second,.52,.63),fov:24},
 {t:49,eye:secondEye,target:surface(second,.52,.63),fov:24},
 {t:55,eye:[-11,4.45,midZ],target:[first.position[0]+.225,4.45,midZ],fov:60},
 {t:58,eye:[-11,4.45,midZ],target:[first.position[0]+.225,4.45,midZ],fov:60},
];
function pose(time){
 const i=anchors.findIndex((b,i)=>i>0&&time<=b.t),b=anchors[i<0?anchors.length-1:i],a=anchors[i<0?anchors.length-2:i-1];
 const u=ease((time-a.t)/(b.t-a.t));
 return{eye:a.eye.map((v,i)=>v+(b.eye[i]-v)*u),target:a.target.map((v,i)=>v+(b.target[i]-v)*u),fov:a.fov+(b.fov-a.fov)*u};
}
const obstacles=romanticismPedestalObstacles().map(o=>({...o,x0:o.x0-.65,x1:o.x1+.65,z0:o.z0-.65,z1:o.z1+.65}));
let previous,maxMps=0,maxDegrees=0;
for(let frame=0;frame<plan.frames;frame++){
 const p=pose(frame/FPS);
 assert.ok(Math.abs(p.eye[0])<26.3&&Math.abs(p.eye[2])<41,'Wall collision');
 assert.ok(!obstacles.some(o=>p.eye[0]>=o.x0&&p.eye[0]<=o.x1&&p.eye[2]>=o.z0&&p.eye[2]<=o.z1&&p.eye[1]<o.y1),'Pedestal clearance at '+frame/FPS);
 if(previous){
  maxMps=Math.max(maxMps,Math.hypot(...p.eye.map((v,i)=>v-previous.eye[i]))*FPS);
  const direction=p.target.map((v,i)=>v-p.eye[i]),prior=previous.target.map((v,i)=>v-previous.eye[i]);
  const dot=direction.reduce((n,v,i)=>n+v*prior[i],0)/(Math.hypot(...direction)*Math.hypot(...prior));
  maxDegrees=Math.max(maxDegrees,Math.acos(Math.max(-1,Math.min(1,dot)))*180/Math.PI*FPS);
 }
 previous=p;
}
assert.ok(maxMps<4.8,{maxMps});assert.ok(maxDegrees<32,{maxDegrees});
await writeFile(path.join(ROOT,'checks/camera-plan.json'),JSON.stringify({anchors,maxMps,maxDegrees,works:[first,second],source_snapshot:plan.source_snapshot},null,2));
console.log('PORTRAIT ROUTE VALIDATED',JSON.stringify({maxMps,maxDegrees,frames:plan.frames}));

const require=createRequire('@RUNTIME_DEPS@/node/package.json');
const {chromium}=require('playwright');
const browser=await chromium.launch({headless:true,executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',args:['--enable-webgl','--ignore-gpu-blocklist']});
try{
 const page=await browser.newPage({viewport:{width:W,height:H},deviceScaleFactor:1});
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('http://127.0.0.1:8095/?world=museum&room=romanticism-salon&debug&manual=1&hud=0&fullscreen=0',{waitUntil:'domcontentloaded',timeout:90000});
 await page.waitForFunction(()=>!!window.__museum,undefined,{timeout:90000});
 let arrived=false;
 for(let i=0;i<180;i++){
  const state=await page.evaluate(()=>__museum.step(1000/30,30));
  if(state.frameFailure)throw Error(state.frameFailure);
  if(state.room==='romanticism-salon'&&state.transit===null){arrived=true;break}
  await page.waitForTimeout(60);
 }
 assert.ok(arrived,'The current native salon did not load');
 const images={};for(const work of plan.artworks)images[work.id]='data:image/jpeg;base64,'+(await readFile(work.file)).toString('base64');
 const labels={};for(const cue of plan.labels)labels[cue.id]='data:image/png;base64,'+(await readFile(path.join(ROOT,'labels',cue.id+'.png'))).toString('base64');
 const report=await page.evaluate(async({W,H,images,labels,cues})=>{
  const module=await import('/src/inception/world/model/museum.js');
  const slot=module.MUSEUM_MANIFEST.portalSlots.find(s=>s.id==='romanticism-salon'),index=module.MUSEUM_MANIFEST.portalSlots.indexOf(slot);
  const world=__museum.world;world.resize(W,H,1);
  const salon=world.romanticismSalonOf(slot.id),nativeLabels=[];
  await document.fonts.load('38px "Heiti SC"','Caspar David Friedrich');
  salon.group.traverse(mesh=>{
   if(mesh.name!=='salon-english-label')return;
   const text=mesh.userData.displayText[0];
   if(/[\u3400-\u9fff]/.test(text))throw Error('Unexpected non-English native label: '+text);
   const old=mesh.material.map,canvas=document.createElement('canvas');
   canvas.width=old.image.width*2;canvas.height=old.image.height*2;
   const g=canvas.getContext('2d');
   if(!mesh.material.transparent){g.fillStyle='#251f1d';g.fillRect(0,0,canvas.width,canvas.height);g.strokeStyle='#947b54';g.lineWidth=12;g.strokeRect(18,18,canvas.width-36,canvas.height-36)}
   let size=Math.floor(canvas.height*.63);
   do{g.font=size+'px "Heiti SC", sans-serif';if(g.measureText(text).width<canvas.width-130)break;size--}while(size>12);
   g.fillStyle='#f1dfc3';g.textAlign='center';g.textBaseline='middle';g.fillText(text,canvas.width/2,canvas.height/2);
   const texture=new old.constructor(canvas);texture.colorSpace=old.colorSpace;texture.anisotropy=old.anisotropy;texture.flipY=old.flipY;texture.needsUpdate=true;
   mesh.material.map=texture;mesh.material.needsUpdate=true;mesh.userData.displayText=[text];
   const useOverlay=['Wanderer above the Sea of Fog','Chalk Cliffs on Rugen'].includes(text);
   if(useOverlay)mesh.visible=false;
   nativeLabels.push({text,font_px:size,useOverlay});
  });
  const upgraded=[];
  for(const[id,src]of Object.entries(images)){
   const image=new Image();image.src=src;await image.decode();
   const mesh=salon.group.getObjectByName('romanticism-art-'+id);if(!mesh)throw Error('Missing native artwork '+id);
   const old=mesh.material.map,texture=new old.constructor(image);
   texture.colorSpace=old.colorSpace;texture.flipY=old.flipY;texture.anisotropy=8;texture.needsUpdate=true;
   mesh.material.map=texture;mesh.material.needsUpdate=true;
   upgraded.push({id,width:image.width,height:image.height});
  }
  const cards={};for(const[id,src]of Object.entries(labels)){const image=new Image();image.src=src;await image.decode();cards[id]=image}
  const canvas=new OffscreenCanvas(W,H),g=canvas.getContext('2d');
  const center=module.roomCenterFor(slot,index),floor=module.roomFloorY(slot,index);
  window.shortState={center,floor,canvas,cards};
  window.drawShort=(p,time,includeLabels=true)=>{
   world.camera.fov=p.fov;world.camera.updateProjectionMatrix();world.setWorldTime(time);
   world.setCamera({eye:[center.x+p.eye[0],floor+p.eye[1],center.z+p.eye[2]],target:[center.x+p.target[0],floor+p.target[1],center.z+p.target[2]]});
   world.render();g.globalAlpha=1;g.drawImage(world.renderer.domElement,0,0);
   if(includeLabels)for(const cue of cues){
    if(time<cue.start||time>=cue.end)continue;
    g.globalAlpha=Math.max(0,Math.min(1,(time-cue.start)/.5,(cue.end-time)/.65));g.drawImage(cards[cue.id],0,0);g.globalAlpha=1;
   }
   const darkness=Math.max(0,1-time/.35,(time-57.15)/.85);
   if(darkness>0){g.globalAlpha=Math.min(1,darkness);g.fillStyle='#000';g.fillRect(0,0,W,H);g.globalAlpha=1}
   return canvas;
  };
  return {...salon.report(),nativeLabels,portrait:[W,H],upgraded,renderSource:'Current IS source; native scene modified only in this capture session.'};
 },{W,H,images,labels,cues:plan.labels});
 assert.equal(report.works,56);assert.equal(report.sculptures,8);assert.ok(report.dragonLoaded&&!report.failures.length);assert.equal(report.nativeLabels.length,70);
 const sampleTimes=[2,7,14,20.5,28.5,35,44,54.5,56];
 const samples=[];
 for(const t of sampleTimes){
  const jpeg=await page.evaluate(({p,t})=>drawShort(p,t).convertToBlob({type:'image/jpeg',quality:.9}).then(async b=>new Uint8Array(await b.arrayBuffer()).toBase64()),{p:pose(t),t});
  const file=path.join(ROOT,'checks',`frame-${String(t).replace('.','_')}.jpg`);await writeFile(file,Buffer.from(jpeg,'base64'));samples.push({time:t,file});
 }
 const framing=[];
 for(const [work,t]of [[first,14],[second,35]]){
  framing.push(await page.evaluate(({p,t,id})=>{
   drawShort(p,t,false);const mesh=__museum.world.romanticismSalonOf('romanticism-salon').group.getObjectByName('romanticism-art-'+id);
   const {width,height}=mesh.geometry.parameters,corners=[];
   for(const x of [-width/2,width/2])for(const y of [-height/2,height/2]){
    const v=__museum.world.camera.position.clone().set(x,y,0);mesh.localToWorld(v);v.project(__museum.world.camera);corners.push([v.x,v.y,v.z]);
   }
   return{id,time:t,corners,fullPaintingVisible:corners.every(v=>Math.abs(v[0])<.96&&Math.abs(v[1])<.85&&v[2]>-1&&v[2]<1)};
  },{p:pose(t),t,id:work.id}));
 }
 assert.ok(framing.every(x=>x.fullPaintingVisible),JSON.stringify(framing));
 await writeFile(path.join(ROOT,'checks/scene-qa.json'),JSON.stringify({report,samples,framing,errors,maxMps,maxDegrees},null,2));
 console.log('LATEST SALON QA READY',samples.length,'portrait frames',report.nativeLabels.length,'English signs');
 if(process.argv.includes('--qa'))process.exitCode=0;
 else{
  const chunks=[];for(let first=0;first<plan.frames;first+=12*FPS)chunks.push({id:'shot-'+String(chunks.length).padStart(2,'0'),first,count:Math.min(12*FPS,plan.frames-first)});
  for(const chunk of chunks){
   const file=path.join(ROOT,'footage',chunk.id+'.mp4');
   if(!process.argv.includes('--recapture')&&await stat(file).then(s=>s.size>1000,()=>false)){console.log('KEPT',chunk.id);continue}
   const poses=Array.from({length:chunk.count},(_,i)=>pose((chunk.first+i)/FPS));
   const result=await page.evaluate(async({chunk,poses,W,H,FPS})=>{
    let failure;const buffers=[];
    const encoder=new VideoEncoder({output(c){const b=new Uint8Array(c.byteLength);c.copyTo(b);buffers.push(b)},error(e){failure=String(e)}});
    encoder.configure({codec:'avc1.640028',width:W,height:H,bitrate:11_000_000,framerate:FPS,avc:{format:'annexb'}});
    for(let i=0;i<chunk.count;i++){
     const image=drawShort(poses[i],(chunk.first+i)/FPS);
     const frame=new VideoFrame(image,{timestamp:Math.round(i*1e6/FPS),duration:Math.round(1e6/FPS)});
     encoder.encode(frame,{keyFrame:i%48===0});frame.close();
     while(encoder.encodeQueueSize>6&&!failure)await new Promise(r=>setTimeout(r,2));if(failure)throw Error(failure);
    }
    await encoder.flush();encoder.close();if(failure)throw Error(failure);
    const data=new Uint8Array(buffers.reduce((n,b)=>n+b.length,0));let at=0;for(const b of buffers){data.set(b,at);at+=b.length}return data.toBase64();
   },{chunk,poses,W,H,FPS});
   const raw=file+'.h264',pending=file+'.pending.mp4';await writeFile(raw,Buffer.from(result,'base64'));
   const ff=spawn('/opt/homebrew/bin/ffmpeg',['-v','error','-y','-fflags','+genpts','-r',String(FPS),'-i',raw,'-c:v','copy',pending],{stdio:['ignore','ignore','inherit']});
   assert.equal((await once(ff,'exit'))[0],0);await rename(pending,file);await unlink(raw);console.log('CAPTURED',chunk.id,chunk.count,'frames');
  }
  await writeFile(path.join(ROOT,'checks/capture-result.json'),JSON.stringify({report,chunks,frames:plan.frames,source_snapshot:plan.source_snapshot,errors},null,2));
 }
 assert.deepEqual(errors,[]);
}finally{await browser.close()}
