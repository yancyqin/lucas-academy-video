// The Wild: clean browser footage, with no titles, narration or prompt overlays.
// Uses the published build's supported manual clock for exact 30 fps action
// takes. The touch take runs in real time and uses actual Chrome touch input.
// No game source, physics, scenery, lights, or saved production data is changed.
// Future repo destination, after owner review: scripts/wild/capture.mjs.
import {createRequire} from 'node:module';
import {spawn, spawnSync} from 'node:child_process';
import {mkdirSync, writeFileSync, readFileSync, existsSync} from 'node:fs';
import {dirname, resolve, join} from 'node:path';
import {fileURLToPath} from 'node:url';
import {once} from 'node:events';
import {createHash} from 'node:crypto';

const HERE=dirname(fileURLToPath(import.meta.url));
const flag=(name,fallback)=>{const at=process.argv.indexOf('--'+name);return at<0?fallback:process.argv[at+1]};
const OUT=resolve(flag('out',HERE));
const ONLY=flag('only','');
const BASE=flag('url','https://is.lucasacademy.org/wild/');
const runtime=process.env.PLAYWRIGHT_DIR||'/tmp/inception-pr135-browser/node_modules/playwright';
const {chromium}=createRequire(join(runtime,'package.json'))('playwright');
const FPS=30, WIDTH=1920, HEIGHT=1080;
mkdirSync(join(OUT,'takes'),{recursive:true});
mkdirSync(join(OUT,'stills'),{recursive:true});
mkdirSync(join(OUT,'source'),{recursive:true});
const errors=[];
const manifest={schema:'wild-browser-footage/1',sourceUrl:BASE,sourceCommit:'80031829439353e2fc6824ddfc442fd1e8d55944',
  captureDate:'2026-11-07',width:WIDTH,height:HEIGHT,fps:FPS,audio:false,addedText:false,promptOverlay:false,
  reconstructedPrompt:'reconstructed-prompt.en.txt',promptStatus:'Original deleted; separate approximate draft authorized by owner.',
  method:'Exact 1/30-second manual game steps for action/region takes; real-time Playwright recording and actual multitouch for touch take.',
  captureOnlyCss:'Hide loading overlay, temporary controls hint, transient region heading and debug statistics. Keep actual stamina, quality and touch controls.',
  repositoryStatus:'Awaiting owner video review before submission to lucas-academy-video.',takes:[],errors};
const save=()=>{
  manifest.takes.sort((a,b)=>a.id.localeCompare(b.id));
  writeFileSync(join(OUT,'capture-manifest.json'),JSON.stringify(manifest,null,2)+'\n');
};
if(ONLY&&existsSync(join(OUT,'capture-manifest.json'))){
  const previous=JSON.parse(readFileSync(join(OUT,'capture-manifest.json'),'utf8'));
  manifest.takes=previous.takes.filter(t=>!ONLY.split(',').includes(t.id));
}
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const browser=await chromium.launch({channel:'chrome',headless:true,args:['--use-angle=metal','--enable-gpu','--ignore-gpu-blocklist']});
const ctx=await browser.newContext({viewport:{width:WIDTH,height:HEIGHT},deviceScaleFactor:1});
const page=await ctx.newPage();
page.on('pageerror',e=>errors.push(e.message));
page.on('console',m=>{if(m.type()==='error')errors.push(m.text())});
const css='#loading,.hint,.region,.stats{display:none!important}';

const shots=[
  {id:'01-walk-sprint-jump-glide',duration:14,setup:{x:30,z:366,yaw:Math.PI,pitch:.2},
   intent:(f,t)=>({stickY:t>=1?1:0,sprint:t>=4&&t<6,jump:f===180||f===188,lookX:t>8?Math.sin((t-8)*.5)*.0013:0})},
  {id:'02-climb-lunge-mantle',duration:8,setup:{x:35,z:328,yaw:0,pitch:.16},prime:{stickY:1},
   intent:(f,t,p)=>({stickY:1,jump:(f===40||f===80)&&p.mode==='climb'})},
  {id:'03-swim-coast',duration:5,setup:{x:790,z:410,yaw:Math.PI/2,pitch:.24},
   intent:(f,t)=>({stickY:.8,lookX:.002})},
  {id:'04-whispering-forest',duration:5,setup:{x:-560,z:20,yaw:Math.PI,pitch:.16},
   intent:(f,t)=>({stickY:.5,lookX:.0022})},
  {id:'05-frost-peaks',duration:5,setup:{x:192,z:-474,yaw:-.4,pitch:.36},
   intent:(f,t)=>({lookX:.003})},
  {id:'06-sunset-dunes',duration:5,setup:{x:580,z:240,yaw:-.8,pitch:.16},
   intent:(f,t)=>({stickY:.55,lookX:.002})},
  {id:'07-quality-low-medium-high',duration:5,setup:{x:-560,z:20,yaw:Math.PI,pitch:.18},
   intent:()=>({}),qualityAt:{30:'low',75:'medium',120:'high'}},
];

async function position(p,shot){
  await p.evaluate(s=>{
    const d=window.__wild,w=d.world;
    d.teleport(s.x,s.z,s.y);
    Object.assign(w.player,{yaw:s.yaw,stamina:1,exhausted:false,rest:1,airTime:0,lunge:0,events:[]});
    Object.assign(w.follow,{yaw:s.yaw,pitch:s.pitch,started:false,idle:0});
  },shot.setup);
}

async function warm(shot){
  await position(page,shot);
  for(let i=0;i<220;i++){
    await page.evaluate(()=>window.__wild.step(1000/30,1));
    const ready=await page.evaluate(()=>{const w=window.__wild.world;return !window.__wild.probe().loading&&w.terrainView.settled()&&w.vegetation.pending.size===0&&w.vegetation.farQueue.length===0&&w.vegetation.settled(w.player)});
    if(ready)break;
    if(i===219)throw Error('Terrain failed to settle for '+shot.id);
    await position(page,shot);
    await sleep(20);
  }
  await position(page,shot);
  await page.evaluate(prime=>window.__wild.step(1000/60,24,prime),shot.prime||{});
  await page.evaluate(()=>{const p=window.__wild.world.player;p.stamina=1;p.exhausted=false;p.rest=1});
}

async function record(shot){
  console.log('START',shot.id,shot.duration+'s');
  await page.evaluate(()=>window.__wild.setQuality('high'));
  await warm(shot);
  const filename=join(OUT,'takes',shot.id+'.mp4');
  const encoder=spawn('ffmpeg',['-hide_banner','-loglevel','error','-y','-f','image2pipe','-vcodec','mjpeg','-framerate',String(FPS),'-i','pipe:0','-an','-vf','scale=in_range=pc:out_range=tv:in_color_matrix=bt601:out_color_matrix=bt709,format=yuv420p','-c:v','libx264','-preset','fast','-crf','17','-color_range','tv','-colorspace','bt709','-color_primaries','bt709','-color_trc','bt709','-r',String(FPS),'-movflags','+faststart',filename],{stdio:['pipe','ignore','pipe']});
  let encodeError='';encoder.stderr.on('data',b=>encodeError+=b.toString());
  const closed=once(encoder,'close');
  const count=shot.duration*FPS,samples=[],events=[],states={};
  let probe=await page.evaluate(()=>window.__wild.probe());
  for(let f=0;f<count;f++){
    if(shot.qualityAt?.[f]){
      await page.locator('#quality').click();
      const tier=await page.evaluate(()=>window.__wild.probe().tier);
      if(tier!==shot.qualityAt[f])throw Error('Quality control did not change tier');
    }
    const intent=shot.intent(f,f/FPS,probe);
    probe=await page.evaluate(i=>window.__wild.step(1000/30,1,i),intent);
    states[probe.mode]=(states[probe.mode]||0)+1;
    for(const event of probe.events)events.push({frame:f,time:f/FPS,event});
    if(f%FPS===0)samples.push({frame:f,time:f/FPS,...probe});
    const bytes=await page.screenshot({type:'jpeg',quality:95,animations:'disabled',caret:'hide'});
    if(!encoder.stdin.write(bytes))await once(encoder.stdin,'drain');
    if([0,Math.floor(count/2),count-1].includes(f))writeFileSync(join(OUT,'stills',shot.id+'-'+String(f).padStart(4,'0')+'.jpg'),bytes);
    if(f&&f%(FPS*3)===0)console.log('FRAME',shot.id,f+'/'+count,probe.mode);
  }
  encoder.stdin.end();
  const [code]=await closed;if(code!==0)throw Error(encodeError||'Encoder failed');
  const bytes=readFileSync(filename);
  manifest.takes.push({id:shot.id,file:'takes/'+shot.id+'.mp4',duration:shot.duration,frameCount:count,states,events,samples,bytes:bytes.length,sha256:createHash('sha256').update(bytes).digest('hex')});
  save();console.log('DONE',shot.id,JSON.stringify({states,events:events.map(x=>x.event),bytes:bytes.length}));
}

async function touchTake(){
  const id='08-touch-controls',duration=4;
  console.log('START',id,'real touch');
  const context=await browser.newContext({viewport:{width:WIDTH,height:HEIGHT},deviceScaleFactor:1,hasTouch:true,isMobile:true,recordVideo:{dir:join(OUT,'source'),size:{width:WIDTH,height:HEIGHT}}});
  const p=await context.newPage();p.on('pageerror',e=>errors.push(e.message));
  await p.goto(BASE+'?debug&hud=0');
  await p.waitForFunction(()=>window.__wild&&!window.__wild.probe().loading,null,{timeout:45000});
  await p.addStyleTag({content:css});
  await position(p,{setup:{x:30,z:366,yaw:Math.PI,pitch:.2}});
  await sleep(1000);
  const cdp=await context.newCDPSession(p);
  const started=Date.now();
  const point={id:1,x:170,y:900};
  await cdp.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[point]});
  await sleep(350);point.y=840;
  await cdp.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[point]});
  await sleep(1000);
  const box=await p.locator('#jump').boundingBox();
  const button={id:2,x:box.x+box.width/2,y:box.y+box.height/2};
  await cdp.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[point,button]});
  await p.waitForFunction(()=>window.__wild.probe().mode==='air');
  const jumped=await p.evaluate(()=>window.__wild.probe());
  await cdp.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});
  await p.waitForFunction(()=>window.__wild.world.player.airTime>.18&&window.__wild.probe().mode==='air');
  await p.touchscreen.tap(button.x,button.y);
  await p.waitForFunction(()=>window.__wild.probe().mode==='glide');
  const glided=await p.evaluate(()=>window.__wild.probe());
  const remaining=duration*1000-(Date.now()-started);if(remaining>0)await sleep(remaining);
  await p.screenshot({path:join(OUT,'stills',id+'-end.jpg'),type:'jpeg',quality:95});
  const video=p.video();await context.close();const raw=await video.path();
  const probe=spawnSync('ffprobe',['-v','error','-show_entries','format=duration','-of','default=noprint_wrappers=1:nokey=1',raw],{encoding:'utf8'});
  const rawDuration=Number(probe.stdout.trim());
  const filename=join(OUT,'takes',id+'.mp4');
  const encode=spawnSync('ffmpeg',['-hide_banner','-loglevel','error','-y','-ss',String(Math.max(0,rawDuration-duration)),'-i',raw,'-t',String(duration),'-an','-vf','fps=30','-c:v','libx264','-preset','fast','-crf','17','-pix_fmt','yuv420p','-movflags','+faststart',filename],{encoding:'utf8'});
  if(encode.status!==0)throw Error(encode.stderr);
  const bytes=readFileSync(filename);
  manifest.takes.push({id,file:'takes/'+id+'.mp4',duration,frameCount:duration*FPS,method:'Real-time browser recording with actual Chrome multitouch',jumped,glided,sourceWebm:raw,bytes:bytes.length,sha256:createHash('sha256').update(bytes).digest('hex')});
  save();console.log('DONE',id,JSON.stringify({modes:[jumped.mode,glided.mode],bytes:bytes.length}));
}

try{
  await page.goto(BASE+'?debug&manual=1&hud=0');
  await page.waitForFunction(()=>window.__wild);
  await page.addStyleTag({content:css});
  for(const shot of shots)if(!ONLY||ONLY.split(',').includes(shot.id))await record(shot);
  if(!ONLY||ONLY.split(',').includes('08-touch-controls'))await touchTake();
  if(errors.length)throw Error('Browser errors: '+errors.join('; '));
  save();console.log('CAPTURE COMPLETE',manifest.takes.length,'takes');
}catch(error){save();throw error}finally{await browser.close()}
