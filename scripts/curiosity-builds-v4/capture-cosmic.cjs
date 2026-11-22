const {chromium}=require('/Users/yqin/repo/ai-testing/node_modules/playwright');
const fs=require('node:fs');
const {record,setup,step,skip,ROOT}=require('./capture-is.cjs');
(async()=>{
 const b=await chromium.connectOverCDP('http://127.0.0.1:9238');const p=await b.contexts()[0].newPage();
 const panorama='/Users/yqin/repo/playground/sky-panorama-lab/out/background10.jpg';
 await p.route('**/0e6000333bc61bea1005c1a82589572bdc0d1927be5fb0b0393512044718df2c-background10.jpg',r=>r.fulfill({path:panorama,contentType:'image/jpeg'}));
 await setup(p,'/?world=museum&room=room-b&debug&manual=1&hud=0&fullscreen=0');await p.keyboard.press('v');
 await p.evaluate(()=>window.__museum.world.setSkyVariant('cosmic-cliffs'));
 await p.waitForFunction(()=>window.__museum.world.skyTextures.has('cosmic-cliffs'),null,{timeout:60000});await skip(p,2);
 const c=await p.evaluate(async()=>{const m=await import('/src/inception/world/model/museum.js');const a=m.MUSEUM_MANIFEST.portalSlots;const i=a.findIndex(x=>x.id==='room-b');return {...m.roomCenterFor(a[i],i),floor:window.__museum.probe().floorY};});
 await record(p,'sky-orbit-cosmic-cliffs',18,()=>({}),t=>{const a=-.7+t*Math.PI*2/18;return {eye:[c.x+Math.sin(a)*9,c.floor+3.4+Math.sin(t*.25)*.4,c.z+Math.cos(a)*9],target:[c.x,c.floor+1.5,c.z],up:[0,1,0]}});
 const receipt=await p.evaluate(()=>({variant:window.__museum.world.skyVariant,room:window.__museum.probe().room,loaded:window.__museum.world.skyTextures.has('cosmic-cliffs')}));
 fs.writeFileSync(ROOT+'/records/cosmic-cliffs.json',JSON.stringify({...receipt,panorama,productionChanged:false},null,2));
 if(receipt.variant!=='cosmic-cliffs'||!receipt.loaded)throw Error('Cosmic Cliffs was not active');
 await p.close();await b.close();
})().catch(e=>{console.error(e);process.exit(1)});
