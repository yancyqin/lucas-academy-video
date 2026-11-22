const {chromium}=require('/Users/yqin/repo/ai-testing/node_modules/playwright');
const fs=require('node:fs');
const OUT='/Users/yqin/repo/playground/lucas-academy-video-data/curiosity-builds-20261118/v4/records';
(async()=>{
 const browser=await chromium.launch({channel:'chrome',headless:true,args:['--use-angle=metal','--enable-gpu','--ignore-gpu-blocklist','--autoplay-policy=no-user-gesture-required']});
 const ctx=await browser.newContext({viewport:{width:1600,height:900},locale:'en-US'});
 await ctx.addInitScript(()=>{localStorage.setItem('inception.subtitles.v1',JSON.stringify({enabled:false,language:'en'}));});
 const page=await ctx.newPage();
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 const url=process.argv[2]||'http://127.0.0.1:5190/?world=museum&room=the-manifold&debug&manual=1&hud=0&fullscreen=0';
 await page.goto(url,{waitUntil:'networkidle',timeout:120000});
 await page.waitForTimeout(2500);
 if(await page.evaluate(()=>!!window.__museum)){
  for(let i=0;i<45;i++){await page.evaluate(()=>window.__museum.step(1000/30,15));await page.waitForTimeout(150);}
 }
 console.log(JSON.stringify({url,text:(await page.locator('body').innerText()).slice(0,10000),probe:await page.evaluate(()=>window.__museum?.probe()),errors},null,2));
 await page.screenshot({path:OUT+'/inspect.png'});
 await browser.close();
})();
