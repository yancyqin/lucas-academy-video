import {createRequire} from 'node:module';
import {readFile,writeFile,readdir,stat} from 'node:fs/promises';
import {createReadStream} from 'node:fs';
import {createHash} from 'node:crypto';
import {pathToFileURL} from 'node:url';
import path from 'node:path';

const ROOT=path.resolve(import.meta.dirname,'..');
const DEST='@USER_HOME@/Desktop/山、海、人间-竖屏短视频-上传';
const require=createRequire('@RUNTIME_DEPS@/node/package.json');
const {chromium}=require('playwright');
const films=JSON.parse(await readFile(path.join(DEST,'资料/播放与字幕数据.json'),'utf8'));
const browser=await chromium.launch({headless:true,executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'});
const assert=(ok,message)=>{if(!ok)throw Error(message)};
const results=[];
async function seek(video,time){
 return video.evaluate(async(v,t)=>{
  await new Promise((resolve,reject)=>{
   const timer=setTimeout(()=>reject(Error('Seek timed out at '+t)),7000);
   v.addEventListener('seeked',()=>{clearTimeout(timer);resolve()},{once:true});v.currentTime=t;
  });
  await new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)));
  return {time:v.currentTime,error:v.error?.message??null};
 },time);
}
try{
 const page=await browser.newPage({viewport:{width:1360,height:1120}}),errors=[];
 page.on('pageerror',error=>errors.push(error.message));
 await page.goto(pathToFileURL(path.join(DEST,'打开预览.html')).href);
 const video=page.locator('video');
 assert(await page.locator('button[data-index]').count()===films.length,'Expected a playlist button per film');
 for(let i=0;i<films.length;i++){
  const film=films[i];
  for(const key of ['src','srt','poster','englishMetadata','chineseMetadata'])assert((await stat(path.join(DEST,film[key]))).isFile(),'Missing '+film[key]);
  await page.locator('select').selectOption('off');
  await page.locator('button[data-index="'+i+'"]').click();
  await page.waitForFunction(index=>window.currentFilm===index&&document.querySelector('video').readyState>=1,i,{timeout:10000});
  const playback=await video.evaluate(async v=>{
   v.muted=true;await v.play();const until=performance.now()+7000;
   while(v.currentTime<.2&&performance.now()<until)await new Promise(resolve=>setTimeout(resolve,30));
   v.pause();return {duration:v.duration,width:v.videoWidth,height:v.videoHeight,currentTime:v.currentTime,error:v.error?.message??null};
  });
  assert(playback.width===1080&&playback.height===1920&&Math.abs(playback.duration-58)<.05&&playback.currentTime>.15&&!playback.error,JSON.stringify(playback));
  await page.locator('select').selectOption('zh');
  const cueCount=await video.evaluate(v=>v.textTracks[0].cues.length);
  assert(cueCount===4,'Old captions leaked into '+film.src+': '+cueCount);
  const subtitles=[];
  for(const cue of film.cues){
   const time=(cue.start+cue.end)/2;await seek(video,time);
   await page.waitForFunction(expected=>[...document.querySelector('video').textTracks[0].activeCues].map(c=>c.text).join('\n')===expected,cue.text,{timeout:3000});
   const text=await video.evaluate(v=>[...v.textTracks[0].activeCues].map(c=>c.text).join('\n'));
   subtitles.push({time,text});
  }
  const cueTime=text=>{const[h,m,s]=text.split(':');return Number(h)*3600+Number(m)*60+Number(s.replace(',','.'))};
  const blocks=(await readFile(path.join(DEST,film.srt),'utf8')).replace(/^\uFEFF/,'').trim().split(/\r?\n\r?\n/);
  assert(blocks.length===4,'Expected four SRT blocks');
  blocks.forEach((block,index)=>{
   const lines=block.split(/\r?\n/),[start,end]=lines[1].split(' --> '),expected=film.cues[index];
   assert(Math.abs(cueTime(start)-expected.start)<.001&&Math.abs(cueTime(end)-expected.end)<.001,'SRT timing mismatch '+film.src);
   assert(lines.slice(2).join('\n')===expected.text,'SRT text mismatch '+film.src);
  });
  const seeks=[];
  for(const time of [23.5,28.5,46,56]){
   const result=await seek(video,time);assert(!result.error,'Media error while seeking');seeks.push(result);
  }
  await seek(video,film.cues[2].start+1.5);
  await video.scrollIntoViewIfNeeded();
  await page.screenshot({path:path.join(ROOT,'checks/browser-'+(i+1)+'.jpg'),type:'jpeg',quality:88});
  results.push({file:film.src,status:'passed',playback,subtitles,seeks});
  console.log('PLAYBACK AND FOUR CHINESE CAPTIONS PASSED',film.src);
 }
 await page.setViewportSize({width:390,height:844});
 await page.locator('button[data-index="2"]').click();
 await page.waitForFunction(()=>document.querySelector('video').readyState>=1);
 await seek(video,14.3);await video.scrollIntoViewIfNeeded();
 await page.screenshot({path:path.join(ROOT,'checks/browser-mobile.jpg'),type:'jpeg',quality:90});
 const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth);
 assert(!overflow&&!errors.length,JSON.stringify({overflow,errors}));
 const result={status:'passed',films:results,checked_captions:films.reduce((n,f)=>n+f.cues.length,0),pageErrors:errors,mobileOverflow:overflow};
 await writeFile(path.join(ROOT,'checks/browser-verified.json'),JSON.stringify(result,null,2)+'\n');
 async function walk(folder){let files=[];for(const entry of await readdir(folder,{withFileTypes:true})){const file=path.join(folder,entry.name);files.push(...(entry.isDirectory()?await walk(file):[file]));}return files;}
 const reportPath=path.join(DEST,'资料/校验记录.json');
 const manifest=[];
 for(const file of (await walk(DEST)).sort()){
  if(file===reportPath)continue;
  const hash=createHash('sha256');for await(const chunk of createReadStream(file))hash.update(chunk);
  manifest.push({file:path.relative(DEST,file),bytes:(await stat(file)).size,sha256:hash.digest('hex')});
 }
 const report=JSON.parse(await readFile(reportPath,'utf8'));
 report.status='passed';report.browser_review=result;report.all_files=manifest;
 await writeFile(reportPath,JSON.stringify(report,null,2)+'\n');
 const deliveryPath=path.join(ROOT,'checks/desktop-package.json');
 const delivery=JSON.parse(await readFile(deliveryPath,'utf8'));
 delivery.status='passed';delivery.browser_review=result;delivery.files=manifest.length;
 await writeFile(deliveryPath,JSON.stringify(delivery,null,2)+'\n');
 const batch=JSON.parse(await readFile(path.join(ROOT,'batch.json'),'utf8'));
 for(const [index,job]of batch.jobs.entries()){
  const file=path.join(job.root,'checks/verified.json'),evidence=JSON.parse(await readFile(file,'utf8'));
  evidence.browser_review=results[index+1];await writeFile(file,JSON.stringify(evidence,null,2)+'\n');
 }
 console.log('DESKTOP PACKAGE PASSED',films.length,'films,',manifest.length,'files,',result.checked_captions,'captions');
}finally{await browser.close()}
