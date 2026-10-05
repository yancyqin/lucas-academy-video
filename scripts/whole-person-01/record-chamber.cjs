// Record the Inception Space transit chamber, avatar hidden, for the opening of
// "全人教育的五个理念". Uses the museum's own Space Travel ride, which holds in the
// chamber with its Live Painting streaming past for as long as you like, and the
// dev server's ?debug&manual=1 hook so every frame is exactly 1/30 s of world time.
//
//   (Inception Space dev server on :8110 — npx vite --port 8110 in inception-space-ui)
//   PLAYWRIGHT_DIR=<dir with node_modules/playwright> node record-chamber.cjs <frames-dir> [seconds]
//   ffmpeg -framerate 30 -i <frames-dir>/%05d.jpg -c:v libx264 -crf 18 -pix_fmt yuv420p -g 15 transit-chamber.mp4
const fs = require('fs');
const path = require('path');
const { chromium } = require(path.join(process.env.PLAYWRIGHT_DIR || '.', 'node_modules/playwright'));

const out = path.resolve(process.argv[2] || 'chamber-frames');
const seconds = Number(process.argv[3] || 12);
const URL = 'http://localhost:8110/?world=museum&debug&manual=1&hud=0&fullscreen=0&inspect=room-b';
const sleep = ms => new Promise(r => setTimeout(r, ms));
const log = (...a) => console.log(new Date().toISOString().slice(11, 19), ...a);

(async () => {
  fs.mkdirSync(out, { recursive: true });
  for (const f of fs.readdirSync(out)) fs.unlinkSync(path.join(out, f));
  const browser = await chromium.launch({ channel: 'chrome', headless: true, args: ['--use-angle=metal', '--enable-gpu', '--ignore-gpu-blocklist'] });
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 720 }, deviceScaleFactor: 1.5 });
  await ctx.addInitScript(() => {
    try {
      localStorage.setItem('inception.subtitles.v1', '{"shown":false}');
      localStorage.setItem('inception.gravity', 'off');
      localStorage.setItem('inception.quality', 'ultra');
    } catch {}
  });
  const page = await ctx.newPage();
  page.on('pageerror', e => log('pageerror', e.message));
  await page.goto(URL, { timeout: 120000 });
  await page.waitForFunction(() => window.__museum?.world, null, { timeout: 120000 });

  // 1. Arrive in the cylinder room (it has the floor console that offers Space Travel).
  for (let i = 0; i < 400; i++) {
    const s = await page.evaluate(() => { const m = window.__museum; m.step(1000 / 30, 2); const p = m.probe(); return { room: p.room, pending: m.world.roomWorkPending(), chamber: p.transitChamber }; });
    if (i % 20 === 0) log('arrive', JSON.stringify(s));
    if (s.room === 'room-b' && s.pending === 0 && s.chamber) break;
    await sleep(120);
  }

  // 2. Floor console -> Space Travel (the 4th entry: three floor modes, then the ride).
  const opened = await page.evaluate(() => {
    const button = [...document.querySelectorAll('button')].find(b => b.style.cssText.includes('bottom: 28px') && b.style.cssText.includes('rgb(89, 215, 255)'));
    if (!button) return false;
    button.click();
    return true;
  });
  log('floor prompt clicked', opened);
  await sleep(300);
  await page.keyboard.press('Digit4');
  await sleep(300);
  const ride = await page.evaluate(() => { const m = window.__museum; m.step(1000 / 30, 2); return m.probe(); });
  log('after Space Travel', JSON.stringify({ room: ride.room, bodyY: ride.bodyY, transit: ride.transit }));
  if (!(ride.bodyY < -300)) throw new Error('not in the transit chamber (bodyY ' + ride.bodyY + ')');

  // 3. Let the chamber painting run a moment, then record.
  await page.evaluate(() => window.__museum.step(1000 / 30, 60));
  const frames = Math.round(seconds * 30);
  for (let i = 0; i < frames; i++) {
    const data = await page.evaluate(() => {
      const m = window.__museum, w = m.world;
      m.step(1000 / 30, 1);
      w.avatarRoot.visible = false; // the owner asked for the chamber without the figure
      w.render();
      return w.renderer.domElement.toDataURL('image/jpeg', 0.93);
    });
    fs.writeFileSync(path.join(out, String(i).padStart(5, '0') + '.jpg'), Buffer.from(data.split(',')[1], 'base64'));
    if (i % 60 === 0) log('frame', i, '/', frames);
  }
  log('done', frames, 'frames ->', out);
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });
