// Silent visual study; never replaces a narrated delivery or a generated story clip.
const fs=require('node:fs');
const path=require('node:path');
const {createHash}=require('node:crypto');
const {spawnSync}=require('node:child_process');
const {bundle}=require('@remotion/bundler');
const {openBrowser,selectComposition,renderStill,renderMedia}=require('@remotion/renderer');
const ROOT=path.resolve(__dirname,'../..'),PUBLIC=path.join(ROOT,'public/family-ai-lab-02');
const OUT=path.join(ROOT,'out/family-ai-lab-02/orbital-v2');
const browserExecutable='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
async function main(){
 fs.mkdirSync(path.join(OUT,'frames'),{recursive:true});
 const pub=path.join(ROOT,'tmp/family-ai-lab-02/orbital-public');fs.mkdirSync(pub,{recursive:true});
 if(!fs.existsSync(path.join(pub,'family-ai-lab-02')))fs.symlinkSync(PUBLIC,path.join(pub,'family-ai-lab-02'),'dir');
 const serveUrl=await bundle({entryPoint:path.join(ROOT,'src/index.ts'),rootDir:ROOT,publicDir:pub,outDir:fs.mkdtempSync(path.join(OUT,'bundle-'))});
 const browser=await openBrowser('chrome',{browserExecutable});
 try{
  const comp=await selectComposition({serveUrl,id:'FamilyAiLab02Orbital',puppeteerInstance:browser,inputProps:{view:'study'}});
  fs.writeFileSync(path.join(OUT,'study-timeline.json'),JSON.stringify(comp.props.tl,null,2)+'\n');
  for(const [i,row] of comp.props.tl.lines.entries()){
   await renderStill({composition:comp,serveUrl,puppeteerInstance:browser,frame:row.from+Math.floor(row.duration*.68),output:path.join(OUT,'frames',`${String(i+1).padStart(2,'0')}-${row.visual}.png`),scale:2/3});
   console.log('Orbital still',row.visual);
  }
  if(process.argv.includes('--stills'))return;
  const output=path.join(OUT,'style-study.mp4');
  await renderMedia({composition:comp,serveUrl,puppeteerInstance:browser,browserExecutable,codec:'h264',outputLocation:output,scale:2/3,concurrency:2,crf:20,x264Preset:'fast',muted:true,timeoutInMilliseconds:120000,offthreadVideoCacheSizeInBytes:128*1024*1024,mediaCacheSizeInBytes:128*1024*1024,offthreadVideoThreads:1,onProgress:({progress})=>{const n=Math.floor(progress*10);if(n!==main.last){main.last=n;console.log('Study',n*10+'%');}}});
  const probe=spawnSync('ffprobe',['-v','error','-show_streams','-show_format','-of','json',output],{encoding:'utf8'});if(probe.status!==0)throw Error('Invalid study output');
  const meta=JSON.parse(probe.stdout),v=meta.streams.find(s=>s.codec_type==='video');
  if(v.width!==1280||v.height!==720||Number(v.nb_frames)!==comp.durationInFrames||meta.streams.some(s=>s.codec_type!=='video'))throw Error('Unexpected study dimensions, frames or tracks');
  fs.writeFileSync(path.join(OUT,'study-receipt.json'),JSON.stringify({kind:'Silent code-animation visual study; story footage is separate',output,sha256:createHash('sha256').update(fs.readFileSync(output)).digest('hex'),frames:comp.durationInFrames,probe:meta},null,2)+'\n');
  console.log('Visual study:',output);
 }finally{await browser.close({silent:true});}
}
main().catch(e=>{console.error(e);process.exitCode=1;});
