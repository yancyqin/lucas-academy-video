const fs=require('node:fs');
const path=require('node:path');
const {spawnSync}=require('node:child_process');
const {bundle}=require('@remotion/bundler');
const {openBrowser,selectComposition,renderStill,renderMedia}=require('@remotion/renderer');

const ROOT=path.resolve(__dirname,'../..');
const OUT=path.join(ROOT,'out/family-ai-lab-01');
const PUB=path.join(ROOT,'tmp/family-ai-lab-01/public');
const options=new Set(process.argv.slice(2));
const pick=new Set((process.argv.find(s=>s.startsWith('--pick='))||'').slice(7).split(',').filter(Boolean).map(Number));
const run=(cmd,args)=>{const r=spawnSync(cmd,args,{stdio:'inherit',cwd:ROOT});if(r.status!==0)throw Error(`${cmd} failed: ${r.status}`);};
async function main(){
 fs.mkdirSync(PUB,{recursive:true});
 if(!fs.existsSync(path.join(PUB,'family-ai-lab-01')))fs.symlinkSync(path.join(ROOT,'public/family-ai-lab-01'),path.join(PUB,'family-ai-lab-01'),'dir');
 fs.mkdirSync(path.join(OUT,'frames'),{recursive:true});fs.mkdirSync(path.join(OUT,'review'),{recursive:true});
 const serveUrl=await bundle({entryPoint:path.join(ROOT,'src/index.ts'),rootDir:ROOT,publicDir:PUB,outDir:fs.mkdtempSync(path.join(OUT,'bundle-'))});
 const browserExecutable=process.env.REMOTION_BROWSER_EXECUTABLE||'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
 const browser=await openBrowser('chrome',{browserExecutable});
 try{
  if(!options.has('--movie')){
   const comp=await selectComposition({serveUrl,id:'FamilyAiLab01En',puppeteerInstance:browser});
   for(const [i,l] of comp.props.tl.lines.entries()){
    if(pick.size&&!pick.has(i+1))continue;
    const frame=l.from+Math.floor(l.duration*.6);
    await renderStill({composition:comp,serveUrl,puppeteerInstance:browser,frame,output:path.join(OUT,'frames',`${String(i+1).padStart(2,'0')}-${l.id}.png`),scale:0.666667});
    if((i+1)%12===0)console.log(`Checked frames ${i+1}/${comp.props.tl.lines.length}`);
   }
   // Frame-by-frame evidence of the real-time race, including the first visible JS finish.
   const race=comp.props.tl.lines.find(l=>l.visual==='race-run').from+15;
   for(const seconds of (pick.size?[]:[0,1/30,.5,1,1.2,4,4.1]))await renderStill({composition:comp,serveUrl,puppeteerInstance:browser,
    frame:race+Math.round(seconds*30),output:path.join(OUT,'frames',`race-${seconds.toFixed(3)}.png`),scale:0.666667});
   const zh=await selectComposition({serveUrl,id:'FamilyAiLab01Zh',puppeteerInstance:browser});
   for(const number of (pick.size?[]:[0,9,42,75])){const l=zh.props.tl.lines[number];await renderStill({composition:zh,serveUrl,puppeteerInstance:browser,
    frame:l.from+Math.floor(l.duration*.5),output:path.join(OUT,'frames',`zh-${l.id}.png`),scale:0.666667});}
  }
  if(options.has('--stills'))return;
  const composition=await selectComposition({serveUrl,id:'FamilyAiLab01',puppeteerInstance:browser});
  const picture=path.join(OUT,'picture.mp4');
  let last=-1;
  await renderMedia({composition,serveUrl,codec:'h264',outputLocation:picture,puppeteerInstance:browser,browserExecutable,
   concurrency:4,crf:19,x264Preset:'fast',muted:true,timeoutInMilliseconds:120000,
   onProgress:({progress})=>{const bucket=Math.floor(progress*20);if(bucket!==last){last=bucket;console.log(`Picture ${Math.round(progress*100)}%`);}}});
  const film=path.join(OUT,'review/family-ai-lab-01.review.mp4');
  run('ffmpeg',['-v','error','-y','-i',picture,'-i',path.join(ROOT,'public/family-ai-lab-01/review.en.ass'),'-i',path.join(ROOT,'public/family-ai-lab-01/review.zh.ass'),
   '-map','0:v:0','-map','1:s:0','-map','2:s:0','-c:v','copy','-c:s','mov_text',
   '-metadata:s:s:0','language=eng','-metadata:s:s:0','title=English',
   '-metadata:s:s:1','language=zho','-metadata:s:s:1','title=简体中文',
   '-disposition:s:0','default','-disposition:s:1','0','-metadata','title=Family AI Lab 01 — Review (no narration)',
   '-movflags','+faststart',film]);
  for(const [src,dest] of [['en','en'],['zh','zh-Hans']])fs.copyFileSync(path.join(ROOT,`public/family-ai-lab-01/review.${src}.srt`),path.join(OUT,`review/${dest}.srt`));
  console.log('Review:',film);
 }finally{await browser.close({silent:true});}
}
main().catch(e=>{console.error(e);process.exitCode=1;});
