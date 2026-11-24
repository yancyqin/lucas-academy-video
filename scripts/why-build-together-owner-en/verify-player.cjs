const {openBrowser}=require('@remotion/renderer');
const {pathToFileURL}=require('node:url');
const fs=require('node:fs');
const path=require('node:path');

async function main(){
 const dir='/Users/yqin/repo/playground/lucas-academy-video-data/why-build-together-20261122/english-owner-track-v05';
 const browser=await openBrowser('chrome',{
  browserExecutable:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',logLevel:'error',
 });
 try{
  const page=await browser.newPage({context:()=>null,logLevel:'error',indent:false,
   pageIndex:0,onBrowserLog:null,onLog:()=>{}});
  await page.setViewport({width:1440,height:1000,deviceScaleFactor:1});
  await page.goto({url:pathToFileURL(path.join(dir,'delivery/preview-en-v05.html')).href,timeout:15000});
  const checks=[];const plan=JSON.parse(fs.readFileSync(path.join(dir,'picture-timeline-v04.json'),'utf8'));
  const expectedCues=fs.readFileSync(path.join(dir,'delivery/why-build-together.en-owner-v05.srt'),'utf8').trim().split(/\n\s*\n/).length;
  const software=plan.scenes.find(s=>s.id==='n007');const sixth=plan.scenes.find(s=>s.id==='n010');
  for(const [name,time] of [['narration',25.4],['software',software.start_frame/30+7.6],
    ['cards',78],['food',85],['sixth-shot',sixth.start_frame/30+6],['building',109.2],['project',plan.insert.start_frame/30+1.2],['ending',plan.seconds-2]]){
   const result=await page.evaluate(async(t,n)=>{
    const v=document.querySelector('video'),track=document.querySelector('track');
    const until=(test)=>new Promise((resolve,reject)=>{
     const start=Date.now();
     const check=()=>{if(test())resolve();else if(Date.now()-start>8000)
      reject(new Error('media did not become ready'));else setTimeout(check,100)};
     check();
    });
    await until(()=>v.readyState>=2&&track.track.cues&&track.track.cues.length===n);
    v.currentTime=t;
    await until(()=>!v.seeking&&track.track.activeCues&&track.track.activeCues.length>0);
    v.muted=true;await v.play();
    await new Promise(resolve=>setTimeout(resolve,450));
    v.pause();
    if(v.currentTime<t+.1)throw new Error('Playback clock did not advance');
    await new Promise(resolve=>setTimeout(resolve,250));
    return {videoDimensions:[v.videoWidth,v.videoHeight],seconds:v.duration,
     playedSeconds:v.currentTime-t,
     cues:track.track.cues.length,mode:track.track.mode,
     activeCaption:[...track.track.activeCues].map(c=>c.text)};
   },time,expectedCues);
   if(result.mode!=='showing')throw new Error('Captions not showing');
   const {value}=await page._client().send('Page.captureScreenshot',{format:'png'});
   fs.writeFileSync(path.join(dir,`captioned-player-${name}.png`),Buffer.from(value.data,'base64'));
   checks.push({name,time,...result});
  }
  const endState=await page.evaluate(async()=>{
   const v=document.querySelector('video');v.currentTime=v.duration-.65;v.muted=true;await v.play();
   await new Promise((resolve,reject)=>{
    const start=Date.now();const check=()=>{if(v.ended)resolve();else if(Date.now()-start>5000)
     reject(new Error('Movie did not stop at its end'));else setTimeout(check,50)};check();
   });
   return {ended:v.ended,stoppedAt:v.currentTime,duration:v.duration};
  });
  if(!endState.ended||Math.abs(endState.duration-plan.seconds)>.05)throw new Error('Unexpected ending duration');
  checks[checks.length-1].endState=endState;
  fs.writeFileSync(path.join(dir,'delivery/player-check.json'),JSON.stringify(checks,null,2)+'\n');
  console.log(JSON.stringify(checks));
 }finally{await browser.close({silent:true})}
}
main().catch(e=>{console.error(e.message);process.exitCode=1});
