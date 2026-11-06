const fs=require('node:fs');
const path=require('node:path');
const {spawnSync}=require('node:child_process');
const {createHash}=require('node:crypto');
const {bundle}=require('@remotion/bundler');
const {openBrowser,selectComposition,renderStill,renderMedia}=require('@remotion/renderer');

const ROOT=path.resolve(__dirname,'../..');
const OUT=path.join(ROOT,'out/family-ai-lab-01');
const PUB=path.join(ROOT,'tmp/family-ai-lab-01/public');
const options=new Set(process.argv.slice(2));
const timeline=JSON.parse(fs.readFileSync(path.join(ROOT,'public/family-ai-lab-01/timeline.json'),'utf8'));
const revision=timeline.revision||1;
const visualRevision=timeline.visualRevision||revision;
const framesDir=path.join(OUT,'frames',...(visualRevision>=2?[`v${visualRevision}`]:[]));
const pick=new Set((process.argv.find(s=>s.startsWith('--pick='))||'').slice(7).split(',').filter(Boolean).map(Number));
const run=(cmd,args)=>{const r=spawnSync(cmd,args,{stdio:'inherit',cwd:ROOT});if(r.status!==0)throw Error(`${cmd} failed: ${r.status}`);};
async function main(){
 const voiced=options.has('--voiced');
 const delivery=path.join(OUT,voiced?'delivery':'review',...(visualRevision>=2?[`v${visualRevision}`]:[]));
 fs.mkdirSync(PUB,{recursive:true});
 if(!fs.existsSync(path.join(PUB,'family-ai-lab-01')))fs.symlinkSync(path.join(ROOT,'public/family-ai-lab-01'),path.join(PUB,'family-ai-lab-01'),'dir');
 fs.mkdirSync(framesDir,{recursive:true});fs.mkdirSync(delivery,{recursive:true});
 const serveUrl=await bundle({entryPoint:path.join(ROOT,'src/index.ts'),rootDir:ROOT,publicDir:PUB,outDir:fs.mkdtempSync(path.join(OUT,'bundle-'))});
 const browserExecutable=process.env.REMOTION_BROWSER_EXECUTABLE||'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
 const browser=await openBrowser('chrome',{browserExecutable});
 let metadataBrowserClosed=false;
 try{
  if(!options.has('--movie')){
   const comp=await selectComposition({serveUrl,id:'FamilyAiLab01',puppeteerInstance:browser});
   for(const [i,l] of comp.props.tl.lines.entries()){
    if(pick.size&&!pick.has(i+1))continue;
    const frame=l.from+Math.floor(l.duration*.6);
    await renderStill({composition:comp,serveUrl,puppeteerInstance:browser,frame,output:path.join(framesDir,`${String(i+1).padStart(2,'0')}-${l.id}.png`),scale:0.666667});
    if((i+1)%12===0)console.log(`Checked frames ${i+1}/${comp.props.tl.lines.length}`);
   }
   // Frame-by-frame evidence of the real-time race, including the first visible JS finish.
   const race=comp.props.tl.lines.find(l=>l.visual==='race-run').from+15;
   for(const seconds of (pick.size?[]:[0,1/30,.5,1,1.2,4,4.1]))await renderStill({composition:comp,serveUrl,puppeteerInstance:browser,
    frame:race+Math.round(seconds*30),output:path.join(framesDir,`race-${seconds.toFixed(3)}.png`),scale:0.666667});
   const zh=await selectComposition({serveUrl,id:'FamilyAiLab01Zh',puppeteerInstance:browser});
   for(const number of (pick.size||revision>=2?[]:[0,9,42,75])){const l=zh.props.tl.lines[number];await renderStill({composition:zh,serveUrl,puppeteerInstance:browser,
    frame:l.from+Math.floor(l.duration*.5),output:path.join(framesDir,`zh-${l.id}.png`),scale:0.666667});}
  }
  if(options.has('--stills'))return;
  const composition=await selectComposition({serveUrl,id:'FamilyAiLab01',puppeteerInstance:browser});
  if(voiced&&!composition.props.tl.narrated)throw Error('Build --voiced and mix both audio tracks first');
  if(revision>=2&&!composition.props.data.intro.ready)throw Error('The verified Muse G4 original is required before rendering the movie');
  if(visualRevision>=3){
   const atmosphere=JSON.parse(fs.readFileSync(path.join(ROOT,'docs/family-ai-lab-01/atmosphere-v3.json'),'utf8'));
   for(const asset of atmosphere.screenBackgrounds){
    if(createHash('sha256').update(fs.readFileSync(path.join(ROOT,asset.path))).digest('hex')!==asset.sha256)throw Error('Period background hash differs: '+asset.path);
   }
  }
  const picture=path.join(OUT,revision>=2?`picture.v${visualRevision}.mp4`:voiced?'picture.voiced.mp4':'picture.mp4');
  if(revision>=2){
   // Bounded caches and fresh Chromium processes prevent a long capture-heavy
   // film from accumulating decoded frames across its entire duration.
   const signature=createHash('sha256').update(JSON.stringify(composition.props))
    .update(fs.readFileSync(path.join(ROOT,'src/videos/family-ai-lab-01/FamilyAiLab01.tsx')))
    .update(fs.readFileSync(path.join(ROOT,'src/videos/family-ai-lab-01/PeriodFrame.tsx')))
    .update(fs.readFileSync(path.join(ROOT,'docs/family-ai-lab-01/atmosphere-v3-prompts.json')))
    .update(fs.readFileSync(path.join(ROOT,'src/Root.tsx')))
    .update(fs.readFileSync(__filename)).digest('hex').slice(0,16);
   const chunks=path.join(OUT,`chunks-v${visualRevision}-${signature}`);fs.mkdirSync(chunks,{recursive:true});
   await browser.close({silent:true});metadataBrowserClosed=true;
   const parts=[],step=3000,total=composition.durationInFrames;
   for(let start=0,index=0;start<total;start+=step,index++){
    const end=Math.min(total-1,start+step-1),part=path.join(chunks,`${String(index).padStart(3,'0')}.mp4`),receipt=part+'.json';
    let valid=false;
    if(fs.existsSync(part)&&fs.existsSync(receipt)){
     const r=JSON.parse(fs.readFileSync(receipt,'utf8'));
     valid=r.start===start&&r.end===end&&r.sha256===createHash('sha256').update(fs.readFileSync(part)).digest('hex');
    }
    if(!valid){
     const chunkBrowser=await openBrowser('chrome',{browserExecutable});
     try{
      console.log(`Chunk ${index+1}/${Math.ceil(total/step)}: frames ${start}–${end}`);
      await renderMedia({composition,serveUrl,codec:'h264',outputLocation:part,puppeteerInstance:chunkBrowser,browserExecutable,
       frameRange:[start,end],concurrency:2,crf:19,x264Preset:'fast',muted:true,timeoutInMilliseconds:120000,
       offthreadVideoCacheSizeInBytes:256*1024*1024,mediaCacheSizeInBytes:128*1024*1024,offthreadVideoThreads:2});
     }finally{await chunkBrowser.close({silent:true});}
     const p=spawnSync('ffprobe',['-v','error','-select_streams','v:0','-show_entries','stream=nb_frames,width,height','-of','json',part],{encoding:'utf8'});
     if(p.status!==0)throw Error('Invalid render chunk: '+part);
     const stream=JSON.parse(p.stdout).streams[0];
     if(Number(stream.nb_frames)!==end-start+1||stream.width!==1920||stream.height!==1080)throw Error('Chunk frame count or size differs: '+part);
     fs.writeFileSync(receipt,JSON.stringify({start,end,sha256:createHash('sha256').update(fs.readFileSync(part)).digest('hex')}));
    }else console.log(`Reused complete chunk ${index+1}`);
    parts.push(part);console.log(`Picture ${Math.round((end+1)/total*100)}%`);
   }
   const playlist=path.join(chunks,'concat.txt');fs.writeFileSync(playlist,parts.map(p=>`file '${path.basename(p)}'`).join('\n')+'\n');
   run('ffmpeg',['-v','error','-y','-f','concat','-safe','0','-i',playlist,'-map','0:v:0','-an','-c','copy','-movflags','+faststart',picture]);
  }else{
   let last=-1;
   await renderMedia({composition,serveUrl,codec:'h264',outputLocation:picture,puppeteerInstance:browser,browserExecutable,
    concurrency:4,crf:19,x264Preset:'fast',muted:true,timeoutInMilliseconds:120000,
    onProgress:({progress})=>{const bucket=Math.floor(progress*20);if(bucket!==last){last=bucket;console.log(`Picture ${Math.round(progress*100)}%`);}}});
  }
  const film=path.join(delivery,voiced?'family-ai-lab-01.bilingual.mp4':'family-ai-lab-01.review.mp4');
  const audioDir=path.join(OUT,'audio',...(revision>=2?[`v${revision}`]:[]));
  const sound=voiced?['-i',path.join(audioDir,'en.wav'),'-i',path.join(audioDir,'zh.wav')]:[];
  const maps=voiced?['-map','0:v:0','-map','1:a:0','-map','2:a:0',...(revision>=2?[]:['-map','3:s:0','-map','4:s:0'])]:['-map','0:v:0',...(revision>=2?[]:['-map','1:s:0','-map','2:s:0'])];
  const audio=voiced?['-c:a','aac','-b:a','192k','-ar','48000','-ac','1','-metadata:s:a:0','language=eng','-metadata:s:a:0','title=English — Louise','-metadata:s:a:1','language=zho','-metadata:s:a:1','title=中文 — Louise','-disposition:a:0','default','-disposition:a:1','0']:[];
  const subtitles=revision>=2?[]:['-c:s','mov_text',
   '-metadata:s:s:0','language=eng','-metadata:s:s:0','title=English',
   '-metadata:s:s:1','language=zho','-metadata:s:s:1','title=简体中文',
   '-disposition:s:0','default','-disposition:s:1','0'];
  const captionInputs=revision>=2?[]:['-i',path.join(ROOT,'public/family-ai-lab-01/review.en.ass'),'-i',path.join(ROOT,'public/family-ai-lab-01/review.zh.ass')];
  run('ffmpeg',['-v','error','-y','-i',picture,...sound,...captionInputs,...maps,'-c:v','copy',...audio,...subtitles,
   '-metadata',voiced?'title=Family AI Lab 01':'title=Family AI Lab 01 — Review (no narration)',
   '-movflags','+faststart',film]);
  for(const [src,dest] of [['en','en'],['zh','zh-Hans']])fs.copyFileSync(path.join(ROOT,`public/family-ai-lab-01/review.${src}.srt`),path.join(delivery,`${dest}.srt`));
  console.log(voiced?'Film:':'Review:',film);
 }finally{if(!metadataBrowserClosed)await browser.close({silent:true});}
}
main().catch(e=>{console.error(e);process.exitCode=1;});
