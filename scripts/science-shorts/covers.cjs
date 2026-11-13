/** Extract unlettered source frames, then typeset every word and digit in code. */
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const {spawnSync}=require('node:child_process');
const {bundle}=require('@remotion/bundler');
const {openBrowser,selectComposition,renderStill}=require('@remotion/renderer');
const ROOT=path.resolve(__dirname,'../..'),INPUT=path.join(ROOT,'public/science-shorts-20261105');
const OUT=path.join(ROOT,'out/science-shorts/cover'),DOC=path.join(ROOT,'docs/science-shorts');
const hash=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const run=(name,args)=>{const r=spawnSync(name,args,{encoding:'utf8'});if(r.status!==0)throw Error(r.stderr||name+' failed');return r.stdout;};
async function main(){
 fs.mkdirSync(OUT,{recursive:true});fs.mkdirSync(path.join(INPUT,'cover'),{recursive:true});
 const data=JSON.parse(fs.readFileSync(path.join(INPUT,'data.json'),'utf8')),sources={};
 for(const [film,key,seconds] of [['perceptron','perceptron-portal',2],['optogenetics','opto-goggles',1.25]]){
  const source=path.join(INPUT,data.assets[key].path);if(hash(source)!==data.assets[key].sha256)throw Error('Source changed: '+key);
  const background=path.join(INPUT,'cover',film+'.png');
  run('ffmpeg',['-v','error','-y','-ss',String(seconds),'-i',source,'-frames:v','1',background]);
  sources[film]={path:path.relative(ROOT,source),sha256:hash(source),seconds,background:path.relative(ROOT,background),backgroundSha256:hash(background)};
 }
 const publicDir=path.join(ROOT,'tmp/science-shorts/public');fs.mkdirSync(publicDir,{recursive:true});
 const link=path.join(publicDir,'science-shorts-20261105');if(!fs.existsSync(link))fs.symlinkSync(INPUT,link,'dir');
 const serveUrl=await bundle({entryPoint:path.join(ROOT,'src/science-short-covers.tsx'),rootDir:ROOT,publicDir,outDir:fs.mkdtempSync(path.join(OUT,'bundle-'))});
 const browser=await openBrowser('chrome',{browserExecutable:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'}),covers=[];
 try{
  for(const film of ['perceptron','optogenetics'])for(const lang of ['zh','en'])for(const shape of ['portrait','landscape']){
   const composition=await selectComposition({serveUrl,id:shape==='portrait'?'ShortCoverPortrait':'ShortCoverLandscape',inputProps:{film,lang},puppeteerInstance:browser});
   const folder=path.join(OUT,film);fs.mkdirSync(folder,{recursive:true});const output=path.join(folder,`cover.${shape}.${lang}.jpg`);
   await renderStill({composition,serveUrl,inputProps:{film,lang},puppeteerInstance:browser,frame:0,output,imageFormat:'jpeg',jpegQuality:95});
   const probe=JSON.parse(run('ffprobe',['-v','error','-show_entries','stream=width,height','-of','json',output])).streams[0];
   const dimensions=shape==='portrait'?[1080,1920]:[1280,720];if(probe.width!==dimensions[0]||probe.height!==dimensions[1])throw Error('Incorrect cover dimensions');
   covers.push({film,language:lang,shape,path:path.relative(ROOT,output),size:dimensions,bytes:fs.statSync(output).size,sha256:hash(output)});
   console.log('Cover',film,lang,shape);
  }
 }finally{await browser.close({silent:true});}
 const manifest={designs:4,files:covers.length,sourceFrames:sources,copy:{perceptron:{zh:[`比Claude Fable 5.1快${data.values.claude_million_zh}万倍`,`比GPT-6-Astra快${data.values.astra_ten_million_zh}万倍！`],en:[`${data.values.claude_million_en} million times faster than Claude Fable 5.1`,`${data.values.astra_ten_million_en} million times faster than GPT-6-Astra`]},optogenetics:{zh:['1分钟了解','2026诺贝尔奖','光遗传学','生理学或医学奖'],en:['In 1 minute','2026 Nobel Prize','Optogenetics','Physiology or Medicine']}},
  typography:'One language per cover; canonical model names preserved. All wording, digits and the original test-picture seven are code-rendered. No logo, series ribbon or QR.',
  framing:'Perceptron landscape keeps the complete owner-selected 00:02 source frame; portrait uses the film\'s fixed center framing. Optogenetics portrait keeps the complete goggles frame in a wide insert.',covers};
 fs.writeFileSync(path.join(DOC,'covers.json'),JSON.stringify(manifest,null,2)+'\n');
 console.log('Verified',covers.length,'covers:',OUT);
}
main().catch(error=>{console.error(error);process.exitCode=1;});
