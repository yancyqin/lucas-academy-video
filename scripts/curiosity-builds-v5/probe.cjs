const {chromium}=require('/Users/yqin/repo/ai-testing/node_modules/playwright');
const fs=require('node:fs');
const OUT='/Users/yqin/repo/playground/lucas-academy-video-data/curiosity-builds-20261118/v5/records';
(async()=>{
 const browser=await chromium.connectOverCDP('http://127.0.0.1:9238');
 const ctx=browser.contexts()[0];const page=ctx.pages()[0];
 if(process.argv[2])await page.goto(process.argv[2],{waitUntil:'domcontentloaded',timeout:45000});
 await page.waitForTimeout(1800);
 if(process.argv[3]){const fn=fs.readFileSync(process.argv[3],'utf8');console.log(await page.evaluate(fn));}
 console.log(JSON.stringify({text:(await page.locator('body').innerText()).slice(0,11000),probe:await page.evaluate(()=>window.__museum?.probe())},null,2));
 await page.screenshot({path:OUT+'/probe.png'});
 await browser.close();
})();
