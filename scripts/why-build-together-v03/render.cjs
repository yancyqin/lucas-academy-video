const {bundle}=require('@remotion/bundler');
const {openBrowser,selectComposition,renderMedia,renderStill}=require('@remotion/renderer');
const fs=require('node:fs');const path=require('node:path');
const ROOT=path.resolve(__dirname,'../..');const OUT=path.join(ROOT,'out/why-build-together-v03');
(async()=>{
 const plan=JSON.parse(fs.readFileSync(path.join(OUT,'timeline.json'),'utf8'));
 const publicDir=path.join(OUT,'assets');fs.mkdirSync(publicDir,{recursive:true});
 const assets=fs.existsSync(path.join(OUT,'assets.json'))?JSON.parse(fs.readFileSync(path.join(OUT,'assets.json'),'utf8')):{};
 const stills=process.argv.includes('--stills');
 if(!stills)for(const id of ['G01','G02','G03','G04','G05','G06'])if(!fs.existsSync(path.join(publicDir,id+'.mp4')))throw new Error('Muse media missing: '+id);
 const serveUrl=await bundle({entryPoint:path.join(ROOT,'src/videos/why-build-together-v03/Film.tsx'),publicDir});
 const browser=await openBrowser('chrome',{browserExecutable:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'});
 const labelChecks=[];
 if(stills){
  const originalNewPage=browser.newPage.bind(browser);
  browser.newPage=async(options)=>{
   const page=await originalNewPage(options);const close=page.close.bind(page);
   page.close=async(...args)=>{
    try{
     const pairs=await page.evaluate(()=>[...document.querySelectorAll('[data-bilingual-label]')].map(el=>{
      const lines=[...el.querySelectorAll('[data-lang]')].map(line=>({language:line.dataset.lang,
       text:line.textContent,fontSize:getComputedStyle(line).fontSize,fontWeight:getComputedStyle(line).fontWeight,
       overflow:line.scrollWidth>line.clientWidth+1}));
      const r=el.getBoundingClientRect();return {id:el.dataset.bilingualLabel,lines,
       bounds:{left:r.left,top:r.top,right:r.right,bottom:r.bottom}};
     }));
     for(const pair of pairs){
      const [zh,en]=pair.lines;
      if(pair.lines.length!==2||zh.language!=='zh'||en.language!=='en'||zh.fontSize!==en.fontSize||zh.fontWeight!==en.fontWeight)
       throw new Error('Bilingual label order or font mismatch: '+pair.id);
      if(pair.lines.some(l=>l.overflow)||pair.bounds.left<0||pair.bounds.top<0||pair.bounds.right>1921||pair.bounds.bottom>1081)
       throw new Error('Bilingual label outside picture: '+pair.id);
     }
     if(pairs.length)labelChecks.push(...pairs);
    }finally{await close(...args)}
   };
   return page;
  };
 }
 try{
 for(const piece of ['intro']){
  const inputProps={piece,scenes:plan.scenes,frames:plan[piece+'_frames'],assets};
  const composition=await selectComposition({serveUrl,id:'WhyBuildTogetherV03',inputProps,puppeteerInstance:browser});
  if(stills){
   const picks=plan.scenes.filter(s=>s.piece===piece);
   for(const s of picks){const frame=s.local_start+Math.min(s.frames-1,Math.round(s.frames*(s.id==='n011'?.45:.65)));await renderStill({serveUrl,composition,inputProps,frame,output:path.join(OUT,'still-'+s.id+'.png'),puppeteerInstance:browser});console.log('Still',s.id)}
   const idea=plan.scenes.find(s=>s.id==='n011');const lead=plan.scenes.find(s=>s.id==='n010').frames;
   await renderStill({serveUrl,composition,inputProps,frame:idea.local_start+(assets.G06.frames-lead)+35,output:path.join(OUT,'still-n011-curiosity.png'),puppeteerInstance:browser});
   const s=plan.scenes.find(s=>s.id==='n011');await renderStill({serveUrl,composition,inputProps,frame:s.local_start+Math.min(s.frames-1,Math.round(12*30)),output:path.join(OUT,'still-n011-drawing.png'),puppeteerInstance:browser});
  }else{
   let last=0;await renderMedia({serveUrl,composition,inputProps,codec:'h264',muted:true,outputLocation:path.join(OUT,piece+'-picture.mp4'),puppeteerInstance:browser,concurrency:3,x264Preset:'fast',crf:17,onProgress:p=>{if(p.renderedFrames-last>=180){last=p.renderedFrames;console.log(piece,p.renderedFrames+'/'+composition.durationInFrames)}}});console.log('Rendered',piece)
  }
 }
 if(stills){
  const expected=JSON.parse(fs.readFileSync(path.join(ROOT,'src/videos/why-build-together-v03/labels.json'),'utf8'));
  const seen=new Set(labelChecks.map(p=>p.id));
  for(const id of Object.keys(expected))if(!seen.has(id))throw new Error('Unreviewed bilingual label: '+id);
  fs.writeFileSync(path.join(OUT,'label-check.json'),JSON.stringify({status:'passed',uniqueLabels:seen.size,
   chineseFirst:true,equalFontSize:true,equalFontWeight:true,insideFrame:true,labels:labelChecks},null,2)+'\n');
  console.log('Bilingual label audit passed:',seen.size,'label pairs.');
 }
 }finally{await browser.close({silent:true})}
})().catch(e=>{console.error(e);process.exit(1)});
