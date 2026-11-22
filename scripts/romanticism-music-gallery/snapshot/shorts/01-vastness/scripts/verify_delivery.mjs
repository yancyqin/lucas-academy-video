import{createRequire}from'node:module';
import{readFile,writeFile,readdir,stat}from'node:fs/promises';
import{createHash}from'node:crypto';
import{pathToFileURL}from'node:url';
import path from'node:path';
const ROOT=path.resolve(import.meta.dirname,'..');
const DEST='@USER_HOME@/Desktop/山、海、人间-短视频示范';
const require=createRequire('@RUNTIME_DEPS@/node/package.json');
const{chromium}=require('playwright');
const browser=await chromium.launch({headless:true,executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'});
try{
 const page=await browser.newPage({viewport:{width:430,height:980}}),errors=[];
 page.on('pageerror',e=>errors.push(e.message));
 await page.goto(pathToFileURL(path.join(DEST,'打开预览.html')).href);
 const video=page.locator('video');
 const playback=await video.evaluate(async v=>{
  if(v.readyState<1)await new Promise((resolve,reject)=>{v.addEventListener('loadedmetadata',resolve,{once:true});v.addEventListener('error',()=>reject(new Error('Metadata failed')),{once:true})});
  v.muted=true;await v.play();const until=performance.now()+6000;
  while(v.currentTime<.2&&performance.now()<until)await new Promise(r=>setTimeout(r,30));v.pause();
  return{duration:v.duration,width:v.videoWidth,height:v.videoHeight,currentTime:v.currentTime,error:v.error?.message??null};
 });
 if(playback.width!==1080||playback.height!==1920||Math.abs(playback.duration-58)>.05||playback.currentTime<.15||playback.error)throw Error(JSON.stringify(playback));
 const seeks=[];
 for(const time of[2,14,23.5,35,46,56]){
  seeks.push(await video.evaluate(async(v,t)=>{await new Promise(resolve=>{v.addEventListener('seeked',resolve,{once:true});v.currentTime=t});return{time:v.currentTime,error:v.error?.message??null}},time));
 }
 await page.locator('select').selectOption('zh');
 const translations=[];
 for(const[time,expected]of[[2,'面对辽阔'],[6,'肖邦 ·《雨滴》前奏曲'],[14,'雾海上的旅人\n卡斯帕·大卫·弗里德里希'],[35,'吕根岛白垩岩\n卡斯帕·大卫·弗里德里希']]){
  const text=await video.evaluate(async(v,t)=>{await new Promise(resolve=>{v.addEventListener('seeked',resolve,{once:true});v.currentTime=t});return[...(v.textTracks[0].activeCues??[])].map(c=>c.text).join('\n')},time);
  if(text!==expected)throw Error(JSON.stringify({time,text,expected}));translations.push({time,text});
 }
 await page.screenshot({path:path.join(ROOT,'checks/desktop-preview.jpg'),type:'jpeg',quality:90});
 const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth);
 if(errors.length||overflow)throw Error(JSON.stringify({errors,overflow}));
 const result={status:'passed',playback,seeks,translations,pageErrors:errors,mobileOverflow:overflow};
 await writeFile(path.join(ROOT,'checks/browser-verified.json'),JSON.stringify(result,null,2));
 for(const file of[path.join(ROOT,'checks/verified.json'),path.join(DEST,'校验记录.json')]){
  const report=JSON.parse(await readFile(file,'utf8'));report.browser_review=result;await writeFile(file,JSON.stringify(report,null,2));
 }
 const parent=path.dirname(DEST),reportPath=path.join(parent,'资料/校验记录.json');
 const reportText=await readFile(reportPath,'utf8').catch(error=>{if(error.code==='ENOENT')return null;throw error});
 if(reportText){
 const report=JSON.parse(reportText);
 for(const name of await readdir(DEST)){
  const file=path.join(DEST,name);if(!(await stat(file)).isFile())continue;
  const relative='短视频示范/'+name,data=await readFile(file);
  report.all_files=report.all_files.filter(x=>x.file!==relative);
  report.all_files.push({file:relative,bytes:data.length,sha256:createHash('sha256').update(data).digest('hex')});
 }
 report.all_files.sort((a,b)=>a.file.localeCompare(b.file));report.portrait_sample={title:'Facing the Vastness',duration_seconds:58,dimensions:[1080,1920],english_labels:true,chinese_srt:true,browser_verified:true};
 await writeFile(reportPath,JSON.stringify(report,null,2));
 }
 console.log(JSON.stringify(result,null,2));
}finally{await browser.close()}
