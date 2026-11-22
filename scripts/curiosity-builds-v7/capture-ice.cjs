const {chromium}=require('/Users/yqin/repo/ai-testing/node_modules/playwright');
const fs=require('node:fs');
const {record,setup,step,skip,until,BASE,ROOT}=require('./capture-is.cjs');
async function ice(p){const state=await p.evaluate(()=>{const w=window.__museum.world;w.setManifoldFunnelSkin('the-manifold','spaceGlass');w.setManifoldBlackHole('the-manifold','white');return {funnel:w.manifoldFunnelSkinOf('the-manifold'),blackHole:w.manifoldBlackHoleOf('the-manifold')};});await skip(p,.2);if(state.funnel!=='spaceGlass'||state.blackHole!=='white')throw Error(JSON.stringify(state));return state;}
(async()=>{const b=await chromium.connectOverCDP('http://127.0.0.1:9238');const p=await b.contexts()[0].newPage();const errors=[];p.on('pageerror',e=>errors.push(e.message));
try{
 await setup(p,'/?world=museum&room=the-manifold&debug&manual=1&hud=0&fullscreen=0');await p.keyboard.press('v');const selected=await ice(p);
 await p.screenshot({path:ROOT+'/records/ice-entry-before.png'});
 await record(p,'roller-entry',2.6,t=>({forward:.55,pitch:t<1?.001:0}));
 const s=await p.evaluate(async()=>{const e=await import('/src/inception/world/model/manifoldExperience.js');const m=await import('/src/inception/world/model/manifoldRoom.js');return {v:e.manifoldTrackOverview('goldenFunnel'),c:m.MANIFOLD_ROOM.pocketCenter};});const c=s.c,v=s.v;
 await record(p,'roller-overview',2,()=>({}),t=>({eye:[c.x+v.x,c.y+Math.max(v.y,83),c.z+v.z-t*.8],target:[c.x+v.target.x,c.y+v.target.y,c.z+v.target.z],up:[0,1,0]}));
 await p.goto(BASE+'/tour?start=manifold&debug&manual=1&hud=0&fullscreen=0',{waitUntil:'domcontentloaded'});
 await p.evaluate(()=>{for(const k of ['narration','backgroundMusic','subtitles']){const e=document.querySelector(`[data-tour-toggle="${k}"]`);if(e?.getAttribute('aria-pressed')==='true')e.click();}});
 await p.locator('[data-ride]').click();await p.waitForFunction(()=>!!window.__museum,null,{timeout:120000});await ice(p);await until(p,/Golden Funnel — .*speed/);
 await record(p,'roller-funnel',7.4,()=>({}),null,{speed:t=>1.5+1.3*Math.sin(Math.PI*t/7.4)});
 const final=await ice(p);fs.writeFileSync(ROOT+'/records/ice-blue-native.json',JSON.stringify({selected,final,errors,source:BASE,noSourceCodeChanges:true},null,2));if(errors.length)throw Error(errors.join('\n'));
}finally{await p.close();await b.close();}
})().catch(e=>{console.error(e);process.exit(1)});
