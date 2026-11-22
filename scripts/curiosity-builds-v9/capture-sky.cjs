/** One uninterrupted native Sky take, including the project's real transition. */
const {chromium}=require('/Users/yqin/repo/ai-testing/node_modules/playwright');
const {spawn}=require('node:child_process');const {once}=require('node:events');const fs=require('node:fs');
const ROOT='/Users/yqin/repo/playground/lucas-academy-video-data/curiosity-builds-20261118/v9';
const NAME='sky-continuous-cosmic-cliffs',FPS=30,SECONDS=25;
const clamp=x=>Math.max(0,Math.min(1,x));const smooth=x=>{x=clamp(x);return x*x*(3-2*x)};const blend=(a,b,t)=>a.map((v,i)=>v+(b[i]-v)*t);
(async()=>{
 const browser=await chromium.connectOverCDP('http://127.0.0.1:9238');const page=await browser.contexts()[0].newPage();const errors=[];
 page.on('pageerror',e=>{errors.push(e.message);console.error('Page error:',e.message)});
 await page.route('**/0e6000333bc61bea1005c1a82589572bdc0d1927be5fb0b0393512044718df2c-background10.jpg',r=>r.fulfill({path:'/Users/yqin/repo/playground/sky-panorama-lab/out/background10.jpg',contentType:'image/jpeg'}));
 await page.goto('http://127.0.0.1:5192/?world=museum&room=room-b&debug&manual=1&hud=0&fullscreen=0',{waitUntil:'domcontentloaded',timeout:60000});
 await page.waitForFunction(()=>!!window.__museum,null,{timeout:120000});await page.keyboard.press('v');
 await page.addStyleTag({content:'#inception-status,button{visibility:hidden!important}'});
 await page.evaluate(()=>{const w=window.__museum.world;const actual=w.setSkyVariant.bind(w);w.setSkyVariant=()=>actual('cosmic-cliffs');w.setSkyVariant('cosmic-cliffs');});
 await page.waitForFunction(()=>window.__museum.world.skyTextures.has('cosmic-cliffs'),null,{timeout:120000});
 const center=await page.evaluate(async()=>{const m=await import('/src/inception/world/model/museum.js'),slots=m.MUSEUM_MANIFEST.portalSlots,i=slots.findIndex(x=>x.id==='room-b');return m.roomCenterFor(slots[i],i)});
 // Omit loading stalls; begin at the first native approach frame. No camera teleport or cut is added.
 for(let i=0;i<400;i++){const s=await page.evaluate(()=>window.__museum.step(1000/30,1));if(s.transit==='approach')break;if(!s.transit)throw Error('Missed transit');await page.waitForTimeout(20);if(i===399)throw Error('Sky room did not load');}
 await page.evaluate(()=>window.__museum.world.settleSkyFade());
 const encoder=spawn('ffmpeg',['-y','-loglevel','error','-f','image2pipe','-framerate',String(FPS),'-vcodec','mjpeg','-i','pipe:0','-an','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',ROOT+'/captures/'+NAME+'.mp4'],{stdio:['pipe','inherit','inherit']});
 const samples=[];let entry=null,entryFrame=null,carry=0;
 for(let frame=0;frame<SECONDS*FPS;frame++){
  carry+=entry?1:.5;const n=Math.floor(carry);carry-=n;
  const native=await page.evaluate(n=>{const s=window.__museum.step(1000/30,n),w=window.__museum.world;return {probe:s,eye:w.camera.position.toArray(),direction:w.camera.getWorldDirection(w.camera.position.clone()).toArray()}},n);
  if(native.probe.frameFailure)throw Error(native.probe.frameFailure);
  if(!entry&&!native.probe.transit){if(native.probe.room!=='room-b')throw Error('Wrong destination');entry=native;entryFrame=frame;console.log('Entered Sky at frame '+frame);}
  let pose=null;
  if(entry){
   const t=(frame-entryFrame)/FPS;const floor=entry.probe.floorY;const radius0=Math.hypot(entry.eye[0]-center.x,entry.eye[2]-center.z);
   const a0=Math.atan2(entry.eye[0]-center.x,entry.eye[2]-center.z);const angle=a0+.32*(t-1.1*(1-Math.exp(-t/1.1)));
   const radius=radius0+(7.2-radius0)*smooth(t/8);const height=entry.eye[1]+(floor+14.5-entry.eye[1])*smooth(t/16);
   const entryTarget=entry.eye.map((v,i)=>v+entry.direction[i]*10);const target=blend(entryTarget,[center.x,floor+.6,center.z],smooth(t/4));
   pose={eye:[center.x+Math.sin(angle)*radius,height,center.z+Math.cos(angle)*radius],target,up:[0,1,0]};
   await page.evaluate(pose=>{const w=window.__museum.world;w.setCamera(pose);w.avatarRoot.visible=false;w.render()},pose);
  }else await page.evaluate(()=>{const w=window.__museum.world;w.avatarRoot.visible=false;w.render()});
  const jpg=await page.screenshot({type:'jpeg',quality:92});if(!encoder.stdin.write(jpg))await once(encoder.stdin,'drain');
  if(frame%15===0)samples.push({frame,seconds:frame/FPS,phase:entry?((frame-entryFrame)/FPS<16?'ascending-orbit':'hover-downward-orbit'):'native-transition',probe:native.probe,pose});
  if(frame%120===0){console.log(NAME+' '+frame+'/'+SECONDS*FPS);await page.screenshot({path:ROOT+'/records/sky-continuous-'+frame+'.jpg',type:'jpeg',quality:90});}
 }
 encoder.stdin.end();const [code]=await once(encoder,'exit');if(code)throw Error('Encoder failed');
 const final=await page.evaluate(()=>({probe:window.__museum.probe(),skyVariant:window.__museum.world.skyVariant}));
 if(errors.length)throw Error(errors.join('\n'));if(final.skyVariant!=='cosmic-cliffs')throw Error('Sky changed');
 const proof={name:NAME,seconds:SECONDS,fps:FPS,frames:SECONDS*FPS,variant:final.skyVariant,one_continuous_take:true,editorial_cuts:0,native_transition_included:true,entry_frame:entryFrame,ascending_seconds:16,hover_seconds:SECONDS-entryFrame/FPS-16,final_height_above_floor:14.5,full_viewport:true,application_source_changed:false,panorama:'/Users/yqin/repo/playground/sky-panorama-lab/out/background10.jpg',center,errors,samples,final};
 fs.writeFileSync(ROOT+'/records/sky-continuous.json',JSON.stringify(proof,null,2)+'\n');
 fs.writeFileSync(ROOT+'/records/cosmic-cliffs.json',JSON.stringify({variant:final.skyVariant,room:'room-b',loaded:true,panorama:proof.panorama,productionChanged:false},null,2)+'\n');
 console.log('Saved continuous take, entry '+entryFrame/FPS+' s; hover '+proof.hover_seconds+' s.');await page.close();await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
