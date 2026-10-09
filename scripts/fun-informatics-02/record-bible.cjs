/** Record the live Bible app, with display-only layout for a bilingual film pane.
 * Game text, segmentation, choices and feedback are the deployed app's own.
 * node scripts/fun-informatics-02/record-bible.cjs [asset-name]
 */
const {chromium} = require('/Users/yqin/repo/ai-testing/node_modules/playwright');
const {spawnSync} = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');
const ROOT = path.resolve(__dirname, '../..');
const OUT = path.join(ROOT, 'public/fun-informatics-02/footage');
const RAW = path.join(ROOT, 'out/fun-informatics-02/recordings');
const SPECS = [
  ['letters-jhn316-zh', 'JHN.3.16', 'CUV', 'letters', false],
  ['letters-jhn316-en', 'JHN.3.16', 'WEB', 'letters', false],
  ['letters-pro2511-zh', 'PRO.25.11', 'CUV', 'letters', true],
  ['letters-pro2511-en', 'PRO.25.11', 'WEB', 'letters', true],
  ['words-psa231-en', 'PSA.23.1', 'WEB', 'words', true],
  ['words-psa231-zh', 'PSA.23.1', 'CUV', 'words', true],
];
const layout = `
  body { margin:0!important; overflow:hidden!important; }
  .app {width:1600px!important;max-width:none!important;margin:0!important;padding:0!important;}
  .app-header, header, footer {display:none!important;}
  main, .stage {padding:0!important; margin:0!important; width:1600px!important; max-width:none!important; height:350px!important; min-height:0!important;}
  .stage {align-items:stretch!important; justify-content:center!important;}
  .card.guess {box-sizing:border-box!important;align-self:center!important;flex-shrink:0!important;width:1550px!important; max-width:1550px!important; height:330px!important; margin:10px auto!important; padding:18px 38px!important; border-radius:20px!important; overflow:hidden!important; display:flex!important; flex-direction:column!important;}
  .guess__heading {display:none!important;}
  .guess__verse {font-size:56px!important; line-height:1.38!important; flex:1!important; min-height:0!important; max-height:155px!important; overflow:auto!important; scrollbar-width:none!important; margin:0!important; padding:6px 0!important;}
  .guess__play {flex:0 0 auto!important; position:relative!important; margin-top:12px!important; padding-top:12px!important;}
  .guess__prompt {font-size:23px!important; margin:0 0 10px!important;}
  .guess__options {display:flex!important; gap:18px!important; justify-content:center!important;}
  .guess__options button {font-size:56px!important; min-width:135px!important; min-height:65px!important; padding:8px 22px!important;}
  .guess__insight,.guess__actions,.guess__summary .btn-row {display:none!important;}
  .guess__summary {font-size:26px!important;}
`;

async function gameProps(page) {
  return page.evaluate(() => {
    const el = document.querySelector('.guess');
    const key = Object.keys(el).find(k => k.startsWith('__reactFiber$'));
    for(let fiber=el[key];fiber;fiber=fiber.return) if(fiber.memoizedProps?.game?.steps) return {game:fiber.memoizedProps.game, reference:fiber.memoizedProps.reference};
    throw Error('Could not read the live game model');
  });
}

async function record(browser, spec) {
  const [name, passage, translation, kind, simulated] = spec;
  const seed = 251103;
  const url = `https://bible.lucasacademy.org/?passage=${passage}&translation=${translation}&game=${kind}`;
  const context = await browser.newContext({viewport:{width:1600,height:350}, deviceScaleFactor:1, recordVideo:{dir:RAW,size:{width:1600,height:350}}});
  await context.addInitScript(s => {Math.random = () => s / 1e9;}, seed);
  const recordingStarted = Date.now();
  const page = await context.newPage();
  await page.goto(url, {waitUntil:'networkidle'});
  await page.locator('.guess__options').waitFor({timeout:45000});
  await page.addStyleTag({content:layout});
  await page.waitForTimeout(600);
  const rect=await page.locator('.card.guess').boundingBox();
  if(rect.x<0||rect.x+rect.width>1601)throw Error(`${name}: game card clipped horizontally: ${JSON.stringify(rect)}`);
  const props = await gameProps(page);
  const events = [];
  const start = Date.now();
  const sourceLeadIn = (start - recordingStarted) / 1000;
  let ordinal = 0;
  for (const [stepIndex,step] of props.game.steps.entries()) {
    for (const [unitIndex,unit] of step.units.entries()) {
      await page.locator('.guess__verse').evaluate(el=>{el.scrollTop=el.scrollHeight;});
      const shown = await page.locator('.guess__options button').allTextContents();
      if(shown.join('|') !== unit.options.join('|')) throw Error(`${name}: live choices changed`);
      const shownAt=(Date.now()-start)/1000;
      const wait = ordinal < 2 ? 2200 : 1300;
      await page.waitForTimeout(wait);
      const wrong = simulated && (ordinal % 3 === 1 || ordinal % 5 === 2);
      if(wrong){
        const other=unit.options.find(x=>x!==unit.answer);
        await page.locator('.guess__options button').filter({hasText:new RegExp('^'+other.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')+'$')}).click();
        events.push({time:(Date.now()-start)/1000,action:'wrong',value:other,stepIndex,unitIndex});
        await page.waitForTimeout(850);
      }
      const answerIndex=unit.options.indexOf(unit.answer);
      await page.keyboard.press(String(answerIndex+1));
      events.push({time:(Date.now()-start)/1000,shownAt,action:'correct',value:unit.answer,word:step.word,shown:step.shown,stepIndex,unitIndex,options:unit.options});
      await page.waitForTimeout(300);
      ordinal++;
    }
  }
  await page.waitForTimeout(3000);
  await page.screenshot({path:path.join(RAW, name+'.png')});
  const video = page.video();
  const videoPath = await video.path();
  await context.close();
  const output = path.join(OUT,name+'.mp4');
  const encode = spawnSync('ffmpeg',['-v','error','-y','-ss',sourceLeadIn.toFixed(3),'-i',videoPath,'-vf','fps=30','-an','-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',output],{stdio:'inherit'});
  if(encode.status!==0)throw Error('ffmpeg failed for '+name);
  const meta={name,url,recorded:new Date().toISOString().slice(0,10),seed,kind,translation,simulated,displayOnlyLayout:true,trimmedSourceLeadInSeconds:sourceLeadIn,videoStartOffsetSeconds:0,events,game:props.game};
  fs.writeFileSync(path.join(OUT,name+'.json'),JSON.stringify(meta,null,2)+'\n');
  console.log(name+': '+ordinal+' single '+(kind==='letters'?'characters':'words')+' recorded');
}

(async()=>{
  fs.mkdirSync(OUT,{recursive:true});fs.mkdirSync(RAW,{recursive:true});
  const browser=await chromium.launch({headless:true});
  try {for(const spec of SPECS){if(process.argv[2]&&process.argv[2]!==spec[0])continue; await record(browser,spec);}}
  finally {await browser.close();}
})().catch(error=>{console.error(error);process.exit(1);});
