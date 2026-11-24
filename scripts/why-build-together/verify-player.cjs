const {openBrowser}=require('@remotion/renderer');
const {pathToFileURL}=require('node:url');
const fs=require('node:fs');
const path=require('node:path');

async function main(){
 const dir=path.resolve(__dirname,'../../out/why-build-together-v01');
 const browser=await openBrowser('chrome',{
  browserExecutable:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',logLevel:'error',
 });
 try{
  const page=await browser.newPage({context:()=>null,logLevel:'error',indent:false,
   pageIndex:0,onBrowserLog:null,onLog:()=>{}});
  await page.setViewport({width:1440,height:1000,deviceScaleFactor:1});
  await page.goto({url:pathToFileURL(path.join(dir,'delivery/打开预览.html')).href,timeout:15000});
  const checks=[];
  for(const [name,time] of [['narration',25.4],['project',121.8]]){
   const result=await page.evaluate(async(t)=>{
    const v=document.querySelector('video'),track=document.querySelector('track');
    const until=(test)=>new Promise((resolve,reject)=>{
     const start=Date.now();
     const check=()=>{if(test())resolve();else if(Date.now()-start>8000)
      reject(new Error('media did not become ready'));else setTimeout(check,100)};
     check();
    });
    await until(()=>v.readyState>=2&&track.track.cues&&track.track.cues.length===60);
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
   },time);
   if(result.mode!=='showing')throw new Error('Captions not showing');
   const {value}=await page._client().send('Page.captureScreenshot',{format:'png'});
   fs.writeFileSync(path.join(dir,`captioned-player-${name}.png`),Buffer.from(value.data,'base64'));
   checks.push({name,time,...result});
  }
  fs.writeFileSync(path.join(dir,'delivery/player-check.json'),JSON.stringify(checks,null,2)+'\n');
  console.log(JSON.stringify(checks));
 }finally{await browser.close({silent:true})}
}
main().catch(e=>{console.error(e.message);process.exitCode=1});
