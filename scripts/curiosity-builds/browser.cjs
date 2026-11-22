const {chromium}=require('/Users/yqin/repo/ai-testing/node_modules/playwright');
(async()=>{
 const browser=await chromium.launch({channel:'chrome',headless:true,args:['--remote-debugging-port=9237','--use-angle=metal','--enable-gpu','--ignore-gpu-blocklist','--autoplay-policy=no-user-gesture-required','--window-size=1920,1167']});
 const context=await browser.newContext({viewport:{width:1920,height:1080},locale:'en-US',deviceScaleFactor:1});
 await context.addInitScript(()=>{localStorage.setItem('inception.subtitles.v1',JSON.stringify({enabled:false,language:'en'}));localStorage.setItem('inception.display.v1',JSON.stringify({brightness:1.15,reducedMotion:false}));});
 await context.newPage();
 console.log('Capture browser ready on http://127.0.0.1:9237');
 setInterval(()=>{},30000);
})();
