const fs=require('node:fs');
const path=require('node:path');
const {spawnSync}=require('node:child_process');
const {bundle}=require('@remotion/bundler');
const {openBrowser,selectComposition,renderStill,renderMedia}=require('@remotion/renderer');
const ROOT=path.resolve(__dirname,'../..');
const OUT=path.join(ROOT,'out/science-shorts');
const PUB=path.join(ROOT,'tmp/science-shorts/public');
const options=new Set(process.argv.slice(2));
const films=(process.argv.find(arg=>arg.startsWith('--film='))||'--film=perceptron,optogenetics').slice(7).split(',');
const cues=process.argv.find(arg=>arg.startsWith('--cues='))?.slice(7).split(',');
const run=(name,args)=>{const result=spawnSync(name,args,{cwd:ROOT,stdio:'inherit'});if(result.status!==0)throw Error(`${name} failed: ${result.status}`);};

async function main(){
 fs.mkdirSync(OUT,{recursive:true});fs.mkdirSync(PUB,{recursive:true});
 const dest=path.join(PUB,'science-shorts-20261105');
 if(!fs.existsSync(dest))fs.symlinkSync(path.join(ROOT,'public/science-shorts-20261105'),dest,'dir');
 const serveUrl=await bundle({entryPoint:path.join(ROOT,'src/science-shorts.tsx'),rootDir:ROOT,publicDir:PUB,outDir:fs.mkdtempSync(path.join(OUT,'bundle-'))});
 const browserExecutable='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
 for(const film of films){
  const browser=await openBrowser('chrome',{browserExecutable});
  try{
   const composition=await selectComposition({serveUrl,id:film==='perceptron'?'PerceptronShort':'OptogeneticsShort',puppeteerInstance:browser});
   const folder=path.join(OUT,film),frames=path.join(folder,'frames');fs.mkdirSync(frames,{recursive:true});
   if(!options.has('--movie')){
    for(const line of composition.props.tl.lines.filter(line=>!cues||cues.includes(line.id))){
     await renderStill({composition,serveUrl,puppeteerInstance:browser,frame:line.from+Math.floor(line.duration*.55),output:path.join(frames,line.id+'.png'),scale:.5});
     console.log('Frame',film,line.id);
    }
    for(const shot of composition.props.tl.shots.filter(s=>!cues&&s.layout!=='portrait')){
     for(const [label,fraction] of [['start',.08],['end',.93]])await renderStill({composition,serveUrl,puppeteerInstance:browser,
      frame:shot.from+Math.floor(shot.duration*fraction),output:path.join(frames,`${shot.first}-${label}.png`),scale:.5});
    }
   }
   if(options.has('--stills'))continue;
   if(!composition.props.tl.narrated)throw Error('Select checked voices and build the actual voiced timeline first');
   const choices=JSON.parse(fs.readFileSync(path.join(ROOT,'docs/science-shorts/voice-choices.json'),'utf8'));
   for(const line of composition.props.tl.lines)for(const lang of ['en','zh'])if(!choices[`${lang}/${line.id}`]?.checked)throw Error('Unchecked voice '+lang+'/'+line.id);
   let last=-1;
   const picture=path.join(folder,'picture.mp4');
   await renderMedia({composition,serveUrl,puppeteerInstance:browser,browserExecutable,codec:'h264',outputLocation:picture,
    concurrency:2,crf:18,x264Preset:'fast',muted:true,offthreadVideoCacheSizeInBytes:256*1024*1024,mediaCacheSizeInBytes:128*1024*1024,
    offthreadVideoThreads:2,timeoutInMilliseconds:120000,onProgress:({progress})=>{const step=Math.floor(progress*10);if(last!==step){last=step;console.log(film,Math.round(progress*100)+'%');}}});
   const movie=path.join(folder,film+'.bilingual.mp4');
   run('ffmpeg',['-v','error','-y','-i',picture,'-i',path.join(folder,'audio/en.wav'),'-i',path.join(folder,'audio/zh.wav'),
    '-map','0:v:0','-map','1:a:0','-map','2:a:0','-c:v','copy','-c:a','aac','-b:a','192k','-ar','48000','-ac','1',
    '-metadata:s:a:0','language=eng','-metadata:s:a:0','title=English — Louise','-metadata:s:a:1','language=zho','-metadata:s:a:1','title=中文 — Louise',
    '-disposition:a:0','default','-disposition:a:1','0','-movflags','+faststart',movie]);
   for(const [index,lang] of ['en','zh'].entries())run('ffmpeg',['-v','error','-y','-i',movie,'-map',`0:a:${index}`,'-c:a','copy','-movflags','+faststart',path.join(folder,lang+'.m4a')]);
   console.log('Movie',movie);
  }finally{await browser.close({silent:true});}
 }
}
main().catch(error=>{console.error(error);process.exitCode=1;});
