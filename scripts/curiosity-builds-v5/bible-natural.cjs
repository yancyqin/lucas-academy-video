const fs=require('node:fs');
const ROOT='/Users/yqin/repo/playground/lucas-academy-video-data/curiosity-builds-20261118/v5';
const frames=[];
async function inspect(p,label){
 const box=await p.locator('.stage').boundingBox();
 const visible=box&&box.x>=-1&&box.y>=-1&&box.x+box.width<=1281&&box.y+box.height<=721;
 frames.push({label,box,visible});if(!visible)throw Error('Game extends outside the natural viewport: '+JSON.stringify(box));
 await p.screenshot({path:ROOT+'/records/bible-natural-'+label+'.png'});
}
module.exports=[{
 name:'bible-natural',url:'http://127.0.0.1:5193/?passage=PSA.119.105&translation=WEB&difficulty=practice',
 viewport:{width:1280,height:720},scale:1.5,locale:'en-US',
 css:'.brandbar,.bible-attribution{display:none!important}.app{justify-content:center}.stage--recall{flex:1;justify-content:center}',
 async prepare(p){await p.waitForSelector('.study__scripture');await p.waitForTimeout(5000);await inspect(p,'read');},
 async run(r){
  await r.hold(3);await r.click('.study__actions .btn--primary');await r.waitFor('.bank .tile');await inspect(r.page,'recall');
  const want='yourwordisalamp tomyfeetandalightformypath'.replace(/\s/g,'');let done=0;
  while(done<want.length){
   const texts=await r.page.locator('.bank .tile:not([disabled])').allTextContents();
   const options=texts.map((text,i)=>({i,s:text.toLowerCase().replace(/[^a-z]/g,'')})).filter(x=>x.s&&want.slice(done).startsWith(x.s)).sort((a,b)=>b.s.length-a.s.length);
   if(!options.length)throw Error('Missing expected verse tile after '+done+' letters');
   const next=options[0];await r.click(r.page.locator('.bank .tile:not([disabled])').nth(next.i),{after:.22});done+=next.s.length;
  }
  r.mark('verse-completed');await r.hold(.9);await inspect(r.page,'complete');
  fs.writeFileSync(ROOT+'/records/bible-natural-verification.json',JSON.stringify({source:'Actual local Bible Sequence renderer',viewport:[1280,720],scale:1.5,post_capture_zoom:false,source_code_changed:false,completed_letters:done,expected_letters:want.length,frames},null,2));
  await r.hold(Math.max(0,21-r.now()));
 }
}];
