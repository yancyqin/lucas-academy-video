const {bundle}=require('@remotion/bundler');
const {openBrowser,selectComposition,renderMedia,renderStill}=require('@remotion/renderer');
const fs=require('node:fs');const path=require('node:path');
const ROOT=path.resolve(__dirname,'../..');
const DATA='/Users/yqin/repo/playground/lucas-academy-video-data/curiosity-builds-20261118/v10';
const plan=require('./plan.json');
(async()=>{const serveUrl=await bundle({entryPoint:ROOT+'/src/videos/curiosity-builds-v10/Film.tsx',publicDir:DATA+'/captures'});
 const browser=await openBrowser('chrome',{browserExecutable:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'});
 fs.mkdirSync(DATA+'/builds',{recursive:true});
 const requested=process.argv.slice(2).filter(x=>!x.startsWith('--'));const tasks=requested.length?requested:plan.projects.map(p=>p.id);
 for(const id of tasks){const project=plan.projects.findIndex(p=>p.id===id);const inputProps={project:Math.max(0,project),kind:project<0?id:'project'};
 const composition=await selectComposition({serveUrl,id:'CuriosityBuild',inputProps,puppeteerInstance:browser});
 if(process.argv.includes('--stills')){for(const frame of [24,42,66,84,94,120,192])await renderStill({serveUrl,composition,inputProps,frame,output:DATA+'/records/title-'+id+'-'+frame+'.png',puppeteerInstance:browser});}
 else{await renderMedia({serveUrl,composition,inputProps,codec:'h264',muted:true,outputLocation:DATA+'/builds/'+id+'.mp4',puppeteerInstance:browser,concurrency:3,x264Preset:'fast',crf:18,onProgress:p=>{if(p.renderedFrames%90===0)console.log(id,p.renderedFrames+'/'+composition.durationInFrames)}});console.log('Rendered '+id);}}
 await browser.close({silent:true});
})().catch(e=>{console.error(e);process.exit(1)});
