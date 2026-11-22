const {chromium}=require('/Users/yqin/repo/ai-testing/node_modules/playwright');
const fs=require('node:fs');
const {record,setup,step,skip,until,BASE,ROOT}=require('./capture-is.cjs');
async function center(p,id){return p.evaluate(async id=>{const m=await import('/src/inception/world/model/museum.js');const a=m.MUSEUM_MANIFEST.portalSlots;const i=a.findIndex(x=>x.id===id);return {...m.roomCenterFor(a[i],i),floor:window.__museum.probe().floorY};},id);}
(async()=>{const mode=process.argv[2]||'roller';const b=await chromium.connectOverCDP('http://127.0.0.1:9238');const p=await b.contexts()[0].newPage();const errors=[];p.on('pageerror',e=>errors.push(e.message));
 if(mode==='roller'){
  await setup(p,'/?world=museum&room=the-manifold&debug&manual=1&hud=0&fullscreen=0');await p.keyboard.press('v');
  await record(p,'roller-entry',2.6,t=>({forward:.55,pitch:t<1?.001:0}));
  const s=await p.evaluate(async()=>{const e=await import('/src/inception/world/model/manifoldExperience.js');const m=await import('/src/inception/world/model/manifoldRoom.js');return {v:e.manifoldTrackOverview('goldenFunnel'),c:m.MANIFOLD_ROOM.pocketCenter};});
  const c=s.c,v=s.v;
  await record(p,'roller-overview',2,()=>({}),t=>({eye:[c.x+v.x,c.y+Math.max(v.y,83),c.z+v.z-t*.8],target:[c.x+v.target.x,c.y+v.target.y,c.z+v.target.z],up:[0,1,0]}));
  await p.goto(BASE+'/tour?start=manifold&debug&manual=1&hud=0&fullscreen=0',{waitUntil:'domcontentloaded'});
  await p.evaluate(()=>{for(const k of ['narration','backgroundMusic','subtitles']){const e=document.querySelector(`[data-tour-toggle="${k}"]`);if(e?.getAttribute('aria-pressed')==='true')e.click();}});
  await p.locator('[data-ride]').click();await p.waitForFunction(()=>!!window.__museum,null,{timeout:120000});
  await until(p,/y = kx — .*speed/);await record(p,'roller-line',2);
  await until(p,/Parabola — .*speed/);await record(p,'roller-parabola',3,()=>({}),null,{speed:t=>1.2+.5*Math.sin(Math.PI*t/3)});
  await until(p,/Golden Funnel — .*speed/);await record(p,'roller-funnel',7.4,()=>({}),null,{speed:t=>1.5+1.3*Math.sin(Math.PI*t/7.4)});
  await until(p,/Möbius — Lap/);await record(p,'roller-mobius',12);
 }else if(mode==='lobby'){
  await setup(p,'/?world=museum&room=chess-lobby&debug&manual=1&hud=0&fullscreen=0');await p.keyboard.press('v');const c=await center(p,'chess-lobby');
  await record(p,'chess-lobby',4,()=>({}),t=>({eye:[c.x+.6,c.floor+3.4,c.z+11-t*.5],target:[c.x,c.floor+4.2,c.z-5],up:[0,1,0]}));
 }else if(mode==='chess'){
  await setup(p,'/?world=museum&room=chess-lobby&debug&manual=1&hud=0&fullscreen=0');await p.keyboard.press('v');let c=await center(p,'chess-lobby');
  await record(p,'chess-lobby',4,()=>({}),t=>({eye:[c.x+.6,c.floor+3.4,c.z+11-t*.5],target:[c.x,c.floor+4.2,c.z-5],up:[0,1,0]}));
  await setup(p,'/?world=museum&room=chess-room-1&debug&manual=1&hud=0&fullscreen=0');await p.keyboard.press('v');
  await p.evaluate(async()=>{const {ChessBoardStage}=await import('/src/inception/chess/threeChess.ts');const old=ChessBoardStage.prototype.step;ChessBoardStage.prototype.step=function(dt){window.__filmStage=this;return old.call(this,dt)};window.__boardApi=await import('/src/inception/chess/chessView.js');});await step(p,2);
  await p.evaluate(()=>{window.__museum.chess({act:'sit',color:0,tc:0});window.__museum.chess({act:'bot',level:1});window.__museum.chessCard(false);});await step(p,2);
  const shot=await p.evaluate(()=>{const s=window.__filmStage,w=window.__museum.world;w.camera.fov=50;w.camera.updateProjectionMatrix();s.group.updateWorldMatrix(true,false);const vec=s.group.position.clone();return {eye:s.group.localToWorld(vec.set(9,s.top+13,15)).toArray(),target:s.group.localToWorld(vec.set(0,s.top+1,0)).toArray()};});
  const events=[];
  await record(p,'chess-play',10,()=>({}),t=>({eye:[shot.eye[0]+t*.06,shot.eye[1],shot.eye[2]],target:shot.target,up:[0,1,0]}),{before:async(page,t,f)=>{if(f%42!==8)return;const event=await page.evaluate(()=>{const m=window.__museum,v=m.probe().chess.table;if(!v||v.phase!=='playing')return null;const api=window.__boardApi,board=api.readBoard(v);if(board.turn!==0)return null;let action;for(const [from,to] of [['e2','e4'],['g1','f3'],['f1','c4'],['d2','d4'],['b1','c3']]){action=api.moveFor(board,from,to);if(action)break;}if(!action){const [from,moves]=[...board.moves][0]||[];if(from&&moves?.[0])action=api.moveFor(board,from,moves[0].to);}if(!action)return null;m.chess({act:'play',action});return {action,before:v.actions.length};});if(event){events.push({t,...event});console.log('Move',JSON.stringify(event));}}});
  const table=await p.evaluate(()=>window.__museum.probe().chess.table);fs.writeFileSync(ROOT+'/records/chess-play-events.json',JSON.stringify({events,table},null,2));if(!table||table.actions.length<4)throw Error('Insufficient real chess moves');
 }else if(mode==='sky'){
  await setup(p,'/?world=museum&room=room-b&debug&manual=1&hud=0&fullscreen=0');await p.keyboard.press('v');const c=await center(p,'room-b');
  await record(p,'sky-orbit',18,()=>({}),t=>{const a=-.7+t*Math.PI*2/18;return {eye:[c.x+Math.sin(a)*9,c.floor+3.4+Math.sin(t*.25)*.4,c.z+Math.cos(a)*9],target:[c.x,c.floor+1.5,c.z],up:[0,1,0]}});
 }
 fs.writeFileSync(ROOT+'/records/'+mode+'-errors.json',JSON.stringify(errors,null,2));await p.close();await b.close();
})().catch(e=>{console.error(e);process.exit(1)});
