const {chromium}=require('/Users/yqin/repo/ai-testing/node_modules/playwright');
const {spawn}=require('node:child_process');
const {once}=require('node:events');
const fs=require('node:fs');
const ROOT='/Users/yqin/repo/playground/lucas-academy-video-data/curiosity-builds-20261118/v2';
const BASE='http://127.0.0.1:5190';
const FPS=30;
async function step(p,n=1,intent={}){return p.evaluate(({n,intent})=>window.__museum.step(1000/30,n,intent.up||false,intent.forward||0,intent.strafe||0,intent.yaw||0,intent.pitch||0),{n,intent});}
async function skip(p,sec){for(let i=0;i<Math.ceil(sec*2);i++){await step(p,15);await p.waitForTimeout(12);}}
async function status(p){return p.locator('#inception-status').textContent();}
async function until(p,re,max=200){for(let i=0;i<max*4;i++){if(re.test(await status(p)))return;await step(p,7);await p.waitForTimeout(8);}throw Error('Did not reach '+re);}
async function record(p,name,seconds,intent=()=>({}),camera=null,controls={}){const file=ROOT+'/captures/'+name+'.mp4';
 const enc=spawn('ffmpeg',['-y','-loglevel','error','-f','image2pipe','-framerate','30','-vcodec','mjpeg','-i','pipe:0','-an','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',file],{stdio:['pipe','inherit','inherit']});
 const start=await p.evaluate(()=>window.__museum.probe());
 if(start.transit)throw Error('Refusing to record an unfinished room load: '+JSON.stringify(start));
 let carry=0;
 for(let f=0;f<Math.round(seconds*FPS);f++){if(controls.before)await controls.before(p,f/FPS,f);carry+=controls.speed?controls.speed(f/FPS):1;const n=Math.floor(carry);carry-=n;await step(p,n,intent(f/FPS));if(camera)await p.evaluate(pose=>{window.__museum.world.setCamera(pose);window.__museum.world.avatarRoot.visible=false;window.__museum.world.render();},camera(f/FPS));const jpg=await p.screenshot({type:'jpeg',quality:92});if(!enc.stdin.write(jpg))await once(enc.stdin,'drain');if(f%120===0)console.log(name+': '+f+'/'+seconds*FPS);}
 enc.stdin.end();const [code]=await once(enc,'exit');if(code)throw Error('Encoding failed '+name);
 const end=await p.evaluate(()=>window.__museum.probe());if(end.frameFailure)throw Error(end.frameFailure);
 fs.writeFileSync(ROOT+'/records/'+name+'.json',JSON.stringify({name,url:p.url(),fps:FPS,seconds,mode:'Actual project renderer, first-person, native manual frame clock; scripted camera input',start,end},null,2));
 await p.screenshot({path:ROOT+'/records/'+name+'.jpg',type:'jpeg',quality:90});console.log('Saved '+file);
}
async function setup(p,url){await p.goto(BASE+url,{waitUntil:'domcontentloaded',timeout:60000});await p.waitForFunction(()=>!!window.__museum,null,{timeout:120000});await skip(p,18);const wanted=new URL(BASE+url).searchParams.get('room');for(let i=0;i<420;i++){const s=await step(p,15);if(s.room===wanted&&!s.transit){await skip(p,.5);return;}await p.waitForTimeout(50);}throw Error('Room did not finish loading: '+wanted);}
module.exports={record,setup,step,skip,until,status,BASE,ROOT};
if(require.main===module)(async()=>{const mode=process.argv[2]||'roller';const b=await chromium.connectOverCDP('http://127.0.0.1:9238');const p=await b.contexts()[0].newPage();
 const errors=[];p.on('pageerror',e=>{errors.push(e.message);console.error('Page error:',e.message)});p.on('console',m=>{if(m.type()==='error')console.error(m.text().slice(0,600))});
 if(mode==='roller'){
  await p.goto(BASE+'/tour?start=manifold&debug&manual=1&hud=0&fullscreen=0',{waitUntil:'networkidle'});
  await p.evaluate(()=>{for(const k of ['narration','backgroundMusic','subtitles']){const e=document.querySelector(`[data-tour-toggle="${k}"]`);if(e?.getAttribute('aria-pressed')==='true')e.click();}});
  await p.locator('[data-ride]').click();await p.waitForFunction(()=>!!window.__museum,null,{timeout:120000});
  await until(p,/y = kx — .*speed/);await record(p,'roller-line',4);
  await until(p,/Parabola — .*speed/);await record(p,'roller-parabola',5);
  await until(p,/Golden Funnel — .*speed/);await record(p,'roller-funnel',14);
  await until(p,/Möbius — Lap/);await record(p,'roller-mobius',6);
 } else if(mode==='chess'){
  await setup(p,'/?world=museum&room=chess-room-1&debug&manual=1&hud=0&fullscreen=0');await p.keyboard.press('v');await step(p);
  await record(p,'chess-room',8,t=>({forward:t<2?.2:0,yaw:Math.sin(t*.7)*.002,pitch:t<1?.001:0}));
 } else if(mode==='sky'){
  await setup(p,'/?world=museum&room=room-b&debug&manual=1&hud=0&fullscreen=0');await p.keyboard.press('v');await step(p);
  const c=await p.evaluate(async()=>{const m=await import('/src/inception/world/model/museum.js');const a=m.MUSEUM_MANIFEST.portalSlots;const i=a.findIndex(x=>x.id==='room-b');return {...m.roomCenterFor(a[i],i),floor:window.__museum.probe().floorY};});
  await record(p,'sky-room',18,()=>({}),t=>{const a=t*.045;return {eye:[c.x+Math.sin(a)*10,c.floor+7+t*.15,c.z+Math.cos(a)*10],target:[c.x,c.floor+Math.max(0,t-10)*1.5,c.z],up:[0,1,0]}});
 } else if(mode==='vangogh'){
  await setup(p,'/?world=museum&room=room-a&debug&manual=1&hud=0&fullscreen=0');await p.keyboard.press('v');await step(p);
  for(let i=0;i<90;i++){const s=await step(p,15,{forward:1});await p.waitForTimeout(15);if(!s.connector)break;}
  await skip(p,2);
  const c=await p.evaluate(async()=>{const m=await import('/src/inception/world/model/museum.js');const a=m.MUSEUM_MANIFEST.portalSlots;const i=a.findIndex(x=>x.id==='room-a');return {...m.roomCenterFor(a[i],i),floor:window.__museum.probe().floorY};});
  await record(p,'vangogh-room',20,()=>({}),t=>({eye:[c.x+3-t*.1,c.floor+2.5,c.z+5],target:[c.x-2+t*.18,c.floor+3.4,c.z-1],up:[0,1,0]}));
 } else if(mode==='journey'){
  await setup(p,'/?world=museum&room=the-art-of-progression&debug&manual=1&hud=0&fullscreen=0');await p.keyboard.press('v');await step(p);
  const center=await p.evaluate(async()=>{const r=await import('/src/inception/tour/journeyOfArtTour.js');return r.toWorld([0,0,0]);});
  console.log('Gallery coordinates',center);
  const pose=(at,look)=>({eye:at.map((v,i)=>v+center[['x','y','z'][i]]),target:look.map((v,i)=>v+center[['x','y','z'][i]]),up:[0,1,0]});
  await record(p,'journey-gallery',12,()=>({}),t=>pose([-18.5+.3*t/12,0,3.3],[-12.65,0,2.8]));
  await record(p,'journey-portraits',8,()=>({}),t=>pose([8.9,-.4,-5.6],[17.06-5.33*t/8,-.9,-6.49-1.18*t/8]));
 }
 fs.writeFileSync(ROOT+'/records/'+mode+'-errors.json',JSON.stringify(errors,null,2));await p.close();await b.close();
})().catch(e=>{console.error(e);process.exit(1)});
