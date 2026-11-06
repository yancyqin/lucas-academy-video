// Full orbital film; independent output preserves the v1 reference.
const fs=require('node:fs');
const path=require('node:path');
const {spawnSync}=require('node:child_process');
const {createHash}=require('node:crypto');
const {bundle}=require('@remotion/bundler');
const {openBrowser,selectComposition,renderStill,renderMedia}=require('@remotion/renderer');
const ROOT=path.resolve(__dirname,'../..'),OUT=path.join(ROOT,'out/family-ai-lab-02/orbital-v2'),PUBLIC=path.join(ROOT,'public/family-ai-lab-02');
const options=new Set(process.argv.slice(2));
const pick=new Set((process.argv.find(s=>s.startsWith('--pick='))||'').slice(7).split(',').filter(Boolean).map(Number));
function run(cmd,args){const p=spawnSync(cmd,args,{stdio:'inherit',cwd:ROOT});if(p.status!==0)throw Error(`${cmd}: ${p.status}`);}
async function main(){
 const stills=options.has('--stills'),voiced=options.has('--voiced');
 const frames=path.join(OUT,'full-frames'),delivery=path.join(OUT,voiced?'delivery':'review');fs.mkdirSync(frames,{recursive:true});fs.mkdirSync(delivery,{recursive:true});
 const pub=path.join(ROOT,'tmp/family-ai-lab-02/orbital-full-public');fs.mkdirSync(pub,{recursive:true});
 if(!fs.existsSync(path.join(pub,'family-ai-lab-02')))fs.symlinkSync(PUBLIC,path.join(pub,'family-ai-lab-02'),'dir');
 const serveUrl=await bundle({entryPoint:path.join(ROOT,'src/index.ts'),rootDir:ROOT,publicDir:pub,outDir:fs.mkdtempSync(path.join(OUT,'bundle-'))});
 const browserExecutable='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
 const browser=await openBrowser('chrome',{browserExecutable});let comp;
 try{
  comp=await selectComposition({serveUrl,id:'FamilyAiLab02Orbital',puppeteerInstance:browser,inputProps:{view:'full'}});
  if(stills){
   for(const [i,row] of comp.props.tl.lines.entries()){
    if(pick.size&&!pick.has(i+1))continue;
    await renderStill({composition:comp,serveUrl,puppeteerInstance:browser,frame:row.from+Math.floor(row.duration*.62),output:path.join(frames,`${String(i+1).padStart(2,'0')}-${row.visual}.png`),scale:2/3});
    console.log('Still',i+1,row.visual);
   }
   return;
  }
 }finally{await browser.close({silent:true});}
 if(voiced&&!comp.props.tl.narrated)throw Error('Build voiced timeline first');
 const fingerprint=createHash('sha256').update(JSON.stringify(comp.props)).update(fs.readFileSync(path.join(ROOT,'src/videos/family-ai-lab-02/FamilyAiLab02Orbital.tsx'))).update(fs.readFileSync(__filename));
 for(const name of ['orbital-v2/story-clips.json','orbital-v2/timeline.json','qr.png','capture/lab.mp4','capture/lab-a.png','curriculum/worksheet-front.jpg',...['banana_3d','red_apple_3d','grapes_3d','watermelon_3d'].map(n=>'curriculum/'+n+'.png')])fingerprint.update(fs.readFileSync(path.join(PUBLIC,name)));
 for(const row of Object.values(JSON.parse(fs.readFileSync(path.join(PUBLIC,'orbital-v2/story-clips.json'))))){fingerprint.update(fs.readFileSync(path.join(PUBLIC,row.src)));fingerprint.update(fs.readFileSync(path.join(PUBLIC,row.lastFrame)));}
 for(const name of ['lab-workbench','cargo-bay','signal-conduit','story-arrival'])fingerprint.update(fs.readFileSync(path.join(PUBLIC,'orbital-v2/art',name+'.png')));
 fingerprint.update(fs.readFileSync(path.join(PUBLIC,'design-v2/01-orbital.png')));
 const signature=fingerprint.digest('hex').slice(0,16);
 const partsDir=path.join(OUT,'chunks-'+signature);fs.mkdirSync(partsDir,{recursive:true});const parts=[];
 for(let start=0,index=0;start<comp.durationInFrames;start+=2400,index++){
  const end=Math.min(start+2399,comp.durationInFrames-1),part=path.join(partsDir,`${String(index).padStart(3,'0')}.mp4`),receipt=part+'.json';let valid=false;
  if(fs.existsSync(part)&&fs.existsSync(receipt)){const r=JSON.parse(fs.readFileSync(receipt));valid=r.start===start&&r.end===end&&r.sha256===createHash('sha256').update(fs.readFileSync(part)).digest('hex');}
  if(!valid){const b=await openBrowser('chrome',{browserExecutable});try{
   console.log('Chunk',index+1,`${start}–${end}`);let bucket=-1;
   await renderMedia({composition:comp,serveUrl,puppeteerInstance:b,browserExecutable,codec:'h264',outputLocation:part,frameRange:[start,end],concurrency:2,crf:18,x264Preset:'fast',muted:true,timeoutInMilliseconds:120000,offthreadVideoCacheSizeInBytes:128*1024*1024,mediaCacheSizeInBytes:128*1024*1024,offthreadVideoThreads:1,onProgress:({progress})=>{const value=Math.floor(progress*10);if(value>bucket){bucket=value;console.log('Chunk',index+1,value*10+'%');}}});
  }finally{await b.close({silent:true});}
   const probe=spawnSync('ffprobe',['-v','error','-show_entries','stream=width,height,nb_frames','-of','json',part],{encoding:'utf8'});if(probe.status!==0)throw Error('Invalid chunk');const stream=JSON.parse(probe.stdout).streams[0];
   if(Number(stream.nb_frames)!==end-start+1||stream.width!==1920||stream.height!==1080)throw Error('Chunk size/frame count differs');
   fs.writeFileSync(receipt,JSON.stringify({start,end,sha256:createHash('sha256').update(fs.readFileSync(part)).digest('hex')}));
  }
  parts.push(part);console.log('Picture',Math.round((end+1)/comp.durationInFrames*100)+'%');
 }
 const playlist=path.join(partsDir,'concat.txt');fs.writeFileSync(playlist,parts.map(p=>`file '${path.basename(p)}'`).join('\n')+'\n');const picture=path.join(OUT,'picture.mp4');
 run('ffmpeg',['-v','error','-y','-f','concat','-safe','0','-i',playlist,'-map','0:v:0','-an','-c','copy',picture]);
 const film=path.join(delivery,voiced?'family-ai-lab-02.bilingual.mp4':'family-ai-lab-02.silent.mp4');
 const audio=voiced?['-i',path.join(OUT,'audio/en.wav'),'-i',path.join(OUT,'audio/zh.wav'),'-map','0:v:0','-map','1:a:0','-map','2:a:0','-c:a','aac','-b:a','192k','-ar','48000','-ac','1','-metadata:s:a:0','language=eng','-metadata:s:a:1','language=zho','-metadata:s:a:0','title=English — Louise','-metadata:s:a:1','title=中文 — Louise','-disposition:a:0','default','-disposition:a:1','0']:['-map','0:v:0'];
 run('ffmpeg',['-v','error','-y','-i',picture,...audio,'-c:v','copy','-movflags','+faststart','-metadata','title=Family AI Lab — The Tiny Pipe',film]);
 for(const [source,dest] of [['en','en'],['zh','zh-Hans']])fs.copyFileSync(path.join(PUBLIC,'orbital-v2',source+'.srt'),path.join(delivery,dest+'.srt'));
 console.log('Film:',film);
}
main().catch(error=>{console.error(error);process.exitCode=1;});
