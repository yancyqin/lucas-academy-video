/** Record the coding-class homework page as a real process for oc07-01: write, run, read the console, fix, run again.
 * The page is the live lucasacademy.org homework "Score starts at zero". Only the layout is changed for the film
 * (description, header and submit form hidden; code and console enlarged); the code runs on the page itself and
 * nothing is submitted.
 *   node scripts/fun-economics-01/record-homework.cjs
 */
const {chromium} = require('/Users/yqin/repo/ai-testing/node_modules/playwright');
const {spawnSync} = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');

const ROOT = path.resolve(__dirname, '../..');
const OUT = path.join(ROOT, 'public/fun-economics-01/footage');
const RAW = path.join(ROOT, 'out/fun-economics-01/recordings');
const URL = 'https://lucasacademy.org/programs/coding-class/score-homework';
const layout = `
  header.challenge-header, section.description, section.submit, .editor-help { display: none !important; }
  html, body { margin: 0 !important; background: #15171c !important; overflow: hidden !important; }
  main.workspace { display: block !important; padding: 32px 40px !important; height: 1080px !important; box-sizing: border-box !important; }
  .right-stack { display: grid !important; grid-template-columns: 1.3fr 1fr !important; gap: 28px !important; height: 1016px !important; }
  section.editor.pane, section.console.pane { height: 1016px !important; display: flex !important; flex-direction: column !important; margin: 0 !important; }
  .code-editor-wrap { flex: 1 1 auto !important; height: auto !important; }
  textarea#code-editor, pre#line-numbers { font-size: 38px !important; line-height: 1.6 !important; height: 100% !important; }
  pre#console-output { font-size: 72px !important; line-height: 1.35 !important; padding: 36px 44px !important; flex: 1 1 auto !important; }
  .pane-tab { font-size: 34px !important; padding: 20px 28px !important; }
  .pane-tab * { font-size: 30px !important; }
  button#run-code { font-size: 36px !important; padding: 16px 34px !important; height: auto !important; }
  #editor-message { font-size: 28px !important; }
  .editor-footer { padding: 18px 26px !important; }
  p#test-result { font-size: 34px !important; line-height: 1.4 !important; padding: 0 44px 32px !important; margin: 0 !important; }
`;

async function caretAtLine(page, index) {
  await page.locator('#code-editor').evaluate((el, i) => {
    const lines = el.value.split('\n');
    const pos = lines.slice(0, i).reduce((n, l) => n + l.length + 1, 0) + lines[i].length;
    el.focus();
    el.setSelectionRange(pos, pos);
  }, index);
}

(async () => {
  fs.mkdirSync(OUT, {recursive: true});
  fs.mkdirSync(RAW, {recursive: true});
  const browser = await chromium.launch({headless: true});
  const context = await browser.newContext({viewport: {width: 1920, height: 1080}, deviceScaleFactor: 1,
    recordVideo: {dir: RAW, size: {width: 1920, height: 1080}}});
  const recordingStarted = Date.now();
  const page = await context.newPage();
  await page.goto(URL, {waitUntil: 'networkidle'});
  await page.addStyleTag({content: layout});
  await page.waitForTimeout(800);
  const start = Date.now();
  const sourceLeadIn = (start - recordingStarted) / 1000;
  const events = [];
  const mark = action => events.push({time: +((Date.now() - start) / 1000).toFixed(2), action});
  const startLines = (await page.locator('#code-editor').inputValue()).split('\n');
  if (startLines[1] !== '' || startLines[5] !== '') throw Error('The homework starter code changed: ' + JSON.stringify(startLines));

  await page.waitForTimeout(1200);
  await caretAtLine(page, 1);
  mark('type score = 0');
  await page.keyboard.type('score = 0', {delay: 110});
  await page.waitForTimeout(700);
  mark('run (forgot TODO 2)');
  await page.locator('#run-code').click();
  await page.waitForTimeout(2600);
  const first = await page.locator('#console-output').innerText();
  mark('console: ' + first.replace(/\n/g, ' / '));
  await caretAtLine(page, 5);
  mark('type score = score + 10');
  await page.keyboard.type('score = score + 10', {delay: 90});
  await page.waitForTimeout(700);
  mark('run again');
  await page.locator('#run-code').click();
  await page.waitForTimeout(3000);
  const second = await page.locator('#console-output').innerText();
  mark('console: ' + second.replace(/\n/g, ' / '));
  if (!/^\s*0\s+0\s*$/.test(first) || !/^\s*0\s+10\s*$/.test(second)) throw Error(`Unexpected console output: ${first} | ${second}`);

  await page.screenshot({path: path.join(RAW, 'homework.png')});
  const videoPath = await page.video().path();
  await context.close();
  await browser.close();
  const output = path.join(OUT, 'homework.mp4');
  const encode = spawnSync('ffmpeg', ['-v', 'error', '-y', '-ss', sourceLeadIn.toFixed(3), '-i', videoPath, '-vf', 'fps=30', '-an',
    '-c:v', 'libx264', '-crf', '18', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', output], {stdio: 'inherit'});
  if (encode.status !== 0) throw Error('ffmpeg failed');
  const meta = {url: URL, recorded: new Date().toISOString().slice(0, 10), displayOnlyLayout: true, submitted: false,
    trimmedSourceLeadInSeconds: sourceLeadIn, events};
  fs.writeFileSync(path.join(OUT, 'homework.json'), JSON.stringify(meta, null, 2) + '\n');
  console.log(JSON.stringify(events, null, 1));
})().catch(error => { console.error(error); process.exit(1); });
