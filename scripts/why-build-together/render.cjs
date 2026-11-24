const {bundle}=require('@remotion/bundler');
const {openBrowser,selectComposition,renderMedia,renderStill}=require('@remotion/renderer');
const fs=require('node:fs');const path=require('node:path');
const ROOT=path.resolve(__dirname,'../..');const OUT=path.join(ROOT,'out/why-build-together-v01');
(async()=>{
 const plan=JSON.parse(fs.readFileSync(path.join(OUT,'timeline.json'),'utf8'));
 const publicDir=path.join(OUT,'assets');fs.mkdirSync(publicDir,{recursive:true});
 const assets=fs.existsSync(path.join(OUT,'assets.json'))?JSON.parse(fs.readFileSync(path.join(OUT,'assets.json'),'utf8')):{};
 const stills=process.argv.includes('--stills');
 if(!stills)for(const id of ['G01','G02','G03','G04','G05','G06','G05-bw'])if(!fs.existsSync(path.join(publicDir,id+'.mp4')))throw new Error('Muse media missing: '+id);
 const serveUrl=await bundle({entryPoint:path.join(ROOT,'src/videos/why-build-together/Film.tsx'),publicDir});
 const browser=await openBrowser('chrome',{browserExecutable:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'});
 try{
 for(const piece of ['intro','outro']){
  const inputProps={piece,scenes:plan.scenes,frames:plan[piece+'_frames'],assets};
  const composition=await selectComposition({serveUrl,id:'WhyBuildTogether',inputProps,puppeteerInstance:browser});
  if(stills){
   const picks=plan.scenes.filter(s=>s.piece===piece&&['n003','n004','n006','n008','n011','n012','n014'].includes(s.id));
   for(const s of picks){const frame=s.local_start+Math.min(s.frames-1,Math.round(s.frames*.7));await renderStill({serveUrl,composition,inputProps,frame,output:path.join(OUT,'still-'+s.id+'.png'),puppeteerInstance:browser});console.log('Still',s.id)}
  }else{
   let last=0;await renderMedia({serveUrl,composition,inputProps,codec:'h264',muted:true,outputLocation:path.join(OUT,piece+'-picture.mp4'),puppeteerInstance:browser,concurrency:3,x264Preset:'fast',crf:17,onProgress:p=>{if(p.renderedFrames-last>=180){last=p.renderedFrames;console.log(piece,p.renderedFrames+'/'+composition.durationInFrames)}}});console.log('Rendered',piece)
  }
 }
 }finally{await browser.close({silent:true})}
})().catch(e=>{console.error(e);process.exit(1)});
