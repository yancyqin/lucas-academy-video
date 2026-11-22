const fs=require('node:fs');
const ROOT='/Users/yqin/repo/playground/lucas-academy-video-data/curiosity-builds-20261118/v5';
const CSS='.stage--welcome>.card>div[aria-hidden],.stage--welcome>.card>.eyebrow,.stage--welcome>.card>.subtitle,.brandbar,.bible-attribution{display:none!important}.stage--welcome .title-xl{margin:8px 0 12px}.app--welcome{padding:18px 32px}.app{justify-content:center}.stage--recall{flex:1;justify-content:center}';
const common={url:'https://bible.lucasacademy.org/',viewport:{width:1280,height:720},scale:1.5,locale:'en-US',seed:20261119,css:CSS};
async function home(p){
 await p.waitForSelector('.verse-game');
 for(const [i,v] of [[0,'PSA'],[1,'119'],[2,'105']])await p.locator('select').nth(i).selectOption(v);
 await p.locator('button.verse-mode').filter({hasText:/^Practice$/}).click();await p.waitForTimeout(400);
}
async function snapshot(p,name,extra={}){
 const card=p.locator('.stage').first();const box=await card.boundingBox();
 const visible=box&&box.x>=-1&&box.y>=-1&&box.x+box.width<=1281&&box.y+box.height<=721;
 // Welcome can include offscreen safe-area padding; its actual controls must fit.
 const controls=await p.locator('.verse-game,.btn--primary,.guess-option,.bank .tile').evaluateAll(es=>es.filter(e=>e.getBoundingClientRect().width).map(e=>{const r=e.getBoundingClientRect();return {text:e.innerText,x:r.x,y:r.y,w:r.width,h:r.height,visible:r.x>=0&&r.y>=0&&r.right<=1281&&r.bottom<=721}}));
 if(controls.some(x=>!x.visible))throw Error('A game control is clipped: '+JSON.stringify(controls));
 await p.screenshot({path:ROOT+'/records/'+name+'.png'});
 fs.writeFileSync(ROOT+'/records/'+name+'.json',JSON.stringify({url:p.url(),viewport:[1280,720],post_capture_zoom:false,box,visible,controls,...extra},null,2));
}
async function endHold(r,seconds){await r.hold(Math.max(0,seconds-r.now()));}
module.exports=[
 {...common,name:'bible-home-sequence',async prepare(p){await home(p);await snapshot(p,'bible-home-sequence-view');},async run(r){await r.hold(1.2);await r.click(r.page.locator('.verse-game').filter({hasText:'Rebuild'}),{after:.2});await r.hold(.4);await r.click('.btn--primary',{after:.2});await endHold(r,6);}},
 {...common,name:'bible-sequence-fast',async prepare(p){await home(p);await p.locator('.btn--primary').click();await p.waitForSelector('.study__scripture');await p.waitForTimeout(5000);await snapshot(p,'bible-sequence-read');},async run(r){
  await r.hold(3);await r.click('.study__actions .btn--primary');await r.waitFor('.bank .tile');
  const want='yourwordisalamptomyfeetandalightformypath';let done=0;
  while(done<want.length){const text=await r.page.locator('.bank .tile:not([disabled])').allTextContents();const choices=text.map((t,i)=>({i,s:t.toLowerCase().replace(/[^a-z]/g,'')})).filter(x=>x.s&&want.slice(done).startsWith(x.s)).sort((a,b)=>b.s.length-a.s.length);if(!choices.length)throw Error('No correct Sequence tile');const next=choices[0];await r.click(r.page.locator('.bank .tile:not([disabled])').nth(next.i),{after:.2});done+=next.s.length;}
  r.mark('sequence-completed');await r.hold(.7);await snapshot(r.page,'bible-sequence-complete',{completed_letters:done,expected_letters:want.length});await endHold(r,16);
 }},
 {...common,name:'bible-home-next-word',async prepare(p){await home(p);},async run(r){await r.hold(.6);await r.click(r.page.locator('.verse-game').filter({hasText:'Next Word'}),{after:.25});await snapshot(r.page,'bible-home-next-word-view');await r.hold(.4);await r.click('.btn--primary',{after:.2});await endHold(r,5);}},
 {...common,name:'bible-next-word-fast',async prepare(p){await home(p);await p.locator('.verse-game').filter({hasText:'Next Word'}).click();await p.locator('.btn--primary').click();await p.waitForSelector('.guess-option');await snapshot(p,'bible-next-word-start');},async run(r){
  await r.hold(1.2);const words=['a','lamp','to','my','feet','and','a','light','for','my','path'];let correct=0;
  for(let i=0;i<words.length;i++){
   const options=r.page.locator('.guess-option');const labels=await options.allTextContents();const index=labels.findIndex(x=>x.toLowerCase().replace(/[^a-z]/g,'')===words[i]);
   if(index<0)throw Error('Missing next word '+words[i]+': '+JSON.stringify(labels));
   await r.click(options.nth(index),{after:.1});correct++;await r.hold(.65);
   if(i<words.length-1)await r.page.waitForFunction(n=>document.body.innerText.includes('Word '+n+' of 11'),i+2,{timeout:10000});
   if(r.now()>19)break;
  }
  r.mark('next-word-demo');await snapshot(r.page,'bible-next-word-finish',{correct_predictions:correct});if(correct<6)throw Error('Insufficient Next Word demo');await endHold(r,21);
 }}
];
