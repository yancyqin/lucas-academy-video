/** Capture the arithmetic page (pages/fun-economics-01/multiplication-roads.html) frame by frame on the film's clock.
 *
 * The page animates with CSS transitions. Instead of recording it in real time, each step is started with
 * window.mathRoads.go(scene, step), every running animation is paused, and each frame is drawn by setting the
 * animations' currentTime: the picture is exact to the frame and in step with the narration. Steps start at the
 * times in public/fun-economics-01/markers.zh.json (check.py places them on spoken words). A frame with nothing
 * moving is copied instead of captured again. Writes public/fun-economics-01/footage/roads.<lang>.mp4, which starts
 * FADE before cue oc04-05 (where the composition starts fading the page in) and ends with oc05-02.
 *   node scripts/fun-economics-01/record-roads.cjs [en]
 * Another film recording the same page passes its folder, its first and last cue, the output name and extra page tokens:
 *   node scripts/fun-economics-01/record-roads.cjs en --film=fun-economics-01-7x8 --from=hx02-01 --to=hx03-01 --name=page --hash=solo
 */
const {chromium} = require('/Users/yqin/repo/ai-testing/node_modules/playwright');
const {spawnSync} = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');

const ROOT = path.resolve(__dirname, '../..');
const opt = (name, fallback) => (process.argv.find(a => a.startsWith(`--${name}=`)) || '').split('=')[1] || fallback;
const FILM = opt('film', 'fun-economics-01');
const PUB = path.join(ROOT, 'public', FILM);
const WORK = path.join(ROOT, 'out', FILM, 'roads-frames');
const FPS = 30;
const FADE = 0.3;  // the composition fades each background in this long before its first cue
const LANG = process.argv.includes('en') ? 'en' : 'zh';
const FROM = opt('from', 'oc04-05'), TO = opt('to', 'oc05-02'), NAME = opt('name', 'roads'), HASH = opt('hash', '');

(async () => {
  const tl = JSON.parse(fs.readFileSync(path.join(PUB, `timeline.${LANG}.json`), 'utf8'));
  const marks = JSON.parse(fs.readFileSync(path.join(PUB, `markers.${LANG}.json`), 'utf8'));
  const cue = id => tl.cues.find(c => c.id === id);
  const t0 = cue(FROM).start - FADE, t1 = cue(TO).end;
  const schedule = Object.entries(marks).map(([label, time]) => {
    const [scene, step] = label.slice(1).split('.').map(Number);
    return {time, scene, step, label};
  }).sort((a, b) => a.time - b.time || a.scene - b.scene || a.step - b.step);
  schedule[0].time = Math.min(schedule[0].time, t0);

  const html = fs.readFileSync(path.join(ROOT, 'pages/fun-economics-01/multiplication-roads.html'), 'utf8');
  fs.rmSync(WORK, {recursive: true, force: true});
  fs.mkdirSync(WORK, {recursive: true});
  const wrapper = path.join(WORK, 'page.html');
  fs.writeFileSync(wrapper, '<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head><body>\n' + html + '\n</body></html>\n');

  const browser = await chromium.launch({headless: true});
  const page = await browser.newPage({viewport: {width: 1920, height: 1080}, deviceScaleFactor: 1});
  await page.goto('file://' + wrapper + `#${LANG}-clean${HASH ? '-' + HASH : ''}`);
  await page.evaluate(() => document.fonts.ready);
  await page.waitForTimeout(800);
  // Every scene the film shows must have all its steps scheduled (the film may skip a whole scene, as it does s3).
  const steps = await page.evaluate(() => window.mathRoads.scenes.map(s => s.steps));
  steps.forEach((n, scene) => {
    const got = schedule.filter(x => x.scene === scene).length;
    if (got && got !== n) throw Error(`scene ${scene} has ${n} steps, markers.${LANG}.json ${got}; run check.py`);
  });

  const startStep = async item => page.evaluate(async ({scene, step}) => {
    document.getAnimations().forEach(a => { try { a.finish(); } catch (e) { a.cancel(); } });
    window.mathRoads.go(scene, step);
    await new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));
    const anims = document.getAnimations();
    anims.forEach(a => a.pause());
    window.__anims = anims.map(a => ({a, end: a.effect.getComputedTiming().endTime}));
    return Math.max(0, ...window.__anims.map(x => x.end));
  }, item);
  const seek = async ms => page.evaluate(ms => { window.__anims.forEach(({a, end}) => { a.currentTime = Math.min(ms, end); }); }, ms);

  const frames = Math.round((t1 - t0) * FPS);
  let current = -1, stepStart = 0, stepEnd = 0, lastFile = null, captured = 0;
  for (let i = 0; i < frames; i++) {
    const t = t0 + i / FPS;
    let k = current;
    while (k + 1 < schedule.length && schedule[k + 1].time <= t) k++;
    if (k < 0) k = 0;
    const fresh = k !== current;
    if (fresh) {
      current = k;
      stepStart = schedule[k].time;
      stepEnd = await startStep(schedule[k]);
    }
    const ms = (t - stepStart) * 1000;
    const out = path.join(WORK, String(i).padStart(6, '0') + '.png');
    if (!fresh && lastFile && ms > stepEnd + 50) {
      fs.linkSync(lastFile, out);
      continue;
    }
    await seek(ms);
    await page.screenshot({path: out});
    lastFile = out;
    captured++;
  }
  await browser.close();
  const output = path.join(PUB, `footage/${NAME}.${LANG}.mp4`);
  const r = spawnSync('ffmpeg', ['-v', 'error', '-y', '-framerate', String(FPS), '-i', path.join(WORK, '%06d.png'),
    '-c:v', 'libx264', '-crf', '16', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', output], {stdio: 'inherit'});
  if (r.status !== 0) throw Error('ffmpeg failed');
  fs.writeFileSync(path.join(PUB, `footage/${NAME}.${LANG}.json`), JSON.stringify({start: t0, end: t1, fps: FPS, frames, captured, schedule}, null, 1) + '\n');
  fs.rmSync(WORK, {recursive: true, force: true});
  console.log(`${NAME}.${LANG}.mp4: ${frames} frames (${captured} captured), ${(t1 - t0).toFixed(1)} s from ${t0.toFixed(2)} s`);
})().catch(e => { console.error(e); process.exit(1); });
