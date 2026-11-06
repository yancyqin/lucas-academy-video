/** Record the actual saved curriculum with its normal controls; never modify it. */
import {createRequire} from 'node:module';
import {mkdirSync,writeFileSync,readFileSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {spawnSync} from 'node:child_process';
import {createHash} from 'node:crypto';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'../..');
const runtime=process.env.PLAYWRIGHT_DIR||`${process.env.HOME}/.cache/codex-runtimes/codex-primary-runtime/dependencies/node`;
const {chromium}=createRequire(resolve(runtime,'package.json'))('playwright');
const pub=resolve(root,'public/family-ai-lab-02'),out=resolve(pub,'capture');mkdirSync(out,{recursive:true});
const browser=await chromium.launch({headless:true,channel:'chrome'});
try {
 const context=await browser.newContext({viewport:{width:1280,height:720},recordVideo:{dir:resolve(out,'raw'),size:{width:1280,height:720}}});
 const page=await context.newPage();
 await page.goto(pathToFileURL(resolve(pub,'lab/binary.html')).href);
 await page.getByRole('button',{name:'All off',exact:true}).click();
 const start=Date.now(),events=[];
 await page.waitForTimeout(750);
 const video=page.video();
 await page.getByRole('button',{name:'Weight 64: 0',exact:true}).hover();await page.waitForTimeout(400);await page.getByRole('button',{name:'Weight 64: 0',exact:true}).click();events.push({action:'Weight 64',seconds:(Date.now()-start)/1000});
 await page.waitForTimeout(1000);
 await page.getByRole('button',{name:'Weight 1: 0',exact:true}).hover();await page.waitForTimeout(400);await page.getByRole('button',{name:'Weight 1: 0',exact:true}).click();events.push({action:'Weight 1',seconds:(Date.now()-start)/1000});
 const result=await page.locator('#result').innerText();
 if(!result.includes('01000001 = 65 → A'))throw Error('Wrong actual lab result: '+result);
 await page.waitForTimeout(1800);await page.screenshot({path:resolve(out,'lab-a.png')});
 await context.close();
 const raw=await video.path();
 const encoded=resolve(out,'lab.mp4');
 const r=spawnSync('ffmpeg',['-v','error','-y','-i',raw,'-an','-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-r','30','-movflags','+faststart',encoded],{stdio:'inherit'});
 if(r.status!==0)throw Error('Capture encode failed');
 const probe=JSON.parse(spawnSync('ffprobe',['-v','error','-show_entries','stream=nb_frames','-of','json',encoded],{encoding:'utf8'}).stdout);
 const record={frames:Number(probe.streams[0].nb_frames),events,result,source:'Unmodified snapshot of lucas-academy-ai/assets/labs/binary.html, lab.css, lab.js, math.js. Native All off/Weight buttons.',sha256:createHash('sha256').update(readFileSync(encoded)).digest('hex')};
 writeFileSync(resolve(pub,'capture.json'),JSON.stringify(record,null,2)+'\n');
 writeFileSync(resolve(root,'docs/family-ai-lab-02/capture.json'),JSON.stringify(record,null,2)+'\n');
 console.log('Captured actual lab',record);
} finally {await browser.close();}
