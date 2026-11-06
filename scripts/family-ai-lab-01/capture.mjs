/** Genuine browser recordings. The capture-only adapter imports the selected
 * trained 419-picture state at 20x20. Python predict/train and the 3x3 activity
 * are unchanged. Nothing writes back to lucas-academy-ai or benchmark results.
 * Serve the sibling curriculum with: python3 -m http.server 8149 --bind 127.0.0.1
 * Runtime: PLAYWRIGHT_DIR=<directory containing package.json>, or bundled runtime.
 */
import {createRequire} from 'node:module';
import {readFileSync, writeFileSync, mkdirSync, copyFileSync} from 'node:fs';
import {resolve, dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {spawnSync} from 'node:child_process';
import {createHash} from 'node:crypto';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '../..');
const runtime = process.env.PLAYWRIGHT_DIR || `${process.env.HOME}/.cache/codex-runtimes/codex-primary-runtime/dependencies/node`;
const {chromium} = createRequire(resolve(runtime, 'package.json'))('playwright');
const out = resolve(ROOT, 'public/family-ai-lab-01/capture');
mkdirSync(out, {recursive: true});
const original = readFileSync(resolve(ROOT, '../lucas-academy-ai/L2-lower-intermediate/perceptron/perceptron.html'), 'utf8');
const model = JSON.parse(readFileSync(resolve(ROOT, 'public/family-ai-lab-01/trained-model.json'), 'utf8'));
let adapter = original;
const a = adapter.indexOf('      examples: [', adapter.indexOf('  20: ['));
const b = adapter.indexOf('] },', a) + 1;
if(a < 0 || b <= a) throw Error('Curriculum structure changed. Review the capture adapter.');
adapter = adapter.slice(0, a) + '      examples: ' + JSON.stringify(model.examples) + adapter.slice(b);
adapter = adapter.replace('state.points = blank(n);', `state.points = n === 20 ? ${JSON.stringify(model.points)} : blank(n);`)
 .replace('state.rounds = 0; state.fixes = 0;', `state.rounds = n === 20 ? ${model.rounds} : 0; state.fixes = 0;`)
 .replace("say(set ? 'All points start at 0: it knows nothing yet.' : 'Empty. Draw something!');",
 "say(n === 20 ? 'Restored trained model: 419 training pictures. No timing measurement.' : (set ? 'All points start at 0: it knows nothing yet.' : 'Empty. Draw something!'));")
 .replace("renderPython();\nloadSet(3, 'mid');", "window.__fal01Read = () => ({points:state.points.slice(),rounds:state.rounds,n:state.n,examples:state.examples.length});\nrenderPython();\nloadSet(3, 'mid');");
for (const name of ['PREDICT_CODE','TRAIN_CODE']) {
 const expr = new RegExp('const '+name+' = `([\\s\\S]*?)`;');
 if(original.match(expr)?.[1] !== adapter.match(expr)?.[1]) throw Error('Learning code changed');
}
writeFileSync(resolve(out,'perceptron.capture.html'), adapter);
copyFileSync(resolve(ROOT, '../lucas-academy-ai/L2-lower-intermediate/perceptron/perceptron.html'),resolve(out,'perceptron.original.html'));
const browser = await chromium.launch({headless:true,channel:'chrome'});
const context = await browser.newContext({viewport:{width:1920,height:1280},recordVideo:{dir:resolve(out,'raw'),size:{width:1920,height:1280}}});
const page = await context.newPage();
const url='http://127.0.0.1:8149/L2-lower-intermediate/perceptron/perceptron.html';
await page.route(url, route=>route.fulfill({status:200,contentType:'text/html',body:adapter}));
await page.goto(url);
await page.waitForFunction(()=>document.getElementById('pystatText').textContent.includes('runs this code'),{timeout:45000});
const now=()=>Date.now()/1000;
const epoch=now(),events=[];
const mark=(name)=>events.push({name,seconds:now()-epoch});
await page.waitForTimeout(1500);mark('three-zero');
await page.screenshot({path:resolve(out,'three-zero.png')});
await page.locator('#roundBtn').hover();await page.waitForTimeout(800);mark('click-round');
await page.locator('#roundBtn').click();
await page.waitForFunction(()=>document.getElementById('stopBtn').hidden);
mark('round-one-complete');
const after=await page.locator('#ptsData').innerText();
if(!after.includes('1'))throw Error('3x3 points did not change');
await page.screenshot({path:resolve(out,'three-round.png')});
await page.waitForTimeout(2400);
await page.locator('#untilBtn').click();await page.waitForFunction(()=>document.getElementById('stopBtn').hidden);
await page.waitForTimeout(2200);mark('three-trained');
await page.screenshot({path:resolve(out,'three-trained.png')});
await page.getByRole('button',{name:'20 × 20',exact:true}).click();
await page.waitForFunction(()=>document.getElementById('stats').textContent.includes('419/419'));
await page.evaluate(()=>window.scrollTo({top:0,behavior:'smooth'}));
mark('twenty-trained');await page.waitForTimeout(2200);
await page.screenshot({path:resolve(out,'twenty-trained.png')});
const final=await page.evaluate(()=>window.__fal01Read());
if(final.examples!==419 || final.points.some((v,i)=>v!==model.points[i]))throw Error('Wrong trained model in capture');
await page.waitForTimeout(2500);mark('end');
await context.close();
const raw=await page.video().path();
const result=spawnSync('ffmpeg',['-v','error','-y','-i',raw,'-an','-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-r','30','-movflags','+faststart',resolve(out,'lab.mp4')],{stdio:'inherit'});
if(result.status!==0)throw Error('Capture encode failed');
const crop=spawnSync('ffmpeg',['-v','error','-y','-i',resolve(out,'twenty-trained.png'),'-vf','crop=380:380:649:263','-frames:v','1',resolve(out,'twenty-points.png')],{stdio:'inherit'});
if(crop.status!==0)throw Error('Points crop failed');
await browser.close();
writeFileSync(resolve(ROOT,'docs/family-ai-lab-01/capture.json'),JSON.stringify({url,events,originalSha256:createHash('sha256').update(original).digest('hex'),
 adapter:'20x20 imports the selected trained 419-picture state. Original Python predict/train unchanged. 3x3 uses original UI training. No benchmark calls.',
 baselineBenchmarkRerun:false,pointsChangedIn3x3:after,final:{n:final.n,examples:final.examples,rounds:final.rounds}},null,2)+'\n');
console.log('Captured',events);
