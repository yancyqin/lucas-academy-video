const fs=require('node:fs'),path=require('node:path'),{spawnSync}=require('node:child_process'),{createHash}=require('node:crypto');
const {bundle}=require('@remotion/bundler'),{openBrowser,selectComposition,renderMedia,renderStill}=require('@remotion/renderer');
const ROOT=path.resolve(__dirname,'../..'),PUBLIC=path.join(ROOT,'public/family-ai-lab-02'),OUT=path.join(ROOT,'out/family-ai-lab-02/orbital-v2/short');
const run=(command,args)=>{const r=spawnSync(command,args,{cwd:ROOT,stdio:'inherit'});if(r.status!==0)throw Error(command+' failed');};
const digest=file=>createHash('sha256').update(fs.readFileSync(file)).digest('hex');
const pick=new Set((process.argv.find(s=>s.startsWith('--pick='))||'').slice(7).split(',').filter(Boolean).map(Number));
async function main(){
 fs.mkdirSync(OUT,{recursive:true});const pub=path.join(ROOT,'tmp/family-ai-lab-02/short-public');fs.mkdirSync(pub,{recursive:true});if(!fs.existsSync(path.join(pub,'family-ai-lab-02')))fs.symlinkSync(PUBLIC,path.join(pub,'family-ai-lab-02'),'dir');
 const serveUrl=await bundle({entryPoint:path.join(ROOT,'src/index.ts'),rootDir:ROOT,publicDir:pub,outDir:fs.mkdtempSync(path.join(OUT,'bundle-'))});
 const browser=await openBrowser('chrome',{browserExecutable:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'});
 try{
  const composition=await selectComposition({serveUrl,id:'FamilyAiLab02Short',puppeteerInstance:browser});
  if(process.argv.includes('--stills')){const folder=path.join(OUT,'frames');fs.mkdirSync(folder,{recursive:true});for(const [i,row] of composition.props.tl.lines.entries()){if(pick.size&&!pick.has(i+1))continue;await renderStill({composition,serveUrl,puppeteerInstance:browser,frame:row.from+Math.floor(row.duration*.62),scale:.5,output:path.join(folder,`${i+1}-${row.visual}.png`)});console.log('Short still',row.visual);}return;}
  const key=createHash('sha256').update(JSON.stringify(composition.props)).update(fs.readFileSync(path.join(ROOT,'src/videos/family-ai-lab-02/FamilyAiLab02Short.tsx')));for(const s of composition.props.tl.storyClips)key.update(fs.readFileSync(path.join(PUBLIC,s.src)));const signature=key.digest('hex');
  const picture=path.join(OUT,'picture.mp4'),receipt=picture+'.json';let cached=false;if(fs.existsSync(picture)&&fs.existsSync(receipt)){const r=JSON.parse(fs.readFileSync(receipt));cached=r.signature===signature&&r.sha256===digest(picture);}
  if(!cached){let bucket=-1;await renderMedia({composition,serveUrl,puppeteerInstance:browser,codec:'h264',outputLocation:picture,crf:18,x264Preset:'fast',muted:true,concurrency:2,offthreadVideoCacheSizeInBytes:128*1024*1024,mediaCacheSizeInBytes:128*1024*1024,offthreadVideoThreads:1,timeoutInMilliseconds:120000,onProgress:({progress})=>{const p=Math.floor(progress*10);if(p>bucket){bucket=p;console.log('Short picture',p*10+'%');}}});fs.writeFileSync(receipt,JSON.stringify({signature,sha256:digest(picture)}));}
  const delivery=path.join(OUT,'delivery');fs.mkdirSync(delivery,{recursive:true});const movie=path.join(delivery,'family-ai-lab-02.short.bilingual.mp4');
  run('ffmpeg',['-v','error','-y','-i',picture,'-i',path.join(OUT,'audio/en.wav'),'-i',path.join(OUT,'audio/zh.wav'),'-map','0:v:0','-map','1:a:0','-map','2:a:0','-c:v','copy','-c:a','aac','-b:a','192k','-ar','48000','-ac','1','-metadata','title=Can 0 and 1 Talk? — Short Story','-metadata:s:a:0','language=eng','-metadata:s:a:1','language=zho','-metadata:s:a:0','title=English — Louise','-metadata:s:a:1','title=中文 — Louise','-disposition:a:0','default','-disposition:a:1','0','-movflags','+faststart',movie]);
  for(const [lang,name] of [['en','en'],['zh','zh-Hans']])fs.copyFileSync(path.join(PUBLIC,'orbital-v2/short',lang+'.srt'),path.join(delivery,name+'.srt'));
  console.log('Short film:',movie);
 }finally{await browser.close({silent:true});}
}
main().catch(e=>{console.error(e);process.exitCode=1;});
